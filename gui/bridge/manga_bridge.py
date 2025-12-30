"""
Manga API Bridge - Exposes manga fetching to QML
"""

import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class FetchWorker(QThread):
    """Background worker for fetching manga data."""
    
    finished = pyqtSignal(dict)
    chaptersLoaded = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            # Import here to avoid circular imports
            from src.api.comix import ComixAPI
            
            # Extract manga code
            manga_code = ComixAPI.extract_manga_code(self.url)
            
            # Fetch manga info
            manga = ComixAPI.get_manga_info(manga_code)
            if not manga:
                self.error.emit("Could not fetch manga information")
                return
            
            # Convert to dict for QML
            manga_dict = {
                "manga_id": manga.manga_id,
                "hash_id": manga.hash_id,
                "title": manga.title,
                "alt_titles": manga.alt_titles,
                "manga_type": manga.manga_type or "Unknown",
                "status": manga.status or "Unknown",
                "poster_url": manga.poster_url or "",
                "year": manga.year or 0,
                "rated_avg": manga.rated_avg or 0,
                "follows_total": manga.follows_total or 0,
                "is_nsfw": manga.is_nsfw,
                "description": manga.description or "",
                "manga_code": manga_code
            }
            
            self.finished.emit(manga_dict)
            
            # Fetch chapters
            chapters = ComixAPI.get_all_chapters(manga_code)
            chapters_list = []
            for ch in chapters:
                chapters_list.append({
                    "chapter_id": ch.chapter_id,
                    "number": str(ch.number),
                    "title": ch.title or "",
                    "group_name": ch.group_name or "Unknown",
                    "pages_count": ch.pages_count,
                    "selected": False
                })
            
            self.chaptersLoaded.emit(chapters_list)
            
        except Exception as e:
            self.error.emit(str(e))


class MangaBridge(QObject):
    """Bridge between Python manga API and QML."""
    
    # Signals to QML
    mangaLoaded = pyqtSignal('QVariant')
    chaptersLoaded = pyqtSignal('QVariant')
    errorOccurred = pyqtSignal(str)
    loadingChanged = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._manga = None
        self._chapters = []
        self._manga_code = ""
    
    @pyqtSlot(str)
    def fetchManga(self, url: str):
        """Fetch manga info and chapters from URL."""
        if not url or "comix.to" not in url:
            self.errorOccurred.emit("Please enter a valid comix.to URL")
            return
        
        self.loadingChanged.emit(True)
        
        # Create and start worker thread
        self._worker = FetchWorker(url)
        self._worker.finished.connect(self._on_manga_loaded)
        self._worker.chaptersLoaded.connect(self._on_chapters_loaded)
        self._worker.error.connect(self._on_error)
        self._worker.start()
    
    def _on_manga_loaded(self, manga: dict):
        self._manga = manga
        self._manga_code = manga.get("manga_code", "")
        self.mangaLoaded.emit(manga)
    
    def _on_chapters_loaded(self, chapters: list):
        self._chapters = chapters
        self.chaptersLoaded.emit(chapters)
        self.loadingChanged.emit(False)
    
    def _on_error(self, error: str):
        self.loadingChanged.emit(False)
        self.errorOccurred.emit(error)
    
    @property
    def manga(self):
        return self._manga
    
    @property
    def chapters(self):
        return self._chapters
    
    @property
    def manga_code(self):
        return self._manga_code
