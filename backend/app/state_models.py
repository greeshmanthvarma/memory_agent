from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class QueryAnalysis(BaseModel):
    query: str
    analysis: str

class ContradictionDetection(BaseModel):
    query: str
    contradiction: str
    created_at: datetime = Field(default_factory=datetime.now)