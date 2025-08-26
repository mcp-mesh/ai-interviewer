"""
Phase 2 Backend - Applications API Routes

Clean delegation to application_agent via MCP Mesh dependency injection.
No authentication checks for testing phase.
"""

import logging
from typing import Optional

import mesh
from fastapi import APIRouter, HTTPException, Request, Depends
from mesh.types import McpMeshAgent

from app.models.schemas import (
    ApplicationListResponse,
    ApplicationDetailResponse, 
    ApplicationSubmission,
    ApplicationStatusUpdate,
    ErrorResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationDetailResponse)
@mesh.route(dependencies=["application_submit"])
async def submit_application(
    request: Request,
    app_data: ApplicationSubmission,
    application_agent: McpMeshAgent = None
) -> ApplicationDetailResponse:
    """
    Submit a new job application.
    
    Delegates to application_agent's application_submit capability.
    """
    try:
        # For testing phase, we'll use a mock user email
        # In real implementation, this would come from JWT token
        user_email = "john@example.com"  # Mock user for testing
        
        logger.info(f"Submitting application for user {user_email} to job {app_data.job_id}")
        
        # Delegate to application agent
        result = await application_agent(
            user_email=user_email,
            job_id=app_data.job_id,
            application_data=app_data.dict()
        )
        
        if not result.get("success"):
            error_msg = result.get("error", "Application submission failed")
            logger.error(f"Failed to submit application: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Application submitted successfully: {result['application']['id']}")
        
        return ApplicationDetailResponse(
            data=result["application"],
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit application: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit application: {str(e)}")


@router.get("", response_model=ApplicationListResponse)
@mesh.route(dependencies=["applications_user_list"])
async def list_user_applications(
    request: Request,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    application_agent: McpMeshAgent = None
) -> ApplicationListResponse:
    """
    Get all applications for the current user.
    
    Delegates to application_agent's applications_user_list capability.
    """
    try:
        # For testing phase, we'll use a mock user email
        user_email = "john@example.com"  # Mock user for testing
        
        logger.info(f"Getting applications for user {user_email}, page {page}, status filter: {status}")
        
        # Delegate to application agent
        result = await application_agent(
            user_email=user_email,
            page=page,
            limit=limit,
            status_filter=status
        )
        
        if not result.get("success", True):
            error_msg = result.get("error", "Failed to retrieve applications")
            logger.error(f"Failed to get applications: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Retrieved {len(result.get('applications', []))} applications for user")
        
        return ApplicationListResponse(
            data=result.get("applications", []),
            total=result.get("total", 0),
            page=page,
            limit=limit,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve applications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve applications: {str(e)}")


@router.put("/{application_id}/status", response_model=ApplicationDetailResponse)
@mesh.route(dependencies=["application_status_update"])
async def update_application_status(
    application_id: str,
    status_update: ApplicationStatusUpdate,
    application_agent: McpMeshAgent = None
) -> ApplicationDetailResponse:
    """
    Update application status (admin function).
    
    Delegates to application_agent's application_status_update capability.
    """
    try:
        logger.info(f"Updating application {application_id} status to {status_update.status}")
        
        # Delegate to application agent
        result = await application_agent(
            application_id=application_id,
            new_status=status_update.status,
            admin_notes=status_update.admin_notes
        )
        
        if not result.get("success"):
            error_msg = result.get("error", "Status update failed")
            logger.error(f"Failed to update application status: {error_msg}")
            
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Application {application_id} status updated successfully")
        
        return ApplicationDetailResponse(
            data=result["application"],
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update application status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update application status: {str(e)}")