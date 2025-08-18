"""PDF text extraction tools using PyMuPDF and pdfplumber."""

import fitz  # PyMuPDF
import pdfplumber
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging

try:
    from ..config.settings import get_settings
    from ..utils.formatting import TextFormatter
except ImportError:
    from config.settings import get_settings
    from utils.formatting import TextFormatter


logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """Handles text extraction from PDF files using multiple methods."""
    
    def __init__(self):
        self.settings = get_settings()
        self.formatter = TextFormatter()
        
        # Configure extraction preferences
        self.max_pages = self.settings.processing.max_pages
        self.preserve_formatting = self.settings.extraction.preserve_formatting
        
    def extract_text(self, file_path: str, method: str = "auto") -> Dict[str, Any]:
        """
        Extract text from PDF using specified method.
        
        Args:
            file_path: Path to PDF file
            method: Extraction method ("pymupdf", "pdfplumber", "auto")
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        logger.info(f"Extracting text from {file_path} using method: {method}")
        
        try:
            if method == "pymupdf":
                return self._extract_with_pymupdf(file_path)
            elif method == "pdfplumber":
                return self._extract_with_pdfplumber(file_path)
            elif method == "auto":
                # Try PyMuPDF first (faster), fallback to pdfplumber
                try:
                    result = self._extract_with_pymupdf(file_path)
                    # Check if extraction was successful
                    if result.get('text_content') and len(result['text_content'].strip()) > 0:
                        result['extraction_method'] = 'pymupdf'
                        return result
                    else:
                        logger.info("PyMuPDF extracted empty text, trying pdfplumber")
                        result = self._extract_with_pdfplumber(file_path)
                        result['extraction_method'] = 'pdfplumber'
                        return result
                except Exception as e:
                    logger.warning(f"PyMuPDF extraction failed: {e}, trying pdfplumber")
                    result = self._extract_with_pdfplumber(file_path)
                    result['extraction_method'] = 'pdfplumber'
                    return result
            else:
                raise ValueError(f"Unknown extraction method: {method}")
                
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            raise
    
    def _extract_with_pymupdf(self, file_path: Path) -> Dict[str, Any]:
        """Extract text using PyMuPDF (fast method)."""
        
        # Open PDF document
        doc = fitz.open(str(file_path))
        
        try:
            page_count = len(doc)
            pages_to_process = min(page_count, self.max_pages)
            
            text_content = []
            page_texts = []
            
            for page_num in range(pages_to_process):
                page = doc.load_page(page_num)
                
                # Extract text with formatting preservation
                if self.preserve_formatting:
                    # Use text extraction with layout preservation
                    text = page.get_text("text")
                else:
                    # Use simple text extraction
                    text = page.get_text()
                
                if text.strip():
                    page_texts.append({
                        'page': page_num + 1,
                        'text': text,
                        'char_count': len(text),
                        'word_count': len(text.split())
                    })
                    text_content.append(text)
            
            # Combine all text
            full_text = '\n\n'.join(text_content)
            
            # Clean and format text
            clean_text = self.formatter.clean_text(full_text, self.preserve_formatting)
            
            # Extract sections
            sections = self.formatter.extract_sections(clean_text)
            
            # Calculate statistics
            text_stats = {
                'char_count': len(clean_text),
                'word_count': len(clean_text.split()),
                'line_count': len(clean_text.split('\n')),
                'pages_processed': pages_to_process,
                'total_pages': page_count
            }
            
            return {
                'text_content': clean_text,
                'page_texts': page_texts,
                'sections': sections,
                'text_stats': text_stats,
                'extraction_method': 'pymupdf',
                'success': True
            }
            
        finally:
            doc.close()
    
    def _extract_with_pdfplumber(self, file_path: Path) -> Dict[str, Any]:
        """Extract text using pdfplumber (better for complex layouts)."""
        
        with pdfplumber.open(str(file_path)) as pdf:
            page_count = len(pdf.pages)
            pages_to_process = min(page_count, self.max_pages)
            
            text_content = []
            page_texts = []
            
            for page_num in range(pages_to_process):
                page = pdf.pages[page_num]
                
                # Extract text with pdfplumber's layout handling
                text = page.extract_text(
                    x_tolerance=3,
                    y_tolerance=3,
                    layout=self.preserve_formatting,
                    x_density=7.25,
                    y_density=13
                )
                
                if text and text.strip():
                    page_texts.append({
                        'page': page_num + 1,
                        'text': text,
                        'char_count': len(text),
                        'word_count': len(text.split())
                    })
                    text_content.append(text)
            
            # Combine all text
            full_text = '\n\n'.join(text_content)
            
            # Clean and format text
            clean_text = self.formatter.clean_text(full_text, self.preserve_formatting)
            
            # Extract sections
            sections = self.formatter.extract_sections(clean_text)
            
            # Calculate statistics
            text_stats = {
                'char_count': len(clean_text),
                'word_count': len(clean_text.split()),
                'line_count': len(clean_text.split('\n')),
                'pages_processed': pages_to_process,
                'total_pages': page_count
            }
            
            return {
                'text_content': clean_text,
                'page_texts': page_texts,
                'sections': sections,
                'text_stats': text_stats,
                'extraction_method': 'pdfplumber',
                'success': True
            }
    
    def extract_text_with_coordinates(self, file_path: str, page_num: int = 0) -> Dict[str, Any]:
        """
        Extract text with position coordinates for advanced processing.
        
        Args:
            file_path: Path to PDF file
            page_num: Page number to extract (0-based)
            
        Returns:
            Dictionary containing text blocks with coordinates
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Use PyMuPDF for coordinate extraction
        doc = fitz.open(str(file_path))
        
        try:
            if page_num >= len(doc):
                raise ValueError(f"Page {page_num + 1} does not exist (PDF has {len(doc)} pages)")
            
            page = doc.load_page(page_num)
            
            # Get text with coordinates
            blocks = page.get_text("dict")
            
            text_blocks = []
            for block in blocks.get("blocks", []):
                if "lines" in block:  # Text block
                    block_text = ""
                    spans = []
                    
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if text:
                                block_text += text + " "
                                spans.append({
                                    'text': text,
                                    'bbox': span.get("bbox"),
                                    'font': span.get("font"),
                                    'size': span.get("size"),
                                    'color': span.get("color")
                                })
                    
                    if block_text.strip():
                        text_blocks.append({
                            'text': block_text.strip(),
                            'bbox': block.get("bbox"),
                            'type': 'text',
                            'spans': spans
                        })
            
            return {
                'page': page_num + 1,
                'text_blocks': text_blocks,
                'page_size': {
                    'width': page.rect.width,
                    'height': page.rect.height
                },
                'success': True
            }
            
        finally:
            doc.close()
    
    def get_document_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic document information without full text extraction.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with document information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        doc = fitz.open(str(file_path))
        
        try:
            info = {
                'page_count': len(doc),
                'file_size': file_path.stat().st_size,
                'can_extract_text': True,  # Assume true, will be updated
                'is_encrypted': doc.needs_pass,
                'has_text': False
            }
            
            # Check if document has extractable text (test first page)
            if len(doc) > 0:
                first_page = doc.load_page(0)
                sample_text = first_page.get_text()
                info['has_text'] = bool(sample_text.strip())
            
            return info
            
        finally:
            doc.close()
    
    def extract_page_text(self, file_path: str, page_num: int) -> Dict[str, Any]:
        """
        Extract text from a specific page.
        
        Args:
            file_path: Path to PDF file
            page_num: Page number (1-based)
            
        Returns:
            Dictionary with page text and metadata
        """
        file_path = Path(file_path)
        page_index = page_num - 1  # Convert to 0-based
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        doc = fitz.open(str(file_path))
        
        try:
            if page_index >= len(doc) or page_index < 0:
                raise ValueError(f"Page {page_num} does not exist (PDF has {len(doc)} pages)")
            
            page = doc.load_page(page_index)
            text = page.get_text()
            
            # Clean text
            clean_text = self.formatter.clean_text(text, self.preserve_formatting)
            
            return {
                'page': page_num,
                'text_content': clean_text,
                'char_count': len(clean_text),
                'word_count': len(clean_text.split()),
                'line_count': len(clean_text.split('\n')),
                'success': True
            }
            
        finally:
            doc.close()