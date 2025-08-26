"""
Phase 2 Backend - Files API Routes

Clean delegation to file_agent via MCP Mesh dependency injection.
No authentication checks for testing phase.
"""

import logging

import mesh
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from mesh.types import McpMeshAgent

from app.models.schemas import (
    FileUploadResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["files"])


@router.post("/resume", response_model=FileUploadResponse)
@mesh.route(dependencies=["file_resume_upload"])
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    process_with_ai: bool = True,
    file_agent: McpMeshAgent = None
) -> FileUploadResponse:
    """
    Upload and process user resume file.
    
    Delegates to file_agent's file_resume_upload capability.
    """
    try:
        # For testing phase, we'll use a mock user email
        # In real implementation, this would come from JWT token
        user_email = "john@example.com"  # Mock user for testing
        
        logger.info(f"Processing resume upload for user: {user_email}, file: {file.filename}")
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Read file content to get size
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size (10MB limit)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size must be less than 10MB"
            )
        
        # Prepare file metadata
        file_data = {
            "filename": file.filename,
            "file_size": file_size,
            "content_type": file.content_type or "application/pdf"
        }
        
        # Delegate to file agent
        result = await file_agent(
            user_email=user_email,
            file_data=file_data,
            process_with_ai=process_with_ai
        )
        
        if not result.get("success"):
            error_msg = result.get("error", "File upload failed")
            logger.error(f"Failed to upload resume: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Resume uploaded successfully for user: {user_email}")
        
        return FileUploadResponse(
            success=True,
            upload=result["upload"],
            processed_data=result.get("processed_data"),
            profile_updated=result.get("profile_updated", False),
            message=result.get("message", "Resume uploaded successfully")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload resume: {str(e)}")


@router.get("/status/{file_id}")
@mesh.route(dependencies=["file_status_get"])
async def get_file_status(
    file_id: str,
    file_agent: McpMeshAgent = None
):
    """
    Get file upload and processing status.
    
    Delegates to file_agent's file_status_get capability.
    """
    try:
        logger.info(f"Getting file status for: {file_id}")
        
        # Delegate to file agent
        result = await file_agent(file_id=file_id)
        
        if not result.get("success"):
            error_msg = result.get("error", "File not found")
            logger.error(f"Failed to get file status: {error_msg}")
            
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"File status retrieved for: {file_id}")
        
        return {
            "success": True,
            "data": result["file"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get file status: {str(e)}")