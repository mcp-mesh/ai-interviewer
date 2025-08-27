"""
Step 3: Questions Handler

Handles generation and saving of responses to job-specific application questions.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import json

from ..database import get_db_session, ApplicationQuestions
from ..tool_specs.questions_tools import get_questions_tool_spec, get_generic_questions_tool_spec
from ..utils.step_management import get_step_title, get_step_description

logger = logging.getLogger(__name__)

async def generate_question_responses_with_llm(
    resume_text: str,
    job_questions: List[Dict[str, Any]],
    llm_service,
    convert_tool_format
) -> Dict[str, Any]:
    """
    Generate responses to job questions using LLM and resume content.
    
    Args:
        resume_text: Raw resume text content
        job_questions: List of job-specific questions
        llm_service: LLM agent for processing
        convert_tool_format: Tool format converter
        
    Returns:
        Dict with generated responses or error
    """
    try:
        logger.info(f"Generating responses for {len(job_questions)} job questions using LLM")
        
        # Get appropriate tool specification
        if job_questions:
            questions_tool = get_questions_tool_spec(job_questions)
        else:
            questions_tool = get_generic_questions_tool_spec()
            logger.info("Using generic questions tool - no specific job questions provided")
        
        # Convert tools to appropriate format for the LLM provider
        converted_tools = [questions_tool]
        if convert_tool_format:
            try:
                converted_tools = await convert_tool_format(tools=[questions_tool])
                logger.info("Successfully converted questions tool for LLM provider")
            except Exception as e:
                logger.warning(f"Tool conversion failed, using original format: {e}")
        
        # Build question context for system prompt
        questions_context = ""
        if job_questions:
            questions_context = "\n".join([
                f"Q{i+1}: {q.get('question', '')} (Type: {q.get('type', 'text')}, Required: {q.get('required', False)})"
                for i, q in enumerate(job_questions)
            ])
        else:
            questions_context = "No specific job questions provided - generate generic application responses."
        
        # Create system prompt for question response generation
        system_prompt = f"""You are a professional application writer. Generate thoughtful responses to job application questions based on the candidate's resume experience.

RESUME TEXT:
{resume_text[:2500]}{'...' if len(resume_text) > 2500 else ''}

JOB QUESTIONS:
{questions_context}

Instructions:
- Analyze the resume to understand the candidate's background, skills, and experience
- Generate authentic, personalized responses that highlight relevant experience
- Ensure responses are professional, concise, and directly address each question
- Write a compelling cover letter that connects resume experience to the role
- Explain why the candidate is interested and uniquely qualified
- Keep responses within specified character limits

STANDARD APPLICATION FIELDS - INFER FROM RESUME:
- Work Authorization: Look for citizenship, visa status, or location indicators
- Visa Sponsorship: Infer from current location vs work history
- Relocation: Look at location history and current location patterns
- Remote Work Preference: Infer from recent work arrangements if mentioned
- Preferred Location: Use most recent location or location patterns from resume
- Salary Range: Base on experience level, role seniority, and industry standards
- Availability: Standard professional availability unless specific dates mentioned

Rate your confidence in the generated responses (0.0-1.0)

Use the provided tool to return all responses in structured format."""

        # Call LLM service
        logger.info(f"Calling LLM service for question response generation")
        result = await llm_service(
            text="Generate responses to the job application questions using the provided tool.",
            system_prompt=system_prompt,
            messages=[],
            tools=converted_tools,
            force_tool_use=True,
            temperature=0.2
        )
        
        if result and result.get("success") and result.get("tool_calls"):
            tool_calls = result.get("tool_calls", [])
            if len(tool_calls) > 0:
                questions_data = tool_calls[0].get("parameters", {})
                logger.info(f"Successfully generated question responses - confidence: {questions_data.get('confidence_score', 'N/A')}")
                return {
                    "success": True,
                    "data": questions_data,
                    "ai_provider": result.get("provider", "unknown"),
                    "ai_model": result.get("model", "unknown")
                }
        
        logger.warning("LLM failed to generate question responses")
        return {
            "success": False,
            "error": "Failed to generate question responses"
        }
        
    except Exception as e:
        logger.error(f"Question response generation failed: {e}")
        return {
            "success": False,
            "error": f"Question response generation error: {str(e)}"
        }

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
    resume_text: str = "",
    step_data: Dict[str, Any] = None,
    job_questions: List[Dict[str, Any]] = None,
    llm_service=None,
    convert_tool_format=None,
    save_data: bool = True
) -> Dict[str, Any]:
    """
    Handle Step 3: Questions processing.
    
    Two modes:
    1. Generate prefill: resume_text provided, step_data=None  
    2. Save user data: step_data provided, resume_text optional
    
    Args:
        application_id: Application ID
        resume_text: Resume text content (for prefill generation)
        step_data: User-submitted data to save (for save mode)
        job_questions: List of job-specific questions
        llm_service: LLM agent for extraction  
        convert_tool_format: Tool format converter
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