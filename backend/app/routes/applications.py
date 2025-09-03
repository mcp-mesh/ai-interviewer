"""
Phase 2 Backend - Applications API Routes

Clean delegation to application_agent via MCP Mesh dependency injection.
Implements the 6-step application wizard with real MCP integration.
"""

import logging
from typing import Optional, Dict, Any

import mesh
from fastapi import APIRouter, HTTPException, Request
from mesh.types import McpMeshAgent
from pydantic import BaseModel

from app.utils.auth import require_user_from_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationStepRequest(BaseModel):
    """Request model for application step operations"""
    job_id: Optional[str] = None  # Required for starting new applications
    step_data: Optional[Dict[str, Any]] = {}


class ApplicationStepResponse(BaseModel):
    """Response model for application step operations"""
    success: bool = True
    message: str
    data: Dict[str, Any]
    timestamp: str


@router.post("/{application_id}/steps/{step_number}", response_model=ApplicationStepResponse)
@mesh.route(dependencies=[
    "application_start_with_prefill",
    "application_step_save_with_next_prefill"
])
async def handle_application_step(
    request: Request,
    application_id: str,
    step_number: int,
    request_data: ApplicationStepRequest,
    application_start_with_prefill: McpMeshAgent = None,
    application_step_save_with_next_prefill: McpMeshAgent = None
) -> ApplicationStepResponse:
    """
    Handle application step operations - start new or save existing step.
    
    - For new applications: use application_id="new" and provide job_id
    - For existing applications: use real application_id and provide step_data
    
    URL Pattern: /api/applications/{application_id}/steps/{step_number}
    
    Examples:
    - Start new application: POST /api/applications/new/steps/1 with job_id
    - Save step 1: POST /api/applications/uuid/steps/1 with step_data
    """
    try:
        # Extract user info from JWT token - authentication required
        user_info = require_user_from_request(request)
        user_email = user_info["email"]
        
        logger.info(f"Processing application step: app_id={application_id}, step={step_number}, user={user_email}")
        
        # Validate step number
        if step_number < 1 or step_number > 6:
            raise HTTPException(status_code=400, detail="Invalid step number. Must be 1-6.")
        
        # Determine if this is a new application start or existing step save
        if application_id == "new" or step_number == 0:
            # Start new application
            if not request_data.job_id:
                raise HTTPException(status_code=400, detail="job_id is required for starting new applications")
            
            logger.info(f"Starting new application for user {user_email} with job {request_data.job_id}")
            
            result = await application_start_with_prefill(
                job_id=request_data.job_id,
                user_email=user_email
            )
            
        else:
            # Save existing step and get next
            logger.info(f"Saving step {step_number} for application {application_id}")
            
            result = await application_step_save_with_next_prefill(
                application_id=application_id,
                step_number=step_number,
                step_data=request_data.step_data or {},
                user_email=user_email
            )
        
        # Check if MCP call was successful
        if not result.get("success"):
            error_msg = result.get("error", "Application operation failed")
            logger.error(f"MCP operation failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Application step operation successful: {result.get('message', 'Success')}")
        
        # Return the MCP response directly (already in correct format)
        return ApplicationStepResponse(
            success=result["success"],
            message=result["message"],
            data=result["data"],
            timestamp=result["timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process application step: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process application step: {str(e)}")


@router.get("/{application_id}/status")
@mesh.route(dependencies=["application_get_status"])
async def get_application_status(
    application_id: str,
    application_agent: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Get application status and progress information.
    
    Delegates to application_agent's application_get_status capability.
    """
    try:
        logger.info(f"Getting status for application: {application_id}")
        
        result = await application_agent(application_id=application_id)
        
        if not result.get("success"):
            error_msg = result.get("error", "Failed to get application status")
            logger.error(f"Failed to get application status: {error_msg}")
            
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Application status retrieved for: {result.get('application_id')}")
        
        # Handle current response format (just success + message + application_id)
        return {
            "success": True,
            "message": result.get("message", "Status retrieved"),
            "data": {
                "application_id": result.get("application_id"),
                "status": "in_progress",  # Placeholder until fully implemented
                "message": result.get("message")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get application status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get application status: {str(e)}")


@router.get("/{application_id}/review")
@mesh.route(dependencies=["application_get_review_data"])
async def get_application_review_data(
    request: Request,
    application_id: str,
    application_agent: McpMeshAgent = None
) -> Dict[str, Any]:
    """
    Get complete application review data for Step 6 (Review Your Application).
    
    Aggregates data from all steps and returns structured review information:
    - Personal information and contact details
    - Professional experience and skills 
    - Application preferences and work authorization
    - Attached documents (resume)
    - Job details and position information
    
    Requires authentication and delegates to application_agent's 
    application_get_review_data capability with job_agent integration.
    
    URL Pattern: /api/applications/{application_id}/review
    """
    try:
        # Extract user info from JWT token - authentication required
        user_info = require_user_from_request(request)
        user_email = user_info["email"]
        
        logger.info(f"Getting review data for application: {application_id} (user: {user_email})")
        
        result = await application_agent(application_id=application_id)
        
        if not result.get("success"):
            error_msg = result.get("error", "Failed to get application review data")
            logger.error(f"Failed to get application review data: {error_msg}")
            
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Application review data retrieved successfully for: {result.get('application_id')}")
        
        # Return the complete review data in the expected format
        return {
            "success": True,
            "message": "Review data retrieved successfully",
            "data": result.get("data", {}),
            "metadata": result.get("metadata", {}),
            "application_id": result.get("application_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get application review data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get application review data: {str(e)}")