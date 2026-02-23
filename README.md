# 🔥 Trendwatcher

**AI-powered food trend intelligence system for Picnic Technologies**

Trendwatcher is an automated platform that discovers emerging food trends across global markets, analyzes their product fit using AI, and provides actionable insights for product teams.

## 🚀 Features

### 1. Multi-Source Data Collection
- **Google Trends** - Trending searches across 10 markets (US, GB, KR, JP, NL, DE, FR, AU, CA, SG)
- **Reddit** - Posts from food-related subreddits (r/food, r/FoodPorn, r/52weeksofcooking, etc.)
- **Food Blogs** - RSS feeds from major food publications (Serious Eats, Bon Appétit, Budget Bytes, etc.)
- **Competitor Pages** - New products from AH, REWE, Carrefour

### 2. Intelligent Trend Extraction
- Fuzzy clustering to group related trends
- Food-intent filtering to remove non-food signals
- Lead/lag market detection (US/GB/KR/JP → NL/DE/FR)
- Deduplication and scoring

### 3. AI-Powered Analysis
- **Claude 4.5** evaluates each trend for:
  - Product fit (high/medium/low)
  - Market readiness (ready/emerging/niche)
  - Adoption timeline (now/3-6mo/6-12mo/12mo+)
  - Customer sentiment
  - Recommended actions and risks

### 4. Product Matching
- Semantic matching to Picnic product catalog
- Confidence scoring with reasoning
- Country-specific availability filtering
- *Ready for integration with Picnic API*

### 5. Automated Scheduling
- Background daemon for hands-free operation
- Configurable cron schedules
- Daily data ingestion
- Weekly trend analysis
- Automated reports

### 6. Multi-Channel Reporting
- **Slack** - Rich formatted reports with emoji indicators
- **Email** - HTML reports with trend tables
- Scheduled delivery (weekly/daily)

---

## 📋 Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd trendwatcher

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Configuration

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Add your API keys to `.env`:**
   ```bash
   # Required for analysis
   ANTHROPIC_API_KEY=sk-ant-...

   # Optional: Reddit data
   REDDIT_CLIENT_ID=your_id
   REDDIT_CLIENT_SECRET=your_secret

   # Optional: Slack reports
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_CHANNEL=#trendwatcher
   ```

3. **See [docs/SETUP.md](docs/SETUP.md) for detailed API setup instructions**

---

## 🎯 Usage

### Basic Workflow

```bash
# 1. Fetch data from all sources
python -m trendwatcher ingest

# 2. Extract and cluster trends
python -m trendwatcher extract

# 3. View top trends
python -m trendwatcher watchlist --top 25

# 4. Analyze with AI (requires ANTHROPIC_API_KEY)
python -m trendwatcher analyze --top 25

# 5. Match to product catalog
python -m trendwatcher match --catalog data/catalog/products.example.json

# 6. Send report
python -m trendwatcher report --channel slack
```

### Automated Operation

```bash
# Start background scheduler (runs continuously)
python -m trendwatcher daemon
```

Configure schedules in `src/trendwatcher/config/scheduler.yaml`:

```yaml
schedule:
  ingest:
    enabled: true
    cron: "0 2 * * *"  # Daily at 2 AM UTC

  extract:
    enabled: true
    cron: "0 3 * * *"  # Daily at 3 AM UTC

  analyze:
    enabled: true
    cron: "0 4 * * 0"  # Weekly on Sunday

  report:
    enabled: true
    cron: "0 9 * * 1"  # Weekly on Monday 9 AM
    channel: "#trendwatcher"
```

---

## 📊 Output Files

```
data/
├── raw/
│   └── docs.jsonl              # Raw documents from all sources
├── processed/
│   ├── trends.json             # Clustered trends with scores
│   ├── trends_analyzed.json    # AI analysis results
│   └── trends_matched.json     # Product matches
├── catalog/
│   └── products.example.json   # Example product catalog
└── logs/
    └── scheduler.log           # Daemon logs
```

---

## 🏗️ Architecture

```
sources.yaml → ingest → docs.jsonl
                  ↓
               extract → trends.json
                  ↓
               analyze → trends_analyzed.json
                  ↓
                match → trends_matched.json
                  ↓
            report (Slack/Email)
```

### Data Sources (Feature 2)

| Source | Type | Free | Rate Limit | Data |
|--------|------|------|------------|------|
| Google Trends | API | ✅ | N/A | Search trends by country |
| Reddit | OAuth | ✅ | 60 req/min | Food subreddit posts |
| Food Blogs | RSS | ✅ | N/A | Recipe articles |
| Competitors | Scraping | ✅ | Polite | New product pages |

### Analysis Pipeline (Features 1 & 3)

- **Input**: Top N trends from `trends.json`
- **Model**: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)
- **Cost**: ~$3 per 1000 trends analyzed
- **Output**: Product fit, market readiness, recommendations, risks

### Scheduling (Feature 4)

- **Engine**: APScheduler with cron triggers
- **Jobs**: Ingest, Extract, Analyze, Report
- **Deployment**: systemd service or Docker container

### Reporting (Feature 5)

- **Slack**: Block Kit formatted messages with emoji indicators
- **Email**: HTML tables with trend analysis
- **Frequency**: Configurable (daily/weekly)

---

## 🔧 Configuration

### Data Sources (`src/trendwatcher/config/sources.yaml`)

Add or modify data sources:

```yaml
sources:
  - id: reddit_food_us
    type: reddit
    subreddits: ["food", "FoodPorn"]
    country: US
    limit: 50
    enabled: true

  - id: food_blogs_us
    type: food_blog
    feeds:
      - name: serious_eats
        url: https://www.seriouseats.com/feeds/latest
    country: US
    enabled: true
```

### Product Catalog

Create your product catalog at `data/catalog/products.json`:

```json
[
  {
    "product_id": "12345",
    "name": "Organic Matcha Powder",
    "category": "Tea & Coffee",
    "tags": ["matcha", "green tea", "organic"],
    "available_in": ["NL", "DE", "FR"]
  }
]
```

**TODO**: Replace with Picnic API integration once API access is established.

---

## 💰 Operating Costs

| Service | Cost | Notes |
|---------|------|-------|
| Claude API | $5-15/mo | ~25 trends/day analyzed |
| Reddit API | Free | OAuth authentication |
| Food Blogs | Free | Public RSS feeds |
| Slack | Free | Existing workspace |
| Email | Free | SMTP (e.g., Gmail) |

**Total**: ~$5-15/month

---

## 🧪 Development

### Project Structure

```
trendwatcher/
├── src/trendwatcher/
│   ├── ingest/           # Data collection (Google, Reddit, Blogs, Competitors)
│   ├── extract/          # Clustering and trend extraction
│   ├── analyze/          # AI-powered analysis
│   ├── match/            # Product catalog matching
│   ├── scheduler/        # Background job scheduling
│   ├── report/           # Slack and email reporting
│   ├── config/           # Configuration files
│   └── cli.py            # Command-line interface
├── data/                 # Data files (gitignored)
├── docs/                 # Documentation
└── tests/                # Unit tests (TODO)
```

### Running Tests

```bash
# TODO: Add pytest tests
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff check src/

# Type checking
mypy src/
```

---

## 📚 Documentation

- **[SETUP.md](docs/SETUP.md)** - Detailed API key setup guide
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and data flow (TODO)

---

## 🎯 Roadmap

### Implemented ✅
- [x] Multi-source data ingestion (Google, Reddit, Blogs, Competitors)
- [x] Intelligent trend extraction with clustering
- [x] AI-powered analysis (Claude 4.5)
- [x] Product catalog matching
- [x] Automated scheduling
- [x] Slack and email reporting

### Planned 🚧
- [ ] TikTok data source (Apify integration)
- [ ] Picnic API integration for product catalog
- [ ] Real-time trend monitoring dashboard
- [ ] Historical trend tracking and predictions
- [ ] A/B testing for product launches
- [ ] Competitor benchmarking analysis

---

## 🤝 Contributing

This is an internal Picnic Technologies project. For questions or contributions:

1. Create a feature branch
2. Make your changes
3. Submit a pull request
4. Tag relevant stakeholders for review

---

## 📄 License

Internal use only - Picnic Technologies

---

## 🆘 Support

### Common Issues

**"ANTHROPIC_API_KEY not found"**
- Copy `.env.example` to `.env` and add your API key
- See [docs/SETUP.md](docs/SETUP.md) for instructions

**"Reddit credentials not found"**
- Set `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in `.env`
- Or disable Reddit sources in `sources.yaml` (set `enabled: false`)

**"Trends file not found"**
- Run `python -m trendwatcher ingest` first
- Then run `python -m trendwatcher extract`

**Scheduler not running jobs**
- Check `src/trendwatcher/config/scheduler.yaml`
- Verify cron expressions are valid
- Check logs at `data/logs/scheduler.log`

### Getting Help

- Check [docs/SETUP.md](docs/SETUP.md) for configuration
- Review logs in `data/logs/scheduler.log`
- Contact the data team for API access issues

---

**Built with ❤️ for Picnic Technologies**
