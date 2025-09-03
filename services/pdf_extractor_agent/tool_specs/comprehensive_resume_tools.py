"""
Comprehensive Resume Tool Specifications

Tool spec for extracting complete personal info and experience data 
for application Steps 1 & 2 prefill.
"""

from typing import Dict, Any

def get_comprehensive_resume_tool_spec() -> Dict[str, Any]:
    """
    Tool specification for extracting comprehensive resume data for application prefill.
    
    Combines Step 1 (personal info) and Step 2 (experience) requirements into a 
    single comprehensive extraction tool.
    
    Returns:
        Dict with tool spec for LLM agents to extract complete application data
    """
    return {
        "name": "extract_comprehensive_resume_data",
        "description": "Extract complete personal information and experience data for job application prefill",
        "input_schema": {
            "type": "object",
            "properties": {
                "personal_info": {
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
                            "maxLength": 300,
                            "description": "Brief professional summary (2-3 sentences, max 300 chars)"
                        },
                        "confidence_score": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "LLM confidence in the extracted personal information"
                        }
                    },
                    "required": ["full_name", "confidence_score"],
                    "description": "Step 1: Personal contact information and basic details"
                },
                "experience_info": {
                    "type": "object",
                    "properties": {
                        "work_experience": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "job_title": {
                                        "type": "string",
                                        "description": "Job title or position"
                                    },
                                    "company_name": {
                                        "type": "string", 
                                        "description": "Company or organization name"
                                    },
                                    "location": {
                                        "type": "string",
                                        "description": "Job location (city, state/country)"
                                    },
                                    "start_date": {
                                        "type": "string",
                                        "description": "Employment start date (MM/YYYY format preferred)"
                                    },
                                    "end_date": {
                                        "type": "string", 
                                        "description": "Employment end date (MM/YYYY format, or 'Present' if current)"
                                    },
                                    "is_current": {
                                        "type": "boolean",
                                        "description": "True if this is current employment"
                                    },
                                    "responsibilities": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Key responsibilities and achievements"
                                    },
                                    "skills_used": {
                                        "type": "array", 
                                        "items": {"type": "string"},
                                        "description": "Technologies, tools, and skills used in this role"
                                    }
                                },
                                "required": ["job_title", "company_name"]
                            },
                            "description": "Complete work history in reverse chronological order"
                        },
                        "total_years_experience": {
                            "type": "number",
                            "description": "Total years of professional work experience"
                        },
                        "current_salary": {
                            "type": "string",
                            "description": "Current or most recent salary if mentioned"
                        },
                        "salary_expectations": {
                            "type": "string", 
                            "description": "Salary expectations if mentioned"
                        },
                        "professional_summary": {
                            "type": "string",
                            "maxLength": 500,
                            "description": "Comprehensive professional summary from resume"
                        },
                        "key_skills": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 20,
                            "description": "Top technical skills and competencies across all experience"
                        },
                        "soft_skills": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "maxItems": 10,
                            "description": "Soft skills inferred from leadership roles, achievements, and experience"
                        },
                        "education": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "degree": {
                                        "type": "string",
                                        "description": "Degree or certification name"
                                    },
                                    "institution": {
                                        "type": "string", 
                                        "description": "School, university, or certifying body"
                                    },
                                    "year": {
                                        "type": "string",
                                        "description": "Graduation year or date if available"
                                    },
                                    "field_of_study": {
                                        "type": "string",
                                        "description": "Major, field of study, or specialization"
                                    }
                                },
                                "required": ["degree", "institution"]
                            },
                            "description": "Education history and certifications"
                        },
                        "industries": {
                            "type": "array",
                            "items": {"type": "string"}, 
                            "description": "Industries and sectors worked in"
                        },
                        "management_experience": {
                            "type": "boolean",
                            "description": "True if candidate has management or leadership experience"
                        },
                        "confidence_score": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "LLM confidence in the extracted experience information"
                        }
                    },
                    "required": ["work_experience", "confidence_score"],
                    "description": "Step 2: Comprehensive work experience and professional background"
                }
            },
            "required": ["personal_info", "experience_info"]
        }
    }