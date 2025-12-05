# Website Scripts

## ⚠️ Status: No Build Step Required

**As of December 2025**, this folder contains deprecated scripts. The website now loads scraped content directly from `scraping/scrape-index.yml` without requiring a build step.

## Deprecated Scripts

### build_scraped_index.py ❌ DEPRECATED

**This script is no longer used or needed.**

Previously, this script scanned bounty folders and generated `scraped-index.json` for the website. It has been replaced by client-side YAML loading.

### Why It Was Deprecated

1. **Simpler deployment**: No Python build step required
2. **Single source of truth**: `scraping/scrape-index.yml` is the only index
3. **Automatic updates**: Changes are immediately reflected on the website
4. **Fewer moving parts**: No JSON generation or sync issues between files

## Current Website Integration

The `index.html` file now:
1. **Loads `scraping/scrape-index.yml` directly** using js-yaml parser (already included)
2. **Transforms it client-side** into the display structure
3. **Filters to successful scrapes only** (excludes failed entries)
4. **Displays scraped documentation** on bounty cards with modal file tree

### Data Flow

```
scraping/scrape-index.yml  →  Website (index.html)  →  User sees scraped docs
     (single source)              (js-yaml parser)          (interactive UI)
```

### File Paths

Scraped content is stored as:
- **Files**: `bounties/{id}-{slug}/scraped/{domain}/{path}.html`
- **Index**: `scraping/scrape-index.yml` (loaded by website)
- **Metadata**: `{file}.meta.yml` (contains title, URL, timestamps)

## Migration Notes

If you need to update the GitHub Actions workflow:

**Old workflow (remove this):**
```yaml
- name: Build scraped index
  run: python website/build_scraped_index.py
```

**New workflow (no build step needed):**
```yaml
# No build step required - website loads YAML directly
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./
```

## Future Scripts

This folder is kept for any future website build scripts that may be needed. Current requirements:
- ✅ Scraped content indexing: Handled by scrape-index.yml (no build needed)
- ✅ Metadata parsing: Handled client-side with js-yaml
- ✅ File organization: Handled by scraping system
