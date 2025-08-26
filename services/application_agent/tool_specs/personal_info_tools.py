"""
Personal Information Tool Specifications

LLM tool specs for extracting personal contact information from resumes.
"""

from typing import Dict, Any

def get_personal_info_tool_spec() -> Dict[str, Any]:
    """
    Tool specification for extracting personal information from resume text.
    
    Returns tool spec that can be used with LLM agents to extract:
    - Full name, email, phone
    - Address information  
    - LinkedIn profile
    - Portfolio/website URLs
    """
    return {
        "name": "extract_personal_information",
        "description": "Extract personal contact information and basic details from resume text",
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {
                    "type": "string",
                    "description": "Complete full name of the candidate"
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Primary email address"
                },
                "phone": {
                    "type": "string", 
                    "description": "Primary phone number (formatted as found in resume)"
                },
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string", "description": "Street address"},
                        "city": {"type": "string", "description": "City"},
                        "state": {"type": "string", "description": "State or province"},
                        "country": {"type": "string", "description": "Country"},
                        "postal_code": {"type": "string", "description": "ZIP or postal code"}
                    },
                    "description": "Complete address information if available"
                },
                "linkedin_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "LinkedIn profile URL if mentioned"
                },
                "portfolio_url": {
                    "type": "string", 
                    "format": "uri",
                    "description": "Portfolio or personal website URL if mentioned"
                },
                "github_url": {
                    "type": "string",
                    "format": "uri", 
                    "description": "GitHub profile URL if mentioned"
                },
                "professional_title": {
                    "type": "string",
                    "description": "Current professional title or desired position"
                },
                "summary": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Professional summary or objective statement if present"
                },
                "confidence_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "LLM confidence in the extracted personal information"
                }
            },
            "required": ["full_name", "confidence_score"]
        }
    }