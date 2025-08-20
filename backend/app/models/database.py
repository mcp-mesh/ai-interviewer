"""
SQLAlchemy database models for AI Interviewer system.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Index, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class CompanyLocation(Base):
    """Company office locations for role assignments."""
    __tablename__ = "company_locations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String(50), nullable=False)
    state = Column(String(50))  # Nullable for non-US locations
    city = Column(String(100), nullable=False)
    office_name = Column(String(100))  # "SF HQ", "NYC Office", "Remote"
    remote_allowed = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    
    # Relationships
    roles = relationship("Role", back_populates="location")
    
    __table_args__ = (
        Index('ix_company_locations_country_state_city', 'country', 'state', 'city'),
        Index('ix_company_locations_active', 'active'),
    )

class EmploymentType(Base):
    """Employment types for standardized role classification."""
    __tablename__ = "employment_types"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type_code = Column(String(50), unique=True, nullable=False)  # "full-time", "part-time", "contract", "internship"
    display_name = Column(String(100), nullable=False)  # "Full Time", "Part Time", "Contract", "Internship"
    description = Column(Text)  # Detailed description
    active = Column(Boolean, default=True)
    
    # Relationships
    roles = relationship("Role", back_populates="employment_type")
    
    __table_args__ = (
        Index('ix_employment_types_type_code', 'type_code'),
        Index('ix_employment_types_active', 'active'),
    )

class Role(Base):
    """Job role model with simplified LLM-powered analysis and admin categorization."""
    __tablename__ = "roles"
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(String(50), unique=True, nullable=False, default=lambda: f"role_{uuid.uuid4().hex[:8]}")
    
    # Basic role information
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    short_description = Column(String(500), nullable=False)  # LLM-generated
    
    # Admin-selected categorization
    category = Column(String(50), nullable=False)  # Business categories: investment_management, legal_compliance, etc.
    
    # Reference fields (normalized)
    location_id = Column(Integer, ForeignKey('company_locations.id'), nullable=False)
    employment_type_id = Column(Integer, ForeignKey('employment_types.id'), nullable=False)
    
    # LLM-determined experience requirements
    required_experience_level = Column(String(20), nullable=False)  # "intern", "junior", "mid", "senior", "lead", "principal"
    required_years_min = Column(Integer)           # LLM-determined minimum years
    required_years_max = Column(Integer)           # LLM-determined maximum years
    
    # LLM-generated tags and confidence
    tags = Column(JSON, nullable=False, default=list)  # ["python", "fastapi", "leadership"]
    confidence_score = Column(Float)                    # LLM confidence in analysis (0.0-1.0)
    
    # Administrative fields
    status = Column(String(20), nullable=False, default="open")  # "open", "closed", "on_hold"
    duration = Column(Integer, nullable=False, default=30)       # Interview duration in minutes
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(200), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(200), nullable=False)
    
    # Relationships
    location = relationship("CompanyLocation", back_populates="roles")
    employment_type = relationship("EmploymentType", back_populates="roles")
    interviews = relationship("Interview", back_populates="role", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_roles_category_status', 'category', 'status'),
        Index('ix_roles_location_id', 'location_id'),
        Index('ix_roles_employment_type_id', 'employment_type_id'),
        Index('ix_roles_experience_level', 'required_experience_level'),
        Index('ix_roles_created_at', 'created_at'),
    )

class UserProfile(Base):
    """User profile with simplified three-factor matching data."""
    __tablename__ = "user_profiles"
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), unique=True, nullable=False)
    
    # Basic information
    name = Column(String(200))
    
    # Simplified three-factor matching data
    categories = Column(JSON, nullable=False, default=list)  # ["technology", "sales"] - multi-category support
    overall_experience_level = Column(String(20))  # "intern", "junior", "mid", "senior", "lead", "principal"
    tags = Column(JSON, nullable=False, default=list)  # ["python", "salesforce", "crm"] - simple skill tags
    
    # Additional context (for future enhancements)
    total_years_experience = Column(Integer)        # Total years in industry
    leadership_experience = Column(JSON, default=dict)  # Basic leadership info
    career_progression = Column(JSON, default=list)     # Career history summary
    
    # LLM analysis confidence
    analysis_confidence = Column(Float)  # Overall confidence in profile extraction
    
    # Preferences
    location_preferences = Column(JSON, default=dict)        # {"countries": ["USA"], "remote_ok": True}
    role_type_preferences = Column(JSON, default=list)       # ["full-time", "contract"]
    
    # Resume data
    resume_content = Column(Text)                   # Original resume text
    resume_metadata = Column(JSON, default=dict)   # File info, upload date, etc.
    
    # Profile status
    is_profile_complete = Column(Boolean, default=False)
    
    # Admin flags
    admin = Column(Boolean, default=False)
    blocked = Column(Boolean, default=False)
    admin_notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    interviews = relationship("Interview", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_user_profiles_email', 'email'),
        Index('ix_user_profiles_categories', 'categories'),
        Index('ix_user_profiles_experience_level', 'overall_experience_level'),
        Index('ix_user_profiles_admin', 'admin'),
        Index('ix_user_profiles_updated_at', 'updated_at'),
    )

class Interview(Base):
    """Interview session with comprehensive tracking."""
    __tablename__ = "interviews"
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False)
    
    # Foreign keys
    user_email = Column(String(200), ForeignKey('user_profiles.email'), nullable=False)
    role_id = Column(String(50), ForeignKey('roles.role_id'), nullable=False)
    
    # Interview status and timing
    status = Column(String(20), nullable=False, default="started")  # "started", "in_progress", "completed", "ended_early"
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)              # Actual duration in seconds
    completion_reason = Column(String(50))          # "completed", "timeout", "ended_by_user", "ended_by_system"
    
    # Interview content
    conversation = Column(JSON, default=list)      # Full conversation log
    questions_asked = Column(Integer, default=0)
    
    # Evaluation results
    evaluation = Column(JSON, default=dict)
    # Example: {
    #   "overall_score": 85,
    #   "technical_knowledge": 90,
    #   "problem_solving": 80,
    #   "communication": 85,
    #   "experience_relevance": 80,
    #   "hire_recommendation": "yes",
    #   "feedback": "Strong technical skills...",
    #   "evaluation_timestamp": "2024-01-01T12:30:00Z",
    #   "detailed_scores": {...}
    # }
    
    # Role information at time of interview (for historical accuracy)
    role_snapshot = Column(JSON, default=dict)     # Role data at time of interview
    
    # System metadata
    user_agent = Column(String(500))
    ip_address = Column(String(50))
    interview_metadata = Column(JSON, default=dict)  # Additional tracking data
    
    # Relationships
    user = relationship("UserProfile", back_populates="interviews")
    role = relationship("Role", back_populates="interviews")
    
    # Indexes
    __table_args__ = (
        Index('ix_interviews_user_email', 'user_email'),
        Index('ix_interviews_role_id', 'role_id'),
        Index('ix_interviews_status', 'status'),
        Index('ix_interviews_started_at', 'started_at'),
        Index('ix_interviews_session_id', 'session_id'),
    )

class RoleMatchHistory(Base):
    """Track role recommendation history for analytics."""
    __tablename__ = "role_match_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(200), nullable=False)
    role_id = Column(String(50), nullable=False)
    
    # Match scoring
    match_score = Column(JSON, nullable=False)  # Full match analysis
    recommended_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # User actions
    viewed = Column(Boolean, default=False)
    applied = Column(Boolean, default=False)  # Started interview
    completed_interview = Column(Boolean, default=False)
    
    # Analytics
    user_feedback = Column(String(20))  # "relevant", "not_relevant", "overqualified", "underqualified"
    
    __table_args__ = (
        Index('ix_role_match_user_email', 'user_email'),
        Index('ix_role_match_role_id', 'role_id'),
        Index('ix_role_match_recommended_at', 'recommended_at'),
    )