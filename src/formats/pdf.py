"""
PDF creation from downloaded images.
"""

from pathlib import Path
from io import BytesIO
from typing import Optional
from PIL import Image
try:
    import pillow_avif
except ImportError:
    pass
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from ..utils.logger import get_logger

logger = get_logger(__name__)


def create_pdf(
    image_paths: list[Path],
    output_path: str | Path,
    title: str = "Manga Chapter"
) -> Path:
    """
    Create a PDF from a list of image files.
    
    Args:
        image_paths: List of image file paths
        output_path: Output PDF file path
        title: PDF title metadata
    
    Returns:
        Path to created PDF
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not image_paths:
        logger.warning("No images provided for PDF creation")
        return output_path
    
    # Get dimensions from first image for reference
    first_img = Image.open(image_paths[0])
    
    c = canvas.Canvas(str(output_path))
    c.setTitle(title)
    
    for img_path in sorted(image_paths):
        try:
            img = Image.open(img_path)
            
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get image dimensions
            img_width, img_height = img.size
            
            # Set PDF page size to match image
            c.setPageSize((img_width, img_height))
            
            # Draw image on page
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            
            c.drawImage(ImageReader(img_buffer), 0, 0, img_width, img_height)
            c.showPage()
            
            logger.debug(f"Added to PDF: {img_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to add image {img_path} to PDF: {e}")
            continue
    
    c.save()
    logger.info(f"Created PDF: {output_path}")
    return output_path


def create_pdf_from_bytes(
    image_data: list[tuple[int, bytes]],
    output_path: str | Path,
    title: str = "Manga Chapter"
) -> Path:
    """
    Create a PDF directly from image bytes without saving to disk first.
    
    Args:
        image_data: List of (index, image_bytes) tuples
        output_path: Output PDF file path
        title: PDF title metadata
    
    Returns:
        Path to created PDF
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not image_data:
        logger.warning("No images provided for PDF creation")
        return output_path
    
    c = canvas.Canvas(str(output_path))
    c.setTitle(title)
    
    for idx, data in sorted(image_data, key=lambda x: x[0]):
        try:
            img = Image.open(BytesIO(data))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_width, img_height = img.size
            c.setPageSize((img_width, img_height))
            
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            
            c.drawImage(ImageReader(img_buffer), 0, 0, img_width, img_height)
            c.showPage()
            
        except Exception as e:
            logger.error(f"Failed to add image {idx} to PDF: {e}")
            continue
    
    c.save()
    logger.info(f"Created PDF: {output_path}")
    return output_path
