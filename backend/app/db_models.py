from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, ARRAY, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid
from app.database import Base


class MemoryType(str, enum.Enum):
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class MemoryModel(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    summary_long = Column(Text, nullable=True)
    embedding_id = Column(uuid.UUID, nullable=False)
    memory_type = Column(SQLEnum(MemoryType), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    user_id = Column(Integer, nullable=False, index=True)
    importance_score = Column(Float, default=0.0)
    tags = Column(ARRAY(String), default=list)
    related_memories = Column(ARRAY(Integer), default=list)
    last_accessed_at = Column(DateTime, nullable=True)
    last_updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="memories")
    messages = relationship("MessageModel", back_populates="conversation")


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
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    memories = relationship("MemoryModel", back_populates="conversation", foreign_keys=[MemoryModel.conversation_id])
    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email =Column(String, nullable=False, unique=True)
    password =Column(String, nullable=True)
    username =Column(String, nullable=False, unique=True)
    collection_name =Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    memories = relationship("MemoryModel", back_populates="user", foreign_keys=[MemoryModel.user_id])
    conversations = relationship("ConversationModel", back_populates="user", foreign_keys=[ConversationModel.user_id])