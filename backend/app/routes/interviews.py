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
from fastapi import APIRouter, HTTPException, Request
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
    session_id: Optional[str] = None


class InterviewEndRequest(BaseModel):
    """Request model for ending interview"""
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
        if status != "active":
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
    session_id: str, 
    user_answer: str, 
    user_email: str,
    interview_conductor: McpMeshAgent
):
    """Generate streaming response for interview answer via SSE."""
    try:
        # Send processing message
        yield f"data: {json.dumps({'type': 'processing', 'message': 'Analyzing your answer...', 'timestamp': datetime.now().isoformat()})}\n\n"
        
        logger.info(f"Processing answer for session {session_id}: {user_answer[:50]}...")
        
        # Call interview conductor to continue interview with user input
        interview_result = await interview_conductor(
            session_id=session_id,
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
        
        if status == "terminated" or phase == "completion":
            # Interview completed/terminated
            evaluation = interview_result.get("evaluation", {})
            session_summary = interview_result.get("session_summary", {})
            
            completion_data = {
                'type': 'interview_complete',
                'message': 'Interview completed',
                'session_id': session_id,
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
                    'session_id': session_id,
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


@router.post("/{session_id}/answer")
@mesh.route(dependencies=["conduct_interview"])
async def submit_interview_answer(
    request: Request,
    session_id: str,
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
        
        logger.info(f"Received answer from user: {user_email} for session: {session_id}")
        
        # Validate answer
        if not request_data.answer.strip():
            raise HTTPException(status_code=400, detail="Answer cannot be empty")
        
        # Return streaming response with interview processing
        return StreamingResponse(
            generate_interview_response(session_id, request_data.answer, user_email, interview_conductor),
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


@router.post("/{session_id}/end")
@mesh.route(dependencies=["end_interview_session"])
async def end_interview(
    request: Request,
    session_id: str,
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
        
        logger.info(f"Ending interview for user: {user_email}, session: {session_id}")
        
        # End session using interview agent via MCP Mesh
        end_result = await session_ender(
            session_id=session_id,
            reason=request_data.reason or "user_requested"
        )
        
        if not end_result or not end_result.get("success"):
            error_msg = end_result.get('error', 'Unknown error') if end_result else 'No response from interview agent'
            logger.error(f"Failed to end interview: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Failed to end interview: {error_msg}")
        
        logger.info(f"Interview ended successfully: {session_id}")
        
        return {
            "success": True,
            "message": end_result.get("message", "Interview ended successfully"),
            "session_id": session_id,
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
        
        # Finalize interview using interview agent via MCP Mesh
        finalize_result = await interview_finalizer(session_id=session_id)
        
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