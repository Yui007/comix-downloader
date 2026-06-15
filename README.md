<div align="center">

# 🎨 Comix Downloader

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue?style=for-the-badge)]()

**A beautiful manga downloader for [comix.to](https://comix.to) with GUI & CLI**

*Fast concurrent downloads • Multiple formats • Scanlator selection*

![GUI Screenshot](GUI.PNG)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🖥️ **Modern GUI** | Beautiful PyQt6/QML interface with dark theme |
| 🎨 **Beautiful CLI** | Rich terminal interface with progress bars |
| ⚡ **Concurrent Downloads** | Multi-threaded chapter and image downloads |
| 📁 **Multiple Formats** | Export as **Images**, **PDF**, or **CBZ** |
| 🎯 **Smart Selection** | Download single, range (`1-10`), or all chapters |
| 🎨 **Scanlator Filter** | Filter and prefer specific scanlator groups |
| ⚙️ **Persistent Settings** | All preferences saved to `config.json` |

---

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Yui007/comix-downloader.git
cd comix-downloader

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser dependencies
playwright install chromium
```

---

## 📖 Usage

### GUI Mode (Recommended)

```bash
# Run with GPU rendering (default)
python gui/main.py

# Run with CPU/Software rendering (for compatibility)
python gui/main.py --cpu
```

1. Paste a manga URL from comix.to
2. Click **FETCH** to load manga info and chapters
3. Select chapters and choose scanlator preference/filter
4. Click **DOWNLOAD CHAPTERS**
5. Access **⚙️ Settings** to configure format, output path, workers

### CLI Mode

```bash
# Interactive mode
python main.py

# Direct download
python main.py download "https://comix.to/title/abc-manga-name" -c "1-10" -f cbz
```

---

## ⚙️ Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Output Format | images / pdf / cbz | `images` |
| Keep Images | Retain images after PDF/CBZ conversion | `No` |
| Enable Logs | Show debug logging | `No` |
| Download Path | Where to save downloads | `downloads` |
| Max Chapter Workers | Concurrent chapter downloads | `3` |
| Max Image Workers | Concurrent image downloads per chapter | `5` |

---

## 📁 Project Structure

```
comix-downloader/
├── main.py                 # CLI entry point
├── gui/
│   ├── main.py             # GUI entry point
│   ├── bridge/             # Python-QML bridges
│   └── qml/                # QML UI components
├── src/
│   ├── api/comix.py        # API wrapper
│   ├── core/               # Models & downloader
│   ├── formats/            # PDF, CBZ, Images
│   └── cli/                # CLI application
└── config.json             # User settings
```

---

## 🔧 Dependencies

**GUI:**
- **[PyQt6](https://pypi.org/project/PyQt6/)** - Qt6 bindings for Python

**CLI:**
- **[Typer](https://typer.tiangolo.com/)** - CLI framework
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal output

**Shared:**
- **[Playwright](https://playwright.dev/python/)** - Browser automation and canvas image extraction
- **[Requests](https://requests.readthedocs.io/)** - HTTP library
- **[Pillow](https://pillow.readthedocs.io/)** - Image processing
- **[ReportLab](https://www.reportlab.com/)** - PDF generation

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This tool is for personal use only. Please respect the copyright of manga authors and publishers. Support official releases when available.

---

<div align="center">

**Made with ❤️ by [Yui007](https://github.com/Yui007)**

⭐ Star this repo if you find it useful!

</div>
