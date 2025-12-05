from __future__ import annotations

from typing import List, Tuple, Type
from urllib.parse import urlparse

from config import ScrapeConfig
from .base import BaseScraper, ScrapedPage
from .static import StaticHttpScraper

HandlerRegistryEntry = Tuple[List[str], Type[BaseScraper]]


class HandlerRegistry:
    """Registry mapping domain patterns to scraper handlers."""

    def __init__(self):
        self._registry: List[HandlerRegistryEntry] = []
        self.register(["*"], StaticHttpScraper)

    def register(self, patterns: List[str], handler_cls: Type[BaseScraper]):
        self._registry.append((patterns, handler_cls))

    def resolve(self, url: str, config: ScrapeConfig, session) -> BaseScraper:
        domain = urlparse(url).netloc.lower()

        # Try pattern-based matches (reuse config categorization pattern semantics)
        for patterns, handler_cls in self._registry:
            for pattern in patterns:
                if pattern == "*":
                    continue
                if pattern.lower() in domain:
                    return handler_cls(session=session, config=config)

        # Default fallback
        return StaticHttpScraper(session=session, config=config)


handler_registry = HandlerRegistry()


def get_handler_for_url(url: str, config: ScrapeConfig, session) -> BaseScraper:
    return handler_registry.resolve(url, config, session)


__all__ = [
    "BaseScraper",
    "ScrapedPage",
    "StaticHttpScraper",
    "get_handler_for_url",
    "HandlerRegistry",
    "handler_registry",
]
