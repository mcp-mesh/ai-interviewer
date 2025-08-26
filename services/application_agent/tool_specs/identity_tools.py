"""
Identity Tool Specifications

LLM tool specs for identity verification information.
"""

from typing import Dict, Any

def get_identity_tool_spec() -> Dict[str, Any]:
    """
    Tool specification for extracting identity-related information from resume text.
    
    Returns tool spec that can be used with LLM agents to infer:
    - Name variations and preferred names
    - Contact information consistency
    - Professional identity markers
    
    Note: Most identity verification requires official documents and cannot be 
    extracted from resumes. This tool focuses on professional identity consistency.
    """
    return {
        "name": "extract_identity_information",
        "description": "Extract professional identity and consistency information from resume text",
        "input_schema": {
            "type": "object",
            "properties": {
                "name_variations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Different name variations found in the resume (full name, nicknames, initials)"
                },
                "preferred_name": {
                    "type": "string",
                    "description": "Preferred or most commonly used name format"
                },
                "professional_name": {
                    "type": "string",
                    "description": "Name used in professional contexts"
                },
                "contact_consistency": {
                    "type": "object",
                    "properties": {
                        "email_consistent": {"type": "boolean", "description": "Whether email addresses are consistent"},
                        "phone_consistent": {"type": "boolean", "description": "Whether phone numbers are consistent"},
                        "address_consistent": {"type": "boolean", "description": "Whether addresses appear consistent"}
                    },
                    "description": "Consistency check of contact information across resume"
                },
                "professional_profiles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "platform": {"type": "string", "description": "Platform name (LinkedIn, GitHub, etc.)"},
                            "url": {"type": "string", "description": "Profile URL"},
                            "username": {"type": "string", "description": "Username/handle if extractable"}
                        },
                        "required": ["platform", "url"]
                    },
                    "description": "Professional online profiles mentioned"
                },
                "identity_confidence": {
                    "type": "object",
                    "properties": {
                        "name_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "Confidence in name extraction"},
                        "contact_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "Confidence in contact information"},
                        "profile_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "Confidence in profile information"}
                    },
                    "description": "Confidence levels for different identity aspects"
                },
                "potential_issues": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Any potential inconsistencies or issues found in identity information"
                },
                "document_requirements": {
                    "type": "object",
                    "properties": {
                        "requires_government_id": {"type": "boolean", "description": "Whether official government ID will be needed"},
                        "requires_work_authorization": {"type": "boolean", "description": "Whether work authorization documents will be needed"},
                        "requires_background_check": {"type": "boolean", "description": "Whether background check documents will be needed"}
                    },
                    "description": "Document requirements that cannot be satisfied by resume alone"
                },
                "confidence_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Overall LLM confidence in the extracted identity information"
                },
                "verification_note": {
                    "type": "string",
                    "description": "Note explaining that identity verification requires official documents beyond resume"
                }
            },
            "required": ["preferred_name", "confidence_score", "verification_note"]
        }
    }