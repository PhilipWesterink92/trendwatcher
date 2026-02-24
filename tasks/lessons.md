# Lessons Learned

## Format
Each entry uses: **Mistake → Cause → Prevention**

---

## Session 2026-02-24: Initial Setup

### Lesson 1: Windows Unicode Handling
**Mistake**: Used Unicode characters (✓, ✗, 🔥) in console output, causing `UnicodeEncodeError`
**Cause**: Windows console uses cp1252 encoding which doesn't support Unicode emoji
**Prevention**: Always use ASCII-safe characters in print statements on Windows. Replace: ✓→[OK], ✗→[ERROR], emoji→text

### Lesson 2: Google Trends API Deprecation
**Mistake**: Initial implementation used `trending_searches` API which returned 404 errors
**Cause**: Google deprecated the trending_searches endpoint without notice
**Prevention**: When external APIs fail with 404, check for API deprecation before debugging code. Implement fallback strategies for third-party dependencies.

### Lesson 3: Source Type Filtering
**Mistake**: `extract_trends.py` only processed "google_trends_rising" type, ignoring food blog posts
**Cause**: Hard-coded type check instead of accepting multiple source types
**Prevention**: When adding new data sources, verify the extract stage accepts their document type. Use sets for multi-value type checking.

### Lesson 4: Secrets in Documentation
**Mistake**: Included actual Slack token in SLACK_INTEGRATION_COMPLETE.md, blocked by GitHub push protection
**Cause**: Used real credentials as examples in documentation
**Prevention**: Always use placeholder values in documentation (e.g., `xoxb-your-token-here`). Add note that real credentials are in .env (gitignored).

### Lesson 5: Rate Limiting Requires Aggressive Delays
**Mistake**: Google Trends v2 still hit 429 errors with 1-2 second delays
**Cause**: Underestimated Google's rate limiting sensitivity across multiple countries
**Prevention**: For rate-limited APIs, start with conservative delays (3-6 seconds). Test with single country before scaling up. Consider daily scheduling instead of frequent polling.

---

(Entries added over time using Mistake → Cause → Prevention format.)
