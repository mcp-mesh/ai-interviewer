"""
Pydantic models for request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

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

# Simplified Role Schemas
class RoleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    category: str = Field(..., description="Business category selected by admin")
    location_id: int = Field(..., description="Reference to company_locations table")
    type: str = Field(..., description="Employment type code")
    duration: int = Field(default=30, ge=10, le=120, description="Interview duration in minutes")

class RoleUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    category: Optional[str] = Field(None, description="Business category")
    location_id: Optional[int] = Field(None, description="Reference to company_locations table")
    type: Optional[str] = Field(None, description="Employment type code")
    status: Optional[str] = Field(None, description="Role status")
    duration: Optional[int] = Field(None, ge=10, le=120, description="Interview duration in minutes")

class RoleResponse(BaseModel):
    role_id: str
    title: str
    description: str
    short_description: str
    category: str
    type: str
    location: Dict[str, Any]  # Includes country, state, city, office_name from locations table
    required_experience_level: str
    required_years_min: Optional[int]
    required_years_max: Optional[int]
    tags: List[str]
    confidence_score: Optional[float]
    status: str
    duration: int
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str

class RoleListResponse(BaseModel):
    roles: List[RoleResponse]
    total_count: int
    page: int
    limit: int

# User Profile Schemas
class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    location_preferences: Optional[Dict[str, Any]] = None
    role_type_preferences: Optional[List[str]] = None
    category_preferences: Optional[List[str]] = None
    preferred_experience_levels: Optional[List[str]] = None

class UserProfileResponse(BaseModel):
    email: str
    name: Optional[str]
    overall_experience_level: Optional[str]
    total_years_experience: Optional[int]
    skills: Dict[str, Dict[str, Any]]
    leadership_experience: Dict[str, Any]
    career_progression: List[Dict[str, Any]]
    preferred_experience_levels: List[str]
    location_preferences: Dict[str, Any]
    role_type_preferences: List[str]
    category_preferences: List[str]
    is_profile_complete: bool
    created_at: datetime
    updated_at: datetime

# Role Matching Schemas
class RoleMatchResponse(BaseModel):
    role: RoleResponse
    match_score: float
    recommendation: str
    match_details: Dict[str, Any]
    reasons: List[str]

class RecommendedRolesResponse(BaseModel):
    recommended_roles: List[RoleMatchResponse]
    user_profile_summary: Dict[str, Any]
    total_matches: int

# Resume Upload Schema
class ResumeUploadResponse(BaseModel):
    success: bool
    message: str
    profile_extracted: bool
    skills_count: int
    confidence_scores: Dict[str, float]

class UserUpdateRequest(BaseModel):
    admin: Optional[bool] = None
    blocked: Optional[bool] = None
    notes: Optional[str] = None

# Interview Schemas
class InterviewDetailResponse(BaseModel):
    session_id: str
    candidate: Dict[str, Any]
    interview: Dict[str, Any]
    role_info: Dict[str, Any]
    conversation: List[Dict[str, Any]]
    evaluation: Dict[str, Any]

class RoleStatistics(BaseModel):
    total_interviews: int
    average_score: float
    strong_yes_count: int
    yes_count: int
    hire_rate: float

class RoleDetailResponse(BaseModel):
    role: RoleResponse
    interviews: List[Dict[str, Any]]
    statistics: RoleStatistics