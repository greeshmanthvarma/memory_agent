from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import List
from app.models import Conversation, Message
import json
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

        formatted_messages = "\n".join([f"{message.role}: {message.content}" for message in messages])
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
