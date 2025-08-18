"""
Pydantic models for request/response schemas.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class InterviewStartRequest(BaseModel):
    role_id: str

class InterviewAnswerRequest(BaseModel):
    answer: str

class InterviewSession(BaseModel):
    session_id: str
    user_email: str
    role_id: str
    status: str = "started"  # started|ended|scored
    user_action: str = "none"  # none|ended_manually|timeout
    started_at: str  # UTC ISO timestamp
    ended_at: Optional[str] = None
    expires_at: float  # UTC timestamp
    duration_minutes: int
    questions_asked: int = 0
    current_question: Optional[str] = None
    question_metadata: Optional[Dict[str, Any]] = None
    role_title: Optional[str] = None
    role_description: Optional[str] = None
    total_score: Optional[int] = None
    last_updated: Optional[str] = None

class UserRoleLookup(BaseModel):
    session_id: str
    user_session_key: str
    agent_session_key: str
    created_at: str
    last_updated: str

class RoleCreateRequest(BaseModel):
    title: str
    description: str
    status: str = "open"  # open, closed, on_hold
    duration: int = 30  # duration in minutes

class RoleResponse(BaseModel):
    role_id: str
    title: str
    description: str
    short_description: str
    status: str
    duration: int
    created_at: str
    created_by: str

class UserUpdateRequest(BaseModel):
    admin: Optional[bool] = None
    blocked: Optional[bool] = None
    notes: Optional[str] = None