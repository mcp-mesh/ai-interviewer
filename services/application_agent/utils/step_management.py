"""
Step Management Utilities

Handles step flow logic, validation, and progression for the 6-step application wizard.
"""

from typing import Dict, Any, Optional
from enum import IntEnum

class ApplicationStep(IntEnum):
    """Application step enumeration"""
    PERSONAL_INFO = 1
    EXPERIENCE = 2
    QUESTIONS = 3
    DISCLOSURES = 4
    IDENTITY = 5
    REVIEW = 6

# Step configuration
STEP_CONFIG = {
    1: {
        "name": "personal_info",
        "title": "Personal Information",
        "description": "Basic contact and personal details"
    },
    2: {
        "name": "experience", 
        "title": "Work Experience",
        "description": "Professional background and employment history"
    },
    3: {
        "name": "questions",
        "title": "Application Questions", 
        "description": "Job-specific questions and responses"
    },
    4: {
        "name": "disclosures",
        "title": "Legal Disclosures",
        "description": "Background checks and legal requirements"
    },
    5: {
        "name": "identity",
        "title": "Identity Verification",
        "description": "Identity documents and verification"
    },
    6: {
        "name": "review",
        "title": "Review & Submit",
        "description": "Final review and application submission"
    }
}

def validate_step(step: int) -> bool:
    """Validate if step number is valid."""
    return step in STEP_CONFIG

def get_step_name(step: int) -> str:
    """Get step name from step number."""
    if not validate_step(step):
        raise ValueError(f"Invalid step: {step}")
    return STEP_CONFIG[step]["name"]

def get_step_title(step: int) -> str:
    """Get step title from step number."""
    if not validate_step(step):
        raise ValueError(f"Invalid step: {step}")
    return STEP_CONFIG[step]["title"]

def get_step_description(step: int) -> str:
    """Get step description from step number."""
    if not validate_step(step):
        raise ValueError(f"Invalid step: {step}")
    return STEP_CONFIG[step]["description"]

def get_next_step(current_step: int) -> Optional[int]:
    """Get next step number, or None if at final step."""
    if not validate_step(current_step):
        raise ValueError(f"Invalid current step: {current_step}")
    
    if current_step >= 6:
        return None  # Final step reached
    
    return current_step + 1

def get_previous_step(current_step: int) -> Optional[int]:
    """Get previous step number, or None if at first step."""
    if not validate_step(current_step):
        raise ValueError(f"Invalid current step: {current_step}")
    
    if current_step <= 1:
        return None  # First step
    
    return current_step - 1

def is_final_step(step: int) -> bool:
    """Check if this is the final step."""
    return step == 6

def get_step_progress_percentage(step: int) -> float:
    """Get completion percentage for current step."""
    if not validate_step(step):
        raise ValueError(f"Invalid step: {step}")
    
    return (step / 6.0) * 100

def get_all_steps_info() -> Dict[int, Dict[str, Any]]:
    """Get information for all steps."""
    return STEP_CONFIG.copy()