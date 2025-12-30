"""
Bridge module for Python↔QML communication
"""
from .manga_bridge import MangaBridge
from .download_bridge import DownloadBridge
from .settings_bridge import SettingsBridge

__all__ = ["MangaBridge", "DownloadBridge", "SettingsBridge"]
