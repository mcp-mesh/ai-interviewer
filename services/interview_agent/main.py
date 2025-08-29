#!/usr/bin/env python3
"""
Interview Agent - Main Implementation

AI-powered technical interviewer that conducts dynamic interviews based on 
role requirements and candidate profiles with Redis session management.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import mesh
import redis
from fastmcp import FastMCP

# Import specific agent types for type hints
from mesh.types import McpAgent, McpMeshAgent

# Create FastMCP app instance
app = FastMCP("Interview Agent Service")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    version="1.0",
    dependencies=[
        {
            "capability": "process_with_tools",
            "tags": ["+openai"],  # tag time is optional (plus to have)
        }
    ],
    tags=["interview", "technical-screening", "ai-interviewer", "session-management"],
    timeout=120,
    retry_count=2
)
async def conduct_interview(
    resume_content: str,
    role_description: str,
    user_session_id: str,
    candidate_answer: str = None,
    duration_minutes: int = None,
    llm_service: McpAgent = None
) -> Dict[str, Any]:
    """
    Conduct a technical interview session with session management.
    
    Args:
        resume_content: Candidate's resume content (text or structured data)
        role_description: Job role requirements and description
        user_session_id: Unique session identifier for this interview
        candidate_answer: Optional candidate's answer to previous question
        llm_service: LLM service for generating questions
    
    Returns:
        Dictionary containing next question and session metadata
    """
    try:
        logger.info(f"Conducting interview for session: {user_session_id}")
        
        # Check if LLM service is available
        logger.info(f"LLM service type: {type(llm_service)}")
        logger.info(f"LLM service value: {llm_service}")
        
        if not llm_service:
            return {
                "success": False,
                "error": "LLM service not available",
                "session_id": user_session_id
            }
        
        # Get or create session
        session_data = get_session_data(user_session_id)
        
        # Check if existing session has expired
        if session_data and check_session_expiration(session_data):
            logger.info(f"Session {user_session_id} has expired, ending it")
            end_session(user_session_id, "timeout")
            return {
                "success": False,
                "error": "Interview session has expired",
                "session_id": user_session_id,
                "expired": True
            }
        
        if not session_data:
            # Create new session with complete metadata
            logger.info(f"Creating new interview session: {user_session_id}")
            start_time = datetime.now(timezone.utc)
            duration_seconds = (duration_minutes * 60) if duration_minutes else DEFAULT_INTERVIEW_DURATION
            session_data = {
                "session_id": user_session_id,
                "role_description": role_description,
                "resume_content": resume_content,
                "conversation": [],
                
                # Timing and duration
                "started_at": start_time.isoformat(),
                "duration_minutes": duration_minutes or (DEFAULT_INTERVIEW_DURATION // 60),
                "expires_at": (start_time.timestamp() + duration_seconds),
                
                # Session state
                "status": "started",  # started|ended
                "user_action": "none",  # none|ended_manually|timeout|completed
                "questions_asked": 0,
                "current_question": None,
                "question_metadata": {},
                "total_score": 0,
                
                # Metadata
                "created_at": start_time.isoformat(),
                "last_updated": start_time.isoformat(),
                "ended_at": None
            }
            
            if not store_session_data(user_session_id, session_data):
                raise RuntimeError("Failed to create session")
        
        # Store candidate answer if provided
        if candidate_answer:
            logger.info(f"Storing candidate answer for session: {user_session_id}")
            if not add_to_conversation(user_session_id, "answer", candidate_answer):
                logger.warning("Failed to store candidate answer")
            
            # Refresh session data
            session_data = get_session_data(user_session_id)
        
        # Analyze conversation history to track coverage
        conversation_messages = format_conversation_for_llm(session_data["conversation"])
        questions_asked = len([msg for msg in session_data["conversation"] if msg["type"] == "question"])
        
        # Prepare context for LLM
        system_prompt = f"""You are conducting a strategic technical interview for the following role:

ROLE DESCRIPTION:
{role_description}

CANDIDATE RESUME:
{resume_content}

INTERVIEW PROGRESS:
- Questions Asked So Far: {questions_asked}
- Previous Questions and Answers: See conversation history below

STRATEGIC INTERVIEW APPROACH:

1. **PRIMARY OBJECTIVE**: Systematically assess ALL key requirements from the role description
2. **COVERAGE STRATEGY**: Plan questions to comprehensively evaluate each requirement area
3. **ROLE-DRIVEN APPROACH**: Use role requirements as the primary driver, not just candidate's resume
4. **SYSTEMATIC EVALUATION**: Ensure broad coverage rather than deep diving into one area too early

QUESTION SELECTION PRIORITIES:

**For Question 1 (Opening):**
- MUST use question_type: "opener" 
- Start with a friendly, role-relevant opening question that assesses core competencies
- Use resume as context but focus on role requirements
- Create a welcoming transition into the technical interview

**For Questions 2-5 (Core Assessment):**
- Cover the MOST CRITICAL requirements from the role description
- Ask about specific technologies, frameworks, and skills mentioned in the role
- Assess hands-on experience with required tools and platforms

**For Questions 6+ (Deep Dive & Gaps):**
- Fill any remaining coverage gaps from role requirements
- Ask follow-up questions to probe deeper into critical areas
- Address any requirements not yet covered

REQUIREMENTS COVERAGE CHECKLIST (extract from role description):
- Identify 3-5 key technical requirements from the role description
- Track which requirements have been adequately assessed
- Prioritize uncovered requirements for next questions
- Balance technical skills with problem-solving and experience

INTERVIEW TACTICS:
- Ask specific, measurable questions about role technologies
- Use scenario-based questions related to actual job responsibilities  
- Probe for depth of knowledge in role-critical areas
- Ask for concrete examples from their experience with required skills
- Follow up with "how would you..." questions for practical application

Your goal is to conduct a comprehensive interview that thoroughly evaluates the candidate against ALL major role requirements, not just areas where they show strength.

QUESTION TYPE SELECTION GUIDE:
- question_type: "opener" → Use for Question 1 ONLY to create a welcoming start
- question_type: "technical" → Use for specific technology/skill assessments
- question_type: "experience" → Use for past experience and accomplishments
- question_type: "problem_solving" → Use for analytical thinking assessments
- question_type: "behavioral" → Use for soft skills and work style evaluation
- question_type: "scenario" → Use for hypothetical situation responses
- question_type: "requirement_specific" → Use for role-specific capabilities

Generate the next strategic interview question using the provided tool."""
        
        # Define tool schema for interview questions
        interview_question_tool = {
            "name": "generate_interview_question",
            "description": "Generate the next strategic interview question based on role requirements and systematic coverage planning",
            "input_schema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The next interview question to ask the candidate"
                    },
                    "question_type": {
                        "type": "string",
                        "enum": ["opener", "technical", "experience", "problem_solving", "behavioral", "clarification", "scenario", "requirement_specific"],
                        "description": "Type of question being asked"
                    },
                    "focus_area": {
                        "type": "string",
                        "description": "The skill or competency area this question targets"
                    },
                    "difficulty_level": {
                        "type": "string",
                        "enum": ["basic", "intermediate", "advanced"],
                        "description": "Difficulty level of the question"
                    },
                    "role_requirement_addressed": {
                        "type": "string",
                        "description": "Specific role requirement or skill this question is designed to assess"
                    },
                    "coverage_strategy": {
                        "type": "string",
                        "enum": ["opening_assessment", "core_requirement", "gap_filling", "depth_probe", "comprehensive_coverage"],
                        "description": "Strategic purpose of this question in the overall interview plan"
                    },
                    "expected_assessment": {
                        "type": "string",
                        "description": "What specific aspect of the candidate's competency this question will reveal"
                    }
                },
                "required": ["question", "question_type", "focus_area", "role_requirement_addressed", "coverage_strategy"]
            }
        }
        
        # Format conversation history for LLM
        conversation_messages = format_conversation_for_llm(session_data["conversation"])
        
        # LLM service will handle tool format conversion internally
        tools_to_use = [interview_question_tool]
        logger.info("Using interview question tool - LLM service will handle format conversion internally")
        
        # Call LLM service with converted tools
        logger.info("Generating next interview question with LLM")
        llm_response = await llm_service(
            text="Generate the next interview question based on the role requirements and conversation history.",
            system_prompt=system_prompt,
            messages=conversation_messages,
            tools=tools_to_use,
            force_tool_use=True,
            temperature=0.7  # Slight creativity for varied questions
        )
        
        logger.info(f"LLM response type: {type(llm_response)}")
        logger.info(f"LLM response: {llm_response}")
        
        if not llm_response.get("success") or not llm_response.get("tool_calls"):
            logger.error(f"LLM failed to generate question: {llm_response.get('error', 'No tool calls')}")
            return {
                "success": False,
                "error": "Failed to generate interview question",
                "session_id": user_session_id
            }
        
        # Extract question from LLM response
        question_data = llm_response["tool_calls"][0]["parameters"]
        question = question_data["question"]
        
        # Store question in conversation with metadata and update session state
        question_number = len([m for m in session_data["conversation"] if m["type"] == "question"]) + 1
        question_metadata = {
            "type": question_data.get("question_type", "unknown"),
            "focus_area": question_data.get("focus_area", "general"),
            "difficulty": question_data.get("difficulty_level", "intermediate"),
            "question_number": question_number,
            "role_requirement_addressed": question_data.get("role_requirement_addressed", "general"),
            "coverage_strategy": question_data.get("coverage_strategy", "comprehensive_coverage"),
            "expected_assessment": question_data.get("expected_assessment", "")
        }
        
        if not add_to_conversation(user_session_id, "question", question, question_metadata):
            logger.warning("Failed to store interview question")
        
        # Update session state with new question
        session_data = get_session_data(user_session_id)  # Refresh after conversation update
        if session_data:
            session_data["questions_asked"] = question_number
            session_data["current_question"] = question
            session_data["question_metadata"] = question_metadata
            session_data["last_updated"] = datetime.now(timezone.utc).isoformat()
            store_session_data(user_session_id, session_data)
        
        # Prepare response
        response = {
            "success": True,
            "session_id": user_session_id,
            "question": question,
            "question_metadata": {
                "type": question_data.get("question_type", "unknown"),
                "focus_area": question_data.get("focus_area", "general"),
                "difficulty": question_data.get("difficulty_level", "intermediate"),
                "question_number": len([m for m in session_data["conversation"] if m["type"] == "question"]),
                "role_requirement_addressed": question_data.get("role_requirement_addressed", "general"),
                "coverage_strategy": question_data.get("coverage_strategy", "comprehensive_coverage"),
                "expected_assessment": question_data.get("expected_assessment", "")
            },
            "session_info": {
                "created_at": session_data["created_at"],
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_questions": len([m for m in session_data["conversation"] if m["type"] == "question"]),
                "total_answers": len([m for m in session_data["conversation"] if m["type"] == "answer"])
            }
        }
        
        logger.info(f"Generated question for session {user_session_id}: {question_data.get('question_type', 'unknown')} question")
        return response
        
    except Exception as e:
        logger.error(f"Interview failed for session {user_session_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": user_session_id
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
@mesh.tool(capability="end_interview_session")
def end_interview_session(session_id: str, reason: str = "ended_manually") -> Dict[str, Any]:
    """End an interview session."""
    try:
        if end_session(session_id, reason):
            return {
                "success": True,
                "session_id": session_id,
                "message": f"Interview session ended: {reason}"
            }
        else:
            return {
                "success": False,
                "error": "Failed to end session or session not found",
                "session_id": session_id
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
        logger.info(f"Retrieving session data: {session_id}")
        
        session_data = get_session_data(session_id)
        if not session_data:
            return {
                "success": False,
                "error": "Session not found",
                "session_id": session_id
            }
        
        # Calculate session statistics
        conversation = session_data.get("conversation", [])
        questions = [m for m in conversation if m["type"] == "question"]
        answers = [m for m in conversation if m["type"] == "answer"]
        
        return {
            "success": True,
            "session_data": session_data,
            "statistics": {
                "total_questions": len(questions),
                "total_answers": len(answers),
                "session_duration": session_data.get("created_at"),
                "last_activity": session_data.get("last_updated"),
                "status": session_data.get("status", "active")
            }
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


@app.tool()
@mesh.tool(capability="health_check", tags=["interview_service", "session_management", "ai_interviewer"])
def get_agent_status() -> Dict[str, Any]:
    """
    Get interview agent status and configuration.
    
    Returns:
        Dictionary containing agent status and capabilities
    """
    try:
        # Test Redis connectivity
        redis_status = "connected"
        redis_info = {}
        
        if redis_client:
            try:
                redis_client.ping()
                info = redis_client.info()
                redis_info = {
                    "version": info.get("redis_version", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown")
                }
            except Exception as e:
                redis_status = f"error: {str(e)}"
        else:
            redis_status = "not_connected"
        
        return {
            "agent_name": "Interview Agent",
            "version": "1.0.0",
            "status": "healthy",
            "capabilities": [
                "interview-service",
                "session-management", 
                "conversation-tracking",
                "dynamic-questioning"
            ],
            "dependencies": {
                "llm-service": "required",
                "redis": redis_status
            },
            "configuration": {
                "redis_host": REDIS_HOST,
                "redis_port": REDIS_PORT,
                "session_ttl": "dynamic (based on role duration)",
                "session_prefix": SESSION_PREFIX
            },
            "redis_info": redis_info,
            "supported_operations": [
                "conduct_interview",
                "get_interview_session", 
                "end_interview_session",
                "finalize_interview",
                "get_agent_status"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


# Agent class definition - MCP Mesh will auto-discover and run the FastMCP app
@mesh.agent(
    name="interview-agent",
    auto_run=True
)
class InterviewAgent:
    """
    Interview Agent for AI Interviewer System
    
    Conducts dynamic technical interviews based on role requirements and 
    candidate profiles with Redis-based session management.
    
    MCP Mesh automatically:
    1. Discovers the 'app' FastMCP instance
    2. Applies dependency injection for LLM service
    3. Starts HTTP server on port 8084
    4. Registers capabilities with mesh registry
    """
    
    def __init__(self):
        logger.info("Initializing Interview Agent v1.0.0")
        logger.info(f"Redis connection: {'Connected' if redis_client else 'Not available'}")
        logger.info("Interview agent ready for technical screening sessions")
        
        if redis_client:
            logger.info("Session management enabled with dynamic TTL based on role duration")
        else:
            logger.warning("Redis not available - session management disabled")


# MCP Mesh handles everything automatically:
# - FastMCP server discovery and startup
# - Dependency injection (LLM service)
# - HTTP server on port 8084  
# - Service registration with mesh registry
