"""
Configuration management for AI Interviewer Backend.
Centralizes all environment variables and application settings.
"""

import os
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if running in dev mode
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

# API configuration  
API_PORT = int(os.getenv("API_PORT", "8080"))

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Timer monitoring constants
SESSION_PREFIX = "interview_session:"
INTERVIEW_TIMEOUT_SECONDS = 300  # 5 minutes
LOCK_PREFIX = "interview_expire_lock:"
LOCK_TTL = 300  # 5 minutes lock expiry

# MinIO S3 client configuration
MINIO_HOST = os.getenv("MINIO_HOST", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
BUCKET_NAME = "ai-interviewer-uploads"

# Environment variables for MCP services
PDF_EXTRACTOR_URL = os.getenv("PDF_EXTRACTOR_URL", "http://pdf-extractor:8090")
INTERVIEW_AGENT_URL = os.getenv("INTERVIEW_AGENT_URL", "http://interview-agent:8090")

# Admin user configuration
ADMIN_EMAIL = "dhyan.raj@gmail.com"