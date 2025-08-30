"""
Interview Agent SQLAlchemy Models

Contains all database table definitions and model relationships for the interview system.
Organized into logical entities: Interview, Question, Response, and Evaluation.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, Float, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base


# Enums for type safety and validation
class InterviewStatus(Enum):
    STARTED = "started"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class QuestionType(Enum):
    OPENER = "opener"
    TECHNICAL = "technical"
    EXPERIENCE = "experience"
    PROBLEM_SOLVING = "problem_solving"
    BEHAVIORAL = "behavioral"
    SCENARIO = "scenario"
    CLARIFICATION = "clarification"
    REQUIREMENT_SPECIFIC = "requirement_specific"


class CoverageStrategy(Enum):
    OPENING_ASSESSMENT = "opening_assessment"
    CORE_REQUIREMENT = "core_requirement"
    GAP_FILLING = "gap_filling"
    DEPTH_PROBE = "depth_probe"
    COMPREHENSIVE_COVERAGE = "comprehensive_coverage"


class DifficultyLevel(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class HireRecommendation(Enum):
    STRONG_YES = "strong_yes"
    YES = "yes"
    MAYBE = "maybe"
    NO = "no"
    STRONG_NO = "strong_no"


class Interview(Base):
    """
    Main Interview table - tracks interview sessions with timing and metadata.
    Central entity that coordinates questions, responses, and evaluations.
    """
    __tablename__ = "interviews"
    __table_args__ = {"schema": "interview_agent"}
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)  # External session identifier
    job_id = Column(String(50), nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    
    # Interview context
    role_description = Column(Text, nullable=False)
    resume_content = Column(Text, nullable=False)
    
    # Timing and duration
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)  # When interview auto-expires
    duration_minutes = Column(Integer, nullable=False, default=60)  # Planned duration
    
    # Status tracking
    status = Column(String(20), nullable=False, default="started")  # started, active, completed, expired, terminated
    completion_reason = Column(String(50), nullable=True)  # manual, timeout, completed, violation
    
    # Session metadata
    questions_asked = Column(Integer, nullable=False, default=0)
    current_question_id = Column(UUID(as_uuid=True), ForeignKey("interview_agent.interview_questions.id"), nullable=True)
    
    # Final scoring (populated after completion)
    final_score = Column(Integer, nullable=True)  # 0-100
    evaluation_completed = Column(Boolean, default=False)
    
    # Session metadata
    session_metadata = Column(JSONB, nullable=True, default=dict)  # Session-specific metadata
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = relationship("InterviewQuestion", back_populates="interview", 
                            foreign_keys="InterviewQuestion.interview_id",
                            cascade="all, delete-orphan", order_by="InterviewQuestion.question_number")
    responses = relationship("InterviewResponse", back_populates="interview", cascade="all, delete-orphan", order_by="InterviewResponse.created_at")
    evaluation = relationship("InterviewEvaluation", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    current_question = relationship("InterviewQuestion", foreign_keys=[current_question_id])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "job_id": self.job_id,
            "user_email": self.user_email,
            "role_description": self.role_description,
            "resume_content": self.resume_content,
            "started_at": self.started_at.isoformat() + "Z" if self.started_at else None,
            "ended_at": self.ended_at.isoformat() + "Z" if self.ended_at else None,
            "expires_at": self.expires_at.isoformat() + "Z" if self.expires_at else None,
            "duration_minutes": self.duration_minutes,
            "status": self.status,
            "completion_reason": self.completion_reason,
            "questions_asked": self.questions_asked,
            "current_question_id": str(self.current_question_id) if self.current_question_id else None,
            "final_score": self.final_score,
            "evaluation_completed": self.evaluation_completed,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }
    
    @property
    def is_expired(self) -> bool:
        """Check if interview has expired"""
        return datetime.utcnow() >= self.expires_at
    
    @property
    def time_remaining_seconds(self) -> int:
        """Calculate remaining time in seconds"""
        if self.status in ["completed", "expired", "terminated"]:
            return 0
        remaining = self.expires_at - datetime.utcnow()
        return max(0, int(remaining.total_seconds()))
    
    def get_conversation_pairs(self) -> List[Dict[str, Any]]:
        """Get all Q&A pairs in chronological order"""
        return [q.to_qa_pair() for q in sorted(self.questions, key=lambda x: x.question_number)]
    
    def get_conversation_for_llm(self) -> List[Dict[str, str]]:
        """Format conversation for LLM messages array"""
        messages = []
        for question in sorted(self.questions, key=lambda x: x.question_number):
            # Add question as assistant message
            messages.append({"role": "assistant", "content": question.question_text})
            # Add response as user message (if exists)
            if question.response:
                messages.append({"role": "user", "content": question.response.response_text})
        return messages
    
    @property
    def completion_stats(self) -> Dict[str, Any]:
        """Get completion statistics for this interview"""
        total_questions = len(self.questions)
        answered_questions = len([q for q in self.questions if q.has_response])
        completion_rate = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        return {
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "unanswered_questions": total_questions - answered_questions,
            "completion_rate": round(completion_rate, 2)
        }


class InterviewQuestion(Base):
    """
    Individual interview questions with metadata and strategic context.
    Each question is generated by the LLM with specific objectives and coverage areas.
    """
    __tablename__ = "interview_questions"
    __table_args__ = {"schema": "interview_agent"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interview_agent.interviews.id"), nullable=False)
    
    # Question content and metadata
    question_text = Column(Text, nullable=False)
    question_number = Column(Integer, nullable=False)  # Sequential order (1, 2, 3...)
    
    # Question categorization
    question_type = Column(String(30), nullable=False)  # opener, technical, experience, etc.
    focus_area = Column(String(255), nullable=False)    # Skill/competency being assessed
    difficulty_level = Column(String(20), nullable=False, default="intermediate")
    
    # Strategic context
    role_requirement_addressed = Column(Text, nullable=False)  # Which job requirement this assesses
    coverage_strategy = Column(String(30), nullable=False)     # opening_assessment, core_requirement, etc.
    expected_assessment = Column(Text, nullable=True)          # What the question aims to evaluate
    
    # LLM generation metadata
    ai_provider = Column(String(50), nullable=True)    # openai, claude, etc.
    ai_model = Column(String(100), nullable=True)      # gpt-4, claude-3, etc.
    generation_context = Column(JSONB, nullable=True)  # Full LLM generation metadata
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    asked_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    interview = relationship("Interview", back_populates="questions", 
                           foreign_keys=[interview_id])
    response = relationship("InterviewResponse", back_populates="question", uselist=False, cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "interview_id": str(self.interview_id),
            "question_text": self.question_text,
            "question_number": self.question_number,
            "question_type": self.question_type,
            "focus_area": self.focus_area,
            "difficulty_level": self.difficulty_level,
            "role_requirement_addressed": self.role_requirement_addressed,
            "coverage_strategy": self.coverage_strategy,
            "expected_assessment": self.expected_assessment,
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model,
            "generation_context": self.generation_context,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "asked_at": self.asked_at.isoformat() + "Z" if self.asked_at else None,
        }
    
    @property
    def has_response(self) -> bool:
        """Check if this question has been answered"""
        return self.response is not None
    
    def to_qa_pair(self) -> Dict[str, Any]:
        """Convert to question-answer pair format for LLM and UI"""
        pair = {
            "question_id": str(self.id),
            "question_number": self.question_number,
            "question": {
                "text": self.question_text,
                "type": self.question_type,
                "focus_area": self.focus_area,
                "difficulty": self.difficulty_level,
                "asked_at": self.asked_at.isoformat() + "Z" if self.asked_at else None,
            },
            "response": None
        }
        
        if self.response:
            pair["response"] = {
                "text": self.response.response_text,
                "submitted_at": self.response.submitted_at.isoformat() + "Z" if self.response.submitted_at else None,
                "response_time_seconds": self.response.response_time_seconds,
                "word_count": self.response.response_length_words,
            }
        
        return pair


class InterviewResponse(Base):
    """
    User responses to interview questions with timing and context.
    Stores the candidate's answers with metadata for evaluation.
    """
    __tablename__ = "interview_responses"
    __table_args__ = {"schema": "interview_agent"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interview_agent.interviews.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("interview_agent.interview_questions.id"), nullable=False, unique=True)
    
    # Response content
    response_text = Column(Text, nullable=False)
    
    # Response metadata
    response_length_words = Column(Integer, nullable=True)      # Word count analysis
    response_time_seconds = Column(Integer, nullable=True)      # Time taken to respond
    input_method = Column(String(20), nullable=True)           # text, voice, mixed
    
    # Quality indicators (can be populated by evaluation)
    relevance_score = Column(Float, nullable=True)             # How relevant to the question
    completeness_score = Column(Float, nullable=True)          # How complete the answer is
    technical_accuracy = Column(Float, nullable=True)          # Technical correctness (if applicable)
    
    # Behavioral violation tracking
    violation_profanity = Column(Integer, nullable=False, default=0)    # Profanity/offensive language
    violation_sexual = Column(Integer, nullable=False, default=0)       # Sexual/inappropriate content
    violation_political = Column(Integer, nullable=False, default=0)    # Political discussions
    violation_off_topic = Column(Integer, nullable=False, default=0)    # Off-topic/unrelated content
    violation_total_score = Column(Integer, nullable=False, default=0)  # Sum of all violations
    violation_flags = Column(JSONB, nullable=True, default=dict)        # Detailed violation metadata
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    interview = relationship("Interview", back_populates="responses")
    question = relationship("InterviewQuestion", back_populates="response")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "interview_id": str(self.interview_id),
            "question_id": str(self.question_id),
            "response_text": self.response_text,
            "response_length_words": self.response_length_words,
            "response_time_seconds": self.response_time_seconds,
            "input_method": self.input_method,
            "relevance_score": self.relevance_score,
            "completeness_score": self.completeness_score,
            "technical_accuracy": self.technical_accuracy,
            "violation_profanity": self.violation_profanity,
            "violation_sexual": self.violation_sexual,
            "violation_political": self.violation_political,
            "violation_off_topic": self.violation_off_topic,
            "violation_total_score": self.violation_total_score,
            "violation_flags": self.violation_flags or {},
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "submitted_at": self.submitted_at.isoformat() + "Z" if self.submitted_at else None,
        }


class InterviewEvaluation(Base):
    """
    Final interview evaluation and scoring with detailed feedback.
    Generated by LLM after interview completion with comprehensive assessment.
    """
    __tablename__ = "interview_evaluations"
    __table_args__ = {"schema": "interview_agent"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interview_agent.interviews.id"), nullable=False, unique=True)
    
    # Overall scoring (0-100 scale)
    overall_score = Column(Integer, nullable=False)                    # Primary score
    technical_knowledge = Column(Integer, nullable=False)              # 0-25 Technical expertise
    problem_solving = Column(Integer, nullable=False)                  # 0-25 Analytical thinking
    communication = Column(Integer, nullable=False)                    # 0-25 Communication skills
    experience_relevance = Column(Integer, nullable=False)             # 0-25 Experience fit
    
    # Hiring recommendation
    hire_recommendation = Column(String(20), nullable=False)           # strong_yes, yes, maybe, no, strong_no
    
    # Detailed feedback
    feedback = Column(Text, nullable=False)                           # Comprehensive written feedback
    strengths = Column(ARRAY(String), nullable=True)                 # List of candidate strengths
    areas_for_improvement = Column(ARRAY(String), nullable=True)     # Areas needing development
    
    # Interview completion analysis
    questions_answered = Column(Integer, nullable=False)              # How many questions were answered
    completion_rate = Column(Float, nullable=False)                   # Percentage of interview completed
    engagement_quality = Column(String(20), nullable=True)           # excellent, good, average, poor
    
    # AI evaluation metadata
    ai_provider = Column(String(50), nullable=False)                 # openai, claude, etc.
    ai_model = Column(String(100), nullable=False)                   # gpt-4, claude-3, etc.
    evaluation_context = Column(JSONB, nullable=True)               # Full evaluation metadata
    confidence_score = Column(Float, nullable=True)                  # LLM confidence in evaluation
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    evaluated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    interview = relationship("Interview", back_populates="evaluation")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "interview_id": str(self.interview_id),
            "overall_score": self.overall_score,
            "technical_knowledge": self.technical_knowledge,
            "problem_solving": self.problem_solving,
            "communication": self.communication,
            "experience_relevance": self.experience_relevance,
            "hire_recommendation": self.hire_recommendation,
            "feedback": self.feedback,
            "strengths": self.strengths or [],
            "areas_for_improvement": self.areas_for_improvement or [],
            "questions_answered": self.questions_answered,
            "completion_rate": self.completion_rate,
            "engagement_quality": self.engagement_quality,
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model,
            "evaluation_context": self.evaluation_context,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "evaluated_at": self.evaluated_at.isoformat() + "Z" if self.evaluated_at else None,
        }