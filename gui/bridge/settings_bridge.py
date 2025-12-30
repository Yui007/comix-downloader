"""
Settings Bridge - Exposes configuration to QML
"""

import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import ConfigManager


class SettingsBridge(QObject):
    """Bridge for settings/configuration."""
    
    # Signals
    settingsChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._config_manager = ConfigManager()
    
    # Output Format
    @pyqtProperty(str, notify=settingsChanged)
    def outputFormat(self):
        return self._config_manager.get("output_format", "images")
    
    @outputFormat.setter
    def outputFormat(self, value: str):
        self._config_manager.set("output_format", value)
        self.settingsChanged.emit()
    
    # Keep Images
    @pyqtProperty(bool, notify=settingsChanged)
    def keepImages(self):
        return self._config_manager.get("keep_images", False)
    
    @keepImages.setter
    def keepImages(self, value: bool):
        self._config_manager.set("keep_images", value)
        self.settingsChanged.emit()
    
    # Download Path
    @pyqtProperty(str, notify=settingsChanged)
    def downloadPath(self):
        return self._config_manager.get("download_path", "downloads")
    
    @downloadPath.setter
    def downloadPath(self, value: str):
        self._config_manager.set("download_path", value)
        self.settingsChanged.emit()
    
    # Max Chapter Workers
    @pyqtProperty(int, notify=settingsChanged)
    def maxChapterWorkers(self):
        return self._config_manager.get("max_chapter_workers", 3)
    
    @maxChapterWorkers.setter
    def maxChapterWorkers(self, value: int):
        self._config_manager.set("max_chapter_workers", max(1, min(10, value)))
        self.settingsChanged.emit()
    
    # Max Image Workers
    @pyqtProperty(int, notify=settingsChanged)
    def maxImageWorkers(self):
        return self._config_manager.get("max_image_workers", 5)
    
    @maxImageWorkers.setter
    def maxImageWorkers(self, value: int):
        self._config_manager.set("max_image_workers", max(1, min(20, value)))
        self.settingsChanged.emit()
    
    # Slots for QML
    @pyqtSlot(str, 'QVariant')
    def setValue(self, key: str, value):
        """Generic setter for any config value."""
        self._config_manager.set(key, value)
        self.settingsChanged.emit()
    
    @pyqtSlot(str, result='QVariant')
    def getValue(self, key: str):
        """Generic getter for any config value."""
        return self._config_manager.get(key)
    
    @pyqtSlot()
    def resetToDefaults(self):
        """Reset all settings to defaults."""
        self._config_manager.reset_to_defaults()
        self.settingsChanged.emit()
    
    @pyqtSlot(result=str)
    def getDownloadPathAbsolute(self):
        """Get absolute path to downloads folder."""
        path = Path(self._config_manager.get("download_path", "downloads"))
        return str(path.absolute())
