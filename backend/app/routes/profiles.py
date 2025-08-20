"""
User profile management routes.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session

import mesh
from mesh.types import McpMeshAgent
from app.models.schemas import (
    UserProfileResponse, UserProfileUpdate, 
    ResumeUploadResponse, RecommendedRolesResponse
)
from app.models.database import UserProfile
from app.database.postgres import get_db
from app.services.skill_extraction import SkillExtractionService
from app.services.role_matching import RoleMatchingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["profiles"])

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(request: Request, db: Session = Depends(get_db)):
    """Get current user's profile."""
    user_data = request.state.user
    user_email = user_data.get("email")
    
    profile = db.query(UserProfile).filter(UserProfile.email == user_email).first()
    
    if not profile:
        # Create basic profile if it doesn't exist
        profile = UserProfile(
            email=user_email,
            name=user_data.get("name", ""),
            skills={},
            leadership_experience={},
            career_progression=[],
            preferred_experience_levels=[],
            location_preferences={},
            role_type_preferences=[],
            category_preferences=[]
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return profile

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    request: Request, 
    db: Session = Depends(get_db)
):
    """Update user profile preferences."""
    user_data = request.state.user
    user_email = user_data.get("email")
    
    profile = db.query(UserProfile).filter(UserProfile.email == user_email).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Update only provided fields
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    logger.info(f"Updated profile for user: {user_email}")
    return profile

@router.post("/profile/resume", response_model=ResumeUploadResponse)
@mesh.route(dependencies=[
    {
        "capability": "process_with_tools",
        "tags": ["+claude"],
    }
])
async def upload_resume(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    llm_service: McpMeshAgent = None
):
    """Upload and analyze resume to extract skills and experience."""
    user_data = request.state.user
    user_email = user_data.get("email")
    
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.doc', '.docx', '.txt')):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF, DOC, DOCX, and TXT files are supported"
        )
    
    # Validate file size (max 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    try:
        # Read file content
        content = await file.read()
        
        # For now, assume text content (in production, use proper PDF/DOC parsing)
        if file.filename.lower().endswith('.txt'):
            resume_text = content.decode('utf-8')
        else:
            # For PDF/DOC files, you'd use libraries like PyPDF2, python-docx, etc.
            # For this demo, we'll simulate with placeholder text
            resume_text = f"Resume content from {file.filename} would be extracted here using appropriate libraries."
            logger.warning(f"PDF/DOC parsing not implemented - using placeholder for {file.filename}")
        
        # Extract profile data using LLM
        logger.info(f"Extracting profile data for user: {user_email}")
        profile_data = await SkillExtractionService.extract_profile_data(resume_text, llm_service)
        
        if "error" in profile_data:
            raise HTTPException(status_code=500, detail=profile_data["error"])
        
        # Get or create user profile
        profile = db.query(UserProfile).filter(UserProfile.email == user_email).first()
        
        if not profile:
            profile = UserProfile(email=user_email)
            db.add(profile)
        
        # Update profile with extracted data
        profile.name = user_data.get("name", profile.name)
        profile.overall_experience_level = profile_data.get("overall_experience_level")
        profile.total_years_experience = profile_data.get("total_years_experience")
        profile.skills = profile_data.get("skills", {})
        profile.leadership_experience = profile_data.get("leadership_experience", {})
        profile.career_progression = profile_data.get("career_progression", [])
        profile.preferred_experience_levels = profile_data.get("preferred_next_levels", [])
        profile.category_preferences = profile_data.get("categories_of_interest", [])
        profile.resume_content = resume_text
        profile.resume_metadata = {
            "filename": file.filename,
            "file_size": len(content),
            "upload_date": "2024-01-01T00:00:00Z",  # Use datetime.utcnow() in production
            "content_type": file.content_type
        }
        profile.is_profile_complete = True
        
        # Calculate confidence scores
        confidence_scores = {}
        for skill_name, skill_data in profile.skills.items():
            if isinstance(skill_data, dict) and "confidence" in skill_data:
                confidence_scores[skill_name] = skill_data["confidence"]
        
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Successfully updated profile for {user_email} with {len(profile.skills)} skills")
        
        return ResumeUploadResponse(
            success=True,
            message="Resume analyzed and profile updated successfully",
            profile_extracted=True,
            skills_count=len(profile.skills),
            confidence_scores=confidence_scores
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing resume upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to process resume")

@router.get("/profile/recommended-roles", response_model=RecommendedRolesResponse)
async def get_recommended_roles(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = 10,
    min_score: float = 0.3
):
    """Get personalized role recommendations for the user."""
    user_data = request.state.user
    user_email = user_data.get("email")
    
    # Check if user has a complete profile
    profile = db.query(UserProfile).filter(UserProfile.email == user_email).first()
    
    if not profile or not profile.is_profile_complete:
        raise HTTPException(
            status_code=400,
            detail="Profile not complete. Please upload a resume first."
        )
    
    # Get role recommendations
    try:
        role_matches = await RoleMatchingService.get_recommended_roles(
            db=db,
            user_email=user_email,
            limit=limit,
            min_score=min_score
        )
        
        # Format response
        recommended_roles = []
        for match in role_matches:
            role = match["role"]
            recommended_roles.append({
                "role": {
                    "role_id": role.role_id,
                    "title": role.title,
                    "description": role.description,
                    "short_description": role.short_description,
                    "category": role.category,
                    "type": role.type,
                    "country": role.country,
                    "state": role.state,
                    "city": role.city,
                    "required_experience_level": role.required_experience_level,
                    "required_years_min": role.required_years_min,
                    "required_years_max": role.required_years_max,
                    "required_skills": role.required_skills,
                    "tags": role.tags,
                    "status": role.status,
                    "duration": role.duration,
                    "created_at": role.created_at,
                    "created_by": role.created_by,
                    "updated_at": role.updated_at,
                    "updated_by": role.updated_by
                },
                "match_score": match["match_score"],
                "recommendation": match["recommendation"],
                "match_details": match["match_details"],
                "reasons": match["reasons"]
            })
        
        user_profile_summary = {
            "experience_level": profile.overall_experience_level,
            "total_years": profile.total_years_experience,
            "top_skills": list(profile.skills.keys())[:10] if profile.skills else [],
            "preferred_categories": profile.category_preferences,
            "location_preferences": profile.location_preferences
        }
        
        return RecommendedRolesResponse(
            recommended_roles=recommended_roles,
            user_profile_summary=user_profile_summary,
            total_matches=len(recommended_roles)
        )
        
    except Exception as e:
        logger.error(f"Error getting role recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get role recommendations")

@router.get("/profile/skills")
async def get_user_skills(request: Request, db: Session = Depends(get_db)):
    """Get user's extracted skills with details."""
    user_data = request.state.user
    user_email = user_data.get("email")
    
    profile = db.query(UserProfile).filter(UserProfile.email == user_email).first()
    
    if not profile:
        return {"skills": {}, "message": "No profile found"}
    
    return {
        "skills": profile.skills,
        "total_skills": len(profile.skills) if profile.skills else 0,
        "experience_level": profile.overall_experience_level,
        "total_years": profile.total_years_experience,
        "leadership": profile.leadership_experience,
        "profile_complete": profile.is_profile_complete
    }

@router.delete("/profile/resume")
async def delete_resume(request: Request, db: Session = Depends(get_db)):
    """Delete user's resume and reset extracted profile data."""
    user_data = request.state.user
    user_email = user_data.get("email")
    
    profile = db.query(UserProfile).filter(UserProfile.email == user_email).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Reset extracted data but keep preferences
    profile.overall_experience_level = None
    profile.total_years_experience = None
    profile.skills = {}
    profile.leadership_experience = {}
    profile.career_progression = []
    profile.resume_content = None
    profile.resume_metadata = {}
    profile.is_profile_complete = False
    
    db.commit()
    
    logger.info(f"Reset profile data for user: {user_email}")
    return {"success": True, "message": "Resume data deleted and profile reset"}

@router.post("/profile/feedback")
async def provide_role_feedback(
    role_id: str,
    feedback: str,  # "relevant", "not_relevant", "overqualified", "underqualified"
    request: Request,
    db: Session = Depends(get_db)
):
    """Provide feedback on role recommendations for improving future matches."""
    user_data = request.state.user
    user_email = user_data.get("email")
    
    valid_feedback = ["relevant", "not_relevant", "overqualified", "underqualified"]
    if feedback not in valid_feedback:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid feedback. Must be one of: {', '.join(valid_feedback)}"
        )
    
    try:
        # Find existing match history and update feedback
        from app.models.database import RoleMatchHistory
        
        match_history = db.query(RoleMatchHistory).filter(
            RoleMatchHistory.user_email == user_email,
            RoleMatchHistory.role_id == role_id
        ).order_by(RoleMatchHistory.recommended_at.desc()).first()
        
        if match_history:
            match_history.user_feedback = feedback
            db.commit()
            
            logger.info(f"Recorded feedback '{feedback}' for role {role_id} from user {user_email}")
            return {"success": True, "message": "Feedback recorded"}
        else:
            raise HTTPException(status_code=404, detail="Role recommendation not found")
            
    except Exception as e:
        logger.error(f"Error recording role feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")