"""
Redis Caching Layer for Interview Sessions

Provides performance optimization through Redis caching of frequently accessed
interview session data. Follows the same pattern as UserCache and ApplicationCache.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import redis

logger = logging.getLogger(__name__)

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Redis Setup
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping()  # Test connection
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None


def test_redis_connection() -> bool:
    """Test Redis connection"""
    try:
        if redis_client:
            redis_client.ping()
            logger.info("Redis connection successful")
            return True
        return False
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False


class InterviewCache:
    """
    Redis-based caching for active interview session data.
    Optimizes performance for real-time interview operations.
    """
    
    CACHE_PREFIX = "interview_session:"
    DEFAULT_TTL = 7200  # 2 hours
    
    @staticmethod
    def get_cache_key(session_id: str) -> str:
        """Generate Redis key for interview session"""
        return f"{InterviewCache.CACHE_PREFIX}{session_id}"
    
    @staticmethod
    def get(session_id: str) -> Optional[Dict[str, Any]]:
        """Get interview session data from cache"""
        if not redis_client:
            return None
            
        try:
            cache_key = InterviewCache.get_cache_key(session_id)
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for session {session_id}: {e}")
            return None
    
    @staticmethod
    def set(session_id: str, session_data: Dict[str, Any], ttl: int = None) -> bool:
        """Set interview session data in cache"""
        if not redis_client:
            return False
            
        try:
            cache_key = InterviewCache.get_cache_key(session_id)
            ttl = ttl or InterviewCache.DEFAULT_TTL
            redis_client.setex(cache_key, ttl, json.dumps(session_data))
            logger.info(f"Interview session cached for {session_id}")
            return True
        except Exception as e:
            logger.error(f"Cache set error for session {session_id}: {e}")
            return False
    
    @staticmethod
    def delete(session_id: str) -> bool:
        """Delete interview session data from cache"""
        if not redis_client:
            return False
            
        try:
            cache_key = InterviewCache.get_cache_key(session_id)
            redis_client.delete(cache_key)
            logger.info(f"Cache invalidated for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for session {session_id}: {e}")
            return False
    
    @staticmethod
    def exists(session_id: str) -> bool:
        """Check if interview session data exists in cache"""
        if not redis_client:
            return False
            
        try:
            cache_key = InterviewCache.get_cache_key(session_id)
            return redis_client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Cache exists check error for session {session_id}: {e}")
            return False
    
    @staticmethod
    def update_session_status(session_id: str, status_data: Dict[str, Any]) -> bool:
        """Update cached session status for real-time UI updates"""
        if not redis_client:
            return False
            
        try:
            cached_session = InterviewCache.get(session_id)
            if cached_session:
                cached_session.update(status_data)
                return InterviewCache.set(session_id, cached_session)
            return False
        except Exception as e:
            logger.error(f"Cache status update error for session {session_id}: {e}")
            return False


class QuestionCache:
    """
    Redis-based caching for frequently accessed question data.
    Useful for caching question generation context and metadata.
    """
    
    CACHE_PREFIX = "interview_question:"
    DEFAULT_TTL = 3600  # 1 hour
    
    @staticmethod
    def get_cache_key(question_id: str) -> str:
        """Generate Redis key for interview question"""
        return f"{QuestionCache.CACHE_PREFIX}{question_id}"
    
    @staticmethod
    def get(question_id: str) -> Optional[Dict[str, Any]]:
        """Get question data from cache"""
        if not redis_client:
            return None
            
        try:
            cache_key = QuestionCache.get_cache_key(question_id)
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for question {question_id}: {e}")
            return None
    
    @staticmethod
    def set(question_id: str, question_data: Dict[str, Any], ttl: int = None) -> bool:
        """Set question data in cache"""
        if not redis_client:
            return False
            
        try:
            cache_key = QuestionCache.get_cache_key(question_id)
            ttl = ttl or QuestionCache.DEFAULT_TTL
            redis_client.setex(cache_key, ttl, json.dumps(question_data))
            return True
        except Exception as e:
            logger.error(f"Cache set error for question {question_id}: {e}")
            return False


class EvaluationCache:
    """
    Redis-based caching for interview evaluations.
    Caches evaluation results for quick access after completion.
    """
    
    CACHE_PREFIX = "interview_evaluation:"
    DEFAULT_TTL = 86400  # 24 hours
    
    @staticmethod
    def get_cache_key(interview_id: str) -> str:
        """Generate Redis key for interview evaluation"""
        return f"{EvaluationCache.CACHE_PREFIX}{interview_id}"
    
    @staticmethod
    def get(interview_id: str) -> Optional[Dict[str, Any]]:
        """Get evaluation data from cache"""
        if not redis_client:
            return None
            
        try:
            cache_key = EvaluationCache.get_cache_key(interview_id)
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for evaluation {interview_id}: {e}")
            return None
    
    @staticmethod
    def set(interview_id: str, evaluation_data: Dict[str, Any], ttl: int = None) -> bool:
        """Set evaluation data in cache"""
        if not redis_client:
            return False
            
        try:
            cache_key = EvaluationCache.get_cache_key(interview_id)
            ttl = ttl or EvaluationCache.DEFAULT_TTL
            redis_client.setex(cache_key, ttl, json.dumps(evaluation_data))
            return True
        except Exception as e:
            logger.error(f"Cache set error for evaluation {interview_id}: {e}")
            return False