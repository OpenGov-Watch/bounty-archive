# Scraping System

Python-based URL scraper for archiving bounty documentation.

## Overview

The scraping system has two workflows:

1. **Automated Workflow** - Generate suggestions from bounty metadata, review them interactively
2. **Manual Workflow** - Directly add URLs to the scrape queue

## Automated Workflow (Recommended)

### 1. Install Dependencies

```bash
cd scraping
pip install -r requirements.txt
```

### 2. Generate Suggestions

Extract URLs from bounty metadata files:

```bash
python suggest.py
```

This scans all `bounties/*/metadata.yml` files and:
- Extracts URLs from all fields in `links` section and `contact.applicationForm`
- Skips already queued/scraped/ignored/suggested URLs
- Uses default mode from `scrape-config.yml` (typically "single")
- Saves suggestions to `scrape-suggestions.yml`

**Note:** All URLs are suggested with default settings. Use `review.py` to:
- Change mode from single → recursive (or vice versa)
- Modify max_depth
- Ignore unwanted URLs

### 3. Review Suggestions

Interactively process suggestions:

```bash
python review.py
```

For each suggestion, choose:
- **[A]ccept** - Add to scrape queue
- **[M]odify** - Edit bounty_id/url/mode/depth, then add to queue
- **[I]gnore** - Add to ignore list (won't be suggested again)
- **[S]kip** - Leave in suggestions for later review
- **[Q]uit** - Exit and keep remaining suggestions

### 4. Run the Scraper

```bash
python scraper.py
```

The script will:
1. Read URLs from `scrape-queue.yml`
2. Fetch pages in their original format (HTML, PDF, JSON, etc.)
3. Save files to `bounties/[id]-[slug]/scraped/[domain]/[path]/`
4. Save metadata in companion `.meta.yml` files
5. Extract and categorize outgoing links (from HTML pages)
6. Update `scrape-results.yml` with results
7. Update `scrape-index.yml` with successfully scraped URLs

### 5. Iterate

1. Run `python suggest.py` again to find new URLs
2. Review with `python review.py`
3. Scrape with `python scraper.py`

## Manual Workflow

### 1. Install Dependencies

```bash
cd scraping
pip install -r requirements.txt
```

### 2. Add URLs to Scrape

Edit `scraping/scrape-queue.yml` and add URLs:

```yaml
queue:
  - bounty_id: 19
    url: "https://use.ink/ubator/"
    mode: "recursive"     # "single" or "recursive"
    max_depth: 2          # Only for recursive mode

  - bounty_id: 11
    url: "https://polkadot.antiscam.team/"
    mode: "single"
```

**Modes:**
- `single` - Scrape just this one page, extract outgoing links
- `recursive` - Scrape this page and all internal pages under the same base URL path (up to max_depth levels)

**Internal links definition:**
- Links that share the same domain AND base URL path
- Example: If scraping `https://use.ink/ubator/`:
  - ✓ Internal: `https://use.ink/ubator/apply/` (same base path)
  - ✓ Internal: `https://use.ink/ubator/faq/` (same base path)
  - ✗ External: `https://use.ink/docs/` (different base path)

### 3. Run the Scraper

```bash
cd scraping
python scraper.py
```

The script will:
1. Read URLs from `scrape-queue.yml`
2. Fetch and convert each page to markdown
3. Save files to `bounties/[id]-[slug]/scraped/[domain]/[path]/`
4. Extract and categorize outgoing links
5. Update `scrape-results.yml` with results

### 4. Review Results

Check `scraping/scrape-results.yml` to see:
- What was scraped successfully
- Where markdown files were saved
- Categorized outgoing URLs (internal/external/social)
- Any errors encountered
- Discovered URLs queue for next scraping round

### 5. Iterate

Review `discovered_queue` in `scraping/scrape-results.yml`:
1. Identify interesting URLs to scrape
2. Add them to `scraping/scrape-queue.yml`
3. Run the scraper again

## File Structure

Scraped content is stored in original format with companion metadata files:
```
bounties/
  [id]-[name]/
    scraped/
      [domain]/
        [path]/
          index.html              # Original HTML content
          index.html.meta.yml     # Metadata for index.html
          page-name.html          # Sub-pages in original format
          page-name.html.meta.yml # Metadata
          document.pdf            # PDFs saved as-is
          document.pdf.meta.yml   # PDF metadata
```

**Examples:**
```
bounties/17-events-bounty/scraped/dotevents.xyz/index.html
bounties/17-events-bounty/scraped/dotevents.xyz/index.html.meta.yml
bounties/19-inkubator/scraped/use.ink/ubator/index.html
bounties/19-inkubator/scraped/use.ink/ubator/apply.html
```

## File Formats

The scraper preserves the original format of each URL:

- **HTML pages** → `.html` files
- **PDF documents** → `.pdf` files
- **JSON data** → `.json` files
- **Plain text** → `.txt` files
- **XML** → `.xml` files

Metadata is stored in companion `.meta.yml` files:

```yaml
url: https://dotevents.xyz/
scraped_at: '2025-11-28T11:10:07Z'
title: DOT Events Bounty
status_code: 200
original_file: index.html
```

## Link Categorization

The scraper categorizes all outgoing links:

**Internal links:**
- Same domain AND same base URL path
- In recursive mode, these are followed up to max_depth

**External links:**
- Different domain OR different base URL path
- Added to `discovered_queue` for potential future scraping

**Social links:**
- Twitter/X, Telegram, Discord, Matrix
- Filtered from generic social media (Facebook, Instagram, etc.)

**Excluded from external links:**
- google.com, youtube.com (unless specific resources)
- Generic social media already captured

## Features

- **Original format preservation**: Files saved in their native format (HTML, PDF, JSON, etc.)
- **Metadata tracking**: Companion `.meta.yml` files with URL, title, timestamp, status
- **Rate limiting**: 1-2 second delay between requests
- **Error handling**: Continues processing if individual URLs fail
- **Deduplication**: Tracks visited URLs to avoid re-scraping
- **Link extraction**: Categorized internal/external/social links (from HTML pages)
- **Recursive crawling**: Follow internal links up to specified depth
- **Multi-format support**: Handles HTML, PDF, JSON, XML, plain text, and more

## Command Line Usage

```bash
# Run scraper with queue file
python scraper.py

# Install dependencies
pip install -r requirements.txt
```

## Files

### Scripts
- **scraper.py** - Main scraper script that fetches and converts URLs to markdown
- **suggest.py** - Generates suggestions from bounty metadata files
- **review.py** - Interactive CLI to review and process suggestions
- **requirements.txt** - Python dependencies (requests, beautifulsoup4, html2text, pyyaml)

### Data Files

**User-managed files:**
- **scrape-queue.yml** - URLs queued for scraping (you curate this)
- **scrape-ignore.yml** - URLs to never suggest or scrape (you curate this)
- **scrape-config.yml** - Configuration for auto-detecting scraping mode (you can customize this)

**Auto-generated files:**
- **scrape-suggestions.yml** - Auto-generated suggestions from metadata (generated by suggest.py)
- **scrape-index.yml** - Index of successfully scraped URLs (updated by scraper.py)
- **scrape-results.yml** - Detailed scraping results and discovered URLs (updated by scraper.py)

## Troubleshooting

**No jobs in queue:**
- Make sure `scrape-queue.yml` has items in the `queue:` list
- Uncomment example entries or add your own

**Bounty folder not found:**
- Ensure bounty folder exists: `bounties/[id]-[slug]/`
- Check that bounty_id matches the folder name

**HTTP errors (403, 404, etc.):**
- Some sites block scrapers - check robots.txt
- Errors are logged in `scrape-results.yml`

**Import errors:**
- Run `pip install -r requirements.txt`
- Use a virtual environment for clean dependencies

## Example Session

```bash
$ cd scraping
$ pip install -r requirements.txt
$ python scraper.py

============================================================
Polkadot Bounty Archive - URL Scraper
============================================================

Found 2 job(s) in queue

Scraping Bounty #19: https://use.ink/ubator/
Mode: recursive, max_depth: 2
  Fetching: https://use.ink/ubator/
  Saved: bounties/19-inkubator/scraped/use.ink/ubator/index.html
  Fetching: https://use.ink/ubator/apply/
  Saved: bounties/19-inkubator/scraped/use.ink/ubator/apply.html
  Fetching: https://use.ink/ubator/faq/
  Saved: bounties/19-inkubator/scraped/use.ink/ubator/faq.html

Scraping Bounty #11: https://polkadot.antiscam.team/
Mode: single
  Fetching: https://polkadot.antiscam.team/
  Saved: bounties/11-anti-scam-bounty/scraped/polkadot.antiscam.team/index.html

Results saved to: scraping/scrape-results.yml

============================================================
SUMMARY
============================================================
Jobs processed: 2
  ✓ Completed: 2
  ✗ Failed: 0

Pages scraped: 4
Errors: 0

Files saved to:
  - bounties/19-inkubator/scraped/
  - bounties/11-anti-scam-bounty/scraped/

============================================================
```

## Advanced Usage

### Custom Base URL Path Detection

The scraper automatically determines the "base path" from the initial URL:
- `https://use.ink/ubator/` → base path: `/ubator/`
- `https://example.com/docs/v2/` → base path: `/docs/v2/`

Internal links must start with this base path to be followed in recursive mode.

### Depth Levels

In recursive mode with `max_depth: 2`:
- **Depth 0**: Initial URL
- **Depth 1**: Internal links found on initial page
- **Depth 2**: Internal links found on depth 1 pages
- **Stop**: Don't process depth 3

### Discovered Queue

External links are added to `discovered_queue` in results file:
```yaml
discovered_queue:
  - url: "https://github.com/use-inkubator/Ecosystem-Grants"
    found_on: "https://use.ink/ubator/"
    bounty_id: 19
```

Review this queue and manually add interesting URLs to `scrape-queue.yml` for the next run.

## Data File Formats

### scrape-queue.yml (User Managed)

URLs you want to scrape:

```yaml
queue:
  - bounty_id: 19
    url: "https://use.ink/ubator/"
    mode: "recursive"
    max_depth: 2
  - bounty_id: 11
    url: "https://polkadot.antiscam.team/"
    mode: "single"
```

### scrape-ignore.yml (User Managed)

URLs to never suggest or scrape:

```yaml
ignored:
  - url: "https://example.com/irrelevant"
    reason: "Not useful content"  # Optional
  - url: "https://twitter.com"
    reason: "Social media - not documentation"
  - url: "https://forms.google.com"
    reason: "Form - not documentation"
```

**Tip:** Use `review.py` to quickly add URLs to the ignore list.

### scrape-config.yml (User Managed)

Configuration for default scraping settings:

```yaml
version: "1.0"

# Default mode for all suggestions
default_mode: "single"  # or "recursive"

# Settings for recursive mode
recursive_defaults:
  max_depth: 2

# Settings for single page mode
single_defaults:
  max_depth: 1
```

**How it works:**
- All suggested URLs use `default_mode` (typically "single")
- You can change the mode per-URL when reviewing with `review.py`
- The depth settings are used when you select that mode

### scrape-suggestions.yml (Auto-Generated)

Suggestions from metadata files (processed with `review.py`):

```yaml
version: "1.0"
last_generated: "2025-11-28T10:00:00Z"
suggestions:
  - bounty_id: 19
    url: "https://use.ink/ubator/"
    mode: "recursive"
    max_depth: 2
    source: "metadata.links.website"
```

### scrape-index.yml (Auto-Generated)

Index of successfully scraped URLs:

```yaml
version: "1.0"
last_updated: "2025-11-28T10:30:00Z"
index:
  - url: "https://polkadot.antiscam.team/"
    bounty_id: 11
    scraped_at: "2025-11-28T10:25:00Z"
    location: "bounties/11-anti-scam-bounty/scraped/polkadot.antiscam.team/"
    pages: 1
```

### scrape-results.yml (Auto-Generated)

Detailed scraping results and discovered URLs:

```yaml
version: "1.0"
last_updated: "2025-11-28T10:30:00Z"
scraped:
  - bounty_id: 19
    url: "https://use.ink/ubator/"
    mode: "recursive"
    status: "completed"
    pages_scraped: 3
    files_created:
      - "bounties/19-inkubator/scraped/use.ink/ubator/index.html"
      - "bounties/19-inkubator/scraped/use.ink/ubator/apply.html"
    outgoing_urls:
      internal: [...]
      external: [...]
      social: [...]
    errors: []
discovered_queue:
  - url: "https://github.com/use-inkubator/Ecosystem-Grants"
    found_on: "https://use.ink/ubator/"
    bounty_id: 19
```

## Workflow Diagram

```
Bounty Metadata Files
         ↓
    [suggest.py] ──→ scrape-suggestions.yml
         ↓
    [review.py] ──→ scrape-queue.yml
         ↓          scrape-ignore.yml
    [scraper.py] ──→ scraped/*.md files
         ↓          scrape-results.yml
         └────────→ scrape-index.yml
```
