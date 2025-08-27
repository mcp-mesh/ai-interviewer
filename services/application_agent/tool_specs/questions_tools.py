"""
Questions Tool Specifications

LLM tool specs for generating responses to job-specific application questions.
"""

from typing import Dict, Any, List

def get_questions_tool_spec(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tool specification for generating responses to job-specific questions.
    
    Args:
        questions: List of job-specific questions from the job posting
        
    Returns tool spec that can be used with LLM agents to generate:
    - Thoughtful responses based on resume experience
    - Cover letter content
    - Motivation and interest statements
    """
    
    # Build dynamic properties based on the questions provided
    question_properties = {}
    required_fields = []
    
    for i, question in enumerate(questions, 1):
        question_key = f"question_{i}_response"
        question_text = question.get("question", "")
        question_type = question.get("type", "text")
        is_required = question.get("required", False)
        
        if question_type == "text":
            question_properties[question_key] = {
                "type": "string",
                "maxLength": 2000,
                "description": f"Response to: {question_text}"
            }
        elif question_type == "boolean":
            question_properties[question_key] = {
                "type": "boolean", 
                "description": f"Yes/No response to: {question_text}"
            }
        elif question_type == "multiple_choice":
            choices = question.get("choices", [])
            question_properties[question_key] = {
                "type": "string",
                "enum": choices,
                "description": f"Select one option for: {question_text}"
            }
        
        if is_required:
            required_fields.append(question_key)
    
    # Add standard fields
    question_properties.update({
        "cover_letter": {
            "type": "string",
            "maxLength": 1500,
            "description": "Professional cover letter based on resume experience and job requirements"
        },
        "why_interested": {
            "type": "string", 
            "maxLength": 500,
            "description": "Why the candidate is interested in this specific role and company"
        },
        "unique_qualifications": {
            "type": "string",
            "maxLength": 500,
            "description": "What makes this candidate uniquely qualified for the role"
        },
        "confidence_score": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "LLM confidence in the generated responses"
        }
    })
    
    required_fields.extend(["confidence_score"])
    
    return {
        "name": "generate_application_responses",
        "description": "Generate thoughtful responses to job application questions based on resume experience",
        "input_schema": {
            "type": "object", 
            "properties": question_properties,
            "required": required_fields
        }
    }

def get_generic_questions_tool_spec() -> Dict[str, Any]:
    """
    Generic questions tool spec for when specific job questions aren't available.
    """
    return {
        "name": "generate_generic_application_responses",
        "description": "Generate standard application responses based on resume experience",
        "input_schema": {
            "type": "object",
            "properties": {
                "cover_letter": {
                    "type": "string",
                    "maxLength": 1500, 
                    "description": "Professional cover letter highlighting relevant experience"
                },
                "career_objective": {
                    "type": "string",
                    "maxLength": 300,
                    "description": "Career objective and goals"
                },
                "why_this_role": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Why interested in this type of role"
                },
                "key_strengths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5,
                    "description": "Top 5 professional strengths based on experience"
                },
                "availability": {
                    "type": "string",
                    "description": "Availability to start work"
                },
                "work_authorization": {
                    "type": "string",
                    "enum": ["yes", "no", "unknown"],
                    "description": "Whether candidate is authorized to work in the country"
                },
                "visa_sponsorship": {
                    "type": "string",
                    "enum": ["yes", "no", "unknown"],
                    "description": "Whether candidate would require visa sponsorship"
                },
                "relocate": {
                    "type": "string", 
                    "enum": ["yes", "no", "maybe"],
                    "description": "Willingness to relocate for the position"
                },
                "remote_work": {
                    "type": "string",
                    "enum": ["onsite", "remote", "hybrid"],
                    "description": "Preferred work arrangement (onsite/remote/hybrid)"
                },
                "preferred_location": {
                    "type": "string",
                    "maxLength": 100,
                    "description": "Preferred work location or city if mentioned in resume or can be inferred"
                },
                "salary_min": {
                    "type": "string",
                    "description": "Minimum salary expectation if mentioned or can be reasonably inferred from experience level"
                },
                "salary_max": {
                    "type": "string", 
                    "description": "Maximum salary expectation if mentioned or can be reasonably inferred from experience level"
                },
                "confidence_score": {
                    "type": "number",
                    "minimum": 0.0, 
                    "maximum": 1.0,
                    "description": "LLM confidence in the generated responses"
                }
            },
            "required": ["cover_letter", "confidence_score"]
        }
    }