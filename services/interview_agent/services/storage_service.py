"""
Storage Service - PostgreSQL Database Operations

Provides high-level database operations for interview sessions, questions,
responses, and evaluations with proper error handling and connection management.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from ..database import (
    Interview, InterviewQuestion, InterviewResponse, InterviewEvaluation,
    Base, get_db_session
)

logger = logging.getLogger(__name__)

class StorageService:
    """
    High-level storage operations for interview data with PostgreSQL backend.
    """
    
    def __init__(self):
        """Initialize storage service."""
        self.logger = logging.getLogger(__name__)
    
    async def create_interview_session(
        self,
        session_id: str,
        job_id: str,
        user_email: str,
        application_id: str,
        job_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Interview:
        """
        Create a new interview session with all required data.
        
        Args:
            session_id: Unique session identifier
            job_id: Job posting identifier
            user_email: User's email address
            application_id: Application identifier
            job_data: Job posting details
            resume_data: User's resume information
            metadata: Additional session metadata
            
        Returns:
            Interview: Created interview session
            
        Raises:
            SQLAlchemyError: Database operation failed
        """
        try:
            with get_db_session() as db:
                # Extract role description from job data
                role_description = job_data.get("description", f"Role: {job_data.get('title', 'Unknown Position')}")
                
                # Extract resume content from resume data  
                resume_content = ""
                if isinstance(resume_data, dict):
                    skills = resume_data.get("skills", [])
                    experience = resume_data.get("experience", [])
                    resume_content = f"Skills: {', '.join(skills) if skills else 'Not specified'}\n"
                    resume_content += f"Experience: {experience if experience else 'Not specified'}"
                else:
                    resume_content = str(resume_data) if resume_data else "Resume not provided"
                
                # Set expiration time based on job duration (default 60 minutes from now)
                from datetime import timedelta
                job_duration = job_data.get("interview_duration_minutes", 60)
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=job_duration)
                
                interview = Interview(
                    session_id=session_id,
                    job_id=job_id,
                    user_email=user_email,
                    role_description=role_description,
                    resume_content=resume_content,
                    status="INPROGRESS",
                    expires_at=expires_at,
                    duration_minutes=job_duration,
                    session_metadata={
                        "application_id": application_id,
                        "job_data": job_data,
                        "resume_data": resume_data,
                        **(metadata or {})
                    }
                )
                
                db.add(interview)
                db.commit()
                db.refresh(interview)
                
                self.logger.info(f"Created interview session: {session_id}")
                return interview
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to create interview session {session_id}: {e}")
            raise
    
    async def get_interview_by_session_id(self, session_id: str) -> Optional[Interview]:
        """
        Get interview session by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Interview or None if not found
        """
        try:
            with get_db_session() as db:
                interview = db.query(Interview).filter(
                    Interview.session_id == session_id
                ).first()
                
                return interview
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get interview session {session_id}: {e}")
            raise
    
    async def get_interview_by_user_and_job(self, user_email: str, job_id: str) -> Optional[Interview]:
        """
        Get interview session by user email and job ID.
        
        Args:
            user_email: User's email address
            job_id: Job posting identifier
            
        Returns:
            Interview or None if not found
        """
        try:
            self.logger.info(f"Searching for existing interview: user={user_email}, job={job_id}")
            
            with get_db_session() as db:
                interview = db.query(Interview).filter(
                    Interview.user_email == user_email,
                    Interview.job_id == job_id
                    # REMOVED: Interview.status == "active" filter - now finds ANY interview
                ).first()
                
                if interview:
                    self.logger.info(f"Found existing interview: session_id={interview.session_id}, status={interview.status}")
                else:
                    self.logger.info(f"No existing interview found for user={user_email}, job={job_id}")
                
                return interview
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get interview for user {user_email}, job {job_id}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting interview for user {user_email}, job {job_id}: {e}")
            raise
    
    async def update_interview_status(
        self,
        session_id: str,
        status: str,
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update interview session status and metadata.
        
        Args:
            session_id: Session identifier
            status: New status (active, completed, abandoned)
            metadata_updates: Additional metadata to merge
            
        Returns:
            bool: Success status
        """
        try:
            with get_db_session() as db:
                interview = db.query(Interview).filter(
                    Interview.session_id == session_id
                ).first()
                
                if not interview:
                    self.logger.warning(f"Interview session not found: {session_id}")
                    return False
                
                interview.status = status
                interview.updated_at = datetime.now(timezone.utc)
                
                # Set ended_at when status changes to COMPLETED
                if status == "COMPLETED" and interview.ended_at is None:
                    interview.ended_at = datetime.now(timezone.utc)
                    self.logger.info(f"Set ended_at for completed interview session {session_id}")
                
                if metadata_updates:
                    current_metadata = interview.session_metadata if interview.session_metadata else {}
                    interview.session_metadata = {**current_metadata, **metadata_updates}
                
                db.commit()
                self.logger.info(f"Updated interview session {session_id} status to {status}")
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to update interview session {session_id}: {e}")
            raise
    
    async def add_question(
        self,
        session_id: str,
        question_text: str,
        question_type: str = "technical",
        difficulty: str = "medium",
        metadata: Optional[Dict[str, Any]] = None
    ) -> InterviewQuestion:
        """
        Add a question to the interview session.
        
        Args:
            session_id: Session identifier
            question_text: The question text
            question_type: Type of question (technical, behavioral, etc.)
            difficulty: Question difficulty level
            metadata: Additional question metadata
            
        Returns:
            InterviewQuestion: Created question record
        """
        try:
            with get_db_session() as db:
                # Get the interview record to get its UUID for the foreign key
                interview = db.query(Interview).filter(
                    Interview.session_id == session_id
                ).first()
                
                if not interview:
                    raise ValueError(f"Interview with session_id {session_id} not found")
                
                question = InterviewQuestion(
                    interview_id=interview.id,
                    question_text=question_text,
                    question_number=interview.questions_asked + 1,
                    question_type=question_type,
                    focus_area="General Assessment",  # Default value
                    difficulty_level=difficulty,
                    role_requirement_addressed="Assessment of candidate capabilities",  # Default value
                    coverage_strategy="core_requirement",  # Default value
                    asked_at=datetime.now(timezone.utc)
                )
                
                db.add(question)
                db.commit()
                db.refresh(question)
                
                # Update interview counters and current question reference
                interview.questions_asked = db.query(InterviewQuestion).filter(InterviewQuestion.interview_id == interview.id).count()
                interview.current_question_id = question.id
                db.commit()
                
                self.logger.info(f"Added question {question.question_number} to session {session_id}, total questions: {interview.questions_asked}")
                return question
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to add question to session {session_id}: {e}")
            raise
    
    async def add_response(
        self,
        session_id: str,
        question_id: int,
        response_text: str,
        response_time_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        violations: Optional[Dict[str, Any]] = None
    ) -> InterviewResponse:
        """
        Add a user response to a question.
        
        Args:
            session_id: Session identifier
            question_id: Question ID being answered
            response_text: User's response
            response_time_seconds: Time taken to respond
            metadata: Additional response metadata
            
        Returns:
            InterviewResponse: Created response record
        """
        try:
            with get_db_session() as db:
                # Get the interview record to get its UUID for the foreign key
                interview = db.query(Interview).filter(
                    Interview.session_id == session_id
                ).first()
                
                if not interview:
                    raise ValueError(f"Interview with session_id {session_id} not found")
                
                response = InterviewResponse(
                    interview_id=interview.id,
                    question_id=question_id,
                    response_text=response_text,
                    response_time_seconds=int(response_time_seconds) if response_time_seconds else None,
                    submitted_at=datetime.now(timezone.utc),
                    # Violation tracking
                    violation_profanity=violations.get('profanity', 0) if violations else 0,
                    violation_sexual=violations.get('sexual', 0) if violations else 0,
                    violation_political=violations.get('political', 0) if violations else 0,
                    violation_off_topic=violations.get('off_topic', 0) if violations else 0,
                    violation_total_score=violations.get('total', 0) if violations else 0,
                    violation_flags=violations.get('flags', {}) if violations else {}
                )
                
                db.add(response)
                db.commit()
                db.refresh(response)
                
                self.logger.info(f"Added response to question {question_id} in session {session_id}")
                return response
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to add response to session {session_id}: {e}")
            raise
    
    async def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get formatted conversation history for LLM processing.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation pairs with questions and responses
        """
        try:
            with get_db_session() as db:
                # First get the interview record to get its UUID
                interview = db.query(Interview).filter(
                    Interview.session_id == session_id
                ).first()
                
                if not interview:
                    return []
                
                # Get all questions for this interview
                questions = db.query(InterviewQuestion).filter(
                    InterviewQuestion.interview_id == interview.id
                ).order_by(InterviewQuestion.asked_at).all()
                
                conversation = []
                for question in questions:
                    # Get the response for this question
                    response = db.query(InterviewResponse).filter(
                        InterviewResponse.question_id == question.id
                    ).first()
                    
                    pair = {
                        "question": {
                            "id": str(question.id),
                            "text": question.question_text,
                            "type": question.question_type,
                            "difficulty": question.difficulty_level,
                            "focus_area": question.focus_area,
                            "number": question.question_number,
                            "asked_at": question.asked_at.isoformat(),
                        }
                    }
                    
                    if response:
                        pair["response"] = {
                            "id": str(response.id),
                            "text": response.response_text,
                            "response_time": response.response_time_seconds,
                            "responded_at": response.submitted_at.isoformat() if response.submitted_at else None,
                        }
                    
                    conversation.append(pair)
                
                return conversation
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get conversation history for session {session_id}: {e}")
            raise
    
    async def save_evaluation(
        self,
        session_id: str,
        overall_score: int,
        technical_knowledge: int,
        problem_solving: int,
        communication: int,
        experience_relevance: int,
        hire_recommendation: str,
        feedback: str,
        questions_answered: int,
        completion_rate: float,
        ai_provider: str,
        ai_model: str,
        strengths: Optional[List[str]] = None,
        areas_for_improvement: Optional[List[str]] = None,
        engagement_quality: Optional[str] = None,
        evaluation_context: Optional[Dict[str, Any]] = None,
        confidence_score: Optional[float] = None
    ) -> InterviewEvaluation:
        """
        Save comprehensive interview evaluation.
        
        Args:
            session_id: Session identifier
            overall_score: Overall interview score (0-100)
            technical_knowledge: Technical expertise score (0-25)
            problem_solving: Problem solving score (0-25)  
            communication: Communication skills score (0-25)
            experience_relevance: Experience relevance score (0-25)
            hire_recommendation: Hiring recommendation
            feedback: Comprehensive written feedback
            questions_answered: Number of questions answered
            completion_rate: Interview completion percentage
            ai_provider: AI provider used for evaluation
            ai_model: AI model used for evaluation
            strengths: List of candidate strengths
            areas_for_improvement: Areas needing development
            engagement_quality: Quality of engagement
            evaluation_context: Evaluation metadata
            confidence_score: AI confidence in evaluation
            
        Returns:
            InterviewEvaluation: Created evaluation record
        """
        try:
            with get_db_session() as db:
                # Get the interview record to get its UUID for the foreign key
                interview = db.query(Interview).filter(
                    Interview.session_id == session_id
                ).first()
                
                if not interview:
                    raise ValueError(f"Interview with session_id {session_id} not found")
                
                evaluation = InterviewEvaluation(
                    interview_id=interview.id,
                    overall_score=overall_score,
                    technical_knowledge=technical_knowledge,
                    problem_solving=problem_solving,
                    communication=communication,
                    experience_relevance=experience_relevance,
                    hire_recommendation=hire_recommendation,
                    feedback=feedback,
                    strengths=strengths,
                    areas_for_improvement=areas_for_improvement,
                    questions_answered=questions_answered,
                    completion_rate=completion_rate,
                    engagement_quality=engagement_quality,
                    ai_provider=ai_provider,
                    ai_model=ai_model,
                    evaluation_context=evaluation_context,
                    confidence_score=confidence_score,
                    evaluated_at=datetime.now(timezone.utc)
                )
                
                db.add(evaluation)
                db.commit()
                db.refresh(evaluation)
                
                self.logger.info(f"Saved evaluation for question {question_id} in session {session_id}")
                return evaluation
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to save evaluation for session {session_id}: {e}")
            raise
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for an interview session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session statistics
        """
        try:
            with get_db_session() as db:
                # Get basic session info
                interview = db.query(Interview).filter(
                    Interview.session_id == session_id
                ).first()
                
                if not interview:
                    return {}
                
                # Count questions and responses
                question_count = db.query(InterviewQuestion).filter(
                    InterviewQuestion.interview_id == interview.id
                ).count()
                
                response_count = db.query(InterviewResponse).filter(
                    InterviewResponse.interview_id == interview.id
                ).count()
                
                evaluation_count = db.query(InterviewEvaluation).filter(
                    InterviewEvaluation.interview_id == interview.id
                ).count()
                
                # Calculate average score if evaluations exist
                avg_score = None
                if evaluation_count > 0:
                    result = db.execute(text("""
                        SELECT AVG(overall_score) FROM interview_agent.interview_evaluations 
                        WHERE interview_id = :interview_id
                    """), {"interview_id": str(interview.id)})
                    avg_score = result.scalar()
                
                # Calculate session duration
                duration_minutes = None
                if interview.status == "COMPLETED":
                    duration = interview.updated_at - interview.created_at
                    duration_minutes = duration.total_seconds() / 60
                
                return {
                    "session_id": session_id,
                    "status": interview.status,
                    "created_at": interview.created_at.isoformat(),
                    "updated_at": interview.updated_at.isoformat(),
                    "question_count": question_count,
                    "response_count": response_count,
                    "evaluation_count": evaluation_count,
                    "average_score": round(avg_score, 2) if avg_score else None,
                    "duration_minutes": round(duration_minutes, 2) if duration_minutes else None,
                    "metadata": interview.session_metadata
                }
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get session statistics for {session_id}: {e}")
            raise

    async def get_interviews_by_job_id(self, job_id: str, status: str = None) -> List[Interview]:
        """
        Get all interviews for a specific job ID, optionally filtered by status.
        
        Args:
            job_id: Job identifier to filter by
            status: Optional status filter (e.g., "COMPLETED")
            
        Returns:
            List of Interview objects matching criteria
        """
        try:
            from sqlalchemy.orm import joinedload
            
            with get_db_session() as db:
                query = db.query(Interview).options(joinedload(Interview.evaluation)).filter(Interview.job_id == job_id)
                
                if status:
                    query = query.filter(Interview.status == status)
                
                interviews = query.all()
                
                self.logger.info(f"Found {len(interviews)} interviews for job_id={job_id}" + 
                               (f" with status={status}" if status else ""))
                
                return interviews
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get interviews for job_id {job_id}: {e}")
            raise

# Global storage service instance
storage_service = StorageService()