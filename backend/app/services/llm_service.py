from openai import OpenAI
from dotenv import load_dotenv
import os
import logging
from typing import List, Dict, Literal
from datetime import datetime, timedelta
from app.models import Message
import json
from sqlalchemy.ext.asyncio import AsyncSession
import tiktoken
import asyncio
from app.db_models import UserModel
from app.models import MemoryCreate, MemoryUpdate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from app.state_models import GraphState, QueryAnalysisOutput, ReflectionOutput, ReflectionInput
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.services.embedding_service import embed_text
from app.services.memory_service import get_memory_by_query, create_memory, update_memory
from app.services.db_service import (
    db_enqueue_memory_mutation,
    db_claim_next_mutation_job,
    db_mark_mutation_done,
    db_mark_mutation_failed,
    db_get_memory_by_id,
)
from app.database import AsyncSessionLocal
load_dotenv()

MUTATION_WORKER_POLL_SECONDS = 2.0
MUTATION_WORKER_IDLE_EXIT_SECONDS = 120.0
_mutation_worker_task: asyncio.Task | None = None
_mutation_worker_lock = asyncio.Lock()


async def ensure_mutation_worker_running() -> None:
    """Start mutation worker lazily, only when needed."""
    global _mutation_worker_task
    async with _mutation_worker_lock:
        if _mutation_worker_task and not _mutation_worker_task.done():
            return
        _mutation_worker_task = asyncio.create_task(run_mutation_worker())
        print("[mutation worker] Spawned on demand", flush=True)


async def stop_mutation_worker() -> None:
    """Stop mutation worker gracefully on app shutdown."""
    global _mutation_worker_task
    async with _mutation_worker_lock:
        task = _mutation_worker_task
        _mutation_worker_task = None
    if not task:
        return
    if task.done():
        try:
            await task
        except Exception:
            pass
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[mutation worker] stop failed: {e}", flush=True)

async def enqueue_memory_action(
    db: AsyncSession, reflection_output: ReflectionOutput, user_id: int, collection_name: str
) -> None:
    """
    Enqueue a mutation in Postgres. Processed by run_mutation_worker().
    Returns immediately after insert.
    """
    if reflection_output.action == "none" or not reflection_output.memory_content:
        print(f"[reflection] enqueue skipped (no-op) action={reflection_output.action} user_id={user_id} collection={collection_name}", flush=True)
        return
    payload = reflection_output.model_dump()
    job_id = await db_enqueue_memory_mutation(user_id, collection_name, payload, db)
    print(f"[reflection] Enqueued mutation job_id={job_id} user_id={user_id} collection={collection_name} action={reflection_output.action}", flush=True)
    await ensure_mutation_worker_running()


async def run_mutation_worker() -> None:
    """
    Worker that claims and processes rows from memory_mutation_queue.
    It exits after being idle for MUTATION_WORKER_IDLE_EXIT_SECONDS.
    """
    print("[mutation worker] Starting loop", flush=True)
    idle_elapsed = 0.0
    while True:
        try:
            async with AsyncSessionLocal() as session:
                job = await db_claim_next_mutation_job(session)
            if job is None:
                idle_elapsed += MUTATION_WORKER_POLL_SECONDS
                if idle_elapsed >= MUTATION_WORKER_IDLE_EXIT_SECONDS:
                    print("[mutation worker] Idle timeout reached, stopping", flush=True)
                    break
                await asyncio.sleep(MUTATION_WORKER_POLL_SECONDS)
                continue
            idle_elapsed = 0.0
            try:
                print(f"[mutation worker] Claimed job_id={job.id} user_id={job.user_id} collection={job.collection_name} status={job.status}", flush=True)
                output = ReflectionOutput.model_validate(job.payload)
                async with AsyncSessionLocal() as session:
                    try:
                        print(f"[mutation worker] Applying action job_id={job.id} user_id={job.user_id} collection={job.collection_name} action={output.action}", flush=True)
                        await apply_memory_action(
                            output,
                            session,
                            job.user_id,
                            job.collection_name,
                            getattr(output, "conversation_id", None),
                        )
                        await session.commit()
                        print(f"[mutation worker] Done job_id={job.id} user_id={job.user_id} collection={job.collection_name}", flush=True)
                    except Exception:
                        await session.rollback()
                        raise
                async with AsyncSessionLocal() as session:
                    await db_mark_mutation_done(job.id, session)
            except Exception as e:
                print(f"[mutation worker] FAILED job_id={job.id} user_id={job.user_id} error={e}", flush=True)
                try:
                    async with AsyncSessionLocal() as session:
                        await db_mark_mutation_failed(job.id, str(e), session)
                except Exception as mark_err:
                    print(f"[mutation worker] failed to mark job {job.id} as failed: {mark_err}", flush=True)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[mutation worker] loop error: {e}", flush=True)
            await asyncio.sleep(MUTATION_WORKER_POLL_SECONDS)
    print("[mutation worker] Loop exited", flush=True)

logger = logging.getLogger(__name__)


def _log_state(node_name: str, state: GraphState, config: RunnableConfig | None = None) -> None:
    """Log a compact, safe summary of graph state at node entry (no full message/retrieval content)."""
    try:
        msg_count = len(state.get("messages") or [])
        user_msg = (state.get("user_message") or "")[:200]
        if len(state.get("user_message") or "") > 200:
            user_msg += "..."
        summary = {
            "node": node_name,
            "user_message_len": len(state.get("user_message") or ""),
            "user_message_preview": user_msg,
            "messages_count": msg_count,
            "intent": state.get("intent"),
            "retrieval_query": (state.get("retrieval_query") or "")[:150] or None,
            "retry_count": state.get("retry_count", 0),
            "retry_feedback": (state.get("retry_feedback") or "")[:200] if state.get("retry_feedback") else None,
            "retrieval_results_count": len(state.get("retrieval_results") or []),
        }
        if (state.get("retrieval_results") or []):
            sims = [r.get("similarity") for r in (state.get("retrieval_results") or [])[:3]]
            summary["top_similarities"] = sims
        if config and isinstance(config.get("configurable"), dict):
            c = config["configurable"]
            summary["thread_id"] = c.get("thread_id")
            summary["user_id"] = c.get("user_id")
            summary["collection_name"] = c.get("collection_name")
        print(f"[graph state at {node_name}] {json.dumps(summary, default=str)}", flush=True)
    except Exception as e:
        print(f"[graph state] failed to log state at {node_name}: {e}", flush=True)


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
query_analysis_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
contradiction_detection_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
reflection_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
consolidation_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


QUERY_ANALYSIS_SYSTEM_PROMPT = """
You are the query analysis component of a personal memory assistant. Your output is used to search **only the user's memory store** — sentences about the user (where they live, preferences, past events, etc.). You are NOT building a query for a search engine or the open web.

## Your Task
Return JSON with: (1) intent, (2) retrieval_query used to find **relevant memories about the user**, (3) filters.

## Intent

- **general_knowledge**: Factual questions where user context doesn't help. Examples: "what is machine learning", "how does TCP work". Set retrieval_query to null.
- **personal**: Clearly about the user's life, preferences, or history. Examples: "what places did I visit recently", "remind me what I said about my project".
- **ambiguous**: Answer could be improved by personal context (location, preferences, past mentions). Examples: "recommend a book", "good food places near me", "good activities in San Francisco". Choose ambiguous when the user might want answers tailored to them.

Bias toward retrieval when the user might benefit from their stored context.

## Retrieval Query (critical)

The retrieval_query searches **the user's memories only**. So you must ask: "What facts about the user would help answer this?" — not "What generic topic is the user asking about?"

- **"Good food places near me"** → Retrieve where the user lives / location (e.g. "where user lives, city, neighborhood, location") and optionally food preferences — NOT "restaurants, dining options" (that would search the web, not memory).
- **"Recommend a book"** → "user's reading preferences, favorite books, genres".
- **"Good activities in San Francisco"** → "user's interests, hobbies, what they like to do" or "user in San Francisco, location" if you need to confirm they're there.
- **"What should I have for dinner?"** → "user's diet, food preferences, cuisine likes".

Keep important user-side terms that might appear in memories (location, preferences, past events). On retry, try a different angle (e.g. "user location" vs "where user lives").

Examples (user message → intent, retrieval_query):
- "what are some good food places near me?" → ambiguous, "where user lives, city, neighborhood, location, food preferences"
- "what are some of the places I visited recently?" → personal, "recently visited places, travel, trips"
- "remind me what I said about the launch" → personal, "launch, project, what user said"
- "recommend me a book" → ambiguous, "user reading preferences, favorite books, genres"
- "what is machine learning?" → general_knowledge, null

## Filters

Only when the user clearly constrains by time or source: "last week", "recently", "from my calendar". Otherwise use {{}}.

## Retry Context

{retry_context}

## Output Format

Valid JSON only, no markdown or explanation:
{{
    "intent": "general_knowledge" | "personal" | "ambiguous",
    "retrieval_query": "short searchable string" | null,
    "filters": {{}}
}}
"""

RETRY_CONTEXT_TEMPLATE = """
This is RETRY attempt {retry_count} of 2. The previous retrieval returned no (or poor) results.
Previous retrieval query: {previous_query}
Reason: {retry_feedback}

You MUST output a *different* retrieval_query — do not repeat the previous query. Try: different keywords, a broader angle (e.g. "user location" vs "where they live"), or include the user's own words from their message. The goal is to give the search a second, meaningfully different attempt.
"""

NO_RETRY_CONTEXT = "This is the first retrieval attempt."

RESPONSE_SYSTEM_PROMPT = """
You are a helpful personal AI assistant with access to the user's long term memories.
Memories relevant to this conversation have already been retrieved and are provided below.
{memory_context}
Guidelines:
- Use the provided memories to personalize your response where relevant
- Reference memories naturally and conversationally
- Do not invent information not present in the conversation or memories
- If no memories are provided or relevant, respond based on your general knowledge
Memory usage:
- "explicit" memories are manually added by the user and are highly reliable
- "implicit" memories are auto-generated from conversations, use with appropriate context
- Memories are sorted by relevance, the first ones are most relevant
- If memories conflict, prioritize explicit memories over implicit ones, then more recent over older
- Synthesize multiple memories when all are relevant
Temporal context:
- Always use the timestamp to reference memories naturally
- Recent memories (hours/days): "You mentioned yesterday...", "Based on your recent..."
- Older memories (weeks/months): "A few weeks ago you told me...", "Earlier this year..."
- Event patterns: If multiple similar events exist, acknowledge the pattern naturally
Tone:
- Be conversational, concise, and natural
- Never mention memory retrieval mechanics - no "based on retrieved memories..." or "I found a memory..."
- Simply incorporate memory information seamlessly as a good friend would
- Never say you couldn't find memories or that you searched for something
"""
REFLECTION_SYSTEM_PROMPT = """
You are the memory management component of a personal AI assistant.
Your job is to analyze a conversation turn and decide whether any memory action is needed.

You will be given:
- The user's message
- The assistant's response
- Existing memories that were retrieved for this turn

## Memory Actions

Decide on ONE of the following actions:

**none**: No memory action needed.
- The conversation is casual or factual with nothing personal worth remembering
- The information is already captured in existing memories
- The information is too vague or temporary to be useful later

**create**: Create a new memory.
- The conversation reveals something new and specific about the user
- It is not already captured in existing memories
- It would meaningfully personalize future conversations

**update**: Update exactly one existing memory.
- New information refines, corrects, or extends that memory
- The existing memory is still partially valid but needs modification
- Always prefer update over create if a relevant memory already exists
- Use target_memory_ids with exactly ONE id

**merge**: Merge two or more existing memories into one.
- Multiple existing memories cover the same topic redundantly
- A single consolidated memory would be more useful than several fragmented ones
- Use target_memory_ids with TWO or more ids
- Set memory_content to the fully synthesized merged text capturing all meaningful information from the individual memories

## What is worth remembering

Good candidates:
- User preferences and opinions ("user prefers X over Y")
- Personal facts ("user lives in X", "user works as Y")
- Goals and intentions ("user is working toward X")
- Significant events ("user started a new job", "user completed X")
- Patterns and habits ("user works out regularly", "user reads before bed")

Not worth remembering:
- Greetings and pleasantries
- One-off temporary requests ("remind me to buy milk")
- General knowledge questions with no personal relevance
- Vague statements that lack specific information
- Anything already well captured in existing memories

## Special rules for event memories

- Memories categorized as "event" should almost always use the "create" action
- Each occurrence of an event (e.g. workouts, trips, meetings) should be stored as a separate memory
- Do NOT use "update" or "merge" to collapse or overwrite past events unless the existing memory is clearly a duplicate of the SAME event on the SAME day
- Facts and preferences can be updated or merged; events generally should not be deduplicated
- If multiple similar events suggest a pattern, you may create a new fact or preference memory capturing the pattern (e.g. "works out regularly") without merging the individual event memories

## Output Format

Fields:
- action: the chosen action
- reasoning: brief explanation of why this action was chosen
- memory_content: full memory text written in neutral third person. null if action is none
- target_memory_ids: for update exactly one id, for merge two or more ids, empty list for none or create
- memory_category: fact, preference, or event. null if action is none
- tags: relevant tags for the memory, empty list if action is none

{{
    "action": "none" | "create" | "update" | "merge",
    "reasoning": "...",
    "memory_content": "..." | null,
    "target_memory_ids": [],
    "memory_category": "fact" | "preference" | "event" | null,
    "tags": []
}}

Return only the JSON object. No preamble, no explanation, no markdown.
"""
REFLECTION_USER_TEMPLATE = """
User message: {user_message}

Assistant response: {assistant_response}

Existing retrieved memories:
{memory_context}

Decide what memory action to take based on this conversation turn.
"""

def _build_summary_prompt(messages: str) -> str:
    """Build the prompt for summarizing a conversation"""
    return f"""
        You are an assistant responsible for creating long-term memories from conversations.

        Your task is to extract durable, reusable information that may be useful in future conversations.

        Messages:
        {messages}

        Each message has a role : user or assistant and the content of the message. The messages list is in chronological order.

        Instructions:
        1. Produce TWO summaries, relevant tags, and a classification:
        - summary_short: ONE concise sentence (max 25 words)
        - summary_long: A brief paragraph (3-6 sentences, max 500 tokens)
        - tags: A list of relevant tags (max 5 tags)
        - memory_category: Classification for deduplication purposes. Must be one of:
          * "fact": Stable factual information (e.g., "User is vegetarian", "User lives in San Francisco")
          * "preference": User preferences or opinions (e.g., "User prefers Italian cuisine", "User likes hiking")
          * "event": One-time or recurring events (e.g., "User did a pull workout today", "User visited Japan")
          
          Facts and preferences should be deduplicated (merged if similar). Events should NOT be deduplicated (each occurrence creates a new memory).
        

        2. Only create a summary if the information can add value to the user's memory space and be used as context for future conversations.
        
        CRITICAL: When in doubt, return null. It is better to skip a summary than to create a low-value memory.
        
        You MUST return null if:
        - The conversation doesn't reveal something specific about the USER
        - The information is temporary, vague, or unlikely to be useful later
        - You're uncertain whether the memory would add value
        
        CRITICAL: Do NOT create summaries for:
        - Temporary questions or one-off requests
        - Greetings, pleasantries, or casual conversation without substance
        - Information that's too vague or generic
        - Details that are unlikely to be relevant later
        - Questions that don't reveal anything about the USER
        
        What counts as "meaningful" memory (examples, not exhaustive):
        - Factual information ABOUT THE USER: preferences, decisions, important events, personal details
        - Reusable context: information that would help personalize future conversations WITH THE USER
        - Stable information: facts about the user that won't change quickly
        
        Rule of thumb: If the conversation doesn't reveal something specific about the USER that would be useful in future conversations, return null. When uncertain, err on the side of returning null.
        
        Use your judgment to determine if information is meaningful based on these guidelines, not just these specific examples.
        
        
        3. The summaries must:
        - Capture factual information, preferences, decisions, or important events
        - Avoid conversational fluff or temporary details
        - Be written in neutral third-person form
        - NOT mention "user", "assistant", or dialogue structure

        4. Do NOT invent information.
        5. Do NOT include opinions unless explicitly stated in the conversation.
        6. Only create a summary if you're confident the information is accurate and useful.
        
        Examples:
        
        Good summary (preference):
        {{
            "summary_short": "User prefers vegetarian restaurants and lives in San Francisco",
            "summary_long": "The user is vegetarian and enjoys exploring plant-based dining options in San Francisco. They mentioned living in the city and being interested in trying new vegetarian restaurants.",
            "tags": ["dietary_preferences", "location", "food"],
            "memory_category": "preference"
        }}
        
        Good summary (event):
        {{
            "summary_short": "User completed a pull workout today",
            "summary_long": "The user did a pull workout today, focusing on back and bicep exercises.",
            "tags": ["fitness", "workout"],
            "memory_category": "event"
        }}
        
        Bad summary (too temporary):
        {{
            "summary_short": null,
            "summary_long": null,
            "tags": [],
            "memory_category": null
        }}
        
        Bad summary (no factual value):
        {{
            "summary_short": null,
            "summary_long": null,
            "tags": [],
            "memory_category": null
        }}

        Return format (JSON only, no markdown, no extra text):
        {{
        "summary_short": "...",
        "summary_long": "...",
        "tags": ["..."],
        "memory_category": "fact" | "preference" | "event"
        }}
        
        If no meaningful memory can be formed, return:
        {{
        "summary_short": null,
        "summary_long": null,
        "tags": [],
        "memory_category": null
        }}
        """

def summarize_conversation(messages: List[Message]) -> dict:
    try:

        formatted_messages = "\n".join([f"role:{message.role}, content:{message.content}" for message in messages])
        prompt = _build_summary_prompt(formatted_messages)


        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                "role":"developer",
                "content":prompt
                }
            ]
        )
        try:
            return json.loads(response.output_text)
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing JSON response: {e}")
    except Exception as e:
        raise Exception(f"Error summarizing conversation: {e}")

def get_title(first_message: str) -> str:
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role" : "developer",
                    "content": f"Generate a concise 4-6 word title for a conversation starting with: {first_message}. Return only the title, no punctuation."
                }
            ]
        )
        return response.output_text
    except Exception as e:
        raise Exception(f"Error generating title: {e}")

def _build_query_analysis_prompt(state: GraphState) -> str:
    retry_count = state.get("retry_count", 0)
    
    if retry_count > 0:
        retry_context = RETRY_CONTEXT_TEMPLATE.format(
            retry_count=retry_count,
            previous_query=state.get("retrieval_query", ""),
            retry_feedback=state.get("retry_feedback", "")
        )
    else:
        retry_context = NO_RETRY_CONTEXT
    
    return QUERY_ANALYSIS_SYSTEM_PROMPT.format(
        retry_context=retry_context
    )


def _normalize_query_for_comparison(q: str) -> str:
    """Normalize so we can detect duplicate retrieval queries on retry."""
    if not q:
        return ""
    return " ".join(str(q).lower().split())


async def query_analysis(state: GraphState) -> dict:
    _log_state("query_analysis", state)
    try:
        prompt = _build_query_analysis_prompt(state)
        response = await query_analysis_model.with_structured_output(
            QueryAnalysisOutput,
            method="function_calling",
        ).ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=state["user_message"])
        ])
        out = response.model_dump()
        # If we're on retry and the model returned the same query, force a different one (use user message)
        retry_count = state.get("retry_count", 0)
        if retry_count >= 1 and out.get("retrieval_query"):
            prev = _normalize_query_for_comparison(state.get("retrieval_query") or "")
            new_q = _normalize_query_for_comparison(out["retrieval_query"])
            if prev and new_q == prev:
                out["retrieval_query"] = (state.get("user_message") or "").strip() or out["retrieval_query"]
        return out
    except Exception as e:
        print(f"[graph] query_analysis failed, defaulting to ambiguous intent: {e}", flush=True)
        return {
            "intent": "ambiguous",
            "retrieval_query": state["user_message"],
            "filters": {}
        }
def should_retrieve(state: GraphState) -> Literal["retrieve", "respond"]:
    intent = state.get("intent")
    retrieval_query = state.get("retrieval_query")

    if intent == "general_knowledge":
        return "respond"
    if retrieval_query and str(retrieval_query).strip():
        return "retrieve"
    if intent in ("personal", "ambiguous"):
        return "retrieve"
    return "respond"


def _relative_time_str(created_at) -> str:
    """Format created_at as human-readable relative time for the LLM."""
    if created_at is None:
        return "unknown"
    if not isinstance(created_at, datetime):
        return str(created_at) if created_at else "unknown"
    now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
    delta = now - created_at
    if delta < timedelta(minutes=1):
        return "just now"
    if delta < timedelta(hours=1):
        return f"{int(delta.total_seconds() / 60)} minutes ago"
    if delta < timedelta(days=1):
        return f"{int(delta.total_seconds() / 3600)} hours ago"
    if delta.days == 1:
        return "yesterday"
    if delta.days < 7:
        return f"{delta.days} days ago"
    if delta.days < 30:
        return f"{delta.days // 7} weeks ago"
    if delta.days < 365:
        return f"{delta.days // 30} months ago"
    return f"{delta.days // 365} years ago"


def _format_retrieval_results_for_prompt(results: List[dict], max_items: int = 5) -> str:
    """Format retrieval results with temporal info for injection into the response prompt."""
    if not results:
        return ""
    def _field(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    lines = []
    for item in results[:max_items]:
        memory = item.get("memory")
        similarity = item.get("similarity", 0)
        if not memory:
            continue
        content = _field(memory, "content", "")
        memory_type = _field(memory, "memory_type", "")
        tags = _field(memory, "tags", []) or []
        tags_str = ", ".join(tags) if tags else "No tags"
        created_at = _field(memory, "created_at")
        time_str = _relative_time_str(created_at) if created_at else "unknown"
        created_iso = created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(created_at, datetime) else str(created_at or "")
        lines.append(
            f"Memory ID {_field(memory, 'id', '')}: {content}\n"
            f"  Memory Type: {memory_type}, Similarity: {similarity:.2f}\n"
            f"  Tags: {tags_str}, Created: {time_str} ({created_iso})\n"
        )
    return "\n\n".join(lines)



async def retrieve_memories(state: GraphState, config: RunnableConfig) -> dict:
    """
    Retrieve memories: search with the analysis retrieval_query and, when different,
    also with the raw user_message; merge and dedupe by memory id (keep max similarity).
    """
    _log_state("retrieve_memories", state, config)
    try:
        retrieval_query = (state.get("retrieval_query") or "").strip()
        user_message = (state.get("user_message") or "").strip()
        user_id = config["configurable"]["user_id"]
        collection_name = config["configurable"]["collection_name"]

        # Use retrieval_query if set, else fall back to user message
        primary_query = retrieval_query or user_message
        if not primary_query:
            return {"retrieval_results": []}

        async with AsyncSessionLocal() as db:
            primary_dense = embed_text(primary_query)
            results = await get_memory_by_query(
                primary_query, primary_dense,
                collection_name, user_id, db
            )

            # If we have a distinct user message, also search with it and merge (better recall)
            if user_message and user_message != primary_query:
                user_dense = embed_text(user_message)
                user_results = await get_memory_by_query(
                    user_message, user_dense,
                    collection_name, user_id, db
                )
                # Merge by memory id, keep max similarity
                seen = {r["memory"].id: r for r in results}
                for r in user_results:
                    mid = r["memory"].id
                    if mid not in seen or (r["similarity"] > seen[mid]["similarity"]):
                        seen[mid] = r
                results = sorted(seen.values(), key=lambda x: x["similarity"], reverse=True)

        if len(results) == 0:
            return {"retrieval_results": []}
        for i, r in enumerate(results):
            mem = r.get("memory")
            content = getattr(mem, "content", "") if mem else ""
            preview = (content[:80] + "…") if len(content) > 80 else content
            mid = getattr(mem, "id", "?") if mem else "?"
            sim = r.get("similarity")
            print(f"[retrieve_memories] #{i+1} id={mid} similarity={sim:.4f} content={preview!r}", flush=True)
        return {"retrieval_results": results}
    except Exception as e:
        print(f"[graph] retrieve_memories failed: {e}", flush=True)
        return {"retrieval_results": []}


def retrieval_evaluation(state: GraphState) -> dict:
    _log_state("retrieval_evaluation", state)
    results = state.get("retrieval_results", [])
    current_retry = state.get("retry_count", 0)
    MIN_RERANK_SCORE = 0.03
    if len(results) == 0:
        return {
            "retry_count": current_retry + 1,
            "retry_feedback": "No memories were found. Try using broader or more general terms.",
        }

    best = float(results[0].get("similarity") or 0.0)
    if best < MIN_RERANK_SCORE:
        return {
            "retry_count": current_retry + 1,
            "retry_feedback": (
                f"Best reranker score was {best:.4f}, below the relevance threshold ({MIN_RERANK_SCORE:.4f}). "
                "Try rephrasing with different keywords, including user-specific terms (location/preferences), "
                "or using a broader query."
            ),
        }

    return {"retry_count": current_retry, "retry_feedback": None}

def decide_retry(state: GraphState) -> Literal["retry", "respond"]:
    if (state.get("retry_count") or 0) >= 2:
        return "respond"
    
    if state.get("retry_feedback") is not None:
        return "retry"
    
    return "respond"

def _build_chat_prompt(memory_context: str) -> str:
    return RESPONSE_SYSTEM_PROMPT.format(memory_context=memory_context)


async def respond(state: GraphState) -> dict:
    _log_state("respond", state)
    try:
        results = state.get("retrieval_results", [])
        memory_context = _format_retrieval_results_for_prompt(results) if results else _format_retrieval_results_for_prompt([])
        prompt = _build_chat_prompt(memory_context)
        messages = [SystemMessage(content=prompt)] + state.get("messages", [])
        response = await chat_model.ainvoke(messages)
        return {"messages" : [response]}
    except Exception as e:
        raise Exception(f"Error responding: {e}")


async def reflection(input: ReflectionInput):
    try:

        prompt = REFLECTION_SYSTEM_PROMPT
        memory_context = _format_retrieval_results_for_prompt(input.retrieval_results)
        user_message = REFLECTION_USER_TEMPLATE.format(
            user_message=input.user_message,
            assistant_response=input.assistant_response,
            memory_context=memory_context,
        )
        messages = [SystemMessage(content=prompt)] + [HumanMessage(content=user_message)]
        response = await reflection_model.with_structured_output(
            ReflectionOutput, method="function_calling"
        ).ainvoke(messages)
        response.conversation_id = input.conversation_id
        async with AsyncSessionLocal() as session:
            await enqueue_memory_action(session, response, input.user_id, input.collection_name)
    except Exception as e:
        print(f"[reflection] Reflection/mutation failed: {e}", flush=True)
        raise Exception(f"Error reflecting: {e}") from e



async def apply_memory_action(
    reflection: ReflectionOutput, db: AsyncSession, user_id: int, collection_name: str, conversation_id: int | None = None
) -> None:
    if reflection.action == "none" or not reflection.memory_content:
        print(
            f"[reflection] apply_memory_action skipped (no-op) action={reflection.action} "
            f"user_id={user_id} collection={collection_name}",
            flush=True,
        )
        return
    try:
        print(
            f"[reflection] apply_memory_action start action={reflection.action} "
            f"user_id={user_id} collection={collection_name} target_ids={reflection.target_memory_ids}",
            flush=True,
        )

        raw_ids = reflection.target_memory_ids or []
        requested_ids = [int(t) for t in raw_ids if str(t).strip()]
        valid_ids: list[int] = []

        for target_id in requested_ids:
            try:
                await db_get_memory_by_id(target_id, user_id, db)
                valid_ids.append(target_id)
            except ValueError:
                print(
                    f"[reflection] Skipping invalid target id={target_id} "
                    f"(not found for user_id={user_id})",
                    flush=True,
                )

        if reflection.action == "update":
            if len(valid_ids) != 1:
                print(
                    f"[reflection] update skipped – expected exactly 1 valid target id, "
                    f"got {len(valid_ids)} (requested={requested_ids}, valid={valid_ids})",
                    flush=True,
                )
                return
        elif reflection.action == "merge":
            if len(valid_ids) < 2:
                print(
                    f"[reflection] merge skipped – expected >=2 valid target ids, "
                    f"got {len(valid_ids)} (requested={requested_ids}, valid={valid_ids})",
                    flush=True,
                )
                return

        dense_embedding = embed_text(reflection.memory_content)
        memory_create = MemoryCreate(
            content=reflection.memory_content,
            memory_type="implicit",
            memory_category=reflection.memory_category,
            tags=reflection.tags or [],
            conversation_id=conversation_id,
        )
        bypass_dedup = reflection.action in ("update", "merge")
        result = await create_memory(
            memory_create,
            dense_embedding,
            user_id,
            collection_name,
            db,
            bypass_dedup,
        )
        new_memory_id = result["memory"].id
        print(
            f"[reflection] Created implicit memory id={new_memory_id} action={reflection.action} "
            f"user_id={user_id} collection={collection_name}",
            flush=True,
        )

        if reflection.action == "update":
            old_id = valid_ids[0]
            await update_memory(
                old_id,
                MemoryUpdate(superseded_by_id=new_memory_id),
                None,
                user_id,
                collection_name,
                db,
            )
        elif reflection.action == "merge":
            for target_id in valid_ids:
                await update_memory(
                    target_id,
                    MemoryUpdate(superseded_by_id=new_memory_id),
                    None,
                    user_id,
                    collection_name,
                    db,
                )
    except Exception as e:
        print(f"[reflection] apply_memory_action failed: {e}", flush=True)
        raise Exception(f"Error applying memory action: {e}") from e


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("query_analysis", query_analysis)
    graph.add_node("retrieve_memories", retrieve_memories)
    graph.add_node("retrieval_evaluation", retrieval_evaluation)
    graph.add_node("respond", respond)


    graph.add_edge(START, "query_analysis")

    graph.add_conditional_edges(
        "query_analysis",
        should_retrieve,
        {
            "retrieve": "retrieve_memories",
            "respond": "respond",
        },
    )

    graph.add_edge("retrieve_memories", "retrieval_evaluation")

    graph.add_conditional_edges(
        "retrieval_evaluation",
        decide_retry,
        {
            "retry": "query_analysis",
            "respond": "respond",
        },
    )

    graph.add_edge("respond", END)
    return graph
    
async def chat(user: UserModel, user_message: str, thread_id: str, graph, state_capture: dict = None):
    initial_state: GraphState = {
        "messages": [HumanMessage(content=user_message)],
        "user_message": user_message,
        "retry_count": 0,
    }

    config: RunnableConfig = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user.id,
            "collection_name": user.collection_name,
        }
    }

    async for mode,chunk in graph.astream(
        initial_state,
        config=config,
        stream_mode=["messages", "updates"],
    ):
        if mode == "messages":
            if isinstance(chunk, tuple):
                message, _metadata = chunk
            else:
                message = chunk
            content = getattr(message, "content", None)
            if isinstance(content, str) and content:
                yield content
        elif mode == "updates":
            if "retrieve_memories" in chunk and state_capture is not None:
                state_capture["retrieval_results"] = chunk["retrieve_memories"].get("retrieval_results", [])
                


def _format_messages(messages: List[Message]) -> List[Dict]:
    """Format a list of messages into a list of dictionaries"""
    formatted_messages = []
    for message in messages:
        formatted_messages.append({
            "role": message.role,
            "content": message.content
        })
    return formatted_messages

def count_conversation_tokens(messages: List[Message]) -> int:
    """Count the number of tokens in a conversation"""
    encoding = tiktoken.get_encoding("cl100k_base")
    formatted_messages = _format_messages(messages)
    json_string = json.dumps(formatted_messages)
    tokens = encoding.encode(json_string)
    return len(tokens)

def compact_conversation(messages: List[Message]) -> List[Dict]:
    try:
        formatted_messages = _format_messages(messages)
        compacted_response = client.responses.compact(
            model="gpt-4o-mini",
            input=formatted_messages
        )
        return compacted_response.output
    except Exception as e:
        raise Exception(f"Error compacting conversation: {e}")

