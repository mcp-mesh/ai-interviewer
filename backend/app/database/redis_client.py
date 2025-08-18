"""
Redis client and operations for AI Interviewer Backend.
Centralizes all Redis interactions and provides helper methods.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import redis
from app.config import REDIS_URL

logger = logging.getLogger(__name__)

class RedisClient:
    """Centralized Redis client with helper methods."""
    
    def __init__(self):
        self.client = redis.from_url(REDIS_URL, decode_responses=True)
        self._test_connection()
    
    def _test_connection(self):
        """Test Redis connection on initialization."""
        try:
            self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def set_json(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store JSON data in Redis with optional TTL."""
        try:
            json_data = json.dumps(data)
            if ttl:
                self.client.setex(key, ttl, json_data)
            else:
                self.client.set(key, json_data)
            return True
        except Exception as e:
            logger.error(f"Failed to set JSON data for key {key}: {e}")
            return False
    
    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve JSON data from Redis."""
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get JSON data for key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            result = self.client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False
    
    def scan_keys(self, pattern: str, count: int = 100) -> List[str]:
        """Scan for keys matching pattern."""
        try:
            keys = []
            cursor = 0
            while True:
                cursor, batch_keys = self.client.scan(cursor=cursor, match=pattern, count=count)
                keys.extend(batch_keys)
                if cursor == 0:
                    break
            return keys
        except Exception as e:
            logger.error(f"Failed to scan keys with pattern {pattern}: {e}")
            return []
    
    def set_with_nx_ex(self, key: str, value: str, ttl: int) -> bool:
        """Set key with NX (not exists) and EX (expiry) flags for distributed locking."""
        try:
            result = self.client.set(key, value, nx=True, ex=ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set lock key {key}: {e}")
            return False
    
    def add_to_set(self, key: str, value: str) -> bool:
        """Add value to Redis set."""
        try:
            self.client.sadd(key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to add to set {key}: {e}")
            return False
    
    def remove_from_set(self, key: str, value: str) -> bool:
        """Remove value from Redis set."""
        try:
            result = self.client.srem(key, value)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to remove from set {key}: {e}")
            return False
    
    def get_set_members(self, key: str) -> List[str]:
        """Get all members of a Redis set."""
        try:
            return list(self.client.smembers(key))
        except Exception as e:
            logger.error(f"Failed to get set members for {key}: {e}")
            return []

# Global Redis client instance
redis_client = RedisClient()