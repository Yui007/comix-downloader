"""
Comix Downloader GUI - Main Entry Point
PyQt6 + QML Application
"""

import sys
import os
import argparse
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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Comix Downloader GUI")
    parser.add_argument(
        "--cpu", 
        action="store_true",
        help="Use software (CPU) rendering instead of GPU"
    )
    return parser.parse_args()


def main():
    """Main entry point for the GUI application."""
    args = parse_args()
    
    # Suppress Qt/QML warnings (they are harmless but noisy)
    os.environ["QT_LOGGING_RULES"] = "*=false"  # Suppress all Qt debug/warning messages
    
    # Set rendering backend (must be set BEFORE QApplication)
    if args.cpu:
        # Full software rendering - works on all systems
        os.environ["QT_QUICK_BACKEND"] = "software"
        os.environ["QT_OPENGL"] = "software"
        os.environ["QSG_RENDER_LOOP"] = "basic"
        print("Using software (CPU) rendering")
    
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

