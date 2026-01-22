from fastapi import APIRouter, Depends, HTTPException
from app.services.llm_service import chat
from app.models import Conversation, Message
from app.services.llm_service import summarize_conversation,chat as chat_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

chat_router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


