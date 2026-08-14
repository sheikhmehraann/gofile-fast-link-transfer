#!/usr/bin/env python3
"""Unified One-Job Entrypoint for GoFile Fast Link Transfer.

Usage:
  python main.py                                (Interactive prompt)
  python main.py "https://example.com/file.zip" (Direct execution)
"""

import sys
import os

# Ensure src is in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from src.gofile_transfer.pipeline import TransferPipeline

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False)


def run_job(url: str):
    """Execute the single link-to-GoFile job."""
    cleaned_url = url.strip().strip("'\"")
    if not cleaned_url:
        console.print("[bold red][X] Error: URL cannot be empty.[/bold red]")
        return

    pipeline = TransferPipeline(connections=16)
    try:
        summary = pipeline.process_url(cleaned_url)
        console.print(f"\n[bold green]✅ Ready to share:[/bold green] [bold underline cyan]{summary.gofile_url}[/bold underline cyan]\n")
    except Exception as e:
        console.print(f"\n[bold red][X] Transfer Failed:[/bold red] {e}\n")


def main():
    console.print(Panel(
        "[bold cyan]⚡ GoFile Fast Link Transfer[/bold cyan]\n"
        "[dim]Supported: Google Drive, SourceForge, MediaFire, Dropbox, Direct URLs[/dim]",
        border_style="cyan"
    ))

    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        try:
            target_url = console.input("[bold yellow]👉 Paste download link:[/bold yellow] ")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Aborted by user.[/dim]")
            sys.exit(0)

    run_job(target_url)


if __name__ == "__main__":
    main()
