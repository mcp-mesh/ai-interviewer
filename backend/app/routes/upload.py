"""
File upload routes - MCP Mesh Integration with hybrid data storage.
"""

import logging
from datetime import datetime
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
        
        # Process resume using Phase 2 profile analysis and single-source storage
        if llm_service:
            logger.info("Processing resume with Phase 2 profile analysis")
            
            # Extract profile analysis from PDF processor result
            profile_analysis = extraction_result.get("profile_analysis", {})
            
            if not profile_analysis:
                logger.error("No profile analysis returned from PDF processor")
                raise HTTPException(status_code=500, detail="Profile analysis failed - no data returned")
            
            # Create/update profile using Phase 2 schema
            processing_result = await HybridDataService.create_or_update_profile_from_resume(
                user_email, resume_text, file_metadata, profile_analysis, db
            )
            
            if not processing_result.get("success"):
                error_msg = processing_result.get("error", "Unknown error during profile creation")
                logger.error(f"Failed to create profile: {error_msg}")
                raise HTTPException(status_code=500, detail=f"Failed to create profile: {error_msg}")
            
            # No Redis redundancy - profile data is in PostgreSQL, session flags in Redis
            return {
                "upload_success": True,
                "filename": file.filename,
                "minio_path": minio_result.get("path"),
                "profile_analysis": {
                    "categories": profile_analysis.get("categories", []),
                    "experience_level": profile_analysis.get("experience_level"),
                    "years_experience": profile_analysis.get("years_experience", 0),
                    "tags_extracted": len(profile_analysis.get("tags", [])),
                    "confidence_score": profile_analysis.get("confidence_score", 0.0),
                    "profile_strength": profile_analysis.get("profile_strength", "average")
                },
                "profile_complete": processing_result.get("profile_complete", False),
                "ready_for_matching": processing_result.get("ready_for_matching", False),
                "message": "Resume processed and profile created successfully"
            }
        else:
            # Fallback: save basic resume data without LLM extraction
            logger.warning("No LLM service available - saving resume without profile analysis")
            
            # Create basic Phase 2 profile structure without LLM analysis
            basic_profile_data = {
                "name": user_data.get("name"),
                # Phase 2: Default/empty matching data
                "categories": [],  # Empty - requires manual categorization or re-upload
                "experience_level": None,  # Requires manual input or LLM analysis
                "years_experience": 0,
                "tags": [],  # Empty - requires LLM analysis
                # Resume storage
                "resume_content": resume_text,
                "resume_filename": file.filename,
                "minio_file_path": minio_result.get("path"),
                "resume_metadata": file_metadata,
                # Profile status
                "is_profile_complete": False,  # Incomplete without LLM analysis
                "needs_review": True,  # Flag for manual processing
                "last_resume_upload": datetime.utcnow(),
                "profile_version": 2
            }
            
            success = HybridDataService.create_or_update_profile(user_email, basic_profile_data, db)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to save resume data")
            
            # Update Redis session data only (no redundant resume storage)
            session_update = {
                "profile_exists": True,
                "profile_complete": False,
                "needs_llm_analysis": True,
                "last_upload": datetime.utcnow().isoformat()
            }
            AuthService.update_user_data(user_email, session_update)
            
            return {
                "upload_success": True,
                "filename": file.filename,
                "minio_path": minio_result.get("path"),
                "profile_complete": False,
                "needs_llm_analysis": True,
                "message": "Resume uploaded successfully - requires profile analysis",
                "recommendation": "Please try again later when profile analysis is available"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))