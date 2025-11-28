# Scraping System

Python-based URL scraper for archiving bounty documentation.

## Quick Start

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

Scraped content is stored in:
```
bounties/
  [id]-[name]/
    scraped/
      [domain]/
        [path]/
          index.md          # Main page content (for URLs ending in /)
          page-name.md      # Sub-pages
```

**Examples:**
```
bounties/19-inkubator/scraped/use.ink/ubator/index.md
bounties/19-inkubator/scraped/use.ink/ubator/apply.md
bounties/19-inkubator/scraped/github.com/use-inkubator/Ecosystem-Grants/README.md
```

## Scraped File Format

Each scraped page includes YAML frontmatter:

```markdown
---
url: https://use.ink/ubator/
scraped_at: 2025-11-28T10:30:00Z
title: ink!ubator - Grants Program
status_code: 200
---

# Page Content

[Converted markdown content...]
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

- **Rate limiting**: 1-2 second delay between requests
- **Error handling**: Continues processing if individual URLs fail
- **Deduplication**: Tracks visited URLs to avoid re-scraping
- **Clean markdown**: Removes navigation, footers, ads
- **YAML frontmatter**: Metadata for each scraped page
- **Link extraction**: Categorized internal/external/social links
- **Recursive crawling**: Follow internal links up to specified depth

## Command Line Usage

```bash
# Run scraper with queue file
python scraper.py

# Install dependencies
pip install -r requirements.txt
```

## Files

- **scraper.py** - Python scraper script
- **requirements.txt** - Python dependencies
- **scrape-queue.yml** - URLs to scrape (input)
- **scrape-results.yml** - Scraping results (output)

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
  Saved: bounties/19-inkubator/scraped/use.ink/ubator/index.md
  Fetching: https://use.ink/ubator/apply/
  Saved: bounties/19-inkubator/scraped/use.ink/ubator/apply.md
  Fetching: https://use.ink/ubator/faq/
  Saved: bounties/19-inkubator/scraped/use.ink/ubator/faq.md

Scraping Bounty #11: https://polkadot.antiscam.team/
Mode: single
  Fetching: https://polkadot.antiscam.team/
  Saved: bounties/11-anti-scam-bounty/scraped/polkadot.antiscam.team/index.md

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
