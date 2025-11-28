#!/usr/bin/env python3
"""
Polkadot Bounty Archive - URL Suggestion Generator

Extracts URLs from bounty metadata files and generates scraping suggestions.
Filters out social media, code repos, and already processed URLs.
"""

import os
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set
from urllib.parse import urlparse


class SuggestionGenerator:
    """Generates scraping suggestions from bounty metadata"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.bounties_dir = project_root / "bounties"
        self.scraping_dir = project_root / "scraping"
        self.queue_file = self.scraping_dir / "scrape-queue.yml"
        self.ignore_file = self.scraping_dir / "scrape-ignore.yml"
        self.index_file = self.scraping_dir / "scrape-index.yml"
        self.suggestions_file = self.scraping_dir / "scrape-suggestions.yml"
        self.config_file = self.scraping_dir / "scrape-config.yml"

        # Load configuration
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """Load scraping configuration"""
        if not self.config_file.exists():
            print(f"Error: Configuration file not found: {self.config_file}")
            print("Please create scrape-config.yml in the scraping directory.")
            print("See SCRAPING.md for the required format.")
            sys.exit(1)

        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if config is None:
                print(f"Error: Configuration file is empty: {self.config_file}")
                sys.exit(1)
            return config

    def load_yaml_file(self, file_path: Path) -> Dict:
        """Load and parse YAML file"""
        if not file_path.exists():
            return {}

        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data is not None else {}

    def get_all_processed_urls(self) -> Set[str]:
        """Get all URLs that have been queued, ignored, indexed, or suggested"""
        urls = set()

        # From queue
        queue_data = self.load_yaml_file(self.queue_file)
        queue = queue_data.get('queue', [])
        if queue:
            urls.update(item['url'] for item in queue if item and 'url' in item)

        # From ignore list
        ignore_data = self.load_yaml_file(self.ignore_file)
        ignored = ignore_data.get('ignored', [])
        if ignored:
            urls.update(item['url'] for item in ignored if item and 'url' in item)

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

        return urls

    def get_default_mode(self) -> tuple[str, int]:
        """Get default scraping mode from config"""
        mode = self.config.get('default_mode', 'single')
        if mode == 'recursive':
            max_depth = self.config.get('recursive_defaults', {}).get('max_depth', 2)
        else:
            max_depth = self.config.get('single_defaults', {}).get('max_depth', 1)
        return mode, max_depth

    def extract_urls_from_metadata(self, metadata_file: Path, bounty_id: int) -> List[Dict]:
        """Extract relevant URLs from a bounty metadata file"""
        metadata = self.load_yaml_file(metadata_file)
        suggestions = []

        if not metadata or 'links' not in metadata:
            return suggestions

        links = metadata['links']
        if not links:
            return suggestions

        # Extract URLs from all fields in links section
        for field, url in links.items():
            # Skip excluded fields (already filtered by domain exclusion later)
            if field in ['subsquare', 'polkassembly', 'forum', 'spreadsheet']:
                continue

            if url and isinstance(url, str) and url.startswith('http'):
                mode, max_depth = self.get_default_mode()
                suggestions.append({
                    'bounty_id': bounty_id,
                    'url': url,
                    'mode': mode,
                    'max_depth': max_depth,
                    'source': f'metadata.links.{field}'
                })

        # Also check contact.applicationForm
        if 'contact' in metadata and metadata['contact']:
            contact = metadata['contact']
            app_form = contact.get('applicationForm')
            if app_form and isinstance(app_form, str) and app_form.startswith('http'):
                mode, max_depth = self.get_default_mode()
                suggestions.append({
                    'bounty_id': bounty_id,
                    'url': app_form,
                    'mode': mode,
                    'max_depth': max_depth,
                    'source': 'metadata.contact.applicationForm'
                })

        return suggestions

    def generate_suggestions(self) -> List[Dict]:
        """Generate suggestions from all bounty metadata files"""
        print("=" * 60)
        print("Polkadot Bounty Archive - Suggestion Generator")
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

            # Extract bounty ID from directory name (e.g., "19-inkubator" -> 19)
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

                # Skip already processed URLs (in queue, ignore list, index, or suggestions)
                if url in processed_urls:
                    stats['already_processed'] += 1
                    continue

                # Add to suggestions
                all_suggestions.append(suggestion)
                stats['new_suggestions'] += 1

        # Save suggestions (merge with existing)
        if all_suggestions:
            # Load existing suggestions
            existing_suggestions_data = self.load_yaml_file(self.suggestions_file)
            existing_suggestions = existing_suggestions_data.get('suggestions', [])
            if existing_suggestions is None:
                existing_suggestions = []

            # Get existing URLs to avoid duplicates
            existing_urls = {s['url'] for s in existing_suggestions if s and 'url' in s}

            # Add only new suggestions (not already in the file)
            for suggestion in all_suggestions:
                if suggestion['url'] not in existing_urls:
                    existing_suggestions.append(suggestion)

            # Save merged suggestions
            suggestions_data = {
                'version': "1.0",
                'last_generated': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'suggestions': existing_suggestions
            }

            with open(self.suggestions_file, 'w', encoding='utf-8') as f:
                yaml.dump(suggestions_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            print(f"\n{stats['new_suggestions']} new suggestions added to: {self.suggestions_file.relative_to(self.project_root)}")
        else:
            print("\nNo new suggestions to add.")

        # Print statistics
        print("\n" + "=" * 60)
        print("STATISTICS")
        print("=" * 60)
        print(f"Bounties scanned: {stats['scanned']}")
        print(f"URLs found: {stats['urls_found']}")
        print(f"  Already processed: {stats['already_processed']}")
        print(f"  New suggestions: {stats['new_suggestions']}")
        print("=" * 60)

        return all_suggestions


def main():
    # Determine project root (parent of scraping directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    generator = SuggestionGenerator(project_root)
    generator.generate_suggestions()


if __name__ == "__main__":
    main()
