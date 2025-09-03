"""
Interview Agent Database Package

Provides a clean, organized interface to all database functionality for the interview system.
Exports models, operations, caching, and connection utilities in a structured way.

Usage:
    from .database import (
        # Models
        Interview, InterviewQuestion, InterviewResponse, InterviewEvaluation,
        
        # Database operations
        create_tables, get_db_session,
        get_interview_by_session_id, create_interview_session,
        add_interview_question, add_interview_response,
        get_interview_conversation_pairs, format_conversation_for_llm,
        
        # Caching
        InterviewCache, QuestionCache, EvaluationCache,
        
        # Testing
        test_connections
    )
"""

# Import base classes
from .base import Base

# Import all models
from .models import (
    Interview,
    InterviewQuestion, 
    InterviewResponse,
    InterviewEvaluation,
    # Enums
    InterviewStatus,
    QuestionType,
    CoverageStrategy,
    DifficultyLevel,
    HireRecommendation
)

# Import database configuration and setup
from .database import (
    create_tables,
    get_db_session,
    test_postgres_connection
)

# Import caching functionality  
from .cache import (
    InterviewCache,
    QuestionCache,
    EvaluationCache,
    test_redis_connection
)

# Import database operations
from .operations import (
    # Interview management
    get_interview_by_session_id,
    get_interview_by_id,
    get_active_interviews_by_user,
    create_interview_session,
    update_interview_status,
    
    # Question management
    add_interview_question,
    get_interview_questions,
    get_unanswered_questions,
    
    # Response management
    add_interview_response,
    get_interview_responses,
    
    # Conversation management
    get_interview_conversation_pairs,
    format_conversation_for_llm,
    
    # Statistics and analytics
    get_interview_statistics,
    get_user_interview_history,
    
    # Evaluation management
    create_interview_evaluation,
    get_interview_evaluation,
    
    # Utility functions
    cleanup_expired_interviews,
    get_active_interview_count
)

# Convenience function for testing all connections
def test_connections() -> dict:
    """Test both PostgreSQL and Redis connections"""
    return {
        "postgres": test_postgres_connection(),
        "redis": test_redis_connection()
    }

# Export everything for easy importing
__all__ = [
    # Base classes
    "Base",
    # Models
    "Interview",
    "InterviewQuestion", 
    "InterviewResponse",
    "InterviewEvaluation",
    # Enums
    "InterviewStatus",
    "QuestionType", 
    "CoverageStrategy",
    "DifficultyLevel",
    "HireRecommendation",
    # Database setup
    "create_tables",
    "get_db_session",
    "test_connections",
    # Caching
    "InterviewCache",
    "QuestionCache", 
    "EvaluationCache",
    # Operations
    "get_interview_by_session_id",
    "get_interview_by_id",
    "get_active_interviews_by_user", 
    "create_interview_session",
    "update_interview_status",
    "add_interview_question",
    "get_interview_questions",
    "get_unanswered_questions",
    "add_interview_response", 
    "get_interview_responses",
    "get_interview_conversation_pairs",
    "format_conversation_for_llm",
    "get_interview_statistics",
    "get_user_interview_history",
    "create_interview_evaluation",
    "get_interview_evaluation",
    "cleanup_expired_interviews",
    "get_active_interview_count"
]