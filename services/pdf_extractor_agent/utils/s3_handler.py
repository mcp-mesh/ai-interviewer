"""S3-compatible storage handler for PDF file downloads."""

import os
import tempfile
import logging
from typing import Optional, Dict, Any, Union
from urllib.parse import urlparse
import requests
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


logger = logging.getLogger(__name__)


class S3Handler:
    """Handler for S3-compatible storage operations."""
    
    def __init__(self):
        # S3 configuration from environment
        self.endpoint = os.getenv("S3_ENDPOINT", "http://localhost:9000")
        self.access_key = os.getenv("S3_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("S3_SECRET_KEY", "minioadmin123")
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "ai-interviewer-uploads")
        self.region = os.getenv("S3_REGION", "us-east-1")
        
        # Initialize S3 client
        self.s3_client = None
        self._init_s3_client()
        
    def _init_s3_client(self):
        """Initialize S3 client with configuration."""
        try:
            from botocore.config import Config
            import threading
            
            # Create a thread-safe S3 client
            config = Config(
                s3={'addressing_style': 'path'},
                max_pool_connections=10,
                retries={'max_attempts': 3}
            )
            
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=config
            )
            logger.info(f"S3 client initialized for endpoint: {self.endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def download_file_from_url(self, file_url: str, temp_dir: str) -> Optional[str]:
        """
        Download file from URL to temporary location.
        
        Supports both S3 URLs and regular HTTP URLs.
        
        Args:
            file_url: S3 URL or HTTP URL to the file
            temp_dir: Directory to store temporary files
            
        Returns:
            Local file path if successful, None otherwise
        """
        try:
            # Parse the URL to determine if it's S3 or HTTP
            parsed_url = urlparse(file_url)
            
            # Always use HTTP download for MinIO and other HTTP-based S3-compatible services
            # This avoids boto3 threading issues
            if parsed_url.scheme in ['http', 'https']:
                return self._download_from_http_url(file_url, temp_dir)
            elif self._is_s3_url(file_url):
                return self._download_from_s3_url(file_url, temp_dir)
            else:
                logger.error(f"Unsupported URL scheme: {parsed_url.scheme}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to download file from {file_url}: {e}")
            return None
    
    def _is_s3_url(self, url: str) -> bool:
        """Check if URL is an S3-compatible URL."""
        parsed = urlparse(url)
        
        # Check for true S3-style URLs (s3://)
        if parsed.scheme == 's3':
            return True
            
        # Check for AWS S3 URLs  
        if parsed.netloc and 's3.amazonaws.com' in parsed.netloc.lower():
            return True
            
        # For MinIO and other S3-compatible services, treat as HTTP to avoid boto3 threading issues
        # This will be handled by _download_from_http_url instead
        return False
    
    def _download_from_s3_url(self, s3_url: str, temp_dir: str) -> Optional[str]:
        """Download file from S3-compatible storage."""
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return None
            
        try:
            # Parse S3 URL to extract bucket and key
            bucket_name, object_key = self._parse_s3_url(s3_url)
            if not bucket_name or not object_key:
                logger.error(f"Invalid S3 URL format: {s3_url}")
                return None
            
            # Generate temporary file path
            filename = os.path.basename(object_key)
            if not filename:
                filename = "downloaded_file.pdf"
            temp_file_path = os.path.join(temp_dir, filename)
            
            # Download from S3
            logger.info(f"Downloading from S3: s3://{bucket_name}/{object_key}")
            self.s3_client.download_file(bucket_name, object_key, temp_file_path)
            
            logger.info(f"Successfully downloaded file to: {temp_file_path}")
            return temp_file_path
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 download failed with error {error_code}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading from S3: {e}")
            return None
    
    def _download_from_http_url(self, http_url: str, temp_dir: str) -> Optional[str]:
        """Download file from HTTP/HTTPS URL."""
        try:
            # Generate temporary file path
            parsed_url = urlparse(http_url)
            filename = os.path.basename(parsed_url.path)
            if not filename or '.' not in filename:
                filename = "downloaded_file.pdf"
            temp_file_path = os.path.join(temp_dir, filename)
            
            # Download via HTTP
            logger.info(f"Downloading from HTTP: {http_url}")
            response = requests.get(http_url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Write to temporary file
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded file to: {temp_file_path}")
            return temp_file_path
            
        except requests.RequestException as e:
            logger.error(f"HTTP download failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading from HTTP: {e}")
            return None
    
    def _parse_s3_url(self, s3_url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse S3 URL to extract bucket name and object key.
        
        Supports formats:
        - s3://bucket-name/path/to/file.pdf
        - http://minio:9000/bucket-name/path/to/file.pdf
        - https://s3.amazonaws.com/bucket-name/path/to/file.pdf
        """
        parsed = urlparse(s3_url)
        
        if parsed.scheme == 's3':
            # Standard S3 URL: s3://bucket/key
            bucket_name = parsed.netloc
            object_key = parsed.path.lstrip('/')
            return bucket_name, object_key
        
        elif parsed.scheme in ['http', 'https']:
            # HTTP-style S3 URL: http://endpoint/bucket/key
            path_parts = parsed.path.strip('/').split('/', 1)
            if len(path_parts) >= 2:
                bucket_name = path_parts[0]
                object_key = path_parts[1]
                return bucket_name, object_key
            elif len(path_parts) == 1:
                # Just bucket name, no key
                return path_parts[0], None
                
        return None, None
    
    def get_file_metadata(self, file_url: str) -> Dict[str, Any]:
        """
        Get metadata for a file from S3-compatible storage.
        
        Args:
            file_url: S3 URL to the file
            
        Returns:
            Dictionary containing file metadata
        """
        if not self._is_s3_url(file_url) or not self.s3_client:
            return {}
            
        try:
            bucket_name, object_key = self._parse_s3_url(file_url)
            if not bucket_name or not object_key:
                return {}
            
            # Get object metadata
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            
            return {
                'content_length': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', ''),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.warning(f"Could not get metadata for {file_url}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting metadata: {e}")
            return {}
    
    def cleanup_temp_file(self, file_path: str) -> bool:
        """
        Clean up temporary downloaded file.
        
        Args:
            file_path: Path to temporary file
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {file_path}: {e}")
            return False


def is_url(path: str) -> bool:
    """Check if a given path is a URL."""
    try:
        parsed = urlparse(path)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False