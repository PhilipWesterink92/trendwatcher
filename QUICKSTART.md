# 🚀 Trendwatcher Quick Start

## Installation Complete ✅

Dependencies installed successfully. Ready to use!

---

## Basic Usage (No API Keys Required)

### 1. Fetch Data
```bash
python -m trendwatcher ingest
```
**Result**: Fetches food blog articles (51 articles from current test)

### 2. Extract Trends
```bash
python -m trendwatcher extract
```
**Result**: Clusters and scores trends (175 trends from test data)

### 3. View Top Trends
```bash
python -m trendwatcher watchlist --top 20
```
**Result**: Beautiful table of trending food topics

---

## With API Keys (Advanced Features)

### Setup .env File
```bash
# Copy example
cp .env.example .env

# Edit and add your keys
nano .env  # or use any text editor
```

### Required API Keys

**For AI Analysis**:
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/
- Cost: ~$0.15-0.50 per analysis of 25 trends

**For Reddit Data** (optional):
- `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET`
- Get from https://www.reddit.com/prefs/apps
- Free with rate limit of 60 req/min

**For Slack Reports** (optional):
- `SLACK_BOT_TOKEN` - Create app at https://api.slack.com/apps
- Free

---

## Full Pipeline Example

```bash
# 1. Fetch data from all sources
python -m trendwatcher ingest

# 2. Extract and cluster trends
python -m trendwatcher extract

# 3. View top trends
python -m trendwatcher watchlist --top 25

# 4. Analyze with AI (requires ANTHROPIC_API_KEY)
python -m trendwatcher analyze --top 25

# 5. Match to products (requires ANTHROPIC_API_KEY)
python -m trendwatcher match --catalog data/catalog/products.example.json

# 6. Send report (requires SLACK_BOT_TOKEN)
python -m trendwatcher report --channel slack
```

---

## Automated Operation

### Configure Schedule
Edit `src/trendwatcher/config/scheduler.yaml`:

```yaml
schedule:
  ingest:
    enabled: true
    cron: "0 2 * * *"  # Daily 2 AM

  extract:
    enabled: true
    cron: "0 3 * * *"  # Daily 3 AM

  analyze:
    enabled: true
    cron: "0 4 * * 0"  # Weekly Sunday 4 AM

  report:
    enabled: false  # Enable after configuring Slack
    cron: "0 9 * * 1"  # Weekly Monday 9 AM
```

### Start Daemon
```bash
python -m trendwatcher daemon
```

Runs continuously in background. Press Ctrl+C to stop.

---

## Test Results Summary ✅

From our test run:

| Component | Status | Details |
|-----------|--------|---------|
| Installation | ✅ SUCCESS | All dependencies installed |
| Food Blog Ingestion | ✅ SUCCESS | 51 articles fetched |
| Trend Extraction | ✅ SUCCESS | 175 trends identified |
| Watchlist Display | ✅ SUCCESS | Table rendering working |
| AI Analysis | ⏸️ Needs API key | Code ready |
| Product Matching | ⏸️ Needs API key | Code ready |
| Reporting | ⏸️ Needs credentials | Code ready |

**Top Trends Discovered**:
1. Miso soup recipes
2. Gluten-free pizza
3. Kimchi dishes
4. Overnight oats
5. Matcha products
6. Ramen recipes

---

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
→ Add to `.env` file (see docs/SETUP.md)

### "Trends file not found"
→ Run `ingest` then `extract` first

### Google Trends returning 404
→ Expected (rate limiting). Use food blogs instead.

### Competitor sites returning 403
→ Expected (anti-bot). Use food blogs instead.

---

## Next Steps

1. ✅ **Core pipeline tested and working**
2. 📝 Configure `.env` with API keys
3. 🧪 Test AI analysis: `python -m trendwatcher analyze --top 5`
4. 🎯 Test product matching with example catalog
5. 📊 Set up Slack for reports
6. ⚙️ Configure scheduler for automation
7. 🚀 Deploy to production

---

## Documentation

- **Full docs**: `README.md`
- **API setup**: `docs/SETUP.md`
- **Test results**: `TEST_RESULTS.md`
- **Help**: `python -m trendwatcher --help`

---

**Built with ❤️ for Picnic Technologies**
