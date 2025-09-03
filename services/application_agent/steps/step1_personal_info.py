"""
Step 1: Personal Information Handler

Handles extraction, validation, and saving of personal contact information.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..database import get_db_session, ApplicationPersonalInfo
# Tool spec import removed - using detailed analysis from user agent
from ..utils.step_management import get_step_title, get_step_description

logger = logging.getLogger(__name__)

# LLM extraction function removed - using detailed analysis from user agent

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
    detailed_analysis: Dict[str, Any] = None,
    step_data: Dict[str, Any] = None,
    save_data: bool = True
) -> Dict[str, Any]:
    """
    Handle Step 1: Personal Information processing.
    
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
        
        # Mode 2: Generate prefill from detailed analysis
        else:
            logger.info("Mode: Generating prefill from detailed analysis")
            
            # Check if detailed analysis is available
            if not detailed_analysis or not detailed_analysis.get("has_detailed_analysis"):
                return {
                    "success": False,
                    "error": "No detailed resume analysis available for prefill",
                    "step": 1,
                    "step_name": "personal_info"
                }
            
            # Use pre-analyzed personal data directly
            personal_data = detailed_analysis.get("personal_info", {})
            
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
                    "ai_provider": detailed_analysis.get("analysis_metadata", {}).get("ai_provider", "unknown"),
                    "ai_model": detailed_analysis.get("analysis_metadata", {}).get("ai_model", "unknown"),
                    "source": "detailed_analysis"
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