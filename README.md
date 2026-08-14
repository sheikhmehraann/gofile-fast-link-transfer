# 🚀 GoFile Fast Link Transfer

> **Ultra-Fast Downloader & GoFile Uploader**
> Convert any downloadable link (Google Drive, SourceForge, Dropbox, Mediafire, or direct HTTP/HTTPS URLs) into an instant high-speed GoFile link.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GoFile API](https://img.shields.io/badge/GoFile-API_v3-green.svg)](https://gofile.io/api)

---

## ✨ Features

- ⚡ **Multi-Threaded Parallel Downloads**: Saturated download speeds using dynamic Range requests across 4 to 16 parallel connections.
- 🔗 **Smart Link Resolvers**:
  - **Google Drive**: Auto-resolves file IDs, virus scan warning interstitials (`confirm=...` token), and export links.
  - **SourceForge**: Auto-resolves project downloads, geographic mirrors, and 302 redirect chains.
  - **Dropbox & Mediafire**: Direct share-link parameter conversion.
  - **Direct HTTP/HTTPS**: Supports any arbitrary direct download link with filename probe.
- 📤 **High-Speed GoFile Uploader**:
  - Auto-selects healthiest server dynamically (`GET https://api.gofile.io/servers`).
  - Streaming `multipart/form-data` uploads (prevents memory spikes on large files).
  - Real-time progress bar displaying speed (MB/s), ETA, and uploaded size.
- 🛠️ **Rich CLI**: Single URL transfers, batch text file processing, and structured JSON output for script integration.

---

## 📦 Installation

```bash
git clone https://github.com/sheikhmehraann/gofile-fast-link-transfer.git
cd gofile-fast-link-transfer
pip install -r requirements.txt
```

---

## 🚀 Quick Usage

### 1. Basic Single Link Transfer
```bash
python cli.py "https://drive.google.com/file/d/YOUR_FILE_ID/view"
```

### 2. Custom Connection Count (e.g. 16 threads for max download speed)
```bash
python cli.py -c 16 "https://downloads.sourceforge.net/project/7-zip/7-Zip/23.01/7z2301-x64.exe"
```

### 3. Batch Transfer from Text File
```bash
python cli.py -b links.txt
```

### 4. Output Results in JSON (for scripts/automation)
```bash
python cli.py --json-output "https://example.com/largefile.zip"
```

---

## 🏗️ Project Architecture

```
gofile-fast-link-transfer/
├── cli.py                        # Rich Command-Line Interface
├── pyproject.toml                # Package configuration
├── requirements.txt              # Dependencies
├── src/
│   └── gofile_transfer/
│       ├── __init__.py           # Main package initialization
│       ├── downloader.py         # Multi-threaded parallel HTTP chunk downloader
│       ├── uploader.py           # GoFile API client & streaming uploader
│       ├── pipeline.py           # End-to-end processing pipeline
│       └── resolvers/
│           ├── base.py           # Abstract resolver interface & ResolvedURL model
│           ├── gdrive.py         # Google Drive resolver with token confirmation
│           ├── sourceforge.py    # SourceForge resolver with mirror auto-select
│           ├── direct.py         # Generic direct HTTP/HTTPS link resolver
│           └── factory.py        # Resolver registry & selector
└── tests/                        # Pytest suite
```

---

## ⚙️ Python API Usage

You can also import `gofile-fast-link-transfer` as a Python library:

```python
from src.gofile_transfer import TransferPipeline

pipeline = TransferPipeline(connections=8)
summary = pipeline.process_url("https://drive.google.com/file/d/YOUR_FILE_ID/view")

print(f"GoFile Link: {summary.gofile_url}")
print(f"Transfer Speed: {summary.upload_speed_mbps:.2f} MB/s")
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
