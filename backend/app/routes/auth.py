"""
Authentication and user management routes.
"""

import logging
from fastapi import APIRouter, Request
from app.config import DEV_MODE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["auth"])

@router.get("/user/profile")
async def get_user_profile(request: Request):
    """Get user profile from authenticated user including resume data."""
    user_data = request.state.user
    bearer_token = request.state.bearer_token
    
    logger.info(f"USER PROFILE ENDPOINT CALLED - User: {user_data.get('email')} - Token: {bearer_token[:20]}...")
    
    # Include resume analysis data if available
    resume_info = user_data.get("resume", {})
    structured_analysis = resume_info.get("structured_analysis", {})
    
    return {
        "message": "Authentication successful!",
        "user": user_data,
        "bearer_token": bearer_token,
        "dev_mode": DEV_MODE,
        "resume_uploaded": bool(resume_info),
        "resume_analysis": {
            "document_quality": structured_analysis.get("document_quality"),
            "ai_provider": structured_analysis.get("ai_provider"), 
            "ai_model": structured_analysis.get("ai_model"),
            "years_experience": structured_analysis.get("years_experience"),
            "education_level": structured_analysis.get("education_level"),
            "technical_skills": structured_analysis.get("technical_skills", []),
            "professional_summary": structured_analysis.get("professional_summary")
        } if structured_analysis else {}
    }

@router.get("/auth/test")
async def test_authentication(request: Request):
    """Test endpoint to show authentication details including bearer token."""
    user_data = request.state.user
    bearer_token = request.state.bearer_token
    
    logger.info(f"Auth test requested by user: {user_data.get('email')}")
    
    return {
        "message": "Authentication successful!",
        "user": user_data,
        "bearer_token": bearer_token,
        "dev_mode": DEV_MODE,
        "all_headers": dict(request.headers)
    }