#!/usr/bin/env python3
"""
Polkadot Bounty Archive - URL Scraper

Scrapes documentation URLs for bounties and saves them in their original format.
Reads configuration from scrape-queue.yml and outputs results to scrape-results.yml.
"""

import os
import re
import sys
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

from config import ScrapeConfig
from data import ScrapeData
from models import QueueEntry, IndexEntry, DiscoveredLink, ScrapeResult, ScrapeStatus, ScrapeMode


@dataclass
class ScrapedPage:
    """Represents a scraped page"""
    url: str
    title: str
    content: str
    status_code: int
    internal_links: Set[str] = field(default_factory=set)
    external_links: Set[str] = field(default_factory=set)
    social_links: Set[str] = field(default_factory=set)


@dataclass
class ScrapeJob:
    """Represents a scraping job from the queue"""
    bounty_id: int
    url: str
    mode: str  # "single" or "recursive"
    max_depth: int = 1
    source: str = "Unknown"
    categories: list = field(default_factory=list)
    type: str = "scrape"
    discovered_at: str = None


class PolkadotBountyScraper:
    """Scraper for Polkadot bounty documentation"""

    def __init__(self, project_root: Path, config: ScrapeConfig):
        self.project_root = project_root
        self.config = config
        self.bounties_dir = project_root / "bounties"
        self.scraping_dir = project_root / "scraping"
        self.data = ScrapeData(self.scraping_dir)

        # Session for requests with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent
        })

    def categorize_link(self, url: str) -> List[str]:
        """Categorize a URL based on configured link_categories"""
        return self.config.categorize_extracted_link(url)

    def load_queue(self) -> List[ScrapeJob]:
        """Load scraping queue from YAML file"""
        queue = self.data.load_queue_typed()

        if not queue:
            print(f"Error: Queue is empty")
            return []

        jobs = []
        for item in queue:
            jobs.append(ScrapeJob(
                bounty_id=item.bounty_id,
                url=item.url,
                mode=item.mode.value,
                max_depth=item.max_depth
            ))
        return jobs

    def get_bounty_slug(self, bounty_id: int) -> Optional[str]:
        """Get bounty folder slug from bounty ID"""
        pattern = f"{bounty_id}-*"
        matches = list(self.bounties_dir.glob(pattern))
        if matches:
            return matches[0].name
        return None

    def fetch_url(self, url: str) -> Optional[requests.Response]:
        """Fetch URL and return response object"""
        try:
            print(f"  Fetching: {url}")
            response = self.session.get(url, timeout=self.config.request_timeout, allow_redirects=True)

            # Check if redirected to different host
            if urlparse(response.url).netloc != urlparse(url).netloc:
                print(f"  Warning: Redirected to different host: {response.url}")

            if response.status_code == 200:
                return response
            else:
                print(f"  Error: HTTP {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print(f"  Error: Timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"  Error: {str(e)}")
            return None

    def extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract page title from HTML"""
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # Try h1 tag
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()

        # Fallback to URL path
        path = urlparse(url).path
        return path.strip('/').split('/')[-1] or 'index'

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> Tuple[Set[str], Set[str], Set[str]]:
        """Extract and categorize links from page"""
        internal_links = set()
        external_links = set()
        social_links = set()

        base_parsed = urlparse(base_url)
        base_path = base_parsed.path.rstrip('/')

        for link in soup.find_all('a', href=True):
            href = link['href']

            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)

            # Skip invalid schemes
            if parsed.scheme not in ('http', 'https'):
                continue

            # Normalize URL (remove fragments, trailing slashes)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
            if parsed.query:
                normalized += f"?{parsed.query}"

            # Skip self-references
            if normalized == base_url.rstrip('/'):
                continue

            # Categorize link
            if parsed.netloc in self.SOCIAL_DOMAINS:
                social_links.add(normalized)
            elif parsed.netloc == base_parsed.netloc and parsed.path.startswith(base_path):
                # Internal: same domain and same base path
                internal_links.add(normalized)
            elif parsed.netloc not in self.EXCLUDE_DOMAINS:
                # External: different domain or different base path
                external_links.add(normalized)

        return internal_links, external_links, social_links

    def get_file_extension(self, response: requests.Response, url: str) -> str:
        """Determine file extension from content-type or URL"""
        content_type = response.headers.get('content-type', '').lower()

        # Map content-type to extension
        if 'text/html' in content_type:
            return '.html'
        elif 'application/pdf' in content_type:
            return '.pdf'
        elif 'application/json' in content_type:
            return '.json'
        elif 'text/plain' in content_type:
            return '.txt'
        elif 'text/xml' in content_type or 'application/xml' in content_type:
            return '.xml'
        elif 'text/markdown' in content_type:
            return '.md'
        else:
            # Try to infer from URL
            parsed = urlparse(url)
            path = parsed.path
            if '.' in path:
                ext = Path(path).suffix
                if ext:
                    return ext
            # Default to .html for web pages
            return '.html'

    def scrape_page(self, url: str, base_url: str) -> Optional[Tuple[ScrapedPage, str]]:
        """Scrape a single page and return page + file extension"""
        response = self.fetch_url(url)

        if not response:
            return None

        # Get file extension
        extension = self.get_file_extension(response, url)

        # Get content type and determine if we can extract links
        content_type = response.headers.get('content-type', '').lower()
        can_parse_links = 'text/html' in content_type

        # Parse HTML if applicable
        if can_parse_links:
            soup = BeautifulSoup(response.content, 'html.parser')
            title = self.extract_title(soup, url)
            internal, external, social = self.extract_links(soup, base_url)
        else:
            soup = None
            title = Path(urlparse(url).path).name or url
            internal, external, social = set(), set(), set()

        # Store original content (text for text-based, bytes for binary)
        if content_type.startswith('text/') or 'json' in content_type or 'xml' in content_type:
            content = response.text
        else:
            content = response.content

        page = ScrapedPage(
            url=url,
            title=title,
            content=content,
            status_code=response.status_code,
            internal_links=internal,
            external_links=external,
            social_links=social
        )

        return page, extension

    def url_to_filepath(self, url: str, bounty_slug: str, extension: str) -> Path:
        """Convert URL to file path with appropriate extension"""
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path.strip('/')

        # Determine filename
        if not path or path.endswith('/'):
            filename = f'index{extension}'
            filepath = path.rstrip('/')
        else:
            parts = path.split('/')
            # Remove existing extension if present
            base_name = Path(parts[-1]).stem
            filename = f"{base_name}{extension}"
            filepath = '/'.join(parts[:-1])

        # Build full path
        full_path = self.bounties_dir / bounty_slug / "scraped" / domain / filepath / filename
        return full_path

    def save_page(self, page: ScrapedPage, filepath: Path):
        """Save scraped page in original format with metadata in companion .meta.yml file"""
        # Create directory
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save original content
        if isinstance(page.content, bytes):
            # Binary content (PDFs, images, etc.)
            with open(filepath, 'wb') as f:
                f.write(page.content)
        else:
            # Text content (HTML, JSON, XML, etc.)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(page.content)

        # Save metadata in companion file
        meta_filepath = filepath.with_suffix(filepath.suffix + '.meta.yml')
        metadata = {
            'url': page.url,
            'scraped_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'title': page.title,
            'status_code': page.status_code,
            'original_file': filepath.name
        }

        with open(meta_filepath, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"  Saved: {filepath.relative_to(self.project_root)}")

    def scrape_recursive(self, job: ScrapeJob) -> Dict:
        """Scrape URL recursively up to max_depth"""
        bounty_slug = self.get_bounty_slug(job.bounty_id)
        if not bounty_slug:
            return {
                'status': 'failed',
                'error': f'Bounty folder not found for ID {job.bounty_id}'
            }

        visited = set()
        queue = [(job.url, 0)]  # (url, depth)
        all_internal = set()
        all_external = set()
        all_social = set()
        files_created = []
        errors = []

        while queue:
            url, depth = queue.pop(0)

            # Skip if already visited
            normalized_url = url.rstrip('/')
            if normalized_url in visited:
                continue
            visited.add(normalized_url)

            # Scrape page
            result = self.scrape_page(url, job.url)

            if result:
                page, extension = result
                # Save page
                filepath = self.url_to_filepath(url, bounty_slug, extension)
                self.save_page(page, filepath)
                files_created.append(str(filepath.relative_to(self.project_root)))

                # Collect links
                all_internal.update(page.internal_links)
                all_external.update(page.external_links)
                all_social.update(page.social_links)

                # Queue internal links for next depth level
                if depth < job.max_depth:
                    for link in page.internal_links:
                        if link.rstrip('/') not in visited:
                            queue.append((link, depth + 1))
            else:
                errors.append(f"Failed to fetch: {url}")

            # Rate limiting
            time.sleep(self.config.rate_limit_delay)

        return {
            'status': 'completed' if not errors or files_created else 'partial' if files_created else 'failed',
            'pages_scraped': len(files_created),
            'files_created': files_created,
            'visited_urls': sorted(visited),
            'outgoing_urls': {
                'internal': sorted(all_internal),
                'external': sorted(all_external),
                'social': sorted(all_social)
            },
            'errors': errors
        }

    def scrape_single(self, job: ScrapeJob) -> Dict:
        """Scrape a single URL"""
        bounty_slug = self.get_bounty_slug(job.bounty_id)
        if not bounty_slug:
            return {
                'status': 'failed',
                'error': f'Bounty folder not found for ID {job.bounty_id}'
            }

        result = self.scrape_page(job.url, job.url)

        if not result:
            return {
                'status': 'failed',
                'error': f'Failed to fetch {job.url}'
            }

        page, extension = result

        # Save page
        filepath = self.url_to_filepath(job.url, bounty_slug, extension)
        self.save_page(page, filepath)

        return {
            'status': 'completed',
            'pages_scraped': 1,
            'files_created': [str(filepath.relative_to(self.project_root))],
            'outgoing_urls': {
                'internal': sorted(page.internal_links),
                'external': sorted(page.external_links),
                'social': sorted(page.social_links)
            },
            'errors': []
        }

    def scrape_job(self, job: ScrapeJob) -> Dict:
        """Scrape a job from the queue"""
        print(f"\nScraping Bounty #{job.bounty_id}: {job.url}")
        print(f"Mode: {job.mode}" + (f", max_depth: {job.max_depth}" if job.mode == "recursive" else ""))

        start_time = datetime.now(timezone.utc)

        if job.mode == "recursive":
            result = self.scrape_recursive(job)
        else:
            result = self.scrape_single(job)

        # Add metadata (preserve all fields from queue)
        result.update({
            'bounty_id': job.bounty_id,
            'url': job.url,
            'mode': job.mode,
            'max_depth': job.max_depth if job.mode == "recursive" else None,
            'source': job.source,
            'categories': job.categories,
            'type': job.type,
            'discovered_at': job.discovered_at,
            'scraped_at': start_time.isoformat().replace('+00:00', 'Z')
        })

        return result

    def save_results(self, results: List[Dict]):
        """Save results to scrape-results.yml"""
        # Add results using data manager
        self.data.add_results(results)
        print(f"\nResults saved to: scraping/scrape-results.yml")

    def update_index(self, results: List[Dict]):
        """Update scrape-index.yml with successfully scraped URLs"""
        entries = []

        # Build index entries from results
        for result in results:
            if result.get('status') in ('completed', 'partial'):
                # Extract location from first file created
                location = ''
                if result.get('files_created'):
                    # Get the directory path from the first file
                    first_file = result['files_created'][0]
                    # Extract path like "bounties/11-anti-scam-bounty/scraped/polkadot.antiscam.team/"
                    if '/scraped/' in first_file or '\\scraped\\' in first_file:
                        parts = first_file.replace('\\', '/').split('/scraped/')
                        if len(parts) == 2:
                            location = parts[0] + '/scraped/' + parts[1].rsplit('/', 1)[0] + '/'

                # For recursive scrapes, index all visited URLs
                urls_to_index = result.get('visited_urls', [result['url']])
                if not urls_to_index:
                    urls_to_index = [result['url']]

                for url in urls_to_index:
                    entry = IndexEntry(
                        url=url,
                        bounty_id=result['bounty_id'],
                        scraped_at=result.get('scraped_at', ''),
                        location=location,
                        pages=1,  # Each URL is 1 page
                        source=result.get('source', 'Unknown'),
                        categories=result.get('categories', []),
                        type=result.get('type', 'scrape'),
                        discovered_at=result.get('discovered_at')
                    )
                    entries.append(entry)

        # Add entries to index using data manager (handles deduplication and conversion)
        if entries:
            self.data.add_to_index(entries)
            print(f"Index updated: scraping/scrape-index.yml")

    def clear_queue(self, results: List[Dict]):
        """Remove successfully scraped URLs from scrape-queue.yml"""
        # Get URLs that were successfully scraped
        successful_urls = []
        for result in results:
            if result.get('status') in ('completed', 'partial'):
                successful_urls.append(result['url'])

        if successful_urls:
            self.data.remove_from_queue(successful_urls)
            print(f"Queue cleared: removed {len(successful_urls)} completed job(s)")

    def save_links(self, results: List[Dict]):
        """Save extracted links to scrape-links.yml"""
        new_links = []

        # Extract and categorize links from results
        for result in results:
            if result.get('status') not in ('completed', 'partial'):
                continue

            source_url = result['url']
            bounty_id = result['bounty_id']
            outgoing = result.get('outgoing_urls', {})

            # Collect all links from all categories (internal, external, social)
            all_links = set()
            all_links.update(outgoing.get('internal', []))
            all_links.update(outgoing.get('external', []))
            all_links.update(outgoing.get('social', []))

            # Categorize each link and prepare for adding
            for url in all_links:
                # Categorize the link
                categories = self.categorize_link(url)

                link = DiscoveredLink(
                    url=url,
                    source_url=source_url,
                    bounty_id=bounty_id,
                    categories=categories,
                    discovered_at=result.get('scraped_at', '')
                )
                new_links.append(link)

        # Add links using data manager (handles deduplication and conversion)
        if new_links:
            before_count = len(self.data.load_links())
            self.data.add_links(new_links)
            after_count = len(self.data.load_links())
            added_count = after_count - before_count
            print(f"Links saved: {added_count} new links discovered")

    def run(self):
        """Main execution"""
        print("=" * 60)
        print("Polkadot Bounty Archive - URL Scraper")
        print("=" * 60)

        # Load queue
        jobs = self.load_queue()

        if not jobs:
            print("\nNo jobs in queue. Add URLs to scraping/scrape-queue.yml")
            return

        print(f"\nFound {len(jobs)} job(s) in queue")

        # Process jobs
        results = []
        for job in jobs:
            result = self.scrape_job(job)
            results.append(result)

        # Save results
        self.save_results(results)

        # Update index
        self.update_index(results)

        # Save extracted links
        self.save_links(results)

        # Clear successfully scraped jobs from queue
        self.clear_queue(results)

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        total_pages = sum(r.get('pages_scraped', 0) for r in results)
        total_errors = sum(len(r.get('errors', [])) for r in results)
        completed = sum(1 for r in results if r.get('status') == 'completed')
        failed = sum(1 for r in results if r.get('status') == 'failed')

        print(f"Jobs processed: {len(results)}")
        print(f"  [+] Completed: {completed}")
        print(f"  [-] Failed: {failed}")
        print(f"\nPages scraped: {total_pages}")
        print(f"Errors: {total_errors}")

        if results:
            print(f"\nFiles saved to:")
            for result in results:
                if result.get('files_created'):
                    print(f"  - {result['files_created'][0].split('/scraped/')[0]}/scraped/")

        print("\n" + "=" * 60)


def main():
    """CLI entry point"""
    # Get project root (parent of scraping directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Load configuration
    config_file = script_dir / "scrape-config.yml"
    config = ScrapeConfig(config_file)

    # Create scraper and run
    scraper = PolkadotBountyScraper(project_root, config)
    scraper.run()


if __name__ == "__main__":
    main()
