#!/usr/bin/env python3
"""
Polkadot Bounty Archive - Configuration Manager

Central configuration class that loads and exposes all settings from scrape-config.yml
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse


class ScrapeConfig:
    """Centralized configuration manager for the scraping system"""

    def __init__(self, config_file: Path):
        self.config_file = config_file
        self._config = self._load_config()

    def _load_config(self) -> Dict:
        """Load and validate configuration file"""
        if not self.config_file.exists():
            print(f"Error: Configuration file not found: {self.config_file}")
            print("Please create scrape-config.yml in the scraping directory.")
            sys.exit(1)

        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if config is None:
                print(f"Error: Configuration file is empty: {self.config_file}")
                sys.exit(1)
            return config

    # ========== Default Settings ==========

    @property
    def default_mode(self) -> str:
        """Get default scraping mode (single or recursive)"""
        return self._config.get('default_mode', 'single')

    def get_default_mode_settings(self) -> Tuple[str, int]:
        """Get default mode and max_depth"""
        mode = self.default_mode
        if mode == 'recursive':
            max_depth = self._config.get('recursive_defaults', {}).get('max_depth', 2)
        else:
            max_depth = self._config.get('single_defaults', {}).get('max_depth', 1)
        return mode, max_depth

    # ========== Auto-Accept Rules ==========

    @property
    def auto_accept_rules(self) -> List[Dict]:
        """Get auto-accept rules for review"""
        return self._config.get('auto_accept', [])

    def should_auto_accept(self, url: str) -> bool:
        """Check if URL should be auto-accepted"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        for rule in self.auto_accept_rules:
            if isinstance(rule, dict):
                rule_domain = rule.get('domain', '').lower()
            elif isinstance(rule, str):
                rule_domain = rule.lower()
            else:
                continue

            if rule_domain in domain:
                return True

        return False

    # ========== URL Categorization ==========

    @property
    def domain_categories(self) -> Dict[str, List[str]]:
        """Get domain-based category mappings"""
        return self._config.get('categorization', {}).get('domains', {})

    @property
    def path_categories(self) -> Dict[str, List[str]]:
        """Get path-based category mappings"""
        return self._config.get('categorization', {}).get('paths', {})

    def categorize_url(self, url: str) -> List[str]:
        """Categorize a URL based on domain and path patterns"""
        categories = set()

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()

            # Check domain patterns
            for pattern, cats in self.domain_categories.items():
                if pattern.lower() in domain:
                    if isinstance(cats, list):
                        categories.update(cats)
                    elif isinstance(cats, str):
                        categories.add(cats)

            # Check path patterns
            for pattern, cats in self.path_categories.items():
                if pattern.lower() in path:
                    if isinstance(cats, list):
                        categories.update(cats)
                    elif isinstance(cats, str):
                        categories.add(cats)

            # Default if no matches
            if not categories:
                categories.add('other')

            return sorted(list(categories))

        except Exception:
            return ['other']

    def get_suggestion_type(self, categories: List[str]) -> str:
        """Determine suggestion type (scrape/associated_url/social) from categories"""
        # Get type mapping from config
        type_mapping = self._config.get('categorization', {}).get('type_mapping', {})

        # Check each type in priority order
        for suggestion_type, category_list in type_mapping.items():
            if any(cat in categories for cat in category_list):
                return suggestion_type

        # Default to scrape
        return 'scrape'

    # ========== Ignored URLs ==========

    @property
    def ignored_urls(self) -> List[Dict]:
        """Get list of ignored URLs with reasons"""
        return self._config.get('ignored', [])

    def is_ignored(self, url: str) -> Tuple[bool, str]:
        """Check if URL is ignored. Returns (is_ignored, reason)"""
        # Normalize URL for comparison
        url_normalized = url.rstrip('/')

        for item in self.ignored_urls:
            if isinstance(item, dict):
                ignored_url = item.get('url', '').rstrip('/')
                reason = item.get('reason', 'No reason provided')
            elif isinstance(item, str):
                ignored_url = item.rstrip('/')
                reason = 'No reason provided'
            else:
                continue

            # Exact match
            if url_normalized == ignored_url:
                return True, reason

            # Domain pattern match
            try:
                parsed = urlparse(url)
                ignored_parsed = urlparse(ignored_url)
                if ignored_parsed.netloc and ignored_parsed.netloc in parsed.netloc:
                    return True, reason
            except Exception:
                pass

        return False, ''

    # ========== Link Categories (for scraper link extraction) ==========

    @property
    def link_categories(self) -> Dict[str, List[str]]:
        """Get link categorization patterns for scraper"""
        return self._config.get('link_categories', {})

    def categorize_extracted_link(self, url: str) -> List[str]:
        """Categorize an extracted link based on link_categories config"""
        categories = []
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        full_url = url.lower()

        # Check each category's patterns
        for category, patterns in self.link_categories.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                # Check if pattern appears in domain or full URL
                if pattern_lower in domain or pattern_lower in full_url or pattern_lower in path:
                    categories.append(category)
                    break  # Only add category once

        return categories if categories else ['other']

    # ========== Rate Limiting ==========

    @property
    def rate_limit_delay(self) -> float:
        """Get rate limit delay in seconds"""
        return float(self._config.get('rate_limit_delay', 1.0))

    @property
    def request_timeout(self) -> int:
        """Get HTTP request timeout in seconds"""
        return int(self._config.get('request_timeout', 30))

    # ========== User Agent ==========

    @property
    def user_agent(self) -> str:
        """Get user agent string for requests"""
        default_ua = "PolkadotBountyArchive/1.0 (https://github.com/OpenGov-Watch/bounty-archive)"
        return self._config.get('user_agent', default_ua)

    # ========== Raw Config Access ==========

    def get(self, key: str, default=None):
        """Get raw config value by key"""
        return self._config.get(key, default)

    def reload(self):
        """Reload configuration from file"""
        self._config = self._load_config()
