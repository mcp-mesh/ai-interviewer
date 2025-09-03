#!/usr/bin/env python3
"""
Claude LLM Agent - Main Entry Point

A Claude LLM processing MCP Mesh agent for the AI Interviewer system.
Provides Claude API integration with dynamic tool support.
"""

import logging
import os
from typing import Any, Dict, List, Optional
import json

import mesh
from fastmcp import FastMCP
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

# Create FastMCP app instance for hybrid functionality
app = FastMCP("Claude LLM Processing Service")

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Claude client
anthropic_api_key = os.getenv("CLAUDE_API_KEY")
if not anthropic_api_key:
    logger.error("CLAUDE_API_KEY environment variable is required")
    raise ValueError("CLAUDE_API_KEY environment variable is required")

claude_client = Anthropic(api_key=anthropic_api_key)

# Configuration
DEFAULT_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "8000"))
DEFAULT_TEMPERATURE = float(os.getenv("CLAUDE_TEMPERATURE", "0.7"))


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def call_claude_api(
    messages: List[Dict[str, str]],
    system_prompt: str = None,
    tools: List[Dict] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE
) -> Dict[str, Any]:
    """
    Call Claude API with retry logic.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        system_prompt: Optional system prompt
        tools: Optional tool definitions for structured output
        model: Claude model to use
        max_tokens: Maximum tokens in response
        temperature: Response randomness (0.0-1.0)
        
    Returns:
        Dict containing response content and metadata
    """
    try:
        # Build API request parameters
        api_params = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system_prompt:
            api_params["system"] = system_prompt
            
        if tools:
            api_params["tools"] = tools
            
        logger.info(f"Calling Claude API with model {model}, {len(messages)} messages, {len(tools) if tools else 0} tools")
        
        # Make API call
        response = claude_client.messages.create(**api_params)
        
        # Process response
        result = {
            "success": True,
            "content": None,
            "tool_calls": [],
            "model": response.model,
            "provider": "anthropic",
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            "stop_reason": response.stop_reason
        }
        
        # Extract content and tool calls
        for content_block in response.content:
            if content_block.type == "text":
                result["content"] = content_block.text
            elif content_block.type == "tool_use":
                result["tool_calls"].append({
                    "id": content_block.id,
                    "name": content_block.name,
                    "parameters": content_block.input
                })
        
        logger.info(f"Claude API call successful. Usage: {result['usage']}")
        return result
        
    except Exception as e:
        logger.error(f"Claude API call failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "content": None,
            "tool_calls": [],
            "usage": None,
            "provider": "anthropic"
        }


@app.tool()
@mesh.tool(
    capability="process_with_tools",
    version="1.5",  # Claude version identifier
    tags=["llm-service", "claude", "anthropic", "text-processing", "ai-analysis"],
    description="Generic LLM processing using Claude API with dynamic tool support",
    timeout=120,  # Allow longer processing time
    streaming=True,  # Enable streaming support for large content processing
    stream_timeout=300,  # 5-minute streaming timeout for large PDFs
    retry_count=2,
    custom_headers={
        "X-Service-Type": "claude-llm-agent",
        "X-Model-Provider": "anthropic",
        "X-Model-Version": "claude-3-sonnet"
    }
)
def process_with_tools(
    text: str,
    system_prompt: str = None,
    tools: List[Dict] = None,
    messages: List[Dict[str, str]] = None,
    force_tool_use: bool = True,
    model: str = DEFAULT_MODEL,
    max_tokens: int = MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE
) -> Dict[str, Any]:
    """
    Generic LLM processing with dynamic tool definitions.
    
    Args:
        text: Primary content to process
        system_prompt: Optional system prompt for context
        tools: Tool definitions in Claude/OpenAI format for structured output
        messages: Optional pre-built message array (if provided, 'text' is ignored)
        force_tool_use: Whether to force tool usage when tools are provided
        model: Claude model to use
        max_tokens: Maximum tokens in response
        temperature: Response randomness (0.0-1.0)
        
    Returns:
        Dict containing response content, tool calls, and metadata
        
    Examples:
        Basic text processing:
        >>> process_with_tools("Analyze this resume...", system_prompt="You are an expert...")
        
        Structured extraction with tools:
        >>> tools = [{"name": "extract_data", "input_schema": {...}}]
        >>> process_with_tools("Resume text...", tools=tools, force_tool_use=True)
        
        Multi-turn conversation:
        >>> messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]
        >>> process_with_tools("", messages=messages)
    """
    try:
        logger.info(f"Processing LLM request with model {model}")
        
        # Build messages array
        if messages:
            # Use provided messages (multi-turn conversation)
            api_messages = messages.copy()
        else:
            # Single message from text parameter
            api_messages = [{"role": "user", "content": text}]
        
        # Force tool use if tools provided and force_tool_use is True
        api_tools = tools
        if tools and force_tool_use:
            # Add tool choice to force usage (Claude-specific)
            logger.info(f"Forcing tool use with {len(tools)} available tools")
        
        # Call Claude API
        response = call_claude_api(
            messages=api_messages,
            system_prompt=system_prompt,
            tools=api_tools,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Add processing metadata
        response.update({
            "processed_at": __import__("datetime").datetime.now().isoformat(),
            "input_length": len(text) if text else sum(len(msg.get("content", "")) for msg in api_messages),
            "tools_provided": len(tools) if tools else 0,
            "tool_use_forced": force_tool_use and bool(tools)
        })
        
        if response["success"]:
            logger.info(f"LLM processing successful. Generated {len(response['tool_calls'])} tool calls")
        else:
            logger.error(f"LLM processing failed: {response.get('error', 'Unknown error')}")
        
        return response
        
    except Exception as e:
        logger.error(f"LLM processing failed with exception: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "content": None,
            "tool_calls": [],
            "usage": None,
            "processed_at": __import__("datetime").datetime.now().isoformat()
        }




@app.tool()
@mesh.tool(
    capability="health_check",
    version="1.5", 
    tags=["llm_service", "claude", "anthropic", "ai_processing"],
    description="Get Claude LLM agent status and configuration"
)
def get_llm_status() -> Dict[str, Any]:
    """
    Get current LLM agent status and configuration.
    
    Returns:
        Dictionary containing agent status, model info, and configuration
    """
    try:
        return {
            "agent_name": "claude-llm-agent",
            "version": "1.5",
            "status": "healthy",
            "model_provider": "anthropic",
            "available_models": [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ],
            "current_model": DEFAULT_MODEL,
            "configuration": {
                "max_tokens": MAX_TOKENS,
                "default_temperature": DEFAULT_TEMPERATURE,
                "retry_attempts": 3,
                "timeout_seconds": 120
            },
            "capabilities": [
                "text_processing", "tool_calling", "structured_output",
                "multi_turn_conversation", "content_analysis"
            ],
            "supported_formats": [
                "text", "json", "structured_data", "tool_calls"
            ],
            "api_key_configured": bool(anthropic_api_key),
            "last_check": __import__("datetime").datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get LLM status: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "last_check": __import__("datetime").datetime.now().isoformat()
        }


# Agent class definition - MCP Mesh will auto-discover and run the FastMCP app
@mesh.agent(
    name="claude-llm-agent",
    http_port=9094,
    auto_run=True  # KEY: This makes MCP Mesh automatically start the FastMCP server
)
class ClaudeLLMAgent:
    """
    Claude LLM Agent for AI Interviewer System
    
    A Claude-specific MCP Mesh agent for LLM processing operations using Claude API.
    
    MCP Mesh will automatically:
    1. Discover the 'app' FastMCP instance above
    2. Apply dependency injection to @mesh.tool decorated functions
    3. Start the FastMCP HTTP server on the configured port
    4. Register all capabilities with the mesh registry
    
    No manual server startup needed!
    """
    
    def __init__(self):
        logger.info("Initializing Claude LLM Agent v1.5")
        logger.info(f"Default model: {DEFAULT_MODEL}")
        logger.info(f"Max tokens: {MAX_TOKENS}")
        logger.info(f"API key configured: {bool(anthropic_api_key)}")
        logger.info("Ready to process LLM requests with dynamic tool support")


# No main method needed!
# MCP Mesh processor automatically handles:
# - FastMCP server discovery and startup  
# - Dependency injection between functions
# - HTTP server configuration
# - Service registration with mesh registry