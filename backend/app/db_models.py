from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, ARRAY, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid
from app.database import Base


class MemoryType(str, enum.Enum):
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    PHOTO = "photo"
    CALENDER = "calender"

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class MemoryModel(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    summary_long = Column(Text, nullable=True)
    embedding_id = Column(UUID(as_uuid=True), nullable=False)
    memory_type = Column(SQLEnum(MemoryType), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    importance_score = Column(Float, default=0.0)
    tags = Column(ARRAY(String), default=list)
    memory_category = Column(String(32), nullable=True, index=True)
    related_memories = Column(ARRAY(Integer), default=list)
    superseded_by_id = Column(Integer, ForeignKey("memories.id"), nullable=True, index=True)
    last_accessed_at = Column(DateTime, nullable=True)
    last_updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="memories", foreign_keys=[conversation_id])
    user = relationship("UserModel", back_populates="memories", foreign_keys=[user_id])


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    role = Column(SQLEnum(MessageRole), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="messages")


class ConversationModel(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True)
    thread_id = Column(String, nullable=True, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    memories = relationship("MemoryModel", back_populates="conversation", foreign_keys=[MemoryModel.conversation_id])
    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("UserModel", back_populates="conversations", foreign_keys=[user_id])



class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email =Column(String, nullable=False, unique=True)
    password =Column(String, nullable=True)
    profile_picture =Column(String, nullable=True)
    username =Column(String, nullable=False, unique=True)
    collection_name =Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    memories = relationship("MemoryModel", back_populates="user", foreign_keys=[MemoryModel.user_id])
    conversations = relationship("ConversationModel", back_populates="user", foreign_keys=[ConversationModel.user_id])

class EvalsModel(Base):
    __tablename__ = "evals"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    thread_id = Column(String, nullable=True, index=True)  
    node_name = Column(String, nullable=False, index=True)
    started_at = Column(DateTime, nullable=False)
    duration_ms = Column(Float, nullable=False)


class MemoryMutationQueueModel(Base):
    __tablename__ = "memory_mutation_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    collection_name = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)  # ReflectionOutput as dict
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, processing, done, failed
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)