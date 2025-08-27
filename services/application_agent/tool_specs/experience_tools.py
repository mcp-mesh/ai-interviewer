"""
Experience Tool Specifications

LLM tool specs for extracting work experience information from resumes.
"""

from typing import Dict, Any

def get_experience_tool_spec() -> Dict[str, Any]:
    """
    Tool specification for extracting work experience from resume text.
    
    Returns tool spec that can be used with LLM agents to extract:
    - Employment history
    - Job titles and companies
    - Employment dates
    - Key responsibilities and achievements
    - Skills and technologies used
    """
    return {
        "name": "extract_work_experience", 
        "description": "Extract detailed work experience and employment history from resume text",
        "input_schema": {
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
                    "description": "List of work experiences in reverse chronological order"
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
                "summary": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Brief professional summary (2-3 sentences) from resume"
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
                            }
                        },
                        "required": ["degree", "institution"]
                    },
                    "description": "Education history and certifications"
                },
                "industries": {
                    "type": "array",
                    "items": {"type": "string"}, 
                    "description": "Industries worked in"
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
            "required": ["work_experience", "confidence_score"]
        }
    }