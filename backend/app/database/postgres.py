"""
PostgreSQL database configuration and session management.
"""

import os
import logging
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.models.database import Base

logger = logging.getLogger(__name__)

# Database configuration - use POSTGRES_URL from environment or construct from parts
DATABASE_URL = os.getenv("POSTGRES_URL")
if not DATABASE_URL:
    # Construct from individual environment variables
    pg_user = os.getenv("POSTGRES_USER", "mcpmesh")
    pg_password = os.getenv("POSTGRES_PASSWORD", "mcpmesh123") 
    pg_host = os.getenv("POSTGRES_HOST", "postgres")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "ai_interviewer")
    DATABASE_URL = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

logger.info(f"Using PostgreSQL database: {DATABASE_URL.replace(os.getenv('POSTGRES_PASSWORD', 'mcpmesh123'), '***')}")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true"  # Enable SQL logging if needed
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self) -> bool:
        """Create all database tables."""
        try:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            return False
    
    def drop_tables(self) -> bool:
        """Drop all database tables (use with caution!)."""
        try:
            logger.warning("Dropping all database tables...")
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            return False
    
    def check_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def init_database(self) -> bool:
        """Initialize database with tables and basic data."""
        try:
            # Check connection first
            if not self.check_connection():
                return False
            
            # Create tables
            if not self.create_tables():
                return False
            
            # Insert initial data if needed
            self._insert_initial_data()
            
            logger.info("Database initialization completed")
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    def _insert_initial_data(self):
        """Insert any required initial data."""
        session = self.SessionLocal()
        try:
            # Add any seed data here if needed
            # For example, admin users, default categories, etc.
            session.commit()
            logger.info("Initial data inserted successfully")
        except Exception as e:
            logger.error(f"Failed to insert initial data: {e}")
            session.rollback()
        finally:
            session.close()

# Global database manager instance
db_manager = DatabaseManager()

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to get database session."""
    yield from db_manager.get_session()

# Helper functions for common database operations
def get_session() -> Session:
    """Get a new database session (remember to close it!)."""
    return SessionLocal()

async def init_db():
    """Initialize database (call this on startup)."""
    logger.info("Initializing database...")
    return db_manager.init_database()

async def check_db_health() -> bool:
    """Check database health for health endpoints."""
    return db_manager.check_connection()