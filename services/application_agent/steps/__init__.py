"""
Application Step Handlers

Individual step processors for the 6-step application wizard.
Each step handles LLM extraction, data validation, and persistence.
"""

from .step1_personal_info import handle_personal_info_step
from .step2_experience import handle_experience_step  
from .step3_questions import handle_questions_step
from .step4_disclosures import handle_disclosures_step
from .step5_identity import handle_identity_step
from .step6_review import handle_review_step

# Step handler mapping
STEP_HANDLERS = {
    1: handle_personal_info_step,
    2: handle_experience_step,
    3: handle_questions_step, 
    4: handle_disclosures_step,
    5: handle_identity_step,
    6: handle_review_step
}

def get_step_handler(step: int):
    """Get handler function for specific step."""
    if step not in STEP_HANDLERS:
        raise ValueError(f"Invalid step: {step}")
    return STEP_HANDLERS[step]

__all__ = [
    "handle_personal_info_step",
    "handle_experience_step",
    "handle_questions_step", 
    "handle_disclosures_step",
    "handle_identity_step",
    "handle_review_step",
    "get_step_handler",
    "STEP_HANDLERS"
]