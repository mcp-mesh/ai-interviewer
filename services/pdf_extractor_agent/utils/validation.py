"""PDF validation utilities for security and integrity checks."""

import os
import magic
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


class ValidationError(Exception):
    """Exception raised when PDF validation fails."""
    pass


@dataclass
class ValidationIssue:
    """Represents a validation issue found during PDF analysis."""
    severity: str  # "error", "warning", "info"
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None


@dataclass 
class ValidationResult:
    """Result of PDF validation process."""
    is_valid: bool
    file_path: str
    file_size: int
    issues: List[ValidationIssue]
    metadata: Dict[str, Any]
    
    def has_errors(self) -> bool:
        """Check if validation found any errors."""
        return any(issue.severity == "error" for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """Check if validation found any warnings."""
        return any(issue.severity == "warning" for issue in self.issues)


class PDFValidator:
    """Validates PDF files for security and processing compatibility."""
    
    def __init__(self, max_file_size_mb: int = 50, allowed_mime_types: List[str] = None):
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.allowed_mime_types = allowed_mime_types or [
            "application/pdf", 
            "application/x-pdf"
        ]
        
    def validate_file(self, file_path: str) -> ValidationResult:
        """
        Comprehensive PDF file validation.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            ValidationResult with validation status and any issues found
        """
        file_path = Path(file_path)
        issues = []
        metadata = {}
        
        # Check if file exists
        if not file_path.exists():
            issues.append(ValidationIssue(
                severity="error",
                message=f"File not found: {file_path}",
                code="FILE_NOT_FOUND"
            ))
            return ValidationResult(
                is_valid=False,
                file_path=str(file_path),
                file_size=0,
                issues=issues,
                metadata=metadata
            )
        
        # Get file size
        try:
            file_size = file_path.stat().st_size
            metadata["file_size_bytes"] = file_size
            metadata["file_size_mb"] = round(file_size / (1024 * 1024), 2)
        except OSError as e:
            issues.append(ValidationIssue(
                severity="error",
                message=f"Cannot access file: {e}",
                code="FILE_ACCESS_ERROR"
            ))
            file_size = 0
        
        # Validate file size
        if file_size > self.max_file_size_bytes:
            issues.append(ValidationIssue(
                severity="error",
                message=f"File too large: {metadata.get('file_size_mb', 0):.2f}MB exceeds limit of {self.max_file_size_mb}MB",
                code="FILE_TOO_LARGE",
                details={"max_size_mb": self.max_file_size_mb}
            ))
        
        # Validate MIME type
        try:
            mime_type = magic.from_file(str(file_path), mime=True)
            metadata["mime_type"] = mime_type
            
            if mime_type not in self.allowed_mime_types:
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Invalid file type: {mime_type}. Expected PDF.",
                    code="INVALID_MIME_TYPE",
                    details={"detected_type": mime_type, "allowed_types": self.allowed_mime_types}
                ))
        except Exception as e:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"Could not detect file type: {e}",
                code="MIME_DETECTION_FAILED"
            ))
        
        # Validate file header (PDF signature)
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    issues.append(ValidationIssue(
                        severity="error",
                        message="Invalid PDF header - file may be corrupted",
                        code="INVALID_PDF_HEADER"
                    ))
                else:
                    # Extract PDF version
                    try:
                        version_part = header[5:8].decode('ascii')
                        metadata["pdf_version"] = version_part
                    except:
                        pass
        except Exception as e:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"Could not read file header: {e}",
                code="HEADER_READ_FAILED"
            ))
        
        # Check for empty file
        if file_size == 0:
            issues.append(ValidationIssue(
                severity="error", 
                message="File is empty",
                code="EMPTY_FILE"
            ))
        elif file_size < 100:  # Very small files are suspicious
            issues.append(ValidationIssue(
                severity="warning",
                message=f"File is very small ({file_size} bytes) - may not be a valid PDF",
                code="SUSPICIOUS_SIZE"
            ))
        
        # Basic security checks
        self._perform_security_checks(file_path, issues, metadata)
        
        # Determine if validation passed
        is_valid = not any(issue.severity == "error" for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            file_path=str(file_path),
            file_size=file_size,
            issues=issues,
            metadata=metadata
        )
    
    def _perform_security_checks(
        self, 
        file_path: Path, 
        issues: List[ValidationIssue], 
        metadata: Dict[str, Any]
    ) -> None:
        """Perform basic security checks on the PDF file."""
        
        # Check for suspicious file extensions in path
        suspicious_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
        path_str = str(file_path).lower()
        
        for ext in suspicious_extensions:
            if ext in path_str:
                issues.append(ValidationIssue(
                    severity="warning",
                    message=f"Suspicious file path contains '{ext}'",
                    code="SUSPICIOUS_PATH"
                ))
        
        # Check for excessively long filenames (potential buffer overflow)
        if len(file_path.name) > 255:
            issues.append(ValidationIssue(
                severity="warning",
                message="Filename is excessively long",
                code="LONG_FILENAME"
            ))
        
        # Basic PDF structure validation
        try:
            with open(file_path, 'rb') as f:
                content = f.read(min(1024, file_path.stat().st_size))
                
                # Check for PDF trailer
                if b'trailer' not in content and file_path.stat().st_size > 1024:
                    # Need to check the end of the file for trailer
                    f.seek(-min(1024, file_path.stat().st_size), 2)
                    tail_content = f.read()
                    if b'trailer' not in tail_content:
                        issues.append(ValidationIssue(
                            severity="warning",
                            message="PDF trailer not found - file may be incomplete",
                            code="MISSING_TRAILER"
                        ))
                
                # Check for xref table
                if b'xref' not in content and b'xref' not in tail_content:
                    issues.append(ValidationIssue(
                        severity="warning", 
                        message="PDF cross-reference table not found",
                        code="MISSING_XREF"
                    ))
                    
        except Exception as e:
            issues.append(ValidationIssue(
                severity="info",
                message=f"Could not perform structural validation: {e}",
                code="STRUCTURE_CHECK_FAILED"
            ))
    
    def validate_content_safety(self, file_path: str) -> ValidationResult:
        """
        Additional safety validation for PDF content.
        This could be extended to check for malicious JavaScript, forms, etc.
        """
        # For now, this is a placeholder for future enhanced security checks
        issues = []
        metadata = {"content_safety_check": "basic"}
        
        # This would be extended with more sophisticated checks:
        # - JavaScript detection
        # - Form field analysis  
        # - External reference detection
        # - Embedded file detection
        
        return ValidationResult(
            is_valid=True,  # Basic implementation always passes
            file_path=file_path,
            file_size=Path(file_path).stat().st_size if Path(file_path).exists() else 0,
            issues=issues,
            metadata=metadata
        )