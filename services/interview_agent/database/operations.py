"""
Database Operations and Utility Functions

Contains high-level database operations for interview management,
including CRUD operations, conversation handling, and statistics.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from .models import Interview, InterviewQuestion, InterviewResponse, InterviewEvaluation
from .database import get_db_session


# Interview Management Operations

def get_interview_by_session_id(session_id: str, db: Session) -> Optional[Interview]:
    """Get interview by session ID with relationships loaded"""
    return db.query(Interview).filter(Interview.session_id == session_id).first()


def get_interview_by_id(interview_id: uuid.UUID, db: Session) -> Optional[Interview]:
    """Get interview by ID with relationships loaded"""
    return db.query(Interview).filter(Interview.id == interview_id).first()


def get_active_interviews_by_user(user_email: str, db: Session) -> List[Interview]:
    """Get all active interviews for a user"""
    return db.query(Interview).filter(
        Interview.user_email == user_email,
        Interview.status.in_(["started", "active"])
    ).all()


def create_interview_session(
    session_id: str, 
    job_id: str, 
    user_email: str, 
    role_description: str, 
    resume_content: str, 
    duration_minutes: int,
    db: Session
) -> Interview:
    """Create new interview session"""
    interview = Interview(
        session_id=session_id,
        job_id=job_id,
        user_email=user_email,
        role_description=role_description,
        resume_content=resume_content,
        duration_minutes=duration_minutes,
        expires_at=datetime.utcnow() + timedelta(minutes=duration_minutes),
        status="started"
    )
    
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    return interview


def update_interview_status(
    interview_id: uuid.UUID, 
    status: str, 
    completion_reason: Optional[str] = None,
    db: Session = None
) -> bool:
    """Update interview status and completion reason"""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        return False
    
    interview.status = status
    if completion_reason:
        interview.completion_reason = completion_reason
    if status in ["completed", "expired", "terminated"]:
        interview.ended_at = datetime.utcnow()
    
    db.commit()
    return True


# Question Management Operations

def add_interview_question(
    interview_id: uuid.UUID,
    question_text: str,
    question_number: int,
    question_metadata: Dict[str, Any],
    db: Session
) -> InterviewQuestion:
    """Add new question to interview"""
    question = InterviewQuestion(
        interview_id=interview_id,
        question_text=question_text,
        question_number=question_number,
        question_type=question_metadata.get("question_type", "unknown"),
        focus_area=question_metadata.get("focus_area", "general"),
        difficulty_level=question_metadata.get("difficulty_level", "intermediate"),
        role_requirement_addressed=question_metadata.get("role_requirement_addressed", "general"),
        coverage_strategy=question_metadata.get("coverage_strategy", "comprehensive_coverage"),
        expected_assessment=question_metadata.get("expected_assessment", ""),
        ai_provider=question_metadata.get("ai_provider"),
        ai_model=question_metadata.get("ai_model"),
        generation_context=question_metadata
    )
    
    db.add(question)
    db.commit()
    db.refresh(question)
    
    # Update interview questions_asked counter
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if interview:
        # Count actual questions instead of using question_number
        actual_count = db.query(InterviewQuestion).filter(InterviewQuestion.interview_id == interview_id).count()
        interview.questions_asked = actual_count
        interview.current_question_id = question.id
        db.commit()
    
    return question


def get_interview_questions(interview_id: uuid.UUID, db: Session) -> List[InterviewQuestion]:
    """Get all questions for an interview ordered by question number"""
    return db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview_id
    ).order_by(InterviewQuestion.question_number).all()


def get_unanswered_questions(interview_id: uuid.UUID, db: Session) -> List[InterviewQuestion]:
    """Get all questions that don't have responses yet"""
    return db.query(InterviewQuestion).outerjoin(InterviewResponse).filter(
        InterviewQuestion.interview_id == interview_id,
        InterviewResponse.id.is_(None)
    ).order_by(InterviewQuestion.question_number).all()


# Response Management Operations

def add_interview_response(
    interview_id: uuid.UUID,
    question_id: uuid.UUID,
    response_text: str,
    response_metadata: Optional[Dict[str, Any]] = None,
    db: Session = None
) -> InterviewResponse:
    """Add user response to interview question"""
    metadata = response_metadata or {}
    
    response = InterviewResponse(
        interview_id=interview_id,
        question_id=question_id,
        response_text=response_text,
        response_length_words=len(response_text.split()) if response_text else 0,
        response_time_seconds=metadata.get("response_time_seconds"),
        input_method=metadata.get("input_method", "text")
    )
    
    db.add(response)
    db.commit()
    db.refresh(response)
    
    return response


def get_interview_responses(interview_id: uuid.UUID, db: Session) -> List[InterviewResponse]:
    """Get all responses for an interview"""
    return db.query(InterviewResponse).filter(
        InterviewResponse.interview_id == interview_id
    ).order_by(InterviewResponse.created_at).all()


# Conversation Management Operations

def get_interview_conversation_pairs(interview_id: uuid.UUID, db: Session) -> List[Dict[str, Any]]:
    """
    Get all question-answer pairs for an interview in chronological order.
    Returns list of Q&A pairs for LLM context and UI display.
    """
    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview_id
    ).order_by(InterviewQuestion.question_number).all()
    
    conversation_pairs = []
    
    for question in questions:
        pair = {
            "question_id": str(question.id),
            "question_number": question.question_number,
            "question": {
                "text": question.question_text,
                "type": question.question_type,
                "focus_area": question.focus_area,
                "difficulty": question.difficulty_level,
                "asked_at": question.asked_at.isoformat() + "Z" if question.asked_at else None,
                "metadata": {
                    "role_requirement_addressed": question.role_requirement_addressed,
                    "coverage_strategy": question.coverage_strategy,
                    "expected_assessment": question.expected_assessment
                }
            },
            "response": None
        }
        
        # Add response if it exists
        if question.response:
            pair["response"] = {
                "text": question.response.response_text,
                "submitted_at": question.response.submitted_at.isoformat() + "Z" if question.response.submitted_at else None,
                "response_time_seconds": question.response.response_time_seconds,
                "input_method": question.response.input_method,
                "word_count": question.response.response_length_words,
                "metadata": {
                    "relevance_score": question.response.relevance_score,
                    "completeness_score": question.response.completeness_score,
                    "technical_accuracy": question.response.technical_accuracy
                }
            }
        
        conversation_pairs.append(pair)
    
    return conversation_pairs


def format_conversation_for_llm(interview_id: uuid.UUID, db: Session) -> List[Dict[str, str]]:
    """
    Format conversation history for LLM messages array.
    Returns list of {role: 'assistant'/'user', content: 'text'} messages.
    """
    pairs = get_interview_conversation_pairs(interview_id, db)
    messages = []
    
    for pair in pairs:
        # Add question as assistant message
        messages.append({
            "role": "assistant",
            "content": pair["question"]["text"]
        })
        
        # Add response as user message (if exists)
        if pair["response"]:
            messages.append({
                "role": "user", 
                "content": pair["response"]["text"]
            })
    
    return messages


# Statistics and Analytics Operations

def get_interview_statistics(interview_id: uuid.UUID, db: Session) -> Dict[str, Any]:
    """Get comprehensive interview statistics"""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        return {}
    
    total_questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview_id
    ).count()
    
    total_responses = db.query(InterviewResponse).filter(
        InterviewResponse.interview_id == interview_id  
    ).count()
    
    unanswered_count = total_questions - total_responses
    completion_rate = (total_responses / total_questions * 100) if total_questions > 0 else 0
    
    return {
        "interview_id": str(interview_id),
        "session_id": interview.session_id,
        "status": interview.status,
        "started_at": interview.started_at.isoformat() + "Z" if interview.started_at else None,
        "ended_at": interview.ended_at.isoformat() + "Z" if interview.ended_at else None,
        "duration_minutes": interview.duration_minutes,
        "time_remaining_seconds": interview.time_remaining_seconds,
        "questions": {
            "total": total_questions,
            "answered": total_responses,
            "unanswered": unanswered_count,
            "completion_rate": round(completion_rate, 2)
        },
        "final_score": interview.final_score,
        "evaluation_completed": interview.evaluation_completed
    }


def get_user_interview_history(user_email: str, db: Session) -> List[Dict[str, Any]]:
    """Get interview history for a user with basic statistics"""
    interviews = db.query(Interview).filter(
        Interview.user_email == user_email
    ).order_by(Interview.created_at.desc()).all()
    
    history = []
    for interview in interviews:
        stats = get_interview_statistics(interview.id, db)
        history.append({
            "interview_id": str(interview.id),
            "session_id": interview.session_id,
            "job_id": interview.job_id,
            "status": interview.status,
            "started_at": interview.started_at.isoformat() + "Z" if interview.started_at else None,
            "ended_at": interview.ended_at.isoformat() + "Z" if interview.ended_at else None,
            "duration_minutes": interview.duration_minutes,
            "final_score": interview.final_score,
            "completion_rate": stats.get("questions", {}).get("completion_rate", 0)
        })
    
    return history


# Evaluation Operations

def create_interview_evaluation(
    interview_id: uuid.UUID,
    evaluation_data: Dict[str, Any],
    db: Session
) -> InterviewEvaluation:
    """Create final interview evaluation"""
    evaluation = InterviewEvaluation(
        interview_id=interview_id,
        overall_score=evaluation_data["overall_score"],
        technical_knowledge=evaluation_data["technical_knowledge"],
        problem_solving=evaluation_data["problem_solving"],
        communication=evaluation_data["communication"],
        experience_relevance=evaluation_data["experience_relevance"],
        hire_recommendation=evaluation_data["hire_recommendation"],
        feedback=evaluation_data["feedback"],
        strengths=evaluation_data.get("strengths"),
        areas_for_improvement=evaluation_data.get("areas_for_improvement"),
        questions_answered=evaluation_data["questions_answered"],
        completion_rate=evaluation_data["completion_rate"],
        engagement_quality=evaluation_data.get("engagement_quality"),
        ai_provider=evaluation_data["ai_provider"],
        ai_model=evaluation_data["ai_model"],
        evaluation_context=evaluation_data.get("evaluation_context"),
        confidence_score=evaluation_data.get("confidence_score")
    )
    
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    
    # Update interview with final score and evaluation status
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if interview:
        interview.final_score = evaluation_data["overall_score"]
        interview.evaluation_completed = True
        interview.status = "COMPLETED"
        db.commit()
    
    return evaluation


def get_interview_evaluation(interview_id: uuid.UUID, db: Session) -> Optional[InterviewEvaluation]:
    """Get evaluation for an interview"""
    return db.query(InterviewEvaluation).filter(
        InterviewEvaluation.interview_id == interview_id
    ).first()


# Utility Functions

def cleanup_expired_interviews(db: Session) -> int:
    """Clean up expired interviews that are still marked as active"""
    current_time = datetime.utcnow()
    
    expired_interviews = db.query(Interview).filter(
        Interview.expires_at < current_time,
        Interview.status.in_(["started", "active"])
    ).all()
    
    count = 0
    for interview in expired_interviews:
        interview.status = "expired"
        interview.completion_reason = "timeout"
        interview.ended_at = current_time
        count += 1
    
    db.commit()
    return count


def get_active_interview_count() -> int:
    """Get count of currently active interviews across all users"""
    with get_db_session() as db:
        return db.query(Interview).filter(
            Interview.status.in_(["started", "active"])
        ).count()