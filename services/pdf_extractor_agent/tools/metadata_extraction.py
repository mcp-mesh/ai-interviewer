"""PDF metadata extraction tools."""

import fitz  # PyMuPDF
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

try:
    from ..config.settings import get_settings
except ImportError:
    from config.settings import get_settings


logger = logging.getLogger(__name__)


class PDFMetadataExtractor:
    """Handles extraction of PDF metadata and document properties."""
    
    def __init__(self):
        self.settings = get_settings()
        self.sanitize_metadata = self.settings.security.sanitize_metadata
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary containing PDF metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        logger.info(f"Extracting metadata from {file_path}")
        
        doc = fitz.open(str(file_path))
        
        try:
            # Get document metadata
            raw_metadata = doc.metadata
            
            # Get document information
            page_count = len(doc)
            
            # Extract basic file information
            file_stats = file_path.stat()
            
            metadata = {
                # File information
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': file_stats.st_size,
                'file_size_mb': round(file_stats.st_size / (1024 * 1024), 2),
                'file_created': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                'file_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                
                # Document properties
                'page_count': page_count,
                'is_encrypted': doc.needs_pass,
                'pdf_version': doc.pdf_version(),
                'permissions': self._extract_permissions(doc),
                
                # Document metadata
                'title': raw_metadata.get('title', ''),
                'author': raw_metadata.get('author', ''),
                'subject': raw_metadata.get('subject', ''),
                'keywords': raw_metadata.get('keywords', ''),
                'creator': raw_metadata.get('creator', ''),
                'producer': raw_metadata.get('producer', ''),
                'creation_date': self._parse_pdf_date(raw_metadata.get('creationDate', '')),
                'modification_date': self._parse_pdf_date(raw_metadata.get('modDate', '')),
                
                # Technical information
                'has_text': self._check_has_text(doc),
                'has_images': self._check_has_images(doc),
                'has_forms': self._check_has_forms(doc),
                'has_annotations': self._check_has_annotations(doc),
                
                # Additional properties
                'language': raw_metadata.get('language', ''),
                'format': raw_metadata.get('format', ''),
                'trapped': raw_metadata.get('trapped', ''),
                
                # Extraction metadata
                'extraction_timestamp': datetime.now().isoformat(),
                'extraction_success': True
            }
            
            # Sanitize metadata if configured
            if self.sanitize_metadata:
                metadata = self._sanitize_metadata(metadata)
            
            # Add page-specific metadata
            metadata['pages'] = self._extract_page_metadata(doc)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed for {file_path}: {e}")
            return {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'extraction_error': str(e),
                'extraction_success': False,
                'extraction_timestamp': datetime.now().isoformat()
            }
        
        finally:
            doc.close()
    
    def _parse_pdf_date(self, date_string: str) -> Optional[str]:
        """
        Parse PDF date format to ISO format.
        
        PDF dates are in format: D:YYYYMMDDHHmmSSOHH'mm'
        """
        if not date_string or not date_string.startswith('D:'):
            return date_string if date_string else None
        
        try:
            # Remove 'D:' prefix
            date_part = date_string[2:]
            
            # Extract date components
            if len(date_part) >= 14:
                year = date_part[:4]
                month = date_part[4:6]
                day = date_part[6:8]
                hour = date_part[8:10]
                minute = date_part[10:12]
                second = date_part[12:14]
                
                # Create ISO format date
                iso_date = f"{year}-{month}-{day}T{hour}:{minute}:{second}"
                
                # Handle timezone offset if present
                if len(date_part) > 14:
                    tz_part = date_part[14:]
                    if tz_part.startswith(('+', '-')):
                        # Simple timezone handling
                        if len(tz_part) >= 3:
                            iso_date += tz_part[:3] + ':00'
                
                return iso_date
            
            # If we can't parse fully, return the cleaned version
            return date_part
            
        except Exception:
            # Return original if parsing fails
            return date_string
    
    def _extract_permissions(self, doc) -> Dict[str, bool]:
        """Extract PDF permissions information."""
        try:
            # Get permissions flags
            perms = {
                'can_print': not doc.is_encrypted or doc.permissions & fitz.PDF_PERM_PRINT != 0,
                'can_copy': not doc.is_encrypted or doc.permissions & fitz.PDF_PERM_COPY != 0,
                'can_modify': not doc.is_encrypted or doc.permissions & fitz.PDF_PERM_MODIFY != 0,
                'can_annotate': not doc.is_encrypted or doc.permissions & fitz.PDF_PERM_ANNOTATE != 0,
                'can_form_fill': not doc.is_encrypted or doc.permissions & fitz.PDF_PERM_FORM != 0,
                'can_extract': not doc.is_encrypted or doc.permissions & fitz.PDF_PERM_ACCESSIBILITY != 0,
                'can_assemble': not doc.is_encrypted or doc.permissions & fitz.PDF_PERM_ASSEMBLE != 0,
                'can_print_high_quality': not doc.is_encrypted or doc.permissions & fitz.PDF_PERM_PRINT_HQ != 0
            }
            return perms
        except Exception:
            return {}
    
    def _check_has_text(self, doc) -> bool:
        """Check if document contains extractable text."""
        try:
            # Sample first few pages
            pages_to_check = min(3, len(doc))
            for i in range(pages_to_check):
                page = doc.load_page(i)
                text = page.get_text()
                if text.strip():
                    return True
            return False
        except Exception:
            return False
    
    def _check_has_images(self, doc) -> bool:
        """Check if document contains images."""
        try:
            # Sample first few pages
            pages_to_check = min(3, len(doc))
            for i in range(pages_to_check):
                page = doc.load_page(i)
                image_list = page.get_images()
                if image_list:
                    return True
            return False
        except Exception:
            return False
    
    def _check_has_forms(self, doc) -> bool:
        """Check if document contains form fields."""
        try:
            # Check for form fields
            form_fields = doc.form_n()
            return form_fields > 0
        except Exception:
            return False
    
    def _check_has_annotations(self, doc) -> bool:
        """Check if document contains annotations."""
        try:
            # Sample first few pages for annotations
            pages_to_check = min(3, len(doc))
            for i in range(pages_to_check):
                page = doc.load_page(i)
                annotations = page.annots()
                if annotations:
                    return True
            return False
        except Exception:
            return False
    
    def _extract_page_metadata(self, doc) -> list:
        """Extract metadata for individual pages."""
        pages = []
        
        try:
            for i in range(min(len(doc), 10)):  # Limit to first 10 pages for performance
                page = doc.load_page(i)
                
                page_info = {
                    'page_number': i + 1,
                    'width': page.rect.width,
                    'height': page.rect.height,
                    'rotation': page.rotation,
                    'has_text': bool(page.get_text().strip()),
                    'has_images': bool(page.get_images()),
                    'has_links': bool(page.get_links()),
                }
                
                # Get text statistics for the page
                text = page.get_text()
                if text.strip():
                    page_info.update({
                        'char_count': len(text),
                        'word_count': len(text.split()),
                        'line_count': len(text.split('\n'))
                    })
                
                pages.append(page_info)
            
        except Exception as e:
            logger.warning(f"Failed to extract page metadata: {e}")
        
        return pages
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize metadata by removing potentially sensitive information.
        
        Args:
            metadata: Raw metadata dictionary
            
        Returns:
            Sanitized metadata dictionary
        """
        sensitive_fields = [
            'file_path',  # May contain sensitive path information
            'author',     # May contain personal information
            'creator',    # May contain software/system information
            'producer'    # May contain software/system information
        ]
        
        sanitized = metadata.copy()
        
        for field in sensitive_fields:
            if field in sanitized and sanitized[field]:
                if field == 'file_path':
                    # Keep only the filename
                    sanitized[field] = Path(sanitized[field]).name
                else:
                    # Replace with generic value
                    sanitized[field] = f"[REDACTED_{field.upper()}]"
        
        return sanitized
    
    def get_basic_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic PDF information without detailed metadata extraction.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with basic PDF information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        doc = fitz.open(str(file_path))
        
        try:
            file_stats = file_path.stat()
            
            return {
                'file_name': file_path.name,
                'file_size': file_stats.st_size,
                'file_size_mb': round(file_stats.st_size / (1024 * 1024), 2),
                'page_count': len(doc),
                'is_encrypted': doc.needs_pass,
                'pdf_version': doc.pdf_version(),
                'has_text': self._check_has_text(doc),
                'can_process': not doc.needs_pass,  # Simple check for processing capability
                'extraction_timestamp': datetime.now().isoformat()
            }
            
        finally:
            doc.close()