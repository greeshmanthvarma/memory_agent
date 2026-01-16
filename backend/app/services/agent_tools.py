from agents import FunctionTool
from app.services.embedding_service import embed_text
from app.services.memory_service import get_memory_by_query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any


@FunctionTool
async def search_memories(query : str,) -> :
    """
        Search for relevant memories by semantic similarity

    
    """

    try:
        query_vector = embed_text(query)