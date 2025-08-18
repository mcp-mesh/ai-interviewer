"""Text and output formatting utilities for PDF extraction results."""

import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_extraction_summary(extraction_data: Dict[str, Any]) -> str:
    """Format extraction results into a human-readable summary."""
    lines = []
    
    # Basic info
    if 'metadata' in extraction_data:
        meta = extraction_data['metadata']
        lines.append("=== PDF EXTRACTION SUMMARY ===")
        lines.append(f"File: {meta.get('file_name', 'Unknown')}")
        lines.append(f"Size: {format_file_size(meta.get('file_size', 0))}")
        lines.append(f"Pages: {meta.get('page_count', 'Unknown')}")
        lines.append("")
    
    # Text extraction
    if 'text_content' in extraction_data:
        text_stats = extraction_data.get('text_stats', {})
        lines.append("=== TEXT EXTRACTION ===")
        lines.append(f"Characters: {text_stats.get('char_count', 0):,}")
        lines.append(f"Words: {text_stats.get('word_count', 0):,}")
        lines.append(f"Lines: {text_stats.get('line_count', 0):,}")
        lines.append("")
    
    # Images
    if 'images' in extraction_data:
        images = extraction_data['images']
        lines.append(f"=== IMAGES ({len(images)} found) ===")
        for i, img in enumerate(images[:5], 1):  # Show first 5
            lines.append(f"Image {i}: {img.get('format', 'Unknown')} - {img.get('size', 'Unknown size')}")
        if len(images) > 5:
            lines.append(f"... and {len(images) - 5} more images")
        lines.append("")
    
    # Tables
    if 'tables' in extraction_data:
        tables = extraction_data['tables']
        lines.append(f"=== TABLES ({len(tables)} found) ===")
        for i, table in enumerate(tables[:3], 1):  # Show first 3
            rows = len(table.get('data', []))
            cols = len(table.get('data', [{}])[0]) if table.get('data') else 0
            lines.append(f"Table {i}: {rows} rows × {cols} columns")
        if len(tables) > 3:
            lines.append(f"... and {len(tables) - 3} more tables")
        lines.append("")
    
    return "\n".join(lines)


class TextFormatter:
    """Handles text cleaning and formatting for extracted PDF content."""
    
    def __init__(self):
        # Common patterns for text cleaning
        self.whitespace_pattern = re.compile(r'\s+')
        self.line_break_pattern = re.compile(r'\n\s*\n')
        self.bullet_pattern = re.compile(r'^[\u2022\u2023\u25e6\u2043\u2219•·‣⁃]\s*', re.MULTILINE)
        
    def clean_text(self, text: str, preserve_formatting: bool = True) -> str:
        """
        Clean extracted text while optionally preserving formatting.
        
        Args:
            text: Raw extracted text
            preserve_formatting: Whether to preserve line breaks and spacing
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove null characters and other problematic characters
        text = text.replace('\x00', '').replace('\ufffd', '')
        
        if preserve_formatting:
            # Preserve formatting but clean up excessive whitespace
            # Normalize line breaks
            text = self.line_break_pattern.sub('\n\n', text)
            # Clean up spaces but preserve single line breaks
            text = re.sub(r'[ \t]+', ' ', text)
        else:
            # Aggressive cleaning - normalize all whitespace
            text = self.whitespace_pattern.sub(' ', text)
        
        return text.strip()
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Attempt to extract common resume/document sections.
        
        Args:
            text: Cleaned text content
            
        Returns:
            Dictionary with identified sections
        """
        sections = {}
        
        # Common section headers (case-insensitive)
        section_patterns = {
            'contact': r'(?i)(?:contact|personal\s+(?:information|details))',
            'summary': r'(?i)(?:summary|profile|objective|about)',
            'experience': r'(?i)(?:(?:work\s+)?experience|employment|professional\s+experience)',
            'education': r'(?i)(?:education|academic|qualifications)',
            'skills': r'(?i)(?:skills|competencies|technical\s+skills)',
            'projects': r'(?i)(?:projects|portfolio)',
            'certifications': r'(?i)(?:certifications?|certificates?|licenses?)',
            'achievements': r'(?i)(?:achievements?|awards?|honors?)',
            'references': r'(?i)(?:references?)'
        }
        
        # Split text into potential sections
        lines = text.split('\n')
        current_section = 'content'
        sections[current_section] = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line matches a section header
            section_found = None
            for section_name, pattern in section_patterns.items():
                if re.match(pattern, line) and len(line) < 50:  # Headers are usually short
                    section_found = section_name
                    break
            
            if section_found:
                current_section = section_found
                if current_section not in sections:
                    sections[current_section] = []
            else:
                sections[current_section].append(line)
        
        # Convert lists to strings
        for section in sections:
            sections[section] = '\n'.join(sections[section]).strip()
        
        # Remove empty sections
        sections = {k: v for k, v in sections.items() if v}
        
        return sections
    
    def format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format PDF metadata into readable text."""
        if not metadata:
            return "No metadata available"
        
        formatted = []
        
        # Format common metadata fields
        field_map = {
            'title': 'Title',
            'author': 'Author', 
            'subject': 'Subject',
            'creator': 'Creator',
            'producer': 'Producer',
            'creation_date': 'Created',
            'modification_date': 'Modified',
            'page_count': 'Pages',
            'pdf_version': 'PDF Version',
            'file_size': 'File Size',
            'encrypted': 'Encrypted'
        }
        
        for key, label in field_map.items():
            if key in metadata and metadata[key]:
                value = metadata[key]
                
                # Format dates
                if 'date' in key and isinstance(value, str):
                    try:
                        # Try to parse and reformat date
                        if value.startswith('D:'):  # PDF date format
                            # PDF date format: D:YYYYMMDDHHmmSSOHH'mm'
                            date_part = value[2:16]  # YYYYMMDDHHMMSS
                            if len(date_part) >= 8:
                                formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                                if len(date_part) >= 14:
                                    formatted_date += f" {date_part[8:10]}:{date_part[10:12]}:{date_part[12:14]}"
                                value = formatted_date
                    except:
                        pass  # Keep original value if parsing fails
                
                # Format file size
                elif key == 'file_size' and isinstance(value, int):
                    value = format_file_size(value)
                
                formatted.append(f"{label}: {value}")
        
        return '\n'.join(formatted) if formatted else "No readable metadata found"
    
    def create_extraction_report(self, extraction_data: Dict[str, Any]) -> str:
        """Create a comprehensive extraction report."""
        report_sections = []
        
        # Header
        report_sections.append("PDF EXTRACTION REPORT")
        report_sections.append("=" * 50)
        report_sections.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_sections.append("")
        
        # Metadata section
        if 'metadata' in extraction_data:
            report_sections.append("DOCUMENT METADATA")
            report_sections.append("-" * 20)
            report_sections.append(self.format_metadata(extraction_data['metadata']))
            report_sections.append("")
        
        # Content summary
        if 'text_content' in extraction_data:
            report_sections.append("CONTENT SUMMARY")
            report_sections.append("-" * 20)
            text_stats = extraction_data.get('text_stats', {})
            report_sections.append(f"Text Length: {text_stats.get('char_count', 0):,} characters")
            report_sections.append(f"Word Count: {text_stats.get('word_count', 0):,} words")
            report_sections.append(f"Line Count: {text_stats.get('line_count', 0):,} lines")
            report_sections.append("")
        
        # Sections
        if 'sections' in extraction_data:
            report_sections.append("IDENTIFIED SECTIONS")
            report_sections.append("-" * 20)
            for section_name in extraction_data['sections'].keys():
                report_sections.append(f"• {section_name.title()}")
            report_sections.append("")
        
        # Additional content
        content_types = []
        if extraction_data.get('images'):
            content_types.append(f"{len(extraction_data['images'])} images")
        if extraction_data.get('tables'):
            content_types.append(f"{len(extraction_data['tables'])} tables")
        
        if content_types:
            report_sections.append("EXTRACTED CONTENT")
            report_sections.append("-" * 20)
            report_sections.append(", ".join(content_types))
            report_sections.append("")
        
        return "\n".join(report_sections)