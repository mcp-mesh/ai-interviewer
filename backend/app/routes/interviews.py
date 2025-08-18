"""
Interview management routes - MCP Mesh Integration.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
import mesh
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from mesh.types import McpMeshAgent

from app.models.schemas import InterviewStartRequest, InterviewAnswerRequest
from app.database.redis_client import redis_client
from app.config import DEV_MODE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interviews", tags=["interviews"])

async def generate_interview_response(user_email: str, candidate_answer: str, interview_conductor: McpMeshAgent, session_checker: McpMeshAgent):
    """Generate streaming response for interview answer."""
    try:
        # Send processing message
        yield f"data: {json.dumps({'type': 'processing', 'message': 'Analyzing your answer...', 'timestamp': datetime.now().isoformat()})}\n\n"
        
        # Get session data
        user_session_key = f"user_interview:{user_email}"
        session_data = redis_client.get_json(user_session_key)
        
        if not session_data:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No active interview session found'})}\n\n"
            return
        
        # Get session details
        session_id = session_data["session_id"]
        
        # Check session status using injected function via MCP Mesh
        if not session_checker:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Interview service unavailable'})}\n\n"
            return
            
        session_status = await session_checker(
            session_id=session_id
        )
        
        if not session_status or not session_status.get("success"):
            yield f"data: {json.dumps({'type': 'error', 'message': 'Interview session not found'})}\n\n"
            return
            
        if session_status.get("status") != "started":
            yield f"data: {json.dumps({'type': 'expired', 'message': 'Interview session has expired', 'timestamp': datetime.now().isoformat()})}\n\n"
            return
        
        # Get role and resume data
        resume_content = ""
        user_data = redis_client.get_json(f"user:{user_email}")
        if user_data:
            resume_content = user_data.get("resume", {}).get("extracted_text", "")
        
        # Get role data from Redis
        role_data = redis_client.get_json(f"roles:{session_data['role_id']}")
        if not role_data:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Role not found'})}\n\n"
            return
            
        role_description = f"Title: {role_data['title']}\nDescription: {role_data['description']}"
        role_duration = role_data.get('duration', 30)  # Default to 30 if not set
        
        # 1. Get session details for agent call
        
        # 2. Call interview agent with answer (agent will handle saving answer to conversation)
        logger.info(f"Submitting answer for user {user_email}: {candidate_answer[:50]}...")
        
        interview_result = await interview_conductor(
            resume_content=resume_content,
            role_description=role_description,
            user_session_id=session_id,
            candidate_answer=candidate_answer,
            duration_minutes=role_duration
        )
        
        if not interview_result or not interview_result.get("success"):
            error_msg = interview_result.get('error', 'Failed to process answer') if interview_result else 'No response from interview agent'
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            return
        
        # Send evaluation feedback if available
        yield f"data: {json.dumps({'type': 'evaluation', 'message': 'Answer processed successfully', 'timestamp': datetime.now().isoformat()})}\n\n"
        
        # Check if we have a next question
        if interview_result.get("question"):
            # Interview agent has handled all session state management
            # Send the next question with updated session info from agent
            session_info = interview_result.get("session_info", {})
            session_info["session_id"] = session_id  # Ensure session_id is included
            yield f"data: {json.dumps({'type': 'question', 'content': interview_result.get('question'), 'metadata': interview_result.get('question_metadata', {}), 'session_info': session_info, 'timestamp': datetime.now().isoformat()})}\n\n"
        else:
            # No more questions - interview is complete (handled by agent)
            yield f"data: {json.dumps({'type': 'interview_complete', 'message': 'Interview completed', 'session_id': session_id, 'timestamp': datetime.now().isoformat()})}\n\n"
        
        # Send completion marker
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in interview response generation: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': f'Server error: {str(e)}'})}\n\n"

async def resume_interview_with_history(user_session: dict, remaining_time: int, agent_session_key: str, interview_conductor: McpMeshAgent):
    """Resume interview session with proper conversation state handling."""
    
    # 1. Get conversation history from agent session
    agent_session = redis_client.get_json(agent_session_key)
    if not agent_session or "conversation" not in agent_session:
        raise HTTPException(500, "Interview session data corrupted")
    
    conversation = agent_session["conversation"]
    
    if not conversation:
        # No conversation yet, start fresh
        current_question = user_session.get("current_question")
        if not current_question:
            raise HTTPException(500, "No question available to resume")
        
        return {
            "success": True,
            "resumed": True,
            "session_id": user_session["session_id"],
            "role": {
                "id": user_session["role_id"],
                "title": user_session["role_title"],
                "description": user_session["role_description"]
            },
            "time_remaining_seconds": int(remaining_time),
            "current_question": current_question,
            "question_metadata": user_session.get("question_metadata", {}),
            "conversation_history": [],
            "questions_asked": user_session.get("questions_asked", 1),
            "message": "Interview resumed - no previous conversation"
        }
    
    # 2. Determine conversation state from last message
    last_message = conversation[-1]
    last_message_type = last_message.get("type", "")
    
    if last_message_type == "question":
        # Last message was AI question - user needs to answer
        return {
            "success": True,
            "resumed": True,
            "session_id": user_session["session_id"],
            "role": {
                "id": user_session["role_id"],
                "title": user_session["role_title"],
                "description": user_session["role_description"]
            },
            "time_remaining_seconds": int(remaining_time),
            "current_question": last_message["content"],
            "question_metadata": user_session.get("question_metadata", {}),
            "conversation_history": conversation[:-1],  # All except current question
            "questions_asked": user_session.get("questions_asked", 1),
            "message": "Interview resumed - please answer the current question"
        }
    
    elif last_message_type == "answer":
        # Last message was user answer - need to get next question from AI
        logger.info(f"Resume: Last message was user answer, getting next question from AI")
        
        try:
            # Get next question from interview capability using MCP Mesh
            interview_result = await interview_conductor(
                resume_content=agent_session["resume_content"],
                role_description=agent_session["role_description"],
                user_session_id=user_session["session_id"],
                candidate_answer=last_message["content"],  # Process the last answer
                duration_minutes=user_session.get("duration_minutes", 30)
            )
            
            if not interview_result or not interview_result.get("success"):
                raise HTTPException(500, "Failed to get next question from AI")
            
            if interview_result.get("question"):
                # Update user session with new question
                user_session["current_question"] = interview_result["question"]
                user_session["question_metadata"] = interview_result.get("question_metadata", {})
                user_session["questions_asked"] = user_session.get("questions_asked", 0) + 1
                user_session["last_updated"] = datetime.now().isoformat()
                
                # Save updated session
                user_session_key = f"user_interview:{user_session['user_email']}"
                redis_client.set_json(user_session_key, user_session)
                
                return {
                    "success": True,
                    "resumed": True,
                    "session_id": user_session["session_id"],
                    "role": {
                        "id": user_session["role_id"],
                        "title": user_session["role_title"],
                        "description": user_session["role_description"]
                    },
                    "time_remaining_seconds": int(remaining_time),
                    "current_question": interview_result["question"],
                    "question_metadata": interview_result.get("question_metadata", {}),
                    "conversation_history": conversation,  # Full history including last answer
                    "questions_asked": user_session["questions_asked"],
                    "message": "Interview resumed - new question generated"
                }
            else:
                # No more questions - interview should end
                user_session["status"] = "ended"
                user_session["user_action"] = "completed"
                user_session["ended_at"] = datetime.now().isoformat()
                
                user_session_key = f"user_interview:{user_session['user_email']}"
                redis_client.set_json(user_session_key, user_session)
                
                # Update lookup
                lookup_key = f"user_role_lookup:{user_session['user_email']}:{user_session['role_id']}"
                lookup_data = redis_client.get_json(lookup_key)
                if lookup_data:
                    lookup_data["last_updated"] = datetime.now().isoformat()
                    redis_client.set_json(lookup_key, lookup_data)
                
                return {
                    "success": True,
                    "resumed": False,
                    "completed": True,
                    "session_id": user_session["session_id"],
                    "conversation_history": conversation,
                    "message": "Interview completed - no more questions available"
                }
                
        except Exception as e:
            logger.error(f"Failed to process resume with AI: {e}")
            raise HTTPException(500, "Failed to resume interview - AI processing error")
    
    else:
        # Unknown message type or corrupted conversation
        raise HTTPException(500, f"Unknown conversation state: {last_message_type}")

@router.post("/start")
@mesh.route(dependencies=["conduct_interview", "get_session_status"])
async def start_interview(
    request_data: InterviewStartRequest, 
    request: Request,
    interview_conductor: McpMeshAgent = None,  # Injected interview capability
    session_checker: McpMeshAgent = None  # Injected session status capability
):
    """Initialize new interview session or resume existing one."""
    user_data = request.state.user
    user_email = user_data.get('email')
    
    logger.info(f"Starting interview for user: {user_email}, role: {request_data.role_id}")
    
    # 1. Check if user has uploaded resume
    if not user_data.get("resume"):
        raise HTTPException(
            status_code=400,
            detail="Please upload your resume before starting an interview"
        )
    
    # 2. Get role details from Redis
    role_data = redis_client.get_json(f"roles:{request_data.role_id}")
    if not role_data:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    
    # Check if interview capabilities are available
    if not interview_conductor or not session_checker:
        raise HTTPException(status_code=503, detail="Interview service unavailable")

    # 3. Check for existing session using lookup pattern
    lookup_key = f"user_role_lookup:{user_email}:{request_data.role_id}"
    existing_lookup = redis_client.get_json(lookup_key)
    
    if existing_lookup:
        # Get the actual session data to check status
        user_session_key = existing_lookup["user_session_key"]
        existing_session = redis_client.get_json(user_session_key)
        
        if existing_session:
            # Use injected capability to get session status via MCP Mesh
            session_status = await session_checker(
                session_id=existing_session["session_id"]
            )
            
            if not session_status or not session_status.get("success"):
                # Session not found in agent, clean up lookup
                redis_client.delete(user_session_key)
                redis_client.delete(lookup_key)
            else:
                status = session_status.get("status")
                if status in ["ended", "completed", "processing"]:
                    raise HTTPException(409, "Interview already completed for this role")
                
                if status == "started":
                    # Return resume data from agent
                    return {
                        "success": True,
                        "resumed": True,
                        "session_id": session_status.get("session_id"),
                        "role": {
                            "id": request_data.role_id,
                            "title": role_data["title"],
                            "description": role_data["description"]
                        },
                        "duration_minutes": session_status.get("duration_minutes"),
                        "time_remaining_seconds": session_status.get("time_remaining_seconds"),
                        "current_question": session_status.get("current_question"),
                        "question_metadata": session_status.get("question_metadata", {}),
                        "conversation_history": session_status.get("conversation_history", []),
                        "questions_asked": session_status.get("questions_asked"),
                        "message": "Interview resumed successfully"
                    }
    
    # 4. Create new interview session
    resume_content = user_data["resume"].get("extracted_text", "")
    role_description = f"Title: {role_data['title']}\nDescription: {role_data['description']}"
    
    # Generate unique session_id for each interview to avoid conversation history accumulation
    session_id = f"interview_{uuid.uuid4().hex[:12]}"
    
    try:
        # Call interview capability to create session and get first question via MCP Mesh
        role_duration = role_data.get("duration", 30)  # Default to 30 minutes if not set
        interview_result = await interview_conductor(
            resume_content=resume_content,
            role_description=role_description,
            user_session_id=session_id,
            duration_minutes=role_duration
            # Don't pass candidate_answer for initial question
        )
        
        logger.info(f"Interview agent response: {interview_result}")
        
        if not interview_result or not interview_result.get("success"):
            error_msg = interview_result.get('error', 'Unknown error') if interview_result else 'No response from interview agent'
            logger.error(f"Interview agent failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start interview: {error_msg}"
            )
        
        # 5. Store minimal lookup table
        duration_seconds = role_duration * 60
        user_session_key = f"user_interview:{user_email}"
        minimal_lookup = {
            "session_id": session_id,
            "user_email": user_email,
            "role_id": request_data.role_id,
            "created_at": datetime.now().isoformat()
        }
        
        # Store minimal lookup (no TTL - needed for role-based duplicate prevention)
        redis_client.set_json(user_session_key, minimal_lookup)
        
        # 6. Create lookup entry for per-role tracking
        lookup_data = {
            "session_id": session_id,
            "user_session_key": user_session_key,
            "agent_session_key": f"interview_session:{session_id}",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        redis_client.set_json(lookup_key, lookup_data)
        
        logger.info(f"Interview session created for user {user_email}, role {request_data.role_id}")
        
        return {
            "success": True,
            "resumed": False,  # New session
            "session_id": session_id,
            "role": {
                "id": request_data.role_id,
                "title": role_data["title"],
                "description": role_data["description"]
            },
            "duration_minutes": role_duration,
            "time_remaining_seconds": duration_seconds,
            "current_question": interview_result.get("question"),
            "question_metadata": interview_result.get("question_metadata", {}),
            "conversation_history": [],  # New session has no history
            "questions_asked": 1,
            "message": "Interview started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to start interview")

@router.post("/end")
@mesh.route(dependencies=["end_interview_session"])
async def end_interview(
    request: Request,
    session_ender: McpMeshAgent = None  # Injected end interview capability
):
    """Manually end the current interview session."""
    user_data = request.state.user
    user_email = user_data.get('email')
    
    logger.info(f"Ending interview for user: {user_email}")
    
    # Get session lookup
    user_session_key = f"user_interview:{user_email}"
    session_lookup = redis_client.get_json(user_session_key)
    
    if not session_lookup:
        raise HTTPException(404, "No active interview session")
    
    if not session_ender:
        raise HTTPException(status_code=503, detail="Interview service unavailable")
    
    # End session using injected capability via MCP Mesh
    end_result = await session_ender(
        session_id=session_lookup["session_id"],
        reason="ended_manually"
    )
    
    if not end_result or not end_result.get("success"):
        raise HTTPException(500, f"Failed to end interview: {end_result.get('error', 'Unknown error')}")
    
    # Trigger background scoring async (don't wait for result)
    try:
        asyncio.create_task(trigger_scoring_async({
            "session_id": session_lookup["session_id"]
        }))
    except Exception as e:
        logger.warning(f"Failed to trigger async scoring for session {session_lookup['session_id']}: {e}")
    
    return {
        "success": True,
        "message": "Interview ended successfully",
        "session_id": session_lookup["session_id"],
        "ended_at": datetime.now().isoformat()
    }

async def trigger_scoring_async(session: dict):
    """Trigger background scoring for completed session."""
    try:
        logger.info(f"Triggering async scoring for session: {session['session_id']}")
        # Note: This function now needs interview_agent parameter passed from caller
        # For now, skip triggering scoring directly in this async function
        logger.info(f"Async scoring needs to be implemented separately for session: {session['session_id']}")
        return
        if result and result.get("success"):
            logger.info(f"Successfully scored session {session['session_id']}: score={result.get('score', 0)}")
        else:
            logger.error(f"Failed to score session {session['session_id']}: {result}")
    except Exception as e:
        logger.error(f"Error in async scoring for session {session['session_id']}: {e}")

@router.post("/finalize/batch")
@mesh.route(dependencies=["finalize_interview"])
async def finalize_pending_sessions(finalize_interview: McpMeshAgent = None):
    """Internal endpoint to finalize all pending sessions via MCP Mesh DI."""
    try:
        logger.info("Starting batch finalization of pending sessions")
        
        from app.database.redis_client import redis_client
        from datetime import datetime, timezone
        
        # Find all sessions that need finalization
        session_pattern = "interview_session:*"
        session_keys = redis_client.scan_keys(session_pattern)
        
        results = []
        finalized_count = 0
        
        for session_key in session_keys:
            try:
                session_id = session_key.replace("interview_session:", "")
                session_data = redis_client.get_json(session_key)
                
                if not session_data:
                    continue
                
                status = session_data.get("status")
                should_finalize = False
                reason = ""
                
                # Check if session needs finalization
                if status == "started":
                    # Check if expired by time (expires_at) OR by duration (start_time + duration)
                    expires_at = session_data.get("expires_at", 0)
                    current_time = datetime.now(timezone.utc).timestamp()
                    
                    # Also check start_time + duration for sessions that might not have expires_at
                    start_time_str = session_data.get("start_time")
                    duration = session_data.get("duration", 1800)  # Default 30 minutes
                    duration_expired = False
                    
                    if start_time_str:
                        try:
                            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                            elapsed_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
                            duration_expired = elapsed_seconds > duration
                        except Exception as e:
                            logger.error(f"Error parsing start_time for session {session_id}: {e}")
                    
                    if current_time >= expires_at or duration_expired:
                        # First mark as ended, then finalize
                        session_data["status"] = "ended"
                        session_data["ended_at"] = datetime.now(timezone.utc).isoformat()
                        session_data["user_action"] = "expired_timeout" if duration_expired else "expired_time"
                        redis_client.set_json(session_key, session_data)
                        
                        should_finalize = True
                        reason = "duration_timeout" if duration_expired else "expires_at_timeout"
                        logger.info(f"Session {session_id} expired ({reason}), marked as ended and queued for finalization")
                
                elif status == "ended":
                    if not session_data.get("evaluation"):
                        # Session was ended manually but not finalized
                        should_finalize = True
                        reason = "manual_end"
                    else:
                        # Session has evaluation but status not updated - fix status only
                        session_data["status"] = "completed"
                        redis_client.set_json(session_key, session_data)
                        logger.info(f"Updated session {session_id} status from 'ended' to 'completed' (already evaluated)")
                
                if should_finalize:
                    logger.info(f"Finalizing session {session_id} (reason: {reason})")
                    
                    # Finalize via MCP Mesh DI
                    result = await finalize_interview(session_id=session_id)
                    
                    if result and result.get("success"):
                        finalized_count += 1
                        results.append({
                            "session_id": session_id,
                            "success": True,
                            "score": result.get("score", 0),
                            "reason": reason
                        })
                        logger.info(f"Successfully finalized session {session_id}: score={result.get('score', 0)}")
                    else:
                        error_msg = result.get("error", "Unknown error") if result else "No response"
                        results.append({
                            "session_id": session_id,
                            "success": False,
                            "error": error_msg,
                            "reason": reason
                        })
                        logger.error(f"Failed to finalize session {session_id}: {error_msg}")
                        
            except Exception as e:
                logger.error(f"Error processing session {session_key}: {e}")
                results.append({
                    "session_id": session_id,
                    "success": False,
                    "error": str(e)
                })
        
        logger.info(f"Batch finalization complete: {finalized_count}/{len(results)} sessions finalized")
        
        return {
            "success": True,
            "finalized_count": finalized_count,
            "total_processed": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch finalize endpoint: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/status")
@mesh.route(dependencies=["get_session_status"])
async def get_interview_status(
    request: Request,
    session_checker: McpMeshAgent = None  # Injected session status capability
):
    """Get current interview session status for the authenticated user."""
    user_data = request.state.user
    user_email = user_data.get('email')
    
    logger.info(f"Interview status requested by user: {user_email}")
    
    # Check for session lookup
    user_session_key = f"user_interview:{user_email}"
    session_lookup = redis_client.get_json(user_session_key)
    
    if not session_lookup:
        return {
            "has_active_session": False,
            "status": "no_session"
        }
    
    if not session_checker:
        return {
            "has_active_session": False,
            "status": "service_unavailable"
        }

    # Check session status with injected capability via MCP Mesh
    session_status = await session_checker(
        session_id=session_lookup["session_id"]
    )
    
    if not session_status or not session_status.get("success"):
        # Clean up orphaned lookup
        redis_client.delete(user_session_key)
        return {
            "has_active_session": False,
            "status": "no_session"
        }
    
    status = session_status.get("status")
    if status != "started":
        return {
            "has_active_session": False,
            "status": status or "unknown"
        }
    
    # User has an active session
    return {
        "has_active_session": True,
        "status": "active",
        "session_id": session_lookup.get("session_id"),
        "role_id": session_lookup.get("role_id"),
        "started_at": session_status.get("started_at")
    }

@router.get("/current")
@mesh.route(dependencies=["get_session_status"])
async def get_current_interview_question(
    request: Request,
    session_checker: McpMeshAgent = None  # Injected session status capability
):
    """Get the current question for the active interview session."""
    user_data = request.state.user
    user_email = user_data.get('email')
    
    logger.info(f"Current question requested by user: {user_email}")
    
    # Get session lookup
    user_session_key = f"user_interview:{user_email}"
    session_lookup = redis_client.get_json(user_session_key)
    
    if not session_lookup:
        raise HTTPException(
            status_code=404,
            detail="No active interview session found"
        )
    
    if not session_checker:
        raise HTTPException(status_code=503, detail="Interview service unavailable")
    
    # Get session status from injected capability via MCP Mesh
    session_status = await session_checker(
        session_id=session_lookup["session_id"]
    )
    
    if not session_status or not session_status.get("success"):
        raise HTTPException(
            status_code=404,
            detail="Interview session not found"
        )
    
    status = session_status.get("status")
    if status != "started":
        raise HTTPException(
            status_code=410,
            detail=f"Interview session is {status}"
        )
    
    # Return session data from interview agent
    conversation_history = session_status.get("conversation_history", [])
    
    # Filter conversation history to exclude current question for UI display
    if conversation_history:
        last_message = conversation_history[-1] if conversation_history else None
        if last_message and last_message.get("type") == "question":
            conversation_history = conversation_history[:-1]  # All except current question
    
    questions_asked = session_status.get("questions_asked", 1)
    return {
        "session_id": session_status.get("session_id"),
        "current_question": session_status.get("current_question"),
        "question_metadata": session_status.get("question_metadata", {}),
        "questions_asked": questions_asked,
        "total_questions": questions_asked,
        "total_answers": questions_asked - 1,
        "role_title": session_lookup.get("role_id"),  # Will be resolved by frontend
        "duration_minutes": session_status.get("duration_minutes"),
        "time_remaining_seconds": session_status.get("time_remaining_seconds"),
        "expires_at": session_status.get("expires_at"),
        "started_at": session_status.get("started_at"),
        "session_status": status,
        "status": "active",  # Legacy field for compatibility
        "conversation_history": conversation_history,
        "resumed": len(conversation_history) > 0
    }

@router.post("/answer")
@mesh.route(dependencies=["conduct_interview", "get_session_status"])
async def submit_interview_answer(
    request_data: InterviewAnswerRequest, 
    request: Request,
    interview_conductor: McpMeshAgent = None,  # Injected interview capability
    session_checker: McpMeshAgent = None  # Injected session status capability
):
    """Submit answer and get next question via Server-Sent Events stream."""
    user_data = request.state.user
    user_email = user_data.get('email')
    
    logger.info(f"Received answer from user: {user_email}")
    
    # Validate answer
    if not request_data.answer.strip():
        raise HTTPException(
            status_code=400,
            detail="Answer cannot be empty"
        )
    
    # Check if user has active interview session
    user_session_key = f"user_interview:{user_email}"
    existing_session = redis_client.get_json(user_session_key)
    
    if not existing_session:
        raise HTTPException(
            status_code=400,
            detail="No active interview session found. Please start an interview first."
        )
    
    if not interview_conductor or not session_checker:
        raise HTTPException(status_code=503, detail="Interview service unavailable")

    # Check session status with injected capability via MCP Mesh
    session_status = await session_checker(
        session_id=existing_session["session_id"]
    )
    
    if not session_status or not session_status.get("success"):
        # Clean up orphaned lookup
        redis_client.delete(user_session_key)
        raise HTTPException(
            status_code=400,
            detail="Interview session not found"
        )
    
    status = session_status.get("status")
    if status != "started":
        raise HTTPException(
            status_code=410,
            detail=f"Interview session is {status}"
        )
    
    # Return streaming response with injected interview capabilities
    return StreamingResponse(
        generate_interview_response(user_email, request_data.answer, interview_conductor, session_checker),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable NGINX buffering
        }
    )
