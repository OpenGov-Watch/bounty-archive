#!/usr/bin/env python3
"""
Build scraped content index for website

Scans all bounty scraped folders and generates a JSON index
that the website can use to display scraped domains and files.
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List
from collections import defaultdict


def load_scrape_index(project_root: Path) -> Dict:
    """Load scrape-index.yml"""
    index_file = project_root / 'scraping' / 'scrape-index.yml'
    if not index_file.exists():
        return {'index': []}

    with open(index_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
        return data


def scan_bounty_scraped(bounty_dir: Path, bounty_id: int) -> Dict:
    """Scan a bounty's scraped folder and build domain tree"""
    scraped_dir = bounty_dir / 'scraped'

    if not scraped_dir.exists():
        return {'domains': []}

    # Group files by domain
    domains = defaultdict(list)

    # Walk through scraped directory
    for domain_dir in scraped_dir.iterdir():
        if not domain_dir.is_dir():
            continue

        domain = domain_dir.name

        # Recursively walk domain directory
        for root, dirs, files in os.walk(domain_dir):
            root_path = Path(root)

            for file in files:
                # Skip metadata files
                if file.endswith('.meta.yml'):
                    continue

                file_path = root_path / file

                # Calculate relative path from domain directory
                rel_path = file_path.relative_to(domain_dir)

                # Try to load metadata
                meta_file = Path(str(file_path) + '.meta.yml')
                metadata = {}
                if meta_file.exists():
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            metadata = yaml.safe_load(f) or {}
                    except:
                        pass

                # Build file entry
                file_entry = {
                    'path': str(rel_path).replace('\\', '/'),
                    'name': file,
                    'url': metadata.get('url', ''),
                    'title': metadata.get('title', ''),
                    'scraped_at': metadata.get('scraped_at', ''),
                }

                domains[domain].append(file_entry)

    # Convert to list of domain objects
    domain_list = []
    for domain, files in sorted(domains.items()):
        # Sort files by path
        files.sort(key=lambda x: x['path'])

        domain_list.append({
            'domain': domain,
            'file_count': len(files),
            'files': files
        })

    return {'domains': domain_list}


def build_index(project_root: Path) -> Dict:
    """Build complete scraped content index"""
    bounties_dir = project_root / 'bounties'

    # Group by bounty ID
    bounty_index = {}

    # Scan all bounty directories
    for bounty_dir in sorted(bounties_dir.iterdir()):
        if not bounty_dir.is_dir():
            continue

        # Extract bounty ID from directory name
        try:
            bounty_id = int(bounty_dir.name.split('-')[0])
        except (ValueError, IndexError):
            continue

        # Scan scraped content
        scraped_data = scan_bounty_scraped(bounty_dir, bounty_id)

        # Only include bounties with scraped content
        if scraped_data['domains']:
            bounty_index[str(bounty_id)] = scraped_data

    return {
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'bounty_count': len(bounty_index),
        'total_domains': sum(len(b['domains']) for b in bounty_index.values()),
        'total_files': sum(
            sum(d['file_count'] for d in b['domains'])
            for b in bounty_index.values()
        ),
        'bounties': bounty_index
    }


def main():
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    print("=" * 60)
    print("Building Scraped Content Index")
    print("=" * 60)

    # Build index
    index = build_index(project_root)

    print(f"\nBounties with scraped content: {index['bounty_count']}")
    print(f"Total domains: {index['total_domains']}")
    print(f"Total files: {index['total_files']}")

    # Save to JSON
    output_file = project_root / 'scraped-index.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)

    print(f"\nIndex saved to: {output_file.relative_to(project_root)}")
    print("=" * 60)


if __name__ == '__main__':
    main()
