# Polkadot Bounty Archive

> 🌐 **[View the Interactive Website →](https://opengov-watch.github.io/bounty-archive/)**

Archive of Polkadot bounty documentation with structured metadata and an interactive website.

## Overview

This repository contains comprehensive documentation for all 20 active Polkadot Treasury bounties, including:
- Detailed README files with bounty information
- Structured YAML metadata for programmatic access
- Interactive web interface for browsing all bounties

## Structure

Each bounty has its own folder in `/bounties` following the pattern `id-name`:

```
bounties/
  19-inkubator/
  43-meetups-bounty/
  52-ux-bounty/
  ...
```

## Active Bounties (20 Total)

- [#10 – Polkadot Pioneers Bounty](https://polkadot.subsquare.io/treasury/bounties/10)
- [#11 – Anti-Scam Bounty](https://polkadot.subsquare.io/treasury/bounties/11)
- [#17 – Events Bounty](https://polkadot.subsquare.io/treasury/bounties/17)
- [#19 – Ink!ubator (Wasm Smart Contracts)](https://polkadot.subsquare.io/treasury/bounties/19)
- [#22 – Polkadot Assurance Legion Bounty](https://polkadot.subsquare.io/treasury/bounties/22)
- [#24 – Moderation Team Bounty](https://polkadot.subsquare.io/treasury/bounties/24)
- [#31 – Public RPCs for Relay and System Chains](https://polkadot.subsquare.io/treasury/bounties/31)
- [#32 – System Parachains Collator Bounty](https://polkadot.subsquare.io/treasury/bounties/32)
- [#33 – Marketing Bounty](https://polkadot.subsquare.io/treasury/bounties/33)
- [#36 – DeFi Infrastructure and Tooling Bounty](https://polkadot.subsquare.io/treasury/bounties/36)
- [#37 – Paseo Testnet Bounty](https://polkadot.subsquare.io/treasury/bounties/37)
- [#38 – Games Bounty](https://polkadot.subsquare.io/treasury/bounties/38)
- [#43 – Meetups Bounty](https://polkadot.subsquare.io/treasury/bounties/43)
- [#44 – Polkadot – Kusama Bridge Security Bounty](https://polkadot.subsquare.io/treasury/bounties/44)
- [#50 – Infrastructure Builders Program](https://polkadot.subsquare.io/treasury/bounties/50)
- [#52 – UX Bounty](https://polkadot.subsquare.io/treasury/bounties/52)
- [#59 – Open Source Developer Grants Bounty](https://polkadot.subsquare.io/treasury/bounties/59)
- [#62 – Legal Bounty](https://polkadot.subsquare.io/treasury/bounties/62)
- [#63 – Fast Grants Bounty](https://polkadot.subsquare.io/treasury/bounties/63)
- [#64 – Rust Bounties](https://polkadot.subsquare.io/treasury/bounties/64)

## Data Format

Each bounty folder contains:
- **README.md** - Human-readable documentation
- **metadata.yml** - Structured data including:
  - Funding information (remaining, total, grant ranges)
  - Curator details (count, multisig, compensation)
  - Links (website, GitHub, proposals, governance)
  - Social channels (Twitter, Telegram, Discord, Matrix)
  - Application details (process, timeline, status)
  - Tags and notes
- **scraped/** (optional) - Archived documentation from bounty websites
  - Preserved in original format (HTML, PDF, JSON, etc.)
  - Organized by domain: `scraped/[domain]/[path]`
  - Metadata stored in companion `.meta.yml` files

See [METADATA_SCHEMA.md](METADATA_SCHEMA.md) for the complete schema definition.

## Website Features

The interactive website (`index.html`) provides:
- 🔍 **Search** - Filter bounties by name, tags, or keywords
- 🏷️ **Category filters** - Development, Security, Infrastructure, Community, Grants, DeFi, UX, etc.
- 📊 **Live statistics** - Total bounties, DOT allocated, categories
- 📄 **Scraped content viewer** - Browse archived documentation with modal file tree
- 📱 **Mobile-responsive** - Works on all devices
- 🎨 **Polkadot branding** - Official color scheme and design

## Scraping & Archiving Documentation

The repository includes an automated workflow for archiving bounty documentation from official websites:

### Quick Start

```bash
cd scraping
pip install -r requirements.txt
```

### Workflow

**1. Generate Suggestions**
```bash
python suggest.py  # Extract URLs from metadata (default)
```
Extracts URLs from all bounty metadata files and generates suggestions for scraping.

**2. Review Suggestions**
```bash
python review.py
```
Interactively review suggestions with three-tier classification:
- **Scrape URLs** (docs, forms, governance) → Added to scrape queue
- **Associated URLs** (GitHub repos) → Added to metadata
- **Associated Socials** (Twitter, Discord, Telegram) → Added to metadata
- Auto-accepts URLs matching rules in `scrape-config.yml`
- Options: Accept, Modify, Ignore, Skip, Quit

**3. Scrape URLs**
```bash
python scraper.py
```
Scrapes all URLs in the queue and saves content. Extracts and categorizes all links found on each page. Successful scrapes are automatically removed from the queue.

**4. Discover New URLs**
```bash
python suggest.py --source=links  # Extract URLs from scraped pages
```
Analyzes extracted links from scraped pages and generates new suggestions. Filters out already scraped, queued, ignored, and suggested URLs. Found URLs are added to suggestions.

**5. Repeat or Push**
- Repeat from step 2 to scrape discovered URLs, or
- Push changes when done:
```bash
git add bounties/ scraping/
git commit -m "Add scraped documentation for bounties #X, #Y"
git push
```

### Common Procedures

**Fresh Start (Reset Everything)**
```bash
python cleanup.py reset-all  # Clears index, results, links, suggestions
python suggest.py            # Re-generate from metadata
```

**View Index Stats**
```bash
python cleanup.py stats      # Show scraped URLs by bounty
```

**Augmentary Run (Go Deeper)**
```bash
python cleanup.py remove-url "https://example.com/"  # Remove from index
# Edit scrape-queue.yml to add URL with recursive mode
python scraper.py            # Re-scrape with new settings
```

### Features

- 📥 **Single & recursive scraping** - Fetch individual pages or entire documentation sites
- 🔄 **Auto-suggestions** - Extracts URLs from bounty metadata automatically
- ✅ **Auto-accept rules** - Configure trusted domains to skip manual review
- 📄 **Original format preservation** - Saves HTML, PDF, JSON, etc. as-is with metadata
- 🔗 **Three-tier classification** - Scrape URLs / Associated URLs (GitHub) / Associated Socials (Twitter, Discord)
- 🔗 **Link extraction & categorization** - Automatically extracts and categorizes links
- 🔍 **Link discovery** - Generates new scraping suggestions from extracted links
- 🗂️ **Organized storage** - Saves to `bounties/[id]-[slug]/scraped/[domain]/`
- 🌐 **Website integration** - Scraped content and associated links appear on bounty cards automatically
- 🧹 **Reset & cleanup tools** - Fresh starts and augmentary runs

See [scraping/SCRAPING.md](scraping/SCRAPING.md) for detailed documentation.

## Deployment

The website is automatically deployed to GitHub Pages via GitHub Actions when changes are pushed to the `main` branch.

### Build Pipeline

On each deployment:
1. **Build scraped index** - `website/build_scraped_index.py` generates `scraped-index.json`
2. **Deploy to GitHub Pages** - All content including scraped files is published
3. **Website displays scraped content** - Bounty cards show archived documentation with interactive viewer

The website at [opengov-watch.github.io/bounty-archive](https://opengov-watch.github.io/bounty-archive/) updates automatically within 1-2 minutes of pushing to `main`.

## For AI Agents

If you're an AI agent working with this repository, see [CLAUDE.md](CLAUDE.md) for detailed instructions on updating bounties, maintaining metadata, and following the contribution workflow.

## Contributing

To update bounty information:
1. Edit the relevant `README.md` and/or `metadata.yml` file in the bounty folder
2. Ensure metadata follows the schema defined in [METADATA_SCHEMA.md](METADATA_SCHEMA.md)
3. Submit a pull request to the repository
4. Changes will be automatically deployed to the website once merged to `main`

## Maintenance

- Bounty data should be updated regularly to reflect current status
- Check for new bounties on [Polkadot Subsquare](https://polkadot.subsquare.io/treasury/bounties)
- Update funding amounts when significant changes occur
- Archive closed bounties by updating their status in metadata.yml

## License

Data sourced from official Polkadot Treasury on-chain data and bounty documentation.
