#!/usr/bin/env python3
"""
Polkadot Bounty Archive - Cleanup & Reset Tool

Manage the scraping index and data files for fresh starts and augmentary runs.
"""

from pathlib import Path
from typing import Optional
import sys

from data import ScrapeData


class CleanupTool:
    """Tool for managing scraping index and resetting data"""

    def __init__(self, scraping_dir: Path):
        self.scraping_dir = scraping_dir.resolve()
        self.project_root = self.scraping_dir.parent
        self.bounties_dir = self.project_root / "bounties"
        self.data = ScrapeData(scraping_dir)

    def show_index_stats(self):
        """Show statistics about the current index"""
        print("\n" + "=" * 60)
        print("SCRAPING STATISTICS")
        print("=" * 60)

        stats = self.data.get_stats()

        # Index stats
        index_stats = stats['index']
        if index_stats['total'] == 0:
            print("\nIndex is empty.")
        else:
            print(f"\nIndexed URLs: {index_stats['total']}")
            print(f"Bounties with scraped content: {len(index_stats['by_bounty'])}")
            print(f"\nBreakdown by bounty:")
            for bounty_id in sorted(index_stats['by_bounty'].keys()):
                count = index_stats['by_bounty'][bounty_id]
                print(f"  Bounty #{bounty_id}: {count} URL(s)")

        # Other stats
        print(f"\nQueue: {stats['queue']['total']} URL(s)")
        print(f"Suggestions: {stats['suggestions']['total']} URL(s)")
        print(f"Discovered links: {stats['links']['total']} link(s)")
        print(f"Results: {stats['results']['total']} scrape(s)")

        print("=" * 60)

    def reset_all(self, confirm: bool = False, delete_files: bool = False):
        """Reset all auto-generated files for a fresh start

        Args:
            confirm: Skip confirmation prompt if True
            delete_files: Also delete scraped files in bounties/*/scraped/
        """
        if not confirm:
            if delete_files:
                print("\n[!] DANGER: Complete reset requested!")
            else:
                print("\n[!] WARNING: This will reset scraping data!")

            print("\nThis will clear:")
            print("  - scrape-index.yml (all indexed URLs)")
            print("  - scrape-results.yml (all scraping results)")
            print("  - scrape-links.yml (all discovered links)")
            print("  - scrape-suggestions.yml (all pending suggestions)")
            print("  - scrape-queue.yml (your queue)")

            if delete_files:
                print("  - bounties/*/scraped/ directories (ALL SCRAPED FILES)")

            print("\nThis will NOT delete:")
            if not delete_files:
                print("  - Scraped files in bounties/*/scraped/")
            print("  - scrape-config.yml (your configuration)")

            if delete_files:
                print("\n[!] THIS CANNOT BE UNDONE!")
                response = input("\nType 'DELETE EVERYTHING' to confirm: ").strip()
                if response != 'DELETE EVERYTHING':
                    print("Cancelled.")
                    return
            else:
                response = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()
                if response != 'yes':
                    print("Cancelled.")
                    return

        # Reset all data files using data manager
        self.data.reset_all(include_queue=True)
        print(f"[+] Reset scrape-index.yml")
        print(f"[+] Reset scrape-results.yml")
        print(f"[+] Reset scrape-links.yml")
        print(f"[+] Reset scrape-suggestions.yml")
        print(f"[+] Reset scrape-queue.yml")

        # Delete scraped files if requested
        if delete_files:
            print("\n[+] Deleting scraped files...")
            deleted_count = self.delete_scraped_files()
            print(f"[+] Deleted {deleted_count} scraped directories")

        print("\n[+] Reset complete!")
        print("\nTo start fresh, run:")
        print("  1. python suggest.py")
        print("  2. python review.py")
        print("  3. python scraper.py")

    def remove_from_index(self, url: Optional[str] = None, bounty_id: Optional[int] = None):
        """Remove specific URL(s) from the index"""
        if not url and not bounty_id:
            print("Error: Must specify either --url or --bounty-id")
            return

        # Get URLs before removal for display
        index = self.data.load_index()
        if not index:
            print("Index is empty, nothing to remove.")
            return

        removed_urls = [
            entry['url'] for entry in index
            if (url and entry.get('url') == url) or
               (bounty_id and entry.get('bounty_id') == bounty_id)
        ]

        # Remove from index
        removed_count = self.data.remove_from_index(url=url, bounty_id=bounty_id)

        print(f"\n[+] Removed {removed_count} URL(s) from index:")
        for removed_url in removed_urls[:10]:
            print(f"  - {removed_url}")
        if len(removed_urls) > 10:
            print(f"  ... and {len(removed_urls) - 10} more")

        print(f"\nThese URLs can now be re-scraped.")
        print("Add them to scrape-queue.yml to scrape them again.")

    def clear_suggestions(self):
        """Clear the suggestions file"""
        self.data.clear_suggestions()
        print(f"\n[+] Cleared scrape-suggestions.yml")

    def clear_queue(self):
        """Clear the queue file"""
        print("\n[!] WARNING: This will clear your scrape queue!")
        response = input("Are you sure? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Cancelled.")
            return

        self.data.clear_queue()
        print(f"\n[+] Cleared scrape-queue.yml")

    def delete_scraped_files(self):
        """Delete all scraped files in bounties/*/scraped/ directories"""
        import shutil

        if not self.bounties_dir.exists():
            print(f"  [!] Bounties directory not found: {self.bounties_dir}")
            return 0

        deleted_count = 0

        for bounty_dir in self.bounties_dir.iterdir():
            if not bounty_dir.is_dir():
                continue

            scraped_dir = bounty_dir / "scraped"
            if scraped_dir.exists() and scraped_dir.is_dir():
                # Delete the entire scraped directory
                shutil.rmtree(scraped_dir)
                deleted_count += 1
                print(f"  [+] Deleted {scraped_dir.relative_to(self.project_root)}")

        return deleted_count


def print_usage():
    """Print usage information"""
    print("""
Polkadot Bounty Archive - Cleanup & Reset Tool

Usage:
  python cleanup.py <command> [options]

Commands:
  stats                    Show index statistics
  reset-all                Reset all scraping data (index/results/links/suggestions/queue)
  reset-all --files        Also delete all scraped files (DANGER!)
  remove-url <url>         Remove specific URL from index (for re-scraping)
  remove-bounty <id>       Remove all URLs for a bounty from index
  clear-suggestions        Clear suggestions file only
  clear-queue              Clear scrape queue only (WARNING: destructive)

Examples:
  # Show current index stats
  python cleanup.py stats

  # Reset all scraping data (keeps scraped files)
  python cleanup.py reset-all

  # Complete reset: delete EVERYTHING including scraped files (DANGER!)
  python cleanup.py reset-all --files

  # Remove a specific URL to re-scrape it recursively
  python cleanup.py remove-url "https://polkadot.antiscam.team/"

  # Remove all scraped content for bounty #11
  python cleanup.py remove-bounty 11

  # Clear pending suggestions
  python cleanup.py clear-suggestions

Use Cases:
  1. Fresh Start: python cleanup.py reset-all
  2. Complete Wipe: python cleanup.py reset-all --files
  3. Re-scrape deeper: python cleanup.py remove-url <url>, then add to queue with recursive mode
  4. Re-scrape bounty: python cleanup.py remove-bounty <id>, then re-generate suggestions
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
        # Check for --files flag
        delete_files = False

        if len(sys.argv) > 2:
            flags = [arg.lower() for arg in sys.argv[2:]]
            if '--files' in flags:
                delete_files = True

        tool.reset_all(delete_files=delete_files)

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
