# Bounty Metadata Schema

This document defines the YAML metadata structure for bounty documentation.

## File Location

Each bounty folder should contain a `metadata.yml` file:
```
bounties/
  19-inkubator/
    README.md
    metadata.yml
```

## Schema Definition

```yaml
# Required fields
id: <number>                    # Bounty ID number
name: <string>                  # Short bounty name
status: <string>                # "active", "closed", "pending"
category: <string>              # Primary category (see categories below)

# Funding information
funding:
  remaining: <number|null>      # DOT remaining (null if unknown)
  total: <number|null>          # Total DOT allocated (null if unknown)
  currency: "DOT"               # Currency type
  grantRange: <string|null>     # Grant range (e.g., "$50k-$60k")

# Curator information
curators:
  count: <number|null>          # Number of curators
  multisigThreshold: <string|null>  # e.g., "4/6", "3/5"
  compensation: <string|null>   # Curator compensation details

# Links (all optional)
links:
  website: <url|null>
  notion: <url|null>
  proposal: <url|null>
  subsquare: <url|null>
  polkassembly: <url|null>
  spreadsheet: <url|null>
  forum: <url|null>

# GitHub repositories (all optional)
github:
  organization: <url|null>
  applications: <url|null>
  milestones: <url|null>
  main: <url|null>

# Social/communication channels (all optional)
social:
  twitter: <handle|null>
  telegram: <handle|null>
  discord: <url|null>
  matrix: <room|null>
  element: <room|null>

# Contact information (all optional)
contact:
  email: <email|null>
  applicationForm: <url|null>

# Application details (all optional)
application:
  process: <string|null>        # Brief description
  maxAmount: <string|null>      # Maximum grant amount
  timeline: <string|null>       # Expected timeline
  status: <string|null>         # "open", "closed", "paused"

# Tags for categorization
tags:
  - <string>
  - <string>

# Additional notes
notes:
  - <string>
  - <string>
```

## Categories

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

## Notes

- All fields marked with `|null` can be omitted or set to `null` if data is unavailable
- URLs should be complete (include https://)
- Twitter handles should include @ prefix
- Matrix/Element rooms should include full room ID
- Tags can be customized per bounty
- Notes array can contain status updates, warnings, or special information
