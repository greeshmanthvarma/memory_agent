from app.db_models import MemoryModel, MessageModel, UserModel, ConversationModel
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

async def db_get_memory_by_embedding_id(embedding_id: uuid.UUID, user_id: int, db: AsyncSession):
    try:
        result = await db.execute(
            select(MemoryModel)
            .filter(MemoryModel.embedding_id == embedding_id)
            .filter(MemoryModel.user_id == user_id)
            .filter(MemoryModel.superseded_by_id == None)
        )
        memory = result.scalar_one_or_none()
        if not memory:
            raise ValueError(f"Memory with embedding id {embedding_id} not found in the database")
        return memory
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error getting memory by embedding id {embedding_id}: {e}")

async def db_get_all_memories(user_id: int, db: AsyncSession):
    try:
        result = await db.execute(
            select(MemoryModel)
            .filter(MemoryModel.user_id == user_id)
            .filter(MemoryModel.superseded_by_id == None)
            .order_by(MemoryModel.created_at.desc())
        )
        memories = result.scalars().all()
        return memories
    except Exception as e:
        raise Exception(f"Error getting all memories for user {user_id}: {e}")

async def db_get_memory_by_id(memory_id: int,user_id: int,db: AsyncSession):
    try:
        result = await db.execute(select(MemoryModel).filter(MemoryModel.id == memory_id).filter(MemoryModel.user_id == user_id))
        memory = result.scalar_one_or_none()
        if not memory:
            raise ValueError(f"Memory with id {memory_id} not found in the database")
        return memory
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error getting memory by id {memory_id}: {e}")

async def db_update_memory(memory_id: int, user_id: int, db: AsyncSession, **updates):
    try:
        db_memory = await db_get_memory_by_id(memory_id, user_id, db)
        for key, value in updates.items():
            if hasattr(db_memory, key):
                setattr(db_memory, key, value)
        await db.commit()
        await db.refresh(db_memory)
        return db_memory
    except ValueError:
        raise
    except Exception as e:
        await db.rollback()
        raise Exception(f"Error updating memory {memory_id}: {e}")


async def db_update_memory_superseded_by(memory_id: int, superseded_by_id: int, user_id: int, db: AsyncSession):
    """Set superseded_by_id on a memory (e.g. when it's replaced by another)."""
    try:
        db_memory = await db_get_memory_by_id(memory_id, user_id, db)
        db_memory.superseded_by_id = superseded_by_id
        await db.commit()
        await db.refresh(db_memory)
        return db_memory
    except ValueError:
        raise
    except Exception as e:
        await db.rollback()
        raise Exception(f"Error setting superseded_by_id on memory {memory_id}: {e}")

async def db_get_memory_by_content(content: str, user_id: int, db: AsyncSession):
    try:
        result = await db.execute(
            select(MemoryModel)
            .filter(MemoryModel.content == content)
            .filter(MemoryModel.user_id == user_id)
            .filter(MemoryModel.superseded_by_id == None)
        )
        memory = result.scalar_one_or_none()
        return memory
    except Exception as e:
        raise Exception(f"Error getting memory by content: {e}")

async def db_create_conversation(conversation: ConversationModel, db: AsyncSession):
    try:
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation
    except Exception as e:
        await db.rollback()
        raise Exception(f"Error creating conversation: {e}")

async def db_create_message(message: MessageModel, db: AsyncSession):
    try:
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message
    except Exception as e:
        await db.rollback()
        raise Exception(f"Error creating message: {e}")

async def db_get_conversation(conversation_id: int, user_id: int, db: AsyncSession):
    try:
        result = await db.execute(select(ConversationModel).filter(ConversationModel.id == conversation_id).filter(ConversationModel.user_id == user_id))
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise ValueError(f"Conversation with id {conversation_id} not found in the database")
        return conversation
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error getting conversation by id {conversation_id}: {e}")

async def db_get_conversation_messages(conversation_id: int, db: AsyncSession):
    try:
        result = await db.execute(select(MessageModel).filter(MessageModel.conversation_id == conversation_id).order_by(MessageModel.created_at))
        return result.scalars().all()
    except Exception as e:
        raise Exception(f"Error getting conversation messages by id {conversation_id}: {e}")

async def db_get_all_conversations(user_id: int, db: AsyncSession):
    try:
        result = await db.execute(select(ConversationModel).filter(ConversationModel.user_id == user_id).order_by(ConversationModel.updated_at.desc()))
        conversations = result.scalars().all()
        return conversations
    except Exception as e:
        raise Exception(f"Error getting all conversations for user {user_id}: {e}")

async def db_delete_conversation(conversation_id: int, user_id: int, db: AsyncSession):
    try:
        result = await db.execute(select(ConversationModel).filter(ConversationModel.id == conversation_id).filter(ConversationModel.user_id == user_id))
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise ValueError(f"Conversation with id {conversation_id} not found in the database")
        await db.delete(conversation)
        await db.commit()
        return True
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error deleting conversation by id {conversation_id}: {e}")

async def db_update_conversation(conversation_id: int, title: str, user_id: int, db: AsyncSession):
    try:
        result = await db.execute(select(ConversationModel).filter(ConversationModel.id == conversation_id).filter(ConversationModel.user_id == user_id))
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise ValueError(f"Conversation with id {conversation_id} not found in the database")
        conversation.title = title
        await db.commit()
        await db.refresh(conversation)
        return True
    except ValueError:
        raise
    except Exception as e:
        await db.rollback()
        raise Exception(f"Error updating conversation by id {conversation_id}: {e}")