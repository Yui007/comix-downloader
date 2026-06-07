"""
Main downloader with threading support for concurrent downloads.
"""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Optional, Callable
from rich.progress import Progress, TaskID, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

from io import BytesIO
from PIL import Image
import requests

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

def get_scramble_order(seed: int, n: int = 25) -> list[int]:
    arr = list(range(n))
    state = seed & 0xFFFFFFFF
    for i in range(n - 1, 0, -1):
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        j = state % (i + 1)
        arr[i], arr[j] = arr[j], arr[i]
    return arr

def descramble_image(image_data: bytes, seed: int) -> bytes:
    try:
        img = Image.open(BytesIO(image_data))
    except Exception as e:
        logger.error(f"Failed to open image for descrambling: {e}")
        return image_data
        
    width, height = img.size
    tile_w = width // 5
    tile_h = height // 5
    
    perm = get_scramble_order(seed)
    
    out_img = Image.new(img.mode, (width, height))
    if img.mode == 'P':
        out_img = Image.new('RGBA', (width, height))
        img = img.convert('RGBA')
        
    out_img.paste(img, (0, 0)) # copy original as base
    
    for src_idx in range(25):
        dst_idx = perm[src_idx]
        src_c = src_idx % 5
        src_r = src_idx // 5
        dst_c = dst_idx % 5
        dst_r = dst_idx // 5
        
        src_box = (src_c * tile_w, src_r * tile_h, (src_c + 1) * tile_w, (src_r + 1) * tile_h)
        dst_box = (dst_c * tile_w, dst_r * tile_h)
        
        tile = img.crop(src_box)
        out_img.paste(tile, dst_box)
        
    out_io = BytesIO()
    fmt = img.format or "PNG"
    if fmt == "WEBP":
        out_img.save(out_io, format="WEBP", quality=95)
    else:
        if out_img.mode == 'RGBA':
            out_img = out_img.convert('RGB')
        out_img.save(out_io, format="JPEG", quality=90)
    return out_io.getvalue()

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
                
            is_scrambled = url.endswith("#scrambled")
            clean_url = url.split("#")[0]
            if not clean_url.startswith("http"):
                clean_url = "https://comix.to" + clean_url

            logger.debug(f"Starting download of image {index}: {clean_url}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://comix.to/",
                "Sec-Ch-Ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "image",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "cross-site",
            }
            if is_scrambled:
                headers["Origin"] = "https://comix.to"
                headers["Sec-Fetch-Mode"] = "cors"

            response = requests.get(clean_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            seed_str = response.headers.get("x-scramble-seed")
            seed = int(seed_str) if seed_str and seed_str.isdigit() else 0
            
            content = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                if is_cancelled():
                    raise InterruptedError("Download cancelled")
                if chunk:
                    content.extend(chunk)
                    
            if is_scrambled and seed != 0:
                logger.debug(f"Descrambling image {index} with seed {seed}")
                content = descramble_image(bytes(content), seed)
                
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
