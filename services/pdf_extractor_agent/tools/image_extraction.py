"""PDF image extraction tools."""

import fitz  # PyMuPDF
from PIL import Image
from typing import Dict, Any, List, Optional
from pathlib import Path
import io
import logging

try:
    from ..config.settings import get_settings
    from ..utils.formatting import format_file_size
except ImportError:
    from config.settings import get_settings
    from utils.formatting import format_file_size


logger = logging.getLogger(__name__)


class PDFImageExtractor:
    """Handles extraction of images from PDF files."""
    
    def __init__(self):
        self.settings = get_settings()
        self.max_images = self.settings.processing.max_image_count
        self.max_image_size_mb = self.settings.processing.max_image_size_mb
        self.image_format = self.settings.extraction.image_format
        self.output_dir = Path(self.settings.output_dir)
        
        # Create output directory if needed
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_images(self, file_path: str, save_images: bool = False) -> Dict[str, Any]:
        """
        Extract all images from PDF file.
        
        Args:
            file_path: Path to PDF file
            save_images: Whether to save images to disk
            
        Returns:
            Dictionary containing extracted image information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        logger.info(f"Extracting images from {file_path}")
        
        doc = fitz.open(str(file_path))
        
        try:
            images = []
            total_extracted = 0
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    if total_extracted >= self.max_images:
                        logger.warning(f"Reached maximum image limit of {self.max_images}")
                        break
                    
                    try:
                        image_info = self._extract_single_image(
                            doc, img, page_num + 1, img_index, save_images
                        )
                        
                        if image_info:
                            images.append(image_info)
                            total_extracted += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
                        continue
                
                if total_extracted >= self.max_images:
                    break
            
            return {
                'images': images,
                'total_images': len(images),
                'pages_processed': len(doc),
                'extraction_success': True,
                'images_saved_to_disk': save_images,
                'output_directory': str(self.output_dir) if save_images else None
            }
            
        except Exception as e:
            logger.error(f"Image extraction failed for {file_path}: {e}")
            return {
                'images': [],
                'total_images': 0,
                'extraction_error': str(e),
                'extraction_success': False
            }
        
        finally:
            doc.close()
    
    def _extract_single_image(
        self, 
        doc, 
        img_ref: tuple, 
        page_num: int, 
        img_index: int, 
        save_to_disk: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Extract a single image from PDF.
        
        Args:
            doc: PyMuPDF document object
            img_ref: Image reference tuple
            page_num: Page number (1-based)
            img_index: Image index on page
            save_to_disk: Whether to save image to disk
            
        Returns:
            Dictionary with image information or None if extraction failed
        """
        try:
            # Get image reference
            xref = img_ref[0]
            pix = fitz.Pixmap(doc, xref)
            
            # Skip CMYK images (not supported by PIL directly)
            if pix.n - pix.alpha < 4:
                # Convert to RGB if needed
                if pix.colorspace and pix.colorspace.name != fitz.csRGB.name:
                    rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                    pix = rgb_pix
                
                # Get image data
                img_data = pix.tobytes(self.image_format.lower())
                
                # Check image size
                image_size_mb = len(img_data) / (1024 * 1024)
                if image_size_mb > self.max_image_size_mb:
                    logger.warning(f"Image too large: {image_size_mb:.2f}MB exceeds limit of {self.max_image_size_mb}MB")
                    return None
                
                # Create PIL Image for additional information
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Generate filename
                base_filename = Path(doc.name).stem if doc.name else "unknown"
                filename = f"{base_filename}_page{page_num:03d}_img{img_index:03d}.{self.image_format.lower()}"
                
                image_info = {
                    'page': page_num,
                    'image_index': img_index,
                    'filename': filename,
                    'format': self.image_format,
                    'width': pix.width,
                    'height': pix.height,
                    'colorspace': pix.colorspace.name if pix.colorspace else 'Unknown',
                    'has_alpha': bool(pix.alpha),
                    'size_bytes': len(img_data),
                    'size_mb': image_size_mb,
                    'size_formatted': format_file_size(len(img_data)),
                    'dpi': (pix.xres, pix.yres) if hasattr(pix, 'xres') else None,
                    'mode': pil_image.mode,
                    'extraction_success': True
                }
                
                # Save to disk if requested
                if save_to_disk:
                    output_path = self.output_dir / filename
                    try:
                        with open(output_path, 'wb') as f:
                            f.write(img_data)
                        image_info['saved_path'] = str(output_path)
                        logger.info(f"Saved image: {output_path}")
                    except Exception as e:
                        logger.warning(f"Failed to save image {filename}: {e}")
                        image_info['save_error'] = str(e)
                else:
                    # Store image data as base64 for in-memory use
                    import base64
                    image_info['image_data_base64'] = base64.b64encode(img_data).decode('utf-8')
                
                return image_info
            
            else:
                logger.warning(f"Skipping CMYK image on page {page_num}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to extract image {img_index} from page {page_num}: {e}")
            return None
        
        finally:
            if 'pix' in locals():
                pix = None  # Release memory
    
    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about images in PDF without extracting them.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with image information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        doc = fitz.open(str(file_path))
        
        try:
            image_info = {
                'total_images': 0,
                'pages_with_images': 0,
                'page_details': []
            }
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                page_image_count = len(image_list)
                image_info['total_images'] += page_image_count
                
                if page_image_count > 0:
                    image_info['pages_with_images'] += 1
                    
                    image_info['page_details'].append({
                        'page': page_num + 1,
                        'image_count': page_image_count
                    })
            
            return image_info
            
        finally:
            doc.close()
    
    def extract_page_images(self, file_path: str, page_num: int, save_images: bool = False) -> Dict[str, Any]:
        """
        Extract images from a specific page.
        
        Args:
            file_path: Path to PDF file
            page_num: Page number (1-based)
            save_images: Whether to save images to disk
            
        Returns:
            Dictionary containing extracted image information
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
            image_list = page.get_images(full=True)
            
            images = []
            for img_index, img in enumerate(image_list[:self.max_images]):
                try:
                    image_info = self._extract_single_image(
                        doc, img, page_num, img_index, save_images
                    )
                    
                    if image_info:
                        images.append(image_info)
                        
                except Exception as e:
                    logger.warning(f"Failed to extract image {img_index} from page {page_num}: {e}")
                    continue
            
            return {
                'page': page_num,
                'images': images,
                'total_images': len(images),
                'extraction_success': True,
                'images_saved_to_disk': save_images,
                'output_directory': str(self.output_dir) if save_images else None
            }
            
        finally:
            doc.close()
    
    def cleanup_output_directory(self) -> Dict[str, Any]:
        """
        Clean up the output directory by removing old image files.
        
        Returns:
            Dictionary with cleanup results
        """
        try:
            if not self.output_dir.exists():
                return {'cleaned_files': 0, 'message': 'Output directory does not exist'}
            
            # Remove all image files
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']
            cleaned_files = 0
            
            for file_path in self.output_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    try:
                        file_path.unlink()
                        cleaned_files += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_path}: {e}")
            
            return {
                'cleaned_files': cleaned_files,
                'output_directory': str(self.output_dir),
                'cleanup_success': True
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {
                'cleaned_files': 0,
                'cleanup_error': str(e),
                'cleanup_success': False
            }