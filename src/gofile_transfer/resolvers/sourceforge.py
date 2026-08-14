"""SourceForge URL resolver with multi-mirror direct link generator for 1 GB/s parallel acceleration."""

import re
import urllib.parse
import httpx
from typing import Optional, List
from .base import BaseResolver, ResolvedURL


class SourceForgeResolver(BaseResolver):
    """Resolver for SourceForge project files with multi-mirror aggregation."""

    MIRRORS = [
        "netactuate", "phoenixnap", "cfhcable", "gigenet", "pilotfiber",
        "cytranet", "iweb", "deac-riga", "deac-fra", "altushost-swe",
        "altushost-bul", "freefr", "jaist", "twds", "nchc", "ixpeering",
        "liquidtelecom", "tenet", "sitsa", "fastly"
    ]

    def can_handle(self, url: str) -> bool:
        return "sourceforge.net" in url.lower()

    def resolve(self, url: str) -> ResolvedURL:
        # Standardize URL
        cleaned_url = url.strip().strip("'\"")
        
        # Ensure /download suffix
        if not cleaned_url.endswith("/download") and "/files/" in cleaned_url:
            if not cleaned_url.endswith("/"):
                cleaned_url += "/download"
            else:
                cleaned_url += "download"

        # Extract project and filepath
        mirror_urls: List[str] = []
        match = re.search(r"sourceforge\.net/projects/([^/]+)/files/(.+?)(?:/download)?(?:\?|$)", cleaned_url, re.IGNORECASE)
        if match:
            project = match.group(1)
            filepath = match.group(2).rstrip("/")
            
            # Generate multi-mirror URLs directly
            for m in self.MIRRORS:
                mirror_urls.append(f"https://{m}.dl.sourceforge.net/project/{project}/{filepath}")
            mirror_urls.append(f"https://master.dl.sourceforge.net/project/{project}/{filepath}")

        # Follow redirect using Wget user-agent to get direct CDN signed mirror and metadata
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            resp = client.head(cleaned_url, headers=headers)
            if resp.status_code >= 400:
                resp = client.get(cleaned_url, headers=headers)

            direct_url = str(resp.url)
            file_size = int(resp.headers.get("Content-Length", 0)) or None
            
            filename = None
            cd = resp.headers.get("Content-Disposition", "")
            if "filename=" in cd:
                fname_match = re.search(r'filename="?([^";]+)"?', cd)
                if fname_match:
                    filename = fname_match.group(1)

            if not filename:
                parsed = urllib.parse.urlparse(direct_url)
                path_part = parsed.path.rstrip("/")
                if path_part:
                    filename = path_part.split("/")[-1]

            if not filename or filename == "download":
                parsed = urllib.parse.urlparse(cleaned_url.replace("/download", ""))
                filename = parsed.path.split("/")[-1]

            if direct_url not in mirror_urls:
                mirror_urls.insert(0, direct_url)

            return ResolvedURL(
                direct_url=direct_url,
                filename=filename,
                file_size=file_size,
                headers=headers,
                supports_ranges=True,
                mirror_urls=mirror_urls
            )
