"""
User Agent Database Models and Connection Setup
"""

import os
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Integer, text
from sqlalchemy.orm import declarative_base
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
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
            "last_active_at": self.last_active_at.isoformat() + "Z" if self.last_active_at else None,
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