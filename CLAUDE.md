# Guide for AI Agents - Polkadot Bounty Archive

This document provides instructions for AI agents (like Claude) working with the Polkadot Bounty Archive repository.

## Repository Overview

This repository maintains a comprehensive archive of all active Polkadot Treasury bounties with:
- **20 bounty folders** with structured documentation
- **YAML metadata** for programmatic access
- **Interactive website** deployed via GitHub Pages

## Repository Structure

```
bounty-archive/
├── index.html                      # Interactive website
├── README.md                       # Public documentation
├── CLAUDE.md                       # This file (AI agent guide)
├── METADATA_SCHEMA.md              # YAML schema definition
├── .github/workflows/pages.yml     # GitHub Pages deployment
├── .claude/
│   └── agents/
│       └── scraper.md              # URL scraper subagent
├── scraping/
│   ├── SCRAPING.md                 # Scraping system documentation
│   ├── scrape-queue.yml            # URLs to scrape (input)
│   └── scrape-results.yml          # Scraping results (output)
└── bounties/
    ├── [id]-[name]/
    │   ├── README.md               # Human-readable docs
    │   ├── metadata.yml            # Structured data
    │   └── scraped/                # Scraped documentation (optional)
    │       └── [domain]/
    │           └── [path]/
    │               └── *.md
    └── ...
```

## Working with This Repository

### 1. Adding a New Bounty

When a new bounty is approved:

1. **Create folder**: `bounties/[id]-[bounty-name-slug]/`
   - Use bounty ID from on-chain data
   - Use kebab-case for name (e.g., `25-new-bounty-name`)

2. **Create README.md** with sections:
   - Title with bounty ID and name
   - Description and purpose
   - Primary documentation links
   - Curator team information
   - Application process
   - Communication channels
   - Transparency reports (if available)

3. **Create metadata.yml** following [METADATA_SCHEMA.md](METADATA_SCHEMA.md):
   - All required fields: id, name, status, category
   - Funding information (if available)
   - Curator details
   - All relevant links
   - Social channels
   - Application details
   - Tags (minimum 2-3 relevant tags)
   - Notes with key facts

4. **Update main README.md**: Add bounty to the "Active Bounties" list in numerical order

5. **Update index.html**: Add the bounty ID and slug to the `bountyIds` array and `getBountySlug()` function

### 2. Updating Existing Bounties

When updating bounty information:

1. **Update both files**: Always update both `README.md` and `metadata.yml` to keep them in sync

2. **Common updates**:
   - Funding amounts (remaining/total)
   - Curator changes
   - Application status (open/closed/paused)
   - New links or resources
   - Status changes (active → closed)
   - New notes for significant events

3. **Verify schema compliance**: Ensure metadata.yml follows the schema

### 3. Metadata Schema Compliance

**Required fields:**
- `id`: Number
- `name`: String
- `status`: "active" | "closed" | "paused"
- `category`: See METADATA_SCHEMA.md for valid values

**Optional but recommended:**
- `funding`: Include if any data is available
- `curators`: Include count at minimum
- `links`: At least subsquare link
- `tags`: 2-5 relevant tags
- `notes`: Key facts, warnings, or status updates

**Use null for unknown values**, don't omit fields entirely.

### 4. Categories

Valid category values:
- `development` - Development tools and frameworks
- `security` - Security audits and protection
- `infrastructure` - RPC nodes, validators, infrastructure
- `community` - Events, meetups, moderation
- `grants` - Grant programs
- `ux` - User experience improvements
- `marketing` - Marketing and promotion
- `defi` - DeFi infrastructure and tooling
- `gaming` - Gaming and entertainment
- `legal` - Legal support and research
- `other` - Miscellaneous

### 5. Research and Data Collection

When researching bounties:

**Primary sources:**
1. Polkadot Subsquare: https://polkadot.subsquare.io/treasury/bounties/[id]
2. Polkassembly: https://polkadot.polkassembly.io/bounty/[id]
3. Official bounty websites (check existing metadata)
4. GitHub organizations
5. Polkadot Forum discussions

**What to capture:**
- Official websites and documentation
- GitHub organizations and repos (especially application repos)
- Social media handles (Twitter, Telegram, Discord, Matrix)
- Email contacts
- Application forms and processes
- Curator names and affiliations
- Funding amounts (in DOT)
- Grant ranges or typical amounts
- Key achievements or statistics
- Important notes or warnings

**Web search approach:**
- Search: `"Polkadot [Bounty Name] Bounty #[id]"`
- Look for official announcements
- Check Polkadot Forum for proposals and updates
- Verify information from multiple sources

### 6. Git Workflow

**Branch naming:**
- Use: `claude/[task-description]-[session-id]`
- Session ID format: `018sxSiSdbQRje2S1RCHa18D` (provided in environment)

**Commit messages:**
- Be descriptive and specific
- Use conventional commit format when applicable
- Examples:
  - `"Add Bounty #25 - Example Bounty Name"`
  - `"Update funding amounts for Bounties #19, #22, #33"`
  - `"Fix metadata schema errors in 5 bounties"`

**Push requirements:**
- Always push to branches starting with `claude/`
- Always push to branches ending with session ID
- Push before completing your work (hooks will verify)

### 7. Scraping Bounty Documentation

The repository includes a scraping system for archiving bounty documentation:

**To scrape URLs:**

1. Add URLs to `scraping/scrape-queue.yml`
2. Invoke the scraper subagent:
   ```
   Please use the scraper subagent (.claude/agents/scraper.md) to scrape the URLs in scraping/scrape-queue.yml
   ```
3. Review results in `scraping/scrape-results.yml`
4. Check scraped content in `bounties/[id]-[slug]/scraped/`

**See [scraping/SCRAPING.md](scraping/SCRAPING.md) for detailed documentation.**

### 8. Common Tasks

#### Task: Update funding amounts for all bounties

1. Fetch latest data from Subsquare/Polkassembly
2. Update `metadata.yml` files with new amounts
3. Commit: `"Update funding amounts from on-chain data [date]"`

#### Task: Add links discovered during research

1. Update `metadata.yml` with new links
2. Update `README.md` if links are significant
3. Commit: `"Add additional links for Bounty #[id]"`

#### Task: Mark bounty as closed

1. Update `metadata.yml`: Change status to "closed"
2. Add note in `notes` array explaining closure
3. Update `README.md` with closure information
4. Commit: `"Mark Bounty #[id] as closed"`

### 9. Quality Checklist

Before committing:
- [ ] YAML syntax is valid (no tabs, proper indentation)
- [ ] All URLs are complete and include `https://`
- [ ] Twitter handles include `@` prefix
- [ ] Funding amounts are numbers (not strings)
- [ ] Status is one of: active, closed, paused
- [ ] Category is valid per schema
- [ ] Tags are lowercase and kebab-case
- [ ] README.md and metadata.yml are in sync
- [ ] No personally identifiable information beyond public curator names
- [ ] Links have been verified (not 404)

### 10. Testing

After making changes:
1. Verify YAML parses correctly (use js-yaml or similar)
2. Check website locally by opening `index.html`
3. Verify bounty card displays correctly
4. Test search and filtering functionality
5. Ensure no JavaScript console errors

### 11. Automation Opportunities

Consider automating:
- Funding amount updates from on-chain data
- New bounty detection from Subsquare
- Link validation (check for 404s)
- Schema validation
- Duplicate detection

### 12. Important Notes

**DO:**
- Keep metadata and README in sync
- Use official sources for data
- Document sources in notes when uncertain
- Mark uncertain information clearly
- Follow the schema strictly
- Commit frequently with clear messages

**DON'T:**
- Guess or fabricate information
- Skip metadata validation
- Break YAML syntax
- Remove fields (use null instead)
- Commit unverified information
- Push to wrong branch names

### 13. Getting Help

If you encounter issues:
1. Check [METADATA_SCHEMA.md](METADATA_SCHEMA.md) for schema reference
2. Look at existing bounties as examples
3. Validate YAML syntax online if needed
4. Ask the user for clarification on uncertain data

### 14. Future Enhancements

Areas for improvement:
- Automated on-chain data syncing
- Historical funding tracking
- Curator change tracking
- Child bounties documentation
- Quarterly report aggregation
- Analytics and insights

---

**Last Updated:** 2025-11-27
**Schema Version:** 1.0
