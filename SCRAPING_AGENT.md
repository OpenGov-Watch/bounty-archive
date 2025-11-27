# Scraping Agent Instructions

Instructions for AI agents performing URL scraping for the bounty archive.

## Task Overview

Scrape URLs from `scrape-queue.yml`, convert to markdown, store in bounty folders, and track results in `scrape-results.yml`.

## Process

### 1. Read Input

Load `scrape-queue.yml` to get the list of URLs to scrape.

### 2. For Each URL in Queue

#### A. Scrape the Page

- Fetch the URL content
- If mode is `single`: scrape only this page
- If mode is `recursive`: scrape this page and follow internal links up to `max_depth`

**Internal links definition:**
- Links that start with the same base URL path
- Example: If scraping `https://use.ink/ubator/`, internal links are:
  - `https://use.ink/ubator/apply/` ✓
  - `https://use.ink/ubator/faq/` ✓
  - `https://use.ink/docs/` ✗ (different path)

#### B. Convert to Markdown

- Convert HTML to clean markdown
- Preserve headings, links, lists, code blocks
- Remove navigation, footers, ads if possible
- Add metadata header:

```markdown
---
url: https://use.ink/ubator/
scraped_at: 2025-11-27T10:00:00Z
title: ink!ubator - Smart Contract Grants
---

# Page content here...
```

#### C. Save to File

Determine the file path:
```
bounties/[bounty-id]-[bounty-slug]/scraped/[domain]/[path]/[filename].md
```

Examples:
- `https://use.ink/ubator/` → `bounties/19-inkubator/scraped/use.ink/ubator/index.md`
- `https://use.ink/ubator/apply/` → `bounties/19-inkubator/scraped/use.ink/ubator/apply.md`
- `https://use.ink/ubator/faq/` → `bounties/19-inkubator/scraped/use.ink/ubator/faq.md`

**File naming:**
- Root path (e.g., `/ubator/`) → `index.md`
- Sub-paths (e.g., `/ubator/apply/`) → `apply.md` or `apply/index.md`

Create directories as needed.

#### D. Extract Outgoing Links

From each page, extract all links and categorize:

**Internal links**: Same base URL path
- `https://use.ink/ubator/apply/`
- `https://use.ink/ubator/faq/`

**External links**: Different domains or paths
- `https://github.com/use-inkubator/Ecosystem-Grants`
- `https://polkadot.network/`
- `https://docs.google.com/...`

**Social links**: Social media domains
- `https://twitter.com/ink_lang`
- `https://t.me/...`
- `https://discord.com/...`
- `https://matrix.to/...`

#### E. Handle Recursive Mode

If `mode: "recursive"`:
1. Queue all internal links found
2. Track depth (starting URL is depth 0)
3. Only scrape links within `max_depth`
4. Don't scrape the same URL twice

### 3. Update Results File

Update `scrape-results.yml` with:
- URL scraped
- Status (completed, failed, partial)
- Timestamp
- Number of pages scraped
- List of files created
- Categorized outgoing URLs
- Any errors encountered

### 4. Update Discovered Queue

Add interesting external links to the `discovered_queue` section of `scrape-results.yml` for user review.

**Exclude from discovered queue:**
- Social media links (already tracked in metadata.yml)
- Generic sites (google.com, youtube.com, etc.)
- Already scraped URLs

**Include in discovered queue:**
- GitHub repos
- Documentation sites
- Official bounty resources
- Google Docs/Sheets
- Forum posts
- Notion pages

## Error Handling

If a URL fails:
- Record the error in results
- Continue with other URLs
- Don't stop the entire process

Common errors:
- 404 Not Found
- 403 Forbidden
- Timeout
- Invalid SSL
- Rate limiting

## Quality Guidelines

**DO:**
- Preserve all content structure
- Keep links functional
- Include images as markdown image links
- Note if content couldn't be converted properly
- Respect rate limits (add delays between requests)
- Check robots.txt

**DON'T:**
- Scrape infinitely (respect max_depth)
- Scrape the same URL multiple times
- Include sensitive data
- Scrape social media timelines
- Scrape login-required pages

## Output Format

### scrape-results.yml structure:

```yaml
version: "1.0"
last_updated: "2025-11-27T10:30:00Z"

scraped:
  - bounty_id: 19
    url: "https://use.ink/ubator/"
    mode: "recursive"
    max_depth: 2
    status: "completed"
    scraped_at: "2025-11-27T10:00:00Z"
    pages_scraped: 5
    files_created:
      - "bounties/19-inkubator/scraped/use.ink/ubator/index.md"
      - "bounties/19-inkubator/scraped/use.ink/ubator/apply.md"
      - "bounties/19-inkubator/scraped/use.ink/ubator/faq.md"
    outgoing_urls:
      internal:
        - "https://use.ink/ubator/apply/"
        - "https://use.ink/ubator/faq/"
      external:
        - "https://github.com/use-inkubator/Ecosystem-Grants"
        - "https://github.com/use-inkubator/Grant-Milestone-Delivery"
        - "https://polkadot.network/"
      social:
        - "https://twitter.com/ink_lang"
        - "https://matrix.to/#/#sm-bounty-support:matrix.org"
    errors: []

discovered_queue:
  - url: "https://github.com/use-inkubator/Ecosystem-Grants"
    found_on: "https://use.ink/ubator/"
    reason: "Application repository"

  - url: "https://github.com/use-inkubator/Grant-Milestone-Delivery"
    found_on: "https://use.ink/ubator/"
    reason: "Milestone delivery repository"
```

## After Completion

1. Commit all scraped files
2. Update scrape-results.yml
3. Clear processed items from scrape-queue.yml
4. Notify user of results
5. Suggest reviewing discovered_queue for next round

## Example Workflow

```
User adds to scrape-queue.yml:
  - bounty_id: 19
    url: "https://use.ink/ubator/"
    mode: "recursive"
    max_depth: 1

Agent:
  1. Scrapes https://use.ink/ubator/ → saves to .../ubator/index.md
  2. Finds internal links: /ubator/apply/, /ubator/faq/
  3. Scrapes those (depth 1) → saves to .../ubator/apply.md, .../ubator/faq.md
  4. Finds external link: https://github.com/use-inkubator/Ecosystem-Grants
  5. Updates scrape-results.yml with all outgoing links
  6. Adds GitHub repo to discovered_queue

User reviews discovered_queue:
  - Decides to scrape GitHub repo
  - Adds to scrape-queue.yml:
    - bounty_id: 19
      url: "https://github.com/use-inkubator/Ecosystem-Grants"
      mode: "single"

Agent scrapes GitHub repo...
```

---

**Remember:** Keep it simple, respect rate limits, preserve content quality, and provide clear results.
