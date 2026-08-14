"""Ultra-fast parallel multi-threaded HTTP downloader with range requests and retry logic."""

import os
import time
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from .resolvers import ResolvedURL


class ParallelDownloader:
    """High-speed multi-threaded downloader with range support and resume capability."""

    def __init__(self, num_connections: int = 16, chunk_size: int = 256 * 1024, max_retries: int = 3):
        self.num_connections = num_connections
        self.chunk_size = chunk_size
        self.max_retries = max_retries

    def download(
        self,
        resolved: ResolvedURL,
        output_dir: str = ".",
        custom_filename: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """Download resolved URL to local disk."""
        filename = custom_filename or resolved.filename or "downloaded_file.bin"
        output_path = os.path.abspath(os.path.join(output_dir, filename))
        os.makedirs(output_dir, exist_ok=True)

        file_size = resolved.file_size
        supports_ranges = resolved.supports_ranges and file_size and file_size > (5 * 1024 * 1024)

        if supports_ranges and self.num_connections > 1:
            self._download_parallel(resolved, output_path, file_size, progress_callback)
        else:
            self._download_single(resolved, output_path, progress_callback)

        return output_path

    def _download_single(self, resolved: ResolvedURL, output_path: str, progress_callback: Optional[Callable[[int, int], None]] = None):
        """Single-stream download fallback."""
        headers = resolved.headers.copy()
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

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
        """Multi-threaded range request download."""
        part_size = file_size // self.num_connections
        ranges = []
        for i in range(self.num_connections):
            start = i * part_size
            end = file_size - 1 if i == self.num_connections - 1 else (start + part_size - 1)
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
            task = progress.add_task(f"Fast Download ({self.num_connections} threads) {os.path.basename(output_path)}", total=file_size)

            def _download_chunk(start: int, end: int, part_id: int):
                nonlocal downloaded_bytes
                range_headers = resolved.headers.copy()
                range_headers["Range"] = f"bytes={start}-{end}"
                range_headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

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
                        time.sleep(1)

            with ThreadPoolExecutor(max_workers=self.num_connections) as executor:
                futures = [executor.submit(_download_chunk, start, end, part_id) for start, end, part_id in ranges]
                for future in as_completed(futures):
                    future.result()
