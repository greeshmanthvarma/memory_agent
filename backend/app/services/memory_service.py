from app.models import MemoryCreate
from app.services.qdrant_service import add_point, search_points
from app.services.db_service import db_create_memory, db_get_memory_by_embedding_id
from app.models import Memory
from app.db_models import MemoryModel, MemoryType
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

def check_similar_memories(content: str, embedding: list[float], user_id: int, collection_name: str, limit: int = 3):
    try:
        similar_memories = []
        memories = search_points(collection_name=collection_name, query_vector=embedding, limit=limit, user_id=user_id)
        for memory in memories:
            if memory["similarity"] > 0.9:
                if memory["content"] != content:
                    similar_memories.append(memory)
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
        embedding_id=db_memory.embedding_id,
        memory_type=db_memory.memory_type.value,
        conversation_id=db_memory.conversation_id,
        user_id=db_memory.user_id,
        importance_score=db_memory.importance_score,
        tags=db_memory.tags,
        related_memories=db_memory.related_memories,
        last_accessed_at=db_memory.last_accessed_at,
        last_updated_at=db_memory.last_updated_at,
        created_at=db_memory.created_at,
        updated_at=db_memory.updated_at,
    )

async def create_memory(memory: MemoryCreate,embedding: list[float],user_id: int,collection_name: str,db: AsyncSession,bypass_similarity_check: bool = False):
    try:
        similar_memories = check_similar_memories(memory.content,embedding,user_id=user_id,collection_name=collection_name)
        if len(similar_memories) > 0 and not bypass_similarity_check:
            similar_memory = similar_memories[0]
            db_similar_memory = await db_get_memory_by_embedding_id(similar_memory["id"],user_id,db)
            return db_memory_to_memory(db_similar_memory)
        else:
          memory_point = add_point(collection_name=collection_name, embedding=embedding, metadata=memory.model_dump())
          db_memory = await db_create_memory(MemoryModel(
            content=memory.content,
            embedding_id=memory_point.id,
            memory_type=MemoryType(memory.memory_type),
            conversation_id=memory.conversation_id,
            user_id=memory.user_id,
            importance_score=memory.importance_score,
            tags=memory.tags,
          ),db)
          return db_memory_to_memory(db_memory)
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error creating memory: {e}")

async def get_memory_by_query(query_vector: list[float], collection_name: str, user_id: int, db: AsyncSession) -> List[dict]:
    try:
        queried_memories = search_points(collection_name=collection_name, query_vector=query_vector, limit=10, user_id=user_id)
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
