from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import List, Dict
from app.models import Message
from app.services.tools import create_search_memories_tool
import json
from sqlalchemy.ext.asyncio import AsyncSession
import tiktoken
from app.db_models import UserModel
load_dotenv()

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
        1. Produce TWO summaries:
        - summary_short: ONE concise sentence (max 25 words)
        - summary_long: A brief paragraph (3-6 sentences, max 500 tokens)

        2. The summaries must:
        - Capture factual information, preferences, decisions, or important events
        - Avoid conversational fluff or temporary details
        - Be written in neutral third-person form
        - NOT mention "user", "assistant", or dialogue structure

        3. Do NOT invent information.
        4. Do NOT include opinions unless explicitly stated in the conversation.
        5. If no meaningful memory can be formed, return null.

        Return format (JSON only):
        {{
        "summary_short": "...",
        "summary_long": "..."
        }}
        """

def summarize_conversation(messages: List[Message]) -> dict:
    try:

        formatted_messages = "\n".join([f"role:{message.role}, content:{message.content}" for message in messages])
        prompt = _build_summary_prompt(formatted_messages)


        response = client.responses.create(
            model="gpt-4o-mini",
            input={
                "role":"developer",
                "content":prompt
            }
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
    - Do not invent information unless it is explicitly stated in the conversation.
    - If no relevant memories are found, respond based on your general knowledge.

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
                "strict":"true",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query to find relevant memories"}
                    },
                    "required": ["query"]
                }
            }
        ]
        input_messages = [
            {
                "role":"developer",
                "content":_build_chat_prompt()
            }]+conversation_history+[
            {
                "role":"user",
                "content":user_message
            }
        ]
        response = client.responses.create(
            tools=tools,
            model="gpt-4o-mini",
            input=input_messages
        )
        tool_call_made = False
        for tool_call in response.output:
            if tool_call.type != "function_call":
                continue

            tool_call_made= True
            if isinstance(tool_call.arguments, str):
                args = json.loads(tool_call.arguments)
            else:
                args = tool_call.arguments

            result = await search_memories_tool(args["query"])
            input_messages.append({
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": str(result)
            })
        if tool_call_made:
            final_response = client.responses.create(
                tools=tools,
                model="gpt-4o-mini",
                input=input_messages
            )
        else:
            final_response = response
        return final_response.output_text
    except Exception as e:
        raise Exception(f"Error formulating a response: {e}")