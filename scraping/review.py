#!/usr/bin/env python3
"""
Polkadot Bounty Archive - Suggestion Reviewer

Interactive CLI to review scraping suggestions.
Process suggestions by accepting, modifying, ignoring, or skipping them.
"""

import os
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse


class SuggestionReviewer:
    """Interactive reviewer for scraping suggestions"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.scraping_dir = project_root / "scraping"
        self.queue_file = self.scraping_dir / "scrape-queue.yml"
        self.ignore_file = self.scraping_dir / "scrape-ignore.yml"
        self.suggestions_file = self.scraping_dir / "scrape-suggestions.yml"
        self.config_file = self.scraping_dir / "scrape-config.yml"

        # Load configuration
        self.config = self.load_config()

        # Track changes
        self.accepted = []
        self.auto_accepted = []
        self.ignored = []
        self.modified = []

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

    def save_yaml_file(self, file_path: Path, data: Dict):
        """Save data to YAML file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def display_suggestion(self, suggestion: Dict, index: int, total: int):
        """Display a suggestion with formatting"""
        print("\n" + "=" * 60)
        print(f"SUGGESTION {index + 1} of {total}")
        print("=" * 60)
        print(f"Bounty ID:  {suggestion['bounty_id']}")
        print(f"URL:        {suggestion['url']}")
        print(f"Mode:       {suggestion['mode']}")
        print(f"Max Depth:  {suggestion.get('max_depth', 'N/A')}")
        print(f"Source:     {suggestion.get('source', 'Unknown')}")
        print("=" * 60)

    def get_user_choice(self) -> str:
        """Get user's choice for a suggestion"""
        while True:
            print("\nActions:")
            print("  [A] Accept - Add to scrape queue")
            print("  [M] Modify - Edit and add to queue")
            print("  [I] Ignore - Add to ignore list")
            print("  [S] Skip - Leave for later")
            print("  [Q] Quit - Exit reviewer")

            choice = input("\nYour choice: ").strip().upper()

            if choice in ['A', 'M', 'I', 'S', 'Q']:
                return choice

            print("Invalid choice. Please enter A, M, I, S, or Q.")

    def modify_suggestion(self, suggestion: Dict) -> Optional[Dict]:
        """Allow user to modify a suggestion"""
        print("\n" + "-" * 60)
        print("MODIFY SUGGESTION")
        print("-" * 60)
        print("Press Enter to keep current value, or type new value:")

        modified = suggestion.copy()

        # Bounty ID
        current = str(modified['bounty_id'])
        new_value = input(f"Bounty ID [{current}]: ").strip()
        if new_value:
            try:
                modified['bounty_id'] = int(new_value)
            except ValueError:
                print("Invalid bounty ID. Keeping current value.")

        # URL
        current = modified['url']
        new_value = input(f"URL [{current}]: ").strip()
        if new_value:
            modified['url'] = new_value

        # Mode
        current = modified['mode']
        while True:
            new_value = input(f"Mode (single/recursive) [{current}]: ").strip().lower()
            if not new_value:
                break
            if new_value in ['single', 'recursive']:
                modified['mode'] = new_value
                break
            print("Invalid mode. Must be 'single' or 'recursive'.")

        # Max Depth
        if modified['mode'] == 'recursive':
            current = str(modified.get('max_depth', 1))
            new_value = input(f"Max Depth [{current}]: ").strip()
            if new_value:
                try:
                    modified['max_depth'] = int(new_value)
                except ValueError:
                    print("Invalid depth. Keeping current value.")
        else:
            modified['max_depth'] = None

        # Confirm
        print("\n" + "-" * 60)
        print("Modified suggestion:")
        print(f"  Bounty ID:  {modified['bounty_id']}")
        print(f"  URL:        {modified['url']}")
        print(f"  Mode:       {modified['mode']}")
        print(f"  Max Depth:  {modified.get('max_depth', 'N/A')}")
        print("-" * 60)

        confirm = input("\nAccept these changes? [Y/n]: ").strip().lower()
        if confirm in ['', 'y', 'yes']:
            return modified
        return None

    def add_to_queue(self, suggestion: Dict):
        """Add suggestion to scrape queue"""
        queue_data = self.load_yaml_file(self.queue_file)

        # Initialize queue if needed
        if 'queue' not in queue_data or queue_data['queue'] is None:
            queue_data['queue'] = []

        # Prepare queue entry (remove source field)
        entry = {
            'bounty_id': suggestion['bounty_id'],
            'url': suggestion['url'],
            'mode': suggestion['mode']
        }

        # Only include max_depth for recursive mode
        if suggestion['mode'] == 'recursive' and suggestion.get('max_depth'):
            entry['max_depth'] = suggestion['max_depth']

        queue_data['queue'].append(entry)
        self.save_yaml_file(self.queue_file, queue_data)

    def add_to_ignore(self, suggestion: Dict, reason: Optional[str] = None):
        """Add suggestion to ignore list"""
        ignore_data = self.load_yaml_file(self.ignore_file)

        # Initialize ignored list if needed
        if 'ignored' not in ignore_data or ignore_data['ignored'] is None:
            ignore_data['ignored'] = []

        # Prepare ignore entry
        entry = {'url': suggestion['url']}
        if reason:
            entry['reason'] = reason

        ignore_data['ignored'].append(entry)
        self.save_yaml_file(self.ignore_file, ignore_data)

    def check_auto_accept(self, url: str) -> Optional[tuple[str, int]]:
        """Check if URL matches auto-accept rules. Returns (mode, max_depth) if matched, None otherwise"""
        auto_accept_rules = self.config.get('auto_accept', [])
        if not auto_accept_rules:
            return None

        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()

        for rule in auto_accept_rules:
            if not rule:
                continue

            rule_domain = rule.get('domain', '').lower()
            rule_path = rule.get('path', '').lower()

            # Check domain match (exact or subdomain)
            domain_match = domain == rule_domain or domain.endswith('.' + rule_domain)

            # Check path match if specified
            if rule_path:
                path_match = path.startswith(rule_path)
            else:
                path_match = True

            if domain_match and path_match:
                # Return mode and max_depth from rule
                mode = rule.get('mode', 'single')
                if mode == 'recursive':
                    max_depth = rule.get('max_depth', self.config.get('recursive_defaults', {}).get('max_depth', 2))
                else:
                    max_depth = rule.get('max_depth', self.config.get('single_defaults', {}).get('max_depth', 1))
                return mode, max_depth

        return None

    def review_suggestions(self):
        """Main review loop"""
        print("=" * 60)
        print("Polkadot Bounty Archive - Suggestion Reviewer")
        print("=" * 60)

        # Load suggestions
        suggestions_data = self.load_yaml_file(self.suggestions_file)
        suggestions = suggestions_data.get('suggestions', [])

        if not suggestions:
            print("\nNo suggestions to review.")
            print("Run: python suggest.py to generate suggestions.")
            return

        print(f"\nFound {len(suggestions)} suggestion(s) to review.")

        # Review each suggestion
        remaining_suggestions = []

        for i, suggestion in enumerate(suggestions):
            # Check if URL matches auto-accept rules
            auto_accept_result = self.check_auto_accept(suggestion['url'])

            if auto_accept_result:
                # Auto-accept: apply matched mode and add to queue
                mode, max_depth = auto_accept_result
                suggestion['mode'] = mode
                suggestion['max_depth'] = max_depth
                self.add_to_queue(suggestion)
                self.auto_accepted.append(suggestion['url'])
                print(f"\n[AUTO-ACCEPTED {i + 1}/{len(suggestions)}] {suggestion['url']}")
                print(f"  Mode: {mode}, Max Depth: {max_depth}")
                continue

            # Manual review required
            self.display_suggestion(suggestion, i, len(suggestions))
            choice = self.get_user_choice()

            if choice == 'A':
                # Accept
                self.add_to_queue(suggestion)
                self.accepted.append(suggestion['url'])
                print(f"\n[+] Added to scrape queue")

            elif choice == 'M':
                # Modify
                modified = self.modify_suggestion(suggestion)
                if modified:
                    self.add_to_queue(modified)
                    self.modified.append(suggestion['url'])
                    print(f"\n[+] Modified and added to scrape queue")
                else:
                    print(f"\n[-] Modification cancelled. Keeping in suggestions.")
                    remaining_suggestions.append(suggestion)

            elif choice == 'I':
                # Ignore
                reason = input("\nOptional reason for ignoring (press Enter to skip): ").strip()
                self.add_to_ignore(suggestion, reason if reason else None)
                self.ignored.append(suggestion['url'])
                print(f"\n[+] Added to ignore list")

            elif choice == 'S':
                # Skip
                remaining_suggestions.append(suggestion)
                print(f"\n-> Skipped. Will remain in suggestions.")

            elif choice == 'Q':
                # Quit
                print("\n-> Exiting reviewer...")
                # Keep all remaining suggestions
                remaining_suggestions.extend(suggestions[i+1:])
                break

        # Update suggestions file with remaining suggestions
        if remaining_suggestions:
            suggestions_data['suggestions'] = remaining_suggestions
            suggestions_data['last_generated'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            self.save_yaml_file(self.suggestions_file, suggestions_data)
        else:
            # Clear suggestions file
            suggestions_data = {
                'version': "1.0",
                'last_generated': None,
                'suggestions': []
            }
            self.save_yaml_file(self.suggestions_file, suggestions_data)

        # Print summary
        self.print_summary(len(remaining_suggestions))

    def print_summary(self, remaining: int):
        """Print summary of review session"""
        print("\n" + "=" * 60)
        print("REVIEW SUMMARY")
        print("=" * 60)
        print(f"Auto-accepted: {len(self.auto_accepted)}")
        print(f"Accepted:      {len(self.accepted)}")
        print(f"Modified:      {len(self.modified)}")
        print(f"Ignored:       {len(self.ignored)}")
        print(f"Remaining:     {remaining}")
        print("=" * 60)

        if self.accepted or self.modified or self.auto_accepted:
            print(f"\nNext step: Run 'python scraper.py' to scrape queued URLs")


def main():
    # Determine project root (parent of scraping directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    reviewer = SuggestionReviewer(project_root)
    reviewer.review_suggestions()


if __name__ == "__main__":
    main()
