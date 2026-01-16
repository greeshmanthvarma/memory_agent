from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.models import MemoryCreate, Memory
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.memory_service import create_memory as create_memory_service
from app.services.embedding_service import embed_text
from app.services.db_service import db_get_all_memories, db_get_memory_by_id
from app.services.memory_service import db_memory_to_memory, get_memory_by_query as get_memory_by_query_service
from typing import List

memory_router = APIRouter(
    prefix="/memory",
    tags=["memory"],
)

@memory_router.post("/create")
async def create_memory(memory: MemoryCreate,db: AsyncSession = Depends(get_db),bypass_similarity_check: bool = False) -> Memory:
    try:
        embedding = embed_text(memory.content)
        return await create_memory_service(memory,embedding,db,bypass_similarity_check)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/related")
async def get_memory_by_query(query: str,collection_name: str,db: AsyncSession = Depends(get_db)) -> List[dict]:
    try:
        query_vector= embed_text(query)
        memories = await get_memory_by_query_service(query_vector,collection_name,db)
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@memory_router.get("/")
async def get_all_memories(user_id: int,db: AsyncSession = Depends(get_db)) -> List[Memory]:
    try:
        memories = await db_get_all_memories(user_id,db)
        return [db_memory_to_memory(memory) for memory in memories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/{memory_id}")
async def get_memory_by_id(memory_id: int,db: AsyncSession = Depends(get_db)) -> Memory:
    try:
        memory = await db_get_memory_by_id(memory_id,db)
        return db_memory_to_memory(memory)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))