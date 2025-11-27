# Scraping System

This directory contains the URL scraping system for archiving bounty documentation.

## How It Works

### 1. Add URLs to Scrape

Edit `scrape-queue.yml` and add URLs you want to scrape:

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

### 2. Run the Scraping Agent

Ask an AI agent (or run a script):
```
"Please scrape the URLs in scrape-queue.yml"
```

The agent will:
1. Read `scrape-queue.yml`
2. Scrape each URL
3. Convert content to markdown
4. Save to `bounties/[id]-[name]/scraped/[domain]/[path]/`
5. Extract all outgoing links
6. Update `scrape-results.yml` with results

### 3. Review Results

Check `scrape-results.yml` to see:
- What was scraped
- Where files were saved
- List of outgoing URLs discovered

### 4. Add More URLs to Scrape

Review the `outgoing_urls` in `scrape-results.yml`. If you want to scrape any of them:
1. Copy the URL
2. Add it to `scrape-queue.yml`
3. Run the agent again

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
