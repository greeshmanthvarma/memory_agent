from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from app.database import get_db
from app.models import MemoryCreate, Memory, MemoryUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.memory_service import create_memory as create_memory_service
from app.services.embedding_service import embed_text
from app.services.qdrant_service import set_memory_superseded_flag
from app.services.db_service import db_get_all_memories as db_get_all_memories_service, db_get_memory_by_id as db_get_memory_by_id_service, db_get_memory_history as db_get_memory_history_service, db_get_memory_by_content as db_get_memory_by_content, db_update_memory as db_update_memory, db_mark_mutation_discarded
from app.services.memory_service import db_memory_to_memory, get_memory_by_query as get_memory_by_query_service, update_memory as update_memory_service, delete_memory as delete_memory_service
from typing import List
from app.db_models import UserModel, MemoryMutationQueueModel, MemoryModel, MemoryType
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

@memory_router.post("/mutation-queue/{job_id}/discard")
async def discard_mutation_job(job_id: int, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        job = await db.execute(select(MemoryMutationQueueModel).where(MemoryMutationQueueModel.id == job_id).filter(MemoryMutationQueueModel.user_id == user.id).filter(MemoryMutationQueueModel.collection_name == user.collection_name))
        job = job.scalar_one_or_none()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status == "discarded":
            return JSONResponse({"message": "Mutation already discarded", "job_id": job_id})
        if job.status != "done":
            raise HTTPException(status_code=400, detail="Only completed mutation jobs can be discarded")

        payload = job.payload
        action = payload.get("action")
        if action == "create":
            memory_content = payload.get("memory_content")
            if not memory_content:
                raise HTTPException(status_code=400, detail="Invalid payload: memory_content is required for create rollback")
            conversation_id = payload.get("conversation_id")
            q = (
                select(MemoryModel)
                .where(
                    MemoryModel.user_id == user.id,
                    MemoryModel.memory_type == MemoryType.IMPLICIT,
                    MemoryModel.content == memory_content,
                    MemoryModel.superseded_by_id == None,
                    # Narrow to memories created during/after this job enqueue window.
                    MemoryModel.created_at >= job.created_at,
                )
                .order_by(MemoryModel.created_at.desc(), MemoryModel.id.desc())
            )
            if conversation_id is not None:
                q = q.where(MemoryModel.conversation_id == conversation_id)
            new_memory = (await db.execute(q)).scalars().first()
            if new_memory is None:
                await db_mark_mutation_discarded(job_id, db)
                return JSONResponse({"message": "Mutation already discarded", "job_id": job_id})
            new_memory_id = new_memory.id
            await delete_memory_service(new_memory_id, user.id, user.collection_name, db)

        elif action == "update" or action == "merge":
            target_memory_ids = payload.get("target_memory_ids") or []
            if not target_memory_ids:
                raise HTTPException(status_code=400, detail="Invalid payload: target_memory_ids is required for update/merge rollback")

            old_memory = await db_get_memory_by_id_service(target_memory_ids[0], user.id, db)
            new_memory_id = old_memory.superseded_by_id
            if new_memory_id is None:
                await db_mark_mutation_discarded(job_id, db)
                return JSONResponse({"message": "Mutation already discarded", "job_id": job_id})

            # Ensure all target memories point to the same replacement memory.
            old_memories = []
            for target_memory_id in target_memory_ids:
                target_memory = await db_get_memory_by_id_service(target_memory_id, user.id, db)
                if target_memory.superseded_by_id != new_memory_id:
                    raise HTTPException(status_code=400, detail="Inconsistent superseded_by chain for rollback targets")
                old_memories.append(target_memory)
            await delete_memory_service(new_memory_id, user.id, user.collection_name, db)
            for target_memory in old_memories:
                await db_update_memory(target_memory.id, user.id, db, superseded_by_id=None)
            set_memory_superseded_flag(
                collection_name=user.collection_name,
                ids=[memory.embedding_id for memory in old_memories],
                is_superseded=False,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported action for discard: {action}")

        await db_mark_mutation_discarded(job_id, db)
        return JSONResponse({"message": "Mutation discarded successfully", "job_id": job_id})
    except HTTPException:
        raise
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