"""
Question Generator - LLM Integration for Dynamic Interview Questions

Handles LLM interactions for generating contextual technical interview questions
based on job requirements, candidate profile, and conversation history.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from mesh.types import McpAgent

logger = logging.getLogger(__name__)

class QuestionGenerator:
    """
    Generates interview questions using LLM integration with job and candidate context.
    """
    
    def __init__(self):
        """Initialize question generator."""
        self.logger = logging.getLogger(__name__)
    
    async def generate_interview_question(
        self,
        job_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        llm_service: McpAgent,
        difficulty_level: str = "medium",
        question_type: str = "technical"
    ) -> Dict[str, Any]:
        """
        Generate a contextual interview question using LLM.
        
        Args:
            job_data: Job posting details
            resume_data: Candidate resume information
            conversation_history: Previous questions and answers
            llm_service: MCP Mesh LLM service
            difficulty_level: Question difficulty (junior, mid, senior, expert)
            question_type: Type of question (technical, behavioral, scenario)
            
        Returns:
            Dictionary containing question text, type, difficulty, and metadata
            
        Raises:
            Exception: Question generation failed
        """
        try:
            if not llm_service:
                raise Exception("LLM service not available for question generation")
            
            # Build context from job and resume data
            job_title = job_data.get("title", "Software Developer")
            job_description = job_data.get("description", "")
            required_skills = job_data.get("required_skills", [])
            preferred_skills = job_data.get("preferred_skills", [])
            
            candidate_skills = resume_data.get("skills", [])
            candidate_experience = resume_data.get("experience", [])
            
            # Format conversation history for context
            conversation_context = self._format_conversation_for_llm(conversation_history)
            
            # Determine question focus based on skills alignment
            question_focus = self._determine_question_focus(
                required_skills, preferred_skills, candidate_skills
            )
            
            # Build system prompt for question generation
            system_prompt = self._build_question_generation_prompt(
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
                candidate_skills=candidate_skills,
                conversation_context=conversation_context,
                difficulty_level=difficulty_level,
                question_type=question_type,
                question_focus=question_focus
            )
            
            # Define question generation tool
            question_tool = {
                "name": "generate_question",
                "description": "Generate a contextual interview question",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The interview question text"
                        },
                        "question_type": {
                            "type": "string", 
                            "enum": ["technical", "behavioral", "scenario", "problem_solving"],
                            "description": "Type of question"
                        },
                        "difficulty": {
                            "type": "string",
                            "enum": ["junior", "mid", "senior", "expert"],
                            "description": "Question difficulty level"
                        },
                        "focus_area": {
                            "type": "string",
                            "description": "Primary skill or concept being assessed"
                        },
                        "expected_concepts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Key concepts the candidate should demonstrate"
                        },
                        "follow_up_topics": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "Potential follow-up topics based on response"
                        }
                    },
                    "required": ["question", "question_type", "difficulty", "focus_area"]
                }
            }
            
            self.logger.info(f"Generating {difficulty_level} {question_type} question for {job_title}")
            
            # Call LLM service for question generation
            llm_response = await llm_service(
                text="Generate an interview question now using the tool.",
                system_prompt=system_prompt,
                messages=[],
                tools=[question_tool],
                force_tool_use=True,
                temperature=0.7  # Slightly higher temperature for creativity
            )
            
            if not llm_response.get("success") or not llm_response.get("tool_calls"):
                raise Exception(f"LLM failed to generate question: {llm_response.get('error', 'No tool calls')}")
            
            # Extract question from tool response
            tool_call = llm_response["tool_calls"][0]
            question_data = tool_call["parameters"]
            
            # Format final question response
            result = {
                "question_text": question_data["question"],
                "question_type": question_data["question_type"],
                "difficulty": question_data["difficulty"],
                "focus_area": question_data["focus_area"],
                "expected_concepts": question_data.get("expected_concepts", []),
                "follow_up_topics": question_data.get("follow_up_topics", []),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "job_title": job_title,
                    "question_number": len(conversation_history) + 1,
                    "generation_temperature": 0.7
                }
            }
            
            self.logger.info(f"Generated question: {result['focus_area']} ({result['difficulty']})")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate interview question: {e}")
            raise Exception(f"Question generation failed: {str(e)}")
    
    async def generate_follow_up_question(
        self,
        previous_question: Dict[str, Any],
        candidate_response: str,
        job_data: Dict[str, Any],
        llm_service: McpAgent
    ) -> Dict[str, Any]:
        """
        Generate a follow-up question based on candidate's response.
        
        Args:
            previous_question: Previous question data
            candidate_response: Candidate's response to previous question
            job_data: Job posting details
            llm_service: MCP Mesh LLM service
            
        Returns:
            Follow-up question dictionary
        """
        try:
            # Build follow-up generation prompt
            system_prompt = f"""You are an experienced technical interviewer. Based on the candidate's response to a previous question, generate an appropriate follow-up question.

PREVIOUS QUESTION:
{previous_question.get('question_text', '')}

CANDIDATE'S RESPONSE:
{candidate_response}

JOB CONTEXT:
- Role: {job_data.get('title', 'Software Developer')}
- Key Skills: {', '.join(job_data.get('required_skills', []))}

Generate a follow-up question that:
1. Builds on their response to go deeper
2. Clarifies any unclear points
3. Tests practical application of concepts mentioned
4. Maintains interview flow and candidate engagement

The follow-up should be natural and conversational while remaining technically relevant."""

            follow_up_tool = {
                "name": "generate_follow_up",
                "description": "Generate a follow-up interview question",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The follow-up question text"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Why this follow-up is appropriate"
                        },
                        "focus_area": {
                            "type": "string",
                            "description": "What aspect this follow-up explores"
                        }
                    },
                    "required": ["question", "reasoning", "focus_area"]
                }
            }
            
            llm_response = await llm_service(
                text="Generate a follow-up question now using the tool.",
                system_prompt=system_prompt,
                messages=[],
                tools=[follow_up_tool],
                force_tool_use=True,
                temperature=0.6
            )
            
            if not llm_response.get("success") or not llm_response.get("tool_calls"):
                raise Exception("Failed to generate follow-up question")
            
            tool_call = llm_response["tool_calls"][0]
            follow_up_data = tool_call["parameters"]
            
            return {
                "question_text": follow_up_data["question"],
                "question_type": "follow_up",
                "difficulty": previous_question.get("difficulty", "medium"),
                "focus_area": follow_up_data["focus_area"],
                "reasoning": follow_up_data["reasoning"],
                "is_follow_up": True,
                "parent_question_id": previous_question.get("id"),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate follow-up question: {e}")
            raise Exception(f"Follow-up generation failed: {str(e)}")
    
    def _format_conversation_for_llm(self, conversation: List[Dict[str, Any]]) -> str:
        """
        Format conversation history for LLM context.
        
        Args:
            conversation: List of conversation pairs
            
        Returns:
            Formatted conversation string
        """
        if not conversation:
            return "This is the first question of the interview."
        
        formatted_pairs = []
        for i, pair in enumerate(conversation[-3:], 1):  # Last 3 pairs for context
            question = pair.get("question", {})
            response = pair.get("response", {})
            
            pair_text = f"Q{i}: {question.get('text', 'Unknown question')}"
            if response:
                pair_text += f"\nA{i}: {response.get('text', 'No response given')}"
            
            formatted_pairs.append(pair_text)
        
        return "\n\n".join(formatted_pairs)
    
    def _determine_question_focus(
        self,
        required_skills: List[str],
        preferred_skills: List[str],
        candidate_skills: List[str]
    ) -> str:
        """
        Determine the primary focus area for the next question.
        
        Args:
            required_skills: Job required skills
            preferred_skills: Job preferred skills  
            candidate_skills: Candidate's skills
            
        Returns:
            Focus area string
        """
        # Find skills that candidate has from required list
        matching_required = [skill for skill in required_skills if skill.lower() in [cs.lower() for cs in candidate_skills]]
        
        # Find skills candidate claims but are also preferred
        matching_preferred = [skill for skill in preferred_skills if skill.lower() in [cs.lower() for cs in candidate_skills]]
        
        # Prioritize required skills, then preferred
        if matching_required:
            return matching_required[0]
        elif matching_preferred:
            return matching_preferred[0]
        elif required_skills:
            return required_skills[0]
        else:
            return "general technical knowledge"
    
    def _build_question_generation_prompt(
        self,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        candidate_skills: List[str],
        conversation_context: str,
        difficulty_level: str,
        question_type: str,
        question_focus: str
    ) -> str:
        """
        Build comprehensive system prompt for question generation.
        
        Returns:
            System prompt string
        """
        return f"""You are an experienced technical interviewer conducting an interview for a {job_title} position.

JOB CONTEXT:
- Role: {job_title}
- Required Skills: {', '.join(required_skills) if required_skills else 'General software development'}
- Job Description: {job_description[:500]}...

CANDIDATE PROFILE:
- Skills: {', '.join(candidate_skills) if candidate_skills else 'Skills to be assessed'}

CONVERSATION HISTORY:
{conversation_context}

QUESTION REQUIREMENTS:
- Type: {question_type}
- Difficulty: {difficulty_level}
- Focus Area: {question_focus}

QUESTION GENERATION GUIDELINES:

1. **Technical Questions**:
   - Test practical knowledge and real-world application
   - Include scenarios they might face in this role
   - Ask about trade-offs, design decisions, and problem-solving approaches
   - Avoid pure trivia - focus on understanding and reasoning

2. **Difficulty Calibration**:
   - Junior: Basic concepts, syntax, simple problem solving
   - Mid: Design patterns, system interactions, debugging scenarios
   - Senior: Architecture decisions, scalability, leading technical discussions
   - Expert: Complex system design, performance optimization, technical leadership

3. **Question Quality**:
   - Clear and specific without being overly complex
   - Open-ended to allow demonstration of knowledge depth
   - Relevant to the job requirements and candidate's background
   - Natural conversation flow from previous questions

4. **Avoid**:
   - Trick questions or gotchas
   - Extremely obscure or rarely-used concepts
   - Questions that can be easily googled
   - Leading questions that suggest the answer

5. **STRICT BEHAVIORAL BOUNDARIES**:
   - ONLY discuss technical topics related to the job role
   - DO NOT answer questions about: salary, benefits, company politics, personal matters
   - DO NOT engage in discussions about: politics, religion, sexual content, inappropriate topics
   - IF asked non-technical questions, politely redirect to technical assessment
   - NEVER provide information about company finances, internal issues, or confidential matters
   - MAINTAIN professional interview focus at all times

Generate a high-quality interview question that will effectively assess the candidate's suitability for this role."""

# Global question generator instance
question_generator = QuestionGenerator()