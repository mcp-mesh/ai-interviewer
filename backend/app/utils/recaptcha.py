"""
reCAPTCHA verification utility for Google reCAPTCHA v3
"""

import logging
import os
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)

# reCAPTCHA v3 verification endpoint
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"

# Minimum score for reCAPTCHA v3 (0.0 is very likely a bot, 1.0 is very likely human)
MIN_RECAPTCHA_SCORE = 0.5


async def verify_recaptcha_token(token: str, expected_action: str = "upload_resume") -> Dict[str, any]:
    """
    Verify Google reCAPTCHA v3 token with Google's API.
    
    Args:
        token: The reCAPTCHA response token from the frontend
        expected_action: The expected action name (should match frontend)
        
    Returns:
        Dict with verification results:
        - success: bool - whether verification passed
        - score: float - reCAPTCHA score (0.0 to 1.0)
        - action: str - action name from token
        - error: str - error message if verification failed
    """
    # TODO: Re-enable reCAPTCHA verification for production
    # Temporarily disabled for testing resume upload functionality
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
    if dev_mode:
        logger.info("DEV_MODE: Skipping reCAPTCHA verification for testing")
        return {
            "success": True,
            "score": 0.9,
            "action": expected_action
        }
    
    secret_key = os.getenv("RECAPTCHA_SECRET_KEY")
    if not secret_key:
        logger.error("RECAPTCHA_SECRET_KEY environment variable not set")
        return {
            "success": False,
            "error": "reCAPTCHA verification not configured"
        }
    
    if not token:
        return {
            "success": False,
            "error": "reCAPTCHA token is required"
        }
    
    try:
        # Prepare verification request
        data = {
            "secret": secret_key,
            "response": token
        }
        
        # Make verification request to Google
        logger.info(f"Verifying reCAPTCHA token for action: {expected_action}")
        response = requests.post(RECAPTCHA_VERIFY_URL, data=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"reCAPTCHA API response: {result}")
        
        # Check if verification succeeded
        if not result.get("success", False):
            error_codes = result.get("error-codes", [])
            logger.warning(f"reCAPTCHA verification failed with errors: {error_codes}")
            return {
                "success": False,
                "error": f"reCAPTCHA verification failed: {', '.join(error_codes)}"
            }
        
        # Extract score and action
        score = result.get("score", 0.0)
        action = result.get("action", "")
        
        # Verify action matches expected
        if expected_action and action != expected_action:
            logger.warning(f"reCAPTCHA action mismatch: expected {expected_action}, got {action}")
            return {
                "success": False,
                "error": f"Invalid reCAPTCHA action: expected {expected_action}, got {action}"
            }
        
        # Check score threshold
        if score < MIN_RECAPTCHA_SCORE:
            logger.warning(f"reCAPTCHA score too low: {score} < {MIN_RECAPTCHA_SCORE}")
            return {
                "success": False,
                "score": score,
                "action": action,
                "error": f"reCAPTCHA score too low: {score}. Please try again."
            }
        
        logger.info(f"reCAPTCHA verification successful: score={score}, action={action}")
        return {
            "success": True,
            "score": score,
            "action": action
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to verify reCAPTCHA token: {e}")
        return {
            "success": False,
            "error": "Failed to verify reCAPTCHA. Please try again."
        }
    except Exception as e:
        logger.error(f"Unexpected error verifying reCAPTCHA: {e}")
        return {
            "success": False,
            "error": "An unexpected error occurred. Please try again."
        }


def get_recaptcha_config() -> Dict[str, any]:
    """
    Get reCAPTCHA configuration for frontend.
    
    Returns:
        Dict with reCAPTCHA configuration
    """
    site_key = os.getenv("RECAPTCHA_SITE_KEY")
    return {
        "site_key": site_key,
        "enabled": bool(site_key),
        "min_score": MIN_RECAPTCHA_SCORE
    }