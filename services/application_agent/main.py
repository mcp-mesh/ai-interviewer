#!/usr/bin/env python3
"""
Application Agent - MCP Mesh Agent for Application Management

Modular Phase 2 implementation with step-specific handlers and smart resume logic.
Clean architecture with separated concerns: main.py orchestrates, steps/ handle details.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

import mesh
from fastmcp import FastMCP
from mesh.types import McpAgent, McpMeshAgent

# Import database components
from .database import create_tables, test_connections

# Import modular components
from .utils import (
    get_or_create_application, 
    update_application_step,
    format_prefill_response,
    format_step_save_response,
    format_error_response,
    get_next_step,
    is_final_step
)
from .steps import get_step_handler

# Create FastMCP app instance
app = FastMCP("Application Management Agent")

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database at startup
logger.info("🚀 Initializing Application Agent v3.0 (Modular Architecture)")

# Test database connections
connections = test_connections()
if connections["postgres"]:
    logger.info("✅ PostgreSQL connection successful")
    if create_tables():
        logger.info("✅ Database schema initialized")
    else:
        logger.error("❌ Failed to initialize database schema")
else:
    logger.error("❌ PostgreSQL connection failed")
    
if connections["redis"]:
    logger.info("✅ Redis connection successful")
else:
    logger.error("❌ Redis connection failed")

logger.info("✅ Application Agent ready with modular step processing")


@app.tool()
@mesh.tool(
    capability="application_start_with_prefill",
    dependencies=[
        {"capability": "get_resume_text"},
        {"capability": "process_with_tools", "tags": ["+openai"]},
        {"capability": "convert_tool_format", "tags": ["+openai"]},
        {"capability": "job_details_get"}
    ],
    tags=["application-management", "step-specific-llm", "intelligent-autofill"],
    description="Start application with smart resume logic - returns target step with prefill data"
)
async def application_start_with_prefill(
    job_id: str,
    user_email: str,
    user_agent: McpMeshAgent = None,
    llm_service: McpMeshAgent = None,
    convert_tool_format: McpMeshAgent = None,
    job_agent: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Start application with smart resume logic:
    - Check for existing application (implements user's resume feature)
    - Return target step based on current progress
    - Generate prefill data for target step using appropriate handler
    
    Args:
        job_id: Job ID to apply for
        user_email: User's email address
        user_agent: MCP Mesh agent for user operations
        llm_service: MCP Mesh agent for LLM processing
        convert_tool_format: Tool format converter for LLM compatibility
        job_agent: MCP Mesh agent for job operations
        
    Returns:
        Dict with application details and target step prefill data
    """
    try:
        logger.info(f"Starting application: user={user_email}, job={job_id}")
        
        # 1. Get or create application (implements smart resume logic)
        application = await get_or_create_application(user_email, job_id)
        target_step_str = application["step"]
        
        # Convert step string to integer for handler (STEP_1 -> 1)
        target_step = int(target_step_str.replace("STEP_", ""))
        
        logger.info(f"Target step for user: {target_step} (status: {application['status']})")
        
        # 2. Get resume text for LLM processing
        resume_text = ""
        if user_agent:
            try:
                resume_result = await user_agent(user_email=user_email)
                if resume_result.get("success") and resume_result.get("text_content"):
                    resume_text = resume_result["text_content"]
                    logger.info(f"Retrieved resume text: {len(resume_text)} characters")
                else:
                    logger.info("No resume text available for prefill generation")
            except Exception as resume_error:
                logger.warning(f"Failed to get resume text: {resume_error}")
        
        # 3. Generate prefill data using appropriate step handler
        step_handler = get_step_handler(target_step)
        
        # Prepare handler arguments
        handler_args = {
            "application_id": application["id"],
            "resume_text": resume_text,
            "llm_service": llm_service,
            "convert_tool_format": convert_tool_format,
            "save_data": False  # Don't save on start, only generate prefill
        }
        
        # Add job_agent for step 6 (review) which needs job details
        if target_step == 6 and job_agent:
            handler_args["job_agent"] = job_agent
        
        step_result = await step_handler(**handler_args)
        
        if not step_result.get("success"):
            logger.error(f"Step {target_step} processing failed: {step_result.get('error')}")
            return format_error_response(
                error=f"Failed to generate prefill for step {target_step}",
                details={"step_error": step_result.get("error")}
            )
        
        # 4. Format successful response
        step_info = {
            "step_number": target_step,
            "step_name": step_result.get("step_name"),
            "step_title": step_result.get("step_title"),
            "step_description": step_result.get("step_description")
        }
        
        logger.info(f"Successfully generated prefill for step {target_step}")
        
        return format_prefill_response(
            target_step=target_step,
            prefill_data=step_result.get("prefill_data", {}),
            application_id=application["id"],
            step_info=step_info,
            message=f"Application ready for step {target_step}"
        )
        
    except Exception as e:
        logger.error(f"Application start failed: {e}")
        return format_error_response(
            error="Failed to start application",
            details={"exception": str(e)}
        )


@app.tool()
@mesh.tool(
    capability="application_step_save_with_next_prefill",
    dependencies=[
        {"capability": "get_resume_text"},
        {"capability": "process_with_tools", "tags": ["+openai"]},
        {"capability": "convert_tool_format", "tags": ["+openai"]},
        {"capability": "job_details_get"}
    ],
    tags=["application-management", "step-management", "intelligent-autofill"],
    description="Save current step data and return next step prefill data"
)
async def application_step_save_with_next_prefill(
    application_id: str,
    step_number: int,
    step_data: Dict[str, Any],
    user_email: str,
    user_agent: McpMeshAgent = None,
    llm_service: McpMeshAgent = None,
    convert_tool_format: McpMeshAgent = None,
    job_agent: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Save current step data and return next step prefill data.
    
    Args:
        application_id: Application ID
        step_number: Current step number (1-6)
        step_data: Data to save for current step
        user_email: User email for resume lookup
        user_agent: MCP Mesh agent for user operations
        llm_service: MCP Mesh agent for LLM processing
        convert_tool_format: Tool format converter
        job_agent: MCP Mesh agent for job operations
        
    Returns:
        Dict with save status and next step prefill data
    """
    try:
        logger.info(f"Saving step {step_number} for application {application_id}")
        
        # 1. Get current step handler and save data
        current_step_handler = get_step_handler(step_number)
        
        # Save current step 
        save_handler_args = {
            "application_id": application_id,
            "resume_text": "",  # Not needed for saving
            "step_data": step_data,  # Pass the data to save
            "save_data": True
        }
        
        # Add required MCP agents for step 6 (review) which needs them for submission
        if step_number == 6:
            save_handler_args.update({
                "job_agent": job_agent,
                "user_agent": user_agent, 
                "llm_service": llm_service,
                "convert_tool_format": convert_tool_format
            })
        
        save_result = await current_step_handler(**save_handler_args)
        
        if not save_result.get("success"):
            logger.error(f"Failed to save step {step_number}: {save_result.get('error')}")
            return format_error_response(
                error=f"Failed to save step {step_number}",
                details={"save_error": save_result.get("error")}
            )
        
        # 2. Update application to next step
        next_step_number = get_next_step(step_number)
        
        if next_step_number is None:
            # Final step reached - mark as completed
            await update_application_step(
                application_id=application_id,
                new_step=step_number,
                status="COMPLETED"
            )
            
            logger.info(f"Application {application_id} completed successfully")
            
            return format_step_save_response(
                next_step=None,
                prefill_data=None,
                application_id=application_id,
                saved_step=step_number,
                is_final=True,
                message="Application completed successfully"
            )
        
        # 3. Update application to next step
        await update_application_step(
            application_id=application_id,
            new_step=next_step_number,
            status="STARTED"
        )
        
        # 4. Get resume text for next step prefill
        resume_text = ""
        if user_agent:
            try:
                resume_result = await user_agent(user_email=user_email)
                if resume_result.get("success") and resume_result.get("text_content"):
                    resume_text = resume_result["text_content"]
                    logger.info(f"Retrieved resume for next step prefill: {len(resume_text)} chars")
            except Exception as resume_error:
                logger.warning(f"Failed to get resume for next step: {resume_error}")
        
        # 5. Generate prefill for next step
        next_step_handler = get_step_handler(next_step_number)
        
        # Prepare handler arguments
        handler_args = {
            "application_id": application_id,
            "resume_text": resume_text,
            "llm_service": llm_service,
            "convert_tool_format": convert_tool_format,
            "save_data": False  # Don't save, just generate prefill
        }
        
        # Add job_agent for step 6 (review) which needs job details
        if next_step_number == 6 and job_agent:
            handler_args["job_agent"] = job_agent
        
        next_step_result = await next_step_handler(**handler_args)
        
        if not next_step_result.get("success"):
            logger.warning(f"Next step prefill failed: {next_step_result.get('error')}")
            # Still return success for save, but with empty prefill
            next_step_prefill = {}
        else:
            next_step_prefill = next_step_result.get("prefill_data", {})
            logger.info(f"Generated prefill for step {next_step_number}")
        
        return format_step_save_response(
            next_step=next_step_number,
            prefill_data=next_step_prefill,
            application_id=application_id,
            saved_step=step_number,
            message=f"Step {step_number} saved, ready for step {next_step_number}"
        )
        
    except Exception as e:
        logger.error(f"Step save failed: {e}")
        return format_error_response(
            error="Failed to save step data",
            details={"exception": str(e)}
        )


@app.tool()
@mesh.tool(
    capability="application_get_status",
    tags=["application-management", "status-check"],
    description="Get current application status and progress"
)
async def application_get_status(
    application_id: str
) -> Dict[str, Any]:
    """
    Get current application status and progress.
    
    Args:
        application_id: Application ID
        
    Returns:
        Dict with application status and progress information
    """
    try:
        from .utils.application_state import get_application_state
        from .utils.response_formatting import format_application_status_response
        
        # This would need to be implemented to get by ID instead of user+job
        # For now, return a placeholder
        logger.info(f"Getting status for application {application_id}")
        
        return {
            "success": True,
            "message": "Status check not yet implemented",
            "application_id": application_id
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return format_error_response(
            error="Failed to get application status",
            details={"exception": str(e)}
        )


@app.tool()
@mesh.tool(
    capability="health_check",
    tags=["application-management", "monitoring"],
    description="Application agent health check"
)
def get_agent_status() -> Dict[str, Any]:
    """Get agent health status."""
    return {
        "agent_name": "application-agent",
        "version": "3.0.0",
        "status": "healthy",
        "architecture": "modular",
        "capabilities": [
            "application_start_with_prefill",
            "application_step_save_with_next_prefill", 
            "application_get_status"
        ],
        "step_handlers": [
            "personal_info",
            "experience", 
            "questions",
            "disclosures",
            "identity",
            "review"
        ],
        "timestamp": datetime.now().isoformat()
    }


# MCP Mesh Agent Class for registration
@mesh.agent(
    name="application-agent",
    auto_run=True
)
class ApplicationAgent(McpAgent):
    """
    Application Agent for AI Interviewer Phase 2
    
    Modular architecture with step-specific handlers:
    - Smart resume logic (checks existing progress)
    - Step-specific LLM extraction with dedicated handlers
    - Clean separation of concerns (utils, steps, tool_specs)
    - Comprehensive database persistence with PostgreSQL + Redis
    - Standardized response formatting
    
    Key Features:
    1. Intelligent application resume - returns user to correct step
    2. Step-specific LLM extraction using dedicated tool specifications
    3. Modular handler architecture for maintainability
    4. Database persistence with upsert logic
    5. Comprehensive error handling and logging
    """
    
    def __init__(self):
        logger.info("Application Agent v3.0 initialized with modular architecture")
        logger.info("Ready for intelligent application processing with step-specific handlers")


if __name__ == "__main__":
    logger.info("Application Agent v3.0 starting with modular architecture...")