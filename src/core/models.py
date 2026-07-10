"""
Data models for manga, chapters, and configuration.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class OutputFormat(str, Enum):
    """Supported output formats."""
    IMAGES = "images"
    PDF = "pdf"
    CBZ = "cbz"


@dataclass
class MangaInfo:
    """Manga information from API."""
    manga_id: Optional[int] = None
    hash_id: Optional[str] = None
    title: str = "Unknown"
    alt_titles: list[str] = field(default_factory=list)
    slug: Optional[str] = None
    rank: Optional[int] = None
    manga_type: Optional[str] = None
    poster_url: Optional[str] = None
    original_language: Optional[str] = None
    status: Optional[str] = None
    final_chapter: Optional[str] = None
    latest_chapter: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    rated_avg: Optional[float] = None
    rated_count: Optional[int] = None
    follows_total: Optional[int] = None
    is_nsfw: bool = False
    year: Optional[int] = None
    genres: list = field(default_factory=list)
    description: str = ""
    
    def get_safe_title(self) -> str:
        """Get filesystem-safe title."""
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in self.title)
        return safe.strip()[:100]


@dataclass
class Chapter:
    """Chapter information."""
    chapter_id: int
    number: str
    title: Optional[str] = None
    volume: Optional[str] = None
    votes: Optional[int] = None
    group_name: Optional[str] = None
    pages_count: int = 0
    
    def get_display_name(self) -> str:
        """Get chapter display name."""
        name = f"Chapter {self.number}"
        if self.title:
            name += f": {self.title}"
        return name
    
    def get_safe_folder_name(self) -> str:
        """Get filesystem-safe folder name."""
        name = f"Chapter_{self.number}"
        if self.title:
            safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in self.title)
            name += f"_{safe_title[:50]}"
        return name


@dataclass
class DownloadConfig:
    """Download configuration."""
    output_format: OutputFormat = OutputFormat.IMAGES
    keep_images: bool = False
    enable_logs: bool = False
    max_chapter_workers: int = 3
    max_image_workers: int = 5
    download_path: str = "downloads"
    retry_count: int = 3
    retry_delay: float = 2.0
