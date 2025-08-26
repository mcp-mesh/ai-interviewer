"""
Disclosures Tool Specifications

LLM tool specs for handling legal disclosures and background information.
"""

from typing import Dict, Any

def get_disclosures_tool_spec() -> Dict[str, Any]:
    """
    Tool specification for extracting disclosure-related information from resume text.
    
    Returns tool spec that can be used with LLM agents to infer:
    - Work authorization status
    - Background check eligibility  
    - Professional licenses and certifications
    - Educational credentials
    
    Note: Most disclosure information cannot be inferred from resumes and requires
    explicit user input. This tool focuses on what can reasonably be extracted.
    """
    return {
        "name": "extract_disclosure_information",
        "description": "Extract disclosure-related information that can be inferred from resume text",
        "input_schema": {
            "type": "object",
            "properties": {
                "professional_licenses": {
                    "type": "array",
                    "items": {
                        "type": "object", 
                        "properties": {
                            "license_name": {"type": "string", "description": "Name of the license or certification"},
                            "issuing_organization": {"type": "string", "description": "Organization that issued the license"},
                            "license_number": {"type": "string", "description": "License number if provided"},
                            "expiration_date": {"type": "string", "description": "Expiration date if mentioned"},
                            "status": {"type": "string", "enum": ["active", "expired", "pending", "unknown"], "description": "License status"}
                        },
                        "required": ["license_name"]
                    },
                    "description": "Professional licenses and certifications mentioned in resume"
                },
                "certifications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "certification_name": {"type": "string", "description": "Name of the certification"},
                            "issuing_organization": {"type": "string", "description": "Certifying organization"},
                            "obtained_date": {"type": "string", "description": "Date obtained if mentioned"},
                            "expiration_date": {"type": "string", "description": "Expiration date if mentioned"}
                        },
                        "required": ["certification_name"]
                    },
                    "description": "Professional certifications listed in resume"
                },
                "education_credentials": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "degree_type": {"type": "string", "description": "Type of degree (Bachelor's, Master's, PhD, etc.)"},
                            "field_of_study": {"type": "string", "description": "Major or field of study"},
                            "institution": {"type": "string", "description": "Educational institution name"},
                            "graduation_year": {"type": "string", "description": "Year of graduation"},
                            "gpa": {"type": "string", "description": "GPA if mentioned"},
                            "honors": {"type": "string", "description": "Academic honors or distinctions"}
                        },
                        "required": ["degree_type", "institution"]
                    },
                    "description": "Educational qualifications and degrees"
                },
                "work_authorization_hints": {
                    "type": "object",
                    "properties": {
                        "likely_status": {
                            "type": "string",
                            "enum": ["likely_authorized", "likely_needs_sponsorship", "unclear"],
                            "description": "Inferred work authorization based on education/work history patterns"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Brief explanation of the inference"
                        }
                    },
                    "description": "Hints about work authorization status based on resume patterns (not definitive)"
                },
                "security_clearance": {
                    "type": "object",
                    "properties": {
                        "has_clearance": {"type": "boolean", "description": "Whether security clearance is mentioned"},
                        "clearance_level": {"type": "string", "description": "Level of security clearance if mentioned"},
                        "status": {"type": "string", "enum": ["active", "inactive", "pending", "unknown"], "description": "Clearance status"}
                    },
                    "description": "Security clearance information if mentioned"
                },
                "professional_memberships": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Professional organizations and memberships"
                },
                "confidence_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "LLM confidence in the extracted disclosure information"
                },
                "extraction_limitations": {
                    "type": "string",
                    "description": "Note about what disclosure information cannot be extracted from resume and requires user input"
                }
            },
            "required": ["confidence_score", "extraction_limitations"]
        }
    }