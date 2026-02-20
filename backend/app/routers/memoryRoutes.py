from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from app.database import get_db
from app.models import MemoryCreate, Memory, MemoryUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.memory_service import create_memory as create_memory_service
from app.services.embedding_service import embed_text, sparse_embed_text
from app.services.db_service import db_get_all_memories as db_get_all_memories_service, db_get_memory_by_id as db_get_memory_by_id_service
from app.services.memory_service import db_memory_to_memory, get_memory_by_query as get_memory_by_query_service, update_memory as update_memory_service
from typing import List
from app.db_models import UserModel
from app.middleware.auth import get_current_user

memory_router = APIRouter(
    prefix="/api/memory",
    tags=["memory"],
)

@memory_router.post("/create")
async def create_memory(
    memory: MemoryCreate,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    bypass_similarity_check: bool = Query(False, description="Skip similarity check for duplicate memories")
):
    try:
        dense_embedding = embed_text(memory.content)
        sparse_embedding = sparse_embed_text(memory.content)
        result = await create_memory_service(memory,dense_embedding,sparse_embedding,user.id,user.collection_name,db,bypass_similarity_check)
        
        if result["is_duplicate"]:
            if result["duplicate_type"] == "exact":
                message = "Memory already exists (exact match found)"
            else:
                message = "Similar memory already exists"
        else:
            message = "Memory created successfully"
        
        return JSONResponse({
            "memory": result["memory"].model_dump(mode='json'),
            "message": message,
            "is_duplicate": result["is_duplicate"]
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/related")
async def get_memory_by_query(
    query: str = Query(..., description="Search query to find related memories"),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    try:
        query_vector= embed_text(query)
        memories = await get_memory_by_query_service(query_vector,user.collection_name,user.id,db)
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@memory_router.get("/")
async def get_all_memories(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Memory]:
    try:
        memories = await db_get_all_memories_service(user.id,db)
        return [db_memory_to_memory(memory) for memory in memories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/{memory_id}")
async def get_memory_by_id(
    memory_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Memory:
    try:
        memory = await db_get_memory_by_id_service(memory_id,user.id,db)
        return db_memory_to_memory(memory)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.patch("/{memory_id}")
async def update_memory(
    memory_id: int,
    memory: MemoryUpdate,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Memory:
    try:
        embedding = embed_text(memory.content) if memory.content is not None else None
        updated = await update_memory_service(memory_id, memory, embedding, user.id, user.collection_name, db)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))