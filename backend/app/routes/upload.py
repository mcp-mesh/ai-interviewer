"""
File upload routes - MCP Mesh Integration with hybrid data storage.
"""

import logging
import mesh
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Depends
from mesh.types import McpMeshAgent
from sqlalchemy.orm import Session

from app.services.file_service import FileService
from app.services.auth_service import AuthService
from app.services.hybrid_data_service import HybridDataService
from app.database.postgres import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])

@router.post("/user/upload-resume")
@mesh.route(dependencies=[
    "extract_text_from_pdf",
    {
        "capability": "process_with_tools",
        "tags": ["+claude"],
    }
])
async def upload_user_resume(
    request: Request, 
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    pdf_processor: McpMeshAgent = None,  # Injected PDF extraction capability
    llm_service: McpMeshAgent = None  # Injected LLM service for skill extraction
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
        
        # Extract text content for skill analysis
        resume_text = extraction_result.get("text_content", "") if extraction_result else ""
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="No text content could be extracted from the PDF")
        
        # Prepare file metadata for hybrid service
        file_metadata = {
            "filename": file.filename,
            "user_name": user_data.get("name"),
            "uploaded_at": minio_result.get("uploaded_at"),
            "file_size": len(file_content),
            "page_count": extraction_result.get("page_count", 0) if extraction_result else 0,
            "minio_path": minio_result.get("path"),
            "sections": extraction_result.get("sections", {}) if extraction_result else {},
            "text_stats": extraction_result.get("text_stats", {}) if extraction_result else {}
        }
        
        # Process resume using hybrid data service (LLM skill extraction + dual storage)
        if llm_service:
            logger.info("Processing resume with LLM skill extraction")
            processing_result = await HybridDataService.process_resume_upload(
                user_email, resume_text, file_metadata, llm_service, db
            )
            
            if not processing_result.get("success"):
                error_msg = processing_result.get("error", "Unknown error during skill extraction")
                logger.error(f"Failed to process resume: {error_msg}")
                raise HTTPException(status_code=500, detail=f"Failed to process resume: {error_msg}")
            
            # Also update Redis with legacy resume format for backward compatibility
            legacy_resume_data = {
                "filename": file.filename,
                "extracted_text": resume_text,
                "uploaded_at": minio_result.get("uploaded_at"),
                "file_size": len(file_content),
                "minio_path": minio_result.get("path"),
                "structured_analysis": processing_result
            }
            
            AuthService.update_user_data(user_email, {"resume": legacy_resume_data})
            
            return {
                "upload_success": True,
                "filename": file.filename,
                "minio_path": minio_result.get("path"),
                "skills_extracted": processing_result.get("skills_extracted", 0),
                "experience_level": processing_result.get("experience_level"),
                "profile_complete": processing_result.get("profile_complete", False),
                "message": "Resume uploaded and processed successfully with skill extraction",
                "hybrid_storage": True
            }
        else:
            # Fallback: save basic resume data without LLM extraction
            logger.warning("No LLM service available - saving resume without skill extraction")
            
            # Create basic profile
            profile_data = {
                "name": user_data.get("name"),
                "resume_content": resume_text,
                "resume_metadata": file_metadata,
                "is_profile_complete": False,
                "skills": {},
                "leadership_experience": {},
                "career_progression": []
            }
            
            success = HybridDataService.create_or_update_profile(user_email, profile_data, db)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to save resume data")
            
            # Update Redis for backward compatibility
            legacy_resume_data = {
                "filename": file.filename,
                "extracted_text": resume_text,
                "uploaded_at": minio_result.get("uploaded_at"),
                "file_size": len(file_content),
                "minio_path": minio_result.get("path")
            }
            
            AuthService.update_user_data(user_email, {"resume": legacy_resume_data})
            
            return {
                "upload_success": True,
                "filename": file.filename,
                "minio_path": minio_result.get("path"),
                "message": "Resume uploaded successfully (skill extraction unavailable)",
                "requires_skill_extraction": True,
                "hybrid_storage": True
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))