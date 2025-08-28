"""
Step 6: Review Handler

Handles final review and submission with LLM qualification assessment.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..database import (
    get_db_session, 
    Application, 
    ApplicationPersonalInfo,
    ApplicationExperience, 
    ApplicationQuestions,
    ApplicationDisclosures,
    ApplicationIdentity
)
from ..tool_specs.qualification_tools import get_qualification_tool_spec
from ..utils.step_management import get_step_title, get_step_description

logger = logging.getLogger(__name__)

async def compile_application_data(
    application_id: str
) -> Dict[str, Any]:
    """
    Compile all application data for LLM qualification assessment.
    
    Args:
        application_id: Application ID
        
    Returns:
        Dict with all application data (excludes EEO identity for privacy)
    """
    try:
        logger.info(f"Compiling application data for qualification assessment: {application_id}")
        
        with get_db_session() as db_session:
            # Get main application record
            application = db_session.query(Application).filter(
                Application.id == application_id
            ).first()
            
            if not application:
                return {
                    "success": False,
                    "error": "Application not found"
                }
            
            # Get data from each step (excluding EEO identity for privacy)
            personal_info = db_session.query(ApplicationPersonalInfo).filter(
                ApplicationPersonalInfo.application_id == application_id
            ).first()
            
            experience = db_session.query(ApplicationExperience).filter(
                ApplicationExperience.application_id == application_id
            ).first()
            
            questions = db_session.query(ApplicationQuestions).filter(
                ApplicationQuestions.application_id == application_id
            ).first()
            
            disclosures = db_session.query(ApplicationDisclosures).filter(
                ApplicationDisclosures.application_id == application_id
            ).first()
            
            # Note: EEO Identity data is intentionally excluded from LLM assessment
            
            # Compile data for LLM assessment
            application_data = {
                "application_info": {
                    "user_email": application.user_email,
                    "job_id": application.job_id,
                    "application_date": application.created_at.isoformat()
                }
            }
            
            # Personal Information
            if personal_info:
                application_data["personal_info"] = {
                    "name": f"{personal_info.first_name} {personal_info.last_name}",
                    "email": personal_info.email,
                    "phone": personal_info.phone,
                    "location": f"{personal_info.city}, {personal_info.state}, {personal_info.country}",
                    "linkedin": personal_info.linkedin or "Not provided"
                }
            
            # Experience and Skills
            if experience:
                application_data["experience"] = {
                    "summary": experience.summary,
                    "technical_skills": experience.technical_skills,
                    "soft_skills": experience.soft_skills or "Not specified",
                    "work_experience": experience.work_experience or [],
                    "education": experience.education or []
                }
            
            # Application Questions
            if questions:
                application_data["questions"] = {
                    "work_authorization": questions.work_authorization,
                    "visa_sponsorship": questions.visa_sponsorship,
                    "relocate": questions.relocate,
                    "remote_work": questions.remote_work,
                    "preferred_location": questions.preferred_location,
                    "availability": questions.availability,
                    "salary_range": {
                        "min": questions.salary_min,
                        "max": questions.salary_max
                    }
                }
            
            # Disclosures
            if disclosures:
                application_data["disclosures"] = {
                    "government_employment": disclosures.government_employment,
                    "non_compete": disclosures.non_compete,
                    "previous_employment": disclosures.previous_employment
                }
            
            logger.info(f"Application data compiled successfully for assessment")
            
            return {
                "success": True,
                "application_data": application_data
            }
            
    except Exception as e:
        logger.error(f"Failed to compile application data: {e}")
        return {
            "success": False,
            "error": f"Failed to compile application data: {str(e)}"
        }

async def assess_qualification_with_llm(
    application_data: Dict[str, Any],
    job_details: Dict[str, Any],
    resume_text: str,
    llm_service,
    convert_tool_format
) -> Dict[str, Any]:
    """
    Perform LLM-based qualification assessment.
    
    Args:
        application_data: Complete application data from all steps
        job_details: Job title, description, and requirements
        resume_text: Original resume text content
        llm_service: LLM agent for assessment
        convert_tool_format: Tool format converter
        
    Returns:
        Dict with qualification assessment results
    """
    try:
        logger.info("Performing LLM qualification assessment")
        
        # Get qualification tool specification
        qualification_tool = get_qualification_tool_spec()
        
        # Convert tools to appropriate format for the LLM provider
        converted_tools = [qualification_tool]
        if convert_tool_format:
            try:
                converted_result = await convert_tool_format(tools=[qualification_tool])
                if converted_result:
                    converted_tools = converted_result
                    logger.info("Successfully converted qualification tool for LLM provider")
                else:
                    logger.warning("Tool conversion returned None, using original format")
            except Exception as e:
                logger.warning(f"Tool conversion failed, using original format: {e}")
        
        # Create comprehensive system prompt
        system_prompt = f"""You are an expert HR professional conducting candidate qualification assessment. Analyze the complete application against job requirements to determine hiring recommendation.

JOB INFORMATION:
Title: {job_details.get('title', 'Position')}
Description: {job_details.get('description', 'No description provided')}
Requirements: {job_details.get('requirements', 'Not specified')}
Location: {job_details.get('location', 'Not specified')}

CANDIDATE APPLICATION DATA:
{str(application_data)}

RESUME TEXT:
{resume_text[:4000]}{'...' if len(resume_text) > 4000 else ''}

ASSESSMENT INSTRUCTIONS:
1. Evaluate technical skills match against job requirements
2. Assess experience level and relevance 
3. Review work authorization and location compatibility
4. Analyze salary expectations vs. budget
5. Check for any red flags or concerns
6. Provide holistic qualification score (0-100)

SCORING GUIDELINES:
- 80-100: Strong match, recommend INTERVIEW
- 60-79: Partial match, recommend HR_REVIEW  
- 0-59: Poor match, recommend REJECT

Provide detailed reasoning for your assessment and recommendation.

Use the provided tool to return structured qualification assessment."""
        
        # Call LLM service
        logger.info(f"Calling LLM service for qualification assessment")
        logger.info(f"llm_service type: {type(llm_service)}, value: {llm_service}")
        logger.info(f"converted_tools type: {type(converted_tools)}, length: {len(converted_tools) if converted_tools else 'None'}")
        
        if llm_service is None:
            logger.error("llm_service is None - cannot perform qualification assessment")
            return {
                "success": False,
                "error": "LLM service not available"
            }
        
        result = await llm_service(
            text="Assess this candidate's qualification for the job using the provided tool.",
            system_prompt=system_prompt,
            messages=[],
            tools=converted_tools,
            force_tool_use=True,
            temperature=0.1
        )
        
        if result and result.get("success") and result.get("tool_calls"):
            tool_calls = result.get("tool_calls", [])
            if len(tool_calls) > 0:
                assessment_data = tool_calls[0].get("parameters", {})
                logger.info(f"LLM qualification assessment completed - Score: {assessment_data.get('qualification_score', 'N/A')}, Recommendation: {assessment_data.get('recommendation', 'N/A')}")
                return {
                    "success": True,
                    "assessment": assessment_data,
                    "ai_provider": result.get("provider", "unknown"),
                    "ai_model": result.get("model", "unknown")
                }
        
        logger.warning("LLM failed to provide qualification assessment")
        return {
            "success": False,
            "error": "Failed to get qualification assessment from LLM"
        }
        
    except Exception as e:
        logger.error(f"Qualification assessment failed: {e}")
        return {
            "success": False,
            "error": f"Qualification assessment error: {str(e)}"
        }

async def handle_review_step(
    application_id: str,
    detailed_analysis: Dict[str, Any] = None,
    step_data: Dict[str, Any] = None,
    job_agent=None,
    user_agent=None,
    llm_service=None,
    convert_tool_format=None,
    cache_agent=None,
    save_data: bool = True
) -> Dict[str, Any]:
    """
    Handle Step 6: Final Review and Submission with LLM Qualification Assessment.
    
    Two modes:
    1. Generate prefill: Returns application summary for review
    2. Submit application: Performs LLM qualification assessment and finalizes
    
    Args:
        application_id: Application ID
        resume_text: Resume text for qualification assessment
        step_data: Submission data (when user submits final application)
        job_agent: MCP agent for job details
        user_agent: MCP agent for resume text
        llm_service: LLM agent for qualification assessment
        convert_tool_format: Tool format converter
        cache_agent: MCP agent for cache invalidation
        save_data: Whether to save assessment data
        
    Returns:
        Dict with review data or final submission results
    """
    try:
        logger.info(f"Processing Step 6 (Final Review) for application {application_id}")
        
        # Mode 1: Final Submission with LLM Assessment
        if step_data and step_data.get("submit_application"):
            logger.info("Mode: Final application submission with qualification assessment")
            
            # 1. Compile all application data
            app_data_result = await compile_application_data(application_id)
            if not app_data_result.get("success"):
                return {
                    "success": False,
                    "error": app_data_result.get("error", "Failed to compile application data"),
                    "step": 6,
                    "step_name": "review"
                }
            
            application_data = app_data_result["application_data"]
            job_id = application_data["application_info"]["job_id"]
            user_email = application_data["application_info"]["user_email"]
            
            # 2. Get job details
            job_details = {"title": "Software Engineer", "description": "Not available", "requirements": "Not specified", "location": "San Francisco, CA"}
            if job_agent:
                try:
                    logger.info(f"Calling job_agent to get details for job {job_id}")
                    job_result = await job_agent(job_id=job_id)
                    logger.info(f"Job agent returned: {type(job_result)} - {str(job_result)[:200]}...")
                    if job_result and not job_result.get("error"):
                        job_details = {
                            "title": job_result.get("title", "Position"),
                            "description": job_result.get("description", "No description"),
                            "requirements": job_result.get("requirements", []),
                            "location": job_result.get("location", "Not specified")
                        }
                        logger.info(f"Retrieved job details for job {job_id}: title='{job_details['title']}'")
                    else:
                        logger.warning(f"Job not found or error: {job_result.get('error', 'Unknown error')}")
                except Exception as job_error:
                    logger.warning(f"Failed to get job details: {job_error}")
            else:
                logger.warning("job_agent is None - job details will not be fetched")
            
            # 3. Get resume text for qualification assessment
            resume_text = ""  # Initialize resume text
            if user_agent:
                try:
                    resume_result = await user_agent(user_email=user_email)
                    if resume_result.get("success") and resume_result.get("text_content"):
                        resume_text = resume_result["text_content"]
                        logger.info(f"Retrieved resume text for qualification assessment")
                except Exception as resume_error:
                    logger.warning(f"Failed to get resume text: {resume_error}")
            
            # 4. Perform LLM qualification assessment
            assessment_result = await assess_qualification_with_llm(
                application_data, job_details, resume_text or "Resume not available", 
                llm_service, convert_tool_format
            )
            
            if not assessment_result.get("success"):
                logger.error(f"Qualification assessment failed: {assessment_result.get('error')}")
                # Default to HR_REVIEW if assessment fails
                assessment_data = {
                    "qualification_score": 65,
                    "recommendation": "HR_REVIEW",
                    "reasoning": "LLM assessment unavailable - defaulting to HR review",
                    "confidence_score": 0.0
                }
                ai_provider = "unknown"
                ai_model = "unknown"
            else:
                assessment_data = assessment_result["assessment"]
                ai_provider = assessment_result.get("ai_provider", "unknown")
                ai_model = assessment_result.get("ai_model", "unknown")
            
            # 5. Update application with assessment results
            qualification_score = assessment_data.get("qualification_score", 0)
            recommendation = assessment_data.get("recommendation", "HR_REVIEW")
            
            # Determine final status based on qualification score
            if qualification_score >= 80:
                final_status = "QUALIFIED"
                result_param = "eligible"
            else:
                final_status = "APPLIED" 
                result_param = "under-review"
            
            # 6. Save assessment to database
            with get_db_session() as db_session:
                application = db_session.query(Application).filter(
                    Application.id == application_id
                ).first()
                
                if application:
                    application.status = final_status
                    application.submitted_at = datetime.utcnow()
                    application.qualification_score = qualification_score
                    application.qualification_recommendation = recommendation
                    application.qualification_reasoning = assessment_data.get("reasoning", "")
                    application.ai_assessment_provider = ai_provider
                    application.ai_assessment_model = ai_model
                    application.updated_at = datetime.utcnow()
                    
                    db_session.commit()
                    logger.info(f"Application {application_id} finalized - Status: {final_status}, Score: {qualification_score}")
            
            # 6.5. Invalidate user cache to refresh applications list
            if cache_agent:
                try:
                    logger.info(f"Invalidating user cache for: {user_email}")
                    cache_result = await cache_agent(user_email=user_email)
                    if cache_result and cache_result.get("success"):
                        logger.info(f"User cache successfully invalidated for: {user_email}")
                    else:
                        logger.warning(f"Cache invalidation failed: {cache_result}")
                except Exception as cache_error:
                    logger.warning(f"Failed to invalidate user cache: {cache_error}")
            else:
                logger.warning("cache_agent is None - user cache will not be invalidated")
            
            # 7. Return response with UI redirect
            redirect_url = f"/apply/{job_id}/result?result={result_param}"
            
            return {
                "success": True,
                "message": "Application submitted successfully",
                "data": {
                    "application_id": application_id,
                    "final_status": final_status,
                    "qualification_score": qualification_score,
                    "recommendation": recommendation,
                    "redirect_url": redirect_url,
                    "ui_action": "SHOW_INTERVIEW" if result_param == "eligible" else "SHOW_UNDER_REVIEW",
                    "assessment_details": {
                        "key_matches": assessment_data.get("key_matches", []),
                        "red_flags": assessment_data.get("red_flags", []),
                        "reasoning": assessment_data.get("reasoning", ""),
                        "ai_provider": ai_provider,
                        "ai_model": ai_model,
                        "confidence": assessment_data.get("confidence_score", 0.0)
                    }
                },
                "progress_percentage": 100.0
            }
        
        # Mode 2: Generate review prefill (application summary)
        else:
            logger.info("Mode: Generating application review summary")
            
            app_data_result = await compile_application_data(application_id)
            if not app_data_result.get("success"):
                return {
                    "success": False,
                    "error": app_data_result.get("error", "Failed to compile application data"),
                    "step": 6,
                    "step_name": "review"
                }
            
            application_data = app_data_result["application_data"]
            
            # Format review data for frontend
            prefill_data = {
                "application_summary": application_data,
                "ready_for_submission": True,  # All steps completed to reach step 6
                "steps_completed": [
                    "Personal Information",
                    "Work Experience", 
                    "Application Questions",
                    "Voluntary Disclosures",
                    "EEO Identity Information"
                ]
            }
            
            return {
                "success": True,
                "step": 6,
                "step_name": "review",
                "step_title": get_step_title(6),
                "step_description": get_step_description(6),
                "prefill_data": prefill_data,
                "is_final_step": True,
                "data_saved": False
            }
        
    except Exception as e:
        logger.error(f"Step 6 processing failed: {e}")
        return {
            "success": False,
            "error": f"Final review step processing failed: {str(e)}",
            "step": 6,
            "step_name": "review"
        }