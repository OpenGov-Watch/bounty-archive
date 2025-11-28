# Website Build Pipeline

This folder contains scripts that process scraped content and generate data files for the website.

## Scripts

### build_scraped_index.py

Scans all bounty folders for scraped documentation and generates `scraped-index.json`.

**What it does:**
- Walks through `bounties/*/scraped/` directories
- Reads `.meta.yml` files for URLs, titles, and timestamps
- Builds a tree structure organized by bounty ID and domain
- Outputs JSON file with all scraped files and metadata

**Output format:**
```json
{
  "generated_at": "2025-11-28T12:00:00Z",
  "bounty_count": 2,
  "total_domains": 3,
  "total_files": 5,
  "bounties": {
    "10": {
      "domains": [
        {
          "domain": "example.com",
          "file_count": 3,
          "files": [
            {
              "path": "index.html",
              "name": "index.html",
              "url": "https://example.com/",
              "title": "Example Page",
              "scraped_at": "2025-11-28T12:00:00Z"
            }
          ]
        }
      ]
    }
  }
}
```

**Run manually:**
```bash
python website/build_scraped_index.py
```

**Run automatically:**
The GitHub Actions workflow (`.github/workflows/pages.yml`) runs this script before deploying to GitHub Pages.

## Integration with Website

The `index.html` file:
1. Loads `scraped-index.json` on page load
2. Displays "Scraped Documentation" section on bounty cards when content exists
3. Shows domain chips and file counts
4. Opens modal with full file tree when clicked

## Adding More Build Scripts

To add new build scripts:
1. Create a new Python script in this folder
2. Add it to `.github/workflows/pages.yml` under the build steps
3. Document it in this README

## Dependencies

- Python 3.12+
- PyYAML

Install dependencies:
```bash
pip install pyyaml
```
