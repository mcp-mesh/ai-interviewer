"""
Phase 2 Backend - Files API Routes

Clean delegation to file_agent via MCP Mesh dependency injection.
No authentication checks for testing phase.
"""

import logging

import mesh
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from mesh.types import McpMeshAgent

from app.models.schemas import (
    FileUploadResponse,
    ErrorResponse
)
from app.utils.recaptcha import verify_recaptcha_token, get_recaptcha_config
from app.utils.minio import upload_resume_to_minio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["files"])


@router.post("/resume", response_model=FileUploadResponse)
@mesh.route(dependencies=["process_resume_upload"])
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    recaptcha_token: str = Form(...),
    process_with_ai: bool = Form(True),
    user_agent: McpMeshAgent = None
) -> FileUploadResponse:
    """
    Upload and process user resume file - Backend Gateway Pattern.
    
    Backend responsibilities:
    1. Verify reCAPTCHA for security
    2. Upload binary PDF to MinIO (since MCP can't handle binary)
    3. Call user_agent with MinIO URL + user_email
    
    User_agent handles all business logic (user verification, PDF processing, database updates).
    """
    try:
        # Verify reCAPTCHA token first
        logger.info("Verifying reCAPTCHA token for resume upload")
        recaptcha_result = await verify_recaptcha_token(recaptcha_token, "upload_resume")
        
        if not recaptcha_result.get("success"):
            error_msg = recaptcha_result.get("error", "reCAPTCHA verification failed")
            logger.warning(f"reCAPTCHA verification failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=f"Security verification failed: {error_msg}"
            )
        
        logger.info(f"reCAPTCHA verified successfully with score: {recaptcha_result.get('score', 'N/A')}")
        
        # Extract user info from JWT token (nginx already validated OAuth)
        from app.utils.auth import require_user_from_request
        user_info = require_user_from_request(request)
        user_email = user_info["email"]
        first_name = user_info.get("first_name", "")
        last_name = user_info.get("last_name", "")
        
        logger.info(f"Gateway processing file upload for: {user_email}")
        
        # Basic file validation (minimal gateway responsibility)
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        # Gateway responsibility: Upload binary file to MinIO (since MCP can't handle binary)
        logger.info(f"Gateway uploading file to MinIO: {file.filename}")
        minio_result = await upload_resume_to_minio(
            file_content=file_content,
            filename=file.filename, 
            user_email=user_email
        )
        
        if not minio_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to upload file to storage")
        
        logger.info(f"Gateway uploaded to MinIO: {minio_result['file_path']}")
        
        # Gateway responsibility: Delegate ALL business logic to user_agent
        logger.info(f"Gateway calling user_agent for complete resume processing")
        
        # Single call to user_agent with MinIO URL - user_agent handles everything else
        processing_result = await user_agent(
            user_email=user_email,
            minio_url=minio_result["minio_url"],
            file_path=minio_result["file_path"],
            filename=file.filename,
            file_size=len(file_content),
            uploaded_at=minio_result["uploaded_at"],
            process_with_ai=process_with_ai
        )
        
        # Gateway just returns user_agent results with minimal processing
        if not processing_result.get("success"):
            error_msg = processing_result.get("error", "Resume processing failed")
            logger.error(f"User agent processing failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info("Gateway successfully processed resume upload via user_agent")
        
        # Return results from user_agent (backend doesn't add business logic)
        return FileUploadResponse(
            success=True,
            upload={
                "file_id": minio_result["file_path"].split("/")[-1].split(".")[0],
                "filename": file.filename,
                "file_path": minio_result["file_path"],
                "file_size": len(file_content),
                "content_type": file.content_type or "application/pdf",
                "uploaded_at": minio_result["uploaded_at"],
                "user_email": user_email
            },
            processed_data=processing_result.get("processed_data"),
            profile_updated=processing_result.get("profile_updated", False),
            message=processing_result.get("message", "Resume processed successfully")
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


