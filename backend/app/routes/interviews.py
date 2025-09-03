"""
Phase 2 Backend - Interview API Routes

Clean delegation to interview_agent via MCP Mesh dependency injection.
Supports SSE streaming for real-time interview experience with PostgreSQL backend.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import mesh
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from mesh.types import McpMeshAgent
from pydantic import BaseModel

from app.utils.auth import require_user_from_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interviews", tags=["interviews"])


class InterviewStartRequest(BaseModel):
    """Request model for starting an interview"""
    job_id: str
    application_id: str


class InterviewAnswerRequest(BaseModel):
    """Request model for submitting interview answers"""
    answer: str
    job_id: str


class InterviewEndRequest(BaseModel):
    """Request model for ending interview"""
    job_id: str
    reason: Optional[str] = "user_requested"


@router.post("/start")
@mesh.route(dependencies=["conduct_interview"])
async def start_interview(
    request: Request,
    request_data: InterviewStartRequest,
    interview_conductor: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Start a new interview session or resume existing one.
    
    Creates new interview session with PostgreSQL storage and application integration.
    Returns session details with first question and remaining duration.
    """
    try:
        # Extract user info from JWT token - authentication required
        user_info = require_user_from_request(request)
        user_email = user_info["email"]
        
        logger.info(f"Starting interview for user: {user_email}, job: {request_data.job_id}, application: {request_data.application_id}")
        
        # Call interview conductor via MCP Mesh to start interview
        interview_result = await interview_conductor(
            job_id=request_data.job_id,
            user_email=user_email,
            application_id=request_data.application_id
        )
        
        if not interview_result or not interview_result.get("success"):
            error_msg = interview_result.get("error", "Failed to start interview") if interview_result else "No response from interview agent"
            logger.error(f"Interview start failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Interview started successfully: session_id={interview_result.get('session_id')}")
        
        # Extract timing information - NEW: Include remaining duration
        metadata = interview_result.get("metadata", {})
        duration_info = {
            "time_remaining_seconds": metadata.get("time_remaining_seconds", 0),
            "duration_minutes": interview_result.get("interview_context", {}).get("duration_minutes"),
            "session_started": interview_result.get("interview_context", {}).get("session_started"),
        }
        
        return {
            "success": True,
            "message": "Interview started successfully",
            "session_id": interview_result.get("session_id"),
            "status": interview_result.get("status"),
            "phase": interview_result.get("phase"),
            "question": {
                "text": interview_result.get("question_text"),
                "metadata": interview_result.get("question_metadata", {}),
                "number": interview_result.get("question", {}).get("number", 1)
            },
            "interview_context": interview_result.get("interview_context", {}),
            "timing": duration_info,
            "session_info": {
                "questions_asked": metadata.get("total_questions", 1),
                "questions_answered": metadata.get("questions_answered", 0),
                "conversation_length": metadata.get("conversation_length", 1)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


@router.get("/current")
@mesh.route(dependencies=["get_current_interview_state"])
async def get_current_interview_state(
    request: Request,
    jobId: str = Query(...),
    interview_state_getter: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Get or create interview state for user-job pair.
    
    Single unified endpoint that replaces the 2-step flow:
    - Finds existing interview (any status) 
    - Creates new if none exists
    - Applies business rules (active/completed/terminated)
    - Returns appropriate state for frontend
    """
    try:
        # Extract user info from JWT token - authentication required
        user_info = require_user_from_request(request)
        user_email = user_info["email"]
        
        logger.info(f"Getting interview state for user: {user_email}, job: {jobId}")
        
        # Call interview agent via MCP Mesh to get/create interview state
        interview_result = await interview_state_getter(
            job_id=jobId,
            user_email=user_email
        )
        
        if not interview_result or not interview_result.get("success"):
            error_msg = interview_result.get("error", "Failed to get interview state") if interview_result else "No response from interview agent"
            logger.error(f"Interview state request failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Handle different interview states
        status = interview_result.get("status")
        logger.info(f"Interview state retrieved: status={status}, session_id={interview_result.get('session_id')}")
        
        if status in ["INPROGRESS", "active"]:  # Support both new and legacy status
            # Return active interview data
            return {
                "success": True,
                "status": status,  # Return the actual status from the interview agent
                "session_id": interview_result.get("session_id"),
                "current_question": interview_result.get("current_question"),
                "question_metadata": interview_result.get("question_metadata", {}),
                "conversation_history": interview_result.get("conversation_history", []),
                "session_info": interview_result.get("session_info", {})
            }
            
        elif status in ["COMPLETED", "completed", "terminated"]:
            # Return completion state
            return {
                "success": True,
                "status": status,
                "session_id": interview_result.get("session_id"),
                "completion_reason": interview_result.get("completion_reason"),
                "completed_at": interview_result.get("completed_at") or interview_result.get("terminated_at"),
                "message": interview_result.get("message", f"Interview {status}")
            }
            
        else:
            # Unknown status
            logger.error(f"Unknown interview status: {status}")
            raise HTTPException(status_code=500, detail=f"Unknown interview status: {status}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get interview state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get interview state: {str(e)}")


@router.get("/status")
@mesh.route(dependencies=["get_interview_session"])
async def get_interview_status(
    request: Request,
    session_checker: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Get current interview session status for the authenticated user.
    
    Checks for active interview sessions and returns current status.
    """
    try:
        # Extract user info from JWT token - authentication required  
        user_info = require_user_from_request(request)
        user_email = user_info["email"]
        
        logger.info(f"Interview status requested by user: {user_email}")
        
        # TODO: We need a way to find sessions by user_email
        # For now, return no active session - this needs user session lookup
        # This would require either:
        # 1. A separate user session tracking system, or
        # 2. A database query to find active sessions by user_email
        
        return {
            "has_active_session": False,
            "status": "no_session",
            "message": "No active interview session found"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get interview status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get interview status: {str(e)}")


@router.get("/{session_id}/current")
@mesh.route(dependencies=["get_interview_session"])
async def get_current_interview_question(
    request: Request,
    session_id: str,
    session_getter: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Get the current question for a specific interview session.
    
    Returns session details with current question and conversation history.
    """
    try:
        # Extract user info from JWT token - authentication required
        user_info = require_user_from_request(request)
        user_email = user_info["email"]
        
        logger.info(f"Current question requested by user: {user_email} for session: {session_id}")
        
        # Get session data from interview agent
        session_result = await session_getter(session_id=session_id)
        
        if not session_result or not session_result.get("success"):
            error_msg = session_result.get("error", "Session not found") if session_result else "No response from interview agent"
            logger.error(f"Failed to get session data: {error_msg}")
            
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail="Interview session not found")
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        # Get data from new MCP response format
        status = session_result.get("status")
        conversation_history = session_result.get("conversation_history", [])
        session_info = session_result.get("session_info", {})
        
        # Check if session is still active
        if status not in ["INPROGRESS", "active"]:  # Support both new and legacy status
            raise HTTPException(status_code=410, detail=f"Interview session is {status or 'inactive'}")
        
        logger.info(f"Current question retrieved for session: {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "status": status,
            "conversation_history": conversation_history,
            "session_info": session_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current interview question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get current interview question: {str(e)}")


async def generate_interview_response(
    job_id: str, 
    user_answer: str, 
    user_email: str,
    interview_conductor: McpMeshAgent
):
    """Generate streaming response for interview answer via SSE."""
    try:
        # Send processing message
        yield f"data: {json.dumps({'type': 'processing', 'message': 'Analyzing your answer...', 'timestamp': datetime.now().isoformat()})}\n\n"
        
        logger.info(f"Processing answer for job {job_id}: {user_answer[:50]}...")
        
        # Call interview conductor to continue interview with job_id and user_email
        interview_result = await interview_conductor(
            job_id=job_id,
            user_email=user_email,
            user_input=user_answer,
            user_action="answer"
        )
        
        if not interview_result or not interview_result.get("success"):
            error_msg = interview_result.get('error', 'Failed to process answer') if interview_result else 'No response from interview agent'
            logger.error(f"Interview processing failed: {error_msg}")
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            return
        
        # Send evaluation feedback
        yield f"data: {json.dumps({'type': 'evaluation', 'message': 'Answer processed successfully', 'timestamp': datetime.now().isoformat()})}\n\n"
        
        # Check if interview completed or has next question
        status = interview_result.get("status")
        phase = interview_result.get("phase")
        
        if status in ["COMPLETED", "terminated"] or phase == "completion":
            # Interview completed/terminated
            evaluation = interview_result.get("evaluation", {})
            session_summary = interview_result.get("session_summary", {})
            
            completion_data = {
                'type': 'interview_complete',
                'message': 'Interview completed',
                'job_id': job_id,
                'session_id': interview_result.get("session_id"),
                'status': status,
                'evaluation': evaluation,
                'session_summary': session_summary,
                'completion_reason': session_summary.get('completion_reason', 'completed'),
                'timestamp': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        elif interview_result.get("question_text"):
            # Next question available
            metadata = interview_result.get("metadata", {})
            
            question_data = {
                'type': 'question',
                'content': interview_result.get('question_text'),
                'metadata': interview_result.get('question_metadata', {}),
                'session_info': {
                    'job_id': job_id,
                    'session_id': interview_result.get("session_id"),
                    'questions_asked': metadata.get('total_questions', 0),
                    'questions_answered': metadata.get('questions_answered', 0),
                    'time_remaining_seconds': metadata.get('time_remaining_seconds', 0),
                    'conversation_length': metadata.get('conversation_length', 0)
                },
                'timestamp': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(question_data)}\n\n"
            
        else:
            # Unexpected state
            logger.warning(f"Unexpected interview state: status={status}, phase={phase}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Unexpected interview state'})}\n\n"
        
        # Send completion marker
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in interview response generation: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': f'Server error: {str(e)}'})}\n\n"


@router.post("/answer")
@mesh.route(dependencies=["conduct_interview"])
async def submit_interview_answer(
    request: Request,
    request_data: InterviewAnswerRequest,
    interview_conductor: McpMeshAgent = None
) -> StreamingResponse:
    """
    Submit answer and get next question via Server-Sent Events stream.
    
    Processes user answer and returns streaming response with next question or completion.
    """
    try:
        # Extract user info from JWT token - authentication required
        user_info = require_user_from_request(request)
        user_email = user_info["email"]
        
        logger.info(f"Received answer from user: {user_email} for job: {request_data.job_id}")
        
        # Validate answer
        if not request_data.answer.strip():
            raise HTTPException(status_code=400, detail="Answer cannot be empty")
        
        # Return streaming response with interview processing
        return StreamingResponse(
            generate_interview_response(request_data.job_id, request_data.answer, user_email, interview_conductor),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable NGINX buffering
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit interview answer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit interview answer: {str(e)}")


@router.post("/end")
@mesh.route(dependencies=["end_interview_session"])
async def end_interview(
    request: Request,
    request_data: InterviewEndRequest,
    session_ender: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Manually end an interview session.
    
    Updates interview and application status, triggers evaluation process.
    """
    try:
        # Extract user info from JWT token - authentication required
        user_info = require_user_from_request(request)
        user_email = user_info["email"]
        
        logger.info(f"Ending interview for user: {user_email}, job: {request_data.job_id}")
        
        # End session using interview agent via MCP Mesh
        end_result = await session_ender(
            job_id=request_data.job_id,
            user_email=user_email,
            reason=request_data.reason or "user_requested"
        )
        
        if not end_result or not end_result.get("success"):
            error_msg = end_result.get('error', 'Unknown error') if end_result else 'No response from interview agent'
            logger.error(f"Failed to end interview: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Failed to end interview: {error_msg}")
        
        logger.info(f"Interview ended successfully for job: {request_data.job_id}")
        
        return {
            "success": True,
            "message": end_result.get("message", "Interview ended successfully"),
            "job_id": request_data.job_id,
            "session_id": end_result.get("session_id"),
            "status": end_result.get("status", "completed"),
            "application_status": end_result.get("application_status"),
            "session_stats": end_result.get("session_stats", {}),
            "ended_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to end interview: {str(e)}")


@router.post("/{session_id}/finalize")
@mesh.route(dependencies=["finalize_interview"])
async def finalize_interview_scoring(
    request: Request,
    session_id: str,
    interview_finalizer: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Manually trigger interview finalization and scoring.
    
    Generates comprehensive evaluation using LLM analysis.
    """
    try:
        # Extract user info from JWT token - authentication required
        user_info = require_user_from_request(request)
        user_email = user_info["email"]
        
        logger.info(f"Finalizing interview scoring for user: {user_email}, session: {session_id}")
        
        # Finalize interview using interview agent via MCP Mesh (now processes all unscored interviews)
        finalize_result = await interview_finalizer()
        
        if not finalize_result or not finalize_result.get("success"):
            error_msg = finalize_result.get('error', 'Unknown error') if finalize_result else 'No response from interview agent'
            logger.error(f"Failed to finalize interview: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Failed to finalize interview: {error_msg}")
        
        logger.info(f"Interview finalized successfully: {session_id}")
        
        return {
            "success": True,
            "message": "Interview finalization completed",
            "session_id": session_id,
            "evaluation": finalize_result.get("evaluation", {}),
            "finalized_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to finalize interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to finalize interview: {str(e)}")


@router.post("/finalize/batch")
@mesh.route(dependencies=["finalize_interview"])
async def finalize_pending_interviews_batch(
    interview_finalizer: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Internal endpoint to finalize all pending interviews via interview agent.
    
    Called by the monitoring service every 30 seconds to process completed interviews
    that haven't been evaluated yet. Uses Redis lock in interview agent to prevent
    concurrent processing across multiple backend instances.
    
    No authentication required as this is an internal monitoring endpoint.
    """
    try:
        logger.info("Starting batch finalization of pending interviews via interview agent")
        
        # Call interview agent's finalize_interview function via MCP Mesh
        # The interview agent handles Redis locking, database queries, and LLM evaluation
        result = await interview_finalizer()
        
        if not result:
            logger.error("No response from interview agent")
            return {
                "success": False,
                "error": "No response from interview agent",
                "finalized_count": 0,
                "total_processed": 0
            }
        
        success = result.get("success", False)
        processed_count = result.get("processed_count", 0)
        total_found = result.get("total_found", 0)
        lock_status = result.get("lock_status", "unknown")
        message = result.get("message", "No message")
        
        if success:
            if processed_count > 0:
                logger.info(f"Batch finalization successful: {processed_count}/{total_found} interviews processed")
            elif lock_status == "held_by_another_instance":
                logger.debug("Batch finalization skipped - another instance processing")
            else:
                logger.debug(f"No interviews needed finalization: {message}")
        else:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Batch finalization failed: {error_msg}")
        
        return {
            "success": success,
            "message": message,
            "finalized_count": processed_count,
            "total_processed": total_found,
            "lock_status": lock_status,
            "results": result.get("results", [])
        }
        
    except Exception as e:
        logger.error(f"Error in batch finalization endpoint: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "finalized_count": 0,
            "total_processed": 0
        }