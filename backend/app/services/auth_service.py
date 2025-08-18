"""
Authentication and user management service.
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import jwt
from app.database.redis_client import redis_client
from app.config import ADMIN_EMAIL

logger = logging.getLogger(__name__)

class AuthService:
    """Handles user authentication and profile management."""
    
    @staticmethod
    def parse_oauth_token(bearer_token: str) -> Optional[Dict[str, Any]]:
        """Parse OAuth JWT token to extract user info (without signature verification)."""
        try:
            # All tokens from nginx should be JWT format (Google's real JWT or nginx-created JWT)
            payload = jwt.decode(bearer_token, options={"verify_signature": False})
            logger.info(f"Parsed JWT token for user: {payload.get('email', 'unknown')} from provider: {payload.get('provider', 'unknown')}")
            
            return {
                "email": payload.get("email"),
                "name": payload.get("name"),
                "given_name": payload.get("given_name"),
                "family_name": payload.get("family_name"),
                "provider": payload.get("provider", "unknown"),
                "token_type": "jwt",
                "sub": payload.get("sub")
            }
                
        except jwt.DecodeError as e:
            logger.error(f"Failed to decode JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing OAuth token: {e}")
            return None



    @staticmethod
    async def get_or_create_user(bearer_token: str) -> Optional[Dict[str, Any]]:
        """Parse OAuth token and get/create user profile."""
        try:
            logger.info(f"Starting get_or_create_user with token length: {len(bearer_token)}")
            
            # Parse the OAuth token
            token_info = AuthService.parse_oauth_token(bearer_token)
            logger.info(f"Token info received: {token_info is not None}")
            if not token_info:
                logger.error("Token info is None, returning None")
                return None
            
            # All tokens are now JWT - extract user info directly
            user_email = token_info.get("email")
            user_name = token_info.get("name")
            provider = token_info.get("provider", "unknown")
            
            logger.info(f"JWT token - email: {user_email}, name: {user_name}, provider: {provider}")
            
            if not user_email:
                logger.warning("No user email found in JWT token, returning None")
                return None
            
            logger.info(f"About to lookup user in Redis with key: user:{user_email}")
            
            # Use email as the persistent key
            user_key = f"user:{user_email}"
            
            # Try to get existing user by email
            user_data = redis_client.get_json(user_key)
            logger.info(f"Redis lookup result: {user_data is not None}")
            
            if user_data:
                # User exists, update last_active and return
                user_data["last_active"] = datetime.now().isoformat()
                
                # Store updated user data (no expiry for user profiles)
                redis_client.set_json(user_key, user_data)
                
                logger.info(f"Existing user found: {user_email}")
                logger.info(f"Returning existing user data: {user_email}")
                return user_data
            
            # User doesn't exist, create new user
            # Check if user is admin
            is_admin = user_email == ADMIN_EMAIL
            
            # Create new user object - using email as primary identifier
            user_data = {
                "email": user_email,
                "name": user_name or user_email.split('@')[0],
                "admin": is_admin,
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "interview_count": 0,
                "current_setup": {
                    "status": "initial"
                }
            }
            
            # Store user in Redis (no expiry for user profiles)
            redis_client.set_json(user_key, user_data)
            
            logger.info(f"New user created: {user_email} (admin: {is_admin})")
            return user_data
            
        except Exception as e:
            logger.error(f"Exception in get_or_create_user: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    def update_user_data(email: str, updates: Dict[str, Any]) -> bool:
        """Update user data in Redis."""
        try:
            user_key = f"user:{email}"
            user_data = redis_client.get_json(user_key)
            
            if not user_data:
                logger.error(f"User not found for email: {email}")
                return False
            
            user_data.update(updates)
            user_data["last_active"] = datetime.now().isoformat()
            
            success = redis_client.set_json(user_key, user_data)
            if success:
                logger.info(f"Updated user data for: {email}")
            return success
            
        except Exception as e:
            logger.error(f"Error updating user data: {e}")
            return False