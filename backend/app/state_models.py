from typing import TypedDict, Optional, Annotated, Literal
import uuid
from pydantic import BaseModel
from langgraph.graph.message import add_messages



class GraphState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    run_id: str
    thread_id: str
    user_id: int
    user_message : str
    # Query analysis
    intent: Literal["general_knowledge","personal", "ambiguous"]
    retrieval_query: str
    filters: dict
    retry_feedback: str
    # Retrieval
    retrieval_results: list
    retry_count: int
    # Reflection / mutation
    memory_action: Optional[dict]
    last_mutation: Optional[dict]
    
class QueryAnalysisOutput(BaseModel):
    intent: Literal["general_knowledge", "personal", "ambiguous"]
    retrieval_query: str | None = None
    filters: dict = {} 

class ReflectionOutput(BaseModel):
    action: Literal["none", "create", "update", "merge"]
    reasoning: str
    memory_content: str | None = None
    target_memory_ids: list[str] = []
    memory_category: Literal["fact", "preference", "event"] | None = None
    tags: list[str] = []

class ReflectionInput(BaseModel):
    user_message: str
    assistant_response: str
    retrieval_results: list
