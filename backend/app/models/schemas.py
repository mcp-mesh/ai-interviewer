"""
Phase 2 Backend - Pydantic Models and Schemas

Job-related request/response models matching frontend expectations.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class JobFilters(BaseModel):
    """Job listing filters"""
    category: Optional[str] = None
    location: Optional[str] = None
    experience_level: Optional[str] = None
    job_type: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class JobSummary(BaseModel):
    """Job summary for listings - matches frontend expected format"""
    id: str
    title: str
    company: str
    location: str
    type: str  # "Full-time", "Part-time", "Contract", "Remote"
    category: str
    description: Optional[str] = None
    requirements: List[str] = []
    benefits: List[str] = []
    salaryRange: Optional[Dict[str, Any]] = None  # {min, max, currency}
    remote: bool = False
    postedAt: str
    matchScore: Optional[int] = None


class JobDetail(BaseModel):
    """Detailed job information"""
    id: str
    title: str
    company: str
    location: str
    job_type: str
    experience_level: Optional[str] = None
    category: str
    salary_range: Optional[str] = None
    posted_date: str
    application_deadline: Optional[str] = None
    description: str
    requirements: List[str]
    responsibilities: List[str] = []
    benefits: List[str] = []
    skills_required: List[str] = []
    is_featured: bool = False
    company_info: Optional[Dict[str, Any]] = None


class JobCategory(BaseModel):
    """Job category information"""
    category: str
    count: int


class JobListResponse(BaseModel):
    """Job listing API response"""
    data: List[JobSummary]
    total: int
    page: int
    limit: int
    success: bool = True


class JobDetailResponse(BaseModel):
    """Job detail API response"""
    data: JobDetail
    success: bool = True


class JobCategoriesResponse(BaseModel):
    """Job categories API response"""
    data: List[JobCategory]
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response format"""
    success: bool = False
    error: str
    code: Optional[str] = None


# Application-related schemas
class ApplicationSubmission(BaseModel):
    """Application submission request"""
    job_id: str
    notes: str
    cover_letter: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class ApplicationSummary(BaseModel):
    """Application summary for listings"""
    id: str
    userId: str
    jobId: str
    status: str  # "submitted", "under-review", "interview_scheduled", "rejected", "hired"
    submittedAt: str
    notes: Optional[str] = None
    interview_date: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApplicationDetail(BaseModel):
    """Detailed application information"""
    id: str
    userId: str
    jobId: str
    status: str
    submittedAt: str
    notes: Optional[str] = None
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None
    interview_date: Optional[str] = None
    rejection_reason: Optional[str] = None
    admin_notes: Optional[str] = None
    status_updated_at: Optional[str] = None


class ApplicationListResponse(BaseModel):
    """Application listing API response"""
    data: List[ApplicationSummary]
    total: int
    page: int
    limit: int
    success: bool = True


class ApplicationDetailResponse(BaseModel):
    """Application detail API response"""
    data: ApplicationDetail
    success: bool = True


class ApplicationStatusUpdate(BaseModel):
    """Application status update request"""
    status: str
    admin_notes: Optional[str] = None


# User-related schemas
class UserProfile(BaseModel):
    """User profile information"""
    skills: List[str] = []
    experience_years: int = 0
    location: str = ""
    resume_url: Optional[str] = None
    bio: Optional[str] = ""
    phone: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""


class UserPreferences(BaseModel):
    """User job preferences"""
    job_types: List[str] = []
    locations: List[str] = []
    salary_min: int = 0
    salary_max: int = 0
    categories: List[str] = []


class UserData(BaseModel):
    """Complete user data"""
    id: str
    name: str
    email: str
    hasResume: bool = False
    isResumeAvailable: bool = False
    profile: UserProfile
    preferences: Optional[UserPreferences] = None
    availableJobs: int = 0
    matchedJobs: int = 0
    applications: List[str] = []
    createdAt: str
    updatedAt: str


class UserProfileResponse(BaseModel):
    """User profile API response"""
    data: UserData
    success: bool = True


class UserProfileUpdate(BaseModel):
    """User profile update request"""
    name: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None


# File-related schemas
class FileUploadData(BaseModel):
    """File upload metadata"""
    filename: str
    file_size: int
    content_type: str = "application/pdf"


class ProcessedResumeData(BaseModel):
    """Processed resume data"""
    skills_extracted: List[str] = []
    experience_years: int = 0
    education: List[Dict[str, Any]] = []
    work_experience: List[Dict[str, Any]] = []
    contact_info: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    confidence_score: float = 0.0
    processing_time: float = 0.0


class FileUploadResult(BaseModel):
    """File upload result"""
    file_id: str
    filename: str
    file_path: str
    file_size: int
    content_type: str
    uploaded_at: str
    user_email: str


class FileUploadResponse(BaseModel):
    """File upload API response"""
    success: bool = True
    upload: FileUploadResult
    processed_data: Optional[ProcessedResumeData] = None
    profile_updated: bool = False
    message: str