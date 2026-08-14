#!/usr/bin/env python3
"""Zero-dependency modern glassmorphic Web App for GoFile Fast Link Transfer."""

import http.server
import socketserver
import json
import urllib.parse
import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gofile_transfer.pipeline import TransferPipeline

PORT = 5000

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GoFile Fast Link Transfer - Turbo Edition</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(18, 26, 43, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #38bdf8;
      --primary-glow: rgba(56, 189, 248, 0.25);
      --accent: #10b981;
      --accent-glow: rgba(16, 185, 129, 0.25);
      --text: #f1f5f9;
      --text-muted: #94a3b8;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Plus Jakarta Sans', sans-serif;
    }

    body {
      background: radial-gradient(circle at 50% 0%, #172554 0%, var(--bg) 60%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }

    .container {
      width: 100%;
      max-width: 680px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-radius: 24px;
      padding: 40px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
      position: relative;
      overflow: hidden;
    }

    .container::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--primary), #818cf8, var(--accent));
    }

    .header {
      text-align: center;
      margin-bottom: 32px;
    }

    .logo-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.25);
      color: var(--primary);
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 16px;
    }

    h1 {
      font-size: 2.2rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      background: linear-gradient(135deg, #ffffff 40%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }

    p.subtitle {
      color: var(--text-muted);
      font-size: 0.95rem;
    }

    .hosts-grid {
      display: flex;
      justify-content: center;
      gap: 12px;
      margin-top: 16px;
      flex-wrap: wrap;
    }

    .host-pill {
      font-size: 0.75rem;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 4px 10px;
      border-radius: 8px;
      color: var(--text-muted);
    }

    .input-group {
      margin-top: 28px;
    }

    .input-wrapper {
      position: relative;
      margin-bottom: 16px;
    }

    input[type="text"] {
      width: 100%;
      background: rgba(10, 15, 29, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 16px 20px;
      border-radius: 14px;
      color: #fff;
      font-size: 1rem;
      font-family: 'JetBrains Mono', monospace;
      outline: none;
      transition: all 0.2s ease;
    }

    input[type="text"]:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--primary-glow);
    }

    button.btn-transfer {
      width: 100%;
      background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
      color: #fff;
      border: none;
      padding: 16px;
      border-radius: 14px;
      font-size: 1.05rem;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.4);
      transition: all 0.2s ease;
    }

    button.btn-transfer:hover {
      transform: translateY(-2px);
      box-shadow: 0 15px 30px -5px rgba(37, 99, 235, 0.6);
    }

    button.btn-transfer:active {
      transform: translateY(0);
    }

    button.btn-transfer:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }

    .status-card {
      margin-top: 24px;
      padding: 20px;
      border-radius: 14px;
      background: rgba(10, 15, 29, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.08);
      display: none;
    }

    .progress-bar-container {
      width: 100%;
      height: 8px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 999px;
      overflow: hidden;
      margin: 14px 0;
    }

    .progress-bar-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, var(--primary), var(--accent));
      transition: width 0.3s ease;
      animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
      0% { opacity: 0.8; }
      50% { opacity: 1; }
      100% { opacity: 0.8; }
    }

    .result-box {
      margin-top: 16px;
      padding: 16px;
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.3);
      border-radius: 12px;
      display: none;
    }

    .result-link {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 8px;
    }

    .result-link a {
      color: #34d399;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      text-decoration: none;
      word-break: break-all;
    }

    .btn-copy {
      background: #059669;
      color: white;
      border: none;
      padding: 8px 14px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 0.85rem;
      cursor: pointer;
      white-space: nowrap;
    }
  </style>
</head>
<body>

  <div class="container">
    <div class="header">
      <div class="logo-badge">⚡ 32-Stream Turbo Engine</div>
      <h1>GoFile Fast Transfer</h1>
      <p class="subtitle">Transfer any downloadable link directly to GoFile in seconds</p>
      
      <div class="hosts-grid">
        <span class="host-pill">Google Drive</span>
        <span class="host-pill">SourceForge</span>
        <span class="host-pill">MediaFire</span>
        <span class="host-pill">Dropbox</span>
        <span class="host-pill">Direct CDN</span>
      </div>
    </div>

    <div class="input-group">
      <div class="input-wrapper">
        <input type="text" id="urlInput" placeholder="Paste downloadable link here..." autocomplete="off">
      </div>
      <button class="btn-transfer" id="transferBtn" onclick="startTransfer()">
        <span>🚀 Start Turbo Transfer</span>
      </button>
    </div>

    <div class="status-card" id="statusCard">
      <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
        <span id="statusLabel" style="color: var(--primary); font-weight: 600;">Connecting...</span>
        <span id="speedLabel" style="color: var(--text-muted); font-family: 'JetBrains Mono';">32x Streams</span>
      </div>
      <div class="progress-bar-container">
        <div class="progress-bar-fill" id="progressBar"></div>
      </div>
      <div id="fileMeta" style="font-size: 0.85rem; color: var(--text-muted);"></div>
    </div>

    <div class="result-box" id="resultBox">
      <div style="font-size: 0.9rem; font-weight: 700; color: #10b981;">🎉 Transfer Successful!</div>
      <div class="result-link">
        <a href="#" id="gofileLink" target="_blank">https://gofile.io/d/...</a>
        <button class="btn-copy" onclick="copyLink()">📋 Copy</button>
      </div>
    </div>
  </div>

  <script>
    async function startTransfer() {
      const urlInput = document.getElementById('urlInput');
      const url = urlInput.value.trim();
      if (!url) return alert('Please enter a valid link!');

      const btn = document.getElementById('transferBtn');
      const statusCard = document.getElementById('statusCard');
      const statusLabel = document.getElementById('statusLabel');
      const progressBar = document.getElementById('progressBar');
      const fileMeta = document.getElementById('fileMeta');
      const resultBox = document.getElementById('resultBox');

      btn.disabled = true;
      statusCard.style.display = 'block';
      resultBox.style.display = 'none';
      progressBar.style.width = '20%';
      statusLabel.innerText = '⚡ Resolving link & selecting fastest server...';

      try {
        const res = await fetch('/api/transfer', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ url: url })
        });

        progressBar.style.width = '70%';
        statusLabel.innerText = '🚀 32-Stream Downloading & Uploading...';

        const data = await res.json();
        if (data.status === 'ok') {
          progressBar.style.width = '100%';
          statusLabel.innerText = '✅ Transfer Complete!';
          fileMeta.innerText = `${data.filename} (${(data.size / (1024*1024)).toFixed(2)} MB) • Total: ${data.duration.toFixed(2)}s`;
          
          document.getElementById('gofileLink').href = data.gofile_url;
          document.getElementById('gofileLink').innerText = data.gofile_url;
          resultBox.style.display = 'block';
        } else {
          alert('Transfer Failed: ' + data.error);
          statusCard.style.display = 'none';
        }
      } catch (err) {
        alert('Network or Server Error: ' + err);
        statusCard.style.display = 'none';
      } finally {
        btn.disabled = false;
      }
    }

    function copyLink() {
      const link = document.getElementById('gofileLink').href;
      navigator.clipboard.writeText(link);
      alert('Copied to clipboard: ' + link);
    }
  </script>
</body>
</html>
"""


class WebHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/transfer":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            url = data.get("url")

            pipeline = TransferPipeline(connections=32)
            try:
                summary = pipeline.process_url(url)
                response = {
                    "status": "ok",
                    "gofile_url": summary.gofile_url,
                    "filename": summary.filename,
                    "size": summary.file_size,
                    "duration": summary.total_time,
                    "speed": summary.upload_speed_mbps
                }
            except Exception as e:
                response = {"status": "error", "error": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))


def run_web_server():
    server = socketserver.TCPServer(("", PORT), WebHandler)
    print(f"🚀 Web Dashboard running live on: http://localhost:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run_web_server()
