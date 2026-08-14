#!/usr/bin/env python3
"""Zero-dependency local Web Dashboard for GoFile Fast Link Transfer.

Usage:
  python web_app.py
  Open http://localhost:5000 in your browser.
"""

import sys
import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Ensure src in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gofile_transfer.pipeline import TransferPipeline

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GoFile Fast Link Transfer</title>
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --border: #334155;
      --success: #10b981;
      --error: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
    .container { width: 100%; max-width: 640px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 32px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); }
    .header { text-align: center; margin-bottom: 24px; }
    .header h1 { font-size: 26px; font-weight: 700; margin-bottom: 8px; background: linear-gradient(135deg, #60a5fa, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .header p { color: var(--text-muted); font-size: 14px; }
    .input-group { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }
    input[type="text"] { width: 100%; padding: 14px 16px; background: #0f172a; border: 1px solid var(--border); border-radius: 10px; color: #fff; font-size: 15px; outline: none; transition: border-color 0.2s; }
    input[type="text"]:focus { border-color: var(--primary); }
    .btn { background: var(--primary); color: white; border: none; border-radius: 10px; padding: 14px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background 0.2s; display: flex; justify-content: center; align-items: center; gap: 8px; }
    .btn:hover { background: var(--primary-hover); }
    .btn:disabled { opacity: 0.6; cursor: not-allowed; }
    .status-card { display: none; margin-top: 24px; padding: 20px; background: #0f172a; border: 1px solid var(--border); border-radius: 12px; }
    .spinner { display: inline-block; width: 18px; height: 18px; border: 3px solid rgba(255,255,255,.3); border-radius: 50%; border-top-color: #fff; animation: spin 1s ease-in-out infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .result-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
    .result-label { color: var(--text-muted); }
    .result-val { font-weight: 600; }
    .gofile-link-box { margin-top: 16px; padding: 12px; background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); border-radius: 8px; text-align: center; }
    .gofile-link-box a { color: var(--success); text-decoration: none; font-size: 16px; font-weight: 700; word-break: break-all; }
    .badge-list { display: flex; gap: 8px; justify-content: center; margin-top: 16px; flex-wrap: wrap; }
    .badge { font-size: 12px; background: #334155; padding: 4px 10px; border-radius: 20px; color: var(--text-muted); }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>⚡ GoFile Fast Link Transfer</h1>
      <p>Download from any host & stream straight to GoFile</p>
      <div class="badge-list">
        <span class="badge">Google Drive</span>
        <span class="badge">SourceForge</span>
        <span class="badge">MediaFire</span>
        <span class="badge">Dropbox</span>
        <span class="badge">Direct URLs</span>
      </div>
    </div>

    <form id="transferForm" onsubmit="startTransfer(event)">
      <div class="input-group">
        <input type="text" id="urlInput" placeholder="Paste downloadable link here..." required />
        <button type="submit" id="submitBtn" class="btn">Start Transfer</button>
      </div>
    </form>

    <div id="statusCard" class="status-card">
      <div id="loadingState" style="text-align: center; padding: 12px;">
        <div class="spinner" style="margin-bottom: 12px;"></div>
        <p id="statusMsg" style="color: var(--text-muted); font-size: 14px;">Resolving, downloading, and uploading...</p>
      </div>
      <div id="resultState" style="display: none;">
        <div class="result-row"><span class="result-label">File Name:</span><span id="resFilename" class="result-val"></span></div>
        <div class="result-row"><span class="result-label">File Size:</span><span id="resSize" class="result-val"></span></div>
        <div class="result-row"><span class="result-label">Download Speed:</span><span id="resDlSpeed" class="result-val"></span></div>
        <div class="result-row"><span class="result-label">Upload Speed:</span><span id="resUlSpeed" class="result-val"></span></div>
        <div class="result-row"><span class="result-label">Total Time:</span><span id="resTime" class="result-val"></span></div>
        <div class="gofile-link-box">
          <a id="resLink" href="#" target="_blank"></a>
        </div>
      </div>
    </div>
  </div>

  <script>
    async function startTransfer(e) {
      e.preventDefault();
      const url = document.getElementById('urlInput').value.trim();
      if (!url) return;

      const btn = document.getElementById('submitBtn');
      const statusCard = document.getElementById('statusCard');
      const loadingState = document.getElementById('loadingState');
      const resultState = document.getElementById('resultState');

      btn.disabled = true;
      statusCard.style.display = 'block';
      loadingState.style.display = 'block';
      resultState.style.display = 'none';

      try {
        const response = await fetch('/api/transfer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url })
        });

        const data = await response.json();
        if (data.status === 'success') {
          loadingState.style.display = 'none';
          resultState.style.display = 'block';

          document.getElementById('resFilename').innerText = data.filename;
          document.getElementById('resSize').innerText = (data.file_size / (1024 * 1024)).toFixed(2) + ' MB';
          document.getElementById('resDlSpeed').innerText = data.download_speed_mbps.toFixed(2) + ' MB/s (' + data.download_time_s.toFixed(2) + 's)';
          document.getElementById('resUlSpeed').innerText = data.upload_speed_mbps.toFixed(2) + ' MB/s (' + data.upload_time_s.toFixed(2) + 's)';
          document.getElementById('resTime').innerText = data.total_time_s.toFixed(2) + 's';
          
          const linkElem = document.getElementById('resLink');
          linkElem.href = data.gofile_url;
          linkElem.innerText = '👉 ' + data.gofile_url;
        } else {
          alert('Transfer Failed: ' + (data.error || 'Unknown error'));
          statusCard.style.display = 'none';
        }
      } catch (err) {
        alert('Request error: ' + err.message);
        statusCard.style.display = 'none';
      } finally {
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>
"""


class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/transfer":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                data = json.loads(body)
                url = data.get("url", "").strip()

                if not url:
                    raise ValueError("URL cannot be empty.")

                pipeline = TransferPipeline(connections=16)
                summary = pipeline.process_url(url)

                res_payload = {
                    "status": "success",
                    "url": summary.original_url,
                    "filename": summary.filename,
                    "file_size": summary.file_size,
                    "gofile_url": summary.gofile_url,
                    "gofile_code": summary.gofile_code,
                    "download_time_s": summary.download_time,
                    "upload_time_s": summary.upload_time,
                    "total_time_s": summary.total_time,
                    "download_speed_mbps": summary.download_speed_mbps,
                    "upload_speed_mbps": summary.upload_speed_mbps,
                }
            except Exception as e:
                res_payload = {"status": "error", "error": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res_payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def start_server(port: int = 5000):
    server = HTTPServer(("127.0.0.1", port), WebHandler)
    print(f"🚀 Web Dashboard running at: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    start_server(port)
