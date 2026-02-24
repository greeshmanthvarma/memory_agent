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
from app.db_models import UserModel
from langchain_openai import ChatOpenAI
from app.state_models import GraphState, QueryAnalysisOutput
from langchain_core.messages import SystemMessage, HumanMessage
from app.services.embedding_service import embed_text, sparse_embed_text
from app.services.memory_service import get_memory_by_query
load_dotenv()

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
query_analysis_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
contradiction_detection_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
reflection_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
consolidation_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


QUERY_ANALYSIS_SYSTEM_PROMPT = """
You are the query analysis component of a personal memory assistant. Your job is to analyze the user's message and prepare it for memory retrieval.

## Your Task
Analyze the user message and return a JSON object with:
1. Classify the intent
2. Generate an optimized retrieval query if needed
3. Extract any filters if applicable

## Intent Classification

Classify the intent as one of three categories:

**general_knowledge**: The query is factual or informational with no personalization value.
- The user is asking about concepts, definitions, or facts
- Knowing anything about the user would not improve the answer
- Examples: "what is machine learning", "how does TCP work", "what year was the Eiffel Tower built"

**personal**: The query is clearly about the user or would benefit significantly from personal context.
- The query references the user's life, preferences, goals, habits, or experiences
- Retrieving memories would meaningfully improve the response
- Examples: "what should I focus on today", "how am I doing on my goals", "remind me what I said about my project"

**ambiguous**: The query could benefit from personalization but is not explicitly personal.
- A general answer exists but personal context could improve it
- Retrieval will be attempted once but not retried if results are poor
- Examples: "recommend me a book", "what are good activities in San Francisco", "what should I have for dinner"

When in doubt between personal and ambiguous, classify as ambiguous.
When in doubt between ambiguous and general_knowledge, classify as ambiguous.
Always bias toward retrieval over skipping it.

## Retrieval Query Generation

If intent is personal or ambiguous, generate an optimized retrieval query that:
- Captures the core information need behind the user's message
- Is phrased to match how memories are likely stored - as natural language summaries of facts, preferences, and experiences
- Expands on vague queries - "what should I work on" becomes "user's current projects priorities and goals"
- Is broader than the original query when the original is too narrow
- Incorporates retry feedback if provided

If intent is general_knowledge, set retrieval_query to null.

## Filters

Extract filters only when the query explicitly implies a constraint:
- Time: "last week", "recently", "in January" → created_at filter
- Source: "something I added manually", "from my calendar" → source filter
- Leave filters as empty dict if no clear constraint exists

## Retry Context

{retry_context}

## Output Format

Return a valid JSON object:
{{
    "intent": "general_knowledge" | "personal" | "ambiguous",
    "retrieval_query": "optimized query string" | null,
    "filters": {{}} | {{"source": "...", "created_at": {{...}}}}
}}

Return only the JSON object. No preamble, no explanation, no markdown.
"""

RETRY_CONTEXT_TEMPLATE = """
This is retry attempt {retry_count} of 2. The previous retrieval attempt failed to find relevant memories.
Previous retrieval query: {previous_query}
Reason: {retry_feedback}
Generate a meaningfully different retrieval query that addresses this feedback.
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


async def query_analysis(state: GraphState) -> dict:
    try:
        prompt = _build_query_analysis_prompt(state)
        response = await query_analysis_model.with_structured_output(QueryAnalysisOutput).ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=state["user_message"])
        ])
        return response.model_dump()
    except Exception as e:
        logger.warning("query analysis failed, defaulting to ambiguous intent")
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
    lines = []
    for item in results[:max_items]:
        memory = item.get("memory")
        similarity = item.get("similarity", 0)
        if not memory:
            continue
        content = getattr(memory, "content", memory.get("content", ""))
        memory_type = getattr(memory, "memory_type", memory.get("memory_type", ""))
        tags = getattr(memory, "tags", memory.get("tags")) or []
        tags_str = ", ".join(tags) if tags else "No tags"
        created_at = getattr(memory, "created_at", memory.get("created_at"))
        time_str = _relative_time_str(created_at) if created_at else "unknown"
        created_iso = created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(created_at, datetime) else str(created_at or "")
        lines.append(
            f"Memory ID {getattr(memory, 'id', memory.get('id', ''))}: {content}\n"
            f"  Memory Type: {memory_type}, Similarity: {similarity:.2f}\n"
            f"  Tags: {tags_str}, Created: {time_str} ({created_iso})\n"
        )
    return "\n\n".join(lines)


def create_retrieve_memories_node(db: AsyncSession, user: UserModel):
    async def retrieve_memories(state: GraphState) -> dict:
        """
        Retrieve memories from the database based on the retrieval query.
        Returns raw results, scores, and a formatted string with temporal info for the prompt.
        """
        try:
            retrieval_query = (state.get("retrieval_query") or "").strip() or state.get("user_message", "")
            dense_query_vector = embed_text(retrieval_query)
            sparse_query_vector = sparse_embed_text(retrieval_query)
            results = await get_memory_by_query(
                retrieval_query, dense_query_vector, sparse_query_vector,
                user.collection_name, user.id, db
            )
            if len(results) == 0:
                return {
                    "retrieval_results": [],
                }
            return {"retrieval_results": results}
        except Exception as e:
            logger.exception("retrieve_memories failed")
            return {
                "retrieval_results": [],
            }
    return retrieve_memories

def retrieval_evaluation(state: GraphState) -> dict:
    results = state.get("retrieval_results", [])
    if len(results) == 0:
        return {"retry_count": state["retry_count"]+1, "retry_feedback": "No memories were found. Try using broader or more general terms."}
    elif results[0].get("similarity") < 0.4:
        return {"retry_count": state["retry_count"]+1, "retry_feedback": f"Best match scored {results[0].get("similarity"):.2f} out of 1.0 which is below the relevance threshold. Try rephrasing with different keywords or broader terms."}
    
    return {"retry_count": state["retry_count"], "retry_feedback": None}

def decide_retry(state: GraphState) -> Literal["retry", "respond"]:
    if (state.get("retry_count") or 0) >= 2:
        return "respond"
    
    if state.get("retry_feedback") is not None:
        return "retry"
    
    return "respond"

def _build_chat_prompt(memory_context: str) -> str:
    return RESPONSE_SYSTEM_PROMPT.format(memory_context=memory_context)

async def respond(state: GraphState) -> dict:
    try:
        memory_context = _format_retrieval_results_for_prompt(state.get("retrieval_results", []))
        prompt = _build_chat_prompt(memory_context)
        messages = [SystemMessage(content=prompt)] + state.get("messages", [])
        response = await chat_model.ainvoke(messages)
        return {"messages" : [response]}
    except Exception as e:
        raise Exception(f"Error responding: {e}")

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

