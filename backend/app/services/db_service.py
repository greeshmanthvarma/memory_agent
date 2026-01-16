from app.db_models import MemoryModel, UserModel
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def db_create_memory(memory: MemoryModel,db: AsyncSession):
    try:
        db.add(memory) #it is a synchronous operation
        await db.commit()
        await db.refresh(memory)
        return memory
    except Exception as e:
        await db.rollback()
        raise Exception(f"Error creating memory: {e}")

async def db_get_memory_by_embedding_id(embedding_id: uuid.UUID,db: AsyncSession):
    try:
        result = await db.execute(select(MemoryModel).filter(MemoryModel.embedding_id == embedding_id))
        memory = result.scalar_one_or_none()
        if not memory:
            raise ValueError(f"Memory with embedding id {embedding_id} not found in the database")
        return memory
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error getting memory by embedding id {embedding_id}: {e}")

async def db_get_all_memories(user_id: int,db: AsyncSession):
    try:
        result = await db.execute(select(MemoryModel).filter(MemoryModel.user_id == user_id))
        memories = result.scalars().all()
        return memories
    except Exception as e:
        raise Exception(f"Error getting all memories for user {user_id}: {e}")

async def db_get_memory_by_id(memory_id: int,db: AsyncSession):
    try:
        result = await db.execute(select(MemoryModel).filter(MemoryModel.id == memory_id))
        memory = result.scalar_one_or_none()
        if not memory:
            raise ValueError(f"Memory with id {memory_id} not found in the database")
        return memory
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error getting memory by id {memory_id}: {e}")