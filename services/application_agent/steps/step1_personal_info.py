"""
Step 1: Personal Information Handler

Handles extraction, validation, and saving of personal contact information.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..database import get_db_session, ApplicationPersonalInfo
from ..tool_specs.personal_info_tools import get_personal_info_tool_spec
from ..utils.step_management import get_step_title, get_step_description

logger = logging.getLogger(__name__)

async def extract_personal_info_with_llm(
    resume_text: str,
    llm_service,
    convert_tool_format
) -> Dict[str, Any]:
    """
    Extract personal information from resume text using LLM.
    
    Args:
        resume_text: Raw resume text content
        llm_service: LLM agent for processing
        convert_tool_format: Tool format converter
        
    Returns:
        Dict with extracted personal information or error
    """
    try:
        logger.info("Extracting personal information using LLM")
        
        # Get tool specification
        personal_info_tool = get_personal_info_tool_spec()
        
        # Convert tools to appropriate format for the LLM provider
        converted_tools = [personal_info_tool]
        if convert_tool_format:
            try:
                converted_tools = await convert_tool_format(tools=[personal_info_tool])
                logger.info("Successfully converted personal info tool for LLM provider")
            except Exception as e:
                logger.warning(f"Tool conversion failed, using original format: {e}")
        
        # Create system prompt for personal information extraction
        system_prompt = f"""You are a professional resume parser. Extract personal contact information from the provided resume text.

RESUME TEXT:
{resume_text[:2000]}{'...' if len(resume_text) > 2000 else ''}

Instructions:
- Extract the candidate's full name, email, and phone number
- Parse complete address if available (street, city, state, country, postal code)
- Find LinkedIn, portfolio, or GitHub URLs if mentioned
- Identify professional title or current position
- Extract professional summary or objective if present
- Be conservative with extraction - only include information that is clearly present
- Rate your confidence in the extraction accuracy (0.0-1.0)

Use the provided tool to return the extracted information in structured format."""

        # Call LLM service
        logger.info(f"Calling LLM service for personal info extraction")
        result = await llm_service(
            text="Extract personal information from this resume using the provided tool.",
            system_prompt=system_prompt,
            messages=[],
            tools=converted_tools,
            force_tool_use=True,
            temperature=0.1
        )
        
        if result and result.get("success") and result.get("tool_calls"):
            tool_calls = result.get("tool_calls", [])
            if len(tool_calls) > 0:
                personal_data = tool_calls[0].get("parameters", {})
                logger.info(f"Successfully extracted personal info - confidence: {personal_data.get('confidence_score', 'N/A')}")
                return {
                    "success": True,
                    "data": personal_data,
                    "ai_provider": result.get("provider", "unknown"),
                    "ai_model": result.get("model", "unknown")
                }
        
        logger.warning("LLM failed to extract personal information")
        return {
            "success": False,
            "error": "Failed to extract personal information from resume"
        }
        
    except Exception as e:
        logger.error(f"Personal info extraction failed: {e}")
        return {
            "success": False,
            "error": f"Personal info extraction error: {str(e)}"
        }

async def save_personal_info_data(
    application_id: str,
    personal_data: Dict[str, Any]
) -> bool:
    """
    Save personal information to database.
    
    Args:
        application_id: Application ID
        personal_data: Personal information data (matches our API format)
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        with get_db_session() as db_session:
            # Check if personal info already exists
            existing_info = db_session.query(ApplicationPersonalInfo).filter(
                ApplicationPersonalInfo.application_id == application_id
            ).first()
            
            # Extract and process data
            address_data = personal_data.get("address", {})
            
            # Split full_name into first_name and last_name for database
            full_name = personal_data.get("full_name", "")
            name_parts = full_name.split(" ", 1) if full_name else ["", ""]
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            if existing_info:
                # Update existing record
                existing_info.first_name = first_name
                existing_info.last_name = last_name
                existing_info.email = personal_data.get("email", "")
                existing_info.phone = personal_data.get("phone", "")
                existing_info.street = address_data.get("street", "")
                existing_info.city = address_data.get("city", "")
                existing_info.state = address_data.get("state", "")
                existing_info.country = address_data.get("country", "")
                existing_info.zip_code = address_data.get("postal_code", "")
                existing_info.linkedin = personal_data.get("linkedin_url", "")
                existing_info.updated_at = datetime.utcnow()
                logger.info(f"Updated existing personal info for application {application_id}")
            else:
                # Create new record
                personal_info = ApplicationPersonalInfo(
                    application_id=application_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=personal_data.get("email", ""),
                    phone=personal_data.get("phone", ""),
                    street=address_data.get("street", ""),
                    city=address_data.get("city", ""),
                    state=address_data.get("state", ""),
                    country=address_data.get("country", ""),
                    zip_code=address_data.get("postal_code", ""),
                    linkedin=personal_data.get("linkedin_url", "")
                )
                db_session.add(personal_info)
                logger.info(f"Created new personal info for application {application_id}")
            
            db_session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to save personal info data: {e}")
        return False

async def handle_personal_info_step(
    application_id: str,
    resume_text: str = "",
    step_data: Dict[str, Any] = None,
    llm_service=None,
    convert_tool_format=None,
    save_data: bool = True
) -> Dict[str, Any]:
    """
    Handle Step 1: Personal Information processing.
    
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
        logger.info(f"Processing Step 1 (Personal Info) for application {application_id}")
        
        # Mode 1: Save user-submitted data
        if step_data:
            logger.info("Mode: Saving user-submitted personal info data")
            
            # Save user data to database
            if save_data:
                save_success = await save_personal_info_data(application_id, step_data)
                if not save_success:
                    return {
                        "success": False,
                        "error": "Failed to save personal information",
                        "step": 1,
                        "step_name": "personal_info"
                    }
            
            return {
                "success": True,
                "step": 1,
                "step_name": "personal_info",
                "step_title": get_step_title(1),
                "step_description": get_step_description(1),
                "data_saved": True,
                "message": "Personal information saved successfully"
            }
        
        # Mode 2: Generate prefill from resume
        else:
            logger.info("Mode: Generating prefill from resume text")
            
            # Extract personal information using LLM
            extraction_result = await extract_personal_info_with_llm(
                resume_text, llm_service, convert_tool_format
            )
            
            if not extraction_result.get("success"):
                return {
                    "success": False,
                    "error": extraction_result.get("error", "Failed to extract personal information"),
                    "step": 1,
                    "step_name": "personal_info"
                }
            
            personal_data = extraction_result["data"]
            
            # Format prefill data for frontend
            prefill_data = {
                "full_name": personal_data.get("full_name", ""),
                "email": personal_data.get("email", ""),
                "phone": personal_data.get("phone", ""),
                "address": {
                    "street": personal_data.get("address", {}).get("street", ""),
                    "city": personal_data.get("address", {}).get("city", ""),
                    "state": personal_data.get("address", {}).get("state", ""),
                    "country": personal_data.get("address", {}).get("country", ""),
                    "postal_code": personal_data.get("address", {}).get("postal_code", "")
                },
                "linkedin_url": personal_data.get("linkedin_url", ""),
                "portfolio_url": personal_data.get("portfolio_url", ""),
                "github_url": personal_data.get("github_url", ""),
                "professional_title": personal_data.get("professional_title", ""),
                "summary": personal_data.get("summary", "")
            }
            
            logger.info(f"Successfully generated prefill for Step 1, application {application_id}")
            
            return {
                "success": True,
                "step": 1,
                "step_name": "personal_info",
                "step_title": get_step_title(1),
                "step_description": get_step_description(1),
                "prefill_data": prefill_data,
                "extraction_metadata": {
                    "confidence_score": personal_data.get("confidence_score", 0.0),
                    "ai_provider": extraction_result.get("ai_provider", "unknown"),
                    "ai_model": extraction_result.get("ai_model", "unknown")
                },
                "data_saved": False
            }
        
    except Exception as e:
        logger.error(f"Step 1 processing failed: {e}")
        return {
            "success": False,
            "error": f"Personal info step processing failed: {str(e)}",
            "step": 1,
            "step_name": "personal_info"
        }