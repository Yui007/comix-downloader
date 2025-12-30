"""
Download Bridge - Handles download operations between Python and QML
"""

import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class DownloadWorker(QThread):
    """Background worker for downloading chapters."""
    
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
    
    def run(self):
        try:
            # Import here to avoid circular imports
            from src.api.comix import ComixAPI
            from src.core.downloader import MangaDownloader, ChapterDownloader
            from src.core.models import MangaInfo, Chapter
            
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
            
            # Convert chapter dicts to Chapter objects
            chapter_objects = []
            for ch in self.chapters:
                chapter_objects.append(Chapter(
                    chapter_id=ch["chapter_id"],
                    number=ch["number"],
                    title=ch.get("title"),
                    group_name=ch.get("group_name"),
                    pages_count=ch.get("pages_count", 0)
                ))
            
            # Create downloader with custom progress callback
            downloader = MangaDownloader(self.config)
            
            successful = 0
            failed = 0
            total = len(chapter_objects)
            
            for idx, chapter in enumerate(chapter_objects):
                try:
                    # Get image URLs
                    image_urls = ComixAPI.get_chapter_images(chapter.chapter_id)
                    
                    # Emit progress as we download
                    chapter_name = chapter.get_display_name()
                    
                    # Download chapter (using the internal method)
                    from src.core.downloader import ChapterDownloader
                    ch_downloader = ChapterDownloader(self.config, manga)
                    success, message = ch_downloader.download_chapter(chapter)
                    
                    if success:
                        successful += 1
                        self.chapterComplete.emit(chapter_name, True, message)
                    else:
                        failed += 1
                        self.chapterComplete.emit(chapter_name, False, message)
                    
                    self.overallProgress.emit(idx + 1, total)
                    
                except Exception as e:
                    failed += 1
                    self.chapterComplete.emit(chapter.get_display_name(), False, str(e))
                    self.overallProgress.emit(idx + 1, total)
            
            self.finished.emit(successful, failed)
            
        except Exception as e:
            self.error.emit(str(e))


class DownloadBridge(QObject):
    """Bridge for download operations."""
    
    # Signals to QML
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
        Start downloading selected chapters.
        
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
        
        # Filter by scanlator if specified
        if scanlator and scanlator != "Any":
            filtered = []
            seen_numbers = set()
            for ch in chapters:
                if ch.get("group_name") == scanlator and ch["number"] not in seen_numbers:
                    filtered.append(ch)
                    seen_numbers.add(ch["number"])
            # Fallback for chapters without preferred scanlator
            for ch in chapters:
                if ch["number"] not in seen_numbers:
                    filtered.append(ch)
                    seen_numbers.add(ch["number"])
            chapters = filtered
        else:
            # Just get unique chapters by number
            seen = set()
            unique = []
            for ch in chapters:
                if ch["number"] not in seen:
                    unique.append(ch)
                    seen.add(ch["number"])
            chapters = unique
        
        self.downloadStarted.emit()
        
        # Create and start worker
        self._worker = DownloadWorker(manga, chapters, config)
        self._worker.chapterProgress.connect(self.chapterProgress.emit)
        self._worker.chapterComplete.connect(self.chapterComplete.emit)
        self._worker.overallProgress.connect(self.overallProgress.emit)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self.errorOccurred.emit)
        self._worker.start()
    
    def _on_finished(self, successful: int, failed: int):
        self.downloadFinished.emit(successful, failed)
    
    @pyqtSlot()
    def cancelDownload(self):
        """Cancel current download."""
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
