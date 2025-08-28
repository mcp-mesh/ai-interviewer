"""
Step 5: Identity Handler

Handles extraction and saving of identity verification information.
"""

import logging
from typing import Dict, Any
from datetime import datetime
import json

from ..database import get_db_session, ApplicationIdentity
# Tool spec import removed - using detailed analysis from user agent
from ..utils.step_management import get_step_title, get_step_description

logger = logging.getLogger(__name__)


async def save_identity_data(
    application_id: str,
    identity_data: Dict[str, Any]
) -> bool:
    """
    Save EEO identity information to database.
    
    Args:
        application_id: Application ID
        identity_data: EEO identity data (matches database schema)
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        with get_db_session() as db_session:
            existing_identity = db_session.query(ApplicationIdentity).filter(
                ApplicationIdentity.application_id == application_id
            ).first()
            
            if existing_identity:
                # Update existing record (matching EEO database schema)
                existing_identity.gender = identity_data.get("gender")
                existing_identity.race = identity_data.get("race", [])
                existing_identity.veteran_status = identity_data.get("veteran_status")
                existing_identity.disability = identity_data.get("disability")
                existing_identity.updated_at = datetime.utcnow()
                logger.info(f"Updated existing EEO identity data for application {application_id}")
            else:
                # Create new record (matching EEO database schema)
                identity_record = ApplicationIdentity(
                    application_id=application_id,
                    gender=identity_data.get("gender"),
                    race=identity_data.get("race", []),
                    veteran_status=identity_data.get("veteran_status"),
                    disability=identity_data.get("disability")
                )
                db_session.add(identity_record)
                logger.info(f"Created new EEO identity record for application {application_id}")
            
            db_session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to save EEO identity data: {e}")
        return False

async def handle_identity_step(
    application_id: str,
    detailed_analysis: Dict[str, Any] = None,
    step_data: Dict[str, Any] = None,
    save_data: bool = True
) -> Dict[str, Any]:
    """
    Handle Step 5: EEO Identity processing.
    
    IMPORTANT: This step does NOT use LLM extraction for privacy/security reasons.
    EEO identity data (gender, race, veteran status, disability) should only be 
    self-reported by users, never extracted from resumes.
    
    Two modes:
    1. Generate prefill: Returns empty prefill (no LLM used)
    2. Save user data: step_data provided (user self-reported EEO data)
    
    Args:
        application_id: Application ID
        resume_text: Resume text content (IGNORED - no LLM extraction)
        step_data: User-submitted EEO data to save (for save mode)
        llm_service: LLM agent (IGNORED - no LLM extraction)
        convert_tool_format: Tool format converter (IGNORED - no LLM extraction)
        save_data: Whether to save data to database
        
    Returns:
        Dict with empty prefill (privacy) or save confirmation
    """
    try:
        logger.info(f"Processing Step 5 (EEO Identity) for application {application_id}")
        
        # Mode 1: Save user-submitted EEO data
        if step_data:
            logger.info("Mode: Saving user-submitted EEO identity data")
            
            # Save user data to database
            if save_data:
                save_success = await save_identity_data(application_id, step_data)
                if not save_success:
                    return {
                        "success": False,
                        "error": "Failed to save EEO identity information",
                        "step": 5,
                        "step_name": "identity"
                    }
            
            return {
                "success": True,
                "step": 5,
                "step_name": "identity",
                "step_title": get_step_title(5),
                "step_description": get_step_description(5),
                "data_saved": True,
                "message": "EEO identity information saved successfully"
            }
        
        # Mode 2: Generate prefill (EMPTY - no LLM extraction for privacy)
        else:
            logger.info("Mode: Generating empty prefill for EEO identity (privacy protection)")
            
            # Return empty prefill for privacy - user must self-report EEO data
            prefill_data = {
                "gender": None,
                "race": [],
                "veteran_status": None,
                "disability": None,
                "privacy_notice": "EEO identity information is voluntary and self-reported only. This information will not be extracted from your resume for privacy protection."
            }
            
            logger.info(f"Successfully generated empty prefill for Step 5 (privacy protection)")
            
            return {
                "success": True,
                "step": 5,
                "step_name": "identity",
                "step_title": get_step_title(5),
                "step_description": get_step_description(5),
                "prefill_data": prefill_data,
                "extraction_metadata": {
                    "llm_used": False,
                    "privacy_protected": True,
                    "note": "EEO data requires user self-reporting only"
                },
                "data_saved": False
            }
        
    except Exception as e:
        logger.error(f"Step 5 processing failed: {e}")
        return {
            "success": False,
            "error": f"EEO identity step processing failed: {str(e)}",
            "step": 5,
            "step_name": "identity"
        }