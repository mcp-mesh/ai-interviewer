"""
Session Manager - Interview Session Lifecycle Management

Handles interview session creation, state management, and coordination
between different interview phases with proper error handling.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from ..services.storage_service import storage_service

logger = logging.getLogger(__name__)

class SessionStatus(Enum):
    """Interview session status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed" 
    ABANDONED = "abandoned"
    ERROR = "error"

class SessionPhase(Enum):
    """Interview session phases."""
    INITIALIZATION = "initialization"
    QUESTIONING = "questioning"
    EVALUATION = "evaluation"
    COMPLETION = "completion"

class SessionManager:
    """
    Manages interview session lifecycle, state transitions, and coordination.
    """
    
    def __init__(self):
        """Initialize session manager."""
        self.logger = logging.getLogger(__name__)
    
    async def create_session(
        self,
        job_id: str,
        user_email: str,
        application_id: str,
        job_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Create a new interview session with all required context.
        
        Args:
            job_id: Job posting identifier
            user_email: User's email address
            application_id: Application identifier
            job_data: Complete job posting details
            resume_data: User's resume information
            session_id: Optional custom session ID
            
        Returns:
            Tuple of (session_id, session_context)
            
        Raises:
            Exception: Session creation failed
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Prepare session metadata
            metadata = {
                "phase": SessionPhase.INITIALIZATION.value,
                "question_count": 0,
                "response_count": 0,
                "start_time": datetime.now(timezone.utc).isoformat(),
                "job_title": job_data.get("title", "Unknown"),
                "difficulty_level": self._determine_difficulty_level(job_data, resume_data)
            }
            
            # Create session in database
            interview = await storage_service.create_interview_session(
                session_id=session_id,
                job_id=job_id,
                user_email=user_email,
                application_id=application_id,
                job_data=job_data,
                resume_data=resume_data,
                metadata=metadata
            )
            
            # Prepare session context for interview flow
            session_context = {
                "session_id": session_id,
                "job_id": job_id,
                "user_email": user_email,
                "application_id": application_id,
                "status": SessionStatus.ACTIVE.value,
                "phase": SessionPhase.INITIALIZATION.value,
                "job_data": job_data,
                "resume_data": resume_data,
                "metadata": metadata,
                "created_at": interview.created_at.isoformat()
            }
            
            self.logger.info(f"Created interview session {session_id} for user {user_email}")
            return session_id, session_context
            
        except Exception as e:
            self.logger.error(f"Failed to create interview session: {e}")
            raise Exception(f"Session creation failed: {str(e)}")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get existing interview session with full context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session context dictionary or None if not found
        """
        try:
            interview = await storage_service.get_interview_by_session_id(session_id)
            
            if not interview:
                self.logger.warning(f"Session not found: {session_id}")
                return None
            
            # Build complete session context
            metadata = interview.session_metadata or {}
            session_context = {
                "session_id": session_id,
                "job_id": interview.job_id,
                "user_email": interview.user_email,
                "application_id": metadata.get("application_id"),
                "status": interview.status,
                "phase": metadata.get("phase", SessionPhase.QUESTIONING.value),
                "job_data": metadata.get("job_data", {}),
                "resume_data": metadata.get("resume_data", {}),
                "metadata": metadata,
                "created_at": interview.created_at.isoformat(),
                "updated_at": interview.updated_at.isoformat()
            }
            
            # Get conversation history
            conversation = await storage_service.get_conversation_history(session_id)
            session_context["conversation"] = conversation
            
            # Get session statistics
            stats = await storage_service.get_session_statistics(session_id)
            session_context["statistics"] = stats
            
            return session_context
            
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {e}")
            raise
    
    async def update_session_phase(
        self,
        session_id: str,
        new_phase: SessionPhase,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update session phase and related metadata.
        
        Args:
            session_id: Session identifier
            new_phase: New session phase
            additional_metadata: Additional metadata to merge
            
        Returns:
            bool: Success status
        """
        try:
            metadata_updates = {
                "phase": new_phase.value,
                "phase_updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if additional_metadata:
                metadata_updates.update(additional_metadata)
            
            success = await storage_service.update_interview_status(
                session_id=session_id,
                status=SessionStatus.ACTIVE.value,  # Keep active during phase transitions
                metadata_updates=metadata_updates
            )
            
            if success:
                self.logger.info(f"Updated session {session_id} to phase {new_phase.value}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update session phase {session_id}: {e}")
            raise
    
    async def complete_session(
        self,
        session_id: str,
        final_evaluation: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Mark session as completed with final evaluation.
        
        Args:
            session_id: Session identifier
            final_evaluation: Final interview evaluation data
            
        Returns:
            bool: Success status
        """
        try:
            metadata_updates = {
                "phase": SessionPhase.COMPLETION.value,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
            
            if final_evaluation:
                metadata_updates["final_evaluation"] = final_evaluation
            
            success = await storage_service.update_interview_status(
                session_id=session_id,
                status=SessionStatus.COMPLETED.value,
                metadata_updates=metadata_updates
            )
            
            if success:
                self.logger.info(f"Completed interview session {session_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to complete session {session_id}: {e}")
            raise
    
    async def abandon_session(
        self,
        session_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Mark session as abandoned.
        
        Args:
            session_id: Session identifier
            reason: Optional reason for abandonment
            
        Returns:
            bool: Success status
        """
        try:
            metadata_updates = {
                "phase": SessionPhase.COMPLETION.value,
                "abandoned_at": datetime.now(timezone.utc).isoformat()
            }
            
            if reason:
                metadata_updates["abandonment_reason"] = reason
            
            success = await storage_service.update_interview_status(
                session_id=session_id,
                status=SessionStatus.ABANDONED.value,
                metadata_updates=metadata_updates
            )
            
            if success:
                self.logger.info(f"Abandoned interview session {session_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to abandon session {session_id}: {e}")
            raise
    
    async def handle_session_error(
        self,
        session_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Handle session error and update status.
        
        Args:
            session_id: Session identifier
            error_message: Error description
            error_details: Additional error information
            
        Returns:
            bool: Success status
        """
        try:
            metadata_updates = {
                "error_occurred_at": datetime.now(timezone.utc).isoformat(),
                "error_message": error_message
            }
            
            if error_details:
                metadata_updates["error_details"] = error_details
            
            success = await storage_service.update_interview_status(
                session_id=session_id,
                status=SessionStatus.ERROR.value,
                metadata_updates=metadata_updates
            )
            
            if success:
                self.logger.error(f"Recorded error for session {session_id}: {error_message}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to handle session error {session_id}: {e}")
            raise
    
    async def get_active_sessions(self, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all active sessions, optionally filtered by user.
        
        Args:
            user_email: Optional user email filter
            
        Returns:
            List of active session contexts
        """
        try:
            # This would require a new storage method to query active sessions
            # For now, return empty list as placeholder
            self.logger.info(f"Querying active sessions for user: {user_email or 'all'}")
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get active sessions: {e}")
            raise
    
    def _determine_difficulty_level(
        self,
        job_data: Dict[str, Any],
        resume_data: Dict[str, Any]
    ) -> str:
        """
        Determine interview difficulty level based on job and candidate data.
        
        Args:
            job_data: Job posting information
            resume_data: Candidate resume information
            
        Returns:
            Difficulty level (junior, mid, senior, expert)
        """
        try:
            # Simple heuristic based on job title and requirements
            job_title = job_data.get("title", "").lower()
            job_description = job_data.get("description", "").lower()
            
            # Check for senior/lead indicators
            if any(keyword in job_title for keyword in ["senior", "lead", "principal", "architect", "staff"]):
                return "senior"
            
            # Check for mid-level indicators
            if any(keyword in job_title for keyword in ["mid", "intermediate", "developer ii", "engineer ii"]):
                return "mid"
            
            # Check for junior indicators
            if any(keyword in job_title for keyword in ["junior", "entry", "associate", "graduate", "intern"]):
                return "junior"
            
            # Check years of experience in job description
            if "5+" in job_description or "5 years" in job_description:
                return "senior"
            elif "3+" in job_description or "3 years" in job_description:
                return "mid"
            
            # Default to mid-level
            return "mid"
            
        except Exception:
            # Safe fallback
            return "mid"

# Global session manager instance
session_manager = SessionManager()