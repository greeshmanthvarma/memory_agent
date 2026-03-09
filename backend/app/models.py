from datetime import datetime
from typing import List, Literal, Optional
import uuid
from pydantic import BaseModel, Field
from app.state_models import ReflectionOutput


class Memory(BaseModel):
    id: int
    content: str
    summary_long: Optional[str] = None
    embedding_id: uuid.UUID
    memory_type: Literal["explicit", "implicit", "photo", "calender"]
    conversation_id: Optional[int] = None
    user_id: int
    importance_score: float = 0.0
    tags: List[str] = Field(default_factory=list)
    memory_category: Optional[Literal["fact", "preference", "event"]] = None
    related_memories: List[int] = Field(default_factory=list)
    last_accessed_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MemoryCreate(BaseModel):
    content: str
    summary_long: Optional[str] = None
    memory_type: Literal["explicit", "implicit", "photo", "calender"]
    conversation_id: Optional[int] = None
    importance_score: float = 0.0
    tags: List[str] = Field(default_factory=list)
    memory_category: Optional[Literal["fact", "preference", "event"]] = None


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    superseded_by_id: Optional[int] = None
    memory_category: Optional[Literal["fact", "preference", "event"]] = None
    summary_long: Optional[str] = None
    conversation_id: Optional[int] = None
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
    thread_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    id: int
    title: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    user_id: int
    thread_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UserRegister(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    identifier: str
    password: str

class ChatRequest(BaseModel):
    user_message: str
    conversation_id: int

class SummarizeRequest(BaseModel):
    messages: List[Message]
    conversation_id: Optional[int] = None  
    create_memory: bool = True
    tags: List[str] = Field(default_factory=list)

class UpdateProfileRequest(BaseModel):
    profile_picture: Optional[str] = None
    username: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None


class TitleFromMessageRequest(BaseModel):
    first_message: str

class MemoryMutationQueue(BaseModel):
    id: int
    payload: ReflectionOutput
    status: Literal["pending", "processing", "done", "failed"]
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None