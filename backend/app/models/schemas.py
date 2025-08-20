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

# User Profile Schemas (Legacy - Phase 1)
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

# Phase 2: Profile Schemas for Role Matching
class ProfileAnalysisResponse(BaseModel):
    """Response schema for profile analysis from LLM."""
    categories: List[str] = Field(..., description="Business categories (max 3, ordered by relevance)")
    experience_level: str = Field(..., description="Overall experience level")
    years_experience: int = Field(..., description="Total years of professional experience")
    tags: List[str] = Field(..., description="Skills, technologies, and competencies")
    professional_summary: str = Field(..., description="Concise professional summary")
    education_level: Optional[str] = Field(None, description="Highest education level")
    confidence_score: float = Field(..., description="LLM confidence in analysis (0.0-1.0)")
    profile_strength: str = Field(..., description="Overall profile strength assessment")

class ProfileStatusResponse(BaseModel):
    """Quick profile status for dashboards and session management."""
    profile_exists: bool
    profile_complete: bool
    profile_version: int = Field(default=2, description="Profile schema version")
    categories: List[str] = Field(default=[], description="User's business categories")
    experience_level: Optional[str] = Field(None, description="User's experience level")
    tags_count: int = Field(default=0, description="Number of skill tags")
    profile_strength: str = Field(default="average", description="Profile quality assessment")
    confidence_score: float = Field(default=0.0, description="Analysis confidence")
    last_updated: Optional[datetime] = Field(None, description="Last profile update")
    ready_for_matching: bool = Field(default=False, description="Ready for role matching")

class UserProfileV2Response(BaseModel):
    """Phase 2 user profile optimized for role matching."""
    email: str
    name: Optional[str]
    # Phase 2: Three-factor matching data
    categories: List[str] = Field(default=[], description="Business categories")
    experience_level: Optional[str] = Field(None, description="Experience level")
    years_experience: int = Field(default=0, description="Years of experience")
    tags: List[str] = Field(default=[], description="Skill and competency tags")
    # Profile metadata
    professional_summary: Optional[str] = Field(None, description="Professional summary")
    education_level: Optional[str] = Field(None, description="Education level")
    confidence_score: float = Field(default=0.0, description="Analysis confidence")
    profile_strength: str = Field(default="average", description="Profile strength")
    profile_version: int = Field(default=2, description="Profile schema version")
    # Status flags
    is_profile_complete: bool = Field(default=False, description="Profile completeness")
    needs_review: bool = Field(default=False, description="Requires manual review")
    ready_for_matching: bool = Field(default=False, description="Ready for role matching")
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_resume_upload: Optional[datetime] = Field(None, description="Last resume upload")

class ResumeUploadV2Response(BaseModel):
    """Phase 2 resume upload response with profile analysis."""
    upload_success: bool
    filename: str
    minio_path: Optional[str] = None
    profile_analysis: Optional[ProfileAnalysisResponse] = None
    profile_complete: bool = Field(default=False, description="Profile completion status")
    ready_for_matching: bool = Field(default=False, description="Ready for role matching")
    needs_llm_analysis: bool = Field(default=False, description="Requires LLM analysis")
    message: str
    recommendation: Optional[str] = Field(None, description="User guidance message")

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