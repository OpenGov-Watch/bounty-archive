from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Set, Tuple, Optional


@dataclass
class ScrapedPage:
    """Represents a scraped page"""

    url: str
    title: str
    content: bytes | str
    status_code: int
    extension: str
    handler: str
    internal_links: Set[str] = field(default_factory=set)
    external_links: Set[str] = field(default_factory=set)
    social_links: Set[str] = field(default_factory=set)


class BaseScraper(ABC):
    """Abstract scraper interface"""

    handler_name: str = "base"

    def __init__(self, session, config):
        self.session = session
        self.config = config

    @abstractmethod
    def fetch(self, url: str) -> Tuple[Optional[ScrapedPage], Optional[int], Optional[str]]:
        """Fetch a URL and return ScrapedPage on success or error details on failure."""

    @abstractmethod
    def discover_links(self, page: ScrapedPage, base_url: str) -> ScrapedPage:
        """Populate link fields on the page and return it."""
