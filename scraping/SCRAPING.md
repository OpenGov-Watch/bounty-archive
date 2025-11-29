# Scraping System Documentation

Python-based URL scraper for archiving bounty documentation with automated link discovery.

## Quick Start

```bash
cd scraping
pip install -r requirements.txt
python suggest.py      # Generate suggestions from metadata
python review.py       # Review and approve suggestions
python scraper.py      # Scrape approved URLs
python discover.py     # Discover new URLs from scraped content
```

## Overview

The scraping system automatically archives bounty documentation with intelligent link discovery:

1. **Extract URLs** from bounty metadata → suggestions
2. **Review suggestions** → scrape queue + metadata
3. **Scrape content** → archive + extract links
4. **Discover new URLs** → generate new suggestions
5. **Repeat** for comprehensive coverage

## Three-Tier URL Classification

All discovered URLs are classified into three types:

### 1. **Scrape URLs** → Queue for scraping
- **Documentation** (docs.*, wiki.*, notion.site, .gitbook.io)
- **Forms** (Google Forms, Typeform, etc.)
- **Governance** (Subsquare, Polkassembly)
- **Other** (general content)

→ Added to `scrape-queue.yml` for archiving

### 2. **Associated URLs** → Metadata reference
- **GitHub** (repositories, organizations)

→ Added to `metadata.yml` under `associated_urls`
→ Displayed in "Associated URLs" section on website

### 3. **Associated Socials** → Metadata reference
- **Twitter/X**, **Telegram**, **Discord**, **Matrix**

→ Added to `metadata.yml` under `associated_socials`
→ Displayed in "Associated Socials" section on website

## Complete Workflow

### 1. Generate Suggestions from Metadata

```bash
python suggest.py
```

Extracts URLs from all `bounties/*/metadata.yml` files:
- Scans `links.*` fields (website, documentation, application)
- Scans `contact.applicationForm`
- Filters out already queued/scraped/ignored URLs
- Generates suggestions with default mode (typically `single`)

**Output:** `scrape-suggestions.yml`

### 2. Review Suggestions

```bash
python review.py
```

Interactive review with auto-accept rules:

**Auto-Accept (Silent):**
- URLs matching `auto_accept` rules in `scrape-config.yml`
- Automatically added to `scrape-queue.yml`

**Manual Review:**
For each suggestion, choose:
- **[A]ccept** - Add to appropriate destination:
  - **Scrape URLs** → `scrape-queue.yml`
  - **Associated URLs** → `metadata.yml` under `associated_urls`
  - **Associated Socials** → `metadata.yml` under `associated_socials`
- **[M]odify** - Edit bounty_id/url/mode/depth (scrape URLs only)
- **[I]gnore** - Add to `scrape-ignore.yml` (never suggest again)
- **[S]kip** - Leave in suggestions for later
- **[Q]uit** - Exit and keep remaining suggestions

**Output:**
- `scrape-queue.yml` (scrape URLs)
- `metadata.yml` files (associated URLs and socials)
- `scrape-ignore.yml` (ignored URLs)

### 3. Scrape URLs

```bash
python scraper.py
```

Processes all URLs in `scrape-queue.yml`:
- Fetches pages in original format (HTML, PDF, JSON, etc.)
- Saves to `bounties/[id]-[slug]/scraped/[domain]/[path]/`
- Creates companion `.meta.yml` files with metadata
- Extracts and categorizes outgoing links (from HTML)
- Updates `scrape-index.yml` with successfully scraped URLs
- Saves discovered links to `scrape-links.yml`

**Scraping Modes:**
- **single** - Scrape just this page
- **recursive** - Follow internal links up to `max_depth`

**Output:**
- Scraped files in `bounties/*/scraped/`
- `scrape-index.yml` (index of scraped URLs)
- `scrape-links.yml` (discovered links with categories)
- `scrape-results.yml` (detailed results)

### 4. Discover New URLs

```bash
python discover.py
```

Analyzes `scrape-links.yml` to find new URLs:
- Filters out already scraped/queued/ignored/suggested URLs
- Classifies into three types (scrape/associated_url/social)
- Generates new suggestions

**Output:** `scrape-suggestions.yml` (appended with new suggestions)

### 5. Iterate

Repeat steps 2-4 to discover and archive nested documentation:

```bash
python review.py    # Review newly discovered URLs
python scraper.py   # Scrape approved URLs
python discover.py  # Find more links
```

## Common Procedures

### Fresh Start (Reset Everything)

To start over from scratch:

```bash
python cleanup.py reset-all
```

This clears all auto-generated data:
- ✓ `scrape-index.yml` (all indexed URLs)
- ✓ `scrape-results.yml` (all scraping results)
- ✓ `scrape-links.yml` (all discovered links)
- ✓ `scrape-suggestions.yml` (all pending suggestions)

**Preserved files:**
- Scraped content in `bounties/*/scraped/`
- Your configuration (`scrape-config.yml`)
- Your ignore list (`scrape-ignore.yml`)
- Your queue (`scrape-queue.yml`)

**After reset, start fresh:**
```bash
python suggest.py   # Re-generate suggestions from metadata
python review.py    # Review suggestions
python scraper.py   # Start scraping
```

### Complete Run from Start

To scrape all bounties comprehensively:

```bash
# 1. Fresh start (optional)
python cleanup.py reset-all

# 2. Generate initial suggestions from metadata
python suggest.py

# 3. Review and approve suggestions
python review.py

# 4. Scrape approved URLs
python scraper.py

# 5. Discover links from scraped content
python discover.py

# 6. Review newly discovered URLs
python review.py

# 7. Scrape new URLs
python scraper.py

# 8. Repeat steps 5-7 until no new URLs are found
python discover.py
python review.py
python scraper.py
```

### Augmentary Runs (Go Deeper)

To re-scrape a site more thoroughly (e.g., switch from `single` to `recursive`):

**Option 1: Remove from index and re-scrape**
```bash
# 1. Remove URL from index
python cleanup.py remove-url "https://polkadot.antiscam.team/"

# 2. Add to queue with recursive mode
# Edit scrape-queue.yml:
# - bounty_id: 11
#   url: "https://polkadot.antiscam.team/"
#   mode: "recursive"
#   max_depth: 2

# 3. Scrape recursively
python scraper.py

# 4. Discover new links
python discover.py
```

**Option 2: Remove entire bounty and re-scrape**
```bash
# 1. Remove all URLs for bounty from index
python cleanup.py remove-bounty 11

# 2. Re-generate suggestions for that bounty
python suggest.py

# 3. Review with different settings (e.g., recursive mode)
python review.py

# 4. Scrape
python scraper.py
```

### View Index Statistics

```bash
python cleanup.py stats
```

Shows:
- Total indexed URLs
- Breakdown by bounty
- Last update timestamp

## File Structure

```
scraping/
├── scraper.py              # Main scraper
├── suggest.py              # Generate suggestions from metadata
├── review.py               # Interactive review tool
├── discover.py             # Discover new URLs from scraped content
├── cleanup.py              # Reset/cleanup tool
├── requirements.txt        # Python dependencies
├── SCRAPING.md            # This documentation
│
├── scrape-config.yml      # Configuration (user-managed)
├── scrape-queue.yml       # Scrape queue (user-managed)
├── scrape-ignore.yml      # Ignore list (user-managed)
│
├── scrape-suggestions.yml # Auto-generated suggestions
├── scrape-index.yml       # Index of scraped URLs
├── scrape-results.yml     # Detailed scraping results
└── scrape-links.yml       # Discovered links with categories
```

## Scraped Content Structure

```
bounties/
  [id]-[name]/
    scraped/
      [domain]/
        [path]/
          index.html              # Original HTML
          index.html.meta.yml     # Metadata
          page-name.html          # Sub-pages
          page-name.html.meta.yml
          document.pdf            # PDFs
          document.pdf.meta.yml
```

**Examples:**
```
bounties/11-anti-scam-bounty/scraped/polkadot.antiscam.team/
├── index.html
├── index.html.meta.yml
├── bounty.html
└── bounty.html.meta.yml

bounties/19-inkubator/scraped/use.ink/ubator/
├── index.html
├── index.html.meta.yml
├── apply.html
└── apply.html.meta.yml
```

## Configuration

### scrape-config.yml

```yaml
version: "1.0"

# Default mode for suggestions
default_mode: "single"  # or "recursive"

# Recursive mode defaults
recursive_defaults:
  max_depth: 2

# Auto-accept rules (silent approval during review)
auto_accept:
  - domain: "docs.google.com"
  - domain: "notion.site"
    mode: "recursive"
    max_depth: 2

# Link categorization (for discovered links)
link_categories:
  social:
    - "twitter.com"
    - "x.com"
    - "telegram.org"
    - "t.me"
    - "discord.gg"
    - "discord.com"
    - "matrix.to"
  github:
    - "github.com"
  documentation:
    - "docs."
    - "wiki."
    - "notion.site"
    - ".gitbook.io"
  governance:
    - "subsquare.io"
    - "polkassembly.io"
  forms:
    - "forms.gle"
    - "google.com/forms"
    - "typeform.com"
```

### Auto-Accept Rules

URLs matching `auto_accept` rules are automatically approved:

```yaml
auto_accept:
  # Auto-accept with default mode
  - domain: "docs.google.com"

  # Auto-accept with specific mode
  - domain: "notion.site"
    mode: "recursive"
    max_depth: 2
```

**Benefits:**
- Skip manual review for trusted domains
- Automatically apply appropriate scraping mode
- Faster workflow for large batches

## Link Categories

The scraper categorizes all discovered links using patterns in `link_categories`:

### Social (→ Associated Socials in metadata)
- Twitter/X, Telegram, Discord, Matrix
- NOT scraped, added to metadata

### GitHub (→ Associated URLs in metadata)
- GitHub repositories and organizations
- NOT scraped, added to metadata as reference

### Documentation (→ Scraped)
- Official docs, wikis, Notion pages, GitBook
- Scraped and archived

### Forms (→ Scraped)
- Google Forms, Typeform, etc.
- Scraped for archival

### Governance (→ Scraped)
- Subsquare, Polkassembly
- Scraped for reference

### Other (→ Scraped)
- Anything not matching above patterns
- Scraped by default

## Advanced Usage

### Recursive Scraping

In recursive mode with `max_depth: 2`:
- **Depth 0**: Initial URL
- **Depth 1**: Internal links found on initial page
- **Depth 2**: Internal links found on depth 1 pages
- **Stop**: Don't process depth 3

**Internal links = Same domain + same base path**

Example: Scraping `https://use.ink/ubator/` recursively
- ✓ Internal: `https://use.ink/ubator/apply/` (same base path `/ubator/`)
- ✓ Internal: `https://use.ink/ubator/faq/` (same base path)
- ✗ External: `https://use.ink/docs/` (different base path)
- ✗ External: `https://github.com/paritytech/ink` (different domain)

### Custom Mode per URL

During review, press **[M]** to modify settings:
- Change bounty ID
- Edit URL
- Switch mode (single ↔ recursive)
- Adjust max_depth

### Ignoring URLs

Add URLs to ignore list during review or manually:

```yaml
# scrape-ignore.yml
ignored:
  - url: "https://example.com/irrelevant"
    reason: "Not useful"
  - url: "https://youtube.com"
    reason: "Video content, not documentation"
```

**Pattern matching:**
- Exact URL match
- Domain pattern match (e.g., `youtube.com` matches all YouTube URLs)

## Metadata Integration

### Associated Socials

Discovered social links are automatically added to bounty metadata:

```yaml
# bounties/11-anti-scam-bounty/metadata.yml
associated_socials:
  twitter:
    - "@DotAntiScam"
  telegram:
    - "polkadot_antiscam"
  discord:
    - "https://discord.gg/xyz"
```

**Displayed on website** in "Associated Socials" section grouped by platform.

### Associated URLs

Discovered GitHub links are automatically added to bounty metadata:

```yaml
# bounties/11-anti-scam-bounty/metadata.yml
associated_urls:
  github:
    - "https://github.com/org/repo"
    - "https://github.com/org/another-repo"
```

**Displayed on website** in "Associated URLs" section grouped by category.

## Troubleshooting

### No suggestions generated

**Cause:** All URLs already scraped/queued/ignored/suggested

**Solution:**
```bash
python cleanup.py stats  # Check what's indexed
python cleanup.py reset-all  # Reset if needed
python suggest.py  # Regenerate
```

### Want to re-scrape a URL

**Solution:**
```bash
python cleanup.py remove-url "https://example.com/"
# Then add to queue and scrape again
```

### Recursive scrape didn't go deep enough

**Solution:**
```bash
# Remove from index
python cleanup.py remove-url "https://example.com/"

# Add to queue with higher depth
# Edit scrape-queue.yml:
# - url: "https://example.com/"
#   mode: "recursive"
#   max_depth: 3  # Increase depth

# Scrape again
python scraper.py
```

### Import errors

```bash
pip install -r requirements.txt
```

### HTTP errors (403, 404)

**Cause:** Some sites block scrapers or URLs are invalid

**Solution:**
- Check `scrape-results.yml` for error details
- Some sites require browser-like requests (not currently supported)
- Invalid URLs should be ignored

## Data Files Reference

### scrape-config.yml (User-Managed)
Configuration for scraping defaults and auto-accept rules.

### scrape-queue.yml (User-Managed)
URLs approved for scraping:
```yaml
queue:
  - bounty_id: 11
    url: "https://example.com/"
    mode: "recursive"
    max_depth: 2
    categories: ["documentation"]  # Preserved from suggestions
```

### scrape-ignore.yml (User-Managed)
URLs to never suggest or scrape:
```yaml
ignored:
  - url: "https://example.com/ignore"
    reason: "Not relevant"
```

### scrape-suggestions.yml (Auto-Generated)
Pending suggestions awaiting review:
```yaml
version: "1.0"
last_generated: "2025-11-28T10:00:00Z"
suggestions:
  - bounty_id: 11
    url: "https://example.com/"
    mode: "single"
    max_depth: 1
    source: "discovered from https://parent.com/"
    categories: ["documentation"]
    type: "scrape"  # or "associated_url" or "social"
```

### scrape-index.yml (Auto-Generated)
Index of successfully scraped URLs:
```yaml
version: "1.0"
last_updated: "2025-11-28T10:30:00Z"
index:
  - url: "https://example.com/"
    bounty_id: 11
    scraped_at: "2025-11-28T10:25:00Z"
    location: "bounties/11-example/scraped/example.com/"
    pages: 1
```

### scrape-links.yml (Auto-Generated)
All discovered links with categorization:
```yaml
version: "1.0"
last_updated: "2025-11-28T10:30:00Z"
total_links: 397
discovered_links:
  - url: "https://github.com/org/repo"
    source_url: "https://example.com/"
    bounty_id: 11
    categories: ["github"]
    discovered_at: "2025-11-28T10:25:00Z"
  - url: "https://docs.example.com/"
    source_url: "https://example.com/"
    bounty_id: 11
    categories: ["documentation"]
    discovered_at: "2025-11-28T10:25:00Z"
```

### scrape-results.yml (Auto-Generated)
Detailed scraping results:
```yaml
version: "1.0"
last_updated: "2025-11-28T10:30:00Z"
scraped:
  - bounty_id: 11
    url: "https://example.com/"
    mode: "recursive"
    status: "completed"
    pages_scraped: 3
    visited_urls:  # All URLs scraped during recursive crawl
      - "https://example.com/"
      - "https://example.com/page1"
      - "https://example.com/page2"
    files_created:
      - "bounties/11-example/scraped/example.com/index.html"
      - "bounties/11-example/scraped/example.com/page1.html"
    errors: []
```

## Best Practices

1. **Start with suggest.py** - Let it discover URLs from metadata
2. **Use auto-accept rules** - Speed up review for trusted domains
3. **Start with single mode** - Test before going recursive
4. **Iterate discover → review → scrape** - Find nested documentation
5. **Check stats regularly** - `python cleanup.py stats`
6. **Backup before reset** - Data files are not versioned
7. **Use cleanup.py for augmentary runs** - Remove from index before re-scraping

## Workflow Diagram

```
┌─────────────────────┐
│ Bounty Metadata     │
│ (metadata.yml)      │
└──────────┬──────────┘
           │
           ▼
     [suggest.py]
           │
           ▼
┌─────────────────────┐
│ scrape-suggestions  │◄───────────┐
└──────────┬──────────┘            │
           │                       │
           ▼                       │
      [review.py]                  │
           │                       │
     ┌─────┴─────┐                 │
     ▼           ▼                 │
┌─────────┐ ┌──────────┐           │
│  queue  │ │ metadata │           │
│  .yml   │ │   .yml   │           │
└────┬────┘ └──────────┘           │
     │                             │
     ▼                             │
[scraper.py]                       │
     │                             │
     ├─────► scraped files         │
     ├─────► scrape-index.yml      │
     └─────► scrape-links.yml      │
                    │               │
                    ▼               │
              [discover.py]─────────┘
```

## Example: Complete Archive of a Bounty

Let's archive Bounty #11 (Anti-Scam) comprehensively:

```bash
# 1. Generate initial suggestion
python suggest.py
# Finds: https://polkadot.antiscam.team/ (from metadata)

# 2. Review and approve
python review.py
# Accept: https://polkadot.antiscam.team/ (single mode)

# 3. Scrape homepage
python scraper.py
# Scraped: 1 page
# Discovered: 10 links (including /bounty, /team, GitHub, Twitter)

# 4. Discover new URLs
python discover.py
# New suggestions:
#   - https://polkadot.antiscam.team/bounty (type: scrape)
#   - https://polkadot.antiscam.team/team (type: scrape)
#   - https://github.com/org/repo (type: associated_url)
#   - https://twitter.com/DotAntiScam (type: social)

# 5. Review new suggestions
python review.py
# Accept /bounty → queue
# Accept /team → queue
# Accept GitHub → metadata (associated_urls)
# Accept Twitter → metadata (associated_socials)

# 6. Scrape new pages
python scraper.py
# Scraped: /bounty, /team
# Discovered: More links

# 7. Repeat until no new URLs
python discover.py
python review.py
python scraper.py

# Result: Comprehensive archive with:
# - All pages scraped
# - GitHub repos in metadata
# - Social links in metadata
# - Website displays everything
```

## Version History

- **v1.0** - Initial scraping system with queue-based workflow
- **v1.1** - Added link extraction and categorization
- **v1.2** - Added discover.py for automated link discovery
- **v1.3** - Added three-tier classification (scrape/associated_url/social)
- **v1.4** - Added cleanup.py for reset and augmentary runs
