"""
Role management routes.
"""

import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException

import mesh
from mesh.types import McpMeshAgent
from app.models.schemas import RoleCreateRequest, RoleResponse
from app.database.redis_client import redis_client
from app.middleware.auth import check_admin_access

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["roles"])

async def generate_short_description(title: str, description: str, llm_service: McpMeshAgent) -> str:
    """Generate a short description using LLM service with fallback to first sentence."""
    try:
        # Create system prompt and text for LLM
        system_prompt = "You are a professional HR assistant. Generate concise, professional job role summaries."
        text = f"Summarize this job role in under 25 words: Role: {title}, Description: {description}"
        
        # Call LLM service with correct parameters
        result = await llm_service(
            text=text,
            system_prompt=system_prompt,
            force_tool_use=False
        )
        
        if result and isinstance(result, dict):
            # Extract response from LLM result
            short_desc = result.get("content", "").strip()
            if short_desc and len(short_desc.split()) <= 25:
                logger.info(f"Generated short description via LLM: {short_desc[:50]}...")
                return short_desc

        logger.warning("LLM response invalid or too long, falling back to first sentence")
        
    except Exception as e:
        logger.error(f"Error calling LLM service for short description: {e}")

    # Fallback: use first sentence of description
    sentences = description.split('.')
    first_sentence = sentences[0].strip() if sentences else description
    
    # Truncate to ~25 words if needed
    words = first_sentence.split()
    if len(words) > 25:
        first_sentence = ' '.join(words[:25]) + '...'

    logger.info(f"Using fallback short description: {first_sentence[:50]}...")
    return first_sentence

@router.get("/roles/{role_id}")
async def get_role_details(role_id: str, request: Request):
    """Get role details with interview history. Admin access required."""
    logger.error(f"🔥🔥🔥 ROLE DETAILS ENDPOINT REACHED - role_id: {role_id} 🔥🔥🔥")
    
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"Role details requested by admin: {admin_data.get('email')} for role: {role_id}")
    
    try:
        # Get role data
        role_data = redis_client.get_json(f"roles:{role_id}")
        if not role_data:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Get completed interviews for this role by checking user sessions
        # First, get all user interview sessions (now keyed by email)
        user_interview_keys = redis_client.scan_keys("user_interview:*")
        logger.info(f"DEBUG: Found {len(user_interview_keys)} user interview sessions")
        
        interviews = []
        for user_interview_key in user_interview_keys:
            user_session = redis_client.get_json(user_interview_key)
            if user_session and user_session.get("role_id") == role_id:
                # This user interviewed for this role
                user_email = user_session.get("user_email")
                session_id = user_session.get("session_id")
                
                # Get user data for name (direct lookup by email)
                user_profile = None
                if user_email:
                    user_profile = redis_client.get_json(f"user:{user_email}")

                # Look for the corresponding completed interview session
                interview_session_key = f"interview_session:{session_id}"
                interview_data = redis_client.get_json(interview_session_key)
                
                if interview_data and interview_data.get("status") == "completed":
                    # Extract evaluation data
                    evaluation = interview_data.get("evaluation", {})
                    
                    interview_info = {
                        "session_id": session_id,
                        "candidate_name": user_profile.get("name", "Unknown") if user_profile else "Unknown",
                        "candidate_email": user_email or "",
                        "interview_date": interview_data.get("start_time", interview_data.get("created_at")),
                        "overall_score": evaluation.get("score", 0),
                        "technical_knowledge": evaluation.get("technical_knowledge", 0),
                        "problem_solving": evaluation.get("problem_solving", 0),
                        "communication": evaluation.get("communication", 0),
                        "experience_relevance": evaluation.get("experience_relevance", 0),
                        "hire_recommendation": evaluation.get("hire_recommendation", "no"),
                        "feedback": evaluation.get("feedback", ""),
                        "completion_reason": interview_data.get("completion_reason", "unknown"),
                        "ended_at": interview_data.get("ended_at"),
                        "duration": interview_data.get("duration", 120)
                    }
                    interviews.append(interview_info)
                elif user_session.get("status") == "ended":
                    # User session ended but no completed interview data found
                    # This can happen if the interview was ended early
                    interview_info = {
                        "session_id": session_id,
                        "candidate_name": user_profile.get("name", "Unknown") if user_profile else "Unknown", 
                        "candidate_email": user_email or "",
                        "interview_date": user_session.get("started_at"),
                        "overall_score": 0,
                        "technical_knowledge": 0,
                        "problem_solving": 0,
                        "communication": 0,
                        "experience_relevance": 0,
                        "hire_recommendation": "no",
                        "feedback": "Interview was ended early or not completed",
                        "completion_reason": user_session.get("user_action", "unknown"),
                        "ended_at": user_session.get("ended_at"),
                        "duration": user_session.get("duration_minutes", 0) * 60 if user_session.get("duration_minutes") else 0
                    }
                    interviews.append(interview_info)

        # Fallback: Check for orphaned completed interview sessions for this role
        # This handles cases where user session was cleaned up but agent session remains
        logger.info(f"DEBUG: Starting fallback search, current interviews count: {len(interviews)}")
        interview_session_keys = redis_client.scan_keys("interview_session:*")
        logger.info(f"DEBUG: Found {len(interview_session_keys)} interview sessions")
        for interview_key in interview_session_keys:
            interview_data = redis_client.get_json(interview_key)
            if interview_data and interview_data.get("status") == "completed":
                # Check if this interview is for the requested role by examining role_description
                role_description = interview_data.get("role_description", "")
                if role_data.get("title") in role_description or role_data.get("description")[:100] in role_description:
                    session_id = interview_data.get("session_id", "")
                    
                    # Check if we already have this session_id in our interviews list
                    existing_session_ids = {interview["session_id"] for interview in interviews}
                    if session_id not in existing_session_ids:
                        # This is an orphaned interview session - try to find the user
                        user_profile = None
                        user_email = ""
                        
                        # Try to extract user info from resume content or search by session timing
                        # Look for any user that might have interviewed around this time
                        user_keys = redis_client.scan_keys("user:*")
                        logger.info(f"DEBUG: Searching for user match for session {session_id}, checking {len(user_keys)} users")
                        interview_resume = interview_data.get("resume_content", "")
                        logger.info(f"DEBUG: Interview resume length: {len(interview_resume)}")
                        
                        for user_key in user_keys:
                            user_data = redis_client.get_json(user_key)
                            if user_data:
                                # Check if resume content matches (simple heuristic)
                                user_resume = user_data.get("resume", {}).get("extracted_text", "")
                                logger.info(f"DEBUG: Checking user {user_data.get('email', 'no-email')}, resume length: {len(user_resume)}")
                                if user_resume and interview_resume and user_resume == interview_resume:
                                    logger.info(f"DEBUG: Found resume match for user {user_data.get('email')}")
                                    user_profile = user_data
                                    user_email = user_data.get("email", "")
                                    break
                                elif user_resume and interview_resume:
                                    logger.info(f"DEBUG: Resume mismatch for {user_data.get('email', 'no-email')}: lengths {len(user_resume)} vs {len(interview_resume)}")

                        if not user_profile:
                            logger.info(f"DEBUG: No user match found for session {session_id}")

                        # Extract evaluation data
                        evaluation = interview_data.get("evaluation", {})
                        
                        interview_info = {
                            "session_id": session_id,
                            "candidate_name": user_profile.get("name", "Unknown") if user_profile else "Unknown",
                            "candidate_email": user_email,
                            "interview_date": interview_data.get("start_time", interview_data.get("created_at")),
                            "overall_score": evaluation.get("score", 0),
                            "technical_knowledge": evaluation.get("technical_knowledge", 0),
                            "problem_solving": evaluation.get("problem_solving", 0),
                            "communication": evaluation.get("communication", 0),
                            "experience_relevance": evaluation.get("experience_relevance", 0),
                            "hire_recommendation": evaluation.get("hire_recommendation", "no"),
                            "feedback": evaluation.get("feedback", ""),
                            "completion_reason": interview_data.get("completion_reason", "unknown"),
                            "ended_at": interview_data.get("ended_at"),
                            "duration": interview_data.get("duration", 120)
                        }
                        interviews.append(interview_info)

        # Sort by interview date (most recent first)
        interviews.sort(key=lambda x: x.get("interview_date", ""), reverse=True)
        
        # Calculate role statistics
        total_interviews = len(interviews)
        avg_score = sum(i.get("overall_score", 0) for i in interviews) / total_interviews if total_interviews > 0 else 0
        hire_recommendations = [i.get("hire_recommendation") for i in interviews]
        strong_yes_count = hire_recommendations.count("strong_yes")
        yes_count = hire_recommendations.count("yes")
        
        role_stats = {
            "total_interviews": total_interviews,
            "average_score": round(avg_score, 1),
            "strong_yes_count": strong_yes_count,
            "yes_count": yes_count,
            "hire_rate": round((strong_yes_count + yes_count) / total_interviews * 100, 1) if total_interviews > 0 else 0
        }
        
        logger.info(f"Retrieved {total_interviews} interviews for role {role_id}")
        return {
            "role": role_data,
            "interviews": interviews,
            "statistics": role_stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve role details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve role details")

@router.get("/roles")
async def get_roles(request: Request):
    """Get roles. Admins see all roles, regular users see only open roles."""
    user_data = request.state.user
    is_admin = user_data.get("admin", False)
    
    logger.info(f"Roles list requested by {'admin' if is_admin else 'user'}: {user_data.get('email')}")
    
    try:
        # Get all role IDs from index
        role_ids = redis_client.get_set_members("roles:index")
        
        if not role_ids:
            return {"roles": []}
        
        # Fetch all roles
        roles = []
        interview_keys = None  # Cache interview keys for admin users
        
        for role_id in role_ids:
            role_data = redis_client.get_json(f"roles:{role_id}")
            if role_data:
                # Filter roles based on user type
                if is_admin or role_data.get("status") == "open":
                    # Add interview count for admin users
                    if is_admin:
                        if interview_keys is None:
                            interview_keys = redis_client.scan_keys("interview_session:*")

                        interview_count = 0
                        for interview_key in interview_keys:
                            interview_data = redis_client.get_json(interview_key)
                            if interview_data and interview_data.get("status") == "completed":
                                role_description = interview_data.get("role_description", "")
                                if role_data.get("title") in role_description or role_data.get("description")[:100] in role_description:
                                    interview_count += 1
                        role_data["interview_count"] = interview_count

                    roles.append(role_data)

        # Sort by creation date (newest first)
        roles.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        logger.info(f"Retrieved {len(roles)} roles for {'admin' if is_admin else 'user'}")
        return {
            "roles": roles,
            "user_type": "admin" if is_admin else "user",
            "total_roles": len(roles)
        }

    except Exception as e:
        logger.error(f"Failed to retrieve roles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve roles")

@router.post("/admin/roles")
@mesh.route(dependencies=[
    {
        "capability": "process_with_tools",
        "tags": ["+openai"],  # tag time is optional (plus to have)
    }
])
async def create_role(role_data: RoleCreateRequest, request: Request, llm_service: McpMeshAgent = None):
    """Create a new role. Admin access required."""
    logger.info("ROLE CREATION ENDPOINT REACHED!")
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Role creation requested by admin: {user_data.get('email')}")
    
    # Validate status
    valid_statuses = ["open", "closed", "on_hold"]
    if role_data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Generate unique role ID
    role_id = f"role_{uuid.uuid4().hex[:8]}"
    
    # Generate short description using LLM service
    logger.info(f"Generating short description for role: {role_data.title}")
    short_description = await generate_short_description(
        title=role_data.title,
        description=role_data.description, 
        llm_service=llm_service
    )
    
    # Create role object
    role = {
        "role_id": role_id,
        "title": role_data.title,
        "description": role_data.description,
        "short_description": short_description,
        "status": role_data.status,
        "duration": role_data.duration,
        "created_at": datetime.now().isoformat(),
        "created_by": user_data.get("email"),
        "updated_at": datetime.now().isoformat(),
        "updated_by": user_data.get("email")
    }
    
    try:
        # Store role in Redis
        redis_client.set_json(f"roles:{role_id}", role)
        
        # Add role ID to roles index
        redis_client.add_to_set("roles:index", role_id)
        
        logger.info(f"Role created successfully: {role_id}")
        return RoleResponse(**role)

    except Exception as e:
        logger.error(f"Failed to create role: {e}")
        raise HTTPException(status_code=500, detail="Failed to create role")

@router.get("/admin/roles")
async def get_all_roles_admin(request: Request):
    """Get all roles (admin-only endpoint for backwards compatibility)."""
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Admin roles list requested by: {user_data.get('email')}")
    
    try:
        # Get all role IDs from index
        role_ids = redis_client.get_set_members("roles:index")
        
        if not role_ids:
            return {"roles": []}
        
        # Fetch all roles and add interview counts
        roles = []
        interview_keys = redis_client.scan_keys("interview_session:*")  # Get all interviews once
        logger.info(f"Admin endpoint: Found {len(interview_keys)} interview keys")
        
        for role_id in role_ids:
            role_data = redis_client.get_json(f"roles:{role_id}")
            if role_data:
                # Add interview count
                interview_count = 0
                for interview_key in interview_keys:
                    interview_data = redis_client.get_json(interview_key)
                    if interview_data and interview_data.get("status") == "completed":
                        role_description = interview_data.get("role_description", "")
                        if role_data.get("title") in role_description or role_data.get("description")[:100] in role_description:
                            interview_count += 1

                role_data["interview_count"] = interview_count
                roles.append(role_data)

        # Sort by creation date (newest first)
        roles.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        logger.info(f"Retrieved {len(roles)} roles for admin")
        return {"roles": roles}

    except Exception as e:
        logger.error(f"Failed to retrieve roles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve roles")

@router.put("/admin/roles/{role_id}")
@mesh.route(dependencies=[
    {
        "capability": "process_with_tools",
        "tags": ["+openai"],  # tag time is optional (plus to have)
    }
])
async def update_role(role_id: str, role_data: RoleCreateRequest, request: Request, llm_service: McpMeshAgent = None):
    """Update an existing role. Admin access required."""
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Role update requested by admin: {user_data.get('email')} for role: {role_id}")
    
    # Validate status
    valid_statuses = ["open", "closed", "on_hold"]
    if role_data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Check if role exists
    existing_role = redis_client.get_json(f"roles:{role_id}")
    if not existing_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Generate short description using LLM service
    logger.info(f"Generating short description for updated role: {role_data.title}")
    short_description = await generate_short_description(
        title=role_data.title,
        description=role_data.description, 
        llm_service=llm_service
    )
    
    # Update role object
    updated_role = {
        "role_id": role_id,
        "title": role_data.title,
        "description": role_data.description,
        "short_description": short_description,
        "status": role_data.status,
        "duration": role_data.duration,
        "created_at": existing_role.get("created_at"),
        "created_by": existing_role.get("created_by"),
        "updated_at": datetime.now().isoformat(),
        "updated_by": user_data.get("email")
    }
    
    try:
        # Store updated role
        redis_client.set_json(f"roles:{role_id}", updated_role)
        
        logger.info(f"Role updated successfully: {role_id}")
        return {
            "success": True,
            "role": updated_role,
            "message": f"Role '{role_data.title}' updated successfully"
        }

    except Exception as e:
        logger.error(f"Failed to update role: {e}")
        raise HTTPException(status_code=500, detail="Failed to update role")

@router.delete("/admin/roles/{role_id}")
async def delete_role(role_id: str, request: Request):
    """Delete a role. Admin access required."""
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Role deletion requested by admin: {user_data.get('email')} for role: {role_id}")
    
    # Check if role exists
    existing_role = redis_client.get_json(f"roles:{role_id}")
    if not existing_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        # Remove from index
        redis_client.remove_from_set("roles:index", role_id)
        
        # Delete role data
        redis_client.delete(f"roles:{role_id}")
        
        logger.info(f"Role deleted successfully: {role_id}")
        return {
            "success": True,
            "message": f"Role deleted successfully"
        }

    except Exception as e:
        logger.error(f"Failed to delete role: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete role")

@router.get("/interviews/{session_id}/details")
async def get_interview_details(session_id: str, request: Request):
    """Get detailed interview information including full conversation and evaluation."""
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"Interview details requested by admin: {admin_data.get('email')} for session: {session_id}")
    
    try:
        # Get interview session data
        interview_data = redis_client.get_json(f"interview_session:{session_id}")
        if not interview_data:
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        # Get user profile for candidate info
        user_email = interview_data.get("user_email", "")
        user_profile = redis_client.get_json(f"user:{user_email}") if user_email else None
        
        # Extract conversation and evaluation
        conversation = interview_data.get("conversation", [])
        evaluation = interview_data.get("evaluation", {})
        
        detailed_info = {
            "session_id": session_id,
            "candidate": {
                "name": user_profile.get("name", "Unknown") if user_profile else "Unknown",
                "email": user_email,
                "resume_info": user_profile.get("resume", {}) if user_profile else {}
            },
            "interview": {
                "started_at": interview_data.get("start_time", interview_data.get("created_at")),
                "ended_at": interview_data.get("ended_at"),
                "duration": interview_data.get("duration", 120),
                "status": interview_data.get("status"),
                "completion_reason": interview_data.get("completion_reason", "unknown")
            },
            "role_info": {
                "description": interview_data.get("role_description", ""),
                "requirements": interview_data.get("role_description", "")
            },
            "conversation": conversation,
            "evaluation": {
                "overall_score": evaluation.get("score", 0),
                "technical_knowledge": evaluation.get("technical_knowledge", 0),
                "problem_solving": evaluation.get("problem_solving", 0),
                "communication": evaluation.get("communication", 0),
                "experience_relevance": evaluation.get("experience_relevance", 0),
                "hire_recommendation": evaluation.get("hire_recommendation", "no"),
                "feedback": evaluation.get("feedback", ""),
                "evaluation_timestamp": evaluation.get("evaluation_timestamp")
            }
        }
        
        logger.info(f"Retrieved detailed info for interview {session_id}")
        return detailed_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve interview details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve interview details")

@router.get("/admin/roles/{role_id}/candidates")
async def get_role_candidates(role_id: str, request: Request):
    """Get candidates who interviewed for a specific role. Admin access required."""
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"Role candidates requested by admin: {admin_data.get('email')} for role: {role_id}")
    
    try:
        # Get completed interviews for this role using simplified email-based approach
        candidates = []
        
        # Get all user interview sessions and check for this role
        user_interview_keys = redis_client.scan_keys("user_interview:*")
        
        for user_interview_key in user_interview_keys:
            user_session = redis_client.get_json(user_interview_key)
            if user_session and user_session.get("role_id") == role_id:
                # This user interviewed for this role
                user_email = user_session.get("user_email")
                session_id = user_session.get("session_id")
                
                # Get user data directly by email
                user_data = redis_client.get_json(f"user:{user_email}") if user_email else None
                user_name = user_data.get("name", "Unknown") if user_data else "Unknown"
                
                # Check if the interview was completed
                if user_session.get("status") in ["ended", "completed"]:
                    # Get evaluation data from agent session
                    interview_session_key = f"interview_session:{session_id}"
                    interview_data = redis_client.get_json(interview_session_key)
                    
                    evaluation = interview_data.get("evaluation", {}) if interview_data else {}
                    
                    candidate_info = {
                        "user_email": user_email,
                        "user_name": user_name,
                        "interview_date": user_session.get("started_at"),
                        "status": "completed",
                        "questions_asked": len(interview_data.get("conversation", [])) if interview_data else 0,
                        "total_score": evaluation.get("score", 0),
                        "completion_reason": user_session.get("user_action", "completed")
                    }
                    candidates.append(candidate_info)

        
        # Sort by interview date (most recent first)
        candidates.sort(key=lambda x: x.get("interview_date", ""), reverse=True)
        
        logger.info(f"Retrieved {len(candidates)} candidates for role {role_id}")
        return {"candidates": candidates}

    except Exception as e:
        logger.error(f"Failed to retrieve role candidates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve candidates")
