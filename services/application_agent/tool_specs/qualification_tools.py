"""
Qualification Assessment Tool Specifications

LLM tool for assessing candidate qualifications against job requirements.
"""

from typing import Dict, Any

def get_qualification_tool_spec() -> Dict[str, Any]:
    """
    Get tool specification for LLM qualification assessment.
    
    Returns comprehensive qualification analysis tool spec.
    """
    return {
        "name": "assess_candidate_qualification",
        "description": "Assess candidate qualification based on application data, resume, and job requirements",
        "input_schema": {
            "type": "object",
            "properties": {
                "qualification_score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Overall qualification score (0-100) based on job requirements match"
                },
                "recommendation": {
                    "type": "string",
                    "enum": ["INTERVIEW", "HR_REVIEW", "REJECT"],
                    "description": "Recommendation: INTERVIEW (≥80%), HR_REVIEW (60-79%), REJECT (<60%)"
                },
                "key_matches": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key qualifications and skills that match job requirements"
                },
                "red_flags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Missing requirements, conflicts, or concerns identified"
                },
                "experience_assessment": {
                    "type": "object",
                    "properties": {
                        "years_match": {"type": "boolean", "description": "Does experience level meet requirements"},
                        "skills_match": {"type": "integer", "minimum": 0, "maximum": 100, "description": "Skills match percentage"},
                        "industry_fit": {"type": "string", "description": "Industry background alignment"}
                    },
                    "description": "Detailed experience evaluation"
                },
                "location_assessment": {
                    "type": "object", 
                    "properties": {
                        "work_authorization": {"type": "boolean", "description": "Has valid work authorization"},
                        "location_compatible": {"type": "boolean", "description": "Location preferences compatible"},
                        "remote_acceptable": {"type": "boolean", "description": "Remote work preferences align"}
                    },
                    "description": "Location and authorization assessment"
                },
                "salary_assessment": {
                    "type": "object",
                    "properties": {
                        "expectations_realistic": {"type": "boolean", "description": "Salary expectations realistic"},
                        "within_budget": {"type": "boolean", "description": "Expectations within budget range"}
                    },
                    "description": "Salary compatibility assessment"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Detailed reasoning for the qualification score and recommendation (2-3 paragraphs)"
                },
                "confidence_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "AI confidence in the assessment accuracy"
                }
            },
            "required": [
                "qualification_score", 
                "recommendation", 
                "key_matches", 
                "red_flags", 
                "reasoning",
                "confidence_score"
            ]
        }
    }