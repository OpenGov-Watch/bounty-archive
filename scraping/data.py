#!/usr/bin/env python3
"""
Polkadot Bounty Archive - Data Manager

Central data management class for operational files (index, links, queue, results, suggestions)
"""

import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union

# Import models for type safety
from models import (
    Suggestion, QueueEntry, IndexEntry, DiscoveredLink, ScrapeResult,
    suggestions_to_dicts, suggestions_from_dicts,
    queue_entries_to_dicts, queue_entries_from_dicts,
    index_entries_to_dicts, index_entries_from_dicts,
    links_to_dicts, links_from_dicts,
    results_to_dicts, results_from_dicts
)


class ScrapeData:
    """Centralized data manager for scraping operational files"""

    def __init__(self, scraping_dir: Path):
        self.scraping_dir = scraping_dir.resolve()
        self.index_file = self.scraping_dir / "scrape-index.yml"
        self.links_file = self.scraping_dir / "scrape-links.yml"
        self.queue_file = self.scraping_dir / "scrape-queue.yml"
        self.results_file = self.scraping_dir / "scrape-results.yml"
        self.suggestions_file = self.scraping_dir / "scrape-suggestions.yml"

    # ========== Generic File Operations ==========

    def _load_yaml(self, file_path: Path) -> Dict:
        """Load YAML file, return empty dict if not exists"""
        if not file_path.exists():
            return {}

        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data is not None else {}

    def _save_yaml(self, file_path: Path, data: Dict):
        """Save YAML file with consistent formatting"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    # ========== Index Operations ==========

    def load_index(self) -> List[Dict]:
        """Load scrape index as dicts"""
        data = self._load_yaml(self.index_file)
        return data.get('index', [])

    def load_index_typed(self) -> List[IndexEntry]:
        """Load scrape index as typed objects"""
        return index_entries_from_dicts(self.load_index())

    def save_index(self, index: Union[List[IndexEntry], List[Dict]]):
        """Save scrape index (accepts typed objects or dicts)"""
        # Convert to dicts if needed
        if index and isinstance(index[0], IndexEntry):
            index = index_entries_to_dicts(index)

        data = {
            'version': '1.0',
            'last_updated': self._get_timestamp(),
            'index': index
        }
        self._save_yaml(self.index_file, data)

    def add_to_index(self, entries: Union[List[IndexEntry], List[Dict]]):
        """Add entries to index (no duplicates by URL)"""
        # Convert to dicts if needed
        if entries and isinstance(entries[0], IndexEntry):
            entries = index_entries_to_dicts(entries)

        index = self.load_index()
        existing_urls = {entry['url'] for entry in index}

        for entry in entries:
            if entry['url'] not in existing_urls:
                index.append(entry)
                existing_urls.add(entry['url'])

        self.save_index(index)

    def is_indexed(self, url: str) -> bool:
        """Check if URL is in index"""
        index = self.load_index()
        return any(entry['url'] == url for entry in index)

    def remove_from_index(self, url: Optional[str] = None, bounty_id: Optional[int] = None) -> int:
        """Remove entries from index by URL or bounty_id. Returns count removed."""
        index = self.load_index()
        original_count = len(index)

        new_index = [
            entry for entry in index
            if not ((url and entry.get('url') == url) or
                   (bounty_id and entry.get('bounty_id') == bounty_id))
        ]

        self.save_index(new_index)
        return original_count - len(new_index)

    # ========== Links Operations ==========

    def load_links(self) -> List[Dict]:
        """Load discovered links as dicts"""
        data = self._load_yaml(self.links_file)
        return data.get('discovered_links', [])

    def load_links_typed(self) -> List[DiscoveredLink]:
        """Load discovered links as typed objects"""
        return links_from_dicts(self.load_links())

    def save_links(self, links: Union[List[DiscoveredLink], List[Dict]]):
        """Save discovered links (accepts typed objects or dicts)"""
        # Convert to dicts if needed
        if links and isinstance(links[0], DiscoveredLink):
            links = links_to_dicts(links)

        data = {
            'version': '1.0',
            'last_updated': self._get_timestamp(),
            'total_links': len(links),
            'discovered_links': links
        }
        self._save_yaml(self.links_file, data)

    def add_links(self, new_links: Union[List[DiscoveredLink], List[Dict]]):
        """Add links (no duplicates by url+source_url combination)"""
        # Convert to dicts if needed
        if new_links and isinstance(new_links[0], DiscoveredLink):
            new_links = links_to_dicts(new_links)

        links = self.load_links()
        existing = {(link['url'], link['source_url']) for link in links}

        for link in new_links:
            key = (link['url'], link['source_url'])
            if key not in existing:
                links.append(link)
                existing.add(key)

        self.save_links(links)

    def get_all_discovered_urls(self) -> set:
        """Get set of all discovered URLs from links"""
        links = self.load_links()
        return {link['url'] for link in links}

    # ========== Queue Operations ==========

    def load_queue(self) -> List[Dict]:
        """Load scrape queue as dicts"""
        data = self._load_yaml(self.queue_file)
        queue = data.get('queue', [])
        return [item for item in queue if item]  # Filter out None/empty

    def load_queue_typed(self) -> List[QueueEntry]:
        """Load scrape queue as typed objects"""
        return queue_entries_from_dicts(self.load_queue())

    def save_queue(self, queue: Union[List[QueueEntry], List[Dict]]):
        """Save scrape queue (accepts typed objects or dicts)"""
        # Convert to dicts if needed
        if queue and isinstance(queue[0], QueueEntry):
            queue = queue_entries_to_dicts(queue)

        data = {'queue': queue}
        self._save_yaml(self.queue_file, data)

    def add_to_queue(self, entries: Union[List[QueueEntry], List[Dict]]):
        """Add entries to queue (no duplicates by URL)"""
        # Convert to dicts if needed
        if entries and isinstance(entries[0], QueueEntry):
            entries = queue_entries_to_dicts(entries)

        queue = self.load_queue()
        existing_urls = {entry['url'] for entry in queue}

        for entry in entries:
            if entry['url'] not in existing_urls:
                queue.append(entry)
                existing_urls.add(entry['url'])

        self.save_queue(queue)

    def is_queued(self, url: str) -> bool:
        """Check if URL is in queue"""
        queue = self.load_queue()
        return any(entry['url'] == url for entry in queue)

    def remove_from_queue(self, urls: List[str]):
        """Remove URLs from queue"""
        queue = self.load_queue()
        queue = [entry for entry in queue if entry['url'] not in urls]
        self.save_queue(queue)

    def clear_queue(self):
        """Clear entire queue"""
        self.save_queue([])

    # ========== Results Operations ==========

    def load_results(self) -> List[Dict]:
        """Load scrape results as dicts"""
        data = self._load_yaml(self.results_file)
        return data.get('scraped', [])

    def load_results_typed(self) -> List[ScrapeResult]:
        """Load scrape results as typed objects"""
        return results_from_dicts(self.load_results())

    def save_results(self, results: Union[List[ScrapeResult], List[Dict]]):
        """Save scrape results (accepts typed objects or dicts)"""
        # Convert to dicts if needed
        if results and isinstance(results[0], ScrapeResult):
            results = results_to_dicts(results)

        data = {
            'version': '1.0',
            'last_updated': self._get_timestamp(),
            'scraped': results
        }
        self._save_yaml(self.results_file, data)

    def add_results(self, new_results: Union[List[ScrapeResult], List[Dict]]):
        """Append new results to existing results"""
        # Convert to dicts if needed
        if new_results and isinstance(new_results[0], ScrapeResult):
            new_results = results_to_dicts(new_results)

        results = self.load_results()
        results.extend(new_results)
        self.save_results(results)

    # ========== Suggestions Operations ==========

    def load_suggestions(self) -> List[Dict]:
        """Load suggestions as dicts"""
        data = self._load_yaml(self.suggestions_file)
        return data.get('suggestions', [])

    def load_suggestions_typed(self) -> List[Suggestion]:
        """Load suggestions as typed objects"""
        return suggestions_from_dicts(self.load_suggestions())

    def save_suggestions(self, suggestions: Union[List[Suggestion], List[Dict]]):
        """Save suggestions (accepts typed objects or dicts)"""
        # Convert to dicts if needed
        if suggestions and isinstance(suggestions[0], Suggestion):
            suggestions = suggestions_to_dicts(suggestions)

        data = {
            'version': '1.0',
            'last_generated': self._get_timestamp(),
            'suggestions': suggestions
        }
        self._save_yaml(self.suggestions_file, data)

    def add_suggestions(self, new_suggestions: Union[List[Suggestion], List[Dict]]):
        """Add suggestions (no duplicates by URL)"""
        # Convert to dicts if needed
        if new_suggestions and isinstance(new_suggestions[0], Suggestion):
            new_suggestions = suggestions_to_dicts(new_suggestions)

        suggestions = self.load_suggestions()
        existing_urls = {s['url'] for s in suggestions}

        for suggestion in new_suggestions:
            if suggestion['url'] not in existing_urls:
                suggestions.append(suggestion)
                existing_urls.add(suggestion['url'])

        self.save_suggestions(suggestions)

    def is_suggested(self, url: str) -> bool:
        """Check if URL is in suggestions"""
        suggestions = self.load_suggestions()
        return any(s['url'] == url for s in suggestions)

    def remove_from_suggestions(self, urls: List[str]):
        """Remove URLs from suggestions"""
        suggestions = self.load_suggestions()
        suggestions = [s for s in suggestions if s['url'] not in urls]
        self.save_suggestions(suggestions)

    def clear_suggestions(self):
        """Clear all suggestions"""
        self.save_suggestions([])

    # ========== Combined Queries ==========

    def is_url_known(self, url: str) -> bool:
        """Check if URL exists in index, queue, or suggestions"""
        return self.is_indexed(url) or self.is_queued(url) or self.is_suggested(url)

    def get_all_known_urls(self) -> set:
        """Get all URLs from index, queue, and suggestions"""
        urls = set()

        # From index
        index = self.load_index()
        urls.update(entry['url'] for entry in index)

        # From queue
        queue = self.load_queue()
        urls.update(entry['url'] for entry in queue)

        # From suggestions
        suggestions = self.load_suggestions()
        urls.update(s['url'] for s in suggestions)

        return urls

    # ========== Reset Operations ==========

    def reset_all(self, include_queue: bool = True):
        """Reset all data files"""
        # Reset index
        self.save_index([])

        # Reset links
        self.save_links([])

        # Reset results
        self.save_results([])

        # Reset suggestions
        self.clear_suggestions()

        # Reset queue if requested
        if include_queue:
            self.clear_queue()

    # ========== Statistics ==========

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about all data files"""
        index = self.load_index()
        links = self.load_links()
        queue = self.load_queue()
        results = self.load_results()
        suggestions = self.load_suggestions()

        # Count by bounty
        bounty_counts = {}
        for entry in index:
            bid = entry.get('bounty_id', 'unknown')
            bounty_counts[bid] = bounty_counts.get(bid, 0) + 1

        return {
            'index': {
                'total': len(index),
                'by_bounty': bounty_counts
            },
            'links': {
                'total': len(links)
            },
            'queue': {
                'total': len(queue)
            },
            'results': {
                'total': len(results)
            },
            'suggestions': {
                'total': len(suggestions)
            }
        }
