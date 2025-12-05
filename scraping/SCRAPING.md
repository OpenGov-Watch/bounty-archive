# Scraping System

Archive bounty documentation with automated link discovery.

## Quick Start

```bash
cd scraping
pip install -r requirements.txt
python suggest.py      # Generate suggestions from metadata
python review.py       # Review and approve suggestions
python scraper.py      # Scrape approved URLs
```

## Workflow

1. **Extract URLs** - `suggest.py` finds URLs in bounty metadata
2. **Review** - `review.py` lets you approve/reject URLs
3. **Scrape** - `scraper.py` downloads and saves content
4. **Discover** - `suggest.py --source=links` finds new URLs from scraped pages
5. **Repeat** - Keep going until no new URLs found

## URL Classification

**Scrape URLs** → Added to queue for archiving
- Documentation (docs.*, wikis, Notion, GitBook)
- Forms (Google Forms, Typeform)
- Governance (Subsquare, Polkassembly)

**Associated URLs** → Added to metadata.yml
- GitHub repos/orgs

**Social Links** → Added to metadata.yml
- Twitter, Telegram, Discord, Matrix

## Scripts

**suggest.py** - Generate URL suggestions
```bash
python suggest.py              # From metadata
python suggest.py --source=links   # From scraped content
```

**review.py** - Interactive review
- Auto-accepts URLs matching rules in config
- Manual review for everything else
- Press [A]ccept, [I]gnore, [S]kip, [Q]uit

**scraper.py** - Main scraper
- Single mode: Just the URL
- Recursive mode: URL + internal links up to max_depth

**cleanup.py** - Maintenance
```bash
python cleanup.py stats                    # Show statistics
python cleanup.py reset-all                # Reset data (keeps scraped files)
python cleanup.py reset-all --files        # Reset everything including files
python cleanup.py remove-url "https://..."  # Remove URL to re-scrape
python cleanup.py remove-bounty 11         # Remove all URLs for bounty
```

## Scraping Modes

**Single** - Just scrape the one URL
```yaml
mode: "single"
max_depth: 1
```

**Recursive** - Follow internal links
```yaml
mode: "recursive"
max_depth: 2  # 0=initial, 1=links from initial, 2=links from depth 1
```

Internal links = same domain + same base path

## Configuration

**scrape-config.yml** - Main configuration

```yaml
default_mode: "single"  # or "recursive"

recursive_defaults:
  max_depth: 2

# Auto-accept during review
auto_accept:
  - domain: "docs.google.com"
  - domain: "notion.site"
    mode: "recursive"
    max_depth: 2

# Categorize discovered links
link_categories:
  social: ["twitter.com", "x.com", "t.me", "discord.gg"]
  github: ["github.com"]
  documentation: ["docs.", "wiki.", "notion.site", ".gitbook.io"]

# Never suggest these
ignored:
  - url: "https://youtube.com"
    reason: "Video content"
```

## File Structure

**User-managed:**
- `scrape-config.yml` - Configuration
- `scrape-queue.yml` - URLs to scrape

**Auto-generated (never edit manually):**
- `scrape-suggestions.yml` - Pending suggestions
- `scrape-index.yml` - Scraped URLs
- `scrape-results.yml` - Scraping results
- `scrape-links.yml` - Discovered links

**Scraped content:**
```
bounties/[id]-[name]/scraped/[domain]/[path]/
├── index.html
├── index.html.meta.yml
├── page.html
└── page.html.meta.yml
```

## Common Tasks

**Full archive of a bounty:**
```bash
python suggest.py
python review.py
python scraper.py
python suggest.py --source=links
python review.py
python scraper.py
# Repeat until no new URLs
```

**Re-scrape with different settings:**
```bash
python cleanup.py remove-url "https://example.com/"
# Add to scrape-queue.yml with new mode/depth
python scraper.py
```

**Fresh start:**
```bash
python cleanup.py reset-all  # Keeps scraped files
```

**Complete wipe:**
```bash
python cleanup.py reset-all --files  # Deletes everything
```

## Architecture

**Data Manager** (`data.py`) - Centralized file operations
- Type-safe using dataclasses (models.py)
- Automatic deduplication
- Built-in validation

**Configuration** (`config.py`) - Settings management
- Auto-accept rules
- URL categorization
- Ignore list

**Models** (`models.py`) - Typed data structures
- Suggestion, QueueEntry, IndexEntry
- DiscoveredLink, ScrapeResult
- Automatic validation on creation

## Troubleshooting

**No suggestions?**
```bash
python cleanup.py stats  # Check what's already indexed
```

**Want deeper scraping?**
```bash
python cleanup.py remove-url "https://example.com/"
# Edit scrape-queue.yml to increase max_depth
python scraper.py
```

**Import errors?**
```bash
pip install -r requirements.txt
```

## Best Practices

- Start with single mode, switch to recursive if needed
- Use auto-accept rules for trusted domains
- Check stats regularly with `cleanup.py stats`
- Never edit auto-generated YAML files manually
- Use cleanup.py to remove URLs before re-scraping
