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
        
        # LLM service will handle tool format conversion internally
        tools_to_use = [evaluation_tool]
        logger.info("Using evaluation tool - LLM service will handle format conversion internally")
        
        # Call LLM service for evaluation
        logger.info("Evaluating interview performance with LLM")
        logger.info("🎯 USING TRANSCRIPT-IN-SYSTEM-PROMPT APPROACH (empty messages)")
        logger.info(f"System prompt length: {len(evaluation_system_prompt)} chars")
        logger.info(f"Transcript length: {len(conversation_transcript)} chars")
        logger.info(f"Messages count: {len(conversation_messages)} (should be 0)")
        logger.info(f"Tool name: {evaluation_tool['name']}")
        logger.info(f"Converted tools count: {len(converted_evaluation_tools)}")
        logger.info(f"Force tool use: True")
        
        try:
            llm_response = await llm_service(
                text="Score this candidate now using the tool.",
                system_prompt=evaluation_system_prompt,
                messages=conversation_messages,
                tools=tools_to_use,
                force_tool_use=True,
                temperature=0.1
            )
            logger.info("LLM service call completed successfully")
        except Exception as llm_call_error:
            logger.error(f"LLM service call failed: {llm_call_error}")
            return {"score": 0, "feedback": "LLM service call failed", "error": str(llm_call_error)}
        
        logger.info(f"LLM response keys: {list(llm_response.keys()) if isinstance(llm_response, dict) else 'Not a dict'}")
        
        # Debug the raw values and their truthiness
        success_value = llm_response.get("success")
        tool_calls_value = llm_response.get("tool_calls")
        logger.info(f"SUCCESS raw value: {success_value} (type: {type(success_value)}, bool: {bool(success_value)})")
        logger.info(f"TOOL_CALLS raw value: {tool_calls_value} (type: {type(tool_calls_value)}, bool: {bool(tool_calls_value)})")
        
        if not llm_response.get("success") or not llm_response.get("tool_calls"):
            logger.error(f"LLM failed to evaluate interview: {llm_response.get('error', 'No tool calls')}")
            return {"score": 0, "feedback": "Evaluation failed", "error": "LLM evaluation error"}
        
        # Debug the tool_calls structure in detail
        tool_calls = llm_response.get("tool_calls", [])
        logger.info(f"Tool calls count: {len(tool_calls)}")
        logger.info(f"Full tool_calls structure: {tool_calls}")
        
        if len(tool_calls) == 0:
            logger.error("No tool calls found in LLM response")
            return {"score": 0, "feedback": "No tool calls", "error": "No tool calls in response"}
        
        # Extract evaluation from tool calls with detailed logging
        tool_call = tool_calls[0]
        logger.info(f"First tool call structure: {tool_call}")
        logger.info(f"Tool call keys: {list(tool_call.keys()) if isinstance(tool_call, dict) else 'Not a dict'}")
        
        # Extract evaluation using the same pattern as working interview questions
        try:
            evaluation_result = tool_call["parameters"]
            logger.info(f"Successfully extracted evaluation parameters: {evaluation_result}")
        except KeyError as e:
            logger.error(f"Missing 'parameters' key in tool_call: {tool_call}")
            logger.error(f"Available keys: {list(tool_call.keys()) if isinstance(tool_call, dict) else 'Not a dict'}")
            return {"score": 0, "feedback": "Tool call missing parameters", "error": f"KeyError: {e}"}
        
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
        
        logger.info(f"Interview evaluation completed - Overall: {formatted_result['score']}/100")
        logger.info(f"Detailed scores - Technical: {formatted_result['technical_knowledge']}/25, Problem Solving: {formatted_result['problem_solving']}/25, Communication: {formatted_result['communication']}/25, Experience: {formatted_result['experience_relevance']}/25")
        logger.info(f"Hire Recommendation: {formatted_result['hire_recommendation']}")
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
                result["success"] = result.get("status") == "active" or result.get("status") == "completed"
            
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
        
        # Check if already terminated
        if interview.status in ["completed", "terminated", "abandoned"]:
            return {
                "success": False,
                "error": f"Interview session already {interview.status}",
                "session_id": session_id,
                "current_status": interview.status
            }
        
        # Update interview status in PostgreSQL
        status_mapping = {
            "ended_manually": "completed",
            "user_requested": "completed", 
            "time_expired": "completed",
            "abandoned": "abandoned"
        }
        new_status = status_mapping.get(reason, "completed")
        
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
        application_status = "INTERVIEW_COMPLETED"  # Default status for all manual ends
        if reason == "abandoned":
            application_status = "DECISION_PENDING"  # For abandoned interviews
        
        try:
            # Extract application_id from session metadata
            metadata = interview.session_metadata or {}
            application_id = metadata.get("application_id")
            
            if application_id and application_status_update:
                await application_status_update(
                    application_id=application_id,
                    new_status=application_status
                )
                logger.info(f"Updated application {application_id} status to {application_status}")
            else:
                logger.warning(f"Could not update application status: application_id={application_id}, agent_available={application_status_update is not None}")
                
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
    timeout=60,
    dependencies=[
        {
            "capability": "process_with_tools",
            "tags": ["+openai"],  # tag time is optional (plus to have)
        }
    ]
)
async def finalize_interview(session_id: str, llm_service: McpAgent = None) -> Dict[str, Any]:
    """
    Manually finalize an interview session with scoring.
    
    Args:
        session_id: Unique session identifier to finalize
        
    Returns:
        Dictionary containing finalization result and score
    """
    try:
        logger.info(f"Manual finalization requested for session: {session_id}")
        
        # Check if LLM service is available
        if not llm_service:
            return {
                "success": False,
                "error": "LLM service not available for evaluation",
                "session_id": session_id
            }
        
# Get session data
        session_data = get_session_data(session_id)
        if not session_data:
            return {
                "success": False,
                "error": "Session not found",
                "session_id": session_id
            }
        
        # Check if already completed
        current_status = session_data.get("status")
        if current_status == "completed":
            return {
                "success": True,
                "session_id": session_id,
                "status": "completed",
                "score": session_data.get("final_score", 0),
                "evaluation": session_data.get("evaluation", {}),
                "message": "Session already completed"
            }
        
        # Mark as processing to prevent double-processing
        session_data["status"] = "processing"
        session_data["processing_started_at"] = datetime.now(timezone.utc).isoformat()
        store_session_data(session_id, session_data)
        
        # Get data needed for evaluation
        conversation = session_data.get("conversation", [])
        role_description = session_data.get("role_description", "")
        resume_content = session_data.get("resume_content", "")
        
        # Determine completion reason
        completion_reason = "manual"  # Backend will handle expired sessions
        
        # Evaluate performance using LLM service
        evaluation = await evaluate_interview_performance(
            conversation=conversation,
            role_description=role_description, 
            resume_content=resume_content,
            llm_service=llm_service
        )
        
        # Update session with final status and score
        session_data.update({
            "status": "completed",
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "completion_reason": completion_reason,
            "evaluation": evaluation,
            "final_score": evaluation.get("score", 0)
        })
        
        # Store final session data
        store_session_data(session_id, session_data)
        
        logger.info(f"Interview {session_id} finalized with score: {evaluation.get('score', 0)} (reason: {completion_reason})")
        
        return {
            "success": True,
            "session_id": session_id,
            "status": "completed",
            "score": evaluation.get("score", 0),
            "evaluation": evaluation,
            "completion_reason": completion_reason,
            "message": f"Interview finalized with LLM evaluation ({completion_reason})"
        }
                
    except Exception as e:
        logger.error(f"Error in finalization for {session_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id
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
