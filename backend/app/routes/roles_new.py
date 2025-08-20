"""
Enhanced role management routes with PostgreSQL and intelligent matching.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

import mesh
from mesh.types import McpMeshAgent
from app.models.schemas import (
    RoleCreateRequest, RoleUpdateRequest, RoleResponse, 
    RoleListResponse, RoleDetailResponse, InterviewDetailResponse
)
from app.models.database import Role, UserProfile, Interview, CompanyLocation, EmploymentType
from app.database.postgres import get_db
from app.middleware.auth import check_admin_access
from app.services.skill_extraction import SkillExtractionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["roles"])

@router.get("/roles", response_model=RoleListResponse)
async def get_roles(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    type: Optional[str] = None,
    country: Optional[str] = None,
    experience_level: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None
):
    """Get roles with filtering and pagination. Admins see all, users see only open roles."""
    user_data = request.state.user
    is_admin = user_data.get("admin", False)
    
    # Base query
    query = db.query(Role)
    
    # Filter by status (non-admins only see open roles)
    if not is_admin:
        query = query.filter(Role.status == "open")
    elif status:
        query = query.filter(Role.status == status)
    
    # Apply filters
    if category:
        query = query.filter(Role.category == category)
    if type:
        # Filter by employment type
        employment_types = db.query(EmploymentType).filter(EmploymentType.type_code == type).all()
        if employment_types:
            type_ids = [et.id for et in employment_types]
            query = query.filter(Role.employment_type_id.in_(type_ids))
    if country:
        # Filter by location country
        locations = db.query(CompanyLocation).filter(CompanyLocation.country == country).all()
        if locations:
            location_ids = [loc.id for loc in locations]
            query = query.filter(Role.location_id.in_(location_ids))
    if experience_level:
        query = query.filter(Role.required_experience_level == experience_level)
    
    # Search in title and description
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Role.title.ilike(search_term),
                Role.description.ilike(search_term),
                Role.short_description.ilike(search_term)
            )
        )
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply pagination with eager loading for related data
    offset = (page - 1) * limit
    roles = query.options(
        joinedload(Role.location),
        joinedload(Role.employment_type)
    ).order_by(Role.created_at.desc()).offset(offset).limit(limit).all()
    
    # Convert to response format
    role_responses = []
    for role in roles:
        # Get location details
        location_details = {
            "id": role.location.id,
            "country": role.location.country,
            "state": role.location.state,
            "city": role.location.city,
            "office_name": role.location.office_name,
            "remote_allowed": role.location.remote_allowed
        }
        
        role_response = RoleResponse(
            role_id=role.role_id,
            title=role.title,
            description=role.description,
            short_description=role.short_description,
            category=role.category,
            type=role.employment_type.type_code,
            location=location_details,
            required_experience_level=role.required_experience_level,
            required_years_min=role.required_years_min,
            required_years_max=role.required_years_max,
            tags=role.tags,
            confidence_score=role.confidence_score,
            status=role.status,
            duration=role.duration,
            created_at=role.created_at,
            created_by=role.created_by,
            updated_at=role.updated_at,
            updated_by=role.updated_by
        )
        role_responses.append(role_response)
    
    logger.info(f"Retrieved {len(roles)} roles for {'admin' if is_admin else 'user'}: {user_data.get('email')}")
    
    return RoleListResponse(
        roles=role_responses,
        total_count=total_count,
        page=page,
        limit=limit
    )

@router.get("/roles/{role_id}", response_model=RoleDetailResponse)
async def get_role_details(role_id: str, request: Request, db: Session = Depends(get_db)):
    """Get role details with interview history. Admin access required."""
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"Role details requested by admin: {admin_data.get('email')} for role: {role_id}")
    
    # Get role with joined location and employment type data
    role = db.query(Role).options(
        joinedload(Role.location),
        joinedload(Role.employment_type)
    ).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Get interviews for this role
    interviews = db.query(Interview).filter(
        Interview.role_id == role_id,
        Interview.status == "completed"
    ).all()
    
    # Format interview data
    interview_data = []
    for interview in interviews:
        # Get user profile for candidate info
        user_profile = db.query(UserProfile).filter(
            UserProfile.email == interview.user_email
        ).first()
        
        evaluation = interview.evaluation or {}
        
        interview_info = {
            "session_id": interview.session_id,
            "candidate_name": user_profile.name if user_profile else "Unknown",
            "candidate_email": interview.user_email,
            "interview_date": interview.started_at.isoformat() if interview.started_at else None,
            "overall_score": evaluation.get("overall_score", 0),
            "technical_knowledge": evaluation.get("technical_knowledge", 0),
            "problem_solving": evaluation.get("problem_solving", 0),
            "communication": evaluation.get("communication", 0),
            "experience_relevance": evaluation.get("experience_relevance", 0),
            "hire_recommendation": evaluation.get("hire_recommendation", "no"),
            "feedback": evaluation.get("feedback", ""),
            "completion_reason": interview.completion_reason or "completed",
            "ended_at": interview.ended_at.isoformat() if interview.ended_at else None,
            "duration": interview.duration_seconds or 0
        }
        interview_data.append(interview_info)
    
    # Sort by interview date (most recent first)
    interview_data.sort(key=lambda x: x.get("interview_date", ""), reverse=True)
    
    # Calculate statistics
    total_interviews = len(interview_data)
    if total_interviews > 0:
        avg_score = sum(i.get("overall_score", 0) for i in interview_data) / total_interviews
        hire_recommendations = [i.get("hire_recommendation") for i in interview_data]
        strong_yes_count = hire_recommendations.count("strong_yes")
        yes_count = hire_recommendations.count("yes")
        hire_rate = (strong_yes_count + yes_count) / total_interviews * 100
    else:
        avg_score = 0
        strong_yes_count = 0
        yes_count = 0
        hire_rate = 0
    
    statistics = {
        "total_interviews": total_interviews,
        "average_score": round(avg_score, 1),
        "strong_yes_count": strong_yes_count,
        "yes_count": yes_count,
        "hire_rate": round(hire_rate, 1)
    }
    
    # Get location details for response
    location_details = {
        "id": role.location.id,
        "country": role.location.country,
        "state": role.location.state,
        "city": role.location.city,
        "office_name": role.location.office_name,
        "remote_allowed": role.location.remote_allowed
    }
    
    role_response = RoleResponse(
        role_id=role.role_id,
        title=role.title,
        description=role.description,
        short_description=role.short_description,
        category=role.category,
        type=role.employment_type.type_code,
        location=location_details,
        required_experience_level=role.required_experience_level,
        required_years_min=role.required_years_min,
        required_years_max=role.required_years_max,
        confidence_score=getattr(role, 'confidence_score', None),
        tags=role.tags,
        status=role.status,
        duration=role.duration,
        created_at=role.created_at,
        created_by=role.created_by,
        updated_at=role.updated_at,
        updated_by=role.updated_by
    )
    
    logger.info(f"Retrieved {total_interviews} interviews for role {role_id}")
    return RoleDetailResponse(
        role=role_response,
        interviews=interview_data,
        statistics=statistics
    )

@router.post("/admin/roles", response_model=RoleResponse)
@mesh.route(dependencies=[
    {
        "capability": "process_with_tools",
        "tags": ["+claude"],
    },
    {
        "capability": "convert_tool_format",
        "tags": ["*"],  # Accept any agent that can convert tools
    }
])
async def create_role(
    role_data: RoleCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    llm_service: McpMeshAgent = None,
    convert_tool_format: McpMeshAgent = None
):
    """Create a new role with LLM-generated requirements. Admin access required."""
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Role creation requested by admin: {user_data.get('email')}")
    
    # Validate enums
    valid_categories = ["investment_management", "legal_compliance", "marketing", "operations", "relationship_management", "sales", "technology"]
    valid_types = ["full-time", "part-time", "contract", "internship"]
    valid_levels = ["intern", "junior", "mid", "senior", "lead", "principal"]
    valid_statuses = ["open", "closed", "on_hold"]
    
    if role_data.category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}")
    if role_data.type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {', '.join(valid_types)}")
    
    # Validate reference data
    location = db.query(CompanyLocation).filter(CompanyLocation.id == role_data.location_id).first()
    if not location:
        raise HTTPException(status_code=400, detail="Invalid location_id")
    
    employment_type = db.query(EmploymentType).filter(EmploymentType.type_code == role_data.type).first()
    if not employment_type:
        raise HTTPException(status_code=400, detail="Invalid employment type")
    
    try:
        # Use LLM to analyze role and generate structured requirements
        logger.info(f"Analyzing role requirements for: {role_data.title}")
        role_analysis = await SkillExtractionService.generate_role_tags(
            title=role_data.title,
            description=role_data.description,
            llm_service=llm_service,
            convert_tool_format=convert_tool_format
        )
        
        if "error" in role_analysis:
            logger.warning(f"LLM analysis failed, using fallback defaults: {role_analysis['error']}")
            # Use fallback defaults since LLM failed
            tags = []
            short_description = role_data.description[:200] + "..." if len(role_data.description) > 200 else role_data.description
        else:
            # Use LLM-generated data
            tags = role_analysis.get("tags", [])
            short_description = role_analysis.get("short_description", role_data.description[:200])
        
        # Create role object using LLM-determined values
        role = Role(
            title=role_data.title,
            description=role_data.description,
            short_description=short_description,
            category=role_data.category,
            location_id=role_data.location_id,
            employment_type_id=employment_type.id,
            required_experience_level=role_analysis.get("experience_level", "mid"),
            required_years_min=role_analysis.get("required_years_min", 2),
            required_years_max=role_analysis.get("required_years_max", 8),
            tags=tags,
            confidence_score=role_analysis.get("confidence_score", 0.5),
            status="open",
            duration=role_data.duration,
            created_by=user_data.get("email"),
            updated_by=user_data.get("email")
        )
        
        db.add(role)
        db.commit()
        db.refresh(role)
        
        logger.info(f"Role created successfully: {role.role_id}")
        
        # Get location details for response
        location_details = {
            "id": location.id,
            "country": location.country,
            "state": location.state,
            "city": location.city,
            "office_name": location.office_name,
            "remote_allowed": location.remote_allowed
        }
        
        return RoleResponse(
            role_id=role.role_id,
            title=role.title,
            description=role.description,
            short_description=role.short_description,
            category=role.category,
            type=employment_type.type_code,
            location=location_details,
            required_experience_level=role.required_experience_level,
            required_years_min=role.required_years_min,
            required_years_max=role.required_years_max,
            tags=role.tags,
            confidence_score=role.confidence_score,
            status=role.status,
            duration=role.duration,
            created_at=role.created_at,
            created_by=role.created_by,
            updated_at=role.updated_at,
            updated_by=role.updated_by
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating role: {e}")
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Database rollback failed: {rollback_error}")
        raise HTTPException(status_code=500, detail="Internal server error while creating role")

@router.put("/admin/roles/{role_id}", response_model=RoleResponse)
@mesh.route(dependencies=[
    {
        "capability": "process_with_tools",
        "tags": ["+claude"],
    },
    {
        "capability": "convert_tool_format",
        "tags": ["*"],  # Accept any agent that can convert tools
    }
])
async def update_role(
    role_id: str,
    role_data: RoleUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    llm_service: McpMeshAgent = None,
    convert_tool_format: McpMeshAgent = None
):
    """Update an existing role. Admin access required."""
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Role update requested by admin: {user_data.get('email')} for role: {role_id}")
    
    # Get existing role
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        # Validate references if being updated
        update_data = role_data.dict(exclude_unset=True)
        
        if "location_id" in update_data:
            location = db.query(CompanyLocation).filter(CompanyLocation.id == update_data["location_id"]).first()
            if not location:
                raise HTTPException(status_code=400, detail="Invalid location_id")
        
        if "type" in update_data:
            employment_type = db.query(EmploymentType).filter(EmploymentType.type_code == update_data["type"]).first()
            if not employment_type:
                raise HTTPException(status_code=400, detail="Invalid employment type")
            # Update to use employment_type_id instead of type string
            update_data["employment_type_id"] = employment_type.id
            del update_data["type"]
        
        # If title or description changed, regenerate LLM analysis
        llm_updates = {}
        if "title" in update_data or "description" in update_data:
            new_title = update_data.get("title", role.title)
            new_description = update_data.get("description", role.description)
            
            logger.info(f"Re-analyzing role requirements for updated role: {new_title}")
            try:
                if llm_service is None:
                    logger.warning("LLM service not available for role update, skipping re-analysis")
                    role_analysis = {"error": "LLM service unavailable"}
                else:
                    role_analysis = await SkillExtractionService.generate_role_tags(
                        title=new_title,
                        description=new_description,
                        llm_service=llm_service,
                        convert_tool_format=convert_tool_format
                    )
            except Exception as llm_error:
                logger.error(f"LLM service call failed during update: {llm_error}")
                role_analysis = {"error": f"LLM service error: {str(llm_error)}"}
            
            if "error" not in role_analysis:
                # Use LLM analysis for experience and tags with validation
                try:
                    experience_level = role_analysis.get("experience_level", role.required_experience_level)
                    valid_levels = ["intern", "junior", "mid", "senior", "lead", "principal"]
                    if experience_level in valid_levels:
                        llm_updates["required_experience_level"] = experience_level
                    
                    years_min = role_analysis.get("required_years_min", role.required_years_min)
                    years_max = role_analysis.get("required_years_max", role.required_years_max)
                    if isinstance(years_min, int) and isinstance(years_max, int):
                        llm_updates["required_years_min"] = max(0, min(20, years_min))
                        llm_updates["required_years_max"] = max(llm_updates.get("required_years_min", years_min), min(25, years_max))
                    
                    tags = role_analysis.get("tags", role.tags)
                    if isinstance(tags, list):
                        llm_updates["tags"] = tags[:15]  # Limit to 15 tags
                    
                    short_desc = role_analysis.get("short_description", role.short_description)
                    if isinstance(short_desc, str):
                        llm_updates["short_description"] = short_desc[:500]  # Limit length
                    
                    confidence = role_analysis.get("confidence_score", role.confidence_score)
                    if isinstance(confidence, (int, float)):
                        llm_updates["confidence_score"] = max(0.0, min(1.0, confidence))
                        
                except (TypeError, ValueError) as validation_error:
                    logger.error(f"LLM data validation failed during update: {validation_error}")
            else:
                logger.warning(f"LLM analysis failed during update: {role_analysis['error']}, keeping existing values")
        
        # Apply manual updates first
        try:
            for field, value in update_data.items():
                setattr(role, field, value)
            
            # Apply LLM updates (can be overridden by manual updates)
            for field, value in llm_updates.items():
                if field not in update_data:  # Only apply if not manually specified
                    setattr(role, field, value)
            
            role.updated_by = user_data.get("email")
        except Exception as update_error:
            logger.error(f"Failed to apply updates to role object: {update_error}")
            raise HTTPException(status_code=500, detail="Failed to apply role updates")
        
        # Database transaction with error handling
        try:
            db.commit()
            db.refresh(role)
        except Exception as db_error:
            logger.error(f"Database commit failed during role update: {db_error}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save role updates to database")
        
        logger.info(f"Role updated successfully: {role_id}")
        
        # Get updated location and employment type details for response  
        try:
            updated_location = db.query(CompanyLocation).filter(CompanyLocation.id == role.location_id).first()
            updated_employment_type = db.query(EmploymentType).filter(EmploymentType.id == role.employment_type_id).first()
            
            location_details = {
                "id": updated_location.id,
                "country": updated_location.country,
                "state": updated_location.state,
                "city": updated_location.city,
                "office_name": updated_location.office_name,
                "remote_allowed": updated_location.remote_allowed
            }
        except Exception as response_error:
            logger.error(f"Failed to fetch location details for response: {response_error}")
            raise HTTPException(status_code=500, detail="Failed to prepare response data")
        
        return RoleResponse(
            role_id=role.role_id,
            title=role.title,
            description=role.description,
            short_description=role.short_description,
            category=role.category,
            type=updated_employment_type.type_code,
            location=location_details,
            required_experience_level=role.required_experience_level,
            required_years_min=role.required_years_min,
            required_years_max=role.required_years_max,
            tags=role.tags,
            confidence_score=role.confidence_score,
            status=role.status,
            duration=role.duration,
            created_at=role.created_at,
            created_by=role.created_by,
            updated_at=role.updated_at,
            updated_by=role.updated_by
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating role: {e}")
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Database rollback failed during update: {rollback_error}")
        raise HTTPException(status_code=500, detail="Internal server error while updating role")

@router.delete("/admin/roles/{role_id}")
async def delete_role(role_id: str, request: Request, db: Session = Depends(get_db)):
    """Delete a role. Admin access required."""
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Role deletion requested by admin: {user_data.get('email')} for role: {role_id}")
    
    # Get role
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        # Note: Related interviews will be cascade deleted due to relationship definition
        db.delete(role)
        db.commit()
        
        logger.info(f"Role deleted successfully: {role_id}")
        return {
            "success": True,
            "message": f"Role '{role.title}' deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete role: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete role")

@router.get("/interviews/{session_id}/details", response_model=InterviewDetailResponse)
async def get_interview_details(session_id: str, request: Request, db: Session = Depends(get_db)):
    """Get detailed interview information. Admin access required."""
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"Interview details requested by admin: {admin_data.get('email')} for session: {session_id}")
    
    # Get interview
    interview = db.query(Interview).filter(Interview.session_id == session_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Get user profile
    user_profile = db.query(UserProfile).filter(
        UserProfile.email == interview.user_email
    ).first()
    
    # Get role
    role = db.query(Role).filter(Role.role_id == interview.role_id).first()
    
    # Format response
    detailed_info = {
        "session_id": interview.session_id,
        "candidate": {
            "name": user_profile.name if user_profile else "Unknown",
            "email": interview.user_email,
            "resume_info": {
                "skills": user_profile.skills if user_profile else {},
                "experience_level": user_profile.overall_experience_level if user_profile else None,
                "total_years": user_profile.total_years_experience if user_profile else None
            }
        },
        "interview": {
            "started_at": interview.started_at.isoformat() if interview.started_at else None,
            "ended_at": interview.ended_at.isoformat() if interview.ended_at else None,
            "duration": interview.duration_seconds or 0,
            "status": interview.status,
            "completion_reason": interview.completion_reason or "unknown"
        },
        "role_info": {
            "title": role.title if role else "Unknown Role",
            "description": role.description if role else "",
            "requirements": {"tags": role.tags if role else [], "experience_level": role.required_experience_level if role else "mid"}
        },
        "conversation": interview.conversation or [],
        "evaluation": interview.evaluation or {}
    }
    
    logger.info(f"Retrieved detailed info for interview {session_id}")
    return detailed_info

@router.get("/roles/categories")
async def get_role_categories():
    """Get available role categories and types for filtering."""
    return {
        "categories": ["engineering", "design", "product", "sales", "marketing", "operations", "finance", "hr", "legal"],
        "types": ["full-time", "part-time", "contract", "internship"],
        "experience_levels": ["intern", "junior", "mid", "senior", "lead", "principal"],
        "statuses": ["open", "closed", "on_hold"]
    }