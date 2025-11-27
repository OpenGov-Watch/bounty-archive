# Polkadot Bounty Archive

Archive of Polkadot bounty documentation with structured metadata and an interactive website.

🌐 **[View the Interactive Website](https://opengov-watch.github.io/bounty-archive/)** (once deployed)

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

See [METADATA_SCHEMA.md](METADATA_SCHEMA.md) for the complete schema definition.

## Website Features

The interactive website (`index.html`) provides:
- 🔍 **Search** - Filter bounties by name, tags, or keywords
- 🏷️ **Category filters** - Development, Security, Infrastructure, Community, Grants, DeFi, UX, etc.
- 📊 **Live statistics** - Total bounties, DOT allocated, categories
- 📱 **Mobile-responsive** - Works on all devices
- 🎨 **Polkadot branding** - Official color scheme and design

## Deployment

The website is automatically deployed to GitHub Pages via GitHub Actions when changes are pushed to the `main` branch.

## Contributing

To update bounty information:
1. Edit the relevant `README.md` and/or `metadata.yml` file
2. Submit a pull request
3. Changes will be automatically deployed once merged

## License

Data sourced from official Polkadot Treasury on-chain data and bounty documentation.
