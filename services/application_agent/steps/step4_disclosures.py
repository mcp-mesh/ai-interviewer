"""
Step 4: Disclosures Handler

Handles extraction and saving of legal disclosure information.
"""

import logging
from typing import Dict, Any
from datetime import datetime
import json

from ..database import get_db_session, ApplicationDisclosures
from ..tool_specs.disclosures_tools import get_disclosures_tool_spec
from ..utils.step_management import get_step_title, get_step_description

logger = logging.getLogger(__name__)

async def extract_disclosures_with_llm(
    resume_text: str,
    llm_service,
    convert_tool_format
) -> Dict[str, Any]:
    """Extract disclosure-related information from resume text using LLM."""
    try:
        logger.info("Extracting disclosures information using LLM")
        
        disclosures_tool = get_disclosures_tool_spec()
        
        converted_tools = [disclosures_tool]
        if convert_tool_format:
            try:
                converted_tools = await convert_tool_format(tools=[disclosures_tool])
                logger.info("Successfully converted disclosures tool for LLM provider")
            except Exception as e:
                logger.warning(f"Tool conversion failed, using original format: {e}")
        
        system_prompt = f"""Extract disclosure-related information from the resume text. Focus on extracting only what can be reasonably inferred from the resume.

RESUME TEXT:
{resume_text[:2500]}{'...' if len(resume_text) > 2500 else ''}

Instructions:
- Extract professional licenses, certifications, and credentials
- Identify educational qualifications and degrees
- Note security clearances if mentioned
- Infer work authorization hints based on education/work patterns (not definitive)
- List professional memberships and organizations
- Be conservative - only extract information that is clearly present
- Note limitations of what can be extracted from resume alone

Use the provided tool to return structured disclosure information."""

        result = await llm_service(
            text="Extract disclosure-related information from this resume using the provided tool.",
            system_prompt=system_prompt,
            messages=[],
            tools=converted_tools,
            force_tool_use=True,
            temperature=0.1
        )
        
        if result and result.get("success") and result.get("tool_calls"):
            tool_calls = result.get("tool_calls", [])
            if len(tool_calls) > 0:
                disclosures_data = tool_calls[0].get("parameters", {})
                logger.info(f"Successfully extracted disclosures - confidence: {disclosures_data.get('confidence_score', 'N/A')}")
                return {
                    "success": True,
                    "data": disclosures_data,
                    "ai_provider": result.get("provider", "unknown"),
                    "ai_model": result.get("model", "unknown")
                }
        
        logger.warning("LLM failed to extract disclosures information")
        return {
            "success": False,
            "error": "Failed to extract disclosures information from resume"
        }
        
    except Exception as e:
        logger.error(f"Disclosures extraction failed: {e}")
        return {
            "success": False,
            "error": f"Disclosures extraction error: {str(e)}"
        }

async def save_disclosures_data(
    application_id: str,
    disclosures_data: Dict[str, Any]
) -> bool:
    """
    Save disclosures information to database.
    
    Args:
        application_id: Application ID
        disclosures_data: Disclosures data (matches database schema)
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        with get_db_session() as db_session:
            existing_disclosures = db_session.query(ApplicationDisclosures).filter(
                ApplicationDisclosures.application_id == application_id
            ).first()
            
            if existing_disclosures:
                # Update existing record (matching database schema)
                existing_disclosures.government_employment = disclosures_data.get("government_employment", "prefer_not_to_say")
                existing_disclosures.non_compete = disclosures_data.get("non_compete", "prefer_not_to_say")
                existing_disclosures.previous_employment = disclosures_data.get("previous_employment", "prefer_not_to_say")
                existing_disclosures.previous_alias = disclosures_data.get("previous_alias", "")
                existing_disclosures.personnel_number = disclosures_data.get("personnel_number", "")
                existing_disclosures.updated_at = datetime.utcnow()
                logger.info(f"Updated existing disclosures data for application {application_id}")
            else:
                # Create new record (matching database schema)
                disclosures_record = ApplicationDisclosures(
                    application_id=application_id,
                    government_employment=disclosures_data.get("government_employment", "prefer_not_to_say"),
                    non_compete=disclosures_data.get("non_compete", "prefer_not_to_say"),
                    previous_employment=disclosures_data.get("previous_employment", "prefer_not_to_say"),
                    previous_alias=disclosures_data.get("previous_alias", ""),
                    personnel_number=disclosures_data.get("personnel_number", "")
                )
                db_session.add(disclosures_record)
                logger.info(f"Created new disclosures record for application {application_id}")
            
            db_session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to save disclosures data: {e}")
        return False

async def handle_disclosures_step(
    application_id: str,
    resume_text: str = "",
    step_data: Dict[str, Any] = None,
    llm_service=None,
    convert_tool_format=None,
    save_data: bool = True
) -> Dict[str, Any]:
    """
    Handle Step 4: Disclosures processing.
    
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
        logger.info(f"Processing Step 4 (Disclosures) for application {application_id}")
        
        # Mode 1: Save user-submitted data
        if step_data:
            logger.info("Mode: Saving user-submitted disclosures data")
            
            # Save user data to database
            if save_data:
                save_success = await save_disclosures_data(application_id, step_data)
                if not save_success:
                    return {
                        "success": False,
                        "error": "Failed to save disclosures information",
                        "step": 4,
                        "step_name": "disclosures"
                    }
            
            return {
                "success": True,
                "step": 4,
                "step_name": "disclosures",
                "step_title": get_step_title(4),
                "step_description": get_step_description(4),
                "data_saved": True,
                "message": "Disclosures information saved successfully"
            }
        
        # Mode 2: Return empty prefill data (no LLM extraction for Step 4)
        else:
            logger.info("Mode: Returning empty prefill data for Step 4 (no LLM extraction)")
            
            # Return empty prefill data - user will fill voluntary disclosures manually
            prefill_data = {
                "government_employment": "prefer_not_to_say",
                "non_compete": "prefer_not_to_say", 
                "previous_employment": "prefer_not_to_say",
                "previous_alias": "",
                "personnel_number": ""
            }
            
            logger.info(f"Successfully returned empty prefill for Step 4, application {application_id}")
            
            return {
                "success": True,
                "step": 4,
                "step_name": "disclosures",
                "step_title": get_step_title(4),
                "step_description": get_step_description(4),
                "prefill_data": prefill_data,
                "extraction_metadata": {
                    "confidence_score": 0.0,
                    "ai_provider": "none",
                    "ai_model": "none",
                    "llm_skipped": True
                },
                "data_saved": False
            }
        
    except Exception as e:
        logger.error(f"Step 4 processing failed: {e}")
        return {
            "success": False,
            "error": f"Disclosures step processing failed: {str(e)}",
            "step": 4,
            "step_name": "disclosures"
        }