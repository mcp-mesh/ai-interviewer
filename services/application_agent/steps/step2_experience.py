"""
Step 2: Experience Handler

Handles extraction, validation, and saving of work experience information.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import json

from ..database import get_db_session, ApplicationExperience
# Tool spec import removed - using detailed analysis from user agent
from ..utils.step_management import get_step_title, get_step_description

logger = logging.getLogger(__name__)

# LLM extraction function removed - using detailed analysis from user agent

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
    detailed_analysis: Dict[str, Any] = None,
    step_data: Dict[str, Any] = None,
    save_data: bool = True
) -> Dict[str, Any]:
    """
    Handle Step 2: Work Experience processing.
    
    Two modes:
    1. Generate prefill: detailed_analysis provided, step_data=None  
    2. Save user data: step_data provided, detailed_analysis optional
    
    Args:
        application_id: Application ID
        detailed_analysis: Pre-analyzed resume data (for prefill generation)
        step_data: User-submitted data to save (for save mode)
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
        
        # Mode 2: Generate prefill from detailed analysis
        else:
            logger.info("Mode: Generating prefill from detailed analysis")
            
            # Check if detailed analysis is available
            if not detailed_analysis or not detailed_analysis.get("has_detailed_analysis"):
                return {
                    "success": False,
                    "error": "No detailed resume analysis available for prefill",
                    "step": 2,
                    "step_name": "experience"
                }
            
            # Use pre-analyzed experience data directly
            experience_data = detailed_analysis.get("experience_info", {})
            
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
                    "ai_provider": detailed_analysis.get("analysis_metadata", {}).get("ai_provider", "unknown"),
                    "ai_model": detailed_analysis.get("analysis_metadata", {}).get("ai_model", "unknown"),
                    "roles_extracted": len(experience_data.get("work_experience", [])),
                    "source": "detailed_analysis"
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