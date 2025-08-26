"""
Tool Specifications for LLM Integration

Standardized tool definitions for extracting information from resume text.
Each module contains tool specs for specific application steps.
"""

from .personal_info_tools import get_personal_info_tool_spec
from .experience_tools import get_experience_tool_spec
from .questions_tools import get_questions_tool_spec
from .disclosures_tools import get_disclosures_tool_spec
from .identity_tools import get_identity_tool_spec

__all__ = [
    "get_personal_info_tool_spec",
    "get_experience_tool_spec", 
    "get_questions_tool_spec",
    "get_disclosures_tool_spec",
    "get_identity_tool_spec"
]