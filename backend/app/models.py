from datetime import datetime
from typing import List, Literal, Optional
import uuid
from pydantic import BaseModel, Field


class Memory(BaseModel):
    id: int
    content: str
    summary_long: Optional[str] = None
    embedding_id: uuid.UUID
    memory_type: Literal["explicit", "implicit"]
    conversation_id: Optional[int] = None
    user_id: int
    importance_score: float = 0.0
    tags: List[str] = Field(default_factory=list)
    related_memories: List[int] = Field(default_factory=list)
    last_accessed_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MemoryCreate(BaseModel):
    content: str
    summary_long: Optional[str] = None
    memory_type: Literal["explicit", "implicit"]
    conversation_id: Optional[int] = None
    importance_score: float = 0.0
    tags: List[str] = Field(default_factory=list)


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    embedding_id: Optional[uuid.UUID] = None
    memory_type: Optional[Literal["explicit", "implicit"]] = None
    importance_score: Optional[float] = None
    tags: Optional[List[str]] = None


class Message(BaseModel):
    id: int
    content: str
    role: Literal["user", "assistant"]
    created_at: datetime
    updated_at: datetime

class MessageCreate(BaseModel):
    content: str
    role: Literal["user", "assistant"]
    conversation_id: Optional[int] = None

class ConversationRead(BaseModel):
    id: int
    title: Optional[str] = None
    memory_id: Optional[int] = None
    messages: List[Message] = Field(default_factory=list)
    user_id: int
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    id: int
    title: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    user_id: int
    created_at: datetime
    updated_at: datetime


class UserRegister(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    identifier: str
    password: str

class SummarizeRequest(BaseModel):
    messages: List[Message]
    conversation_id: Optional[int] = None  
    create_memory: bool = True
    tags: List[str] = Field(default_factory=list)