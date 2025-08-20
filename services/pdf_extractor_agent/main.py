#!/usr/bin/env python3
"""
PDF Extractor Agent - Main Implementation

A simple PDF processing MCP Mesh agent for the AI Interviewer system.
"""

import logging
import os
from typing import Any, Dict
from datetime import datetime

import mesh
from fastmcp import FastMCP

# Import specific agent types for type hints
from mesh.types import McpAgent, McpMeshAgent

# Create FastMCP app instance
app = FastMCP("PDF Extractor Service")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simple configuration like other agents
HTTP_PORT = int(os.getenv("HTTP_PORT", "9093"))
AGENT_NAME = os.getenv("AGENT_NAME", "pdf-extractor")

logger.info(f"Starting PDF Extractor Agent on port {HTTP_PORT}")
logger.info(f"Agent name: {AGENT_NAME}")

def extract_basic_sections(text: str) -> Dict[str, str]:
    """Extract basic resume sections from text using simple pattern matching."""
    import re
    
    sections = {}
    
    # Common section headers (case-insensitive)
    section_patterns = {
        'contact': r'(?i)(?:contact|personal\s+(?:information|details)|phone|email)',
        'summary': r'(?i)(?:summary|profile|objective|about|overview)',
        'experience': r'(?i)(?:(?:work\s+)?experience|employment|professional\s+experience|career)',
        'education': r'(?i)(?:education|academic|qualifications|degree|university|college)',
        'skills': r'(?i)(?:skills|competencies|technical\s+skills|technologies)',
        'projects': r'(?i)(?:projects|portfolio|work\s+samples)',
        'certifications': r'(?i)(?:certifications?|certificates?|licenses?)',
        'achievements': r'(?i)(?:achievements?|awards?|honors?|accomplishments)',
        'references': r'(?i)(?:references?)'
    }
    
    # Split text into potential sections
    lines = text.split('\n')
    current_section = 'content'
    sections[current_section] = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line matches a section header
        section_found = None
        for section_name, pattern in section_patterns.items():
            if re.match(pattern, line) and len(line) < 50:  # Headers are usually short
                section_found = section_name
                break

        if section_found:
            current_section = section_found
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(line)

    # Convert lists to strings and clean up
    for section in sections:
        sections[section] = '\n'.join(sections[section]).strip()

    # Remove empty sections
    sections = {k: v for k, v in sections.items() if v}
    
    return sections

# Simple PDF extraction function with enhanced LLM analysis
@app.tool()
@mesh.tool(
    capability="extract_text_from_pdf",
    timeout=300,
    retry_count=2,
    dependencies=[
        {
            "capability": "process_with_tools",
            "tags": ["+openai"],  # tag time is optional (plus to have)
        },
        {
            "capability": "convert_tool_format",
            "tags": ["+openai"],  # tag time is optional (plus to have)
        }
    ],
    tags=["pdf", "text-extraction", "document-processing"]
)

async def extract_text_from_pdf(file_path: str, extraction_method: str = "auto", llm_service: McpAgent = None, convert_tool_format: McpAgent = None) -> Dict[str, Any]:
    """Extract text content from a PDF file."""
    try:
        import fitz
        import httpx
        import tempfile
        import os
        
        logger.info(f"Extracting text from PDF: {file_path} (method: {extraction_method})")
        
        # Handle MinIO URLs by downloading first
        local_file_path = file_path
        temp_file = None
        
        if file_path.startswith("http://") or file_path.startswith("https://"):
            logger.info(f"Downloading file from URL: {file_path}")
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.get(file_path)
                    response.raise_for_status()
                    
                    # Create temporary file
                    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                    temp_file.write(response.content)
                    temp_file.close()
                    local_file_path = temp_file.name
                    logger.info(f"Downloaded to temporary file: {local_file_path}")
            except Exception as e:
                logger.error(f"Failed to download file from URL: {e}")
                return {
                    "success": False,
                    "error": f"Failed to download file from URL: {str(e)}",
                    "file_path": file_path,
                    "timestamp": datetime.now().isoformat(),
                    "extraction_method": extraction_method
                }

        doc = fitz.open(local_file_path)
        text = ""
        page_count = len(doc)
        
        for page_num in range(page_count):
            page = doc.load_page(page_num)
            text += page.get_text()

        doc.close()
        
        # Clean up temporary file if created
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
                logger.info(f"Cleaned up temporary file: {temp_file.name}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")

        # Calculate basic text statistics
        text_stats = {
            "char_count": len(text),
            "word_count": len(text.split()),
            "line_count": len(text.split('\n')),
            "pages_processed": page_count,
            "total_pages": page_count
        }
        
        # Extract basic sections using simple text parsing
        basic_sections = extract_basic_sections(text)
        
        result = {
            "success": True,
            "text_content": text,
            "page_count": page_count,
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "extraction_method": extraction_method,  # Required by backend
            "sections": basic_sections,  # For backend's structured_data
            "text_stats": text_stats,
            "analysis_enhanced": False  # Will be set to True if LLM analysis succeeds
        }
        
        # Enhanced analysis with LLM if available
        if llm_service and text.strip():
            try:
                logger.info("Enhancing PDF extraction with LLM analysis")
                
                # Define profile analysis tool schema optimized for role matching
                profile_analysis_tool = {
                    "name": "analyze_resume_for_matching",
                    "description": "Analyze resume content and extract profile data optimized for role matching",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "categories": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["investment_management", "legal_compliance", "marketing", "operations", "relationship_management", "sales", "technology"]
                                },
                                "maxItems": 3,
                                "description": "Business categories that match this candidate's background (max 3, ordered by relevance)"
                            },
                            "experience_level": {
                                "type": "string",
                                "enum": ["intern", "junior", "mid", "senior", "lead", "principal"],
                                "description": "Overall experience level based on career progression and responsibilities"
                            },
                            "years_experience": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 50,
                                "description": "Total years of professional experience"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "maxItems": 20,
                                "description": "Skills, technologies, tools, and competencies for role matching"
                            },
                            "professional_summary": {
                                "type": "string",
                                "maxLength": 300,
                                "description": "Concise professional summary (2-3 sentences)"
                            },
                            "education_level": {
                                "type": "string",
                                "description": "Highest education level achieved"
                            },
                            "confidence_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "LLM confidence in the profile analysis"
                            },
                            "profile_strength": {
                                "type": "string",
                                "enum": ["excellent", "good", "average", "needs_improvement"],
                                "description": "Overall profile strength assessment"
                            }
                        },
                        "required": ["categories", "experience_level", "years_experience", "tags", "professional_summary"]
                    }
                }
                
                # Convert tools to appropriate format for the LLM provider
                logger.info("Converting profile analysis tool format for LLM provider")
                converted_tools = [profile_analysis_tool]  # Default to Claude format
                
                if convert_tool_format:
                    try:
                        converted_tools = await convert_tool_format(tools=[profile_analysis_tool])
                        logger.info(f"Successfully converted {len(converted_tools)} profile analysis tools for LLM provider")
                    except Exception as tool_convert_error:
                        logger.warning(f"Profile tool conversion failed, using original format: {tool_convert_error}")
                        converted_tools = [profile_analysis_tool]
                else:
                    logger.info("Tool conversion service not available, using Claude format for resume analysis")

                # Create profile analysis system prompt for role matching
                analysis_system_prompt = f"""You are a professional profile analysis expert. Analyze the provided resume/CV text and extract profile data optimized for role matching systems.

RESUME/CV CONTENT TO ANALYZE:
{text[:3000]}{'...' if len(text) > 3000 else ''}

Instructions:
- Identify 1-3 business categories this candidate best fits (investment_management, legal_compliance, marketing, operations, relationship_management, sales, technology) ordered by relevance
- Determine overall experience level (intern, junior, mid, senior, lead, principal) based on career progression and responsibilities
- Extract total years of professional experience as a number (convert "over X years" to actual number)
- Create a comprehensive tags list of skills, technologies, tools, and competencies (up to 20 items)
- Write a concise professional summary (2-3 sentences, max 300 characters)
- Identify highest education level achieved
- Rate your confidence in this analysis (0.0-1.0)
- Assess overall profile strength (excellent, good, average, needs_improvement)

Focus on extracting data that enables precise candidate-role matching. Categories should reflect the candidate's primary and secondary areas of expertise. Tags should include both technical skills and soft skills relevant for matching.

Use the provided tool to return your analysis in the exact structured format."""

                # Call LLM service with converted tools
                logger.info("Calling LLM service for profile analysis")
                logger.info(f"Text length: {len(text)} characters")
                logger.info(f"Tool name: {profile_analysis_tool['name']}")
                logger.info(f"Converted tools count: {len(converted_tools)}")
                
                analysis_result = await llm_service(
                    text="Analyze this resume/CV document content for role matching using the provided tool.",
                    system_prompt=analysis_system_prompt,
                    messages=[],  # Empty messages array
                    tools=converted_tools,
                    force_tool_use=True,
                    temperature=0.1
                )
                
                logger.info("LLM service call completed for profile analysis")
                
                if analysis_result and analysis_result.get("success") and analysis_result.get("tool_calls"):
                    # Extract profile analysis from tool calls 
                    tool_calls = analysis_result.get("tool_calls", [])
                    if len(tool_calls) > 0:
                        profile_data = tool_calls[0].get("parameters", {})
                        
                        # Inject AI provider and model from LLM service response
                        profile_data["ai_provider"] = analysis_result.get("provider", "unknown")
                        profile_data["ai_model"] = analysis_result.get("model", "unknown")
                        
                        result["profile_analysis"] = profile_data
                        result["analysis_enhanced"] = True
                        result["summary"] = profile_data.get("professional_summary", "Profile analysis completed")
                        logger.info(f"Profile analysis completed - AI provider: {profile_data['ai_provider']}, model: {profile_data['ai_model']}")
                        logger.info(f"Categories: {profile_data.get('categories', [])}")
                        logger.info(f"Experience level: {profile_data.get('experience_level', 'N/A')}")
                        logger.info(f"Profile strength: {profile_data.get('profile_strength', 'N/A')}")
                    else:
                        logger.warning("No tool calls found in LLM response for profile analysis")
                        result["analysis_enhanced"] = False
                        result["summary"] = "Profile analysis failed - no tool calls"
                else:
                    logger.warning("LLM profile analysis failed or returned no results")
                    result["analysis_enhanced"] = False
                    result["summary"] = "Profile analysis failed"
                    
            except Exception as e:
                logger.error(f"LLM profile analysis failed: {e}")
                result["analysis_enhanced"] = False
                result["analysis_error"] = str(e)
                result["summary"] = "Profile analysis failed due to error"

        # Add fallback summary if LLM is not available or failed
        if "summary" not in result:
            # Generate basic summary from text stats
            word_count = result["text_stats"]["word_count"]
            page_count = result["page_count"]
            sections_count = len(result["sections"])
            result["summary"] = f"Document with {word_count} words across {page_count} page(s), containing {sections_count} identified sections."

        return result

    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "extraction_method": extraction_method
        }


@app.tool()
@mesh.tool(capability="health_check", tags=["pdf_service", "document_processing", "text_extraction"])
def get_agent_status() -> Dict[str, Any]:
    """Get agent status and configuration."""
    return {
        "agent_name": AGENT_NAME,
        "port": HTTP_PORT,
        "status": "healthy",
        "capabilities": ["text_extraction", "document_analysis", "structured_data_extraction"],
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# MCP Mesh Agent Class for registration - same pattern as working agents
@mesh.agent(
    name="pdf-extractor",
    auto_run=True
)
class PDFExtractorAgent(McpAgent):
    """
    PDF Extractor Agent for AI Interviewer System
    
    Provides comprehensive PDF processing capabilities through MCP Mesh:
    1. Text extraction from PDF files with PyMuPDF
    2. Enhanced document analysis via LLM service integration
    3. Structured data extraction (contact info, skills, experience, etc.)
    4. Document type classification and quality scoring
    5. Tool format conversion for different LLM providers
    6. Agent status monitoring and health checks
    
    MCP Mesh Dependencies:
    - llm-service: For enhanced document analysis and insights
    - tool-conversion: For cross-LLM provider compatibility
    """
    
    def __init__(self):
        logger.info("Initializing PDF Extractor Agent v1.0.0")
        logger.info("PDF processing capabilities ready:")
        logger.info("  - Text extraction with PyMuPDF")
        logger.info("  - Enhanced document analysis via LLM service")
        logger.info("  - Structured data extraction and classification")
        logger.info("  - Tool format conversion for LLM compatibility")
        logger.info("Agent ready for comprehensive PDF processing requests")


# MCP Mesh handles everything automatically:
# - FastMCP server discovery and startup  
# - HTTP server on port 9093
# - Service registration with mesh registry
