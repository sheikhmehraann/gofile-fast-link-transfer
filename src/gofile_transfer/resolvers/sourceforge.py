"""SourceForge link resolver."""

import re
import requests
from urllib.parse import urlparse
from .base import BaseResolver, ResolvedURL


class SourceForgeResolver(BaseResolver):
    """Resolver for SourceForge file and mirror download links."""

    SF_DOMAINS = ["sourceforge.net", "sf.net", "downloads.sourceforge.net"]

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in self.SF_DOMAINS)

    def resolve(self, url: str) -> ResolvedURL:
        # Ensure mirror query parameter if not present
        target_url = url
        if "use_mirror" not in target_url and "sourceforge.net" in target_url:
            delimiter = "&" if "?" in target_url else "?"
            target_url += f"{delimiter}use_mirror=autoselect"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # Follow redirects to get final direct mirror URL
        res = requests.head(target_url, headers=headers, allow_redirects=True, timeout=15)
        if res.status_code >= 400 or "Content-Type" in res.headers and "text/html" in res.headers.get("Content-Type", ""):
            # Fallback to GET stream if HEAD is blocked or returns HTML redirect page
            res = requests.get(target_url, headers=headers, allow_redirects=True, stream=True, timeout=15)

        final_url = res.url
        filename = None
        cd = res.headers.get("Content-Disposition", "")
        if cd:
            fn_match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)["\']?', cd, re.IGNORECASE)
            if fn_match:
                filename = fn_match.group(1)

        if not filename:
            path_parts = [p for p in urlparse(final_url).path.split("/") if p and p != "download"]
            filename = path_parts[-1] if path_parts else "sourceforge_file.bin"

        file_size = None
        if "Content-Length" in res.headers:
            try:
                file_size = int(res.headers["Content-Length"])
            except ValueError:
                pass

        supports_ranges = res.headers.get("Accept-Ranges") == "bytes"

        return ResolvedURL(
            original_url=url,
            direct_url=final_url,
            filename=filename,
            file_size=file_size,
            headers=headers,
            cookies=res.cookies.get_dict(),
            supports_ranges=supports_ranges
        )
