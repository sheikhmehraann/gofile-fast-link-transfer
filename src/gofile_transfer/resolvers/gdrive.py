"""Google Drive link resolver with smart confirmation form parsing and token resolution."""

import re
import requests
from urllib.parse import parse_qs, urlparse, urljoin
from typing import Optional
from .base import BaseResolver, ResolvedURL


class GoogleDriveResolver(BaseResolver):
    """Resolver for Google Drive sharing, folder, and export links."""

    GDRIVE_DOMAINS = ["drive.google.com", "docs.google.com", "drive.usercontent.google.com"]

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in self.GDRIVE_DOMAINS)

    def extract_file_id(self, url: str) -> Optional[str]:
        """Extract Google Drive file ID from various URL patterns."""
        match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "id" in params and params["id"]:
            return params["id"][0]

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

        initial_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        res = session.get(initial_url, stream=True)

        final_res = res

        # Check if Google returned an HTML page (e.g., Virus scan warning / Download anyway form)
        content_type = res.headers.get("Content-Type", "")
        if "text/html" in content_type:
            html_text = res.text

            # 1. Search for HTML form action and inputs (Google Drive Download anyway form)
            form_match = re.search(r'<form[^>]*action="([^"]+)"[^>]*>(.*?)</form>', html_text, re.DOTALL | re.IGNORECASE)
            if form_match:
                action_url = form_match.group(1)
                if not action_url.startswith("http"):
                    action_url = urljoin(res.url, action_url)

                form_content = form_match.group(2)
                inputs = re.findall(r'name="([^"]+)"\s+value="([^"]+)"', form_content)

                form_params = {k: v for k, v in inputs}
                if "id" not in form_params:
                    form_params["id"] = file_id

                final_res = session.get(action_url, params=form_params, stream=True)
            else:
                # 2. Check for confirm token in cookies or links
                confirm_token = None
                for key, val in session.cookies.items():
                    if key.startswith("download_warning"):
                        confirm_token = val
                        break

                if not confirm_token:
                    token_match = re.search(r'confirm=([a-zA-Z0-9_-]+)', html_text)
                    if token_match:
                        confirm_token = token_match.group(1)

                if confirm_token:
                    final_res = session.get("https://drive.google.com/uc?export=download", params={"id": file_id, "confirm": confirm_token}, stream=True)

        # Extract filename from Content-Disposition header
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

        return ResolvedURL(
            original_url=url,
            direct_url=final_res.url,
            filename=filename,
            file_size=file_size,
            headers=dict(final_res.request.headers),
            cookies=session.cookies.get_dict(),
            supports_ranges=supports_ranges
        )
