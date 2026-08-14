"""SourceForge URL resolver with canonical GeoDNS director resolution."""

import re
import urllib.parse
import httpx
from typing import Optional
from .base import BaseResolver, ResolvedURL


class SourceForgeResolver(BaseResolver):
    """Resolver for SourceForge project files using canonical director redirects."""

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

    def can_handle(self, url: str) -> bool:
        return "sourceforge.net" in url.lower()

    def resolve(self, url: str) -> ResolvedURL:
        cleaned_url = url.strip().strip("'\"")
        
        # Canonical director format: https://downloads.sourceforge.net/project/<PROJECT>/<FILEPATH>
        match = re.search(r"sourceforge\.net/(?:projects/([^/]+)/files/|p/([^/]+)/.*?/download\?|project/([^/]+)/)(.+?)(?:/download)?(?:\?.*)?$", cleaned_url, re.IGNORECASE)
        
        headers = {"User-Agent": self.USER_AGENT}

        if match:
            project = match.group(1) or match.group(2) or match.group(3)
            filepath = match.group(4).rstrip("/")
            canonical_url = f"https://downloads.sourceforge.net/project/{project}/{filepath}"
        else:
            canonical_url = cleaned_url if cleaned_url.endswith("/download") else f"{cleaned_url}/download"

        # Resolve 302 redirect chain to signed mirror CDN with token
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            resp = client.head(canonical_url, headers=headers)
            if resp.status_code >= 400:
                resp = client.get(canonical_url, headers=headers)

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

            return ResolvedURL(
                direct_url=direct_url,
                filename=filename,
                file_size=file_size,
                headers=headers,
                supports_ranges=True,
                mirror_urls=[direct_url, canonical_url]
            )
