"""
Step 3: Questions Handler

Handles generation and saving of responses to job-specific application questions.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import json

from ..database import get_db_session, ApplicationQuestions
# Tool spec imports removed - using detailed analysis from user agent
from ..utils.step_management import get_step_title, get_step_description

logger = logging.getLogger(__name__)


async def save_questions_data(
    application_id: str,
    questions_data: Dict[str, Any]
) -> bool:
    """
    Save question responses to database.
    
    Args:
        application_id: Application ID
        questions_data: Questions data (matches database schema)
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        with get_db_session() as db_session:
            # Check if questions data already exists
            existing_questions = db_session.query(ApplicationQuestions).filter(
                ApplicationQuestions.application_id == application_id
            ).first()
            
            if existing_questions:
                # Update existing record (matching database schema)
                existing_questions.work_authorization = questions_data.get("work_authorization", "no")
                existing_questions.visa_sponsorship = questions_data.get("visa_sponsorship", "no")
                existing_questions.relocate = questions_data.get("relocate", "no")
                existing_questions.remote_work = questions_data.get("remote_work", "no")
                existing_questions.preferred_location = questions_data.get("preferred_location", "")
                existing_questions.availability = questions_data.get("availability", "immediately")
                existing_questions.salary_min = questions_data.get("salary_min", "0")
                existing_questions.salary_max = questions_data.get("salary_max", "0")
                existing_questions.updated_at = datetime.utcnow()
                logger.info(f"Updated existing questions data for application {application_id}")
            else:
                # Create new record (matching database schema)
                questions_record = ApplicationQuestions(
                    application_id=application_id,
                    work_authorization=questions_data.get("work_authorization", "no"),
                    visa_sponsorship=questions_data.get("visa_sponsorship", "no"),
                    relocate=questions_data.get("relocate", "no"),
                    remote_work=questions_data.get("remote_work", "no"),
                    preferred_location=questions_data.get("preferred_location", ""),
                    availability=questions_data.get("availability", "immediately"),
                    salary_min=questions_data.get("salary_min", "0"),
                    salary_max=questions_data.get("salary_max", "0")
                )
                db_session.add(questions_record)
                logger.info(f"Created new questions record for application {application_id}")
            
            db_session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to save questions data: {e}")
        return False

async def handle_questions_step(
    application_id: str,
    detailed_analysis: Dict[str, Any] = None,
    step_data: Dict[str, Any] = None,
    job_questions: List[Dict[str, Any]] = None,
    save_data: bool = True
) -> Dict[str, Any]:
    """
    Handle Step 3: Questions processing.
    
    Two modes:
    1. Generate prefill: No prefill needed for step 3 (user preferences)
    2. Save user data: step_data provided for save mode
    
    Args:
        application_id: Application ID
        detailed_analysis: Not used for step 3 (maintained for consistency)
        step_data: User-submitted data to save (for save mode)
        job_questions: List of job-specific questions
        save_data: Whether to save data to database
        
    Returns:
        Dict with prefill data and processing results
    """
    try:
        logger.info(f"Processing Step 3 (Questions) for application {application_id}")
        
        # Mode 1: Save user-submitted data
        if step_data:
            logger.info("Mode: Saving user-submitted questions data")
            
            # Save user data to database
            if save_data:
                save_success = await save_questions_data(application_id, step_data)
                if not save_success:
                    return {
                        "success": False,
                        "error": "Failed to save questions information",
                        "step": 3,
                        "step_name": "questions"
                    }
            
            return {
                "success": True,
                "step": 3,
                "step_name": "questions",
                "step_title": get_step_title(3),
                "step_description": get_step_description(3),
                "data_saved": True,
                "message": "Questions information saved successfully"
            }
        
        # Mode 2: Return empty prefill data (no LLM extraction for Step 3)
        else:
            logger.info("Mode: Returning empty prefill data for Step 3 (no LLM extraction)")
            
            # Return empty prefill data - user will fill these fields manually
            prefill_data = {
                "work_authorization": "unknown",
                "visa_sponsorship": "unknown", 
                "relocate": "maybe",
                "remote_work": "hybrid",
                "preferred_location": "",
                "availability": "",
                "salary_min": "",
                "salary_max": ""
            }
            
            logger.info(f"Successfully returned empty prefill for Step 3, application {application_id}")
            
            return {
                "success": True,
                "step": 3,
                "step_name": "questions",
                "step_title": get_step_title(3),
                "step_description": get_step_description(3),
                "prefill_data": prefill_data,
                "extraction_metadata": {
                    "confidence_score": 0.0,
                    "ai_provider": "none",
                    "ai_model": "none", 
                    "questions_count": len(job_questions) if job_questions else 0,
                    "llm_skipped": True
                },
                "data_saved": False
            }
        
    except Exception as e:
        logger.error(f"Step 3 processing failed: {e}")
        return {
            "success": False,
            "error": f"Questions step processing failed: {str(e)}",
            "step": 3,
            "step_name": "questions"
        }