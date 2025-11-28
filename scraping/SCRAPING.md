# Scraping System

URL scraping system for archiving bounty documentation using Claude subagents.

## Quick Start

### 1. Add URLs to Scrape

Edit `scraping/scrape-queue.yml` and add URLs:

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

Use the Task tool to invoke the scraper subagent:

```
Task(
  subagent_type: "general-purpose",
  description: "Scrape bounty documentation URLs",
  prompt: "Read the prompt from .claude/agents/scraper.md and execute the scraping tasks defined in scraping/scrape-queue.yml"
)
```

Or ask Claude directly:
```
Please use the scraper subagent (.claude/agents/scraper.md) to scrape the URLs in scraping/scrape-queue.yml
```

### 3. Review Results

Check `scraping/scrape-results.yml` to see:
- What was scraped successfully
- Where markdown files were saved
- Categorized outgoing URLs (internal/external/social)
- Any errors encountered
- Discovered URLs queue for next scraping round

### 4. Iterate

Review `discovered_queue` in `scraping/scrape-results.yml`:
1. Identify interesting URLs to scrape
2. Add them to `scraping/scrape-queue.yml`
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

See [.claude/agents/scraper.md](../.claude/agents/scraper.md) for detailed instructions for AI agents performing the scraping.

## Files

- **scraping/scrape-queue.yml** - URLs to scrape (you edit this)
- **scraping/scrape-results.yml** - Results and discovered URLs (agent updates this)
- **.claude/agents/scraper.md** - Claude subagent definition for scraping
