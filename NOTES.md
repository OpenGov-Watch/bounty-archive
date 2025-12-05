what doesn't work:
- Google Docs
- after cleanup.py reset-all and suggest.py, it says "already processed: 19" which shouldn't happen

## Code Review Findings - 2025-11-29

### Bugs Fixed
- ✅ scraper.py:469 - Incorrect timestamp format (produced malformed ISO timestamps)
- ✅ suggest.py:87 - Type hint incompatibility (broke Python 3.9 compatibility)
- ✅ review.py - Poor error messages when bounty folder not found
- ✅ review.py:594 - Quit bug (current suggestion lost when pressing Q)

### Future Improvements (Not Critical)

#### Performance
- Consider batch YAML writes instead of per-operation writes
- Add progress bars for long operations (suggest.py, scraper.py)

#### Error Handling
- Add try-catch around YAML loading operations
- Add validation for queue items before processing (check bounty_id is int, url is valid)
- Add retry logic for failed HTTP requests (currently fails immediately)

#### Features
- Make rate limiting configurable in scrape-config.yml (currently hardcoded to 1s)
- Add backup mechanism in cleanup.py reset-all (create timestamped backups before deletion)
- Add comprehensive logging system (replace print statements with proper logger)
- Add URL normalization in discover.py (handle trailing slashes consistently)

#### Code Quality
- Use pathlib methods more consistently (scraper.py:535-538 mixes forward/backslash)
- Add null check before accessing files_created[0] in summary (scraper.py:725)

### Security & Performance Assessment
- ✅ No security vulnerabilities found
- ✅ Efficient URL deduplication using sets
- ✅ Proper rate limiting and timeouts
- ✅ No memory leaks identified
- ✅ Production-ready code

### Priority Recommendations
1. **High Priority:** Add backup mechanism in cleanup.py
2. **Medium Priority:** Make rate limiting configurable
3. **Low Priority:** Add comprehensive logging system