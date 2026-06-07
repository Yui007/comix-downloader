"""
CBZ (Comic Book ZIP) creation with ComicInfo.xml metadata.
"""

import zipfile
from pathlib import Path
from io import BytesIO
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from typing import Optional
from ..core.models import MangaInfo, Chapter
from ..utils.logger import get_logger

logger = get_logger(__name__)


def create_comic_info_xml(
    manga: MangaInfo,
    chapter: Chapter,
    page_count: int
) -> str:
    """
    Create ComicInfo.xml content for CBZ metadata.
    
    Args:
        manga: Manga information
        chapter: Chapter information
        page_count: Number of pages
    
    Returns:
        XML string
    """
    root = Element("ComicInfo")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
    
    # Title
    SubElement(root, "Title").text = chapter.get_display_name()
    
    # Series info
    SubElement(root, "Series").text = manga.title
    
    if manga.alt_titles:
        SubElement(root, "AlternateSeries").text = manga.alt_titles[0] if manga.alt_titles else ""
    
    # Chapter/Volume numbers
    try:
        SubElement(root, "Number").text = str(chapter.number)
    except (ValueError, TypeError):
        pass
    
    if chapter.volume:
        try:
            SubElement(root, "Volume").text = str(chapter.volume)
        except (ValueError, TypeError):
            pass
    
    # Summary
    if manga.description:
        SubElement(root, "Summary").text = manga.description[:2000]  # Limit length
    
    # Year
    if manga.year:
        SubElement(root, "Year").text = str(manga.year)
    
    # Publisher/Team
    if chapter.group_name:
        SubElement(root, "Publisher").text = chapter.group_name
    
    # Genre
    if manga.genres:
        SubElement(root, "Genre").text = ", ".join(str(g) for g in manga.genres[:10])
    
    # Page count
    SubElement(root, "PageCount").text = str(page_count)
    
    # Language
    if manga.original_language:
        SubElement(root, "LanguageISO").text = manga.original_language
    
    # Manga type
    SubElement(root, "Manga").text = "Yes" if manga.manga_type in ("manga", "manhwa", "manhua") else "Unknown"
    
    # Rating
    if manga.rated_avg:
        # Convert to 5-star scale
        rating = min(5.0, max(0.0, float(manga.rated_avg)))
        SubElement(root, "CommunityRating").text = f"{rating:.1f}"
    
    # Status
    if manga.status:
        SubElement(root, "SeriesStatus").text = manga.status.title()
    
    # NSFW flag
    if manga.is_nsfw:
        SubElement(root, "AgeRating").text = "Adults Only 18+"
    
    # Web link
    SubElement(root, "Web").text = f"https://comix.to/title/{manga.hash_id}-{manga.slug}"
    
    # Format to pretty XML
    xml_str = tostring(root, encoding="unicode")
    parsed = minidom.parseString(xml_str)
    return parsed.toprettyxml(indent="  ", encoding=None)


def create_cbz(
    image_paths: list[Path],
    output_path: str | Path,
    manga: Optional[MangaInfo] = None,
    chapter: Optional[Chapter] = None
) -> Path:
    """
    Create a CBZ archive from image files.
    
    Args:
        image_paths: List of image file paths
        output_path: Output CBZ file path
        manga: Manga information for ComicInfo.xml
        chapter: Chapter information for ComicInfo.xml
    
    Returns:
        Path to created CBZ
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not image_paths:
        logger.warning("No images provided for CBZ creation")
        return output_path
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as cbz:
        # Add images
        for img_path in sorted(image_paths):
            cbz.write(img_path, img_path.name)
            logger.debug(f"Added to CBZ: {img_path.name}")
        
        # Add ComicInfo.xml if manga info available
        if manga and chapter:
            comic_info = create_comic_info_xml(manga, chapter, len(image_paths))
            cbz.writestr("ComicInfo.xml", comic_info)
            logger.debug("Added ComicInfo.xml")
    
    logger.info(f"Created CBZ: {output_path}")
    return output_path


def create_cbz_from_bytes(
    image_data: list[tuple[int, bytes]],
    output_path: str | Path,
    manga: Optional[MangaInfo] = None,
    chapter: Optional[Chapter] = None
) -> Path:
    """
    Create a CBZ archive directly from image bytes.
    
    Args:
        image_data: List of (index, image_bytes) tuples
        output_path: Output CBZ file path
        manga: Manga information for ComicInfo.xml
        chapter: Chapter information for ComicInfo.xml
    
    Returns:
        Path to created CBZ
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not image_data:
        logger.warning("No images provided for CBZ creation")
        return output_path
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as cbz:
        # Add images
        for idx, data in sorted(image_data, key=lambda x: x[0]):
            ext = _get_extension_from_bytes(data)
            filename = f"{idx:03d}{ext}"
            cbz.writestr(filename, data)
        
        # Add ComicInfo.xml if manga info available
        if manga and chapter:
            comic_info = create_comic_info_xml(manga, chapter, len(image_data))
            cbz.writestr("ComicInfo.xml", comic_info)
    
    logger.info(f"Created CBZ: {output_path}")
    return output_path


def _get_extension_from_bytes(data: bytes) -> str:
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
        return ".jpg"
