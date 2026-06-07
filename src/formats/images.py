"""
Image saving utilities.
"""

from pathlib import Path
from typing import Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)


def save_images(
    image_data: list[tuple[int, bytes]],
    output_dir: str | Path,
    chapter_name: str
) -> list[Path]:
    """
    Save downloaded images to a folder.
    
    Args:
        image_data: List of (index, image_bytes) tuples
        output_dir: Base output directory
        chapter_name: Chapter folder name
    
    Returns:
        List of saved image paths
    """
    chapter_dir = Path(output_dir) / chapter_name
    chapter_dir.mkdir(parents=True, exist_ok=True)
    
    saved_paths = []
    
    for idx, data in sorted(image_data, key=lambda x: x[0]):
        # Determine file extension from data
        ext = _get_image_extension(data)
        filename = f"{idx:03d}{ext}"
        filepath = chapter_dir / filename
        
        with open(filepath, "wb") as f:
            f.write(data)
        
        saved_paths.append(filepath)
        logger.debug(f"Saved image: {filepath}")
    
    logger.info(f"Saved {len(saved_paths)} images to {chapter_dir}")
    return saved_paths


def _get_image_extension(data: bytes) -> str:
    """Determine image extension from file header."""
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return ".png"
    elif data[:2] == b'\xff\xd8':
        return ".jpg"
    elif data[:6] in (b'GIF87a', b'GIF89a'):
        return ".gif"
    elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return ".webp"
    elif data[4:8] == b'ftyp' and b'avif' in data[8:16]:
        return ".avif"
    else:
        return ".jpg"  # Default to jpg


def cleanup_images(image_paths: list[Path]) -> None:
    """Delete image files after conversion."""
    for path in image_paths:
        try:
            path.unlink()
            logger.debug(f"Deleted: {path}")
        except OSError as e:
            logger.warning(f"Failed to delete {path}: {e}")
    
    # Try to remove empty directory
    if image_paths:
        parent = image_paths[0].parent
        try:
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                logger.debug(f"Removed empty directory: {parent}")
        except OSError:
            pass
