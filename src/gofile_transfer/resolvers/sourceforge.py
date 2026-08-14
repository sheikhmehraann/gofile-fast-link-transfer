"""SourceForge link resolver."""

import re
import requests
from urllib.parse import urlparse
from .base import BaseResolver, ResolvedURL


class SourceForgeResolver(BaseResolver):
    """Resolver for SourceForge file and mirror download links."""

    SF_DOMAINS = ["sourceforge.net", "sf.net", "downloads.sourceforge.net", "master.dl.sourceforge.net"]

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in self.SF_DOMAINS)

    def resolve(self, url: str) -> ResolvedURL:
        clean_url = url
        if "sourceforge.net/projects" in clean_url and not clean_url.endswith("/download") and "?download" not in clean_url:
            clean_url = clean_url.rstrip("/") + "/download"

        session = requests.Session()
        headers = {
            "User-Agent": "Wget/1.21.3",
            "Accept": "*/*",
            "Connection": "Keep-Alive"
        }

        # Follow redirects with CLI UA to receive signed mirror URL
        res = session.get(clean_url, headers=headers, allow_redirects=True, stream=True, timeout=25)
        res.raise_for_status()

        final_url = res.url
        filename = None
        cd = res.headers.get("Content-Disposition", "")
        if cd:
            fn_match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)["\']?', cd, re.IGNORECASE)
            if fn_match:
                filename = fn_match.group(1)

        if not filename:
            path_parts = [p for p in urlparse(final_url).path.split("/") if p and p != "download"]
            filename = path_parts[-1] if path_parts else "sourceforge_file.zip"

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
            cookies=session.cookies.get_dict(),
            supports_ranges=supports_ranges
        )
