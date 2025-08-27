"""
Step 2: Experience Handler

Handles extraction, validation, and saving of work experience information.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import json

from ..database import get_db_session, ApplicationExperience
from ..tool_specs.experience_tools import get_experience_tool_spec
from ..utils.step_management import get_step_title, get_step_description

logger = logging.getLogger(__name__)

async def extract_experience_with_llm(
    resume_text: str,
    llm_service,
    convert_tool_format
) -> Dict[str, Any]:
    """
    Extract work experience from resume text using LLM.
    
    Args:
        resume_text: Raw resume text content
        llm_service: LLM agent for processing
        convert_tool_format: Tool format converter
        
    Returns:
        Dict with extracted experience information or error
    """
    try:
        logger.info("Extracting work experience using LLM")
        
        # Get tool specification
        experience_tool = get_experience_tool_spec()
        
        # Convert tools to appropriate format for the LLM provider
        converted_tools = [experience_tool]
        if convert_tool_format:
            try:
                converted_tools = await convert_tool_format(tools=[experience_tool])
                logger.info("Successfully converted experience tool for LLM provider")
            except Exception as e:
                logger.warning(f"Tool conversion failed, using original format: {e}")
        
        # Create system prompt for experience extraction
        system_prompt = f"""You are a professional resume parser. Extract 5 key fields from any resume format: Brief Summary, Technical Skills, Soft Skills, Work Experience, and Education.

RESUME TEXT (First 5000 characters):
{resume_text[:5000]}{'...' if len(resume_text) > 5000 else ''}

EXTRACTION GUIDELINES:
1. BRIEF SUMMARY: Create 2-3 sentence summary from any overview/profile/objective section, or synthesize from overall content
2. TECHNICAL SKILLS: Find programming languages, technologies, tools, frameworks mentioned anywhere in the resume  
3. SOFT SKILLS: Infer from job descriptions, achievements, leadership roles - look for management, communication, problem-solving indicators
4. WORK EXPERIENCE: Extract job entries with company names, job titles, employment dates, and key responsibilities
5. EDUCATION: Find degrees, certifications, schools, universities mentioned anywhere in the document

FLEXIBLE PARSING APPROACH:
- Adapt to any resume format (chronological, functional, hybrid, modern, traditional)
- Look for common patterns: company names, job titles, dates, degree names, school names
- Infer information from context when explicit sections aren't labeled
- Handle various date formats (MM/YYYY, Month Year, Year only)
- Extract skills from job descriptions if no dedicated skills section exists
- Synthesize professional summary if no explicit summary section is present
- Identify education from institution names, degree keywords (Bachelor, Master, PhD, Certification)

Focus on extracting complete, accurate information regardless of resume formatting or structure."""

        # Call LLM service
        logger.info(f"Calling LLM service for experience extraction")
        result = await llm_service(
            text="Extract detailed work experience from this resume using the provided tool.",
            system_prompt=system_prompt,
            messages=[],
            tools=converted_tools,
            force_tool_use=True,
            temperature=0.1
        )
        
        if result and result.get("success") and result.get("tool_calls"):
            tool_calls = result.get("tool_calls", [])
            if len(tool_calls) > 0:
                experience_data = tool_calls[0].get("parameters", {})
                logger.info(f"Successfully extracted experience - {len(experience_data.get('work_experience', []))} roles, confidence: {experience_data.get('confidence_score', 'N/A')}")
                return {
                    "success": True,
                    "data": experience_data,
                    "ai_provider": result.get("provider", "unknown"),
                    "ai_model": result.get("model", "unknown")
                }
        
        logger.warning("LLM failed to extract work experience")
        return {
            "success": False,
            "error": "Failed to extract work experience from resume"
        }
        
    except Exception as e:
        logger.error(f"Experience extraction failed: {e}")
        return {
            "success": False,
            "error": f"Experience extraction error: {str(e)}"
        }

async def save_experience_data(
    application_id: str,
    experience_data: Dict[str, Any]
) -> bool:
    """
    Save work experience to database.
    
    Args:
        application_id: Application ID
        experience_data: Experience information (matches database schema)
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        with get_db_session() as db_session:
            # Check if experience data already exists
            existing_experience = db_session.query(ApplicationExperience).filter(
                ApplicationExperience.application_id == application_id
            ).first()
            
            # Extract data according to database schema
            work_experience = experience_data.get("work_experience", [])
            education = experience_data.get("education", [])
            
            if existing_experience:
                # Update existing record
                existing_experience.summary = experience_data.get("summary", "")
                existing_experience.technical_skills = experience_data.get("technical_skills", "")
                existing_experience.soft_skills = experience_data.get("soft_skills", "")
                existing_experience.work_experience = work_experience
                existing_experience.education = education
                existing_experience.updated_at = datetime.utcnow()
                logger.info(f"Updated existing experience data for application {application_id}")
            else:
                # Create new record
                experience_record = ApplicationExperience(
                    application_id=application_id,
                    summary=experience_data.get("summary", ""),
                    technical_skills=experience_data.get("technical_skills", ""),
                    soft_skills=experience_data.get("soft_skills", ""),
                    work_experience=work_experience,
                    education=education
                )
                db_session.add(experience_record)
                logger.info(f"Created new experience record for application {application_id}")
            
            db_session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to save experience data: {e}")
        return False

async def handle_experience_step(
    application_id: str,
    resume_text: str = "",
    step_data: Dict[str, Any] = None,
    llm_service=None,
    convert_tool_format=None,
    save_data: bool = True
) -> Dict[str, Any]:
    """
    Handle Step 2: Work Experience processing.
    
    Two modes:
    1. Generate prefill: resume_text provided, step_data=None  
    2. Save user data: step_data provided, resume_text optional
    
    Args:
        application_id: Application ID
        resume_text: Resume text content (for prefill generation)
        step_data: User-submitted data to save (for save mode)
        llm_service: LLM agent for extraction  
        convert_tool_format: Tool format converter
        save_data: Whether to save data to database
        
    Returns:
        Dict with prefill data and processing results
    """
    try:
        logger.info(f"Processing Step 2 (Experience) for application {application_id}")
        
        # Mode 1: Save user-submitted data
        if step_data:
            logger.info("Mode: Saving user-submitted experience data")
            
            # Save user data to database
            if save_data:
                save_success = await save_experience_data(application_id, step_data)
                if not save_success:
                    return {
                        "success": False,
                        "error": "Failed to save experience information",
                        "step": 2,
                        "step_name": "experience"
                    }
            
            return {
                "success": True,
                "step": 2,
                "step_name": "experience",
                "step_title": get_step_title(2),
                "step_description": get_step_description(2),
                "data_saved": True,
                "message": "Experience information saved successfully"
            }
        
        # Mode 2: Generate prefill from resume
        else:
            logger.info("Mode: Generating prefill from resume text")
            
            # Extract experience information using LLM
            extraction_result = await extract_experience_with_llm(
                resume_text, llm_service, convert_tool_format
            )
            
            if not extraction_result.get("success"):
                return {
                    "success": False,
                    "error": extraction_result.get("error", "Failed to extract work experience"),
                    "step": 2,
                    "step_name": "experience"
                }
            
            experience_data = extraction_result["data"]
            
            # Format prefill data for frontend (matching database schema)
            # Map LLM tool response fields to database schema fields
            key_skills = experience_data.get("key_skills", [])
            technical_skills = ", ".join(key_skills) if key_skills else ""
            
            soft_skills_array = experience_data.get("soft_skills", [])
            soft_skills = ", ".join(soft_skills_array) if soft_skills_array else ""
            
            # Use extracted summary or generate fallback
            extracted_summary = experience_data.get("summary", "")
            if not extracted_summary:
                # Generate fallback summary from extracted data
                industries = experience_data.get("industries", [])
                total_years = experience_data.get("total_years_experience", 0)
                management_exp = experience_data.get("management_experience", False)
                
                summary_parts = []
                if total_years:
                    summary_parts.append(f"Over {total_years} years of professional experience")
                if industries:
                    summary_parts.append(f"in {', '.join(industries)}")
                if management_exp:
                    summary_parts.append("with management and leadership experience")
                
                extracted_summary = ". ".join(summary_parts) + "." if summary_parts else ""
            
            prefill_data = {
                "summary": extracted_summary,
                "technical_skills": technical_skills,
                "soft_skills": soft_skills,
                "work_experience": experience_data.get("work_experience", []),
                "education": experience_data.get("education", [])
            }
            
            logger.info(f"Successfully generated prefill for Step 2, application {application_id}")
            
            return {
                "success": True,
                "step": 2,
                "step_name": "experience",
                "step_title": get_step_title(2),
                "step_description": get_step_description(2),
                "prefill_data": prefill_data,
                "extraction_metadata": {
                    "confidence_score": experience_data.get("confidence_score", 0.0),
                    "ai_provider": extraction_result.get("ai_provider", "unknown"),
                    "ai_model": extraction_result.get("ai_model", "unknown"),
                    "roles_extracted": len(experience_data.get("work_experience", []))
                },
                "data_saved": False
            }
        
    except Exception as e:
        logger.error(f"Step 2 processing failed: {e}")
        return {
            "success": False,
            "error": f"Experience step processing failed: {str(e)}",
            "step": 2,
            "step_name": "experience"
        }