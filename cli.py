#!/usr/bin/env python3
"""CLI interface for GoFile Fast Link Transfer."""

import sys
import os
import json
import click
from rich.console import Console
from src.gofile_transfer import TransferPipeline, __version__

# Reconfigure stdout/stderr to UTF-8 on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False)



@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("urls", nargs=-1, required=False)
@click.option("-b", "--batch", type=click.Path(exists=True), help="Path to text file containing URLs (one per line).")
@click.option("-c", "--connections", default=8, show_default=True, help="Number of parallel connections for downloader.")
@click.option("-t", "--token", envvar="GOFILE_TOKEN", help="Optional GoFile API token.")
@click.option("-f", "--folder-id", help="Optional GoFile destination folder ID.")
@click.option("-o", "--output", type=click.Path(), help="Directory to save downloaded files locally.")
@click.option("-k", "--keep", is_flag=True, help="Keep downloaded files on local disk after upload.")
@click.option("--json-output", is_flag=True, help="Output summary results in JSON format.")
@click.version_option(__version__, "-v", "--version", message="GoFile Fast Link Transfer v%(version)s")
def main(urls, batch, connections, token, folder_id, output, keep, json_output):
    """Ultra-fast downloader & uploader to transfer Google Drive, SourceForge, or direct links straight to GoFile."""
    target_urls = list(urls)

    if batch:
        with open(batch, "r", encoding="utf-8") as f:
            for line in f:
                cleaned = line.strip()
                if cleaned and not cleaned.startswith("#"):
                    target_urls.append(cleaned)

    if not target_urls:
        console.print("[bold red]Error:[/bold red] Please provide at least one URL or a --batch file.")
        click.echo(main.get_help(click.Context(main)))
        sys.exit(1)

    pipeline = TransferPipeline(connections=connections, gofile_token=token, keep_files=keep)
    results = []

    for idx, url in enumerate(target_urls, 1):
        if len(target_urls) > 1 and not json_output:
            console.print(f"\n[bold yellow]--- Processing Link ({idx}/{len(target_urls)}) ---[/bold yellow]")

        try:
            summary = pipeline.process_url(url, output_dir=output, folder_id=folder_id)
            results.append({
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
                "status": "success"
            })
        except Exception as e:
            console.print(f"[bold red][X] Failed to process URL '{url}':[/bold red] {e}")
            results.append({
                "url": url,
                "status": "error",
                "error": str(e)
            })

    if json_output:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
