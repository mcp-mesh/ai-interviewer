"""
LLM-powered skill and experience extraction service.
"""

import logging
from typing import Dict, Any, Optional
from mesh.types import McpMeshAgent

logger = logging.getLogger(__name__)

class SkillExtractionService:
    """Service for extracting skills and experience from resumes using LLM."""
    
    @staticmethod
    async def extract_profile_data(resume_text: str, llm_service: McpMeshAgent) -> Dict[str, Any]:
        """Extract comprehensive professional profile from resume text."""
        
        tools = [{
            "name": "extract_professional_profile",
            "description": "Extract comprehensive professional profile from resume",
            "input_schema": {
                "type": "object",
                "properties": {
                    "overall_experience_level": {
                        "type": "string",
                        "enum": ["intern", "junior", "mid", "senior", "lead", "principal"],
                        "description": "Overall career level based on responsibilities and years"
                    },
                    "total_years_experience": {
                        "type": "integer",
                        "description": "Total years of professional experience",
                        "minimum": 0,
                        "maximum": 50
                    },
                    "skills": {
                        "type": "object",
                        "description": "Technical and soft skills with experience levels",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "level": {
                                    "type": "string",
                                    "enum": ["beginner", "junior", "mid", "senior", "expert"],
                                    "description": "Proficiency level in this skill"
                                },
                                "years": {
                                    "type": "integer",
                                    "description": "Years of experience with this skill",
                                    "minimum": 0,
                                    "maximum": 30
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                    "description": "Confidence in assessment (0-1)"
                                },
                                "context": {
                                    "type": "string",
                                    "description": "How this skill was used (brief context)",
                                    "maxLength": 200
                                }
                            },
                            "required": ["level", "years", "confidence"]
                        }
                    },
                    "leadership_experience": {
                        "type": "object",
                        "properties": {
                            "has_leadership": {"type": "boolean"},
                            "team_size_managed": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 1000
                            },
                            "leadership_years": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 30
                            },
                            "leadership_level": {
                                "type": "string",
                                "enum": ["none", "team_lead", "manager", "senior_manager", "director", "vp"]
                            }
                        },
                        "required": ["has_leadership"]
                    },
                    "career_progression": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "maxLength": 100},
                                "level": {
                                    "type": "string", 
                                    "enum": ["intern", "junior", "mid", "senior", "lead", "principal"]
                                },
                                "years": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 10
                                },
                                "company_size": {
                                    "type": "string",
                                    "enum": ["startup", "small", "medium", "large", "enterprise"]
                                }
                            },
                            "required": ["title", "level"]
                        },
                        "maxItems": 10
                    },
                    "preferred_next_levels": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["intern", "junior", "mid", "senior", "lead", "principal"]
                        },
                        "description": "What career levels this person should target next",
                        "maxItems": 3
                    },
                    "categories_of_interest": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["engineering", "design", "product", "sales", "marketing", "operations", "finance", "hr", "legal"]
                        },
                        "description": "Categories of roles this person would be interested in",
                        "maxItems": 5
                    }
                },
                "required": ["overall_experience_level", "total_years_experience", "skills", "leadership_experience"]
            }
        }]
        
        system_prompt = """You are an expert technical recruiter and career counselor with 15+ years of experience. 
        Analyze this resume and extract detailed professional profile information with high accuracy.
        
        EXPERIENCE LEVEL GUIDELINES:
        - intern: 0-1 years, learning fundamentals, academic projects
        - junior: 1-3 years, can work with guidance, simple tasks
        - mid: 3-7 years, works independently, some mentoring of others
        - senior: 7-12 years, leads projects, mentors others, complex problem solving
        - lead: 10+ years, leads teams/initiatives, strategic thinking, architecture decisions
        - principal: 15+ years, sets technical direction, industry expertise, thought leadership
        
        SKILL LEVEL ASSESSMENT:
        - beginner: Basic familiarity, learning, can do simple tasks with help
        - junior: Can use with guidance, 1-2 years experience, knows basics
        - mid: Proficient, can work independently, 3-5 years, solid understanding
        - senior: Expert level, can teach others, 5+ years, deep knowledge
        - expert: Industry-recognized expertise, 7+ years, innovates and sets standards
        
        ANALYSIS PRINCIPLES:
        1. Be realistic and conservative - don't over-inflate levels
        2. Consider actual responsibilities, not just technologies mentioned
        3. Look for evidence of impact, leadership, and growing responsibility
        4. Distinguish between exposure (junior) vs proficiency (mid+) vs expertise (senior+)
        5. Factor in company size and role complexity
        6. Consider technology adoption timelines (e.g., newer tech = potentially lower years)
        
        CONFIDENCE SCORING:
        - 0.9-1.0: Clear evidence with specific examples and timeframes
        - 0.7-0.8: Good evidence but some inference required  
        - 0.5-0.6: Reasonable guess based on context clues
        - 0.3-0.4: Weak evidence, significant uncertainty
        - 0.1-0.2: Very uncertain, minimal evidence
        
        Focus on extracting the most valuable skills for job matching. Prioritize:
        - Programming languages and frameworks
        - Cloud platforms and DevOps tools
        - Databases and data technologies
        - Leadership and soft skills
        - Domain expertise
        """
        
        try:
            logger.info("Extracting professional profile from resume")
            
            result = await llm_service(
                text=resume_text,
                system_prompt=system_prompt,
                tools=tools,
                force_tool_use=True
            )
            
            if not result or "tool_calls" not in result or not result["tool_calls"]:
                logger.error("LLM did not return tool calls for profile extraction")
                return {"error": "Failed to extract profile data"}
            
            profile_data = result["tool_calls"][0]["parameters"]
            
            # Validate and clean the extracted data
            cleaned_data = SkillExtractionService._validate_and_clean_profile(profile_data)
            
            logger.info(f"Successfully extracted profile data with {len(cleaned_data.get('skills', {}))} skills")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
            return {"error": f"Profile extraction failed: {str(e)}"}
    
    @staticmethod
    async def generate_role_tags(title: str, description: str, llm_service: McpMeshAgent, convert_tool_format: McpMeshAgent = None) -> Dict[str, Any]:
        """Generate structured tags and requirements for a role."""
        
        tools = [{
            "name": "analyze_job_role",
            "description": "Analyze job role and extract experience level, years range, and relevant tags",
            "input_schema": {
                "type": "object",
                "properties": {
                    "experience_level": {
                        "type": "string",
                        "enum": ["intern", "junior", "mid", "senior", "lead", "principal"],
                        "description": "Required experience level based on responsibilities and title"
                    },
                    "required_years_min": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 20,
                        "description": "Minimum years of experience required"
                    },
                    "required_years_max": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 25,
                        "description": "Maximum years of experience optimal"
                    },
                    "short_description": {
                        "type": "string",
                        "maxLength": 200,
                        "description": "Concise role summary"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 15,
                        "description": "Relevant skills, tools, technologies specific to this role and category"
                    },
                    "confidence_score": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "LLM confidence in the analysis (0.0-1.0)"
                    }
                },
                "required": ["experience_level", "required_years_min", "required_years_max", "short_description", "tags"]
            }
        }]
        
        system_prompt = """You are an expert HR professional and job analyst specializing in experience assessment and skill identification.
        
        Analyze this job role and extract structured requirements for matching candidates. The business category has already been determined by the admin.
        
        CORE RESPONSIBILITIES:
        1. Determine the appropriate experience level based on title and responsibilities
        2. Estimate realistic years of experience range for this role
        3. Extract relevant, searchable tags that candidates would have on their resumes
        4. Create a concise role summary
        5. Assess your confidence in the analysis
        
        EXPERIENCE LEVEL GUIDELINES:
        - intern: Learning role, 0-1 years, academic projects, internships
        - junior: Entry level, 1-3 years, works with guidance, basic responsibilities
        - mid: Independent contributor, 3-7 years, works autonomously, some mentoring
        - senior: Expert contributor, 7-12 years, leads projects, mentors others, complex problem solving
        - lead: Leadership role, 10+ years, manages teams/initiatives, strategic decisions
        - principal: Senior leadership, 15+ years, sets technical/business direction, industry expertise
        
        TAG GENERATION PRINCIPLES:
        1. Focus on specific tools, technologies, and methodologies mentioned
        2. Include relevant soft skills (leadership, communication, project management)
        3. Add industry-specific terms and domain knowledge
        4. Use terms that would appear on candidate resumes
        5. Keep tags concise and searchable (prefer "python" over "python programming")
        
        CONFIDENCE SCORING:
        - 0.9-1.0: Very clear role with specific requirements and obvious experience level
        - 0.7-0.8: Clear role but some interpretation needed for experience or requirements
        - 0.5-0.6: Moderate clarity, some ambiguity in responsibilities or level
        - 0.3-0.4: Unclear role description, significant assumptions required
        - 0.1-0.2: Very poor job description, minimal useful information
        """
        
        try:
            role_text = f"Role: {title}\n\nDescription:\n{description}"
            
            # Convert tools to appropriate format for the LLM provider
            logger.info("Converting role analysis tool format for LLM provider")
            converted_tools = tools  # Default to Claude format
            
            if convert_tool_format:
                try:
                    converted_tools = await convert_tool_format(tools=tools)
                    logger.info(f"Successfully converted {len(converted_tools)} role analysis tools for LLM provider")
                except Exception as tool_convert_error:
                    logger.warning(f"Role analysis tool conversion failed, using original format: {tool_convert_error}")
                    converted_tools = tools
            else:
                logger.info("Tool conversion service not available, using Claude format for role analysis")
            
            result = await llm_service(
                text=role_text,
                system_prompt=system_prompt,
                tools=converted_tools,
                force_tool_use=True
            )
            
            if not result or "tool_calls" not in result or not result["tool_calls"]:
                logger.error("LLM did not return tool calls for role analysis")
                return {"error": "Failed to analyze role"}
            
            role_data = result["tool_calls"][0]["parameters"]
            logger.info(f"Successfully analyzed role '{title}' - experience: {role_data.get('experience_level')}, tags: {len(role_data.get('tags', []))}")
            
            return role_data
            
        except Exception as e:
            logger.error(f"Error analyzing role: {e}")
            return {"error": f"Role analysis failed: {str(e)}"}
    
    @staticmethod
    def _validate_and_clean_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted profile data."""
        
        # Ensure required fields exist with defaults
        cleaned = {
            "overall_experience_level": profile_data.get("overall_experience_level", "junior"),
            "total_years_experience": max(0, profile_data.get("total_years_experience", 0)),
            "skills": profile_data.get("skills", {}),
            "leadership_experience": profile_data.get("leadership_experience", {"has_leadership": False}),
            "career_progression": profile_data.get("career_progression", []),
            "preferred_next_levels": profile_data.get("preferred_next_levels", []),
            "categories_of_interest": profile_data.get("categories_of_interest", [])
        }
        
        # Validate and clean skills data
        clean_skills = {}
        skills_data = cleaned.get("skills", {})
        if isinstance(skills_data, dict):
            for skill_name, skill_data in skills_data.items():
                if isinstance(skill_data, dict) and "level" in skill_data:
                    try:
                        skill_name_clean = skill_name.lower().strip()[:100]  # Limit skill name length
                        clean_skills[skill_name_clean] = {
                            "level": skill_data.get("level", "beginner"),
                            "years": max(0, min(30, int(skill_data.get("years", 0)))),
                            "confidence": max(0.0, min(1.0, float(skill_data.get("confidence", 0.5)))),
                            "context": str(skill_data.get("context", ""))[:200]  # Limit context length
                        }
                    except (ValueError, TypeError) as skill_error:
                        logger.warning(f"Skipping invalid skill data for '{skill_name}': {skill_error}")
                        continue
        
        cleaned["skills"] = clean_skills
        
        # Validate experience level
        valid_levels = ["intern", "junior", "mid", "senior", "lead", "principal"]
        if cleaned["overall_experience_level"] not in valid_levels:
            logger.warning(f"Invalid experience level: {cleaned['overall_experience_level']}, defaulting to 'junior'")
            cleaned["overall_experience_level"] = "junior"
        
        # Validate total years experience
        try:
            cleaned["total_years_experience"] = max(0, min(50, int(cleaned["total_years_experience"])))
        except (ValueError, TypeError):
            logger.warning("Invalid total_years_experience, using 0")
            cleaned["total_years_experience"] = 0
        
        # Validate leadership experience
        if not isinstance(cleaned["leadership_experience"], dict):
            cleaned["leadership_experience"] = {"has_leadership": False}
        
        # Validate lists
        if not isinstance(cleaned["career_progression"], list):
            cleaned["career_progression"] = []
        if not isinstance(cleaned["preferred_next_levels"], list):
            cleaned["preferred_next_levels"] = []
        if not isinstance(cleaned["categories_of_interest"], list):
            cleaned["categories_of_interest"] = []
        
        logger.info(f"Profile validation completed: {len(clean_skills)} skills, {cleaned['overall_experience_level']} level")
        return cleaned