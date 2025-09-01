"""
Application Agent Database Models and Connection Setup

Following the user_agent pattern with application_agent schema.
Includes main application table and step-specific tables for the 6-step wizard flow.
"""

import os
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Integer, text, ForeignKey, Float, ARRAY
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import redis

logger = logging.getLogger(__name__)

# Application Status Enum
class ApplicationStatus(Enum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    SUBMITTED = "SUBMITTED"
    QUALIFIED = "QUALIFIED"
    INTERVIEW_STARTED = "INTERVIEW_STARTED"
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED" 
    INPROGRESS = "INPROGRESS"  # For active interviews
    DECISION_PENDING = "DECISION_PENDING"

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://mcpmesh:mcpmesh123@postgres:5432/ai_interviewer"
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


class Application(Base):
    """
    Main Application table - tracks the overall application workflow.
    Each application goes through 6 steps with specific status transitions.
    """
    __tablename__ = "applications"
    __table_args__ = {"schema": "application_agent"}
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(50), nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    
    # Workflow tracking
    step = Column(String(20), nullable=False, default="STEP_1")
    # STEP_1, STEP_2, STEP_3, STEP_4, STEP_5, STEP_6
    
    status = Column(String(30), nullable=False, default="STARTED")
    # STARTED, SUBMITTED, QUALIFIED, DECISION_PENDING
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    
    # LLM Qualification Assessment
    qualification_score = Column(Integer, nullable=True)  # 0-100 score
    qualification_recommendation = Column(String(20), nullable=True)  # INTERVIEW, HR_REVIEW, REJECT
    qualification_reasoning = Column(Text, nullable=True)  # Detailed explanation
    ai_assessment_provider = Column(String(50), nullable=True)  # openai, claude, etc.
    ai_assessment_model = Column(String(100), nullable=True)  # gpt-4, claude-3, etc.
    
    # Relationships to step-specific tables
    personal_info = relationship("ApplicationPersonalInfo", back_populates="application", uselist=False, cascade="all, delete-orphan")
    experience = relationship("ApplicationExperience", back_populates="application", uselist=False, cascade="all, delete-orphan")
    questions = relationship("ApplicationQuestions", back_populates="application", uselist=False, cascade="all, delete-orphan")
    disclosures = relationship("ApplicationDisclosures", back_populates="application", uselist=False, cascade="all, delete-orphan")
    identity = relationship("ApplicationIdentity", back_populates="application", uselist=False, cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "job_id": self.job_id,
            "user_email": self.user_email,
            "step": self.step,
            "status": self.status,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
            "submitted_at": self.submitted_at.isoformat() + "Z" if self.submitted_at else None,
            "qualification_score": self.qualification_score,
            "qualification_recommendation": self.qualification_recommendation,
            "qualification_reasoning": self.qualification_reasoning,
            "ai_assessment_provider": self.ai_assessment_provider,
            "ai_assessment_model": self.ai_assessment_model,
        }


class ApplicationPersonalInfo(Base):
    """
    Step 1: Personal Information and Contact Details
    Captures name, contact info, and address data.
    """
    __tablename__ = "application_personal_info"
    __table_args__ = {"schema": "application_agent"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application_agent.applications.id"), nullable=False, unique=True)
    
    # Personal info fields
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    linkedin = Column(String(500), nullable=True)
    
    # Address fields
    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    application = relationship("Application", back_populates="personal_info")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "application_id": str(self.application_id),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "linkedin": self.linkedin,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }


class ApplicationExperience(Base):
    """
    Step 2: Professional Experience and Education
    Stores summary, skills, work history, and education data.
    """
    __tablename__ = "application_experience"
    __table_args__ = {"schema": "application_agent"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application_agent.applications.id"), nullable=False, unique=True)
    
    # Experience summary
    summary = Column(Text, nullable=False)
    technical_skills = Column(Text, nullable=False)
    soft_skills = Column(Text, nullable=True)
    
    # Store complex data as JSONB arrays
    work_experience = Column(JSONB, nullable=True)  # Array of work experience objects
    education = Column(JSONB, nullable=True)        # Array of education objects
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    application = relationship("Application", back_populates="experience")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "application_id": str(self.application_id),
            "summary": self.summary,
            "technical_skills": self.technical_skills,
            "soft_skills": self.soft_skills,
            "work_experience": self.work_experience or [],
            "education": self.education or [],
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }


class ApplicationQuestions(Base):
    """
    Step 3: Application Questions
    Work authorization, location preferences, and employment details.
    """
    __tablename__ = "application_questions"
    __table_args__ = {"schema": "application_agent"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application_agent.applications.id"), nullable=False, unique=True)
    
    # Work authorization
    work_authorization = Column(String(10), nullable=False)  # 'yes', 'no'
    visa_sponsorship = Column(String(10), nullable=False)    # 'yes', 'no'
    
    # Location preferences
    relocate = Column(String(20), nullable=False)            # 'yes', 'no', 'maybe'
    remote_work = Column(String(20), nullable=False)         # 'fully-remote', 'hybrid', 'no'
    preferred_location = Column(String(255), nullable=False)
    
    # Employment details
    availability = Column(String(20), nullable=False)        # 'immediately', '2weeks', '4weeks', 'other'
    salary_min = Column(String(20), nullable=False)
    salary_max = Column(String(20), nullable=False)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    application = relationship("Application", back_populates="questions")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "application_id": str(self.application_id),
            "work_authorization": self.work_authorization,
            "visa_sponsorship": self.visa_sponsorship,
            "relocate": self.relocate,
            "remote_work": self.remote_work,
            "preferred_location": self.preferred_location,
            "availability": self.availability,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }


class ApplicationDisclosures(Base):
    """
    Step 4: Voluntary Disclosures
    Government employment, non-compete agreements, and previous employment info.
    """
    __tablename__ = "application_disclosures"
    __table_args__ = {"schema": "application_agent"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application_agent.applications.id"), nullable=False, unique=True)
    
    government_employment = Column(String(20), nullable=False)   # 'yes', 'no', 'prefer_not_to_say'
    non_compete = Column(String(20), nullable=False)             # 'yes', 'no', 'prefer_not_to_say'
    previous_employment = Column(String(20), nullable=False)     # 'yes', 'no', 'prefer_not_to_say'
    previous_alias = Column(String(255), nullable=True)
    personnel_number = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    application = relationship("Application", back_populates="disclosures")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "application_id": str(self.application_id),
            "government_employment": self.government_employment,
            "non_compete": self.non_compete,
            "previous_employment": self.previous_employment,
            "previous_alias": self.previous_alias,
            "personnel_number": self.personnel_number,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }


class ApplicationIdentity(Base):
    """
    Step 5: Self Identity (EEO Information)
    Optional demographic information for equal opportunity reporting.
    """
    __tablename__ = "application_identity"
    __table_args__ = {"schema": "application_agent"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application_agent.applications.id"), nullable=False, unique=True)
    
    gender = Column(String(30), nullable=True)                   # 'male', 'female', 'non-binary', 'other', 'prefer_not_to_say'
    race = Column(ARRAY(String), nullable=True)                  # Array of race/ethnicity selections
    veteran_status = Column(String(30), nullable=True)          # 'yes', 'no', 'prefer_not_to_say'
    disability = Column(String(30), nullable=True)              # 'yes', 'no', 'prefer_not_to_say'
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    application = relationship("Application", back_populates="identity")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "application_id": str(self.application_id),
            "gender": self.gender,
            "race": self.race or [],
            "veteran_status": self.veteran_status,
            "disability": self.disability,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }


def create_tables():
    """Create database tables and schema if they don't exist"""
    try:
        # Create schema first
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS application_agent"))
            conn.commit()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Application agent database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create application agent database tables: {e}")
        return False


def get_db_session() -> Session:
    """Get database session"""
    return SessionLocal()


class ApplicationCache:
    """Redis-based caching for application data"""
    
    CACHE_PREFIX = "application:"
    DEFAULT_TTL = 1800  # 30 minutes
    
    @staticmethod
    def get_cache_key(application_id: str) -> str:
        return f"{ApplicationCache.CACHE_PREFIX}{application_id}"
    
    @staticmethod
    def get(application_id: str) -> Optional[Dict[str, Any]]:
        """Get application data from cache"""
        try:
            cache_key = ApplicationCache.get_cache_key(application_id)
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for application {application_id}: {e}")
            return None
    
    @staticmethod
    def set(application_id: str, application_data: Dict[str, Any], ttl: int = None) -> bool:
        """Set application data in cache"""
        try:
            cache_key = ApplicationCache.get_cache_key(application_id)
            ttl = ttl or ApplicationCache.DEFAULT_TTL
            redis_client.setex(cache_key, ttl, json.dumps(application_data))
            logger.info(f"Application data cached for {application_id}")
            return True
        except Exception as e:
            logger.error(f"Cache set error for application {application_id}: {e}")
            return False
    
    @staticmethod
    def delete(application_id: str) -> bool:
        """Delete application data from cache"""
        try:
            cache_key = ApplicationCache.get_cache_key(application_id)
            redis_client.delete(cache_key)
            logger.info(f"Cache invalidated for application {application_id}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for application {application_id}: {e}")
            return False
    
    @staticmethod
    def exists(application_id: str) -> bool:
        """Check if application data exists in cache"""
        try:
            cache_key = ApplicationCache.get_cache_key(application_id)
            return redis_client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Cache exists check error for application {application_id}: {e}")
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