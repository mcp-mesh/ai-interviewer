#!/usr/bin/env python3
"""
PDF Extractor Agent - Main Implementation

A simple PDF processing MCP Mesh agent for the AI Interviewer system.
"""

import logging
import os
import asyncio
from typing import Any, Dict
from datetime import datetime

import mesh
from fastmcp import FastMCP

# Import specific agent types for type hints
from mesh.types import McpAgent, McpMeshAgent

# Import comprehensive tool spec
from .tool_specs.comprehensive_resume_tools import get_comprehensive_resume_tool_spec

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


async def detailed_resume_analysis(
    full_text: str,
    user_agent: McpMeshAgent,
    llm_service: McpMeshAgent,
    user_email: str
):
    """
    Background task for comprehensive resume analysis.
    
    Extracts complete personal info and experience data for application prefill
    using the full resume text (no truncation).
    
    Args:
        full_text: Complete resume text content
        user_agent: User agent for storing results  
        llm_service: LLM agent for processing
        user_email: User's email address
    """
    try:
        logger.info(f"Starting detailed resume analysis for {user_email}")
        logger.info(f"Full text length: {len(full_text)} characters")
        
        # 1. Get comprehensive tool spec for Steps 1 & 2
        comprehensive_tool_spec = get_comprehensive_resume_tool_spec()
        
        # 2. LLM service will handle tool format conversion internally
        tools_to_use = [comprehensive_tool_spec]
        
        # 3. Create comprehensive system prompt
        comprehensive_prompt = f"""You are an expert resume analyzer for job application systems. Extract comprehensive data for Steps 1 & 2 of the application process.

FULL RESUME TEXT:
{full_text}

EXTRACT THE FOLLOWING DATA USING THE PROVIDED TOOL:

STEP 1 - PERSONAL INFORMATION:
- Full name, email address, phone number
- Complete address (street, city, state, country, postal code)
- LinkedIn profile, portfolio website, GitHub profile URLs
- Current professional title or desired position
- Brief professional summary (2-3 sentences, max 300 chars)

STEP 2 - EXPERIENCE INFORMATION:
- Complete work history (reverse chronological order)
- For each job: title, company, location, dates, key responsibilities, technologies used
- Total years of professional experience
- Top 20 technical skills across all experience
- Top 10 soft skills (leadership, communication, etc.)
- Education and certifications with degrees, institutions, years
- Industries worked in
- Management/leadership experience (yes/no)
- Current salary and salary expectations if mentioned

REQUIREMENTS:
- Extract ALL available information from the full resume text
- Be comprehensive - don't truncate or summarize work experience
- Include confidence scores for both personal_info and experience_info sections
- Format dates as MM/YYYY where possible
- Use the provided tool to return structured data

Focus on extracting data that will perfectly prefill job application forms with accurate, complete information."""
        
        # 4. Call LLM with comprehensive analysis
        result = await asyncio.wait_for(
            llm_service(
                text="Extract comprehensive resume data for application prefill",
                system_prompt=comprehensive_prompt,
                messages=[],
                tools=tools_to_use,
                force_tool_use=True,
                temperature=0.1
            ),
            timeout=300  # 5 minutes
        )
        
        # 5. Extract tool call results
        if result and result.get("success") and result.get("tool_calls"):
            tool_calls = result.get("tool_calls", [])
            if len(tool_calls) > 0:
                extracted_data = tool_calls[0].get("parameters", {})
                personal_info = extracted_data.get("personal_info", {})
                experience_info = extracted_data.get("experience_info", {})
                
                logger.info(f"LLM extraction completed for {user_email}")
                logger.info(f"Personal info confidence: {personal_info.get('confidence_score', 'N/A')}")
                logger.info(f"Experience info confidence: {experience_info.get('confidence_score', 'N/A')}")
                
                # 6. Store results via user agent
                update_result = await user_agent(
                    user_email=user_email,
                    personal_info=personal_info,
                    experience_info=experience_info
                )
                
                if update_result.get("success"):
                    logger.info(f"Successfully completed detailed analysis for {user_email}")
                else:
                    logger.error(f"Failed to store detailed analysis for {user_email}: {update_result.get('error')}")
            else:
                logger.warning(f"No tool calls in LLM result for {user_email}")
        else:
            logger.warning(f"LLM failed to extract comprehensive data for {user_email}")
            
    except asyncio.TimeoutError:
        logger.warning(f"Detailed analysis timeout (5 minutes) for {user_email}")
    except Exception as e:
        logger.error(f"Detailed analysis failed for {user_email}: {str(e)}")


# Simple PDF extraction function with enhanced LLM analysis
@app.tool()
@mesh.tool(
    capability="extract_text_from_pdf",
    timeout=300,
    retry_count=2,
    dependencies=[
        {
            "capability": "process_with_tools",
            "tags": ["+openai"],  # tag openai is optional (plus to have)
        },
        {
            "capability": "update_detailed_resume_analysis",
            "tags": ["user-management"],  # New user agent capability
        }
    ],
    tags=["pdf", "text-extraction", "document-processing"]
)

async def extract_text_from_pdf(
    file_path: str, 
    extraction_method: str = "auto",
    user_email: str = None,
    llm_service: McpAgent = None, 
    update_detailed_resume_analysis: McpAgent = None,
) -> Dict[str, Any]:
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
                
                # Define quick analysis tool schema - basic info only for speed
                profile_analysis_tool = {
                    "name": "analyze_resume_for_matching",
                    "description": "Quick resume validation and basic profile extraction",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "is_resume": {
                                "type": "boolean",
                                "description": "Whether the document appears to be a resume/CV"
                            },
                            "full_name": {
                                "type": "string",
                                "description": "Candidate's full name"
                            },
                            "experience_level": {
                                "type": "string",
                                "enum": ["intern", "junior", "mid", "senior", "lead", "principal"],
                                "description": "Overall experience level based on career progression"
                            },
                            "education_level": {
                                "type": "string",
                                "description": "Highest education level achieved (e.g., Bachelor's, Master's, PhD)"
                            },
                            "years_experience": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 50,
                                "description": "Total years of professional work experience"
                            },
                            "confidence_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "LLM confidence in this analysis"
                            }
                        },
                        "required": ["is_resume", "full_name", "experience_level", "education_level", "years_experience", "confidence_score"]
                    }
                }
                
                # LLM service will handle tool format conversion internally
                tools_to_use = [profile_analysis_tool]
                logger.info("Using profile analysis tool - LLM service will handle format conversion internally")

                # Create quick analysis system prompt with resume validation
                analysis_system_prompt = f"""You are a resume validation and analysis expert. Your task is to:
1. First validate if this document is actually a resume/CV
2. If it is a resume, extract basic profile information for quick processing

DOCUMENT CONTENT TO ANALYZE:
{text[:3000]}{'...' if len(text) > 3000 else ''}

IMPORTANT CONTEXT:
- You are receiving the first few pages of a document that may be a resume
- A resume may appear incomplete because you're only seeing the beginning
- Focus on typical resume indicators: name, contact info, work experience, education

VALIDATION CRITERIA:
- Does this look like a professional resume/CV?
- Look for: personal name, contact info, work history, education, skills
- Even if incomplete (first pages only), does it have resume structure?

EXTRACTION INSTRUCTIONS (only if is_resume=true):
- Extract candidate's full name
- Determine experience level: intern, junior, mid, senior, lead, principal
- Calculate total years of professional work experience (0-50)
- Identify highest education level (Bachelor's, Master's, PhD, High School, etc.)
- Rate your confidence in this analysis (0.0-1.0)

If this is NOT a resume (is_resume=false), still fill required fields with placeholder values but be honest about the validation.

Use the provided tool to return your analysis."""

                # Call LLM service with tools
                logger.info("Calling LLM service for profile analysis")
                logger.info(f"Text length: {len(text)} characters")
                logger.info(f"Tool name: {profile_analysis_tool['name']}")
                logger.info(f"Tools count: {len(tools_to_use)}")
                
                analysis_result = await llm_service(
                    text="Analyze this resume/CV document content for role matching using the provided tool.",
                    system_prompt=analysis_system_prompt,
                    messages=[],  # Empty messages array
                    tools=tools_to_use,
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

        # 🚀 Launch background detailed analysis task (don't wait)
        if (update_detailed_resume_analysis and user_email and llm_service and 
            text and len(text.strip()) > 0):
            
            logger.info(f"Starting background detailed analysis for {user_email}")
            asyncio.create_task(
                detailed_resume_analysis(
                    full_text=text,
                    user_agent=update_detailed_resume_analysis,
                    llm_service=llm_service,
                    user_email=user_email
                )
            )
        else:
            logger.info("Skipping detailed analysis - missing required parameters")

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
