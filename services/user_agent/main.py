#!/usr/bin/env python3
"""
User Agent - MCP Mesh Agent for User Management

Phase 2B implementation with PostgreSQL + Redis caching.
Capabilities: user_profile_get, user_profile_update, cache_invalidate
"""

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

import mesh
from fastmcp import FastMCP
from mesh.types import McpAgent

# Import database components
from .database import (
    User, get_db_session, UserCache, create_tables, test_connections
)

# Create FastMCP app instance
app = FastMCP("User Management Agent")

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database at module level - executed when MCP Mesh loads this module
logger.info("🚀 Initializing User Agent v2.1 (Database + Cache)")

# Test database connections
connections = test_connections()
if connections["postgres"]:
    logger.info("✅ PostgreSQL connection successful")
    # Create tables and schema
    if create_tables():
        logger.info("✅ Database schema initialized")
    else:
        logger.error("❌ Failed to initialize database schema")
else:
    logger.error("❌ PostgreSQL connection failed")
    
if connections["redis"]:
    logger.info("✅ Redis connection successful")
else:
    logger.error("❌ Redis connection failed")

logger.info("✅ User Agent ready to serve requests")


@app.tool()
@mesh.tool(
    capability="user_profile_get",
    tags=["user-management", "profiles", "data-retrieval"],
    description="Get user profile and preferences by email"
)
def user_profile_get(user_email: str, first_name: str = "", last_name: str = "") -> Dict[str, Any]:
    """
    Get user profile information with cache-first, postgres-backed storage.
    Creates user if doesn't exist.
    
    Args:
        user_email: User's email address
        first_name: First name from OAuth token
        last_name: Last name from OAuth token
        
    Returns:
        Dict with user profile data in frontend-expected format
    """
    try:
        logger.info(f"Getting profile for user: {user_email}")
        
        # Step 1: Check cache first
        cached_profile = UserCache.get(user_email)
        if cached_profile:
            logger.info(f"Profile found in cache for: {user_email}")
            return {
                "user": cached_profile,
                "success": True
            }
        
        # Step 2: Check database
        with get_db_session() as db:
            db_user = db.query(User).filter(User.email == user_email).first()
            
            if db_user:
                logger.info(f"Profile found in database for: {db_user.full_name}")
                # Update last active
                db_user.last_active_at = datetime.utcnow()
                db.commit()
                
                # Convert to frontend format
                profile = build_frontend_user_profile(db_user)
                
                # Cache the profile
                UserCache.set(user_email, profile)
                
                return {
                    "user": profile,
                    "success": True
                }
        
        # Step 3: User doesn't exist - create new user
        logger.info(f"Creating new user: {user_email}")
        
        # Parse full name
        if not first_name and not last_name:
            # Fallback to email-based name
            name_from_email = user_email.split("@")[0].replace(".", " ").title()
            name_parts = name_from_email.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        full_name = f"{first_name} {last_name}".strip() or user_email.split("@")[0]
        
        with get_db_session() as db:
            new_user = User(
                email=user_email,
                first_name=first_name,
                last_name=last_name,
                full_name=full_name,
                profile_completed=False,
                onboarding_completed=False,
                last_active_at=datetime.utcnow()
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"Created new user in database: {new_user.full_name} ({user_email})")
            
            # Convert to frontend format
            profile = build_frontend_user_profile(new_user)
            
            # Cache the profile
            UserCache.set(user_email, profile)
            
            return {
                "user": profile,
                "success": True
            }
            
    except Exception as e:
        logger.error(f"Error in user_profile_get: {str(e)}")
        return {"user": None, "success": False, "error": str(e)}


def build_frontend_user_profile(db_user: User) -> Dict[str, Any]:
    """
    Build user profile in frontend-expected format from database user.
    Returns basic profile - other agents will add their data later.
    """
    return {
        "id": str(db_user.id),
        "email": db_user.email,
        "name": db_user.full_name,
        "first_name": db_user.first_name,
        "last_name": db_user.last_name,
        
        # Basic flags - will be populated by other agents later
        "hasResume": False,
        "isResumeAvailable": False,
        "isApplicationsAvailable": True,
        "availableJobs": 0,
        "matchedJobs": 0,
        
        # Basic profile structure - empty for now
        "profile": {
            "skills": [],
            "experience_years": 0,
            "location": "",
            "resume_url": None,
            "bio": f"Welcome {db_user.first_name}! Complete your profile to get personalized job matches.",
            "phone": "",
            "linkedin": "",
            "github": ""
        },
        
        # Basic preferences structure - empty for now
        "preferences": db_user.basic_preferences or {
            "job_types": [],
            "locations": [],
            "salary_min": 0,
            "salary_max": 0,
            "categories": []
        },
        
        # Will be populated by other agents
        "applications": [],
        
        # Timestamps
        "createdAt": db_user.created_at.isoformat() + "Z" if db_user.created_at else None,
        "updatedAt": db_user.updated_at.isoformat() + "Z" if db_user.updated_at else None,
        
        # User agent specific flags
        "profile_completed": db_user.profile_completed,
        "onboarding_completed": db_user.onboarding_completed,
    }


@app.tool()
@mesh.tool(
    capability="user_profile_update",
    tags=["user-management", "profiles", "data-modification"],
    description="Update user profile and preferences"
)
def user_profile_update(
    user_email: str,
    profile_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update user profile information.
    
    Args:
        user_email: User's email address
        profile_data: Updated profile data
        
    Returns:
        Dict with updated user profile or error
    """
    try:
        logger.info(f"Updating profile for user: {user_email}")
        
        # Find user by email
        if user_email not in STATIC_USERS:
            logger.warning(f"User not found: {user_email}")
            return {
                "user": None,
                "success": False,
                "error": f"User {user_email} not found"
            }
        
        # Get current user data
        user = STATIC_USERS[user_email].copy()
        
        # Update profile fields
        if "name" in profile_data:
            user["name"] = profile_data["name"]
        
        if "profile" in profile_data:
            profile_updates = profile_data["profile"]
            for key, value in profile_updates.items():
                if key in user["profile"]:
                    user["profile"][key] = value
        
        if "preferences" in profile_data:
            preferences_updates = profile_data["preferences"]
            for key, value in preferences_updates.items():
                if key in user["preferences"]:
                    user["preferences"][key] = value
        
        # Update timestamp
        user["updatedAt"] = datetime.utcnow().isoformat() + "Z"
        
        # In real system, this would save to database
        # For mock, we just return the updated data
        
        result = {
            "user": user,
            "success": True,
            "message": "Profile updated successfully"
        }
        
        logger.info(f"Profile updated for user: {user['name']}")
        return result
        
    except Exception as e:
        logger.error(f"Error in user_profile_update: {str(e)}")
        return {"success": False, "error": str(e)}


@app.tool()
@mesh.tool(
    capability="cache_invalidate",
    tags=["user-management", "caching", "invalidation"],
    description="Invalidate user profile cache"
)
def cache_invalidate(user_email: str) -> Dict[str, Any]:
    """
    Invalidate user profile cache. Called by other agents when user data changes.
    
    Args:
        user_email: User's email address
        
    Returns:
        Dict with success status
    """
    try:
        logger.info(f"Invalidating cache for user: {user_email}")
        
        success = UserCache.delete(user_email)
        
        if success:
            logger.info(f"Cache successfully invalidated for: {user_email}")
            return {
                "success": True,
                "message": f"Cache invalidated for {user_email}"
            }
        else:
            logger.warning(f"Cache invalidation failed for: {user_email}")
            return {
                "success": False,
                "error": f"Failed to invalidate cache for {user_email}"
            }
            
    except Exception as e:
        logger.error(f"Error in cache_invalidate: {str(e)}")
        return {"success": False, "error": str(e)}


# Agent class definition - MCP Mesh pattern
@mesh.agent(
    name="user-agent",
    auto_run=True
)
class UserAgent(McpAgent):
    """
    User Agent for AI Interviewer Phase 2B
    
    Handles all user-related operations with PostgreSQL + Redis caching.
    Capabilities: user_profile_get, user_profile_update, cache_invalidate
    """
    pass  # Database initialization already done at module level


if __name__ == "__main__":
    logger.info("User Agent starting...")