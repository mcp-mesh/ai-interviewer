#!/usr/bin/env python3
"""
OpenAI LLM Agent - Main Entry Point

A generic LLM processing MCP Mesh agent for the AI Interviewer system.
Provides OpenAI ChatGPT API integration with dynamic tool support.
"""

import logging
import os
from typing import Any, Dict, List, Optional
import json

import mesh
from fastmcp import FastMCP
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Create FastMCP app instance for hybrid functionality
app = FastMCP("OpenAI LLM Processing Service")

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OPENAI_API_KEY environment variable is required")
    raise ValueError("OPENAI_API_KEY environment variable is required")

openai_client = OpenAI(api_key=openai_api_key)

# Configuration
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))
DEFAULT_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def call_openai_api(
    messages: List[Dict[str, str]],
    tools: List[Dict] = None,
    tool_choice: str = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE
) -> Dict[str, Any]:
    """
    Call OpenAI API with retry logic.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        tools: Optional tool definitions for structured output
        tool_choice: Tool choice strategy ('auto', 'none', or specific tool)
        model: OpenAI model to use
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
        
        if tools:
            api_params["tools"] = tools
            if tool_choice:
                api_params["tool_choice"] = tool_choice
            
        logger.info(f"Calling OpenAI API with model {model}, {len(messages)} messages, {len(tools) if tools else 0} tools")
        
        # Make API call
        response = openai_client.chat.completions.create(**api_params)
        
        # Process response
        result = {
            "success": True,
            "content": None,
            "tool_calls": [],
            "model": response.model,
            "provider": "openai",
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "stop_reason": response.choices[0].finish_reason
        }
        
        # Extract content and tool calls
        message = response.choices[0].message
        if message.content:
            result["content"] = message.content
            
        if message.tool_calls:
            for tool_call in message.tool_calls:
                result["tool_calls"].append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "parameters": json.loads(tool_call.function.arguments)
                })
        
        logger.info(f"OpenAI API call successful. Usage: {result['usage']}")
        return result
        
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "content": None,
            "tool_calls": [],
            "usage": None,
            "provider": "openai"
        }


@app.tool()
@mesh.tool(
    capability="process_with_tools",
    version="1.5",  # OpenAI version identifier
    tags=["llm-service", "openai", "chatgpt", "text-processing", "ai-analysis"],
    description="Generic LLM processing using OpenAI ChatGPT API with dynamic tool support",
    timeout=120,  # Allow longer processing time
    retry_count=2,
    custom_headers={
        "X-Service-Type": "llm-agent",
        "X-Model-Provider": "openai",
        "X-Model-Version": "gpt-4o"
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
        tools: Tool definitions in OpenAI format for structured output
        messages: Optional pre-built message array (if provided, 'text' is ignored)
        force_tool_use: Whether to force tool usage when tools are provided
        model: OpenAI model to use
        max_tokens: Maximum tokens in response
        temperature: Response randomness (0.0-1.0)
        
    Returns:
        Dict containing response content, tool calls, and metadata
        
    Examples:
        Basic text processing:
        >>> process_with_tools("Analyze this resume...", system_prompt="You are an expert...")
        
        Structured extraction with tools:
        >>> tools = [{"type": "function", "function": {"name": "extract_data", "parameters": {...}}}]
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
            api_messages = []
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})
            api_messages.append({"role": "user", "content": text})
        
        # Convert tools to OpenAI format if needed
        api_tools = _convert_tools_to_openai_format(tools) if tools else None
        
        # Force tool use if tools provided and force_tool_use is True
        tool_choice = None
        if api_tools and force_tool_use:
            tool_choice = "required"  # OpenAI's equivalent to forcing tool use
            logger.info(f"Forcing tool use with {len(api_tools)} available tools")
        elif api_tools:
            tool_choice = "auto"
        
        # Call OpenAI API
        response = call_openai_api(
            messages=api_messages,
            tools=api_tools,
            tool_choice=tool_choice,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Add processing metadata
        response.update({
            "processed_at": __import__("datetime").datetime.now().isoformat(),
            "input_length": len(text) if text else sum(len(msg.get("content", "")) for msg in api_messages),
            "tools_provided": len(api_tools) if api_tools else 0,
            "tool_use_forced": force_tool_use and bool(api_tools)
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


def _convert_tools_to_openai_format(tools: List[Dict]) -> List[Dict]:
    """
    Internal utility to convert Claude tool format to OpenAI tool format.
    
    Args:
        tools: List of tool definitions in Claude format
        
    Returns:
        List of tool definitions in OpenAI format
    """
    if not tools:
        return tools
    
    # Check if already in OpenAI format
    if tools[0].get("type") == "function":
        return tools  # Already converted
    
    try:
        logger.debug(f"Converting {len(tools)} tools from Claude to OpenAI format")
        
        converted_tools = []
        for tool in tools:
            if isinstance(tool, dict):
                # Convert from Claude format to OpenAI format
                function_def = tool.copy()
                
                # Convert Claude's 'input_schema' to OpenAI's 'parameters'
                if "input_schema" in function_def:
                    function_def["parameters"] = function_def.pop("input_schema")
                
                openai_tool = {
                    "type": "function",
                    "function": function_def
                }
                converted_tools.append(openai_tool)
            else:
                logger.warning(f"Invalid tool format: {tool}")
                continue
        
        logger.debug(f"Auto-converted {len(converted_tools)} tools to OpenAI format")
        return converted_tools
        
    except Exception as e:
        logger.error(f"Tool format conversion failed: {str(e)}")
        return tools  # Return original tools as fallback


@app.tool()
@mesh.tool(
    capability="health_check",
    version="1.5",
    tags=["llm_service", "openai", "chatgpt", "ai_processing"],
    description="Get OpenAI LLM agent status and configuration"
)
def get_llm_status() -> Dict[str, Any]:
    """
    Get current OpenAI LLM agent status and configuration.
    
    Returns:
        Dictionary containing agent status, model info, and configuration
    """
    try:
        return {
            "agent_name": "llm-openai-agent",
            "version": "1.5",
            "status": "healthy",
            "model_provider": "openai",
            "available_models": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
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
            "api_key_configured": bool(openai_api_key),
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
    name="llm-openai-agent",
    http_port=8090,
    auto_run=True  # KEY: This makes MCP Mesh automatically start the FastMCP server
)
class OpenAILLMAgent:
    """
    OpenAI LLM Agent for AI Interviewer System
    
    A generic MCP Mesh agent for LLM processing operations using OpenAI ChatGPT API.
    
    MCP Mesh will automatically:
    1. Discover the 'app' FastMCP instance above
    2. Apply dependency injection to @mesh.tool decorated functions
    3. Start the FastMCP HTTP server on the configured port
    4. Register all capabilities with the mesh registry
    
    No manual server startup needed!
    """
    
    def __init__(self):
        logger.info("Initializing OpenAI LLM Agent v1.5")
        logger.info(f"Default model: {DEFAULT_MODEL}")
        logger.info(f"Max tokens: {MAX_TOKENS}")
        logger.info(f"API key configured: {bool(openai_api_key)}")
        logger.info("Ready to process LLM requests with dynamic tool support")


# No main method needed!
# MCP Mesh processor automatically handles:
# - FastMCP server discovery and startup  
# - Dependency injection between functions
# - HTTP server configuration
# - Service registration with mesh registry
