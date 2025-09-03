#!/usr/bin/env python3
"""
Job Agent Database Models and Connection Setup using SQLAlchemy ORM
Converted from asyncpg/raw SQL to match user-agent pattern
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Integer, text, Index
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid

logger = logging.getLogger(__name__)

# Database Configuration
def _build_database_url():
    """Build database URL from environment variables"""
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432") 
    database = os.getenv("POSTGRES_DB", "ai_interviewer")
    user = os.getenv("POSTGRES_USER", "mcpmesh")
    password = os.getenv("POSTGRES_PASSWORD", "mcpmesh123")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

DATABASE_URL = os.getenv("DATABASE_URL") or _build_database_url()

# SQLAlchemy Setup
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Job(Base):
    """
    Jobs table - contains all job postings managed by job_agent
    """
    __tablename__ = "jobs"
    __table_args__ = (
        # Indexes for performance (SQLAlchemy will create these)
        Index('idx_jobs_category', 'category'),
        Index('idx_jobs_location', 'location'), 
        Index('idx_jobs_city', 'city'),
        Index('idx_jobs_state', 'state'),
        Index('idx_jobs_country', 'country'),
        Index('idx_jobs_job_type', 'job_type'),
        Index('idx_jobs_posted_date', 'posted_date'),
        Index('idx_jobs_is_active', 'is_active'),
        
        # Schema must be last in tuple
        {"schema": "job_agent"}
    )
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)  # Keep for backward compatibility/display
    
    # Location breakdown for filtering
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)  # Nullable for international locations
    country = Column(String(100), nullable=False)
    
    # Job details with constraints
    job_type = Column(String(50), nullable=False)  # CHECK constraint handled in create_tables()
    category = Column(String(50), nullable=False)  # CHECK constraint handled in create_tables()
    experience_level = Column(String(50), nullable=True)
    remote = Column(Boolean, default=False)
    
    # Content (markdown)
    description = Column(Text, nullable=False)
    short_description = Column(String(500), nullable=True)
    requirements = Column(ARRAY(Text), nullable=True)
    benefits = Column(ARRAY(Text), nullable=True)
    skills_required = Column(ARRAY(Text), nullable=True)
    
    # Compensation
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(10), default='USD')
    
    # Interview and application details
    interview_duration_minutes = Column(Integer, default=60, nullable=False)  # Default 60 minutes
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    posted_date = Column(DateTime(timezone=True), default=func.now())
    application_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Company info
    company_size = Column(String(50), nullable=True)
    company_industry = Column(String(100), nullable=True)
    company_website = Column(String(255), nullable=True)
    
    # Admin fields
    created_by = Column(String(255), nullable=True)  # Admin user who created the job
    updated_by = Column(String(255), nullable=True)  # Admin user who last updated the job
    status = Column(String(50), default='open', nullable=False)  # open, closed, on_hold
    interview_count = Column(Integer, default=0, nullable=False)  # Number of interviews conducted
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "job_type": self.job_type,
            "category": self.category,
            "experience_level": self.experience_level,
            "remote": self.remote,
            "description": self.description,
            "short_description": self.short_description,
            "requirements": self.requirements or [],
            "benefits": self.benefits or [],
            "skills_required": self.skills_required or [],
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "interview_duration_minutes": self.interview_duration_minutes,
            "is_active": self.is_active,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
            "application_deadline": self.application_deadline.isoformat() if self.application_deadline else None,
            "company_size": self.company_size,
            "company_industry": self.company_industry,
            "company_website": self.company_website,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "status": self.status,
            "interview_count": self.interview_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def create_tables():
    """Create database tables, schema and constraints if they don't exist"""
    try:
        # Create schema first
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS job_agent"))
            conn.commit()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Add CHECK constraints that SQLAlchemy doesn't handle well
        with engine.connect() as conn:
            # Job type constraint
            conn.execute(text("""
                DO $$ BEGIN
                    ALTER TABLE job_agent.jobs ADD CONSTRAINT jobs_job_type_check 
                    CHECK (job_type IN ('Full-time', 'Part-time', 'Contract', 'Internship'));
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # Category constraint
            conn.execute(text("""
                DO $$ BEGIN
                    ALTER TABLE job_agent.jobs ADD CONSTRAINT jobs_category_check 
                    CHECK (category IN ('Engineering', 'Operations', 'Finance', 'Marketing', 'Sales', 'Other'));
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # Status constraint
            conn.execute(text("""
                DO $$ BEGIN
                    ALTER TABLE job_agent.jobs ADD CONSTRAINT jobs_status_check 
                    CHECK (status IN ('open', 'closed', 'on_hold'));
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # Full text search index
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_jobs_search ON job_agent.jobs 
                USING gin(to_tsvector('english', title || ' ' || description));
            """))
            
            conn.commit()
        
        logger.info("✅ Job agent database tables and constraints created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create job agent database tables: {e}")
        return False


def get_db_session() -> Session:
    """Get database session"""
    return SessionLocal()


def insert_sample_data():
    """Insert sample job data for demo purposes"""
    try:
        with get_db_session() as db:
            # Check if sample data already exists
            existing_count = db.query(Job).filter(Job.company == 'S. Corp').count()
            if existing_count > 0:
                logger.info(f"📊 Sample job data already exists ({existing_count} jobs), skipping insertion")
                return True
            
            logger.info("🔄 Inserting sample job data...")
            
            # Load all 15 job data files dynamically
            sample_jobs = []
            
            # Import and load all job data files
            from .job_data import (
                job_01, job_02, job_03, job_04, job_05, job_06,
                job_07, job_08, job_09, job_10, job_11, job_12,
                job_13, job_14, job_15
            )
            
            job_modules = [
                job_01, job_02, job_03, job_04, job_05, job_06,
                job_07, job_08, job_09, job_10, job_11, job_12,
                job_13, job_14, job_15
            ]
            
            for job_module in job_modules:
                job_data = job_module.get_job_data()
                job = Job(**job_data)
                sample_jobs.append(job)
            
            # Insert all sample jobs
            for job in sample_jobs:
                db.add(job)
            
            db.commit()
            logger.info(f"✅ Successfully inserted {len(sample_jobs)} sample jobs")
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to insert sample job data: {e}")
        return False


def test_connection() -> bool:
    """Test database connection"""
    try:
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        logger.info("✅ PostgreSQL connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False