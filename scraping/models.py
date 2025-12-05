#!/usr/bin/env python3
"""
Polkadot Bounty Archive - Data Models

Type-safe data models for all operational data structures.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum


class SuggestionType(Enum):
    """Type of suggestion"""
    SCRAPE = "scrape"
    ASSOCIATED_URL = "associated_url"
    SOCIAL = "social"


class ScrapeMode(Enum):
    """Scraping mode"""
    SINGLE = "single"
    RECURSIVE = "recursive"


class ScrapeStatus(Enum):
    """Scraping status"""
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class Suggestion:
    """A URL suggestion for scraping or metadata"""
    bounty_id: int
    url: str
    source: str
    categories: List[str]
    type: SuggestionType
    mode: Optional[str] = None
    max_depth: Optional[int] = None
    discovered_at: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize data"""
        if not self.url.startswith('http'):
            raise ValueError(f"Invalid URL: {self.url}")
        if self.bounty_id <= 0:
            raise ValueError(f"Invalid bounty_id: {self.bounty_id}")
        if not self.categories:
            self.categories = ['other']
        # Convert string to enum if needed
        if isinstance(self.type, str):
            self.type = SuggestionType(self.type)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization"""
        result = asdict(self)
        result['type'] = self.type.value
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Suggestion':
        """Create from dictionary"""
        return cls(
            bounty_id=data['bounty_id'],
            url=data['url'],
            source=data.get('source', 'Unknown'),
            categories=data.get('categories', ['other']),
            type=SuggestionType(data.get('type', 'scrape')),
            mode=data.get('mode'),
            max_depth=data.get('max_depth'),
            discovered_at=data.get('discovered_at')
        )


@dataclass
class QueueEntry:
    """A scraping job in the queue"""
    bounty_id: int
    url: str
    mode: ScrapeMode
    max_depth: int = 1
    source: str = "Unknown"
    categories: List[str] = field(default_factory=lambda: ['other'])
    type: str = "scrape"
    discovered_at: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize data"""
        if not self.url.startswith('http'):
            raise ValueError(f"Invalid URL: {self.url}")
        if self.bounty_id <= 0:
            raise ValueError(f"Invalid bounty_id: {self.bounty_id}")
        if self.max_depth < 0 or self.max_depth > 9:
            raise ValueError(f"Invalid max_depth: {self.max_depth}")
        # Convert string to enum if needed
        if isinstance(self.mode, str):
            self.mode = ScrapeMode(self.mode)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization"""
        result = asdict(self)
        result['mode'] = self.mode.value
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueEntry':
        """Create from dictionary"""
        return cls(
            bounty_id=data['bounty_id'],
            url=data['url'],
            mode=ScrapeMode(data.get('mode', 'single')),
            max_depth=data.get('max_depth', 1),
            source=data.get('source', 'Unknown'),
            categories=data.get('categories', ['other']),
            type=data.get('type', 'scrape'),
            discovered_at=data.get('discovered_at')
        )


@dataclass
class IndexEntry:
    """An indexed URL that has been scraped"""
    url: str
    bounty_id: int
    scraped_at: str
    location: str
    source: str = "Unknown"
    categories: List[str] = field(default_factory=lambda: ['other'])
    type: str = "scrape"
    discovered_at: Optional[str] = None
    status: str = "success"  # "success" or "failed"
    error_code: Optional[int] = None  # HTTP status code (404, 403, etc.)
    error_message: Optional[str] = None  # Error description

    def __post_init__(self):
        """Validate data"""
        if not self.url.startswith('http'):
            raise ValueError(f"Invalid URL: {self.url}")
        if self.bounty_id <= 0:
            raise ValueError(f"Invalid bounty_id: {self.bounty_id}")
        if self.status not in ('success', 'failed'):
            raise ValueError(f"Invalid status: {self.status}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization"""
        result = asdict(self)
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndexEntry':
        """Create from dictionary"""
        return cls(
            url=data['url'],
            bounty_id=data['bounty_id'],
            scraped_at=data.get('scraped_at', ''),
            location=data.get('location', ''),
            source=data.get('source', 'Unknown'),
            categories=data.get('categories', ['other']),
            type=data.get('type', 'scrape'),
            discovered_at=data.get('discovered_at'),
            status=data.get('status', 'success'),
            error_code=data.get('error_code'),
            error_message=data.get('error_message')
        )


@dataclass
class DiscoveredLink:
    """A link discovered during scraping"""
    url: str
    source_url: str
    bounty_id: int
    categories: List[str]
    discovered_at: str

    def __post_init__(self):
        """Validate data"""
        if not self.url.startswith('http'):
            raise ValueError(f"Invalid URL: {self.url}")
        if not self.source_url.startswith('http'):
            raise ValueError(f"Invalid source_url: {self.source_url}")
        if self.bounty_id <= 0:
            raise ValueError(f"Invalid bounty_id: {self.bounty_id}")
        if not self.categories:
            self.categories = ['other']

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiscoveredLink':
        """Create from dictionary"""
        return cls(
            url=data['url'],
            source_url=data['source_url'],
            bounty_id=data['bounty_id'],
            categories=data.get('categories', ['other']),
            discovered_at=data.get('discovered_at', '')
        )


@dataclass
class ScrapeResult:
    """Result of a scraping operation"""
    bounty_id: int
    url: str
    mode: str
    status: ScrapeStatus
    pages_scraped: int
    scraped_at: str
    files_created: List[str] = field(default_factory=list)
    visited_urls: List[str] = field(default_factory=list)
    outgoing_urls: Dict[str, List[str]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    source: str = "Unknown"
    categories: List[str] = field(default_factory=lambda: ['other'])
    type: str = "scrape"
    discovered_at: Optional[str] = None
    max_depth: Optional[int] = None

    def __post_init__(self):
        """Validate and normalize data"""
        if not self.url.startswith('http'):
            raise ValueError(f"Invalid URL: {self.url}")
        if self.bounty_id <= 0:
            raise ValueError(f"Invalid bounty_id: {self.bounty_id}")
        if self.pages_scraped < 0:
            raise ValueError(f"Invalid pages_scraped: {self.pages_scraped}")
        # Convert string to enum if needed
        if isinstance(self.status, str):
            self.status = ScrapeStatus(self.status)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization"""
        result = asdict(self)
        result['status'] = self.status.value
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScrapeResult':
        """Create from dictionary"""
        return cls(
            bounty_id=data['bounty_id'],
            url=data['url'],
            mode=data.get('mode', 'single'),
            status=ScrapeStatus(data.get('status', 'completed')),
            pages_scraped=data.get('pages_scraped', 0),
            scraped_at=data.get('scraped_at', ''),
            files_created=data.get('files_created', []),
            visited_urls=data.get('visited_urls', []),
            outgoing_urls=data.get('outgoing_urls', {}),
            errors=data.get('errors', []),
            source=data.get('source', 'Unknown'),
            categories=data.get('categories', ['other']),
            type=data.get('type', 'scrape'),
            discovered_at=data.get('discovered_at'),
            max_depth=data.get('max_depth')
        )


# Helper functions for bulk conversions

def suggestions_to_dicts(suggestions: List[Suggestion]) -> List[Dict[str, Any]]:
    """Convert list of Suggestions to list of dicts"""
    return [s.to_dict() for s in suggestions]


def suggestions_from_dicts(dicts: List[Dict[str, Any]]) -> List[Suggestion]:
    """Convert list of dicts to list of Suggestions"""
    return [Suggestion.from_dict(d) for d in dicts]


def queue_entries_to_dicts(entries: List[QueueEntry]) -> List[Dict[str, Any]]:
    """Convert list of QueueEntries to list of dicts"""
    return [e.to_dict() for e in entries]


def queue_entries_from_dicts(dicts: List[Dict[str, Any]]) -> List[QueueEntry]:
    """Convert list of dicts to list of QueueEntries"""
    return [QueueEntry.from_dict(d) for d in dicts]


def index_entries_to_dicts(entries: List[IndexEntry]) -> List[Dict[str, Any]]:
    """Convert list of IndexEntries to list of dicts"""
    return [e.to_dict() for e in entries]


def index_entries_from_dicts(dicts: List[Dict[str, Any]]) -> List[IndexEntry]:
    """Convert list of dicts to list of IndexEntries"""
    return [IndexEntry.from_dict(d) for d in dicts]


def links_to_dicts(links: List[DiscoveredLink]) -> List[Dict[str, Any]]:
    """Convert list of DiscoveredLinks to list of dicts"""
    return [link.to_dict() for link in links]


def links_from_dicts(dicts: List[Dict[str, Any]]) -> List[DiscoveredLink]:
    """Convert list of dicts to list of DiscoveredLinks"""
    return [DiscoveredLink.from_dict(d) for d in dicts]


def results_to_dicts(results: List[ScrapeResult]) -> List[Dict[str, Any]]:
    """Convert list of ScrapeResults to list of dicts"""
    return [r.to_dict() for r in results]


def results_from_dicts(dicts: List[Dict[str, Any]]) -> List[ScrapeResult]:
    """Convert list of dicts to list of ScrapeResults"""
    return [ScrapeResult.from_dict(d) for d in dicts]
