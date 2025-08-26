"""
Response Formatting Utilities

Standardized response formatting for all application agent endpoints.
"""

from typing import Dict, Any, Optional
from datetime import datetime

def format_success_response(
    data: Dict[str, Any],
    message: str = "Operation completed successfully"
) -> Dict[str, Any]:
    """Format a successful response."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

def format_error_response(
    error: str,
    error_code: str = "GENERAL_ERROR",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format an error response."""
    response = {
        "success": False,
        "error": error,
        "error_code": error_code,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response

def format_prefill_response(
    target_step: int,
    prefill_data: Dict[str, Any],
    application_id: str,
    step_info: Dict[str, Any],
    message: str = "Prefill data generated successfully"
) -> Dict[str, Any]:
    """Format a prefill response for step navigation."""
    return {
        "success": True,
        "message": message,
        "data": {
            "application_id": application_id,
            "target_step": target_step,
            "step_info": step_info,
            "prefill_data": prefill_data,
            "progress_percentage": (target_step / 6.0) * 100
        },
        "timestamp": datetime.now().isoformat()
    }

def format_step_save_response(
    next_step: Optional[int],
    prefill_data: Optional[Dict[str, Any]],
    application_id: str,
    saved_step: int,
    is_final: bool = False,
    message: str = "Step saved successfully"
) -> Dict[str, Any]:
    """Format a step save response."""
    data = {
        "application_id": application_id,
        "saved_step": saved_step,
        "is_final": is_final
    }
    
    if not is_final and next_step:
        data.update({
            "next_step": next_step,
            "prefill_data": prefill_data,
            "progress_percentage": (next_step / 6.0) * 100
        })
    else:
        data["progress_percentage"] = 100
    
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

def format_application_status_response(
    application: Dict[str, Any],
    message: str = "Application status retrieved"
) -> Dict[str, Any]:
    """Format application status response."""
    return {
        "success": True,
        "message": message,
        "data": {
            "application": application,
            "progress_percentage": (application.get("step", 1) / 6.0) * 100
        },
        "timestamp": datetime.now().isoformat()
    }