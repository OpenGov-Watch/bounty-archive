#!/usr/bin/env python3
"""
Polkadot Bounty Archive - Cleanup & Reset Tool

Manage the scraping index and data files for fresh starts and augmentary runs.
"""

import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional
import sys


class CleanupTool:
    """Tool for managing scraping index and resetting data"""

    def __init__(self, scraping_dir: Path):
        self.scraping_dir = scraping_dir
        self.index_file = scraping_dir / "scrape-index.yml"
        self.results_file = scraping_dir / "scrape-results.yml"
        self.links_file = scraping_dir / "scrape-links.yml"
        self.suggestions_file = scraping_dir / "scrape-suggestions.yml"
        self.queue_file = scraping_dir / "scrape-queue.yml"

    def load_yaml_file(self, file_path: Path):
        """Load YAML file"""
        if not file_path.exists():
            return {}

        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def save_yaml_file(self, file_path: Path, data: dict):
        """Save YAML file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def show_index_stats(self):
        """Show statistics about the current index"""
        print("\n" + "=" * 60)
        print("INDEX STATISTICS")
        print("=" * 60)

        index_data = self.load_yaml_file(self.index_file)
        index = index_data.get('index', [])

        if not index:
            print("Index is empty.")
            return

        # Count by bounty
        bounty_counts = {}
        for entry in index:
            bounty_id = entry.get('bounty_id', 'unknown')
            bounty_counts[bounty_id] = bounty_counts.get(bounty_id, 0) + 1

        print(f"\nTotal indexed URLs: {len(index)}")
        print(f"Bounties with scraped content: {len(bounty_counts)}")
        print(f"\nBreakdown by bounty:")
        for bounty_id in sorted(bounty_counts.keys()):
            count = bounty_counts[bounty_id]
            print(f"  Bounty #{bounty_id}: {count} URL(s)")

        print(f"\nLast updated: {index_data.get('last_updated', 'Unknown')}")
        print("=" * 60)

    def reset_all(self, confirm: bool = False):
        """Reset all auto-generated files for a fresh start"""
        if not confirm:
            print("\n⚠️  WARNING: This will reset ALL scraping data!")
            print("\nThis will clear:")
            print("  - scrape-index.yml (all indexed URLs)")
            print("  - scrape-results.yml (all scraping results)")
            print("  - scrape-links.yml (all discovered links)")
            print("  - scrape-suggestions.yml (all pending suggestions)")
            print("\nThis will NOT delete:")
            print("  - Scraped files in bounties/*/scraped/")
            print("  - scrape-queue.yml (your queue)")
            print("  - scrape-ignore.yml (your ignore list)")
            print("  - scrape-config.yml (your configuration)")

            response = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Cancelled.")
                return

        # Reset index
        index_data = {
            'version': '1.0',
            'last_updated': None,
            'index': []
        }
        self.save_yaml_file(self.index_file, index_data)
        print(f"✓ Reset {self.index_file.name}")

        # Reset results
        results_data = {
            'version': '1.0',
            'last_updated': None,
            'scraped': []
        }
        self.save_yaml_file(self.results_file, results_data)
        print(f"✓ Reset {self.results_file.name}")

        # Reset links
        links_data = {
            'version': '1.0',
            'last_updated': None,
            'total_links': 0,
            'discovered_links': []
        }
        self.save_yaml_file(self.links_file, links_data)
        print(f"✓ Reset {self.links_file.name}")

        # Reset suggestions
        suggestions_data = {
            'version': '1.0',
            'last_generated': None,
            'suggestions': []
        }
        self.save_yaml_file(self.suggestions_file, suggestions_data)
        print(f"✓ Reset {self.suggestions_file.name}")

        print("\n✅ All auto-generated files have been reset.")
        print("\nTo start fresh, run:")
        print("  1. python suggest.py")
        print("  2. python review.py")
        print("  3. python scraper.py")

    def remove_from_index(self, url: Optional[str] = None, bounty_id: Optional[int] = None):
        """Remove specific URL(s) from the index"""
        if not url and not bounty_id:
            print("Error: Must specify either --url or --bounty-id")
            return

        index_data = self.load_yaml_file(self.index_file)
        index = index_data.get('index', [])

        if not index:
            print("Index is empty, nothing to remove.")
            return

        original_count = len(index)
        removed_urls = []

        # Filter out matching entries
        new_index = []
        for entry in index:
            should_remove = False

            if url and entry.get('url') == url:
                should_remove = True
            if bounty_id and entry.get('bounty_id') == bounty_id:
                should_remove = True

            if should_remove:
                removed_urls.append(entry.get('url'))
            else:
                new_index.append(entry)

        # Update index
        index_data['index'] = new_index
        index_data['last_updated'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        self.save_yaml_file(self.index_file, index_data)

        removed_count = original_count - len(new_index)
        print(f"\n✓ Removed {removed_count} URL(s) from index:")
        for url in removed_urls[:10]:
            print(f"  - {url}")
        if len(removed_urls) > 10:
            print(f"  ... and {len(removed_urls) - 10} more")

        print(f"\nThese URLs can now be re-scraped.")
        print("Add them to scrape-queue.yml to scrape them again.")

    def clear_suggestions(self):
        """Clear the suggestions file"""
        suggestions_data = {
            'version': '1.0',
            'last_generated': None,
            'suggestions': []
        }
        self.save_yaml_file(self.suggestions_file, suggestions_data)
        print(f"\n✓ Cleared {self.suggestions_file.name}")

    def clear_queue(self):
        """Clear the queue file"""
        print("\n⚠️  WARNING: This will clear your scrape queue!")
        response = input("Are you sure? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Cancelled.")
            return

        queue_data = {
            'queue': []
        }
        self.save_yaml_file(self.queue_file, queue_data)
        print(f"\n✓ Cleared {self.queue_file.name}")


def print_usage():
    """Print usage information"""
    print("""
Polkadot Bounty Archive - Cleanup & Reset Tool

Usage:
  python cleanup.py <command> [options]

Commands:
  stats                    Show index statistics
  reset-all                Reset all auto-generated files (fresh start)
  remove-url <url>         Remove specific URL from index (for re-scraping)
  remove-bounty <id>       Remove all URLs for a bounty from index
  clear-suggestions        Clear suggestions file
  clear-queue              Clear scrape queue (WARNING: destructive)

Examples:
  # Show current index stats
  python cleanup.py stats

  # Reset everything for a fresh start
  python cleanup.py reset-all

  # Remove a specific URL to re-scrape it recursively
  python cleanup.py remove-url "https://polkadot.antiscam.team/"

  # Remove all scraped content for bounty #11
  python cleanup.py remove-bounty 11

  # Clear pending suggestions
  python cleanup.py clear-suggestions

Use Cases:
  1. Fresh Start: python cleanup.py reset-all
  2. Re-scrape deeper: python cleanup.py remove-url <url>, then add to queue with recursive mode
  3. Re-scrape bounty: python cleanup.py remove-bounty <id>, then re-generate suggestions
""")


def main():
    """CLI entry point"""
    script_dir = Path(__file__).parent
    tool = CleanupTool(script_dir)

    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()

    if command == "stats":
        tool.show_index_stats()

    elif command == "reset-all":
        tool.reset_all()

    elif command == "remove-url":
        if len(sys.argv) < 3:
            print("Error: Missing URL argument")
            print("Usage: python cleanup.py remove-url <url>")
            return
        url = sys.argv[2]
        tool.remove_from_index(url=url)

    elif command == "remove-bounty":
        if len(sys.argv) < 3:
            print("Error: Missing bounty ID argument")
            print("Usage: python cleanup.py remove-bounty <id>")
            return
        try:
            bounty_id = int(sys.argv[2])
            tool.remove_from_index(bounty_id=bounty_id)
        except ValueError:
            print("Error: Bounty ID must be a number")
            return

    elif command == "clear-suggestions":
        tool.clear_suggestions()

    elif command == "clear-queue":
        tool.clear_queue()

    else:
        print(f"Error: Unknown command '{command}'")
        print_usage()


if __name__ == "__main__":
    main()
