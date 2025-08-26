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
from mesh.types import McpAgent, McpMeshAgent

# Import database components
from .database import (
    User, Resume, get_db_session, UserCache, create_tables, test_connections
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
    Now uses structured Resume table data instead of JSONB.
    """
    # Extract resume data from the new Resume table relationship
    resume = db_user.resume
    logger.info(f"Resume relationship for {db_user.email}: {'found' if resume else 'not found'}")
    if resume:
        logger.info(f"Resume details: experience_level={resume.experience_level}, years={resume.years_experience}")
    structured_analysis = resume.to_structured_analysis() if resume else {}
    
    return {
        "id": str(db_user.id),
        "email": db_user.email,
        "name": db_user.full_name,
        "first_name": db_user.first_name,
        "last_name": db_user.last_name,
        
        # Resume flags (Step 5 - consolidated to single hasResume flag)
        "hasResume": db_user.has_resume,
        "isApplicationsAvailable": True,
        "availableJobs": 0,
        "matchedJobs": 0,
        
        # Enhanced profile structure with resume data
        "profile": {
            "skills": structured_analysis.get("tags", []),
            "experience_years": structured_analysis.get("years_experience", 0),
            "location": "",
            "resume_url": resume.file_path if resume else None,
            "bio": structured_analysis.get("professional_summary", f"Welcome {db_user.first_name}! Complete your profile to get personalized job matches."),
            "phone": "",
            "linkedin": "",
            "github": ""
        },
        
        # Basic preferences structure
        "preferences": db_user.basic_preferences or {
            "job_types": [],
            "locations": [],
            "salary_min": 0,
            "salary_max": 0,
            "categories": structured_analysis.get("categories", [])
        },
        
        # Resume-specific fields (only present if resume exists)
        "resume_analysis": {
            "years_experience": resume.years_experience if resume else None,
            "experience_level": resume.experience_level if resume else None,
            "professional_summary": resume.professional_summary if resume else None,
            "education_level": resume.education_level if resume else None,
            "ai_provider": resume.ai_provider if resume else None,
            "ai_model": resume.ai_model if resume else None,
            "profile_strength": resume.profile_strength if resume else None,
            "confidence_score": resume.confidence_score if resume else None,
        } if resume else {},
        
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
    capability="get_resume_text",
    tags=["user-management", "resume-processing", "text-content"],
    description="Get raw resume text content for LLM processing"
)
def get_resume_text(user_email: str) -> Dict[str, Any]:
    """
    Get raw resume text content for LLM processing.
    Separate from user_profile_get to avoid unnecessary bandwidth usage.
    
    Args:
        user_email: User's email address
        
    Returns:
        Dict with resume text content and metadata
    """
    try:
        logger.info(f"Getting resume text for user: {user_email}")
        
        with get_db_session() as db:
            db_user = db.query(User).filter(User.email == user_email).first()
            
            if not db_user or not db_user.resume:
                return {
                    "success": True,
                    "has_resume": False,
                    "text_content": "",
                    "message": "No resume found"
                }
            
            resume = db_user.resume
            
            return {
                "success": True,
                "has_resume": True,
                "text_content": resume.text_content or "",
                "filename": resume.filename,
                "processed_at": resume.processed_at.isoformat() + "Z" if resume.processed_at else None,
                "analysis_enhanced": resume.analysis_enhanced,
                "message": "Resume text retrieved successfully"
            }
            
    except Exception as e:
        logger.error(f"Error getting resume text: {str(e)}")
        return {"success": False, "error": str(e)}


@app.tool()
@mesh.tool(
    capability="process_resume_upload",
    tags=["user-management", "resume-processing", "file-processing"],
    description="Process uploaded resume file and update user profile",
    dependencies=[
        {
            "capability": "extract_text_from_pdf",
            "tags": ["pdf", "text-extraction"]
        }
    ]
)
async def process_resume_upload(
    user_email: str,
    minio_url: str,
    file_path: str,
    filename: str,
    file_size: int,
    uploaded_at: str,
    process_with_ai: bool = True,
    pdf_extractor: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Process uploaded resume file using MCP Mesh pattern.
    
    Flow: user_agent → pdf_extractor_agent → llm_agent → back to user_agent
    
    Args:
        user_email: User's email address
        minio_url: MinIO URL for PDF file access
        file_path: MinIO file path
        filename: Original filename
        file_size: File size in bytes
        uploaded_at: Upload timestamp
        process_with_ai: Whether to use AI for enhanced analysis
        pdf_extractor: MCP Mesh agent for PDF processing
        
    Returns:
        Dict with processing results and updated profile
    """
    try:
        logger.info(f"Processing resume upload for user: {user_email}")
        logger.info(f"MinIO URL: {minio_url}")
        
        # Step 1: Call pdf_extractor_agent via MCP Mesh
        logger.info("Calling PDF extractor agent via MCP Mesh")
        
        # Use MCP Mesh dependency injection pattern
        extraction_result = await pdf_extractor(
            file_path=minio_url,
            extraction_method="auto"
        )
        
        if not extraction_result or not extraction_result.get("success"):
            error_msg = extraction_result.get("error", "PDF extraction failed") if extraction_result else "PDF extraction failed"
            logger.error(f"PDF extraction failed: {error_msg}")
            return {
                "success": False,
                "error": f"Resume processing failed: {error_msg}",
                "profile_updated": False
            }
        
        logger.info(f"PDF extraction successful. Enhanced: {extraction_result.get('analysis_enhanced', False)}")
        
        # Step 2: Process extraction results
        resume_data = {
            "filename": filename,
            "file_path": file_path,
            "file_size": file_size,
            "uploaded_at": uploaded_at,
            "minio_url": minio_url,
            "extraction_success": True,
            "text_content": extraction_result.get("text_content", ""),
            "sections": extraction_result.get("sections", {}),
            "structured_analysis": extraction_result.get("structured_analysis", {}),
            "analysis_enhanced": extraction_result.get("analysis_enhanced", False),
            "text_stats": extraction_result.get("text_stats", {}),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        # Step 3: Create Resume record in database with structured fields
        logger.info(f"Creating Resume record for: {user_email}")
        
        try:
            with get_db_session() as db:
                # Find user by email
                db_user = db.query(User).filter(User.email == user_email).first()
                
                if not db_user:
                    logger.error(f"User not found in database: {user_email}")
                    return {
                        "success": False,
                        "error": f"User {user_email} not found in database",
                        "profile_updated": False
                    }
                
                # Delete existing resume if any (one-to-one relationship)
                existing_resume = db.query(Resume).filter(Resume.user_id == db_user.id).first()
                if existing_resume:
                    logger.info(f"Deleting existing resume for user: {user_email}")
                    db.delete(existing_resume)
                
                # Extract structured analysis from PDF processing result
                profile_analysis = extraction_result.get("profile_analysis", {})
                
                # Create new Resume record with structured fields
                new_resume = Resume(
                    user_id=db_user.id,
                    filename=filename,
                    file_path=file_path,
                    file_size=file_size,
                    minio_url=minio_url,
                    uploaded_at=datetime.fromisoformat(uploaded_at.replace('Z', '+00:00')),
                    processed_at=datetime.utcnow(),
                    
                    # AI analysis structured fields
                    categories=profile_analysis.get("categories"),
                    experience_level=profile_analysis.get("experience_level"),
                    years_experience=profile_analysis.get("years_experience"),
                    tags=profile_analysis.get("tags"),
                    professional_summary=profile_analysis.get("professional_summary"),
                    education_level=profile_analysis.get("education_level"),
                    confidence_score=profile_analysis.get("confidence_score"),
                    profile_strength=profile_analysis.get("profile_strength"),
                    
                    # AI processing metadata
                    ai_provider=profile_analysis.get("ai_provider"),
                    ai_model=profile_analysis.get("ai_model"),
                    analysis_enhanced=extraction_result.get("analysis_enhanced", False),
                    
                    # Raw content for fallback
                    text_content=extraction_result.get("text_content"),
                    basic_sections=extraction_result.get("sections"),
                    text_stats=extraction_result.get("text_stats")
                )
                
                db.add(new_resume)
                
                # Update user profile completion status
                db_user.profile_completed = True
                db_user.updated_at = datetime.utcnow()
                
                # Commit changes
                db.commit()
                db.refresh(new_resume)
                
                logger.info(f"Resume record created successfully for: {db_user.full_name}")
                logger.info(f"Resume ID: {new_resume.id}")
                logger.info(f"Categories: {new_resume.categories}")
                logger.info(f"Experience level: {new_resume.experience_level}")
                
        except Exception as db_error:
            logger.error(f"Database error creating resume record: {str(db_error)}")
            return {
                "success": False,
                "error": f"Failed to create resume record: {str(db_error)}",
                "profile_updated": False
            }
        
        # Invalidate user cache to force fresh data with new resume info
        UserCache.delete(user_email)
        
        logger.info(f"Resume processing completed successfully for: {user_email}")
        
        return {
            "success": True,
            "resume_data": new_resume.to_dict(),
            "processed_data": new_resume.to_structured_analysis(),
            "profile_updated": True,
            "message": f"Resume processed and profile updated successfully. AI analysis: {'enhanced' if extraction_result.get('analysis_enhanced') else 'basic'}"
        }
        
    except Exception as e:
        logger.error(f"Error in process_resume_upload: {str(e)}")
        return {
            "success": False,
            "error": f"Resume processing failed: {str(e)}",
            "profile_updated": False
        }


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