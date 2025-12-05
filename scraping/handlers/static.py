from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedPage


class StaticHttpScraper(BaseScraper):
    """Default scraper for static HTTP/HTTPS content."""

    handler_name = "static_http"

    def fetch(self, url: str) -> Tuple[Optional[ScrapedPage], Optional[int], Optional[str]]:
        try:
            response = self.session.get(
                url, timeout=self.config.request_timeout, allow_redirects=True
            )

            content_type = response.headers.get("content-type", "").lower()
            extension = self._get_file_extension(content_type, url)
            title = self._extract_title(response, url)
            content: bytes | str
            if content_type.startswith("text/") or "json" in content_type or "xml" in content_type:
                content = response.text
            else:
                content = response.content

            page = ScrapedPage(
                url=url,
                title=title,
                content=content,
                status_code=response.status_code,
                extension=extension,
                handler=self.handler_name,
            )

            error_code: Optional[int] = None
            error_message: Optional[str] = None
            if response.status_code != 200:
                error_code = response.status_code
                error_message = f"HTTP {response.status_code}"

            return page, error_code, error_message

        except Exception as e:  # noqa: BLE001
            return None, None, str(e)

    def discover_links(self, page: ScrapedPage, base_url: str) -> ScrapedPage:
        if not isinstance(page.content, str):
            return page

        soup = BeautifulSoup(page.content, "html.parser")
        internal_links, external_links, social_links = self._extract_links(soup, base_url)
        page.internal_links = internal_links
        page.external_links = external_links
        page.social_links = social_links
        # Refresh title from DOM if available
        if soup.title and soup.title.string:
            page.title = soup.title.string.strip()
        return page

    def _extract_title(self, response, url: str) -> str:
        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            return Path(urlparse(url).path).name or url

        soup = BeautifulSoup(response.content, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()

        path = urlparse(url).path
        return path.strip("/").split("/")[-1] or "index"

    def _extract_links(self, soup: BeautifulSoup, base_url: str):
        internal_links = set()
        external_links = set()
        social_links = set()

        base_parsed = urlparse(base_url)
        base_path = base_parsed.path.rstrip("/")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)

            if parsed.scheme not in ("http", "https"):
                continue

            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
            if parsed.query:
                normalized += f"?{parsed.query}"

            if normalized == base_url.rstrip("/"):
                continue

            is_ignored, _ = self.config.is_ignored(normalized)
            if is_ignored:
                continue

            if parsed.netloc in self.config.social_domains:
                social_links.add(normalized)
            elif parsed.netloc == base_parsed.netloc and parsed.path.startswith(base_path):
                internal_links.add(normalized)
            else:
                external_links.add(normalized)

        return internal_links, external_links, social_links

    def _get_file_extension(self, content_type: str, url: str) -> str:
        if "text/html" in content_type:
            return ".html"
        if "application/pdf" in content_type:
            return ".pdf"
        if "application/json" in content_type:
            return ".json"
        if "text/plain" in content_type:
            return ".txt"
        if "text/xml" in content_type or "application/xml" in content_type:
            return ".xml"
        if "text/markdown" in content_type:
            return ".md"

        parsed = urlparse(url)
        path = parsed.path
        if "." in path:
            ext = Path(path).suffix
            if ext:
                return ext
        return ".html"
