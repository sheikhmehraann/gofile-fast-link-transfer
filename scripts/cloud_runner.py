#!/usr/bin/env python3
"""GitHub Actions Cloud Runner script for GoFile Fast Link Transfer with Zero-Disk Stream Pipe."""

import sys
import os

# Ensure src in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gofile_transfer.pipeline import TransferPipeline


def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("❌ Error: No download URL provided.")
        sys.exit(1)

    url = sys.argv[1].strip().strip("'\"")
    token = os.environ.get("GOFILE_TOKEN") or None

    print("\n" + "=" * 60)
    print("🚀 Starting 1-Job Zero-Disk Cloud Stream Pipe Transfer")
    print(f"🔗 URL: {url}")
    print("=" * 60 + "\n")

    pipeline = TransferPipeline(connections=16, gofile_token=token, use_stream_pipe=True)

    try:
        summary = pipeline.process_url(url)

        print("\n" + "=" * 60)
        print(f"🎉 SUCCESS! GOFILE LINK: {summary.gofile_url}")
        print(f"📄 File: {summary.filename} ({summary.file_size / (1024 * 1024):.2f} MB)")
        print(f"⚡ Transfer Mode: {summary.mode}")
        print(f"⚡ Transfer Speed: {summary.upload_speed_mbps:.2f} MB/s")
        print(f"⏱️ Total Time: {summary.total_time:.2f}s")
        print("=" * 60 + "\n")

        # GitHub Actions Notice Annotation (appears at top of run page)
        print(f"::notice title=🎉 GoFile Download Link::{summary.gofile_url}")

        # Post to GitHub Actions Step Summary
        step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if step_summary_path:
            md_summary = (
                f"# 🚀 Cloud Transfer Completed Successfully!\n\n"
                f"| Metric | Details |\n"
                f"| :--- | :--- |\n"
                f"| **GoFile Link** | [**{summary.gofile_url}**]({summary.gofile_url}) |\n"
                f"| **File Name** | `{summary.filename}` |\n"
                f"| **File Size** | {summary.file_size / (1024 * 1024):.2f} MB |\n"
                f"| **Transfer Mode** | {summary.mode} |\n"
                f"| **Transfer Speed** | {summary.upload_speed_mbps:.2f} MB/s |\n"
                f"| **Total Duration** | {summary.total_time:.2f}s |\n\n"
                f"## 👉 [Click Here to Download from GoFile]({summary.gofile_url})\n"
            )
            with open(step_summary_path, "a", encoding="utf-8") as f:
                f.write(md_summary)

    except Exception as e:
        print(f"\n❌ Transfer Failed: {e}\n")
        step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if step_summary_path:
            with open(step_summary_path, "a", encoding="utf-8") as f:
                f.write(f"# ❌ Cloud Transfer Failed\n\n**Error:** `{e}`\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
