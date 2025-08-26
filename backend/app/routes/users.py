"""
Phase 2 Backend - Users API Routes

Clean delegation to user_agent via MCP Mesh dependency injection.
No authentication checks for testing phase.
"""

import logging

import mesh
from fastapi import APIRouter, HTTPException, Request
from mesh.types import McpMeshAgent

from app.models.schemas import (
    UserProfileResponse,
    UserProfileUpdate,
    ErrorResponse
)
from app.utils.auth import require_user_from_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserProfileResponse)
@mesh.route(dependencies=["user_profile_get"])
async def get_user_profile(
    request: Request,
    user_agent: McpMeshAgent = None
) -> UserProfileResponse:
    """
    Get current user's profile and preferences.
    
    Delegates to user_agent's user_profile_get capability.
    """
    try:
        # Extract user info from JWT token - authentication required
        user_info = require_user_from_request(request)
        
        logger.info(f"Getting profile for user: {user_info['email']}")
        
        # Delegate to user agent with structured user info
        result = await user_agent(
            user_email=user_info["email"],
            first_name=user_info.get("first_name", ""),
            last_name=user_info.get("last_name", "")
        )
        
        if not result.get("success"):
            error_msg = result.get("error", "Profile not found")
            logger.error(f"Failed to get user profile: {error_msg}")
            
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Profile retrieved for user: {result['user']['name']}")
        
        return UserProfileResponse(
            data=result["user"],
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user profile: {str(e)}")


@router.put("/profile", response_model=UserProfileResponse)
@mesh.route(dependencies=["user_profile_update"])
async def update_user_profile(
    request: Request,
    profile_update: UserProfileUpdate,
    user_agent: McpMeshAgent = None
) -> UserProfileResponse:
    """
    Update current user's profile and preferences.
    
    Delegates to user_agent's user_profile_update capability.
    """
    try:
        # Extract user info from JWT token - authentication required
        user_info = require_user_from_request(request)
        
        logger.info(f"Updating profile for user: {user_info['email']}")
        
        # Delegate to user agent
        result = await user_agent(
            user_email=user_info["email"],
            first_name=user_info.get("first_name", ""),
            last_name=user_info.get("last_name", ""),
            profile_data=profile_update.dict(exclude_none=True)
        )
        
        if not result.get("success"):
            error_msg = result.get("error", "Profile update failed")
            logger.error(f"Failed to update user profile: {error_msg}")
            
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Profile updated for user: {result['user']['name']}")
        
        return UserProfileResponse(
            data=result["user"],
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user profile: {str(e)}")