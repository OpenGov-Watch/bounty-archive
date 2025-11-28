#!/usr/bin/env python3
"""
Polkadot Bounty Archive - URL Scraper

Scrapes documentation URLs for bounties and saves them as markdown files.
Reads configuration from scrape-queue.yml and outputs results to scrape-results.yml.
"""

import os
import re
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup
import html2text


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


class PolkadotBountyScraper:
    """Scraper for Polkadot bounty documentation"""

    SOCIAL_DOMAINS = {
        'twitter.com', 'x.com', 't.me', 'telegram.me',
        'discord.com', 'discord.gg', 'matrix.to', 'matrix.org'
    }

    EXCLUDE_DOMAINS = {
        'google.com', 'youtube.com', 'facebook.com', 'instagram.com',
        'linkedin.com', 'reddit.com'
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.bounties_dir = project_root / "bounties"
        self.scraping_dir = project_root / "scraping"
        self.queue_file = self.scraping_dir / "scrape-queue.yml"
        self.results_file = self.scraping_dir / "scrape-results.yml"

        # Initialize HTML to Markdown converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0  # Don't wrap lines

        # Session for requests with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; PolkadotBountyArchiver/1.0)'
        })

    def load_queue(self) -> List[ScrapeJob]:
        """Load scraping queue from YAML file"""
        if not self.queue_file.exists():
            print(f"Error: Queue file not found: {self.queue_file}")
            return []

        with open(self.queue_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        jobs = []
        for item in data.get('queue', []):
            if not item:  # Skip None/empty items
                continue
            jobs.append(ScrapeJob(
                bounty_id=item['bounty_id'],
                url=item['url'],
                mode=item.get('mode', 'single'),
                max_depth=item.get('max_depth', 1)
            ))
        return jobs

    def get_bounty_slug(self, bounty_id: int) -> Optional[str]:
        """Get bounty folder slug from bounty ID"""
        pattern = f"{bounty_id}-*"
        matches = list(self.bounties_dir.glob(pattern))
        if matches:
            return matches[0].name
        return None

    def fetch_url(self, url: str) -> Optional[Tuple[str, int, BeautifulSoup]]:
        """Fetch URL and return content, status code, and parsed HTML"""
        try:
            print(f"  Fetching: {url}")
            response = self.session.get(url, timeout=30, allow_redirects=True)

            # Check if redirected to different host
            if urlparse(response.url).netloc != urlparse(url).netloc:
                print(f"  Warning: Redirected to different host: {response.url}")

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                return response.text, response.status_code, soup
            else:
                print(f"  Error: HTTP {response.status_code}")
                return None, response.status_code, None

        except requests.exceptions.Timeout:
            print(f"  Error: Timeout")
            return None, 0, None
        except requests.exceptions.RequestException as e:
            print(f"  Error: {str(e)}")
            return None, 0, None

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

    def convert_to_markdown(self, html: str, soup: BeautifulSoup) -> str:
        """Convert HTML to clean markdown"""
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Try to find main content area
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_=re.compile(r'content|main|article', re.I)) or
            soup.find('body')
        )

        if main_content:
            html_content = str(main_content)
        else:
            html_content = html

        # Convert to markdown
        markdown = self.html_converter.handle(html_content)

        # Clean up excessive newlines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        return markdown.strip()

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

    def scrape_page(self, url: str, base_url: str) -> Optional[ScrapedPage]:
        """Scrape a single page"""
        html, status_code, soup = self.fetch_url(url)

        if not html or not soup:
            return None

        title = self.extract_title(soup, url)
        markdown = self.convert_to_markdown(html, soup)
        internal, external, social = self.extract_links(soup, base_url)

        return ScrapedPage(
            url=url,
            title=title,
            content=markdown,
            status_code=status_code,
            internal_links=internal,
            external_links=external,
            social_links=social
        )

    def url_to_filepath(self, url: str, bounty_slug: str) -> Path:
        """Convert URL to file path"""
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path.strip('/')

        # Determine filename
        if not path or path.endswith('/'):
            filename = 'index.md'
            filepath = path.rstrip('/')
        else:
            parts = path.split('/')
            filename = f"{parts[-1]}.md"
            filepath = '/'.join(parts[:-1])

        # Build full path
        full_path = self.bounties_dir / bounty_slug / "scraped" / domain / filepath / filename
        return full_path

    def save_page(self, page: ScrapedPage, filepath: Path):
        """Save scraped page to file with YAML frontmatter"""
        # Create directory
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Build frontmatter
        frontmatter = {
            'url': page.url,
            'scraped_at': datetime.utcnow().isoformat() + 'Z',
            'title': page.title,
            'status_code': page.status_code
        }

        # Build content
        content = "---\n"
        content += yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        content += "---\n\n"
        content += page.content

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

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
            page = self.scrape_page(url, job.url)

            if page:
                # Save page
                filepath = self.url_to_filepath(url, bounty_slug)
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
            time.sleep(1)

        return {
            'status': 'completed' if not errors or files_created else 'partial' if files_created else 'failed',
            'pages_scraped': len(files_created),
            'files_created': files_created,
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

        page = self.scrape_page(job.url, job.url)

        if not page:
            return {
                'status': 'failed',
                'error': f'Failed to fetch {job.url}'
            }

        # Save page
        filepath = self.url_to_filepath(job.url, bounty_slug)
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

        start_time = datetime.utcnow()

        if job.mode == "recursive":
            result = self.scrape_recursive(job)
        else:
            result = self.scrape_single(job)

        # Add metadata
        result.update({
            'bounty_id': job.bounty_id,
            'url': job.url,
            'mode': job.mode,
            'max_depth': job.max_depth if job.mode == "recursive" else None,
            'scraped_at': start_time.isoformat() + 'Z'
        })

        return result

    def save_results(self, results: List[Dict]):
        """Save results to scrape-results.yml"""
        # Load existing results if any
        if self.results_file.exists():
            with open(self.results_file, 'r', encoding='utf-8') as f:
                existing = yaml.safe_load(f) or {}
        else:
            existing = {}

        # Initialize structure
        if 'scraped' not in existing:
            existing['scraped'] = []
        if 'discovered_queue' not in existing:
            existing['discovered_queue'] = []

        # Add new results
        existing['scraped'].extend(results)
        existing['last_updated'] = datetime.utcnow().isoformat() + 'Z'
        existing['version'] = "1.0"

        # Build discovered queue
        for result in results:
            if result.get('status') in ('completed', 'partial'):
                outgoing = result.get('outgoing_urls', {})
                for url in outgoing.get('external', []):
                    # Check if already in queue
                    if not any(item['url'] == url for item in existing['discovered_queue']):
                        existing['discovered_queue'].append({
                            'url': url,
                            'found_on': result['url'],
                            'bounty_id': result['bounty_id']
                        })

        # Save results
        with open(self.results_file, 'w', encoding='utf-8') as f:
            yaml.dump(existing, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"\nResults saved to: {self.results_file.relative_to(self.project_root)}")

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

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        total_pages = sum(r.get('pages_scraped', 0) for r in results)
        total_errors = sum(len(r.get('errors', [])) for r in results)
        completed = sum(1 for r in results if r.get('status') == 'completed')
        failed = sum(1 for r in results if r.get('status') == 'failed')

        print(f"Jobs processed: {len(results)}")
        print(f"  ✓ Completed: {completed}")
        print(f"  ✗ Failed: {failed}")
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

    scraper = PolkadotBountyScraper(project_root)
    scraper.run()


if __name__ == "__main__":
    main()
