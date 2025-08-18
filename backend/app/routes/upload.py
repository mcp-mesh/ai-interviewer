"""
File upload routes - MCP Mesh Integration.
"""

import logging
import mesh
from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from mesh.types import McpMeshAgent

from app.services.file_service import FileService
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])

@router.post("/user/upload-resume")
@mesh.route(dependencies=["extract_text_from_pdf"])
async def upload_user_resume(
    request: Request, 
    file: UploadFile = File(...),
    pdf_processor: McpMeshAgent = None  # Injected PDF extraction capability (variable name doesn't matter)
):
    """Upload and process user resume document using MCP Mesh dependency injection."""
    user_data = request.state.user
    user_email = user_data.get('email')
    logger.info(f"Resume upload by user: {user_email}")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF documents are supported"
        )
    
    # Validate file size (10MB limit)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 10MB"
        )
    
    # Read file content
    try:
        file_content = await file.read()
        logger.info(f"Resume uploaded: {file.filename} ({len(file_content)} bytes)")
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")
    
    try:
        # First upload to MinIO to get accessible URL
        file_service = FileService()
        minio_result = await file_service.upload_to_minio(file_content, file.filename, user_email)
        minio_url = minio_result.get("minio_url")
        
        # Then extract text using MCP Mesh injected capability with MinIO URL
        extraction_result = None
        if pdf_processor and minio_url:
            try:
                # Use MCP Mesh capability to extract text from PDF via MinIO URL
                logger.info("Using MCP Mesh PDF extraction capability with MinIO URL")
                extraction_result = await pdf_processor(
                    file_path=minio_url,  # Pass MinIO URL instead of filename
                    extraction_method="auto"
                )
                logger.info("PDF extraction completed successfully")
            except Exception as e:
                logger.error(f"PDF extraction failed: {e}")
                raise HTTPException(status_code=500, detail=f"PDF extraction failed: {e}")
        else:
            raise HTTPException(status_code=503, detail="PDF extractor service unavailable")
        
        # Prepare resume data for user profile - extract from actual response structure
        resume_data = {
            "filename": file.filename,
            "extracted_text": extraction_result.get("text_content", "") if extraction_result else "",
            "structured_analysis": extraction_result.get("structured_analysis", {}) if extraction_result else {},
            "sections": extraction_result.get("sections", {}) if extraction_result else {},
            "text_stats": extraction_result.get("text_stats", {}) if extraction_result else {},
            "analysis_enhanced": extraction_result.get("analysis_enhanced", False) if extraction_result else False,
            "summary": extraction_result.get("summary", "") if extraction_result else "",
            "uploaded_at": minio_result.get("uploaded_at"),
            "file_size": len(file_content),
            "page_count": extraction_result.get("page_count", 0) if extraction_result else 0,
            "minio_path": minio_result.get("path")
        }
        
        # Update user data with resume information - nest under "resume" key as expected by interview system  
        success = AuthService.update_user_data(user_email, {"resume": resume_data})
        if not success:
            logger.error("Failed to update user data with resume information")
            raise HTTPException(status_code=500, detail="Failed to save resume data")
        
        return {
            "upload_success": True,
            "filename": file.filename,
            "minio_path": minio_result.get("path"),
            "extraction_result": extraction_result,
            "resume_data": resume_data,
            "message": "Resume uploaded and processed successfully with MCP Mesh",
            "dependencies_used": {
                "extract_text_from_pdf": pdf_processor is not None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))