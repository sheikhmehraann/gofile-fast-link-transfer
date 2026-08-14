"""Ultra-fast 32-thread parallel HTTP downloader with aria2c native acceleration."""

import os
import time
import shutil
import subprocess
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from .resolvers import ResolvedURL


class ParallelDownloader:
    """32-Thread parallel downloader with native aria2c acceleration and Python multi-threaded fallback."""

    def __init__(self, num_connections: int = 32, chunk_size: int = 1024 * 1024, max_retries: int = 3):
        self.num_connections = num_connections
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.has_aria2 = shutil.which("aria2c") is not None

    def download(
        self,
        resolved: ResolvedURL,
        output_dir: str = ".",
        custom_filename: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """Download resolved URL to local disk using 32 parallel streams."""
        filename = custom_filename or resolved.filename or "downloaded_file.bin"
        output_path = os.path.abspath(os.path.join(output_dir, filename))
        os.makedirs(output_dir, exist_ok=True)

        # 1. Try aria2c if available (32 connections C++ epoll engine)
        if self.has_aria2 and not resolved.cookies:
            try:
                success = self._download_aria2(resolved.direct_url, output_dir, filename)
                if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path
            except Exception:
                pass

        # 2. Multi-threaded range request engine (Python 32 parallel threads)
        file_size = resolved.file_size
        supports_ranges = resolved.supports_ranges and file_size and file_size > (1 * 1024 * 1024)

        if supports_ranges and self.num_connections > 1:
            self._download_parallel(resolved, output_path, file_size, progress_callback)
        else:
            self._download_single(resolved, output_path, progress_callback)

        return output_path

    def _download_aria2(self, direct_url: str, output_dir: str, filename: str) -> bool:
        """Download via native aria2c with 32 connections."""
        cmd = [
            "aria2c",
            f"--max-connection-per-server={self.num_connections}",
            f"--split={self.num_connections}",
            "--min-split-size=1M",
            "--file-allocation=none",
            "--summary-interval=1",
            "--console-log-level=warn",
            "--dir", output_dir,
            "--out", filename,
            direct_url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0

    def _download_single(self, resolved: ResolvedURL, output_path: str, progress_callback: Optional[Callable[[int, int], None]] = None):
        """Single-stream download with 1MB buffer."""
        headers = resolved.headers.copy()
        headers["User-Agent"] = "Wget/1.21.3"

        with httpx.Client(follow_redirects=True, timeout=60.0, cookies=resolved.cookies) as client:
            with client.stream("GET", resolved.direct_url, headers=headers) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("Content-Length", 0)) or resolved.file_size or 0

                with open(output_path, "wb") as f, Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                ) as progress:
                    task = progress.add_task(f"Downloading {os.path.basename(output_path)}", total=total_size)
                    downloaded = 0
                    for chunk in response.iter_bytes(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress.update(task, completed=downloaded)
                            if progress_callback:
                                progress_callback(downloaded, total_size)

    def _download_parallel(self, resolved: ResolvedURL, output_path: str, file_size: int, progress_callback: Optional[Callable[[int, int], None]] = None):
        """Multi-threaded range request download with 32 parallel workers."""
        workers = min(self.num_connections, max(1, file_size // (512 * 1024)))
        part_size = file_size // workers
        ranges = []
        for i in range(workers):
            start = i * part_size
            end = file_size - 1 if i == workers - 1 else (start + part_size - 1)
            ranges.append((start, end, i))

        with open(output_path, "wb") as f:
            f.truncate(file_size)

        downloaded_bytes = 0

        with Progress(
            TextColumn("[bold green]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task(f"⚡ 32x Parallel Download {os.path.basename(output_path)}", total=file_size)

            def _download_chunk(start: int, end: int, part_id: int):
                nonlocal downloaded_bytes
                range_headers = resolved.headers.copy()
                range_headers["Range"] = f"bytes={start}-{end}"
                range_headers["User-Agent"] = "Wget/1.21.3"

                for attempt in range(self.max_retries):
                    try:
                        with httpx.Client(follow_redirects=True, timeout=60.0, cookies=resolved.cookies) as client:
                            with client.stream("GET", resolved.direct_url, headers=range_headers) as response:
                                response.raise_for_status()
                                current_pos = start
                                with open(output_path, "rb+") as f:
                                    f.seek(start)
                                    for chunk in response.iter_bytes(chunk_size=self.chunk_size):
                                        if chunk:
                                            f.write(chunk)
                                            chunk_len = len(chunk)
                                            current_pos += chunk_len
                                            downloaded_bytes += chunk_len
                                            progress.update(task, completed=downloaded_bytes)
                                            if progress_callback:
                                                progress_callback(downloaded_bytes, file_size)
                        return
                    except Exception as e:
                        if attempt == self.max_retries - 1:
                            raise RuntimeError(f"Chunk {part_id} failed after {self.max_retries} retries: {e}")
                        time.sleep(0.3)

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(_download_chunk, start, end, part_id) for start, end, part_id in ranges]
                for future in as_completed(futures):
                    future.result()
