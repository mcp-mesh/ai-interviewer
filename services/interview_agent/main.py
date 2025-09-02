#!/usr/bin/env python3
"""
Interview Agent - Main Implementation

AI-powered technical interviewer that conducts dynamic interviews based on 
role requirements and candidate profiles with PostgreSQL database storage
and Redis caching for optimal performance.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

# Configuration: Time threshold for interview closing
# When remaining time is less than this percentage of total duration,
# return a standard closing message instead of generating new questions
TIME_THRESHOLD_PERCENTAGE = 10  # 10% of total interview duration

# Configuration: Behavioral violation thresholds
# Auto-terminate interview if total violations exceed this threshold
VIOLATION_THRESHOLD = 3  # Maximum allowed violations before termination

import mesh
import redis
from fastmcp import FastMCP

# Redis client for lock management
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"), decode_responses=True)

# Redis lock constants for interview finalization
FINALIZE_LOCK_KEY = "interview_finalization_lock"
FINALIZE_LOCK_TTL = 300  # 5 minutes

async def acquire_finalization_lock() -> bool:
    """Acquire Redis lock for interview finalization to prevent concurrent processing."""
    try:
        # Use SET with NX (not exists) and EX (expiry) for atomic lock acquisition
        result = redis_client.set(
            FINALIZE_LOCK_KEY,
            f"locked_{datetime.now(timezone.utc).isoformat()}",
            nx=True,  # Only set if key doesn't exist
            ex=FINALIZE_LOCK_TTL  # Auto-expire in 5 minutes
        )
        if result:
            logger.info("Successfully acquired interview finalization lock")
            return True
        else:
            logger.info("Interview finalization lock is already held by another instance")
            return False
    except Exception as e:
        logger.error(f"Failed to acquire finalization lock: {e}")
        return False

async def release_finalization_lock() -> bool:
    """Release Redis lock for interview finalization."""
    try:
        result = redis_client.delete(FINALIZE_LOCK_KEY)
        if result:
            logger.info("Successfully released interview finalization lock")
            return True
        else:
            logger.warning("Finalization lock was not present when trying to release")
            return False
    except Exception as e:
        logger.error(f"Failed to release finalization lock: {e}")
        return False

# Import specific agent types for type hints
from mesh.types import McpAgent, McpMeshAgent

# Import database models and functions from the new organized structure
from .database import (
    # Models
    Interview, InterviewQuestion, InterviewResponse, InterviewEvaluation,
    # Database operations
    create_tables, get_db_session, test_connections,
    get_interview_by_session_id, create_interview_session,
    add_interview_question, add_interview_response,
    get_interview_conversation_pairs, format_conversation_for_llm,
    # Caching
    InterviewCache
)

# Import new modular components
from .core.interview_conductor import interview_conductor

# Create FastMCP app instance
app = FastMCP("Interview Agent Service")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database at module level - executed when MCP Mesh loads this module
logger.info("🚀 Initializing Interview Agent v1.0 (PostgreSQL + Redis)")

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

logger.info("✅ Interview Agent ready to serve requests")

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
        decode_responses=True,
        socket_timeout=5
    )
    # Test connection
    redis_client.ping()
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

# Session management
SESSION_PREFIX = "interview_session:"
DEFAULT_INTERVIEW_DURATION = 120  # 2 minutes for testing (will be role-configurable later)


def get_session_key(session_id: str) -> str:
    """Generate Redis key for session."""
    return f"{SESSION_PREFIX}{session_id}"


# Timer and locking logic moved to backend for centralized orchestration


def store_session_data(session_id: str, data: Dict[str, Any]) -> bool:
    """Store session data in Redis permanently (no TTL)."""
    if not redis_client:
        logger.error("Redis client not available")
        return False
    
    try:
        key = get_session_key(session_id)
        redis_client.set(key, json.dumps(data))  # No TTL - permanent storage
        logger.info(f"Stored session data for {session_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to store session data: {e}")
        return False


def get_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve session data from Redis."""
    if not redis_client:
        logger.error("Redis client not available")
        return None
    
    try:
        key = get_session_key(session_id)
        data = redis_client.get(key)
        if data:
            logger.info(f"Retrieved session data for {session_id}")
            return json.loads(data)
        else:
            logger.warning(f"No session data found for {session_id}")
            return None
    except Exception as e:
        logger.error(f"Failed to retrieve session data: {e}")
        return None


def create_session(resume_content: str, role_description: str, duration_minutes: int = None) -> str:
    """Create new interview session with proper timing fields."""
    session_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    session_data = {
        "session_id": session_id,
        "role_description": role_description,
        "resume_content": resume_content,
        "conversation": [],
        "start_time": start_time.isoformat(),
        "duration": (duration_minutes * 60) if duration_minutes else DEFAULT_INTERVIEW_DURATION,  # Interview duration in seconds
        "created_at": start_time.isoformat(),
        "last_updated": start_time.isoformat(),
        "status": "active"
    }
    
    if store_session_data(session_id, session_data):
        logger.info(f"Created new interview session: {session_id} (duration: {session_data['duration']}s)")
        return session_id
    else:
        raise RuntimeError("Failed to create interview session")


def add_to_conversation(session_id: str, message_type: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Add message to conversation history."""
    session_data = get_session_data(session_id)
    if not session_data:
        return False
    
    message = {
        "type": message_type,  # "question" or "answer"
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if metadata:
        message["metadata"] = metadata
    
    session_data["conversation"].append(message)
    session_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    return store_session_data(session_id, session_data)


def format_conversation_for_llm(conversation: List[Dict]) -> List[Dict[str, str]]:
    """Format conversation history for LLM messages array."""
    messages = []
    
    for msg in conversation:
        if msg["type"] == "question":
            messages.append({"role": "assistant", "content": msg["content"]})
        elif msg["type"] == "answer":
            messages.append({"role": "user", "content": msg["content"]})
    
    return messages


def check_session_expiration(session_data: Dict[str, Any]) -> bool:
    """Check if session has expired."""
    if not session_data:
        return True
    
    current_time = datetime.now(timezone.utc).timestamp()
    expires_at = session_data.get("expires_at", 0)
    return current_time >= expires_at


def end_session(session_id: str, reason: str = "completed") -> bool:
    """End an interview session."""
    session_data = get_session_data(session_id)
    if not session_data:
        return False
    
    session_data["status"] = "ended"
    session_data["user_action"] = reason
    session_data["ended_at"] = datetime.now(timezone.utc).isoformat()
    session_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    return store_session_data(session_id, session_data)


async def evaluate_interview_performance(
    conversation: List[Dict], 
    role_description: str, 
    resume_content: str,
    llm_service: McpAgent
) -> Dict[str, Any]:
    """Evaluate interview performance using LLM service via MCP Mesh."""
    try:
        if not llm_service:
            logger.error("LLM service not available for evaluation")
            return {"score": 0, "feedback": "LLM service unavailable", "error": "No LLM service"}
        
        # Format conversation as transcript for system prompt (avoids pattern confusion)
        def format_conversation_as_transcript(conversation: List[Dict]) -> str:
            transcript = []
            for msg in conversation:
                if msg["type"] == "question":
                    transcript.append(f"Interviewer: {msg['content']}")
                elif msg["type"] == "answer":
                    transcript.append(f"Candidate: {msg['content']}")
            return "\n\n".join(transcript)
        
        conversation_transcript = format_conversation_as_transcript(conversation)
        
        # Calculate interview statistics for evaluation context
        questions_asked = len([msg for msg in conversation if msg["type"] == "question"])
        answers_given = len([msg for msg in conversation if msg["type"] == "answer"])
        
        # Create evaluation system prompt with embedded transcript (avoids pattern confusion)
        evaluation_system_prompt = f"""You are an interview evaluator reviewing a completed technical interview.

ROLE DESCRIPTION:
{role_description}

CANDIDATE RESUME:
{resume_content}

INTERVIEW STATISTICS:
- Questions Asked: {questions_asked}
- Answers Given: {answers_given}
- Interview Completion: {answers_given}/{questions_asked} questions answered

=== COMPLETED INTERVIEW TRANSCRIPT ===
{conversation_transcript}
=== END TRANSCRIPT ===

Evaluate the candidate based on their responses in the transcript above. Use the evaluation tool to provide comprehensive scores and feedback.

CRITICAL EVALUATION GUIDELINES:

1. **Interview Completion Assessment**:
   - Candidates who answer fewer than 3 questions should receive LOW scores (≤50) regardless of answer quality
   - Incomplete interviews (≤50% questions answered) indicate lack of commitment or serious interview issues
   - Consider completion rate as a PRIMARY factor in overall scoring

2. **Scoring Guidelines**:
   - Overall score (0-100): Holistic assessment considering BOTH completion and performance
   - Technical knowledge (0-25): Domain expertise, technical concepts, depth of understanding
   - Problem solving (0-25): Analytical thinking, approach to complex problems, solution quality  
   - Communication (0-25): Clarity, articulation, ability to explain technical concepts
   - Experience relevance (0-25): How well experience aligns with role requirements

3. **Hire Recommendation Logic**:
   - NEVER recommend "yes" or "strong_yes" for candidates who answered <3 questions
   - "strong_no": <2 questions answered OR extremely poor performance
   - "no": 2-3 questions with poor answers OR incomplete interview
   - "maybe": 3-4 questions with mixed performance
   - "yes": 4+ questions with good performance
   - "strong_yes": 5+ questions with excellent performance

4. **Feedback Structure**:
   **Strengths:**
   - List 2-3 positive aspects from their responses
   - Highlight relevant experience or technical knowledge shown

   **Areas for Improvement:**  
   - List 2-3 specific areas needing development
   - Include interview completion concerns if applicable
   - Suggest specific skills or knowledge gaps to address

Be thorough, fair, and realistic in your evaluation. Prioritize interview completion and engagement as fundamental requirements."""

        # Empty messages array to avoid pattern confusion
        conversation_messages = []
        
        # Define comprehensive evaluation tool schema
        evaluation_tool = {
            "name": "evaluate_interview_performance",
            "description": "Provide comprehensive evaluation of candidate performance",
            "input_schema": {
                "type": "object",
                "properties": {
                    "overall_score": {
                        "type": "integer",
                        "description": "Overall interview score from 0-100"
                    },
                    "technical_knowledge": {
                        "type": "integer", 
                        "description": "Technical knowledge and expertise score (0-25)"
                    },
                    "problem_solving": {
                        "type": "integer",
                        "description": "Problem-solving and analytical thinking score (0-25)"
                    },
                    "communication": {
                        "type": "integer",
                        "description": "Communication clarity and articulation score (0-25)"
                    },
                    "experience_relevance": {
                        "type": "integer",
                        "description": "Relevance of experience to role requirements score (0-25)"
                    },
                    "hire_recommendation": {
                        "type": "string",
                        "enum": ["strong_yes", "yes", "maybe", "no", "strong_no"],
                        "description": "Hiring recommendation based on overall performance"
                    },
                    "feedback": {
                        "type": "string",
                        "description": "Detailed feedback on candidate's performance, strengths, and areas for improvement"
                    }
                },
                "required": ["overall_score", "technical_knowledge", "problem_solving", "communication", "experience_relevance", "hire_recommendation", "feedback"]
            }
        }
        
        # Prepare tools for LLM service (handles conversion internally)
        tools_to_use = [evaluation_tool]
        
        # Call LLM service for evaluation
        logger.info(f"Evaluating interview performance with LLM - {questions_asked} questions, {answers_given} answers")
        
        try:
            llm_response = await llm_service(
                text="Score this candidate now using the tool.",
                system_prompt=evaluation_system_prompt,
                messages=conversation_messages,
                tools=tools_to_use,
                force_tool_use=True,
                temperature=0.1
            )
            logger.info("LLM evaluation completed successfully")
        except Exception as llm_call_error:
            logger.error(f"LLM service call failed: {llm_call_error}")
            return {"score": 0, "feedback": "LLM service call failed", "error": str(llm_call_error)}
        
        # Validate LLM response structure
        if not llm_response.get("success") or not llm_response.get("tool_calls"):
            error_msg = llm_response.get('error', 'No tool calls returned')
            logger.error(f"LLM evaluation failed: {error_msg}")
            return {"score": 0, "feedback": "Evaluation failed", "error": error_msg}
        
        # Extract evaluation from tool calls
        tool_calls = llm_response.get("tool_calls", [])
        if len(tool_calls) == 0:
            logger.error("No tool calls found in LLM response")
            return {"score": 0, "feedback": "No evaluation data", "error": "No tool calls in response"}
        
        # Get evaluation parameters from first tool call
        try:
            evaluation_result = tool_calls[0]["parameters"]
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract evaluation parameters: {e}")
            return {"score": 0, "feedback": "Tool call format error", "error": f"Parameter extraction failed: {e}"}
        
        # Format the comprehensive result
        formatted_result = {
            "score": evaluation_result.get("overall_score", 0),
            "technical_knowledge": evaluation_result.get("technical_knowledge", 0),
            "problem_solving": evaluation_result.get("problem_solving", 0),
            "communication": evaluation_result.get("communication", 0),
            "experience_relevance": evaluation_result.get("experience_relevance", 0),
            "hire_recommendation": evaluation_result.get("hire_recommendation", "no"),
            "feedback": evaluation_result.get("feedback", ""),
            "evaluation_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Interview evaluation completed - Score: {formatted_result['score']}/100, Recommendation: {formatted_result['hire_recommendation']}")
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error evaluating interview performance: {e}")
        return {"score": 0, "feedback": "Evaluation error", "error": str(e)}


# Timer monitoring moved to backend - interview agent only handles finalization when called


@app.tool()
@mesh.tool(
    capability="conduct_interview",
    version="2.0",
    dependencies=[
        {
            "capability": "process_with_tools",
            "tags": ["+openai"],  # LLM service - need tag to choose between openai/claude
        },
        {
            "capability": "user_applications_get"  # Application agent - only one provider, no tags needed
        },
        {
            "capability": "job_details_get"  # Job agent - only one provider, no tags needed
        },
        {
            "capability": "application_status_update"  # Application agent - only one provider, no tags needed
        }
    ],
    tags=["interview", "technical-screening", "ai-interviewer", "session-management"],
    timeout=120,
    retry_count=2
)
async def conduct_interview(
    session_id: Optional[str] = None,
    job_id: Optional[str] = None,
    user_email: Optional[str] = None,
    application_id: Optional[str] = None,
    user_input: Optional[str] = None,
    user_action: Optional[str] = None,
    # Legacy parameters for backward compatibility
    resume_content: Optional[str] = None,
    role_description: Optional[str] = None,
    user_session_id: Optional[str] = None,
    candidate_answer: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    # MCP Mesh dependencies (injected automatically)
    process_with_tools: McpMeshAgent = None,
    user_applications_get: McpMeshAgent = None,
    job_details_get: McpMeshAgent = None,
    application_status_update: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Conduct a technical interview session with modular PostgreSQL-based architecture.
    
    This function handles both starting new interviews and continuing existing ones:
    
    NEW INTERVIEW (Start):
    - Requires: job_id, user_email, application_id
    - Creates new session, gets job/application data, generates first question
    
    CONTINUE INTERVIEW (Resume):
    - Requires: session_id, user_input (optional), user_action (optional)
    - Processes response, generates next question or completes interview
    
    LEGACY SUPPORT:
    - Still supports old parameters (resume_content, role_description, user_session_id)
    - Automatically converts to new format for backward compatibility
    
    Args:
        session_id: Existing session ID (for continue operations)
        job_id: Job posting identifier (for new interview)
        user_email: User's email address (for new interview)
        application_id: Application identifier (for new interview)
        user_input: User's response to current question
        user_action: User action (answer, skip, end)
        
        # Legacy parameters (backward compatibility)
        resume_content: Candidate's resume (legacy)
        role_description: Job description (legacy)  
        user_session_id: Session ID (legacy)
        candidate_answer: User answer (legacy)
        duration_minutes: Interview duration (legacy)
        
        # MCP Mesh dependencies (auto-injected)
        process_with_tools: LLM service for questions and evaluation
        user_applications_get: Application agent for application data
        job_details_get: Job agent for job details
        application_status_update: Application agent for status updates
    
    Returns:
        Dictionary containing interview response with question/completion data
    """
    try:
        logger.info("🚀 Starting modular interview conductor v2.0")
        
        # Handle legacy parameter conversion for backward compatibility
        if user_session_id and not session_id:
            session_id = user_session_id
            logger.info(f"Legacy parameter conversion: user_session_id -> session_id: {session_id}")
        
        if candidate_answer and not user_input:
            user_input = candidate_answer
            logger.info("Legacy parameter conversion: candidate_answer -> user_input")
        
        # Prepare MCP Mesh dependencies dictionary
        dependencies = {
            "process_with_tools": process_with_tools,
            "user_applications_get": user_applications_get,
            "job_details_get": job_details_get,
            "application_status_update": application_status_update
        }
        
        # Validate critical dependencies
        if not process_with_tools:
            raise Exception("LLM service (process_with_tools) not available")
        
        logger.info(f"Dependencies available: {list(dependencies.keys())}")
        
        # Use the modular interview conductor
        result = await interview_conductor.conduct_interview(
            session_id=session_id,
            job_id=job_id,
            user_email=user_email,
            application_id=application_id,
            user_input=user_input,
            user_action=user_action,
            dependencies=dependencies
        )
        
        # Convert result to legacy format if needed for backward compatibility
        if isinstance(result, dict):
            # Ensure we have a success field for legacy compatibility
            if "success" not in result:
                result["success"] = result.get("status") in ["INPROGRESS", "COMPLETED"]
            
            # Legacy response format compatibility
            if "question" in result and isinstance(result["question"], dict):
                result["question_text"] = result["question"].get("text", result["question"].get("question", ""))
                result["question_metadata"] = {
                    "type": result["question"].get("type", "technical"),
                    "focus_area": result["question"].get("focus_area", "general"),
                    "difficulty": result["question"].get("difficulty", "medium"),
                    "question_number": result["question"].get("number", 1)
                }
            
            logger.info(f"Interview operation completed successfully for session {result.get('session_id')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Modular interview operation failed: {e}")
        
        # Legacy error format for backward compatibility
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id or user_session_id or "unknown",
            "version": "2.0_modular"
        }


@app.tool()
@mesh.tool(capability="get_session_status")  
def get_session_status(session_id: str) -> Dict[str, Any]:
    """Get current session status and metadata."""
    try:
        session_data = get_session_data(session_id)
        if not session_data:
            return {
                "success": False,
                "error": "Session not found",
                "session_id": session_id
            }
        
        # Check expiration
        if check_session_expiration(session_data):
            end_session(session_id, "timeout")
            session_data = get_session_data(session_id)  # Get updated data
        
        # Calculate remaining time
        current_time = datetime.now(timezone.utc).timestamp()
        remaining_seconds = max(0, int(session_data.get("expires_at", 0) - current_time))
        
        return {
            "success": True,
            "session_id": session_id,
            "status": session_data.get("status", "unknown"),
            "user_action": session_data.get("user_action", "none"),
            "started_at": session_data.get("started_at"),
            "ended_at": session_data.get("ended_at"),
            "duration_minutes": session_data.get("duration_minutes"),
            "expires_at": session_data.get("expires_at"),
            "time_remaining_seconds": remaining_seconds,
            "questions_asked": session_data.get("questions_asked", 0),
            "current_question": session_data.get("current_question"),
            "question_metadata": session_data.get("question_metadata", {}),
            "total_score": session_data.get("total_score", 0),
            "conversation_history": session_data.get("conversation", []),
            "last_updated": session_data.get("last_updated")
        }
        
    except Exception as e:
        logger.error(f"Failed to get session status for {session_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id
        }


@app.tool()
@mesh.tool(
    capability="end_interview_session",
    dependencies=[
        {
            "capability": "application_status_update"  # Application agent for status updates
        }
    ]
)
async def end_interview_session(
    session_id: str, 
    reason: str = "ended_manually",
    application_status_update: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    End an interview session with proper database updates and application status changes.
    
    Args:
        session_id: Session identifier to end
        reason: Reason for ending (ended_manually, user_requested, etc.)
        application_status_update: Application agent for status updates (auto-injected)
    
    Returns:
        Dictionary with success status and session details
    """
    try:
        from .services.storage_service import storage_service
        
        # Get interview session from PostgreSQL
        interview = await storage_service.get_interview_by_session_id(session_id)
        if not interview:
            return {
                "success": False,
                "error": "Interview session not found",
                "session_id": session_id
            }
        
        # Check if already completed
        if interview.status == "COMPLETED":
            return {
                "success": False,
                "error": f"Interview session already {interview.status}",
                "session_id": session_id,
                "current_status": interview.status
            }
        
        # Update interview status in PostgreSQL
        status_mapping = {
            "ended_manually": "COMPLETED",
            "user_requested": "COMPLETED", 
            "time_expired": "COMPLETED",
            "abandoned": "COMPLETED",
            "security_violation": "COMPLETED"
        }
        new_status = status_mapping.get(reason, "COMPLETED")
        
        success = await storage_service.update_interview_status(
            session_id=session_id,
            status=new_status,
            metadata_updates={
                "ended_at": datetime.now(timezone.utc).isoformat(),
                "end_reason": reason
            }
        )
        
        if not success:
            return {
                "success": False,
                "error": "Failed to update interview status in database",
                "session_id": session_id
            }
        
        # Update application status in application agent
        application_status = "COMPLETED"  # Default status for all manual ends
        if reason == "abandoned":
            application_status = "DECISION_PENDING"  # For abandoned interviews
        
        try:
            # Use job_id and user_email to update application status
            if application_status_update:
                status_result = await application_status_update(
                    job_id=interview.job_id,
                    user_email=interview.user_email,
                    new_status=application_status
                )
                if status_result.get("success"):
                    logger.info(f"Updated application status to {application_status}: {status_result}")
                else:
                    logger.warning(f"Failed to update application status: {status_result}")
            else:
                logger.warning("application_status_update agent not available")
                
        except Exception as e:
            logger.warning(f"Failed to update application status: {e}")
            # Don't fail the interview end for application status update failure
        
        # Get session statistics for response
        stats = await storage_service.get_session_statistics(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "message": f"Interview session ended: {reason}",
            "status": new_status,
            "application_status": application_status,
            "session_stats": {
                "questions_asked": stats.get("question_count", 0),
                "responses_given": stats.get("response_count", 0),
                "duration_minutes": stats.get("duration_minutes", 0),
                "ended_reason": reason
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to end session {session_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id
        }


@app.tool()
@mesh.tool(capability="get_interview_session")
def get_interview_session(session_id: str) -> Dict[str, Any]:
    """
    Get interview session data and conversation history.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Dictionary containing session data and conversation history
    """
    try:
        logger.info(f"Retrieving PostgreSQL session data: {session_id}")
        
        with get_db_session() as db:
            # Get interview from PostgreSQL database
            interview = get_interview_by_session_id(session_id, db)
            if not interview:
                return {
                    "success": False,
                    "error": "Session not found",
                    "session_id": session_id
                }
            
            # Get conversation history in the format expected by the frontend
            conversation_history = get_interview_conversation_pairs(interview.id, db)
            
            # Calculate session info
            questions_asked = len([pair for pair in conversation_history if pair.get("question")])
            questions_answered = len([pair for pair in conversation_history if pair.get("question") and pair.get("response")])
            time_remaining_seconds = interview.time_remaining_seconds
            
            return {
                "success": True,
                "status": interview.status,
                "conversation_history": conversation_history,
                "session_info": {
                    "questions_asked": questions_asked,
                    "questions_answered": questions_answered,
                    "time_remaining_seconds": time_remaining_seconds
                },
                "session_id": session_id
            }
        
    except Exception as e:
        logger.error(f"Failed to retrieve session {session_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id
        }



@app.tool()
@mesh.tool(
    capability="finalize_interview", 
    timeout=300,  # Increased timeout for batch processing
    dependencies=[
        {
            "capability": "process_with_tools",
            "tags": ["+openai"],
        }
    ]
)
async def finalize_interview(llm_service: McpAgent = None) -> Dict[str, Any]:
    """
    Finalize all interviews that need scoring with Redis lock for concurrent protection.
    
    Processes all interviews that are either:
    1. Status = COMPLETED and evaluation_completed = false
    2. Started time + duration < current time (expired interviews)
    
    Uses Redis lock to prevent concurrent processing across multiple backend instances.
    
    Args:
        llm_service: LLM service for evaluation
        
    Returns:
        Dictionary containing finalization results for all processed interviews
    """
    # Step 1: Try to acquire Redis lock for finalization
    lock_acquired = await acquire_finalization_lock()
    if not lock_acquired:
        return {
            "success": True,
            "message": "Finalization skipped - another instance is processing",
            "processed_count": 0,
            "total_found": 0,
            "results": [],
            "lock_status": "held_by_another_instance"
        }
    
    try:
        logger.info("Starting batch finalization of unscored interviews")
        
        # Check if LLM service is available
        if not llm_service:
            return {
                "success": False,
                "error": "LLM service not available for evaluation",
                "processed_count": 0
            }
        
        from .services.storage_service import storage_service
        current_time = datetime.now(timezone.utc)
        
        # Query interviews that need finalization
        from sqlalchemy import or_, text
        with get_db_session() as db:
            interviews_to_finalize = db.query(Interview).filter(
                Interview.evaluation_completed == False,
                or_(
                    Interview.status == "COMPLETED",
                    # Expired interviews: started_at + duration < current_time
                    text("started_at + (duration_minutes || ' minutes')::interval < :current_time")
                )
            ).params(current_time=current_time).all()
        
        if not interviews_to_finalize:
            logger.info("No interviews found that need finalization")
            return {
                "success": True,
                "message": "No interviews need finalization",
                "processed_count": 0,
                "results": []
            }
        
        logger.info(f"Found {len(interviews_to_finalize)} interviews to finalize")
        
        results = []
        successful_count = 0
        
        for interview in interviews_to_finalize:
            try:
                logger.info(f"Processing interview {interview.session_id}")
                
                # Update expired interviews to COMPLETED status
                if interview.status != "COMPLETED":
                    await storage_service.update_interview_status(
                        interview.session_id,
                        "COMPLETED",
                        {"completion_reason": "time_expired", "finalized_at": current_time.isoformat()}
                    )
                    logger.info(f"Updated expired interview {interview.session_id} to COMPLETED")
                
                # Get conversation history from database (within a new session to avoid lazy loading issues)
                with get_db_session() as db:
                    interview_with_relations = db.query(Interview).filter(
                        Interview.session_id == interview.session_id
                    ).first()
                    conversation_pairs = interview_with_relations.get_conversation_pairs() if interview_with_relations else []
                
                # Format conversation for evaluation (convert to old format expected by evaluate_interview_performance)
                conversation = []
                for pair in conversation_pairs:
                    # Add question
                    conversation.append({
                        "type": "question",
                        "content": pair["question"]["text"],
                        "timestamp": pair["question"].get("asked_at", "")
                    })
                    # Add response if exists
                    if pair.get("response"):
                        conversation.append({
                            "type": "answer", 
                            "content": pair["response"]["text"],
                            "timestamp": pair["response"].get("submitted_at", "")
                        })
                
                # Evaluate performance using existing LLM service
                evaluation = await evaluate_interview_performance(
                    conversation=conversation,
                    role_description=interview.role_description,
                    resume_content=interview.resume_content,
                    llm_service=llm_service
                )
                
                # Save evaluation to interview_evaluations table
                with get_db_session() as db:
                    interview_evaluation = InterviewEvaluation(
                        interview_id=interview.id,
                        overall_score=evaluation.get("score", 0),
                        technical_knowledge=evaluation.get("technical_knowledge", 0),
                        problem_solving=evaluation.get("problem_solving", 0),
                        communication=evaluation.get("communication", 0),
                        experience_relevance=evaluation.get("experience_relevance", 0),
                        hire_recommendation=evaluation.get("hire_recommendation", "no"),
                        feedback=evaluation.get("feedback", ""),
                        questions_answered=len([p for p in conversation_pairs if p.get("response")]),
                        completion_rate=len([p for p in conversation_pairs if p.get("response")]) / len(conversation_pairs) * 100 if conversation_pairs else 0,
                        ai_provider="openai",  # Based on dependency tag
                        ai_model="gpt-4",     # Default model
                        evaluation_context={"evaluation_timestamp": current_time.isoformat()}
                    )
                    
                    db.add(interview_evaluation)
                    
                    # Update interview with final score and evaluation_completed flag
                    interview_record = db.query(Interview).filter(Interview.id == interview.id).first()
                    if interview_record:
                        interview_record.final_score = evaluation.get("score", 0)
                        interview_record.evaluation_completed = True
                        interview_record.updated_at = current_time
                    
                    db.commit()
                
                successful_count += 1
                results.append({
                    "session_id": interview.session_id,
                    "success": True,
                    "score": evaluation.get("score", 0),
                    "hire_recommendation": evaluation.get("hire_recommendation", "no"),
                    "questions_answered": len([p for p in conversation_pairs if p.get("response")]),
                    "total_questions": len(conversation_pairs)
                })
                
                logger.info(f"Successfully finalized interview {interview.session_id} with score {evaluation.get('score', 0)}")
                
            except Exception as e:
                logger.error(f"Failed to finalize interview {interview.session_id}: {str(e)}")
                results.append({
                    "session_id": interview.session_id,
                    "success": False,
                    "error": str(e)
                })
        
        logger.info(f"Batch finalization completed: {successful_count}/{len(interviews_to_finalize)} successful")
        
        return {
            "success": True,
            "message": f"Finalized {successful_count} interviews",
            "processed_count": successful_count,
            "total_found": len(interviews_to_finalize),
            "results": results,
            "lock_status": "acquired_and_processed"
        }
                
    except Exception as e:
        logger.error(f"Error in batch finalization: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "processed_count": 0,
            "lock_status": "acquired_but_failed"
        }
    finally:
        # Step 3: Always release the Redis lock
        await release_finalization_lock()


@app.tool()
@mesh.tool(
    capability="get_current_interview_state",
    dependencies=[
        {"capability": "user_applications_get"},     # For getting user data
        {"capability": "job_details_get"},           # For getting job data  
        {"capability": "application_status_update"}, # For updating application status
        {"capability": "process_with_tools", "tags": ["+openai"]}  # For LLM service (interview creation)
    ]
)
async def get_current_interview_state(
    job_id: str, 
    user_email: str,
    user_applications_get: McpMeshAgent = None,
    job_details_get: McpMeshAgent = None,
    application_status_update: McpMeshAgent = None,
    process_with_tools: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Get or create interview state for user-job pair.
    
    Single unified endpoint to handle all interview state logic:
    - Find existing interview (any status)
    - Create new if none exists  
    - Apply business rules based on current state
    - Return appropriate state for frontend
    
    Args:
        job_id: Job posting identifier
        user_email: User's email address
        user_applications_get: MCP agent for getting user data
        job_details_get: MCP agent for getting job data
        
    Returns:
        Dictionary containing interview state and data
    """
    try:
        logger.info(f"Getting interview state for user={user_email}, job={job_id}")
        
        # Find existing interview (no status filter - gets ANY interview)
        from .services.storage_service import storage_service
        existing = await storage_service.get_interview_by_user_and_job(user_email, job_id)
        
        if not existing:
            logger.info("No existing interview found, creating new one")
            return await _create_new_interview(job_id, user_email, job_details_get, user_applications_get, application_status_update, process_with_tools)
        
        logger.info(f"Found existing interview: session_id={existing.session_id}, status={existing.status}")
        
        # Apply business rules based on existing interview status
        if existing.status == "INPROGRESS":
            if _is_expired(existing):
                logger.info("Interview expired, terminating")
                await storage_service.update_interview_status(
                    existing.session_id, 
                    "COMPLETED", 
                    {"completion_reason": "time_expired"}
                )
                return _format_completed_response(existing)
            else:
                logger.info("Resuming active interview")
                return await _format_active_response(existing)
        
        elif existing.status == "COMPLETED":
            logger.info(f"Interview already {existing.status}")
            return _format_completed_response(existing)
        
        elif existing.status == "error":
            logger.info("Interview had errors, creating new one")
            return await _create_new_interview(job_id, user_email, job_details_get, user_applications_get, application_status_update, process_with_tools)
        
        else:
            raise ValueError(f"Unknown interview status: {existing.status}")
            
    except Exception as e:
        logger.error(f"Error in get_current_interview_state: {e}")
        return {
            "success": False,
            "error": str(e),
            "status": "error"
        }


async def _create_new_interview(job_id: str, user_email: str, job_details_get: McpMeshAgent, user_applications_get: McpMeshAgent, application_status_update: McpMeshAgent, process_with_tools: McpMeshAgent) -> Dict[str, Any]:
    """Create new interview session and return first question."""
    try:
        # Get job data from job agent
        job_data_raw = await job_details_get(job_id=job_id)
        logger.info(f"Job data response: {job_data_raw}")
        
        # MCP mesh returns data in different formats, handle both
        if not job_data_raw:
            raise ValueError("Failed to get job data: No response")
        
        # Extract job data from MCP response
        if isinstance(job_data_raw, dict) and 'id' in job_data_raw:
            # Direct job data (when MCP mesh returns the job object directly)
            job_data = job_data_raw
        elif isinstance(job_data_raw, dict) and job_data_raw.get("success"):
            # Wrapped response format
            job_data = job_data_raw.get("job", {})
        else:
            # Log the actual response for debugging
            logger.error(f"Unexpected job data format: {job_data_raw}")
            raise ValueError(f"Failed to get job data: Unexpected response format")
        
        # Get user applications from user agent  
        user_apps_raw = await user_applications_get(user_email=user_email)
        if not user_apps_raw or not user_apps_raw.get("success"):
            logger.warning(f"Could not get user applications: {user_apps_raw.get('error') if user_apps_raw else 'No response'}")
            user_apps = {"applications": []}  # Provide default
        else:
            user_apps = user_apps_raw
        
        # Create interview session
        session_id = str(uuid.uuid4())
        from .services.storage_service import storage_service
        
        # Extract resume data from user applications
        applications = user_apps.get("applications", [])
        resume_data = {
            "skills": [],
            "experience": "No application data available"
        }
        
        # If user has applications, extract resume info from the first one
        if applications and len(applications) > 0:
            first_app = applications[0]
            if isinstance(first_app, dict):
                resume_data["skills"] = first_app.get("skills", [])
                resume_data["experience"] = first_app.get("experience", "Not specified")
        
        # Handle potential race condition where duplicate requests try to create the same interview
        try:
            interview = await storage_service.create_interview_session(
                session_id=session_id,
                job_id=job_id,
                user_email=user_email,
                application_id=f"app_{session_id[:8]}",  # Generate application ID
                job_data=job_data,
                resume_data=resume_data
            )
        except Exception as e:
            # Check if this is a UniqueViolation (duplicate interview)
            error_msg = str(e).lower()
            if "unique_user_job_interview" in error_msg or "duplicate key" in error_msg:
                logger.info(f"Interview already exists for user={user_email}, job={job_id}, retrieving existing")
                # Get the existing interview that was just created by the parallel request
                existing = await storage_service.get_interview_by_user_and_job(user_email, job_id)
                if existing:
                    logger.info(f"Retrieved existing interview: {existing.session_id}")
                    return await _format_active_response(existing)
                else:
                    # Fallback if we can't retrieve the existing interview
                    raise Exception("Failed to create or retrieve interview session")
            else:
                # Re-raise other database errors
                raise e
        
        # Update application status to INPROGRESS
        try:
            status_result = await application_status_update(
                job_id=job_id,
                user_email=user_email,
                new_status="INPROGRESS"
            )
            if status_result.get("success"):
                logger.info(f"Application status updated to INPROGRESS: {status_result}")
            else:
                logger.warning(f"Failed to update application status: {status_result}")
        except Exception as e:
            logger.error(f"Error updating application status to INPROGRESS: {e}")
        
        # Generate first question using interview conductor
        logger.info(f"Starting interview question generation for session {session_id}")
        dependencies = {
            "process_with_tools": process_with_tools,  # LLM service for generating questions
            "job_details_get": job_details_get,
            "user_applications_get": user_applications_get,
            "application_status_update": application_status_update
        }
        
        try:
            first_question = await interview_conductor.conduct_interview(
                session_id=session_id,
                job_id=job_id,
                user_email=user_email,
                application_id=f"app_{session_id[:8]}",
                dependencies=dependencies
            )
            
            # Validate question data is complete
            if not first_question or not first_question.get("question", {}).get("text"):
                raise Exception(f"Question generation failed - no question text returned")
                
            logger.info(f"First question generated successfully for session {session_id}")
            
        except Exception as question_error:
            logger.error(f"Failed to generate first question for session {session_id}: {question_error}")
            raise Exception(f"Interview start failed: Unable to generate first question - {str(question_error)}")
        
        # Calculate time remaining
        duration_minutes = job_data.get("interview_duration_minutes", 60)
        time_remaining_seconds = duration_minutes * 60
        
        return {
            "success": True,
            "status": "INPROGRESS",
            "session_id": session_id,
            "current_question": first_question.get("question", {}).get("text"),
            "question_metadata": {
                "type": first_question.get("question", {}).get("type"),
                "difficulty": first_question.get("question", {}).get("difficulty"),
                "focus_area": first_question.get("question", {}).get("focus_area"),
                "question_number": first_question.get("question", {}).get("number")
            },
            "conversation_history": [],
            "session_info": {
                "questions_asked": 1,
                "questions_answered": 0,
                "time_remaining_seconds": time_remaining_seconds
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating new interview: {e}")
        return {
            "success": False,
            "error": str(e),
            "status": "error"
        }


async def _format_active_response(interview) -> Dict[str, Any]:
    """Format response for active interview."""
    try:
        from .services.storage_service import storage_service
        conversation = await storage_service.get_conversation_history(interview.session_id)
        
        # Get current unanswered question
        current_question = None
        current_metadata = {}
        if conversation and not conversation[-1].get("response"):
            current_question = conversation[-1]["question"]["text"]
            current_metadata = {
                "type": conversation[-1]["question"]["type"],
                "difficulty": conversation[-1]["question"]["difficulty"],
                "focus_area": conversation[-1]["question"]["focus_area"],
                "question_number": conversation[-1]["question"]["number"]
            }
        
        # Calculate time remaining
        # Ensure both datetimes are timezone-aware
        now_utc = datetime.now(timezone.utc)
        created_at_utc = interview.created_at.replace(tzinfo=timezone.utc) if interview.created_at.tzinfo is None else interview.created_at
        elapsed = (now_utc - created_at_utc).total_seconds()
        duration_seconds = interview.duration_minutes * 60
        time_remaining = max(0, duration_seconds - elapsed)
        
        return {
            "success": True,
            "status": "INPROGRESS",
            "session_id": interview.session_id,
            "current_question": current_question,
            "question_metadata": current_metadata,
            "conversation_history": [c for c in conversation if c.get("response")],
            "session_info": {
                "questions_asked": len(conversation),
                "questions_answered": len([c for c in conversation if c.get("response")]),
                "time_remaining_seconds": int(time_remaining)
            }
        }
        
    except Exception as e:
        logger.error(f"Error formatting active response: {e}")
        return {
            "success": False,
            "error": str(e),
            "status": "error"
        }


def _format_completed_response(interview) -> Dict[str, Any]:
    """Format response for completed interview."""
    return {
        "success": True,
        "status": interview.status,
        "session_id": interview.session_id,
        "completion_reason": interview.session_metadata.get("completion_reason") if interview.session_metadata else None,
        "completed_at": interview.updated_at.isoformat(),
        "message": f"Interview {interview.status}. No further action possible."
    }



def _is_expired(interview) -> bool:
    """Check if interview has expired."""
    if not interview.expires_at:
        return False
    
    current_time = datetime.now(timezone.utc)
    expires_at = interview.expires_at
    
    # Handle timezone-naive datetime
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    return current_time > expires_at


@app.tool()
@mesh.tool(
    capability="get_job_interviews",
    tags=["interview-data", "admin", "analytics"],
    description="Get all completed interviews for a specific job with evaluation data"
)
async def get_job_interviews(job_id: str) -> Dict[str, Any]:
    """
    Get all completed interviews for a specific job ID.
    
    Returns interview data with evaluation scores when available.
    Some interviews may not have evaluation data if processing failed.
    
    Args:
        job_id: Job identifier to get interviews for
        
    Returns:
        Dictionary with interviews array and statistics
    """
    try:
        logger.info(f"Getting all completed interviews for job_id={job_id}")
        
        from .services.storage_service import storage_service
        
        # Get all completed interviews for this job
        interviews = await storage_service.get_interviews_by_job_id(job_id, status="COMPLETED")
        
        if not interviews:
            logger.info(f"No completed interviews found for job_id={job_id}")
            return {
                "success": True,
                "interviews": [],
                "statistics": {
                    "total_interviews": 0,
                    "average_score": 0,
                    "strong_yes_count": 0,
                    "yes_count": 0,
                    "hire_rate": 0
                }
            }
        
        logger.info(f"Found {len(interviews)} completed interviews for job_id={job_id}")
        
        # Format interviews with evaluation data
        formatted_interviews = []
        scores = []
        hire_recommendations = []
        
        for interview in interviews:
            # Base interview data - use user_email for both candidate fields since we don't store name separately
            interview_data = {
                "session_id": interview.session_id,
                "candidate_name": interview.user_email.split('@')[0],  # Use email prefix as name fallback
                "candidate_email": interview.user_email,
                "interview_date": interview.started_at.isoformat() if interview.started_at else None,
                "completion_reason": interview.session_metadata.get("completion_reason") if interview.session_metadata else None,
                "ended_at": interview.ended_at.isoformat() if interview.ended_at else None,
                "duration": interview.session_metadata.get("duration_seconds") if interview.session_metadata else None
            }
            
            # Add evaluation data if available
            if interview.evaluation_completed and interview.evaluation:
                evaluation = interview.evaluation
                interview_data.update({
                    "overall_score": evaluation.overall_score,
                    "technical_knowledge": evaluation.technical_knowledge,
                    "problem_solving": evaluation.problem_solving,
                    "communication": evaluation.communication,
                    "experience_relevance": evaluation.experience_relevance,
                    "hire_recommendation": evaluation.hire_recommendation,
                    "feedback": evaluation.feedback
                })
                
                # Collect data for statistics
                if evaluation.overall_score:
                    scores.append(evaluation.overall_score)
                if evaluation.hire_recommendation:
                    hire_recommendations.append(evaluation.hire_recommendation)
            else:
                # No evaluation data available
                interview_data.update({
                    "overall_score": None,
                    "technical_knowledge": None,
                    "problem_solving": None,
                    "communication": None,
                    "experience_relevance": None,
                    "hire_recommendation": "not_evaluated",
                    "feedback": "Evaluation not completed"
                })
            
            formatted_interviews.append(interview_data)
        
        # Calculate statistics
        total_interviews = len(interviews)
        average_score = sum(scores) / len(scores) if scores else 0
        strong_yes_count = hire_recommendations.count("strong_yes")
        yes_count = hire_recommendations.count("yes")
        hire_rate = ((strong_yes_count + yes_count) / len(hire_recommendations) * 100) if hire_recommendations else 0
        
        statistics = {
            "total_interviews": total_interviews,
            "average_score": round(average_score, 2),
            "strong_yes_count": strong_yes_count,
            "yes_count": yes_count,
            "hire_rate": round(hire_rate, 2)
        }
        
        logger.info(f"Returning {len(formatted_interviews)} interviews with statistics: {statistics}")
        
        return {
            "success": True,
            "interviews": formatted_interviews,
            "statistics": statistics
        }
        
    except Exception as e:
        logger.error(f"Error getting job interviews: {e}")
        return {
            "success": False,
            "error": str(e),
            "interviews": [],
            "statistics": {
                "total_interviews": 0,
                "average_score": 0,
                "strong_yes_count": 0,
                "yes_count": 0,
                "hire_rate": 0
            }
        }


# Agent class definition - MCP Mesh pattern
@mesh.agent(
    name="interview-agent",
    auto_run=True
)
class InterviewAgent(McpAgent):
    """
    Interview Agent for AI Interviewer Phase 2
    
    Handles technical interview sessions with modular PostgreSQL-based architecture.
    Capabilities: conduct_interview, get_session_status, end_interview_session, 
    get_interview_session, finalize_interview
    """
    pass  # Database initialization already done at module level


if __name__ == "__main__":
    logger.info("Interview Agent starting...")
