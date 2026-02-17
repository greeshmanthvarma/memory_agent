from openai import OpenAI
from dotenv import load_dotenv
import os
import logging
from typing import List, Dict
from app.models import Message
from app.services.tools import create_search_memories_tool
import json
from sqlalchemy.ext.asyncio import AsyncSession
import tiktoken
from app.db_models import UserModel
load_dotenv()

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def _build_chat_prompt() -> str:
    """Build the prompt for chatting with the agent"""
    return """
    You are a helpful AI assistant with access to user's long term memories. 
    You can search through the user's memories to recall past information, preferences, and experiences.

    Guidelines:
    - Use the search_memories tool when you need to recall past information that might be relevant to the conversation.
    - If the user asks you to recall a memory, you should use the search_memories tool to recall the memory.
    - Be conversational, helpful, and natural.
    - Reference specific memories when relevant to provide personalized responses.
    - Do not invent information unless it is explicitly stated in the conversation or memories.
    - If no relevant memories are found, respond based on your general knowledge.
    
    CRITICAL: Do NOT mention memory search results in your responses unless it's directly relevant to answering the user's question.
    - Do NOT say things like "I couldn't find any memories..." or "It looks like I didn't find..." or "I searched your memories and..."
    - Simply respond naturally with your answer, incorporating memory information seamlessly when available.
    - If memories are relevant, reference them naturally (e.g., "Since you enjoyed Dandadan..." instead of "Based on the memory I found about Dandadan...").
    - If no memories are found, just answer the question directly without mentioning the search (e.g., "Here are some recent romance SOL anime..." instead of "I didn't find memories, but here are...").
    
    Using memory information effectively:
    - Memory Type: "explicit" memories are manually logged by the user and are highly reliable. "implicit" memories are auto-generated from conversations and should be used with appropriate context.
    - Similarity scores: Higher scores (>0.8) indicate more relevant memories. Use multiple memories if they're all relevant.
    - Tags: Use tags to understand memory categories and find related information.
    - Multiple memories: When multiple memories are returned, synthesize them to provide comprehensive context. If memories conflict, prioritize more recent or explicit ones.
    
    Temporal context guidelines:
    - The "Created" timestamp shows when the memory was formed. Always use this temporal information in your responses.
    - For recent memories (hours/days ago): Reference them with specific timeframes (e.g., "You mentioned X yesterday", "Based on your recent conversation about Y").
    - For older memories (weeks/months/years ago): Acknowledge the time gap appropriately (e.g., "You mentioned X a few weeks ago", "Earlier this year you told me about Y").
    - Event-type memories: These represent specific occurrences at particular times. Always reference them with temporal context:
      * Recent events: "You did a pull workout yesterday" (specific)
      * Older events: "You did pull workouts last week" or "You mentioned doing pull workouts a few days ago" (appropriate timeframe)
    - Recency priority: More recent memories are often more relevant to current context, but older memories provide valuable historical context and patterns.
    - Temporal patterns: If multiple event-type memories show patterns (e.g., multiple workouts), acknowledge the pattern with temporal context (e.g., "You've been doing pull workouts regularly this week").
    - When referencing temporal information, be natural and conversational - don't just state dates, use relative timeframes that feel natural.
    
    Best practices:
    - Proactively search memories when the conversation topic is clearly personal or user-specific (e.g., preferences, past experiences, personal questions). Do NOT search for general knowledge questions that don't require personal context.
    - When referencing memories, be specific but natural (e.g., "Based on what you mentioned about X..." rather than "According to Memory ID 123...").
    - If a memory seems incorrect or outdated, acknowledge uncertainty and ask for clarification if needed.
    - Respect user privacy - memories are personal and should be referenced appropriately in context.
    - Keep responses concise and direct. Don't add unnecessary meta-commentary about memory searches.

   """
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

async def chat(user: UserModel, db: AsyncSession,user_message: str,messages: List[Message]) -> str:
    try:
        search_memories_tool = create_search_memories_tool(db, user)
        token_count = count_conversation_tokens(messages)
        if token_count > 80000:
            compacted_messages = compact_conversation(messages)
            conversation_history = compacted_messages
        else:
            conversation_history = _format_messages(messages)

        tools = [
            {
                "type": "function",
                "name": "search_memories",
                "description": "Search for relevant memories by semantic similarity.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query to find relevant memories"}
                    },
                    "required": ["query"],
                    "additionalProperties": False
                }
            }
        ]
        input_messages = conversation_history + [
            {"role": "user", "content": user_message}
        ]
        stream = client.responses.create(
            tools=tools,
            model="gpt-4o-mini",
            instructions=_build_chat_prompt(),
            input=input_messages,
            stream=True,
        )
        tool_call_made = False

        for event in stream:
            if event.type == "response.output_item.done" and getattr(event, "item", None) and getattr(event.item, "type", None) == "function_call":
                tool_call_made = True
                if isinstance(event.item.arguments, str):
                    args = json.loads(event.item.arguments)
                    arguments_str = event.item.arguments
                else:
                    args = event.item.arguments or {}
                    arguments_str = json.dumps(args)
                input_messages.append({
                    "type": "function_call",
                    "call_id": event.item.call_id,
                    "name": event.item.name,
                    "arguments": arguments_str,
                })
                if event.item.name == "search_memories":
                    result = await search_memories_tool(args.get("query", ""))
                    input_messages.append({
                        "type": "function_call_output",
                        "call_id": event.item.call_id,
                        "output": str(result),
                    })
            elif event.type == "response.output_text.delta":
                delta = getattr(event, "delta", None) or getattr(event, "text", "") or ""
                if delta:
                    #logger.info("stream chunk (first response): %r", delta)
                    #print(f"[stream] first response chunk: {delta!r}", flush=True)
                    yield delta

        if tool_call_made:
            final_stream = client.responses.create(
                tools=tools,
                model="gpt-4o-mini",
                instructions=_build_chat_prompt(),
                input=input_messages,
                stream=True,
            )
            for event in final_stream:
                if event.type == "response.output_text.delta":
                    delta = getattr(event, "delta", None) or getattr(event, "text", "") or ""
                    if delta:
                        yield delta
    
    except Exception as e:
        raise Exception(f"Error formulating a response: {e}")