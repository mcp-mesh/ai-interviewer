"""
MCP client service for communicating with other services.
"""

import json
import logging
from typing import Optional, Dict, Any

import httpx
from app.config import PDF_EXTRACTOR_URL, INTERVIEW_AGENT_URL

logger = logging.getLogger(__name__)

class MCPClient:
    """Client for MCP service communication."""
    
    async def call_pdf_extractor(self, file_path: str, file_content: bytes) -> Optional[Dict[str, Any]]:
        """Call PDF extractor service via MCP using MCP Mesh streaming for large files."""
        try:
            # For now, use regular function call with extended timeout
            # TODO: Implement proper MCP Mesh streaming integration
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "extract_text_from_pdf",
                    "arguments": {
                        "file_path": file_path,
                        "extraction_method": "auto"
                    }
                }
            }
            
            # Extended timeout for large PDFs
            async with httpx.AsyncClient(timeout=600.0) as client:
                async with client.stream(
                    "POST",
                    f"{PDF_EXTRACTOR_URL}/mcp/",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    }
                ) as response:
                    
                    if response.status_code != 200:
                        logger.error(f"PDF extractor returned status {response.status_code}")
                        return None
                    
                    # Process Server-Sent Events stream
                    response_data = None
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            try:
                                data = json.loads(data_str)
                                if "result" in data:
                                    response_data = data["result"]
                                    break
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse SSE data: {data_str}")
                                continue
                    
                    # Use response_data for processing
                    
                    if not response_data:
                        logger.error("No valid response data received from PDF extractor")
                        return None
                    
                    # Extract content from MCP response
                    if "content" in response_data and isinstance(response_data["content"], list):
                        content_list = response_data["content"]
                        if len(content_list) > 0:
                            content_item = content_list[0]
                            if "text" in content_item:
                                extracted_text = content_item["text"]
                                try:
                                    # Try to parse as JSON if it's a string
                                    if isinstance(extracted_text, str):
                                        return json.loads(extracted_text)
                                    else:
                                        return extracted_text
                                except json.JSONDecodeError:
                                    # If not JSON, return as plain text
                                    return {
                                        "text": extracted_text,
                                        "structured_data": {},
                                        "metadata": {"extraction_method": "text_only"}
                                    }
                    
                    logger.error(f"Unexpected response format: {response_data}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling PDF extractor: {e}")
            return None

    async def call_interview_agent(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call interview agent via MCP JSON-RPC."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{INTERVIEW_AGENT_URL}/mcp/",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    }
                ) as response:
                    
                    if response.status_code != 200:
                        logger.error(f"Interview agent returned status {response.status_code}")
                        return None
                    
                    # Process Server-Sent Events stream
                    response_data = None
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            try:
                                data = json.loads(data_str)
                                if "result" in data:
                                    response_data = data["result"]
                                    break
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse interview agent SSE data: {data_str}")
                                continue
                    
                    if not response_data:
                        logger.error("No valid response data received from interview agent")
                        return None
                    
                    # Handle MCP structured response format
                    if "structuredContent" in response_data:
                        return response_data["structuredContent"]
                    elif "content" in response_data and isinstance(response_data["content"], list):
                        # Try to parse content as JSON
                        content_list = response_data["content"]
                        if len(content_list) > 0 and "text" in content_list[0]:
                            try:
                                return json.loads(content_list[0]["text"])
                            except json.JSONDecodeError:
                                pass
                    
                    return response_data
                    
        except Exception as e:
            logger.error(f"Error calling interview agent: {e}")
            return None