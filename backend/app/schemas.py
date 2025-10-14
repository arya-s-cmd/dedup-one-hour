from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ComplaintIn(BaseModel):
    external_id: Optional[str]=None
    name: Optional[str]=None
    phone: Optional[str]=None
    email: Optional[str]=None
    timestamp: Optional[str]=None
    text: Optional[str]=None

class ComplaintOut(ComplaintIn):
    id: int

class GroupOut(BaseModel):
    id: int
    status: str
    score_summary: Optional[str]
    members: List[ComplaintOut]
    top_evidence: Dict[str, Any] = Field(default_factory=dict)

class DecisionIn(BaseModel):
    decision: str  # approve|keep_separate|merge_into
    actor: str
    target_canonical_id: Optional[int] = None
