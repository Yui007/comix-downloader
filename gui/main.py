"""
Comix Downloader GUI - Main Entry Point
PyQt6 + QML Application
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QFontDatabase

from gui.bridge import MangaBridge, DownloadBridge, SettingsBridge


def load_fonts():
    """Load custom fonts."""
    fonts_dir = Path(__file__).parent / "resources" / "fonts"
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))


def main():
    """Main entry point for the GUI application."""
    # Enable high DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("Comix Downloader")
    app.setOrganizationName("ComixDownloader")
    
    # Load fonts
    load_fonts()
    
    # Create QML engine
    engine = QQmlApplicationEngine()
    
    # Create bridge instances
    manga_bridge = MangaBridge()
    download_bridge = DownloadBridge()
    settings_bridge = SettingsBridge()
    
    # Expose bridges to QML
    engine.rootContext().setContextProperty("MangaBridge", manga_bridge)
    engine.rootContext().setContextProperty("DownloadBridge", download_bridge)
    engine.rootContext().setContextProperty("SettingsBridge", settings_bridge)
    
    # Add QML import path
    qml_dir = Path(__file__).parent / "qml"
    engine.addImportPath(str(qml_dir))
    
    # Load main QML file
    qml_file = qml_dir / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    
    # Check if QML loaded successfully
    if not engine.rootObjects():
        print("Error: Failed to load QML")
        sys.exit(-1)
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
