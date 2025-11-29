#!/usr/bin/env python3
"""
Polkadot Bounty Archive - Link Discovery

Reads scrape-links.yml and generates new scraping suggestions by filtering out
already-scraped, queued, ignored, and suggested URLs.
"""

import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set
from urllib.parse import urlparse


class LinkDiscoverer:
    """Discovers new URLs to scrape from extracted links"""

    def __init__(self, scraping_dir: Path):
        self.scraping_dir = scraping_dir
        self.links_file = scraping_dir / "scrape-links.yml"
        self.index_file = scraping_dir / "scrape-index.yml"
        self.queue_file = scraping_dir / "scrape-queue.yml"
        self.ignore_file = scraping_dir / "scrape-ignore.yml"
        self.suggestions_file = scraping_dir / "scrape-suggestions.yml"
        self.config_file = scraping_dir / "scrape-config.yml"

        # Load configuration
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """Load scraping configuration"""
        if not self.config_file.exists():
            print(f"Warning: Config file not found: {self.config_file}")
            return {}

        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config or {}

    def load_discovered_links(self) -> List[Dict]:
        """Load all discovered links from scrape-links.yml"""
        if not self.links_file.exists():
            print(f"No links file found: {self.links_file}")
            return []

        with open(self.links_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or 'discovered_links' not in data:
            return []

        return data['discovered_links']

    def load_indexed_urls(self) -> Set[str]:
        """Load URLs that have already been scraped"""
        if not self.index_file.exists():
            return set()

        with open(self.index_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or 'index' not in data:
            return set()

        return {item['url'] for item in data['index']}

    def load_queued_urls(self) -> Set[str]:
        """Load URLs that are in the scraping queue"""
        if not self.queue_file.exists():
            return set()

        with open(self.queue_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or 'queue' not in data or data['queue'] is None:
            return set()

        return {item['url'] for item in data['queue']}

    def load_ignored_urls(self) -> Set[str]:
        """Load URLs that should be ignored"""
        if not self.ignore_file.exists():
            return set()

        with open(self.ignore_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or 'ignored' not in data:
            return set()

        ignored = set()
        for item in data['ignored']:
            url = item.get('url', '')
            # Handle wildcard patterns
            if url:
                ignored.add(url)

        return ignored

    def load_suggested_urls(self) -> Set[str]:
        """Load URLs that have already been suggested"""
        if not self.suggestions_file.exists():
            return set()

        with open(self.suggestions_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or 'suggestions' not in data:
            return set()

        return {item['url'] for item in data['suggestions']}

    def is_ignored(self, url: str, ignored_patterns: Set[str]) -> bool:
        """Check if URL matches any ignore pattern"""
        parsed = urlparse(url)
        domain = parsed.netloc

        for pattern in ignored_patterns:
            # Exact URL match
            if url == pattern or url.rstrip('/') == pattern.rstrip('/'):
                return True

            # Domain pattern match
            if pattern in domain:
                return True

        return False

    def discover_new_urls(self) -> List[Dict]:
        """Discover new URLs by filtering discovered links"""
        print("=" * 60)
        print("Polkadot Bounty Archive - Link Discovery")
        print("=" * 60)

        # Load discovered links
        discovered_links = self.load_discovered_links()
        print(f"\nTotal discovered links: {len(discovered_links)}")

        if not discovered_links:
            print("No discovered links found. Run scraper.py first.")
            return []

        # Load existing URLs to filter out
        indexed = self.load_indexed_urls()
        queued = self.load_queued_urls()
        ignored_patterns = self.load_ignored_urls()
        suggested = self.load_suggested_urls()

        print(f"Already scraped: {len(indexed)}")
        print(f"Already queued: {len(queued)}")
        print(f"Ignore patterns: {len(ignored_patterns)}")
        print(f"Already suggested: {len(suggested)}")

        # Filter to find new URLs
        new_suggestions = []
        seen_urls = set()

        for link in discovered_links:
            url = link['url']

            # Skip if already seen in this discovery run
            if url in seen_urls:
                continue

            # Skip if already scraped, queued, or suggested
            if url in indexed or url in queued or url in suggested:
                continue

            # Skip if matches ignore pattern
            if self.is_ignored(url, ignored_patterns):
                continue

            # This is a new URL!
            seen_urls.add(url)

            # Determine type based on categories
            categories = link.get('categories', ['other'])

            # Associated socials (not scraped, added to metadata)
            social_categories = {'social', 'discord', 'telegram', 'matrix'}
            is_social = bool(set(categories) & social_categories)

            # Associated URLs (not scraped, added to metadata)
            associated_categories = {'github'}
            is_associated = bool(set(categories) & associated_categories)

            # Everything else gets scraped
            if is_social:
                suggestion_type = 'social'
            elif is_associated:
                suggestion_type = 'associated_url'
            else:
                suggestion_type = 'scrape'

            # Get default mode from config (only used for scrape type)
            default_mode = self.config.get('default_mode', 'single')
            default_depth = 1
            if default_mode == 'recursive':
                default_depth = self.config.get('recursive_defaults', {}).get('max_depth', 2)

            suggestion = {
                'url': url,
                'bounty_id': link['bounty_id'],
                'mode': default_mode,
                'max_depth': default_depth,
                'source': f"discovered from {link['source_url']}",
                'categories': categories,
                'discovered_at': link.get('discovered_at', ''),
                'type': suggestion_type
            }

            new_suggestions.append(suggestion)

        print(f"\n{Fore.GREEN}New URLs discovered: {len(new_suggestions)}{Style.RESET_ALL}" if len(new_suggestions) > 0 else f"\nNew URLs discovered: {len(new_suggestions)}")

        return new_suggestions

    def save_suggestions(self, new_suggestions: List[Dict]):
        """Append new suggestions to scrape-suggestions.yml"""
        if not new_suggestions:
            print("\nNo new suggestions to save.")
            return

        # Load existing suggestions
        if self.suggestions_file.exists():
            with open(self.suggestions_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}

        # Initialize structure
        if 'suggestions' not in data or data['suggestions'] is None:
            data['suggestions'] = []

        # Add new suggestions
        data['suggestions'].extend(new_suggestions)

        # Update metadata
        data['version'] = "1.0"
        data['last_generated'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        # Save suggestions
        with open(self.suggestions_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"\nSuggestions saved to: {self.suggestions_file}")
        print(f"Run review.py to review and approve suggestions.")

    def run(self):
        """Main execution"""
        new_suggestions = self.discover_new_urls()

        if new_suggestions:
            # Show sample of discovered URLs
            print(f"\nSample of discovered URLs:")
            for suggestion in new_suggestions[:10]:
                categories_str = ', '.join(suggestion['categories'])
                print(f"  - {suggestion['url']}")
                print(f"    Bounty #{suggestion['bounty_id']} | Categories: {categories_str}")

            if len(new_suggestions) > 10:
                print(f"  ... and {len(new_suggestions) - 10} more")

        self.save_suggestions(new_suggestions)

        print("\n" + "=" * 60)


# Colorama for colored output (optional)
try:
    from colorama import Fore, Style
except ImportError:
    class Fore:
        GREEN = ""
    class Style:
        RESET_ALL = ""


def main():
    """CLI entry point"""
    script_dir = Path(__file__).parent
    discoverer = LinkDiscoverer(script_dir)
    discoverer.run()


if __name__ == "__main__":
    main()
