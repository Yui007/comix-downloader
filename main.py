"""
Comix Downloader - Beautiful Interactive CLI
A modern manga downloader for comix.to with threading support.
"""

import sys
from pathlib import Path

# Add src to path for proper imports
sys.path.insert(0, str(Path(__file__).parent))

from src.cli.app import main, app

if __name__ == "__main__":
    # Check if any command line arguments were provided
    if len(sys.argv) > 1:
        # Use Typer for command-line mode
        app()
    else:
        # Interactive mode
        main()
