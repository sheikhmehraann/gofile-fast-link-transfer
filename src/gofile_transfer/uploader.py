"""GoFile API client and high-speed uploader module."""

import os
import requests
from dataclasses import dataclass
from typing import Optional, Callable
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn


@dataclass
class GoFileResult:
    """Dataclass holding GoFile upload response data."""
    download_page: str
    code: str
    file_id: str
    file_name: str
    parent_folder: Optional[str] = None
    md5: Optional[str] = None


class GoFileUploader:
    """GoFile.io client for fetching servers and uploading files."""

    API_SERVERS_URL = "https://api.gofile.io/servers"

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    def get_best_server(self) -> str:
        """Fetch best available upload server from GoFile API."""
        try:
            res = self.session.get(self.API_SERVERS_URL, timeout=10)
            res.raise_for_status()
            data = res.json()
            if data.get("status") == "ok" and "servers" in data.get("data", {}):
                servers = data["data"]["servers"]
                if servers:
                    return servers[0]["name"]
        except Exception as e:
            # Fallback to default server if API query fails
            pass
        return "store1"

    def upload(
        self,
        file_path: str,
        folder_id: Optional[str] = None,
        custom_filename: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> GoFileResult:
        """Upload a local file to GoFile with real-time streaming and progress tracking."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        server = self.get_best_server()
        upload_url = f"https://{server}.gofile.io/contents/uploadfile"

        file_size = os.path.getsize(file_path)
        filename = custom_filename or os.path.basename(file_path)

        with open(file_path, "rb") as f:
            fields = {"file": (filename, f, "application/octet-stream")}
            if folder_id:
                fields["folderId"] = folder_id
            if self.token:
                fields["token"] = self.token

            encoder = MultipartEncoder(fields=fields)

            with Progress(
                TextColumn("[bold yellow]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(f"Uploading to GoFile ({server}) {filename}", total=file_size)

                def _monitor_callback(monitor):
                    progress.update(task, completed=monitor.bytes_read)
                    if progress_callback:
                        progress_callback(monitor.bytes_read, file_size)

                monitor = MultipartEncoderMonitor(encoder, _monitor_callback)
                headers = {"Content-Type": monitor.content_type}

                res = self.session.post(upload_url, data=monitor, headers=headers, timeout=300)
                res.raise_for_status()
                response_data = res.json()

                if response_data.get("status") != "ok":
                    raise RuntimeError(f"GoFile upload failed: {response_data}")

                data = response_data["data"]
                return GoFileResult(
                    download_page=data.get("downloadPage", f"https://gofile.io/d/{data.get('code', '')}"),
                    code=data.get("code", ""),
                    file_id=data.get("fileId", ""),
                    file_name=data.get("fileName", filename),
                    parent_folder=data.get("parentFolder"),
                    md5=data.get("md5")
                )
