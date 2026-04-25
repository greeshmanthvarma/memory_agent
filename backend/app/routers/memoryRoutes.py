from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from app.database import get_db
from app.models import MemoryCreate, Memory, MemoryUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.memory_service import create_memory as create_memory_service
from app.services.embedding_service import embed_text
from app.services.db_service import db_get_all_memories as db_get_all_memories_service, db_get_memory_by_id as db_get_memory_by_id_service, db_get_memory_history as db_get_memory_history_service
from app.services.memory_service import db_memory_to_memory, get_memory_by_query as get_memory_by_query_service, update_memory as update_memory_service, delete_memory as delete_memory_service
from typing import List
from app.db_models import UserModel, MemoryMutationQueueModel
from app.middleware.auth import get_current_user
from app.models import MemoryMutationQueue
from app.state_models import ReflectionOutput

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
        result = await create_memory_service(memory, dense_embedding, user.id, user.collection_name, db, bypass_similarity_check)
        
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
        dense_query_vector = embed_text(query)
        memories = await get_memory_by_query_service(query, dense_query_vector, user.collection_name, user.id, db)
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


@memory_router.get("/mutation-queue")
async def get_mutation_queue(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            select(MemoryMutationQueueModel)
            .where(
                MemoryMutationQueueModel.user_id == user.id,
                MemoryMutationQueueModel.collection_name == user.collection_name,
            )
            .order_by(MemoryMutationQueueModel.finished_at.desc())
        )
        row = result.scalars().first()
        if row is None:
            return None

        return MemoryMutationQueue(
            id=row.id,
            payload=ReflectionOutput(**row.payload),
            status=row.status,
            created_at=row.created_at,
            finished_at=row.finished_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@memory_router.get("/{memory_id}/history")
async def get_memory_history(
    memory_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Memory]:
    try:
        versions = await db_get_memory_history_service(memory_id, user.id, db)
        return [db_memory_to_memory(memory) for memory in versions]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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

@memory_router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        await delete_memory_service(memory_id, user.id, user.collection_name, db)
        return JSONResponse({"message": "Memory deleted successfully"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))