"""
File upload and processing service.
"""

import json
import logging
import uuid
from datetime import datetime
from io import BytesIO
from typing import Optional, Dict, Any

from minio import Minio
from minio.error import S3Error
from app.config import MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, BUCKET_NAME
# Removed MCP client import - now using MCP Mesh dependency injection

logger = logging.getLogger(__name__)

class FileService:
    """Handles file uploads and processing."""
    
    def __init__(self):
        self.minio_client = None
        self._init_minio()
    
    def _init_minio(self):
        """Initialize MinIO client."""
        try:
            self.minio_client = Minio(
                MINIO_HOST,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False  # Use HTTP for internal communication
            )
            
            # Ensure bucket exists
            if not self.minio_client.bucket_exists(BUCKET_NAME):
                self.minio_client.make_bucket(BUCKET_NAME)
                logger.info(f"Created MinIO bucket: {BUCKET_NAME}")
        except Exception as e:
            logger.warning(f"MinIO not available, file uploads will be disabled: {e}")
            self.minio_client = None
    
    async def upload_to_minio(self, file_content: bytes, filename: str, user_email: str) -> Dict[str, Any]:
        """Upload file to MinIO only (no processing)."""
        if not self.minio_client:
            raise Exception("File upload service not available")
        
        # Generate unique file key for MinIO
        file_extension = filename.split('.')[-1].lower()
        unique_filename = f"resumes/{user_email}/{uuid.uuid4()}.{file_extension}"
        
        try:
            # Upload to MinIO
            logger.info(f"Uploading to MinIO: {unique_filename}")
            self.minio_client.put_object(
                BUCKET_NAME,
                unique_filename,
                BytesIO(file_content),
                length=len(file_content),
                content_type="application/pdf"
            )
            logger.info(f"Successfully uploaded to MinIO: {unique_filename}")
            
            return {
                "path": unique_filename,
                "minio_url": f"http://{MINIO_HOST}/{BUCKET_NAME}/{unique_filename}",
                "uploaded_at": datetime.now().isoformat(),
                "size_bytes": len(file_content)
            }
            
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise Exception("File upload failed")
        except Exception as e:
            logger.error(f"MinIO upload error: {e}")
            raise Exception("File upload failed")

    async def upload_and_process_resume(self, file_content: bytes, filename: str, user_email: str) -> Dict[str, Any]:
        """Upload resume to MinIO and process it via PDF extractor."""
        if not self.minio_client:
            raise Exception("File upload service not available")
        
        # Generate unique file key for MinIO
        file_extension = filename.split('.')[-1].lower()
        unique_filename = f"resumes/{user_email}/{uuid.uuid4()}.{file_extension}"
        
        try:
            # Upload to MinIO
            logger.info(f"Uploading to MinIO: {unique_filename}")
            self.minio_client.put_object(
                BUCKET_NAME,
                unique_filename,
                BytesIO(file_content),
                length=len(file_content),
                content_type="application/pdf"
            )
            logger.info(f"Successfully uploaded to MinIO: {unique_filename}")
            
            # Call PDF extractor service via MCP using MinIO URL
            minio_url = f"http://{MINIO_HOST}/{BUCKET_NAME}/{unique_filename}"
            logger.info(f"Calling PDF extractor service with MinIO URL: {minio_url}")
            extraction_result = await self.mcp_client.call_pdf_extractor(minio_url, file_content)
            logger.info(f"PDF extraction result keys: {extraction_result.keys() if extraction_result else 'None'}")
            
            if extraction_result:
                logger.info(f"Has structured_analysis: {'structured_analysis' in extraction_result}")
                logger.info(f"Has analysis_enhanced: {'analysis_enhanced' in extraction_result}")
            
            if not extraction_result:
                # For now, create a basic extraction result as fallback
                logger.warning("PDF extraction failed, creating fallback result")
                extraction_result = {
                    "text": "PDF content extraction failed - using fallback",
                    "structured_data": {
                        "filename": filename,
                        "pages": 1,
                        "status": "extraction_failed"
                    },
                    "metadata": {
                        "processing_time": 0,
                        "method": "fallback"
                    }
                }
            
            # Create resume data structure
            resume_data = {
                "resume": {
                    "filename": filename,
                    "minio_path": unique_filename,
                    "size_bytes": len(file_content),
                    "uploaded_at": datetime.now().isoformat(),
                    "extracted_text": extraction_result.get("text_content", ""),
                    "structured_data": extraction_result.get("sections", {}),
                    "structured_analysis": extraction_result.get("structured_analysis", {}),
                    "analysis_enhanced": extraction_result.get("analysis_enhanced", False),
                    "extraction_metadata": {
                        "success": extraction_result.get("success", False),
                        "extraction_method": extraction_result.get("extraction_method", "unknown"),
                        "text_stats": extraction_result.get("text_stats", {}),
                        "summary": extraction_result.get("summary", "")
                    }
                }
            }
            
            return {
                "upload_success": True,
                "filename": filename,
                "minio_path": unique_filename,
                "extraction_result": extraction_result,
                "resume_data": resume_data
            }
            
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise Exception("File upload failed")
        except Exception as e:
            logger.error(f"Resume upload error: {e}")
            raise Exception("Resume processing failed")