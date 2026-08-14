#!/usr/bin/env python3
"""Main Entry Point for GoFile Fast Link Transfer with Rich Cyberpunk Aesthetic."""

import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

# Ensure local package import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gofile_transfer.pipeline import TransferPipeline

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False)

BANNER = r"""
  ██████╗  ██████╗ ███████╗██╗██╗     ███████╗
 ██╔════╝ ██╔═══██╗██╔════╝██║██║     ██╔════╝
 ██║  ███╗██║   ██║█████╗  ██║██║     █████╗  
 ██║   ██║██║   ██║██╔══╝  ██║██║     ██╔══╝  
 ╚██████╔╝╚██████╔╝██║     ██║███████╗███████╗
  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚══════╝╚══════╝
 ⚡ Ultra-Fast Multi-Thread Link Transfer Engine ⚡
"""


def print_banner():
    banner_text = Text(BANNER, style="bold cyan")
    info_panel = Panel(
        banner_text,
        subtitle="[bold yellow]Google Drive • SourceForge • MediaFire • Dropbox • Direct Links[/bold yellow]",
        border_style="bold blue",
    )
    console.print(info_panel)


def main():
    print_banner()

    if len(sys.argv) > 1 and sys.argv[1].strip():
        url = sys.argv[1].strip().strip("'\"")
    else:
        url = Prompt.ask("\n[bold green]👉 Enter download link[/bold green]")

    if not url:
        console.print("[bold red]❌ Error: No download link provided![/bold red]")
        sys.exit(1)

    token = os.environ.get("GOFILE_TOKEN") or None

    try:
        pipeline = TransferPipeline(connections=32, gofile_token=token)
        summary = pipeline.process_url(url)
        console.print(f"\n[bold green]✅ Ready to share:[/bold green] [bold underline cyan]{summary.gofile_url}[/bold underline cyan]\n")
    except KeyboardInterrupt:
        console.print("\n[bold red][!] Transfer cancelled by user.[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red][!] Transfer failed:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
