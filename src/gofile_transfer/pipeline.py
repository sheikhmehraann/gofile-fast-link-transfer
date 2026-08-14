"""Orchestrated link-to-GoFile pipeline with Zero-Disk Direct Streaming Pipe support."""

import os
import sys
import time
import tempfile
from dataclasses import dataclass
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .resolvers import ResolverFactory, ResolvedURL
from .downloader import ParallelDownloader
from .uploader import GoFileUploader, GoFileResult
from .streamer import DirectStreamPipe

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False)


@dataclass
class TransferSummary:
    """Dataclass storing end-to-end performance and result details."""
    original_url: str
    filename: str
    file_size: int
    gofile_url: str
    gofile_code: str
    download_time: float
    upload_time: float
    total_time: float
    download_speed_mbps: float
    upload_speed_mbps: float
    mode: str = "Live Stream Pipe"


class TransferPipeline:
    """End-to-end pipeline with Zero-Disk Stream Pipe for fastest possible throughput."""

    def __init__(self, connections: int = 16, gofile_token: Optional[str] = None, keep_files: bool = False, use_stream_pipe: bool = True):
        self.factory = ResolverFactory()
        self.downloader = ParallelDownloader(num_connections=connections)
        self.uploader = GoFileUploader(token=gofile_token)
        self.streamer = DirectStreamPipe(uploader=self.uploader)
        self.keep_files = keep_files
        self.use_stream_pipe = use_stream_pipe

    def process_url(self, url: str, output_dir: Optional[str] = None, folder_id: Optional[str] = None) -> TransferSummary:
        """Process URL via Zero-Disk Stream Pipe or Multi-Threaded Parallel buffer."""
        start_total = time.time()

        console.print(f"[bold cyan][>] Resolving URL:[/bold cyan] {url}")
        resolved: ResolvedURL = self.factory.resolve(url)

        console.print(f"[bold green][+] Link Resolved![/bold green] Direct URL: {resolved.direct_url[:80]}...")
        console.print(f"[bold white]File Name:[/bold white] {resolved.filename} | [bold white]Size:[/bold white] {f'{resolved.file_size / (1024*1024):.2f} MB' if resolved.file_size else 'Unknown'}")

        # Method 1: Zero-Disk Concurrent Streaming Pipe (Fastest Mode)
        if self.use_stream_pipe and not self.keep_files and not output_dir and resolved.file_size:
            try:
                console.print("[bold magenta]🚀 Mode: Zero-Disk Concurrent Stream Pipe (Simultaneous Download + Upload)[/bold magenta]")
                start_stream = time.time()
                gofile_res = self.streamer.transfer_stream(resolved, folder_id=folder_id)
                stream_duration = max(time.time() - start_stream, 0.001)

                file_size = resolved.file_size or 0
                avg_speed = (file_size / (1024 * 1024)) / stream_duration
                total_duration = time.time() - start_total

                summary = TransferSummary(
                    original_url=url,
                    filename=gofile_res.file_name,
                    file_size=file_size,
                    gofile_url=gofile_res.download_page,
                    gofile_code=gofile_res.code,
                    download_time=stream_duration,
                    upload_time=stream_duration,
                    total_time=total_duration,
                    download_speed_mbps=avg_speed,
                    upload_speed_mbps=avg_speed,
                    mode="Zero-Disk Stream Pipe (Live)"
                )
                self.print_summary_panel(summary)
                return summary
            except Exception as e:
                console.print(f"[yellow][!] Stream pipe notice ({e}). Falling back to multi-connection parallel engine...[/yellow]")

        # Method 2: Multi-Connection Parallel Range Buffer (Fallback / Keep-Files Mode)
        temp_dir = output_dir or tempfile.mkdtemp(prefix="gofile_transfer_")
        try:
            start_dl = time.time()
            local_path = self.downloader.download(resolved, output_dir=temp_dir)
            dl_duration = max(time.time() - start_dl, 0.001)

            file_size = os.path.getsize(local_path)
            dl_speed = (file_size / (1024 * 1024)) / dl_duration
            console.print(f"[bold green][+] Download Completed![/bold green] Time: {dl_duration:.2f}s ({dl_speed:.2f} MB/s)")

            start_ul = time.time()
            gofile_res = self.uploader.upload(local_path, folder_id=folder_id)
            ul_duration = max(time.time() - start_ul, 0.001)
            ul_speed = (file_size / (1024 * 1024)) / ul_duration
            total_duration = time.time() - start_total

            console.print(f"[bold green][+] Upload Completed![/bold green] Time: {ul_duration:.2f}s ({ul_speed:.2f} MB/s)")

            summary = TransferSummary(
                original_url=url,
                filename=resolved.filename or os.path.basename(local_path),
                file_size=file_size,
                gofile_url=gofile_res.download_page,
                gofile_code=gofile_res.code,
                download_time=dl_duration,
                upload_time=ul_duration,
                total_time=total_duration,
                download_speed_mbps=dl_speed,
                upload_speed_mbps=ul_speed,
                mode="16-Thread Parallel Buffer"
            )
            self.print_summary_panel(summary)
            return summary
        finally:
            if not self.keep_files and temp_dir and os.path.exists(temp_dir) and not output_dir:
                try:
                    for f in os.listdir(temp_dir):
                        os.remove(os.path.join(temp_dir, f))
                    os.rmdir(temp_dir)
                except Exception:
                    pass

    def print_summary_panel(self, summary: TransferSummary):
        """Render a clean rich terminal summary panel."""
        table = Table(show_header=False, box=None)
        table.add_row("[bold cyan]GoFile Link:[/bold cyan]", f"[bold green u]{summary.gofile_url}[/bold green u]")
        table.add_row("[bold white]File Name:[/bold white]", summary.filename)
        table.add_row("[bold white]File Size:[/bold white]", f"{summary.file_size / (1024 * 1024):.2f} MB")
        table.add_row("[bold white]Transfer Mode:[/bold white]", f"[magenta]{summary.mode}[/magenta]")
        table.add_row("[bold white]Transfer Speed:[/bold white]", f"{summary.upload_speed_mbps:.2f} MB/s")
        table.add_row("[bold white]Total Duration:[/bold white]", f"{summary.total_time:.2f}s")

        console.print(Panel(table, title="[+] Transfer Completed Successfully", border_style="bold green"))
