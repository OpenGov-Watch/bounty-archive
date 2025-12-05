#!/usr/bin/env python3
"""
Polkadot Bounty Archive - URL Scraper

Scrapes documentation URLs for bounties and saves them in their original format.
Reads configuration from scrape-queue.yml and outputs results to scrape-results.yml.
"""

import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass, field

import requests

from config import ScrapeConfig
from data import ScrapeData
from handlers import ScrapedPage, get_handler_for_url
from models import QueueEntry, IndexEntry, DiscoveredLink, ScrapeResult, ScrapeStatus, ScrapeMode


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
        """Categorize a URL based on configured categorization rules"""
        return self.config.categorize_url(url)

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
                max_depth=item.max_depth,
                source=item.source,
                categories=item.categories,
                type=item.type,
                discovered_at=item.discovered_at
            ))
        return jobs

    def get_bounty_slug(self, bounty_id: int) -> Optional[str]:
        """Get bounty folder slug from bounty ID"""
        pattern = f"{bounty_id}-*"
        matches = list(self.bounties_dir.glob(pattern))
        if matches:
            return matches[0].name
        return None

    def scrape_page(
        self, url: str, base_url: str
    ) -> Tuple[Optional[ScrapedPage], Optional[str], Optional[int], Optional[str], str]:
        """Scrape a single page using a registered handler."""

        handler = get_handler_for_url(url, self.config, self.session)
        print(f"  Fetching with handler [{handler.handler_name}]: {url}")
        page, error_code, error_message = handler.fetch(url)

        if not page:
            return None, None, error_code, error_message, handler.handler_name

        page = handler.discover_links(page, base_url)
        return page, page.extension, error_code, error_message, handler.handler_name

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
            'original_file': filepath.name,
            'handler': page.handler
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
        url_results = {}  # Track per-URL status

        while queue:
            url, depth = queue.pop(0)

            # Skip if already visited
            normalized_url = url.rstrip('/')
            if normalized_url in visited:
                continue
            visited.add(normalized_url)

            # Scrape page
            page, extension, error_code, error_message, handler_name = self.scrape_page(url, job.url)

            if page:
                filepath = self.url_to_filepath(url, bounty_slug, extension)

                # Save the response body for traceability regardless of status
                self.save_page(page, filepath)
                files_created.append(str(filepath.relative_to(self.project_root)))

                if page.status_code == 200:
                    # Track success
                    url_results[url] = {
                        'status': 'success',
                        'error_code': None,
                        'error_message': None,
                        'handler': handler_name
                    }

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
                    # Non-200 response is recorded as a failure but does not block completion
                    url_results[url] = {
                        'status': 'failed',
                        'error_code': error_code or page.status_code,
                        'error_message': error_message or f'HTTP {page.status_code}',
                        'handler': handler_name
                    }
                    errors.append(f"Non-200 response for {url}: HTTP {page.status_code}")
            else:
                # Failed - create error marker file
                error_filepath = self.url_to_filepath(url, bounty_slug, '.error.yml')
                error_data = {
                    'url': url,
                    'error_code': error_code,
                    'error_message': error_message,
                    'attempted_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    'bounty_id': job.bounty_id
                }

                # Create directory and save error file
                error_filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(error_filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(error_data, f, default_flow_style=False, allow_unicode=True)

                print(f"  Error marker saved: {error_filepath.relative_to(self.project_root)}")

                # Track failure
                url_results[url] = {
                    'status': 'failed',
                    'error_code': error_code,
                    'error_message': error_message,
                    'handler': handler_name
                }
                errors.append(f"Failed to fetch: {url} ({error_message})")

            # Rate limiting
            time.sleep(self.config.rate_limit_delay)

        failed_results = [r for r in url_results.values() if r.get('status') == 'failed']
        # Treat any HTTP response (indicated by presence of an error_code) as non-fatal
        response_only_failures = bool(failed_results) and all(r.get('error_code') is not None for r in failed_results)

        if files_created:
            status = 'completed' if (not errors or response_only_failures) else 'partial'
        else:
            status = 'completed' if (response_only_failures or not errors) else 'failed'

        return {
            'status': status,
            'pages_scraped': len(files_created),
            'files_created': files_created,
            'visited_urls': sorted(visited),
            'url_results': url_results,  # Per-URL status tracking
            'outgoing_urls': {
                'internal': sorted(all_internal),
                'external': sorted(all_external),
                'social': sorted(all_social)
            },
            'errors': errors,
            'handler': url_results.get(job.url, {}).get('handler')
        }

    def scrape_single(self, job: ScrapeJob) -> Dict:
        """Scrape a single URL"""
        bounty_slug = self.get_bounty_slug(job.bounty_id)
        if not bounty_slug:
            return {
                'status': 'failed',
                'error': f'Bounty folder not found for ID {job.bounty_id}',
                'url_results': {},
            }

        page, extension, error_code, error_message, handler_name = self.scrape_page(job.url, job.url)

        url_results = {}

        if page:
            filepath = self.url_to_filepath(job.url, bounty_slug, extension)
            self.save_page(page, filepath)

            if page.status_code == 200:
                url_results[job.url] = {
                    'status': 'success',
                    'error_code': None,
                    'error_message': None,
                    'handler': handler_name
                }

                return {
                    'status': 'completed',
                    'pages_scraped': 1,
                    'files_created': [str(filepath.relative_to(self.project_root))],
                    'visited_urls': [job.url],
                    'url_results': url_results,
                    'outgoing_urls': {
                        'internal': sorted(page.internal_links),
                        'external': sorted(page.external_links),
                        'social': sorted(page.social_links)
                    },
                    'errors': [],
                    'handler': handler_name
                }

            url_results[job.url] = {
                'status': 'failed',
                'error_code': error_code or page.status_code,
                'error_message': error_message or f'HTTP {page.status_code}',
                'handler': handler_name
            }

            return {
                'status': 'completed',
                'pages_scraped': 0,
                'files_created': [str(filepath.relative_to(self.project_root))],
                'visited_urls': [job.url],
                'url_results': url_results,
                'outgoing_urls': {
                    'internal': [],
                    'external': [],
                    'social': []
                },
                'errors': [f'Non-200 response: HTTP {page.status_code}'],
                'handler': handler_name
            }

        # Create error marker file
        error_filepath = self.url_to_filepath(job.url, bounty_slug, '.error.yml')
        error_data = {
            'url': job.url,
            'error_code': error_code,
            'error_message': error_message,
            'attempted_at': datetime.now(timezone.utc).isoformat(),
            'bounty_id': job.bounty_id
        }

        error_filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(error_filepath, 'w', encoding='utf-8') as f:
            yaml.dump(error_data, f)

        url_results[job.url] = {
            'status': 'failed',
            'error_code': error_code,
            'error_message': error_message,
            'handler': handler_name
        }

        # If we received an HTTP status code, treat it as non-fatal for queue clearing
        result_status = 'completed' if error_code is not None else 'failed'

        return {
            'status': result_status,
            'pages_scraped': 0,
            'files_created': [],
            'visited_urls': [job.url],
            'url_results': url_results,
            'outgoing_urls': {
                'internal': [],
                'external': [],
                'social': []
            },
            'errors': [f'Failed to fetch {job.url}: {error_message}'],
            'handler': handler_name
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
            'scraped_at': start_time.isoformat().replace('+00:00', 'Z'),
            'handler': result.get('handler') or result.get('url_results', {}).get(job.url, {}).get('handler')
        })

        return result

    def save_results(self, results: List[Dict]):
        """Save results to scrape-results.yml"""
        # Add results using data manager
        self.data.add_results(results)
        print(f"\nResults saved to: scraping/scrape-results.yml")

    def update_index(self, results: List[Dict]):
        """Update scrape-index.yml with all attempted URLs (successful and failed)"""
        entries = []

        # Build index entries from results
        for result in results:
            # Get per-URL results if available
            url_results = result.get('url_results', {})

            # Extract base location from first successful file
            base_location = ''
            if result.get('files_created'):
                first_file = result['files_created'][0]
                # Extract path like "bounties/11-anti-scam-bounty/scraped/polkadot.antiscam.team/"
                if '/scraped/' in first_file or '\\scraped\\' in first_file:
                    parts = first_file.replace('\\', '/').split('/scraped/')
                    if len(parts) == 2:
                        base_location = parts[0] + '/scraped/' + parts[1].rsplit('/', 1)[0] + '/'

            # Index all attempted URLs
            urls_to_index = result.get('visited_urls', [result['url']])
            if not urls_to_index:
                urls_to_index = [result['url']]

            for url in urls_to_index:
                # Get per-URL status if available
                url_status = url_results.get(url, {})
                status = 'success' if url_status.get('status') == 'success' else 'failed'
                error_code = url_status.get('error_code')
                error_message = url_status.get('error_message')
                handler = url_status.get('handler') or result.get('handler')

                # Use base_location for successful URLs, empty for failed
                location = base_location if status == 'success' else ''

                entry = IndexEntry(
                    url=url,
                    bounty_id=result['bounty_id'],
                    scraped_at=result.get('scraped_at', ''),
                    location=location,
                    source=result.get('source', 'Unknown'),
                    categories=result.get('categories', []),
                    type=result.get('type', 'scrape'),
                    discovered_at=result.get('discovered_at'),
                    status=status,
                    error_code=error_code,
                    error_message=error_message,
                    handler=handler
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
