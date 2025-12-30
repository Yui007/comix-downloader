<div align="center">

# 🎨 Comix Downloader

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue?style=for-the-badge)]()

**A beautiful, interactive CLI manga downloader for [comix.to](https://comix.to)**

*Fast concurrent downloads • Multiple formats • Scanlator selection*

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎨 **Beautiful CLI** | Rich terminal interface with ASCII banner, styled tables, and progress bars |
| ⚡ **Concurrent Downloads** | Multi-threaded chapter and image downloads for blazing speed |
| 📁 **Multiple Formats** | Export as **Images**, **PDF**, or **CBZ** (with ComicInfo.xml metadata) |
| 🎯 **Smart Selection** | Download single, range (`1-10`), or all chapters |
| 🎨 **Scanlator Preference** | Choose your preferred scanlator group when duplicates exist |
| 🔄 **Retry Logic** | Automatic retries with exponential backoff (2s → 4s → 8s) |
| ⚙️ **Persistent Settings** | All preferences saved to `config.json` |
| 📝 **Optional Logging** | Debug logs disabled by default, toggle in settings |

---

## 📸 Screenshots

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║       ██████╗ ██████╗ ███╗   ███╗██╗██╗  ██╗                 ║
║      ██╔════╝██╔═══██╗████╗ ████║██║╚██╗██╔╝                 ║
║      ██║     ██║   ██║██╔████╔██║██║ ╚███╔╝                  ║
║      ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║██╔╝ ██╗                 ║
║       ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═╝                 ║
║                                                               ║
║             🎨 Beautiful Manga Downloader CLI                 ║
╚═══════════════════════════════════════════════════════════════╝

╭─────────────────────── Main Menu ───────────────────────╮
│   1 │ 📥 Download Manga by URL                          │
│   2 │ ⚙️  Settings                                       │
│   3 │ 🚪 Exit                                           │
╰─────────────────────────────────────────────────────────╯
```

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

# Run the application
python main.py
```

---

## 📖 Usage

### Interactive Mode (Recommended)

```bash
python main.py
```

1. Select **"Download Manga by URL"**
2. Paste a manga URL from comix.to
3. Choose chapters: `5` (single), `1-10` (range), or `all`
4. Select your preferred scanlator (if multiple available)
5. Watch the progress bars as chapters download!

### Command Line Mode

```bash
# Download specific chapters
python main.py download "https://comix.to/title/abc-manga-name" -c "1-10" -f cbz

# Options
  -c, --chapters    Chapter selection (e.g., "1-10", "all")
  -f, --format      Output format: images, pdf, cbz
  -o, --output      Output directory
```

---

## ⚙️ Settings

Access via **Main Menu → Settings** or directly:

```bash
python main.py settings
```

| Setting | Description | Default |
|---------|-------------|---------|
| Output Format | images / pdf / cbz | `images` |
| Keep Images | Retain images after PDF/CBZ conversion | `No` |
| Enable Logs | Show debug logging | `No` |
| Download Path | Where to save downloads | `downloads` |
| Max Chapter Workers | Concurrent chapter downloads | `3` |
| Max Image Workers | Concurrent image downloads per chapter | `5` |
| Chapters Display Limit | Chapters shown in table (0=all) | `20` |

Settings are saved to `config.json` and persist between sessions.

---

## 📁 Project Structure

```
comix-downloader/
├── main.py                 # Entry point
├── config.json             # User settings
├── requirements.txt        # Dependencies
└── src/
    ├── api/
    │   └── comix.py        # API wrapper for comix.to
    ├── core/
    │   ├── models.py       # Data classes
    │   └── downloader.py   # Threaded download engine
    ├── formats/
    │   ├── images.py       # Image saving
    │   ├── pdf.py          # PDF generation
    │   └── cbz.py          # CBZ with ComicInfo.xml
    ├── cli/
    │   ├── app.py          # Main CLI application
    │   ├── menus.py        # Interactive menus
    │   └── display.py      # Rich styling
    └── utils/
        ├── config.py       # Configuration manager
        ├── retry.py        # Retry with backoff
        └── logger.py       # Logging setup
```

---

## 🔧 Dependencies

- **[Typer](https://typer.tiangolo.com/)** - CLI framework
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal output
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
