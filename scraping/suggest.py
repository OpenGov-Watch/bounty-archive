#!/usr/bin/env python3
"""
Polkadot Bounty Archive - URL Suggestion Generator

Generates scraping suggestions from two sources:
1. Bounty metadata files (--source=metadata, default)
2. Discovered links from scraped pages (--source=links)

All suggestions include categories and type classification.
"""

import argparse
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set

from config import ScrapeConfig


class SuggestionGenerator:
    """Generates scraping suggestions from metadata or discovered links"""

    def __init__(self, project_root: Path, config: ScrapeConfig):
        self.project_root = project_root
        self.config = config
        self.bounties_dir = project_root / "bounties"
        self.scraping_dir = project_root / "scraping"
        self.queue_file = self.scraping_dir / "scrape-queue.yml"
        self.index_file = self.scraping_dir / "scrape-index.yml"
        self.suggestions_file = self.scraping_dir / "scrape-suggestions.yml"
        self.links_file = self.scraping_dir / "scrape-links.yml"

    def load_yaml_file(self, file_path: Path) -> Dict:
        """Load and parse YAML file"""
        if not file_path.exists():
            return {}

        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data is not None else {}

    def get_all_processed_urls(self) -> Set[str]:
        """Get all URLs that have been queued, indexed, or suggested"""
        urls = set()

        # From queue
        queue_data = self.load_yaml_file(self.queue_file)
        queue = queue_data.get('queue', [])
        if queue:
            urls.update(item['url'] for item in queue if item and 'url' in item)

        # From index
        index_data = self.load_yaml_file(self.index_file)
        index = index_data.get('index', [])
        if index:
            urls.update(item['url'] for item in index if item and 'url' in item)

        # From existing suggestions
        suggestions_data = self.load_yaml_file(self.suggestions_file)
        suggestions = suggestions_data.get('suggestions', [])
        if suggestions:
            urls.update(item['url'] for item in suggestions if item and 'url' in item)

        # From ignored list (in config)
        for ignored_item in self.config.ignored_urls:
            if isinstance(ignored_item, dict):
                urls.add(ignored_item.get('url', ''))
            elif isinstance(ignored_item, str):
                urls.add(ignored_item)

        return urls

    def extract_urls_from_metadata(self, metadata_file: Path, bounty_id: int) -> List[Dict]:
        """Extract URLs from a bounty metadata file with categorization"""
        metadata = self.load_yaml_file(metadata_file)
        suggestions = []

        if not metadata or 'links' not in metadata:
            return suggestions

        links = metadata['links']
        if not links:
            return suggestions

        # Extract URLs from all fields in links section
        for field, url in links.items():
            # Skip excluded fields
            if field in ['subsquare', 'polkassembly', 'forum', 'spreadsheet']:
                continue

            if url and isinstance(url, str) and url.startswith('http'):
                # Check if ignored
                is_ignored, reason = self.config.is_ignored(url)
                if not is_ignored:
                    mode, max_depth = self.config.get_default_mode_settings()
                    categories = self.config.categorize_url(url)
                    suggestion_type = self.config.get_suggestion_type(categories)

                    suggestions.append({
                        'bounty_id': bounty_id,
                        'url': url,
                        'mode': mode,
                        'max_depth': max_depth,
                        'source': f'metadata.links.{field}',
                        'categories': categories,
                        'type': suggestion_type,
                        'discovered_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                    })

        # Also check contact.applicationForm
        if 'contact' in metadata and metadata['contact']:
            contact = metadata['contact']
            app_form = contact.get('applicationForm')
            if app_form and isinstance(app_form, str) and app_form.startswith('http'):
                # Check if ignored
                is_ignored, reason = self.config.is_ignored(app_form)
                if not is_ignored:
                    mode, max_depth = self.config.get_default_mode_settings()
                    categories = self.config.categorize_url(app_form)
                    suggestion_type = self.config.get_suggestion_type(categories)

                    suggestions.append({
                        'bounty_id': bounty_id,
                        'url': app_form,
                        'mode': mode,
                        'max_depth': max_depth,
                        'source': 'metadata.contact.applicationForm',
                        'categories': categories,
                        'type': suggestion_type,
                        'discovered_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                    })

        return suggestions

    def generate_from_metadata(self) -> List[Dict]:
        """Generate suggestions from all bounty metadata files"""
        print("=" * 60)
        print("Polkadot Bounty Archive - Suggestion Generator (Metadata)")
        print("=" * 60)

        # Get all processed URLs
        print("\nLoading processed URLs...")
        processed_urls = self.get_all_processed_urls()
        print(f"  Found {len(processed_urls)} already processed URLs")

        # Find all bounty directories
        bounty_dirs = sorted([d for d in self.bounties_dir.iterdir() if d.is_dir()])
        print(f"\nScanning {len(bounty_dirs)} bounty directories...")

        all_suggestions = []
        stats = {
            'scanned': 0,
            'urls_found': 0,
            'already_processed': 0,
            'new_suggestions': 0
        }

        for bounty_dir in bounty_dirs:
            metadata_file = bounty_dir / 'metadata.yml'
            if not metadata_file.exists():
                continue

            stats['scanned'] += 1

            # Extract bounty ID from directory name
            try:
                bounty_id = int(bounty_dir.name.split('-')[0])
            except (ValueError, IndexError):
                print(f"  Warning: Could not parse bounty ID from {bounty_dir.name}")
                continue

            # Extract URLs from metadata
            suggestions = self.extract_urls_from_metadata(metadata_file, bounty_id)
            stats['urls_found'] += len(suggestions)

            # Filter suggestions
            for suggestion in suggestions:
                url = suggestion['url']

                # Skip already processed URLs
                if url in processed_urls:
                    stats['already_processed'] += 1
                    continue

                # Add to suggestions
                all_suggestions.append(suggestion)
                stats['new_suggestions'] += 1

        self._print_stats(stats, "metadata")
        return all_suggestions

    def generate_from_links(self) -> List[Dict]:
        """Generate suggestions from discovered links"""
        print("=" * 60)
        print("Polkadot Bounty Archive - Suggestion Generator (Links)")
        print("=" * 60)

        # Load discovered links
        links_data = self.load_yaml_file(self.links_file)
        discovered_links = links_data.get('discovered_links', [])

        print(f"\nTotal discovered links: {len(discovered_links)}")

        if not discovered_links:
            print("No discovered links found. Run scraper.py first.")
            return []

        # Get all processed URLs
        processed_urls = self.get_all_processed_urls()

        print(f"Already processed: {len(processed_urls)}")

        # Filter to find new URLs
        new_suggestions = []
        seen_urls = set()

        for link in discovered_links:
            url = link['url']

            # Skip if already seen in this run
            if url in seen_urls:
                continue

            # Skip if already processed
            if url in processed_urls:
                continue

            # Check if ignored
            is_ignored, reason = self.config.is_ignored(url)
            if is_ignored:
                continue

            # This is a new URL!
            seen_urls.add(url)

            # Get categories (from link or categorize)
            categories = link.get('categories', [])
            if not categories:
                categories = self.config.categorize_url(url)

            # Determine type
            suggestion_type = self.config.get_suggestion_type(categories)

            # Get default mode
            mode, max_depth = self.config.get_default_mode_settings()

            suggestion = {
                'url': url,
                'bounty_id': link['bounty_id'],
                'mode': mode,
                'max_depth': max_depth,
                'source': f"discovered from {link['source_url']}",
                'categories': categories,
                'discovered_at': link.get('discovered_at', datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
                'type': suggestion_type
            }

            new_suggestions.append(suggestion)

        print(f"\nNew URLs discovered: {len(new_suggestions)}")

        return new_suggestions

    def save_suggestions(self, new_suggestions: List[Dict]):
        """Save suggestions to scrape-suggestions.yml"""
        if not new_suggestions:
            print("\nNo new suggestions to add.")
            return

        # Load existing suggestions
        existing_suggestions_data = self.load_yaml_file(self.suggestions_file)
        existing_suggestions = existing_suggestions_data.get('suggestions', [])
        if existing_suggestions is None:
            existing_suggestions = []

        # Get existing URLs to avoid duplicates
        existing_urls = {s['url'] for s in existing_suggestions if s and 'url' in s}

        # Add only new suggestions
        added_count = 0
        for suggestion in new_suggestions:
            if suggestion['url'] not in existing_urls:
                existing_suggestions.append(suggestion)
                added_count += 1

        # Save merged suggestions
        suggestions_data = {
            'version': "1.0",
            'last_generated': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'suggestions': existing_suggestions
        }

        with open(self.suggestions_file, 'w', encoding='utf-8') as f:
            yaml.dump(suggestions_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        if added_count > 0:
            print(f"\n{added_count} new suggestions added to: {self.suggestions_file.relative_to(self.project_root)}")
        else:
            print(f"\nAll suggestions already exist in {self.suggestions_file.relative_to(self.project_root)}")

    def _print_stats(self, stats: Dict, source: str):
        """Print statistics"""
        print("\n" + "=" * 60)
        print("STATISTICS")
        print("=" * 60)
        if source == "metadata":
            print(f"Bounties scanned: {stats['scanned']}")
        print(f"URLs found: {stats['urls_found']}")
        print(f"  Already processed: {stats['already_processed']}")
        print(f"  New suggestions: {stats['new_suggestions']}")
        print("=" * 60)

        if stats['new_suggestions'] > 0:
            print(f"\nNext step: Run 'python review.py' to review suggestions")
        print("=" * 60)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate scraping suggestions from metadata or discovered links"
    )
    parser.add_argument(
        '--source',
        choices=['metadata', 'links'],
        default='metadata',
        help='Source for suggestions: metadata (default) or links'
    )

    args = parser.parse_args()

    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Load configuration
    config_file = script_dir / "scrape-config.yml"
    config = ScrapeConfig(config_file)

    # Create generator
    generator = SuggestionGenerator(project_root, config)

    # Generate suggestions based on source
    if args.source == 'metadata':
        suggestions = generator.generate_from_metadata()
    else:
        suggestions = generator.generate_from_links()

    # Save suggestions
    generator.save_suggestions(suggestions)


if __name__ == "__main__":
    main()
