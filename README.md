# 🚀 GoFile Fast Link Transfer

<div align="center">

![GoFile Fast Transfer](https://img.shields.io/badge/Speed-Parallel_16x-brightgreen.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/downloads/)
[![GoFile API](https://img.shields.io/badge/GoFile-API_v3-green.svg)](https://gofile.io/api)
[![Tests: Passing](https://img.shields.io/badge/tests-7%20passed-success.svg)]()

**The fastest, single-job engine to download any file from any hosting platform and upload directly to GoFile.**

[Quick Start](#-quick-start) •
[Features](#-key-features) •
[Web Dashboard](#-web-dashboard) •
[Architecture](#-architecture) •
[Supported Hosts](#-supported-hosts) •
[CLI Reference](#-cli-reference)

</div>

---

## ⚡ Quick Start

### 1. Installation
```bash
git clone https://github.com/sheikhmehraann/gofile-fast-link-transfer.git
cd gofile-fast-link-transfer
pip install -r requirements.txt
```

### 2. Single-Job Execution (Ek Hi Job)
```bash
# Direct link transfer
python main.py "https://example.com/any-file.zip"

# Or simply run and paste link interactively:
python main.py

# Windows Double-Click Launcher:
run.bat
```

### 3. Web Dashboard (Browser Interface)
```bash
python web_app.py
# Open http://localhost:5000 in your browser!
```

---

## ✨ Key Features

- 🏎️ **Ultra-Fast Parallel Engine**: Splits downloads into 16 concurrent range streams, saturating your full connection bandwidth.
- 🛡️ **Zero Errors & Deep Resilience**: Automatic chunk-level retries, exponential backoff, and multi-server GoFile fallback.
- 🔗 **Smart Link Resolvers**:
  - **Google Drive**: Bypasses the 10+ GB virus scan confirmation interstitials, dynamic UUIDs, and cookies automatically.
  - **SourceForge**: Direct mirror selection and 302 redirect resolution.
  - **MediaFire**: Scrapes and extracts direct CDN download URLs.
  - **Dropbox & GitHub**: Auto-converts share links to direct raw streams.
  - **Direct HTTP/HTTPS**: Direct probe for content disposition and range support.
- 🌐 **Modern Web UI Dashboard**: Zero-dependency browser interface with instant copyable GoFile links.
- 📊 **Rich Terminal Interface**: Live download/upload progress bars, instant MB/s calculation, and structured JSON output.

---

## 📋 Supported Hosts

| Service | Supported URL Types | Auto-Bypass |
| :--- | :--- | :---: |
| **Google Drive** | `/file/d/...`, `/uc?id=...`, `/open?id=...` | ✅ (Large files & UUID tokens) |
| **SourceForge** | `sourceforge.net/projects/.../download` | ✅ (Mirror selection) |
| **MediaFire** | `mediafire.com/file/...` | ✅ (Direct link extraction) |
| **Dropbox** | `dropbox.com/s/...` | ✅ (`dl=1` conversion) |
| **GitHub Releases** | `/releases/download/...`, `/raw/...` | ✅ (Direct stream) |
| **Direct URLs** | Any HTTP/HTTPS binary endpoint | ✅ (Parallel range request) |

---

## 🏗️ Architecture

```mermaid
graph TD
    A[Input URL] --> B{Resolver Factory}
    B -->|Google Drive| C[GDrive Resolver]
    B -->|SourceForge| D[SourceForge Resolver]
    B -->|MediaFire| E[MediaFire Resolver]
    B -->|Direct / Dropbox| F[Direct Resolver]
    
    C & D & E & F --> G[Resolved Direct Stream]
    
    G --> H[Parallel Range Downloader]
    H -->|16 Threads| I[High-Speed Local Buffer]
    
    I --> J[GoFile Multi-Server Pool]
    J -->|Server 1| K[GoFile API v3]
    J -->|Fallback 2/3| K
    
    K --> L[🎉 Shareable GoFile Link]
```

---

## 🖥️ CLI Reference

```bash
# Run with custom thread count (e.g. 16 threads)
python cli.py -c 16 "https://drive.google.com/file/d/..."

# Process a list of URLs in batch
python cli.py -b links.txt

# Output structured JSON for automation scripts
python cli.py --json-output "https://example.com/archive.tar.gz"

# Keep downloaded files locally on disk after upload
python cli.py -k "https://example.com/file.zip"
```

---

## 💻 Python Library Usage

```python
from src.gofile_transfer import TransferPipeline

pipeline = TransferPipeline(connections=16)
summary = pipeline.process_url("https://drive.google.com/file/d/YOUR_FILE_ID/view")

print(f"GoFile URL: {summary.gofile_url}")
print(f"Download Speed: {summary.download_speed_mbps:.2f} MB/s")
print(f"Upload Speed: {summary.upload_speed_mbps:.2f} MB/s")
```

---

## 🧪 Running Tests

```bash
python -m pytest
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
