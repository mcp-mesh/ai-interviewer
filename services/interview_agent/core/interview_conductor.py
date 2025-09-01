"""
Interview Conductor - Main Interview Orchestration

Handles the complete interview flow including session management, question generation,
response collection, and evaluation with proper error handling and state management.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from mesh.types import McpMeshAgent

# Import time threshold configuration
from ..main import TIME_THRESHOLD_PERCENTAGE, VIOLATION_THRESHOLD

from .session_manager import session_manager, SessionPhase, SessionStatus
from .question_generator import question_generator
from .turn_manager import turn_manager
from .violation_detector import violation_detector
from ..services.storage_service import storage_service
from ..services.dependency_service import dependency_service
from ..database import get_db_session, Interview

logger = logging.getLogger(__name__)

class InterviewConductor:
    """
    Main orchestrator for interview sessions handling the complete interview lifecycle.
    """
    
    def __init__(self):
        """Initialize interview conductor."""
        self.logger = logging.getLogger(__name__)
    
    async def conduct_interview(
        self,
        session_id: Optional[str] = None,
        job_id: Optional[str] = None,
        user_email: Optional[str] = None,
        application_id: Optional[str] = None,
        user_input: Optional[str] = None,
        user_action: Optional[str] = None,
        dependencies: Optional[Dict[str, McpMeshAgent]] = None
    ) -> Dict[str, Any]:
        """
        Main interview orchestration function handling both start and continue scenarios.
        
        Args:
            session_id: Existing session ID (for continue) or None (for start)
            job_id: Job posting identifier (required for start)
            user_email: User's email address (required for start) 
            application_id: Application identifier (required for start)
            user_input: User's response to current question
            user_action: User action (answer, skip, end)
            dependencies: MCP Mesh injected dependencies
            
        Returns:
            Interview response with question, status, and metadata
            
        Raises:
            Exception: Interview operation failed
        """
        try:
            # Register dependencies for cross-agent communication
            if dependencies:
                dependency_service.register_dependencies(dependencies)
            
            # Validate dependencies are available
            validation_results = await dependency_service.validate_dependencies()
            missing_deps = [cap for cap, available in validation_results.items() if not available]
            
            if missing_deps:
                raise Exception(f"Missing required dependencies: {missing_deps}")
            
            # Get LLM service
            llm_service = dependencies.get("process_with_tools") if dependencies else None
            if not llm_service:
                raise Exception("LLM service (process_with_tools) not available")
            
            # Determine operation type: start new or continue existing
            if session_id:
                return await self._continue_interview_session(
                    session_id=session_id,
                    user_input=user_input,
                    user_action=user_action,
                    llm_service=llm_service
                )
            else:
                return await self._start_new_interview(
                    job_id=job_id,
                    user_email=user_email,
                    application_id=application_id,
                    llm_service=llm_service
                )
                
        except Exception as e:
            self.logger.error(f"Interview operation failed: {e}")
            
            # If we have a session_id, record the error
            if session_id:
                try:
                    await session_manager.handle_session_error(
                        session_id=session_id,
                        error_message=str(e),
                        error_details={"operation": "conduct_interview"}
                    )
                except Exception:
                    pass  # Don't fail on error recording failure
            
            raise Exception(f"Interview operation failed: {str(e)}")
    
    async def _start_new_interview(
        self,
        job_id: str,
        user_email: str,
        application_id: str,
        llm_service: McpMeshAgent
    ) -> Dict[str, Any]:
        """
        Start a new interview session.
        
        Args:
            job_id: Job posting identifier
            user_email: User's email address
            application_id: Application identifier
            llm_service: LLM service for question generation
            
        Returns:
            New interview session response
        """
        try:
            self.logger.info(f"Starting interview for user {user_email}, job {job_id}")
            
            # First, check if there's already an active interview session for this user and job
            existing_session = await self._find_existing_session(user_email, job_id)
            self.logger.info(f"_find_existing_session returned: {existing_session}")
            if existing_session:
                self.logger.info(f"Found existing session {existing_session['session_id']} for user {user_email}, job {job_id}")
                return await self._return_existing_session_with_history(existing_session['session_id'])
            
            self.logger.info(f"No existing session found, creating new interview for user {user_email}, job {job_id}")
            
            # Get job details from job agent
            job_data = await dependency_service.get_job_details(job_id)
            if not job_data:
                raise Exception(f"Job {job_id} not found")
            
            # Get user applications to find resume data
            user_applications = await dependency_service.get_user_applications(user_email)
            
            # Find the specific application by job_id since application_id isn't in the response
            target_application = None
            for app in user_applications:
                if app.get("jobId") == job_id:
                    target_application = app
                    break
            
            if not target_application:
                raise Exception(f"Application for job {job_id} not found for user {user_email}")
            
            # For now, create basic resume data from what we can infer
            # TODO: In the future, we could add a dependency to get detailed resume data
            resume_data = {
                "skills": [],  # Could be enhanced with actual resume data
                "experience": [],
                "education": [],
                "status": target_application.get("status", "UNKNOWN")
            }
            
            # Create new interview session
            session_id, session_context = await session_manager.create_session(
                job_id=job_id,
                user_email=user_email,
                application_id=application_id,
                job_data=job_data,
                resume_data=resume_data
            )
            
            # Update application status to INPROGRESS
            try:
                await dependency_service.update_application_status(
                    application_id=application_id,
                    new_status="INPROGRESS"
                )
                self.logger.info(f"Updated application {application_id} status to INPROGRESS")
            except Exception as e:
                self.logger.warning(f"Failed to update application status: {e}")
                # Don't fail the interview start for status update failure
            
            # Move to questioning phase
            await session_manager.update_session_phase(
                session_id=session_id,
                new_phase=SessionPhase.QUESTIONING
            )
            
            # Generate first interview question
            difficulty_level = session_context["metadata"].get("difficulty_level", "mid")
            
            first_question = await question_generator.generate_interview_question(
                job_data=job_data,
                resume_data=resume_data,
                conversation_history=[],
                llm_service=llm_service,
                difficulty_level=difficulty_level,
                question_type="technical"
            )
            
            # Store question in database
            question_record = await storage_service.add_question(
                session_id=session_id,
                question_text=first_question["question_text"],
                question_type=first_question["question_type"],
                difficulty=first_question["difficulty"],
                metadata=first_question.get("metadata", {})
            )
            
            # Get the interview record to access time_remaining_seconds
            interview = await storage_service.get_interview_by_session_id(session_id)
            
            # Build response
            response = {
                "session_id": session_id,
                "status": "active",
                "phase": "questioning",
                "question": {
                    "id": question_record.id,
                    "text": first_question["question_text"],
                    "type": first_question["question_type"],
                    "difficulty": first_question["difficulty"],
                    "focus_area": first_question.get("focus_area"),
                    "number": 1
                },
                "interview_context": {
                    "job_title": job_data.get("title"),
                    "company_name": job_data.get("company_name", "Company"),
                    "session_started": session_context["created_at"],
                    "difficulty_level": difficulty_level
                },
                "metadata": {
                    "total_questions": 1,
                    "questions_answered": 0,
                    "session_created": session_context["created_at"],
                    "time_remaining_seconds": interview.time_remaining_seconds if interview else 0,
                    "full_conversation": [{"role": "assistant", "content": first_question["question_text"]}],
                    "conversation_state": {
                        "whose_turn": "user",
                        "action": "wait_for_response",
                        "strip_last_message": False,
                        "reason": "First question asked - waiting for user response"
                    }
                }
            }
            
            self.logger.info(f"Started new interview session {session_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to start new interview: {e}")
            raise Exception(f"Failed to start interview: {str(e)}")
    
    async def _continue_interview_session(
        self,
        session_id: str,
        user_input: Optional[str],
        user_action: Optional[str],
        llm_service: McpMeshAgent
    ) -> Dict[str, Any]:
        """
        Continue an existing interview session.
        
        Args:
            session_id: Session identifier
            user_input: User's response to current question
            user_action: User action (answer, skip, end)
            llm_service: LLM service for operations
            
        Returns:
            Interview continuation response
        """
        try:
            self.logger.info(f"Continuing interview session {session_id}")
            
            # Get existing session
            session_context = await session_manager.get_session(session_id)
            if not session_context:
                raise Exception(f"Interview session {session_id} not found")
            
            # Check if session has expired
            from datetime import datetime, timezone
            interview = await storage_service.get_interview_by_session_id(session_id)
            if interview:
                current_time = datetime.utcnow()  # Use naive UTC datetime to match database
                if current_time > interview.expires_at:
                    # Session has expired - mark it as expired and return error
                    await storage_service.update_interview_status(
                        session_id=session_id,
                        status="expired",
                        metadata_updates={"expired_at": current_time.isoformat()}
                    )
                    
                    # Update application status to COMPLETED
                    try:
                        metadata = interview.session_metadata or {}
                        application_id = metadata.get("application_id")
                        if application_id:
                            await dependency_service.update_application_status(
                                application_id=application_id,
                                new_status="COMPLETED"
                            )
                    except Exception as e:
                        self.logger.warning(f"Failed to update application status for expired session: {e}")
                    
                    # Calculate how long ago it expired
                    expired_duration = current_time - interview.expires_at
                    expired_minutes = int(expired_duration.total_seconds() / 60)
                    
                    raise Exception(f"Interview session has ended due to timeout. The session expired {expired_minutes} minutes ago.")
            
            if session_context["status"] != "INPROGRESS":
                raise Exception(f"Interview session {session_id} is not active (status: {session_context['status']})")
            
            # Handle user actions
            if user_action == "end":
                return await self._end_interview_session(session_id, session_context, llm_service)
            
            # Get full conversation history from database through storage service
            with get_db_session() as db:
                interview_with_relations = db.query(Interview).filter(
                    Interview.session_id == session_id
                ).first()
                full_conversation = interview_with_relations.get_conversation_for_llm() if interview_with_relations else []
            
            # Analyze conversation state and determine turn
            conversation_state = turn_manager.analyze_conversation_state(
                conversation_history=full_conversation,
                has_user_input=bool(user_input and user_input.strip())
            )
            
            self.logger.info(f"Conversation state: {conversation_state['reason']}")
            
            # Process user input based on turn analysis
            if user_input and user_input.strip():
                if turn_manager.should_save_user_input(full_conversation, user_input):
                    # Save user response to database
                    await self._process_user_response_with_turn_management(session_id, user_input, full_conversation)
                    # Refresh conversation history after saving
                    with get_db_session() as db:
                        interview_with_relations = db.query(Interview).filter(
                            Interview.session_id == session_id
                        ).first()
                        full_conversation = interview_with_relations.get_conversation_for_llm() if interview_with_relations else []
                    
                    # VIOLATION THRESHOLD CHECK: Check if violations exceed threshold
                    total_violations = await self._get_total_violations_for_session(session_id)
                    should_terminate, termination_reason = violation_detector.is_termination_required(
                        total_violations, VIOLATION_THRESHOLD
                    )
                    
                    if should_terminate:
                        self.logger.warning(f"Auto-terminating interview due to violations: {termination_reason}")
                        return await self._terminate_interview_for_violations(
                            session_id=session_id,
                            session_context=session_context,
                            termination_reason=termination_reason,
                            total_violations=total_violations,
                            llm_service=llm_service
                        )
                    
                    # CLOSING QUESTION FIREWALL: Check if last question was closing message
                    if len(full_conversation) >= 2:
                        last_assistant_msg = None
                        # Find the last assistant message
                        for msg in reversed(full_conversation):
                            if msg["role"] == "assistant":
                                last_assistant_msg = msg
                                break
                        
                        # Check if last assistant message was a closing question
                        if last_assistant_msg and self._is_closing_question(last_assistant_msg["content"]):
                            self.logger.info(f"Closing question detected - ending interview session {session_id}")
                            # User responded to closing question - complete the interview
                            return await self._complete_interview_after_closing_question(
                                session_id=session_id,
                                session_context=session_context,
                                user_question=user_input,
                                llm_service=llm_service
                            )
                else:
                    self.logger.info(f"Stripping duplicate user message: {user_input[:50]}...")
            
            # Check conversation statistics for metadata
            questions_asked = len([msg for msg in full_conversation if msg["role"] == "assistant"])
            responses_given = len([msg for msg in full_conversation if msg["role"] == "user"])
            
            # Interview should only end due to timeout (already checked above) or explicit user action
            # No question limits - interview continues until duration expires
            
            # Check if we're in the final time threshold - if so, provide closing message
            if interview:
                time_remaining = interview.time_remaining_seconds
                total_duration_seconds = interview.duration_minutes * 60
                time_threshold_seconds = (TIME_THRESHOLD_PERCENTAGE / 100) * total_duration_seconds
                
                if time_remaining <= time_threshold_seconds:
                    # Return standard closing message instead of generating new question
                    next_question = await self._generate_closing_question(
                        session_id=session_id,
                        time_remaining=time_remaining,
                        total_duration_minutes=interview.duration_minutes
                    )
                else:
                    # Generate next question with full conversation history
                    next_question = await self._generate_next_question_with_history(
                        session_context=session_context,
                        conversation_history=full_conversation,
                        llm_service=llm_service
                    )
            else:
                # Fallback: Generate regular question if interview not found
                next_question = await self._generate_next_question_with_history(
                    session_context=session_context,
                    conversation_history=full_conversation,
                    llm_service=llm_service
                )
            
            # Get the interview record to access time_remaining_seconds
            interview = await storage_service.get_interview_by_session_id(session_id)
            
            # Build continuation response
            response = {
                "session_id": session_id,
                "status": "active", 
                "phase": session_context["phase"],
                "question": next_question,
                "interview_context": {
                    "job_title": session_context["job_data"].get("title"),
                    "company_name": session_context["job_data"].get("company_name", "Company"),
                    "session_started": session_context["created_at"]
                },
                "metadata": {
                    "total_questions": questions_asked + 1,
                    "questions_answered": responses_given,
                    "conversation_length": len(full_conversation),
                    "time_remaining_seconds": interview.time_remaining_seconds if interview else 0,
                    "full_conversation": full_conversation,
                    "conversation_state": conversation_state
                }
            }
            
            self.logger.info(f"Continued interview session {session_id} - Question #{questions_asked + 1}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to continue interview session {session_id}: {e}")
            raise Exception(f"Failed to continue interview: {str(e)}")
    
    async def _process_user_response(
        self,
        session_id: str,
        session_context: Dict[str, Any],
        user_input: str
    ) -> None:
        """
        Process and store user's response to the current question.
        
        Args:
            session_id: Session identifier
            session_context: Current session context
            user_input: User's response text
        """
        try:
            # Get the most recent unanswered question
            conversation = session_context.get("conversation", [])
            
            # Find the last question without a response
            current_question = None
            for pair in reversed(conversation):
                if "question" in pair and "response" not in pair:
                    current_question = pair["question"]
                    break
            
            if not current_question:
                self.logger.warning(f"No current question found for session {session_id}")
                return
            
            # Store response in database
            response_record = await storage_service.add_response(
                session_id=session_id,
                question_id=current_question["id"],
                response_text=user_input,
                response_time_seconds=None,  # Could calculate if we tracked ask time
                metadata={"processed_at": datetime.now(timezone.utc).isoformat()}
            )
            
            self.logger.info(f"Stored response to question {current_question['id']} in session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to process user response for session {session_id}: {e}")
            raise
    
    async def _generate_next_question(
        self,
        session_context: Dict[str, Any],
        llm_service: McpMeshAgent
    ) -> Dict[str, Any]:
        """
        Generate the next interview question based on session context.
        
        Args:
            session_context: Current session context
            llm_service: LLM service for question generation
            
        Returns:
            Next question dictionary
        """
        try:
            session_id = session_context["session_id"]
            job_data = session_context["job_data"]
            resume_data = session_context["resume_data"]
            conversation_history = session_context.get("conversation", [])
            difficulty_level = session_context["metadata"].get("difficulty_level", "mid")
            
            # Generate question using question generator
            question_data = await question_generator.generate_interview_question(
                job_data=job_data,
                resume_data=resume_data,
                conversation_history=conversation_history,
                llm_service=llm_service,
                difficulty_level=difficulty_level,
                question_type="technical"
            )
            
            # Store question in database
            question_record = await storage_service.add_question(
                session_id=session_id,
                question_text=question_data["question_text"],
                question_type=question_data["question_type"],
                difficulty=question_data["difficulty"],
                metadata=question_data.get("metadata", {})
            )
            
            # Format question response
            question_response = {
                "id": question_record.id,
                "text": question_data["question_text"],
                "type": question_data["question_type"],
                "difficulty": question_data["difficulty"],
                "focus_area": question_data.get("focus_area"),
                "number": len(conversation_history) + 1
            }
            
            return question_response
            
        except Exception as e:
            self.logger.error(f"Failed to generate next question: {e}")
            raise
    
    async def _process_user_response_with_turn_management(
        self,
        session_id: str,
        user_input: str,
        conversation_history: List[Dict[str, str]]
    ) -> None:
        """
        Process and store user's response with turn management.
        
        Args:
            session_id: Session identifier
            user_input: User's response text
            conversation_history: Full conversation history from database
        """
        try:
            # Find the most recent assistant question that needs a response
            current_question_id = None
            
            # Get interview record with questions in a database session
            with get_db_session() as db:
                interview = db.query(Interview).filter(
                    Interview.session_id == session_id
                ).first()
                
                if not interview:
                    raise Exception(f"Interview not found for session {session_id}")
                
                # Find the latest question without a response
                for question in reversed(interview.questions):
                    if not question.has_response:
                        current_question_id = question.id
                        break
            
            if not current_question_id:
                self.logger.warning(f"No unanswered question found for session {session_id}")
                return
            
            # VIOLATION DETECTION: Analyze user input for behavioral violations
            violations = violation_detector.detect_violations(
                text=user_input,
                job_description=interview.role_description if interview else ""
            )
            
            # Store response in database with violation data
            response_record = await storage_service.add_response(
                session_id=session_id,
                question_id=current_question_id,
                response_text=user_input,
                response_time_seconds=None,
                metadata={
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "turn_managed": True,
                    "violation_analysis": violations.get('analysis', {})
                },
                violations=violations
            )
            
            self.logger.info(f"Stored user response to question {current_question_id} in session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to process user response with turn management for session {session_id}: {e}")
            raise
    
    async def _generate_next_question_with_history(
        self,
        session_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        llm_service: McpMeshAgent
    ) -> Dict[str, Any]:
        """
        Generate the next interview question using full conversation history.
        
        Args:
            session_context: Current session context
            conversation_history: Full conversation history from database
            llm_service: LLM service for question generation
            
        Returns:
            Next question dictionary
        """
        try:
            session_id = session_context["session_id"]
            job_data = session_context["job_data"]
            resume_data = session_context["resume_data"]
            difficulty_level = session_context["metadata"].get("difficulty_level", "mid")
            
            self.logger.info(f"Generating question with full conversation history ({len(conversation_history)} messages)")
            
            # Generate question using question generator with full history
            question_data = await question_generator.generate_interview_question(
                job_data=job_data,
                resume_data=resume_data,
                conversation_history=conversation_history,  # Use full database history
                llm_service=llm_service,
                difficulty_level=difficulty_level,
                question_type="technical"
            )
            
            # Store question in database
            question_record = await storage_service.add_question(
                session_id=session_id,
                question_text=question_data["question_text"],
                question_type=question_data["question_type"],
                difficulty=question_data["difficulty"],
                metadata={
                    **question_data.get("metadata", {}),
                    "generated_with_full_history": True,
                    "history_length": len(conversation_history)
                }
            )
            
            # Format question response
            question_response = {
                "id": question_record.id,
                "text": question_data["question_text"],
                "type": question_data["question_type"],
                "difficulty": question_data["difficulty"],
                "focus_area": question_data.get("focus_area"),
                "number": len([msg for msg in conversation_history if msg["role"] == "assistant"]) + 1
            }
            
            return question_response
            
        except Exception as e:
            self.logger.error(f"Failed to generate next question with history: {e}")
            raise
    
    async def _generate_closing_question(
        self,
        session_id: str,
        time_remaining: int,
        total_duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Generate a standard closing message when time is running low.
        
        Args:
            session_id: Session identifier
            time_remaining: Remaining time in seconds
            total_duration_minutes: Total interview duration in minutes
            
        Returns:
            Closing question dictionary
        """
        try:
            self.logger.info(f"Generating closing message for session {session_id} - {time_remaining} seconds remaining")
            
            # Standard closing message
            closing_message = (
                "That's all the time I have for questions today. "
                "Thank you for sharing your technical insights and experience with me. "
                "Do you have any questions for me about the role, the team, or the company before we wrap up?"
            )
            
            # Store the closing message as a question in database
            question_record = await storage_service.add_question(
                session_id=session_id,
                question_text=closing_message,
                question_type="closing",
                difficulty="none",
                metadata={
                    "is_closing_message": True,
                    "time_remaining_seconds": time_remaining,
                    "time_threshold_triggered": True,
                    "threshold_percentage": TIME_THRESHOLD_PERCENTAGE
                }
            )
            
            # Format question response
            question_response = {
                "id": question_record.id,
                "text": closing_message,
                "type": "closing",
                "difficulty": "none",
                "focus_area": "interview_closing",
                "number": question_record.question_number,
                "is_closing": True,
                "time_remaining_seconds": time_remaining
            }
            
            self.logger.info(f"Generated closing message for session {session_id}")
            return question_response
            
        except Exception as e:
            self.logger.error(f"Failed to generate closing message for session {session_id}: {e}")
            # Fallback to simple closing message
            return {
                "id": None,
                "text": "That's all the time I have. Do you have any questions for me?",
                "type": "closing",
                "difficulty": "none",
                "focus_area": "interview_closing",
                "number": 999,
                "is_closing": True,
                "time_remaining_seconds": time_remaining
            }
    
    def _is_closing_question(self, message_content: str) -> bool:
        """
        Check if a message is our standard closing question.
        
        Args:
            message_content: The message content to check
            
        Returns:
            True if this is a closing question, False otherwise
        """
        closing_indicators = [
            "That's all the time I have",
            "Do you have any questions for me",
            "before we wrap up",
            "Thank you for sharing your technical insights"
        ]
        
        message_lower = message_content.lower()
        return any(indicator.lower() in message_lower for indicator in closing_indicators)
    
    async def _complete_interview_after_closing_question(
        self,
        session_id: str,
        session_context: Dict[str, Any],
        user_question: str,
        llm_service: McpMeshAgent
    ) -> Dict[str, Any]:
        """
        Complete the interview after user responds to closing question.
        This prevents the LLM from answering potentially sensitive questions.
        
        Args:
            session_id: Session identifier
            session_context: Current session context
            user_question: User's question (saved but not answered)
            llm_service: LLM service for evaluation
            
        Returns:
            Interview completion response
        """
        try:
            self.logger.info(f"Completing interview after closing question - session {session_id}")
            self.logger.info(f"User question (saved but not answered): {user_question[:100]}...")
            
            # The user's question is already saved to database by _process_user_response_with_turn_management
            # We just need to end the interview without letting LLM answer the question
            
            # Move to evaluation phase
            await session_manager.update_session_phase(
                session_id=session_id,
                new_phase=SessionPhase.EVALUATION
            )
            
            # Get complete conversation history for evaluation
            conversation_history = await storage_service.get_conversation_history(session_id)
            
            # Perform final evaluation using the existing evaluation logic
            evaluation_result = await self._evaluate_interview_performance(
                conversation=conversation_history,
                job_data=session_context["job_data"],
                resume_data=session_context["resume_data"],
                llm_service=llm_service
            )
            
            # Mark session as completed
            await session_manager.complete_session(
                session_id=session_id,
                final_evaluation=evaluation_result
            )
            
            # Update application status to COMPLETED
            try:
                application_id = session_context["application_id"]
                await dependency_service.update_application_status(
                    application_id=application_id,
                    new_status="COMPLETED"
                )
                self.logger.info(f"Updated application {application_id} status to COMPLETED")
            except Exception as e:
                self.logger.warning(f"Failed to update application status: {e}")
            
            # Get the interview record for final stats
            interview = await storage_service.get_interview_by_session_id(session_id)
            
            # Build completion response (same format as timeout completion)
            response = {
                "session_id": session_id,
                "status": "completed",
                "phase": "completion",
                "evaluation": evaluation_result,
                "session_summary": {
                    "questions_asked": len([q for q in conversation_history if "question" in q]),
                    "responses_given": len([q for q in conversation_history if "response" in q]),
                    "duration_minutes": round((datetime.now(timezone.utc) - interview.started_at).total_seconds() / 60, 2) if interview else 0,
                    "completion_reason": "user_question_after_closing",
                    "average_score": evaluation_result.get("score", 0)
                },
                "interview_context": {
                    "job_title": session_context.get("job_data", {}).get("title", "Unknown Position"),
                    "company_name": "Company",
                    "completed_at": datetime.now(timezone.utc).isoformat() + "Z"
                },
                "metadata": {
                    "time_remaining_seconds": 0,
                    "user_question_saved": user_question[:100] + "..." if len(user_question) > 100 else user_question,
                    "closing_firewall_triggered": True
                },
                "success": True
            }
            
            self.logger.info(f"Interview completed after closing question - session {session_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to complete interview after closing question: {e}")
            raise Exception(f"Failed to complete interview: {str(e)}")
    
    async def _get_total_violations_for_session(self, session_id: str) -> int:
        """
        Get total violation score for all responses in this session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Total violation score across all responses
        """
        try:
            with get_db_session() as db:
                interview = db.query(Interview).filter(
                    Interview.session_id == session_id
                ).first()
                
                if not interview:
                    return 0
                
                total_violations = 0
                for response in interview.responses:
                    total_violations += response.violation_total_score
                
                return total_violations
                
        except Exception as e:
            self.logger.error(f"Failed to get violations for session {session_id}: {e}")
            return 0
    
    async def _terminate_interview_for_violations(
        self,
        session_id: str,
        session_context: Dict[str, Any],
        termination_reason: str,
        total_violations: int,
        llm_service: McpMeshAgent
    ) -> Dict[str, Any]:
        """
        Terminate interview due to behavioral violations.
        
        Args:
            session_id: Session identifier
            session_context: Current session context
            termination_reason: Reason for termination
            total_violations: Total violation score
            llm_service: LLM service for evaluation
            
        Returns:
            Termination response
        """
        try:
            self.logger.warning(f"Terminating interview {session_id}: {termination_reason}")
            
            # Move to evaluation phase
            await session_manager.update_session_phase(
                session_id=session_id,
                new_phase=SessionPhase.EVALUATION
            )
            
            # Get conversation history for basic evaluation
            conversation_history = await storage_service.get_conversation_history(session_id)
            
            # Create minimal evaluation for terminated session
            evaluation_result = {
                "score": 0,  # Automatic zero score for violations
                "technical_knowledge": 0,
                "problem_solving": 0,
                "communication": 0,
                "experience_relevance": 0,
                "hire_recommendation": "strong_no",
                "feedback": f"Interview terminated due to behavioral violations. {termination_reason}",
                "evaluation_timestamp": datetime.now(timezone.utc).isoformat() + "Z"
            }
            
            # Mark session as completed with violation reason
            await session_manager.complete_session(
                session_id=session_id,
                final_evaluation=evaluation_result
            )
            
            # Update application status
            try:
                application_id = session_context["application_id"]
                await dependency_service.update_application_status(
                    application_id=application_id,
                    new_status="COMPLETED"  # Still completed, just with poor outcome
                )
                self.logger.info(f"Updated application {application_id} status after violation termination")
            except Exception as e:
                self.logger.warning(f"Failed to update application status: {e}")
            
            # Build termination response
            response = {
                "session_id": session_id,
                "status": "terminated",
                "phase": "completion",
                "evaluation": evaluation_result,
                "session_summary": {
                    "questions_asked": len([q for q in conversation_history if "question" in q]),
                    "responses_given": len([q for q in conversation_history if "response" in q]),
                    "duration_minutes": 0,  # Terminated early
                    "completion_reason": "behavioral_violations",
                    "total_violations": total_violations,
                    "average_score": 0
                },
                "interview_context": {
                    "job_title": session_context.get("job_data", {}).get("title", "Unknown Position"),
                    "company_name": "Company",
                    "terminated_at": datetime.now(timezone.utc).isoformat() + "Z"
                },
                "metadata": {
                    "time_remaining_seconds": 0,
                    "termination_reason": termination_reason,
                    "total_violations": total_violations,
                    "violation_threshold": VIOLATION_THRESHOLD
                },
                "success": False,
                "error": termination_reason
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to terminate interview for violations: {e}")
            raise Exception(f"Failed to terminate interview: {str(e)}")
    
    async def _end_interview_session(
        self,
        session_id: str,
        session_context: Dict[str, Any],
        llm_service: McpMeshAgent
    ) -> Dict[str, Any]:
        """
        End the interview session with final evaluation.
        
        Args:
            session_id: Session identifier
            session_context: Current session context
            llm_service: LLM service for evaluation
            
        Returns:
            Interview completion response
        """
        try:
            self.logger.info(f"Ending interview session {session_id}")
            
            # Move to evaluation phase
            await session_manager.update_session_phase(
                session_id=session_id,
                new_phase=SessionPhase.EVALUATION
            )
            
            # Get complete conversation history for evaluation
            conversation_history = await storage_service.get_conversation_history(session_id)
            
            # Perform final evaluation using the existing evaluation logic
            evaluation_result = await self._evaluate_interview_performance(
                conversation=conversation_history,
                job_data=session_context["job_data"],
                resume_data=session_context["resume_data"],
                llm_service=llm_service
            )
            
            # Mark session as completed
            await session_manager.complete_session(
                session_id=session_id,
                final_evaluation=evaluation_result
            )
            
            # Update application status to COMPLETED
            try:
                application_id = session_context["application_id"]
                await dependency_service.update_application_status(
                    application_id=application_id,
                    new_status="COMPLETED"
                )
                self.logger.info(f"Updated application {application_id} status to COMPLETED")
            except Exception as e:
                self.logger.warning(f"Failed to update application status: {e}")
            
            # Get session statistics
            session_stats = await storage_service.get_session_statistics(session_id)
            
            # Build completion response
            response = {
                "session_id": session_id,
                "status": "completed",
                "phase": "completion",
                "evaluation": evaluation_result,
                "session_summary": {
                    "questions_asked": session_stats.get("question_count", 0),
                    "responses_given": session_stats.get("response_count", 0),
                    "duration_minutes": session_stats.get("duration_minutes"),
                    "average_score": evaluation_result.get("score", 0)
                },
                "interview_context": {
                    "job_title": session_context["job_data"].get("title"),
                    "company_name": session_context["job_data"].get("company_name", "Company"),
                    "completed_at": datetime.now(timezone.utc).isoformat()
                },
                "metadata": {
                    "time_remaining_seconds": 0  # Interview is completed, no time remaining
                }
            }
            
            self.logger.info(f"Completed interview session {session_id} - Score: {evaluation_result.get('score', 0)}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to end interview session {session_id}: {e}")
            raise
    
    async def _evaluate_interview_performance(
        self,
        conversation: List[Dict[str, Any]],
        job_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        llm_service: McpMeshAgent
    ) -> Dict[str, Any]:
        """
        Evaluate interview performance using LLM.
        
        Args:
            conversation: Complete conversation history
            job_data: Job posting details
            resume_data: Candidate resume data
            llm_service: LLM service for evaluation
            
        Returns:
            Evaluation results dictionary
        """
        try:
            # Convert conversation to format expected by evaluation function
            formatted_conversation = []
            
            for pair in conversation:
                if "question" in pair:
                    formatted_conversation.append({
                        "type": "question",
                        "content": pair["question"]["text"]
                    })
                
                if "response" in pair:
                    formatted_conversation.append({
                        "type": "answer", 
                        "content": pair["response"]["text"]
                    })
            
            # Use the existing evaluation logic from main.py
            job_description = f"{job_data.get('title', 'Software Developer')}\n\n{job_data.get('description', '')}"
            resume_content = f"Skills: {', '.join(resume_data.get('skills', []))}\n\nExperience: {resume_data.get('experience', 'No experience provided')}"
            
            # This would call the existing evaluate_interview_performance function
            # For now, return a placeholder
            evaluation = {
                "score": 75,
                "technical_knowledge": 18,
                "problem_solving": 19,
                "communication": 20,
                "experience_relevance": 18,
                "hire_recommendation": "yes",
                "feedback": "Good technical understanding with room for improvement in specific areas.",
                "evaluation_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate interview performance: {e}")
            return {
                "score": 0,
                "feedback": "Evaluation failed",
                "error": str(e),
                "evaluation_timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _find_existing_session(self, user_email: str, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Find existing active interview session for user and job.
        
        Args:
            user_email: User's email address
            job_id: Job posting identifier
            
        Returns:
            Existing session data or None if not found
        """
        try:
            self.logger.info(f"_find_existing_session called for user={user_email}, job={job_id}")
            
            # Look for active session for this user and job
            interview = await storage_service.get_interview_by_user_and_job(user_email, job_id)
            
            self.logger.info(f"_find_existing_session result: interview={'found' if interview else 'not found'}")
            
            if interview and interview.status == "INPROGRESS":
                try:
                    # Check if the session has expired
                    from datetime import datetime, timezone
                    current_time = datetime.now(timezone.utc)
                    
                    # Ensure expires_at is timezone-aware (add UTC timezone if naive)
                    expires_at = interview.expires_at
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    
                    self.logger.info(f"Checking expiry: current={current_time}, expires={expires_at}, expired={current_time > expires_at}")
                    if current_time > expires_at:
                        # Session has expired - mark it as completed (expired)
                        await storage_service.update_interview_status(
                            session_id=interview.session_id,
                            status="expired",
                            metadata_updates={"expired_at": current_time.isoformat()}
                        )
                        
                        # Update application status to COMPLETED
                        try:
                            metadata = interview.session_metadata or {}
                            application_id = metadata.get("application_id")
                            if application_id:
                                await dependency_service.update_application_status(
                                    application_id=application_id,
                                    new_status="COMPLETED"
                                )
                        except Exception as e:
                            self.logger.warning(f"Failed to update application status for expired session: {e}")
                        
                        self.logger.info(f"Session {interview.session_id} has expired")
                        # Return the expired session instead of None to trigger the expired error
                        return {
                            "session_id": interview.session_id,
                            "status": "expired",
                            "created_at": interview.created_at,
                            "updated_at": interview.updated_at
                        }
                    
                    # Session is not expired, return it
                    result = {
                        "session_id": interview.session_id,
                        "status": interview.status,
                        "created_at": interview.created_at,
                        "updated_at": interview.updated_at
                    }
                    
                    self.logger.info(f"Returning existing session: {result['session_id']}")
                    return result
                    
                except Exception as exp_error:
                    self.logger.error(f"Error checking expiry for session {interview.session_id}: {exp_error}")
                    # Return None if there's an expiry checking error
                    return None
            
            self.logger.info("No valid active session found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding existing session for user {user_email}, job {job_id}: {e}")
            return None
    
    async def _return_existing_session_with_history(self, session_id: str) -> Dict[str, Any]:
        """
        Return existing session with complete Q&A history.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session response with conversation history
        """
        try:
            # Get session context
            session_context = await session_manager.get_session(session_id)
            if not session_context:
                raise Exception(f"Session {session_id} not found")
            
            # Check if session has expired
            from datetime import datetime, timezone
            interview = await storage_service.get_interview_by_session_id(session_id)
            if interview:
                current_time = datetime.utcnow()  # Use naive UTC datetime to match database
                if current_time > interview.expires_at:
                    # Session has expired - mark it as expired and return error
                    await storage_service.update_interview_status(
                        session_id=session_id,
                        status="expired",
                        metadata_updates={"expired_at": current_time.isoformat()}
                    )
                    
                    # Update application status to COMPLETED
                    try:
                        metadata = interview.session_metadata or {}
                        application_id = metadata.get("application_id")
                        if application_id:
                            await dependency_service.update_application_status(
                                application_id=application_id,
                                new_status="COMPLETED"
                            )
                    except Exception as e:
                        self.logger.warning(f"Failed to update application status for expired session: {e}")
                    
                    # Calculate how long ago it expired
                    expired_duration = current_time - interview.expires_at
                    expired_minutes = int(expired_duration.total_seconds() / 60)
                    
                    raise Exception(f"Interview session has ended due to timeout. The session expired {expired_minutes} minutes ago.")
            
            # Get full conversation history from database through storage service
            with get_db_session() as db:
                interview_with_relations = db.query(Interview).filter(
                    Interview.session_id == session_id
                ).first()
                full_conversation = interview_with_relations.get_conversation_for_llm() if interview_with_relations else []
            conversation = await storage_service.get_conversation_history(session_id)
            
            # Analyze conversation state with turn management
            conversation_state = turn_manager.analyze_conversation_state(
                conversation_history=full_conversation,
                has_user_input=False
            )
            
            # Determine current status based on conversation state
            unanswered_questions = [q for q in conversation if not q.get("response")]
            
            if unanswered_questions:
                # There are unanswered questions - return the first unanswered one
                current_question = unanswered_questions[0]["question"]
                status = "questioning"
                phase = "questioning"
            else:
                # All questions answered - interview is complete or needs evaluation
                status = "COMPLETED" 
                phase = "evaluation"
                current_question = None
            
            # Prepare response
            response = {
                "session_id": session_id,
                "status": status,
                "phase": phase,
                "interview_context": {
                    "job_title": session_context.get("job_data", {}).get("title", "Unknown Position"),
                    "company_name": "Company",
                    "session_started": session_context.get("created_at"),
                    "difficulty_level": session_context.get("metadata", {}).get("difficulty_level", "medium")
                },
                "conversation_history": conversation,
                "metadata": {
                    "total_questions": len(conversation),
                    "questions_answered": len([q for q in conversation if q.get("response")]),
                    "session_created": session_context.get("created_at"),
                    "time_remaining_seconds": interview.time_remaining_seconds if interview else 0,
                    "full_conversation": full_conversation,
                    "conversation_state": conversation_state
                },
                "success": True
            }
            
            # Add current question if there is one
            if current_question:
                response["question"] = {
                    "id": current_question.get("id"),
                    "text": current_question.get("text"),
                    "type": current_question.get("type"),
                    "difficulty": current_question.get("difficulty"),
                    "focus_area": current_question.get("focus_area"),
                    "number": current_question.get("number")
                }
                response["question_text"] = current_question.get("text")
                response["question_metadata"] = {
                    "type": current_question.get("type"),
                    "focus_area": current_question.get("focus_area"),
                    "difficulty": current_question.get("difficulty"),
                    "question_number": current_question.get("number")
                }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error returning existing session {session_id}: {e}")
            raise Exception(f"Failed to return existing session: {str(e)}")

# Global interview conductor instance  
interview_conductor = InterviewConductor()