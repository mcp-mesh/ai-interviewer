"""
Admin utilities for checking admin privileges and handling admin operations.
"""

import logging
from typing import Dict, Any
from fastapi import HTTPException, Request
from mesh.types import McpMeshAgent

from app.utils.auth import require_user_from_request

logger = logging.getLogger(__name__)


async def require_admin_user(request: Request, user_agent: McpMeshAgent) -> Dict[str, Any]:
    """
    Require authenticated admin user for admin endpoints.
    
    Args:
        request: FastAPI Request object
        user_agent: MCP Mesh agent for user operations
        
    Returns:
        Dict containing admin user info
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
    """
    try:
        # Step 1: Authenticate user
        user_info = require_user_from_request(request)
        user_email = user_info["email"]
        
        logger.info(f"Checking admin privileges for user: {user_email}")
        
        # Step 2: Get user profile to check admin status
        profile_result = await user_agent(
            user_email=user_email,
            first_name=user_info.get("first_name", ""),
            last_name=user_info.get("last_name", "")
        )
        
        if not profile_result.get("success"):
            error_msg = profile_result.get("error", "Failed to get user profile")
            logger.error(f"Failed to get profile for admin check: {error_msg}")
            raise HTTPException(status_code=500, detail="Failed to verify admin privileges")
        
        user_profile = profile_result.get("user", {})
        is_admin = user_profile.get("is_admin", False)
        
        # Step 3: Check admin privileges
        if not is_admin:
            logger.warning(f"Access denied: User {user_email} is not an admin")
            raise HTTPException(
                status_code=403, 
                detail="Admin privileges required to access this resource"
            )
        
        logger.info(f"Admin access granted for user: {user_email}")
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking admin privileges: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify admin privileges")


def format_admin_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format user data for admin user listing response.
    
    Args:
        user_data: Raw user data from user agent
        
    Returns:
        Dict formatted for admin response
    """
    return {
        "id": user_data.get("id", ""),
        "email": user_data.get("email", ""),
        "name": user_data.get("name", ""),
        "first_name": user_data.get("first_name", ""),
        "last_name": user_data.get("last_name", ""),
        "is_admin": user_data.get("is_admin", False),
        "profile_completed": user_data.get("profile_completed", False),
        "has_resume": user_data.get("has_resume", False),
        "created_at": user_data.get("created_at", ""),
        "last_active_at": user_data.get("last_active_at"),
        "admin_notes": user_data.get("admin_notes", "")
    }