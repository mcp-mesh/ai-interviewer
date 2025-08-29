"""
User Agent Database Models and Connection Setup
"""

import os
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
import enum
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Integer, text, ForeignKey, Float, ARRAY, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import redis

logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@postgres:5432/ai_interviewer"
)

# Redis Configuration  
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# SQLAlchemy Setup
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis Setup
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)


class User(Base):
    """
    User table - contains only data managed by user_agent.
    Other agents will have their own user tables in their schemas.
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "user_agent"}
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Basic user info
    first_name = Column(String(100), nullable=False, default="")
    last_name = Column(String(100), nullable=False, default="")
    
    # Computed/derived fields
    full_name = Column(String(255), nullable=False, default="")  # computed from first_name + last_name
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=True)
    
    # Basic profile flags (managed by user_agent)
    profile_completed = Column(Boolean, default=False)
    onboarding_completed = Column(Boolean, default=False)
    
    # Store basic preferences as JSONB
    basic_preferences = Column(JSONB, nullable=True)
    
    # Resume relationship (One-to-One)
    resume = relationship("Resume", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    @property
    def has_resume(self) -> bool:
        """Check if user has a resume"""
        return self.resume is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "profile_completed": self.profile_completed,
            "onboarding_completed": self.onboarding_completed,
            "basic_preferences": self.basic_preferences or {},
            # Resume fields
            "has_resume": self.has_resume,
            # Timestamps
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
            "last_active_at": self.last_active_at.isoformat() + "Z" if self.last_active_at else None,
        }


class BackgroundStatus(enum.Enum):
    """Background processing status for resume enhancement"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    ERROR = "error"


class Resume(Base):
    """
    Resume table - contains structured resume data with proper relational design.
    Linked to User table via foreign key relationship.
    """
    __tablename__ = "resumes"
    __table_args__ = {"schema": "user_agent"}
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_agent.users.id"), nullable=False, unique=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)  # MinIO path
    file_size = Column(Integer, nullable=False)  # File size in bytes
    minio_url = Column(Text, nullable=False)  # MinIO URL for agent access
    
    # Processing status
    uploaded_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Core profile fields from AI analysis (matching profile_analysis_tool schema)
    categories = Column(ARRAY(String), nullable=True)  # Business categories (max 3)
    experience_level = Column(String(20), nullable=True)  # intern, junior, mid, senior, lead, principal
    years_experience = Column(Integer, nullable=True)  # 0-50 years
    tags = Column(ARRAY(String), nullable=True)  # Skills, technologies, tools (max 20)
    professional_summary = Column(Text, nullable=True)  # Max 300 chars
    education_level = Column(String(100), nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0.0-1.0 LLM confidence
    profile_strength = Column(String(20), nullable=True)  # excellent, good, average, needs_improvement
    
    # AI processing metadata
    ai_provider = Column(String(50), nullable=True)  # openai, claude, etc.
    ai_model = Column(String(100), nullable=True)  # gpt-4o, claude-3-5-sonnet, etc.
    analysis_enhanced = Column(Boolean, default=False)  # Whether LLM analysis succeeded
    background_status = Column(Enum(BackgroundStatus), default=BackgroundStatus.PENDING)  # Background task status
    
    # Detailed analysis for application prefill (Steps 1 & 2)
    detailed_personal_info = Column(JSONB, nullable=True)  # Step 1: Contact info, URLs, etc.
    detailed_experience_info = Column(JSONB, nullable=True)  # Step 2: Work history, skills, education
    detailed_analysis_completed = Column(Boolean, default=False)  # Whether detailed analysis finished
    detailed_analysis_at = Column(DateTime, nullable=True)  # When detailed analysis completed
    
    # Raw content and basic sections (fallback data)
    text_content = Column(Text, nullable=True)  # Raw extracted text
    basic_sections = Column(JSONB, nullable=True)  # Basic section parsing results
    text_stats = Column(JSONB, nullable=True)  # Text statistics (word count, etc.)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship back to user
    user = relationship("User", back_populates="resume")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "minio_url": self.minio_url,
            # AI Analysis Results
            "categories": self.categories or [],
            "experience_level": self.experience_level,
            "years_experience": self.years_experience,
            "tags": self.tags or [],
            "professional_summary": self.professional_summary,
            "education_level": self.education_level,
            "confidence_score": self.confidence_score,
            "profile_strength": self.profile_strength,
            # AI Metadata
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model,
            "analysis_enhanced": self.analysis_enhanced,
            "background_status": self.background_status.value if self.background_status else "pending",
            # Detailed Analysis for Application Prefill
            "detailed_personal_info": self.detailed_personal_info,
            "detailed_experience_info": self.detailed_experience_info,
            "detailed_analysis_completed": self.detailed_analysis_completed,
            "detailed_analysis_at": self.detailed_analysis_at.isoformat() + "Z" if self.detailed_analysis_at else None,
            # Processing status
            "uploaded_at": self.uploaded_at.isoformat() + "Z" if self.uploaded_at else None,
            "processed_at": self.processed_at.isoformat() + "Z" if self.processed_at else None,
            # Timestamps
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }
    
    def to_structured_analysis(self) -> Dict[str, Any]:
        """Convert to structured_analysis format compatible with existing frontend"""
        return {
            "categories": self.categories or [],
            "experience_level": self.experience_level,
            "years_experience": self.years_experience or 0,
            "tags": self.tags or [],
            "professional_summary": self.professional_summary or "",
            "education_level": self.education_level,
            "confidence_score": self.confidence_score,
            "profile_strength": self.profile_strength,
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model
        }


def create_tables():
    """Create database tables and schema if they don't exist"""
    try:
        # Create schema first
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS user_agent"))
            conn.commit()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False


def get_db_session() -> Session:
    """Get database session"""
    return SessionLocal()


class UserCache:
    """Redis-based caching for user profiles"""
    
    CACHE_PREFIX = "user_profile:"
    DEFAULT_TTL = 3600  # 1 hour
    
    @staticmethod
    def get_cache_key(email: str) -> str:
        return f"{UserCache.CACHE_PREFIX}{email}"
    
    @staticmethod
    def get(email: str) -> Optional[Dict[str, Any]]:
        """Get user profile from cache"""
        try:
            cache_key = UserCache.get_cache_key(email)
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for {email}: {e}")
            return None
    
    @staticmethod
    def set(email: str, user_data: Dict[str, Any], ttl: int = None) -> bool:
        """Set user profile in cache"""
        try:
            cache_key = UserCache.get_cache_key(email)
            ttl = ttl or UserCache.DEFAULT_TTL
            redis_client.setex(cache_key, ttl, json.dumps(user_data))
            logger.info(f"User profile cached for {email}")
            return True
        except Exception as e:
            logger.error(f"Cache set error for {email}: {e}")
            return False
    
    @staticmethod
    def delete(email: str) -> bool:
        """Delete user profile from cache (cache invalidation)"""
        try:
            cache_key = UserCache.get_cache_key(email)
            redis_client.delete(cache_key)
            logger.info(f"Cache invalidated for {email}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for {email}: {e}")
            return False
    
    @staticmethod
    def exists(email: str) -> bool:
        """Check if user profile exists in cache"""
        try:
            cache_key = UserCache.get_cache_key(email)
            return redis_client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Cache exists check error for {email}: {e}")
            return False


def test_connections() -> Dict[str, bool]:
    """Test database and redis connections"""
    results = {"postgres": False, "redis": False}
    
    # Test PostgreSQL
    try:
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        results["postgres"] = True
        logger.info("PostgreSQL connection successful")
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
    
    # Test Redis
    try:
        redis_client.ping()
        results["redis"] = True
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
    
    return results