# Project: Trendwatcher

## Purpose
Trendwatcher ingests external signals, detects emerging food trends, scores them, and produces structured outputs for downstream commercial use.

Core expectations:
- deterministic where possible
- observable via logs
- testable end-to-end
- safe with external requests (timeouts, retries, caching)

---

## Key Structure

- `src/trendwatcher/`: core pipeline logic
  - `ingest/`: data collection modules (Google Trends, food blogs, Reddit, competitors)
  - `extract/`: trend clustering and scoring
  - `analyze/`: LLM-powered trend analysis
  - `match/`: product catalog matching
  - `report/`: Slack and email reporting
  - `scheduler/`: automated job scheduling
  - `config/`: YAML configuration files
- `data/`: pipeline data
  - `raw/docs.jsonl`: ingested documents
  - `processed/trends.json`: extracted trends
  - `cache/`: HTTP response cache
- `tests/`: automated tests
- `.env`: environment variables (credentials, never committed)

---

## Definition of Done (MANDATORY)

Never mark work complete unless ALL are true:

1. Relevant tests pass (or new tests added if needed)
2. Pipeline can run locally without errors
3. Logs clearly show stage progress
4. No silent failures
5. External calls have timeout + retry logic
6. Caching behavior preserved or tested when touched
7. Changes are minimal and focused

You must explicitly show evidence when claiming success.

---

## Workflow Rules

### Planning
- Enter plan mode for any non-trivial task (3+ steps or architectural choice)
- Write a short plan before major changes
- If something breaks, STOP and re-plan

### Implementation
- Prefer root-cause fixes over patches
- Keep diffs minimal
- Avoid unnecessary dependencies
- Do not change public interfaces without tests/docs

### Verification
- Always run tests when code changes
- When touching HTTP logic, verify cache behavior
- When touching pipeline stages, verify end-to-end run

---

## Self-Improvement Loop (CRITICAL)

After ANY user correction:

1. Update `tasks/lessons.md`
2. Capture:
   - Mistake
   - Root cause
   - Preventive rule

3. Future work must follow accumulated lessons.

At the start of each session:
- Review `tasks/lessons.md`
- Apply relevant safeguards

---

## Engineering Guardrails

### External Requests
Must include:
- timeout
- retry/backoff when appropriate
- cache awareness when applicable
- clear user agent

### Logging
Each major pipeline stage must log:
- start
- success/failure
- key counts where meaningful

### Tests
Prefer:
- small deterministic unit tests
- plus at least one realistic flow test for critical paths

---

## Decision Guidance

When uncertain:
- Ask ONE precise clarifying question, OR
- Present two options with tradeoffs

Do not proceed on vague assumptions for risky changes.

---

## Project-Specific Context

### Windows Compatibility
- **Critical**: Avoid Unicode characters in console output (use ASCII alternatives)
- Windows console uses cp1252 encoding - emoji and special chars cause `UnicodeEncodeError`
- Replace: ✓ → [OK], ✗ → [ERROR], 🔥 → (text), etc.

### API Rate Limiting
- **Google Trends**: Prone to 429 errors, use 3-6 second delays between batches
- **Reddit**: 60 req/min limit (OAuth), sufficient for our usage
- **Slack**: No significant limits for posting
- Always implement exponential backoff for retries

### Data Source Reliability
- **Food blogs**: Most reliable, ~51 posts/day, no rate limits
- **Google Trends**: Working but rate-limited (use sparingly)
- **Competitors**: Blocked by anti-bot protection (403 errors)
- **Reddit**: High-value but requires OAuth setup

### Configuration Files
- `.env`: Credentials (never commit, always in .gitignore)
- `sources.yaml`: Data source configuration (enable/disable sources)
- `scheduler.yaml`: Automated job schedules (cron format)

### Testing Strategy
- Run `python -m trendwatcher ingest` to test data collection
- Run `python -m trendwatcher extract` to test clustering
- Run `python -m trendwatcher watchlist` to verify output
- Full pipeline: ingest → extract → report (check Slack channel)

### Known Issues
1. **Google Trends API deprecated**: Now using interest_over_time with keyword monitoring
2. **Unicode on Windows**: All console output must be ASCII-safe
3. **Competitor scraping**: Limited by anti-bot measures (accept limitation)
4. **Food blog parsing**: One feed (Serious Eats) has malformed XML (graceful failure)
