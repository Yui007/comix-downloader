"""
Download Bridge - Handles download operations between Python and QML
"""

import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import threading

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class DownloadWorker(QThread):
    """Background worker for downloading chapters concurrently."""
    
    chapterProgress = pyqtSignal(str, int, int)  # chapter_name, current, total
    chapterComplete = pyqtSignal(str, bool, str)  # chapter_name, success, message
    overallProgress = pyqtSignal(int, int)  # completed, total
    finished = pyqtSignal(int, int)  # successful, failed
    error = pyqtSignal(str)
    
    def __init__(self, manga_dict: dict, chapters: list, config):
        super().__init__()
        self.manga_dict = manga_dict
        self.chapters = chapters
        self.config = config
        self._lock = threading.Lock()
        self._completed = 0
        self._successful = 0
        self._failed = 0
    
    def _download_single_chapter(self, chapter_dict, manga, total):
        """Download a single chapter. Called from thread pool."""
        try:
            from src.api.comix import ComixAPI
            from src.core.downloader import ChapterDownloader
            from src.core.models import Chapter
            
            # Convert dict to Chapter object
            chapter = Chapter(
                chapter_id=chapter_dict["chapter_id"],
                number=chapter_dict["number"],
                title=chapter_dict.get("title"),
                group_name=chapter_dict.get("group_name"),
                pages_count=chapter_dict.get("pages_count", 0)
            )
            
            chapter_name = chapter.get_display_name()
            
            # Download the chapter
            ch_downloader = ChapterDownloader(self.config, manga)
            success, message = ch_downloader.download_chapter(chapter)
            
            # Update progress with thread safety
            with self._lock:
                self._completed += 1
                if success:
                    self._successful += 1
                else:
                    self._failed += 1
                completed = self._completed
                successful = self._successful
                failed = self._failed
            
            # Emit signals (Qt handles thread safety for signals)
            self.chapterComplete.emit(chapter_name, success, message)
            self.overallProgress.emit(completed, total)
            
            return success, chapter_name
            
        except Exception as e:
            chapter_name = f"Chapter {chapter_dict.get('number', '?')}"
            with self._lock:
                self._completed += 1
                self._failed += 1
                completed = self._completed
            
            self.chapterComplete.emit(chapter_name, False, str(e))
            self.overallProgress.emit(completed, total)
            return False, chapter_name
    
    def run(self):
        try:
            from src.core.models import MangaInfo
            
            # Convert dict back to MangaInfo
            manga = MangaInfo(
                manga_id=self.manga_dict.get("manga_id"),
                hash_id=self.manga_dict.get("hash_id"),
                title=self.manga_dict.get("title", "Unknown"),
                alt_titles=self.manga_dict.get("alt_titles", []),
                manga_type=self.manga_dict.get("manga_type"),
                status=self.manga_dict.get("status"),
                poster_url=self.manga_dict.get("poster_url"),
                year=self.manga_dict.get("year"),
                rated_avg=self.manga_dict.get("rated_avg"),
                follows_total=self.manga_dict.get("follows_total"),
                is_nsfw=self.manga_dict.get("is_nsfw", False),
                description=self.manga_dict.get("description", "")
            )
            
            total = len(self.chapters)
            max_workers = self.config.max_chapter_workers
            
            # Use ThreadPoolExecutor for concurrent downloads
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self._download_single_chapter, ch, manga, total)
                    for ch in self.chapters
                ]
                
                # Wait for all to complete
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception:
                        pass  # Errors already handled in _download_single_chapter
            
            self.finished.emit(self._successful, self._failed)
            
        except Exception as e:
            self.error.emit(str(e))


class DownloadBridge(QObject):
    """Bridge for download operations exposed to QML."""
    
    downloadStarted = pyqtSignal()
    chapterProgress = pyqtSignal(str, int, int)
    chapterComplete = pyqtSignal(str, bool, str)
    overallProgress = pyqtSignal(int, int)
    downloadFinished = pyqtSignal(int, int)
    errorOccurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        # Import here to avoid circular imports
        from src.utils.config import ConfigManager
        self._config_manager = ConfigManager()
    
    @pyqtSlot('QVariant', 'QVariant', str, str)
    def startDownload(self, manga: dict, chapters, format_type: str, scanlator: str):
        """
        Start downloading selected chapters concurrently.
        
        Args:
            manga: Manga info dict
            chapters: List of selected chapter dicts (QJSValue from QML)
            format_type: Output format (images/pdf/cbz)
            scanlator: Preferred scanlator or empty for any
        """
        # Convert QJSValue to Python list
        if hasattr(chapters, 'toVariant'):
            chapters = chapters.toVariant()
        if not isinstance(chapters, list):
            chapters = list(chapters) if chapters else []
        
        if not chapters:
            self.errorOccurred.emit("No chapters selected")
            return
        
        # Import here to avoid circular imports
        from src.core.models import OutputFormat
        
        # Get config and update format
        config = self._config_manager.get_download_config()
        config.output_format = OutputFormat(format_type)
        
        # Filter by scanlator preference if specified
        if scanlator and scanlator != "Any":
            filtered = []
            seen_numbers = set()
            # Prioritize chapters from preferred scanlator
            for ch in chapters:
                if ch.get("group_name") == scanlator and ch["number"] not in seen_numbers:
                    filtered.append(ch)
                    seen_numbers.add(ch["number"])
            # Add remaining chapters for numbers not covered
            for ch in chapters:
                if ch["number"] not in seen_numbers:
                    filtered.append(ch)
                    seen_numbers.add(ch["number"])
            chapters = filtered
        else:
            # Get unique chapters by number
            seen = set()
            unique = []
            for ch in chapters:
                if ch["number"] not in seen:
                    unique.append(ch)
                    seen.add(ch["number"])
            chapters = unique
        
        self.downloadStarted.emit()
        
        # Create and start worker with concurrent downloads
        self._worker = DownloadWorker(manga, chapters, config)
        self._worker.chapterProgress.connect(self.chapterProgress.emit)
        self._worker.chapterComplete.connect(self.chapterComplete.emit)
        self._worker.overallProgress.connect(self.overallProgress.emit)
        self._worker.finished.connect(self.downloadFinished.emit)
        self._worker.error.connect(self.errorOccurred.emit)
        self._worker.start()
    
    @pyqtSlot()
    def cancelDownload(self):
        """Cancel the current download."""
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
