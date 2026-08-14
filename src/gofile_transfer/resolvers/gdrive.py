"""Google Drive link resolver."""

import re
import requests
from urllib.parse import parse_qs, urlparse
from typing import Optional
from .base import BaseResolver, ResolvedURL


class GoogleDriveResolver(BaseResolver):
    """Resolver for Google Drive sharing and export links."""

    GDRIVE_DOMAINS = ["drive.google.com", "docs.google.com"]

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in self.GDRIVE_DOMAINS)

    def extract_file_id(self, url: str) -> Optional[str]:
        """Extract Google Drive file ID from various URL patterns."""
        # Pattern 1: /file/d/ID/view
        match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)

        # Pattern 2: ?id=ID or &id=ID
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "id" in params and params["id"]:
            return params["id"][0]

        # Pattern 3: /d/ID
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)

        return None

    def resolve(self, url: str) -> ResolvedURL:
        file_id = self.extract_file_id(url)
        if not file_id:
            raise ValueError(f"Could not extract Google Drive file ID from URL: {url}")

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        base_download_url = "https://drive.google.com/uc?export=download"
        res = session.get(base_download_url, params={"id": file_id}, stream=True)

        confirm_token = None
        for key, val in res.cookies.items():
            if key.startswith("download_warning"):
                confirm_token = val
                break

        if not confirm_token:
            # Check HTML for confirm token input or link
            content_sample = res.text[:5000] if "text/html" in res.headers.get("Content-Type", "") else ""
            token_match = re.search(r'confirm=([a-zA-Z0-9_-]+)', content_sample)
            if token_match:
                confirm_token = token_match.group(1)

        if confirm_token:
            final_res = session.get(base_download_url, params={"id": file_id, "confirm": confirm_token}, stream=True)
        else:
            final_res = res

        # Extract filename from Content-Disposition if present
        filename = None
        cd = final_res.headers.get("Content-Disposition", "")
        if cd:
            fn_match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)["\']?', cd, re.IGNORECASE)
            if fn_match:
                filename = fn_match.group(1)

        if not filename:
            filename = f"gdrive_{file_id}.bin"

        file_size = None
        if "Content-Length" in final_res.headers:
            try:
                file_size = int(final_res.headers["Content-Length"])
            except ValueError:
                pass

        supports_ranges = final_res.headers.get("Accept-Ranges") == "bytes"

        # Get response cookies dict
        cookies_dict = session.cookies.get_dict()

        return ResolvedURL(
            original_url=url,
            direct_url=final_res.url,
            filename=filename,
            file_size=file_size,
            headers=dict(final_res.request.headers),
            cookies=cookies_dict,
            supports_ranges=supports_ranges
        )
