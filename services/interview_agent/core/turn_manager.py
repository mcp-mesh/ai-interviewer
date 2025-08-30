"""
Turn Manager - Interview Conversation Flow Control

Manages conversation turns between user and assistant, preventing duplicate messages
and ensuring proper conversation flow with full history context.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class TurnManager:
    """
    Manages conversation turns and message flow for interview sessions.
    """
    
    def __init__(self):
        """Initialize turn manager."""
        self.logger = logging.getLogger(__name__)
    
    def analyze_conversation_state(
        self, 
        conversation_history: List[Dict[str, str]], 
        has_user_input: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze conversation to determine whose turn it is and what action to take.
        
        Args:
            conversation_history: Full conversation history from database
            has_user_input: Whether user provided new input
            
        Returns:
            Dict with turn analysis:
            - whose_turn: "user" | "assistant" 
            - action: "generate_question" | "save_and_generate" | "wait_for_response"
            - strip_last_message: Whether to ignore new user input
            - reason: Human-readable explanation
        """
        # No conversation history - assistant should ask first question
        if not conversation_history:
            return {
                "whose_turn": "assistant",
                "action": "generate_question", 
                "strip_last_message": False,
                "reason": "Starting new interview - assistant asks first question"
            }
        
        last_message = conversation_history[-1]
        last_role = last_message.get("role")
        
        if last_role == "assistant":
            # Last message was assistant question - user's turn to respond
            if has_user_input:
                return {
                    "whose_turn": "user",
                    "action": "save_and_generate",
                    "strip_last_message": False,
                    "reason": "User responding to assistant's question - save response and generate next question"
                }
            else:
                return {
                    "whose_turn": "user", 
                    "action": "wait_for_response",
                    "strip_last_message": False,
                    "reason": "Waiting for user to respond to assistant's question"
                }
        
        elif last_role == "user":
            # Last message was user response - assistant's turn to ask next question
            if has_user_input:
                return {
                    "whose_turn": "assistant",
                    "action": "generate_question",
                    "strip_last_message": True,
                    "reason": "User sent duplicate message - stripping and generating next question"
                }
            else:
                return {
                    "whose_turn": "assistant",
                    "action": "generate_question", 
                    "strip_last_message": False,
                    "reason": "Assistant's turn to generate next question"
                }
        
        else:
            # Fallback for unexpected conversation state
            self.logger.warning(f"Unexpected conversation state - last role: {last_role}")
            return {
                "whose_turn": "assistant",
                "action": "generate_question",
                "strip_last_message": False, 
                "reason": f"Recovering from unexpected state (last role: {last_role})"
            }
    
    def should_save_user_input(
        self, 
        conversation_history: List[Dict[str, str]], 
        user_input: Optional[str]
    ) -> bool:
        """
        Determine if user input should be saved to database.
        
        Args:
            conversation_history: Full conversation history
            user_input: User's input message
            
        Returns:
            True if input should be saved, False if it should be stripped
        """
        if not user_input or not user_input.strip():
            return False
        
        state = self.analyze_conversation_state(
            conversation_history=conversation_history,
            has_user_input=True
        )
        
        return not state["strip_last_message"]
    
    def get_conversation_for_llm(
        self,
        conversation_history: List[Dict[str, str]],
        user_input: Optional[str] = None,
        strip_duplicate: bool = False
    ) -> List[Dict[str, str]]:
        """
        Prepare conversation history for LLM processing.
        
        Args:
            conversation_history: Full conversation from database
            user_input: New user input (if any)
            strip_duplicate: Whether to ignore user_input (duplicate message)
            
        Returns:
            Properly formatted conversation for LLM
        """
        # Start with existing conversation history
        llm_conversation = conversation_history.copy()
        
        # Add user input if it should be included
        if user_input and user_input.strip() and not strip_duplicate:
            llm_conversation.append({
                "role": "user",
                "content": user_input.strip()
            })
        
        self.logger.info(f"Prepared conversation for LLM: {len(llm_conversation)} messages")
        return llm_conversation

# Global turn manager instance
turn_manager = TurnManager()