# Scraping System

URL scraping system for archiving bounty documentation using Claude subagents.

## Quick Start

### 1. Add URLs to Scrape

Edit `scrape-queue.yml` and add URLs:

```yaml
queue:
  - bounty_id: 19
    url: "https://use.ink/ubator/"
    mode: "recursive"     # "single" or "recursive"
    max_depth: 2          # Only for recursive mode
```

**Modes:**
- `single` - Scrape just this one page, extract outgoing links
- `recursive` - Scrape this page and all pages under this URL path (respects max_depth)

### 2. Invoke the Scraper Subagent

Use the Task tool to invoke the scraper:

```
I need you to scrape the URLs in scrape-queue.yml. Use the general-purpose subagent and follow the instructions in SCRAPING_AGENT.md.

Please:
1. Read scrape-queue.yml for the list of URLs
2. Fetch each URL using WebFetch
3. Convert content to markdown with YAML frontmatter
4. Save files to bounties/[id]-[slug]/scraped/[domain]/[path]/
5. Extract and categorize outgoing links
6. Update scrape-results.yml with results and discovered links
```

Or more simply:
```
Please scrape the URLs in scrape-queue.yml following SCRAPING_AGENT.md instructions
```

### 3. Review Results

Check `scrape-results.yml` to see:
- What was scraped successfully
- Where markdown files were saved
- Categorized outgoing URLs (internal/external/social)
- Any errors encountered
- Discovered URLs queue for next scraping round

### 4. Iterate

Review `discovered_queue` in `scrape-results.yml`:
1. Identify interesting URLs to scrape
2. Add them to `scrape-queue.yml`
3. Invoke the scraper again

## File Locations

Scraped content is stored in:
```
bounties/
  [id]-[name]/
    scraped/
      [domain]/
        [path]/
          index.md          # Main page content
          page-name.md      # Sub-pages
```

Example:
```
bounties/19-inkubator/scraped/use.ink/ubator/index.md
bounties/19-inkubator/scraped/use.ink/ubator/apply.md
bounties/19-inkubator/scraped/github.com/use-inkubator/Ecosystem-Grants/README.md
```

## Agent Instructions

See [SCRAPING_AGENT.md](SCRAPING_AGENT.md) for detailed instructions for AI agents performing the scraping.

## Files

- **scrape-queue.yml** - URLs to scrape (you edit this)
- **scrape-results.yml** - Results and discovered URLs (agent updates this)
- **SCRAPING_AGENT.md** - Instructions for AI agents
