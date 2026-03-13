from app.models import MemoryCreate
from app.services.qdrant_service import add_point, search_points, search_points_raw, get_point_vectors, delete_points
from app.services.db_service import db_create_memory, db_get_memory_by_embedding_id, db_get_memory_by_content, db_get_memory_by_id, db_update_memory, db_delete_memory
from app.models import Memory, MemoryUpdate
from app.db_models import MemoryModel, MemoryType
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
def check_similar_memories(content: str, dense_embedding: list[float], user_id: int, collection_name: str, limit: int = 5):
    try:
        similar_memories = []
        raw = search_points_raw(
            collection_name=collection_name,
            query=content,
            dense_query_vector=dense_embedding,
            limit=limit,
            user_id=user_id,
        )
        for point in (raw.points or []):
            score = getattr(point, "score", None)
            payload = getattr(point, "payload", None) or {}
            if score is None:
                continue
            if score > 0.9:
                existing_content = payload.get("content")
                if existing_content and existing_content != content:
                    similar_memories.append({"id": point.id, "content": existing_content, "similarity": score})
        if len(similar_memories) > 0:
            return similar_memories
        else:
            return []
    except Exception as e:
        raise Exception(f"Error checking similar memories: {e}")

def db_memory_to_memory(db_memory: MemoryModel) -> Memory:
    return Memory(
        id=db_memory.id,
        content=db_memory.content,
        summary_long=db_memory.summary_long,
        embedding_id=db_memory.embedding_id,
        memory_type=db_memory.memory_type.value,
        conversation_id=db_memory.conversation_id,
        user_id=db_memory.user_id,
        importance_score=db_memory.importance_score,
        tags=db_memory.tags,
        memory_category=getattr(db_memory, "memory_category", None),
        related_memories=db_memory.related_memories,
        last_accessed_at=db_memory.last_accessed_at,
        last_updated_at=db_memory.last_updated_at,
        created_at=db_memory.created_at,
        updated_at=db_memory.updated_at,
    )

async def create_memory(memory: MemoryCreate, dense_embedding: list[float], user_id: int, collection_name: str, db: AsyncSession, bypass_similarity_check: bool = False):
    try:
        should_deduplicate = not bypass_similarity_check and memory.memory_category != "event"
        if should_deduplicate:
            exact_match = await db_get_memory_by_content(memory.content, user_id, db)
            if exact_match:
                return {
                    "memory": db_memory_to_memory(exact_match),
                    "is_duplicate": True,
                    "duplicate_type": "exact"
                }
            similar_memories = check_similar_memories(memory.content, dense_embedding, user_id=user_id, collection_name=collection_name)
            if len(similar_memories) > 0:
                similar_memory = similar_memories[0]
                db_similar_memory = await db_get_memory_by_embedding_id(similar_memory["id"], user_id, db)
                return {
                    "memory": db_memory_to_memory(db_similar_memory),
                    "is_duplicate": True,
                    "duplicate_type": "semantic"
                }

        conversation_id = memory.conversation_id if memory.conversation_id and memory.conversation_id != 0 else None

        metadata = memory.model_dump(exclude={"summary_long"})
        metadata["user_id"] = user_id
        metadata["conversation_id"] = conversation_id
        metadata["is_superseded"] = False 

        memory_point = add_point(collection_name=collection_name, dense_embedding=dense_embedding, metadata=metadata)

        db_memory = await db_create_memory(MemoryModel(
            content=memory.content,
            summary_long=memory.summary_long,
            embedding_id=memory_point.id,
            memory_type=MemoryType(memory.memory_type),
            conversation_id=conversation_id,
            user_id=user_id,
            importance_score=memory.importance_score,
            tags=memory.tags,
        ), db)
        return {
            "memory": db_memory_to_memory(db_memory),
            "is_duplicate": False,
            "duplicate_type": None
        }
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error creating memory: {e}")

async def get_memory_by_query(query: str, dense_query_vector: list[float], collection_name: str, user_id: int, db: AsyncSession) -> List[dict]:
    try:
        queried_memories = search_points(collection_name=collection_name, query=query, dense_query_vector=dense_query_vector,limit=15, user_id=user_id)
        memories = []
        for memory in queried_memories:
            try:
                db_memory = await db_get_memory_by_embedding_id(memory["id"],user_id,db)
                memories.append({"memory": db_memory_to_memory(db_memory), "similarity": memory["similarity"]})
            except ValueError:
                continue
        
        return sorted(memories, key=lambda x: x["similarity"], reverse=True)
    
    except Exception as e:
        raise Exception(f"Error getting memories by query: {e}")

async def update_memory(memory_id: int, memory: MemoryUpdate, dense_embedding: Optional[list[float]], user_id: int, collection_name: str, db: AsyncSession):
    try:
        db_memory = await db_get_memory_by_id(memory_id, user_id, db)
        updates = memory.model_dump(exclude_unset=True)
        
        is_superseded = True if updates.get("superseded_by_id") else False

        memory_type = db_memory.memory_type
        payload = {
            "user_id": user_id,
            "conversation_id": updates.get("conversation_id", db_memory.conversation_id),
            "content": updates.get("content", db_memory.content),
            "memory_type": memory_type.value,
            "importance_score": updates.get("importance_score", db_memory.importance_score),
            "tags": updates.get("tags", db_memory.tags or []),
            "is_superseded": is_superseded,
        }
        current_dense, _ = get_point_vectors(collection_name, db_memory.embedding_id)
        dense_to_use = dense_embedding if dense_embedding is not None else current_dense
        add_point(collection_name=collection_name, dense_embedding=dense_to_use, metadata=payload, id=db_memory.embedding_id)

        updates.pop("memory_type", None)
        db_updates = dict(updates)
        await db_update_memory(memory_id, user_id, db, **db_updates)
        updated = await db_get_memory_by_id(memory_id, user_id, db)
        return db_memory_to_memory(updated)
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error updating memory: {e}")

async def delete_memory(memory_id: int, user_id: int, collection_name: str, db: AsyncSession):
    try:
        deleted = await db_delete_memory(memory_id, user_id, db)
        delete_points(collection_name=collection_name, ids=[deleted.embedding_id])
        return deleted
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error deleting memory: {e}")
