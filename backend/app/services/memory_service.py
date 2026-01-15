from app.models import MemoryCreate
from app.services.embedding_service import embed_text
from app.services.qdrant_service import add_point, search_points
from app.services.db_service import db_create_memory
from app.db_models import MemoryModel

def check_similar_memories(content: str, embedding: list[float], limit: int = 3):
    try:
        similar_memories = []
        memories = search_points(collection_name="memories", query_vector=embedding, limit=limit)
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

def create_memory(memory: MemoryCreate,embedding: list[float],bypass_similarity_check: bool = False):
    try:
        similar_memories = check_similar_memories(memory.content,embedding)
        if len(similar_memories) > 0 and not bypass_similarity_check:
            return similar_memories[0]
        else:
            memory = add_point(collection_name="memories", embedding=embedding, metadata=memory.model_dump())
            db_create_memory(MemoryModel(
                content=memory.content,
                embedding_id=memory.embedding_id,
                memory_type=memory.memory_type,
                conversation_id=memory.conversation_id,
                user_id=memory.user_id,
                importance_score=memory.importance_score,
                tags=memory.tags,
            ))
            return memory 
    except Exception as e:
        raise Exception(f"Error creating memory: {e}")
