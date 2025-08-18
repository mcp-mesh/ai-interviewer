"""PDF table extraction tools using pdfplumber."""

import pdfplumber
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import csv
import io
import logging

try:
    from ..config.settings import get_settings
except ImportError:
    from config.settings import get_settings


logger = logging.getLogger(__name__)


class PDFTableExtractor:
    """Handles extraction of tables from PDF files using pdfplumber."""
    
    def __init__(self):
        self.settings = get_settings()
        self.max_pages = self.settings.processing.max_pages
        self.table_format = self.settings.extraction.table_format
        self.output_dir = Path(self.settings.output_dir)
        
        # Create output directory if needed
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_tables(self, file_path: str, save_tables: bool = False) -> Dict[str, Any]:
        """
        Extract all tables from PDF file.
        
        Args:
            file_path: Path to PDF file
            save_tables: Whether to save tables to disk
            
        Returns:
            Dictionary containing extracted table information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        logger.info(f"Extracting tables from {file_path}")
        
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                tables = []
                pages_processed = min(len(pdf.pages), self.max_pages)
                
                for page_num in range(pages_processed):
                    page = pdf.pages[page_num]
                    page_tables = self._extract_page_tables(page, page_num + 1)
                    tables.extend(page_tables)
                
                # Save tables if requested
                if save_tables and tables:
                    self._save_tables(tables, file_path.stem)
                
                return {
                    'tables': tables,
                    'total_tables': len(tables),
                    'pages_processed': pages_processed,
                    'total_pages': len(pdf.pages),
                    'extraction_success': True,
                    'tables_saved_to_disk': save_tables,
                    'output_directory': str(self.output_dir) if save_tables else None
                }
                
        except Exception as e:
            logger.error(f"Table extraction failed for {file_path}: {e}")
            return {
                'tables': [],
                'total_tables': 0,
                'extraction_error': str(e),
                'extraction_success': False
            }
    
    def _extract_page_tables(self, page, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract tables from a single page.
        
        Args:
            page: pdfplumber page object
            page_num: Page number (1-based)
            
        Returns:
            List of table dictionaries
        """
        page_tables = []
        
        try:
            # Find tables on the page
            tables = page.find_tables()
            
            for table_index, table in enumerate(tables):
                try:
                    # Extract table data
                    table_data = table.extract()
                    
                    if not table_data or not any(table_data):
                        continue
                    
                    # Clean and process table data
                    cleaned_data = self._clean_table_data(table_data)
                    
                    if not cleaned_data:
                        continue
                    
                    # Create table information
                    table_info = {
                        'page': page_num,
                        'table_index': table_index,
                        'data': cleaned_data,
                        'rows': len(cleaned_data),
                        'columns': len(cleaned_data[0]) if cleaned_data else 0,
                        'bbox': table.bbox,  # Bounding box coordinates
                        'has_header': self._detect_header(cleaned_data),
                        'extraction_success': True
                    }
                    
                    # Add formatted versions
                    table_info['formatted'] = self._format_table(cleaned_data, self.table_format)
                    
                    page_tables.append(table_info)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract table {table_index} from page {page_num}: {e}")
                    continue
            
        except Exception as e:
            logger.warning(f"Failed to find tables on page {page_num}: {e}")
        
        return page_tables
    
    def _clean_table_data(self, raw_data: List[List]) -> List[List[str]]:
        """
        Clean and normalize table data.
        
        Args:
            raw_data: Raw table data from pdfplumber
            
        Returns:
            Cleaned table data
        """
        if not raw_data:
            return []
        
        cleaned = []
        
        for row in raw_data:
            if not row or all(cell is None or (isinstance(cell, str) and not cell.strip()) for cell in row):
                continue  # Skip empty rows
            
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append('')
                else:
                    # Clean cell content
                    cell_str = str(cell).strip()
                    # Remove excessive whitespace
                    cell_str = ' '.join(cell_str.split())
                    cleaned_row.append(cell_str)
            
            cleaned.append(cleaned_row)
        
        # Ensure all rows have the same number of columns
        if cleaned:
            max_columns = max(len(row) for row in cleaned)
            for row in cleaned:
                while len(row) < max_columns:
                    row.append('')
        
        return cleaned
    
    def _detect_header(self, table_data: List[List[str]]) -> bool:
        """
        Detect if the table has a header row.
        
        Args:
            table_data: Cleaned table data
            
        Returns:
            True if header detected
        """
        if not table_data or len(table_data) < 2:
            return False
        
        first_row = table_data[0]
        second_row = table_data[1] if len(table_data) > 1 else []
        
        # Simple heuristics for header detection
        header_indicators = 0
        
        # Check if first row cells are non-numeric while second row has numbers
        for i, (first_cell, second_cell) in enumerate(zip(first_row, second_row)):
            if first_cell and second_cell:
                try:
                    # If second row is numeric but first is not
                    float(second_cell.replace(',', '').replace('$', '').replace('%', ''))
                    if not first_cell.replace(' ', '').isdigit():
                        header_indicators += 1
                except ValueError:
                    pass
        
        # Check for common header patterns
        first_row_text = ' '.join(first_row).lower()
        header_keywords = ['name', 'date', 'amount', 'total', 'description', 'item', 'price', 'quantity']
        
        if any(keyword in first_row_text for keyword in header_keywords):
            header_indicators += 1
        
        return header_indicators >= 1
    
    def _format_table(self, table_data: List[List[str]], format_type: str) -> Any:
        """
        Format table data in specified format.
        
        Args:
            table_data: Cleaned table data
            format_type: Output format ('json', 'csv', 'dict')
            
        Returns:
            Formatted table data
        """
        if not table_data:
            return None
        
        if format_type.lower() == 'json':
            # Convert to list of dictionaries if has header
            if self._detect_header(table_data) and len(table_data) > 1:
                headers = table_data[0]
                rows = table_data[1:]
                return [dict(zip(headers, row)) for row in rows]
            else:
                # Return as array of arrays
                return table_data
        
        elif format_type.lower() == 'csv':
            # Convert to CSV string
            output = io.StringIO()
            writer = csv.writer(output)
            for row in table_data:
                writer.writerow(row)
            return output.getvalue()
        
        elif format_type.lower() == 'dict':
            # Return as dictionary with metadata
            result = {
                'headers': table_data[0] if self._detect_header(table_data) else None,
                'data': table_data[1:] if self._detect_header(table_data) else table_data,
                'rows': len(table_data),
                'columns': len(table_data[0]) if table_data else 0
            }
            return result
        
        else:
            # Default to original format
            return table_data
    
    def _save_tables(self, tables: List[Dict[str, Any]], base_filename: str) -> None:
        """
        Save extracted tables to disk.
        
        Args:
            tables: List of table dictionaries
            base_filename: Base filename for output files
        """
        for i, table in enumerate(tables):
            try:
                # Create filename
                filename = f"{base_filename}_page{table['page']:03d}_table{i+1:03d}"
                
                if self.table_format.lower() == 'json':
                    output_path = self.output_dir / f"{filename}.json"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(table['formatted'], f, indent=2, ensure_ascii=False)
                
                elif self.table_format.lower() == 'csv':
                    output_path = self.output_dir / f"{filename}.csv"
                    with open(output_path, 'w', encoding='utf-8', newline='') as f:
                        f.write(table['formatted'])
                
                logger.info(f"Saved table: {output_path}")
                
            except Exception as e:
                logger.warning(f"Failed to save table {i+1}: {e}")
    
    def extract_page_tables(self, file_path: str, page_num: int, save_tables: bool = False) -> Dict[str, Any]:
        """
        Extract tables from a specific page.
        
        Args:
            file_path: Path to PDF file
            page_num: Page number (1-based)
            save_tables: Whether to save tables to disk
            
        Returns:
            Dictionary containing extracted table information
        """
        file_path = Path(file_path)
        page_index = page_num - 1  # Convert to 0-based
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                if page_index >= len(pdf.pages) or page_index < 0:
                    raise ValueError(f"Page {page_num} does not exist (PDF has {len(pdf.pages)} pages)")
                
                page = pdf.pages[page_index]
                tables = self._extract_page_tables(page, page_num)
                
                # Save tables if requested
                if save_tables and tables:
                    self._save_tables(tables, f"{file_path.stem}_page{page_num}")
                
                return {
                    'page': page_num,
                    'tables': tables,
                    'total_tables': len(tables),
                    'extraction_success': True,
                    'tables_saved_to_disk': save_tables,
                    'output_directory': str(self.output_dir) if save_tables else None
                }
                
        except Exception as e:
            logger.error(f"Table extraction failed for page {page_num} of {file_path}: {e}")
            return {
                'page': page_num,
                'tables': [],
                'total_tables': 0,
                'extraction_error': str(e),
                'extraction_success': False
            }
    
    def get_table_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about tables in PDF without extracting them.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with table information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                table_info = {
                    'total_tables': 0,
                    'pages_with_tables': 0,
                    'page_details': []
                }
                
                pages_to_check = min(len(pdf.pages), self.max_pages)
                
                for page_num in range(pages_to_check):
                    page = pdf.pages[page_num]
                    
                    try:
                        tables = page.find_tables()
                        table_count = len(tables)
                        
                        table_info['total_tables'] += table_count
                        
                        if table_count > 0:
                            table_info['pages_with_tables'] += 1
                            table_info['page_details'].append({
                                'page': page_num + 1,
                                'table_count': table_count
                            })
                    
                    except Exception as e:
                        logger.warning(f"Failed to check tables on page {page_num + 1}: {e}")
                        continue
                
                return table_info
                
        except Exception as e:
            logger.error(f"Failed to get table info for {file_path}: {e}")
            return {
                'total_tables': 0,
                'pages_with_tables': 0,
                'page_details': [],
                'error': str(e)
            }