"""
MinIO client utilities for file upload and management.
Ported from backup backend with Phase 2 improvements.
"""

import logging
import os
import uuid
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, Optional

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

# MinIO configuration from environment
MINIO_HOST = os.getenv("MINIO_HOST", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
BUCKET_NAME = "ai-interviewer-uploads"

class MinIOService:
    """MinIO client service for file operations."""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize MinIO client and ensure bucket exists."""
        try:
            self.client = Minio(
                MINIO_HOST,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False  # Use HTTP for internal docker communication
            )
            
            # Ensure bucket exists
            if not self.client.bucket_exists(BUCKET_NAME):
                self.client.make_bucket(BUCKET_NAME)
                logger.info(f"Created MinIO bucket: {BUCKET_NAME}")
            else:
                logger.info(f"MinIO bucket exists: {BUCKET_NAME}")
                
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if MinIO service is available."""
        return self.client is not None
    
    async def upload_file(
        self, 
        file_content: bytes, 
        filename: str, 
        user_email: str,
        content_type: str = "application/pdf"
    ) -> Dict[str, Any]:
        """
        Upload file to MinIO storage.
        
        Args:
            file_content: Binary file content
            filename: Original filename
            user_email: User email for path organization
            content_type: MIME type of the file
            
        Returns:
            Dict with upload results including MinIO path and URL
            
        Raises:
            Exception: If upload fails or MinIO not available
        """
        if not self.is_available():
            raise Exception("MinIO service not available")
        
        # Generate unique file path
        file_extension = filename.split('.')[-1].lower()
        unique_filename = f"resumes/{user_email}/{uuid.uuid4()}.{file_extension}"
        
        try:
            logger.info(f"Uploading file to MinIO: {unique_filename}")
            
            # Upload to MinIO
            self.client.put_object(
                BUCKET_NAME,
                unique_filename,
                BytesIO(file_content),
                length=len(file_content),
                content_type=content_type
            )
            
            logger.info(f"Successfully uploaded to MinIO: {unique_filename}")
            
            # Generate MinIO URL for agent access
            minio_url = f"http://{MINIO_HOST}/{BUCKET_NAME}/{unique_filename}"
            
            return {
                "success": True,
                "file_path": unique_filename,
                "minio_url": minio_url,
                "bucket": BUCKET_NAME,
                "size_bytes": len(file_content),
                "uploaded_at": datetime.now().isoformat(),
                "original_filename": filename
            }
            
        except S3Error as e:
            logger.error(f"MinIO S3 error during upload: {e}")
            raise Exception(f"File upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during MinIO upload: {e}")
            raise Exception(f"File upload failed: {str(e)}")
    
    async def get_file_url(self, file_path: str) -> str:
        """
        Get MinIO URL for a file path.
        
        Args:
            file_path: MinIO object path
            
        Returns:
            MinIO URL for agent access
        """
        return f"http://{MINIO_HOST}/{BUCKET_NAME}/{file_path}"
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from MinIO storage.
        
        Args:
            file_path: MinIO object path
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            self.client.remove_object(BUCKET_NAME, file_path)
            logger.info(f"Deleted file from MinIO: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from MinIO: {e}")
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in MinIO.
        
        Args:
            file_path: MinIO object path
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            self.client.stat_object(BUCKET_NAME, file_path)
            return True
        except Exception:
            return False


# Global MinIO service instance
minio_service = MinIOService()


async def upload_resume_to_minio(
    file_content: bytes, 
    filename: str, 
    user_email: str
) -> Dict[str, Any]:
    """
    Convenience function for resume uploads.
    
    Args:
        file_content: PDF file content
        filename: Original filename
        user_email: User email
        
    Returns:
        Upload result with MinIO path and URL
    """
    return await minio_service.upload_file(
        file_content=file_content,
        filename=filename,
        user_email=user_email,
        content_type="application/pdf"
    )