"""
Main downloader with threading support for concurrent downloads.
"""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Optional, Callable
from rich.progress import Progress, TaskID, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

from .models import MangaInfo, Chapter, DownloadConfig, OutputFormat
from ..api.comix import ComixAPI
from ..formats.images import save_images, cleanup_images
from ..formats.pdf import create_pdf
from ..formats.cbz import create_cbz
from ..utils.retry import RetryableDownloader
from ..utils.logger import get_logger
from ..utils.session import get_session

logger = get_logger(__name__)

# Global event to signal cancellation across all downloaders
_cancel_event = threading.Event()

def cancel_downloads():
    """Signal all active downloaders to stop."""
    _cancel_event.set()
    logger.warning("Cancellation signal received. Stopping downloads...")

def is_cancelled():
    """Check if cancellation has been signaled."""
    return _cancel_event.is_set()


class ImageDownloader:
    """Downloads images with threading and retry logic."""
    
    def __init__(self, config: DownloadConfig):
        self.config = config
        self.retrier = RetryableDownloader(
            max_retries=config.retry_count,
            base_delay=config.retry_delay
        )
    
    def download_image(self, url: str, index: int) -> tuple[int, bytes | None, str | None]:
        """
        Download a single image with retry logic.
        
        Returns:
            Tuple of (index, image_bytes, error_message)
        """
        def _download():
            if is_cancelled():
                raise InterruptedError("Download cancelled")
                
            logger.debug(f"Starting download of image {index}: {url}")
            response = get_session().get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Use chunks like test.py for better speed and lower memory usage
            content = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                if is_cancelled():
                    raise InterruptedError("Download cancelled")
                if chunk:
                    content.extend(chunk)
            return bytes(content)
        
        success, data, error = self.retrier.download_with_retry(
            _download,
            f"Image {index}"
        )
        
        return index, data if success else None, error
    
    def download_all_images(
        self,
        image_urls: list[str],
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
        on_progress: Optional[Callable[[int, int], None]] = None
    ) -> list[tuple[int, bytes]]:
        """
        Download all images concurrently.
        
        Returns:
            List of (index, image_bytes) tuples for successful downloads
        """
        results = []
        failed = []
        
        logger.info(f"Downloading {len(image_urls)} images concurrently...")
        
        with ThreadPoolExecutor(max_workers=self.config.max_image_workers) as executor:
            futures = {
                executor.submit(self.download_image, url, idx): idx
                for idx, url in enumerate(image_urls, 1)
            }
            
            for future in as_completed(futures):
                if is_cancelled():
                    break
                idx = futures[future]
                try:
                    index, data, error = future.result()
                    if data:
                        results.append((index, data))
                    else:
                        failed.append((index, error))
                        logger.error(f"Failed to download image {index}: {error}")
                except Exception as e:
                    failed.append((idx, str(e)))
                    logger.error(f"Exception downloading image {idx}: {e}")
                
                if progress and task_id:
                    progress.advance(task_id)
                
                if on_progress:
                    on_progress(len(results) + len(failed), len(image_urls))
        
        if failed:
            logger.warning(f"{len(failed)} images failed to download")
        
        return sorted(results, key=lambda x: x[0])


class ChapterDownloader:
    """Downloads a single chapter with all its images."""
    
    def __init__(self, config: DownloadConfig, manga: MangaInfo):
        self.config = config
        self.manga = manga
        self.image_downloader = ImageDownloader(config)
    
    def download_chapter(
        self,
        chapter: Chapter,
        progress: Optional[Progress] = None,
        parent_task: Optional[TaskID] = None,
        on_image_progress: Optional[Callable[[int, int], None]] = None
    ) -> tuple[bool, str]:
        """
        Download a chapter and save in configured format.
        
        Returns:
            Tuple of (success, message)
        """
        manga_folder = self.manga.get_safe_title()
        chapter_folder = chapter.get_safe_folder_name()
        base_path = Path(self.config.download_path) / manga_folder
        
        try:
            # Fetch image URLs
            slug_or_id = self.manga.slug if self.manga.slug else self.manga.hash_id
            image_urls = ComixAPI.get_chapter_images(slug_or_id, chapter.chapter_id, chapter.number)
            
            if not image_urls:
                return False, f"No images found for {chapter.get_display_name()}"
            
            # Create task for image downloads
            task_id = None
            if progress:
                task_id = progress.add_task(
                    f"[cyan]  └─ {chapter.get_display_name()}",
                    total=len(image_urls)
                )
            
            # Download all images
            image_data = self.image_downloader.download_all_images(
                image_urls, progress, task_id, on_progress=on_image_progress
            )
            
            if not image_data:
                return False, f"Failed to download any images for {chapter.get_display_name()}"
            
            # Save in configured format
            if self.config.output_format == OutputFormat.IMAGES:
                save_images(image_data, base_path, chapter_folder)
                
            elif self.config.output_format == OutputFormat.PDF:
                if self.config.keep_images:
                    image_paths = save_images(image_data, base_path, chapter_folder)
                    pdf_path = base_path / f"{chapter_folder}.pdf"
                    create_pdf(image_paths, pdf_path, chapter.get_display_name())
                else:
                    from ..formats.pdf import create_pdf_from_bytes
                    pdf_path = base_path / f"{chapter_folder}.pdf"
                    create_pdf_from_bytes(image_data, pdf_path, chapter.get_display_name())
                    
            elif self.config.output_format == OutputFormat.CBZ:
                if self.config.keep_images:
                    image_paths = save_images(image_data, base_path, chapter_folder)
                    cbz_path = base_path / f"{chapter_folder}.cbz"
                    create_cbz(image_paths, cbz_path, self.manga, chapter)
                else:
                    from ..formats.cbz import create_cbz_from_bytes
                    cbz_path = base_path / f"{chapter_folder}.cbz"
                    create_cbz_from_bytes(image_data, cbz_path, self.manga, chapter)
            
            if progress and task_id:
                progress.update(task_id, completed=len(image_urls))
            
            return True, f"Downloaded {chapter.get_display_name()} ({len(image_data)} pages)"
            
        except Exception as e:
            logger.error(f"Error downloading chapter {chapter.number}: {e}")
            return False, f"Error: {str(e)}"


class MangaDownloader:
    """Main downloader orchestrating concurrent chapter downloads."""
    
    def __init__(self, config: DownloadConfig):
        self.config = config
    
    def download_chapters(
        self,
        manga: MangaInfo,
        chapters: list[Chapter],
        progress: Progress,
        on_chapter_complete: Optional[Callable[[Chapter, bool, str], None]] = None
    ) -> tuple[int, int]:
        """
        Download multiple chapters concurrently.
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        chapter_downloader = ChapterDownloader(self.config, manga)
        
        # Create main progress task
        main_task = progress.add_task(
            f"[bold green]Downloading {manga.title}",
            total=len(chapters)
        )
        
        with ThreadPoolExecutor(max_workers=self.config.max_chapter_workers) as executor:
            futures = {
                executor.submit(
                    chapter_downloader.download_chapter,
                    chapter,
                    progress,
                    main_task
                ): chapter
                for chapter in chapters
            }
            
            for future in as_completed(futures):
                if is_cancelled():
                    break
                chapter = futures[future]
                try:
                    success, message = future.result()
                    if success:
                        successful += 1
                    else:
                        failed += 1
                    
                    if on_chapter_complete:
                        on_chapter_complete(chapter, success, message)
                        
                except Exception as e:
                    failed += 1
                    logger.error(f"Exception downloading chapter {chapter.number}: {e}")
                    if on_chapter_complete:
                        on_chapter_complete(chapter, False, str(e))
                
                progress.advance(main_task)
        
        return successful, failed
