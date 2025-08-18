"""
Admin management routes.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException

from app.database.redis_client import redis_client
from app.middleware.auth import check_admin_access

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/users")
async def get_all_users(request: Request):
    """Get all users. Admin access required."""
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Users list requested by admin: {user_data.get('email')}")
    
    try:
        # Get all user keys (the actual user data is stored as user:email)
        user_keys = redis_client.scan_keys("user:*")
        
        users = []
        for user_key in user_keys:
            user_data = redis_client.get_json(user_key)
            if user_data:
                # Transform the user data to match expected format
                user_profile = {
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                    "admin": user_data.get("admin", False),
                    "blocked": user_data.get("blocked", False),
                    "created_at": user_data.get("created_at"),
                    "last_login": user_data.get("last_active", user_data.get("created_at")),
                    "provider": "google",  # Assuming Google OAuth
                    "notes": user_data.get("notes", "")
                }
                users.append(user_profile)
        
        # Sort by last_login (most recent first)
        users.sort(key=lambda x: x.get("last_login", ""), reverse=True)
        
        logger.info(f"Retrieved {len(users)} users for admin")
        return {"users": users}
        
    except Exception as e:
        logger.error(f"Failed to retrieve users: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve users")

@router.put("/users/{user_email}")
async def update_user(user_email: str, user_update: dict, request: Request):
    """Update user profile. Admin access required."""
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"User update requested by admin: {admin_data.get('email')} for user: {user_email}")
    
    # Get user directly by email key
    user_key = f"user:{user_email}"
    user_profile = redis_client.get_json(user_key)
    
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update allowed fields
    allowed_fields = ["admin", "blocked", "notes"]
    for field in allowed_fields:
        if field in user_update:
            user_profile[field] = user_update[field]
    
    user_profile["updated_at"] = datetime.now().isoformat()
    user_profile["updated_by"] = admin_data.get("email")
    
    try:
        # Store updated user profile back to the user key
        redis_client.set_json(user_key, user_profile)
        
        logger.info(f"User profile updated successfully: {user_email}")
        return {
            "success": True,
            "user": user_profile,
            "message": "User updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.get("/debug/interview-keys")
async def debug_interview_keys(request: Request):
    """Debug endpoint to check interview keys. Admin access required."""
    check_admin_access(request)
    
    try:
        interview_keys = redis_client.scan_keys("interview_session:*")
        logger.info(f"DEBUG ENDPOINT: Found {len(interview_keys)} interview session keys: {interview_keys}")
        
        keys_data = []
        for key in interview_keys[:5]:  # Only show first 5 to avoid flooding
            data = redis_client.get_json(key)
            keys_data.append({
                "key": key,
                "session_id": data.get("session_id") if data else None,
                "status": data.get("status") if data else None,
                "user_email": data.get("user_email") if data else None
            })
        
        return {
            "total_keys": len(interview_keys),
            "sample_keys": keys_data
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/user-matching/{user_email}")
async def debug_user_matching(user_email: str, request: Request):
    """Debug endpoint to trace user matching logic for specific user email."""
    check_admin_access(request)
    
    try:
        result = {
            "user_email": user_email,
            "user_data": None,
            "interview_sessions": [],
            "matching_attempts": []
        }
        
        # 1. Get user data directly by email
        user_data = redis_client.get_json(f"user:{user_email}")
        result["user_data"] = user_data
        
        # 2. Get all interview sessions and check matching
        interview_keys = redis_client.scan_keys("interview_session:*")
        
        for interview_key in interview_keys:
            interview_data = redis_client.get_json(interview_key)
            if interview_data:
                session_id = interview_data.get("session_id", "")
                session_user_email = interview_data.get("user_email", "")
                status = interview_data.get("status", "")
                
                interview_info = {
                    "key": interview_key,
                    "session_id": session_id,
                    "user_email": session_user_email,
                    "status": status,
                    "matches": []
                }
                
                # Test email matching
                if session_user_email == user_email:
                    interview_info["matches"].append("email_match")
                
                # Only include interviews that have some data
                if session_id or session_user_email or status:
                    result["interview_sessions"].append(interview_info)
        
        # 3. Check user interview session
        user_session_key = f"user_interview:{user_email}"
        user_session = redis_client.get_json(user_session_key)
        
        # 4. Create matching summary
        matching_sessions = [s for s in result["interview_sessions"] if s["matches"]]
        completed_matching_sessions = [s for s in matching_sessions if s["status"] == "completed"]
        
        result["summary"] = {
            "user_session_exists": user_session is not None,
            "user_session_data": user_session,
            "total_interviews": len(result["interview_sessions"]),
            "matching_interviews": len(matching_sessions),
            "completed_matching_interviews": len(completed_matching_sessions),
            "matching_session_ids": [s["session_id"] for s in matching_sessions]
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e), "traceback": str(e)}

@router.get("/users/{user_email}/interviews")
async def get_user_interviews_admin(user_email: str, request: Request):
    """Get user's interview history. Admin access required."""
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"User interviews requested by admin: {admin_data.get('email')} for user: {user_email}")
    
    try:
        # Get user data directly by email
        user_data = redis_client.get_json(f"user:{user_email}")
        
        if not user_data:
            logger.warning(f"No user found for {user_email}")
            return {"interviews": []}
        
        # Search for completed interviews for this user
        interviews = []
        
        # Scan for all user_role_lookup keys for this user
        lookup_pattern = f"user_role_lookup:{user_email}:*"
        lookup_keys = redis_client.scan_keys(lookup_pattern)
        
        for lookup_key in lookup_keys:
            try:
                lookup_data = redis_client.get_json(lookup_key)
                if not lookup_data:
                    continue
                    
                session_id = lookup_data.get("session_id")
                if not session_id:
                    continue
                
                # Get the interview agent session data
                interview_session_key = f"interview_session:{session_id}"
                interview_data = redis_client.get_json(interview_session_key)
                
                if interview_data and interview_data.get("status") == "completed":
                    # Extract role ID from lookup key
                    role_id = lookup_key.split(":")[-1]  # Extract role_id from key
                    
                    # Get role details
                    role_data = redis_client.get_json(f"roles:{role_id}")
                    role_title = role_data.get("title", "Unknown Role") if role_data else "Unknown Role"
                    
                    # Extract evaluation data from interview data
                    evaluation = interview_data.get("evaluation", {})
                    conversation = interview_data.get("conversation", [])
                    
                    interview_info = {
                        "session_id": session_id,
                        "role_id": role_id,
                        "role_title": role_title,
                        "started_at": interview_data.get("started_at"),
                        "ended_at": interview_data.get("ended_at"),
                        "status": interview_data.get("status"),
                        "questions_asked": len([m for m in conversation if m.get("type") == "question"]),
                        "answers_given": len([m for m in conversation if m.get("type") == "answer"]),
                        "total_score": evaluation.get("score", 0),
                        "technical_knowledge": evaluation.get("technical_knowledge", 0),
                        "problem_solving": evaluation.get("problem_solving", 0),
                        "communication": evaluation.get("communication", 0),
                        "experience_relevance": evaluation.get("experience_relevance", 0),
                        "hire_recommendation": evaluation.get("hire_recommendation", "unknown"),
                        "feedback": evaluation.get("feedback", ""),
                        "duration_minutes": interview_data.get("duration_minutes", 0),
                        "completion_reason": interview_data.get("completion_reason", "unknown")
                    }
                    interviews.append(interview_info)
                    
            except Exception as e:
                logger.error(f"Error processing lookup {lookup_key}: {e}")
                continue
        
        # Sort by started_at (most recent first)
        interviews.sort(key=lambda x: x.get("started_at") or "", reverse=True)
        
        logger.info(f"Retrieved {len(interviews)} interviews for user {user_email}")
        return {"interviews": interviews}
        
    except Exception as e:
        logger.error(f"Failed to retrieve user interviews: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve interviews")

@router.post("/users/{user_email}/reset-interview/{role_id}")
async def reset_user_interview(user_email: str, role_id: str, request: Request):
    """Allow user to retake an interview for a specific role. Admin access required."""
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"Interview reset requested by admin: {admin_data.get('email')} for user: {user_email}, role: {role_id}")
    
    try:
        # 1. Remove the user_role_lookup key for this specific role (this is what makes interviews show up)
        user_role_lookup_key = f"user_role_lookup:{user_email}:{role_id}"
        lookup_data = redis_client.get_json(user_role_lookup_key)
        
        if lookup_data:
            session_id = lookup_data.get("session_id")
            logger.info(f"Found lookup data for session_id: {session_id}")
            
            # Remove the lookup key (this prevents interview from showing in list)
            redis_client.delete(user_role_lookup_key)
            logger.info(f"Deleted user_role_lookup key: {user_role_lookup_key}")
            
            # Remove the interview agent session
            if session_id:
                agent_session_key = f"interview_session:{session_id}"
                redis_client.delete(agent_session_key) 
                logger.info(f"Deleted interview session: {agent_session_key}")
        
        # 2. Remove user_interview session if it matches this role
        user_session_key = f"user_interview:{user_email}"
        existing_session = redis_client.get_json(user_session_key)
        
        if existing_session and existing_session.get("role_id") == role_id:
            redis_client.delete(user_session_key)
            logger.info(f"Deleted current user session: {user_session_key}")
        
        logger.info(f"Interview reset successful for user {user_email} and role {role_id}")
        return {
            "success": True,
            "message": f"User can now retake the interview for this role"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset interview")