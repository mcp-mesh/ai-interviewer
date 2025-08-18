"""Settings and configuration management for the PDF extractor agent."""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class ProcessingLimits:
    """Limits for PDF processing operations."""
    max_file_size_mb: int = 50  # Maximum PDF file size in MB
    max_pages: int = 100        # Maximum number of pages to process
    timeout_seconds: int = 300  # Processing timeout (5 minutes)
    max_image_count: int = 20   # Maximum images to extract per PDF
    max_image_size_mb: int = 10 # Maximum size per extracted image


@dataclass
class SecurityConfig:
    """Security configuration for PDF processing."""
    allow_encrypted_pdfs: bool = False       # Allow processing encrypted PDFs
    sanitize_metadata: bool = True           # Remove potentially sensitive metadata
    validate_file_headers: bool = True       # Validate PDF file headers
    quarantine_suspicious: bool = True       # Quarantine suspicious files
    allowed_mime_types: List[str] = field(default_factory=lambda: [
        "application/pdf",
        "application/x-pdf"
    ])


@dataclass
class ExtractionConfig:
    """Configuration for extraction operations."""
    preserve_formatting: bool = True         # Maintain text formatting
    extract_images: bool = True             # Extract embedded images
    extract_tables: bool = True             # Extract tables (requires pdfplumber)
    extract_metadata: bool = True           # Extract PDF metadata
    image_format: str = "PNG"              # Format for extracted images
    table_format: str = "json"             # Format for extracted tables
    text_encoding: str = "utf-8"           # Text encoding


@dataclass
class CacheConfig:
    """Caching configuration."""
    enabled: bool = True                    # Enable result caching
    ttl_seconds: int = 3600                # Cache TTL (1 hour)
    max_entries: int = 1000                # Maximum cache entries
    cache_images: bool = False             # Cache extracted images (can be large)


@dataclass
class Settings:
    """Main configuration settings for the PDF extractor agent."""
    
    # Agent identification
    agent_name: str = "pdf-extractor"
    http_port: int = 9093
    version: str = "1.0.0"
    
    # Processing configuration
    processing: ProcessingLimits = field(default_factory=ProcessingLimits)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # External service dependencies
    dependencies: List[str] = field(default_factory=lambda: ["llm-service"])
    
    # Storage and temporary files
    temp_dir: str = "/tmp/pdf_extractor"
    output_dir: str = "/tmp/pdf_extractor/output"
    
    # Logging and monitoring
    log_level: str = "INFO"
    metrics_enabled: bool = True
    
    # MCP Mesh configuration
    mcp_mesh_enabled: bool = True
    mcp_mesh_registry_url: str = "http://registry:8000"
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        # Processing limits
        processing = ProcessingLimits(
            max_file_size_mb=int(os.getenv("PDF_MAX_FILE_SIZE_MB", "50")),
            max_pages=int(os.getenv("PDF_MAX_PAGES", "100")),
            timeout_seconds=int(os.getenv("PDF_TIMEOUT_SECONDS", "300")),
            max_image_count=int(os.getenv("PDF_MAX_IMAGE_COUNT", "20")),
            max_image_size_mb=int(os.getenv("PDF_MAX_IMAGE_SIZE_MB", "10"))
        )
        
        # Security config
        security = SecurityConfig(
            allow_encrypted_pdfs=os.getenv("PDF_ALLOW_ENCRYPTED", "false").lower() == "true",
            sanitize_metadata=os.getenv("PDF_SANITIZE_METADATA", "true").lower() == "true",
            validate_file_headers=os.getenv("PDF_VALIDATE_HEADERS", "true").lower() == "true",
            quarantine_suspicious=os.getenv("PDF_QUARANTINE_SUSPICIOUS", "true").lower() == "true"
        )
        
        # Extraction config
        extraction = ExtractionConfig(
            preserve_formatting=os.getenv("PDF_PRESERVE_FORMATTING", "true").lower() == "true",
            extract_images=os.getenv("PDF_EXTRACT_IMAGES", "true").lower() == "true",
            extract_tables=os.getenv("PDF_EXTRACT_TABLES", "true").lower() == "true",
            extract_metadata=os.getenv("PDF_EXTRACT_METADATA", "true").lower() == "true",
            image_format=os.getenv("PDF_IMAGE_FORMAT", "PNG"),
            table_format=os.getenv("PDF_TABLE_FORMAT", "json")
        )
        
        # Cache config
        cache = CacheConfig(
            enabled=os.getenv("PDF_CACHE_ENABLED", "true").lower() == "true",
            ttl_seconds=int(os.getenv("PDF_CACHE_TTL_SECONDS", "3600")),
            max_entries=int(os.getenv("PDF_CACHE_MAX_ENTRIES", "1000")),
            cache_images=os.getenv("PDF_CACHE_IMAGES", "false").lower() == "true"
        )
        
        return cls(
            agent_name=os.getenv("AGENT_NAME", "pdf-extractor"),
            http_port=int(os.getenv("HTTP_PORT", "9093")),
            processing=processing,
            security=security,
            extraction=extraction,
            cache=cache,
            temp_dir=os.getenv("PDF_TEMP_DIR", "/tmp/pdf_extractor"),
            output_dir=os.getenv("PDF_OUTPUT_DIR", "/tmp/pdf_extractor/output"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            metrics_enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true",
            mcp_mesh_enabled=os.getenv("MCP_MESH_ENABLED", "true").lower() == "true",
            mcp_mesh_registry_url=os.getenv("MCP_MESH_REGISTRY_URL", "http://registry:8000")
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def configure_settings(settings: Settings) -> None:
    """Configure the global settings instance."""
    global _settings
    _settings = settings