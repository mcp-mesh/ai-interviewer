"""
Database Connection and Configuration

Handles PostgreSQL connection setup, session management, and table creation.
Follows the same pattern as user_agent and application_agent for consistency.
"""

import os
import logging
from typing import Dict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from .base import Base

logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://mcpmesh:mcpmesh123@postgres:5432/ai_interviewer"
)

# SQLAlchemy Setup
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> bool:
    """
    Create database tables and schema if they don't exist.
    Called automatically at agent startup.
    """
    try:
        # Create schema first
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS interview_agent"))
            conn.commit()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Interview agent database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create interview agent database tables: {e}")
        return False


def get_db_session() -> Session:
    """Get database session for interview operations"""
    return SessionLocal()


def test_postgres_connection() -> bool:
    """Test PostgreSQL database connection"""
    try:
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection successful")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False