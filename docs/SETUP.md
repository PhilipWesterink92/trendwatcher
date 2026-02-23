# 🔧 Trendwatcher Setup Guide

Complete guide for setting up API keys and configuring trendwatcher.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Anthropic Claude API](#1-anthropic-claude-api-required)
3. [Reddit API](#2-reddit-api-optional)
4. [Slack Integration](#3-slack-integration-optional)
5. [Email Configuration](#4-email-configuration-optional)
6. [Testing Your Setup](#testing-your-setup)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.11 or higher
- Virtual environment activated
- Dependencies installed (`pip install -e .`)

---

## 1. Anthropic Claude API (Required)

**Required for**: AI-powered trend analysis and product matching

### Step 1: Get API Key

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in with your account
3. Navigate to **API Keys** section
4. Click **Create Key**
5. Copy your API key (starts with `sk-ant-`)

### Step 2: Add to .env

```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### Cost Estimation

- Model: Claude Sonnet 4.5
- Cost: ~$3 per million input tokens, ~$15 per million output tokens
- Typical usage: Analyzing 25 trends = ~50K tokens = **$0.15-0.50 per analysis**
- Monthly estimate (weekly analysis): **$5-15/month**

### Testing

```bash
python -m trendwatcher analyze --top 5
```

---

## 2. Reddit API (Optional)

**Required for**: Fetching posts from food-related subreddits

### Step 1: Create Reddit App

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Log in with your Reddit account
3. Scroll to bottom and click **"create another app..."**
4. Fill out the form:
   - **name**: `trendwatcher`
   - **App type**: Select **"script"**
   - **description**: Food trend monitoring
   - **about url**: (leave blank)
   - **redirect uri**: `http://localhost:8080`
5. Click **"create app"**

### Step 2: Get Credentials

After creating the app, you'll see:

- **Client ID**: String under "personal use script" (about 14 characters)
- **Client Secret**: Longer string labeled "secret"

### Step 3: Add to .env

```bash
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_secret_here
REDDIT_USER_AGENT=trendwatcher/0.1
```

### Step 4: Enable Reddit Sources

Edit `src/trendwatcher/config/sources.yaml`:

```yaml
- id: reddit_food_us
  type: reddit
  subreddits: ["food", "FoodPorn", "52weeksofcooking"]
  country: US
  limit: 50
  enabled: true  # Change from false to true
```

### Rate Limits

- **60 requests per minute** with OAuth
- Trendwatcher makes ~1 request per subreddit
- Well within limits for typical usage

### Testing

```bash
python -m trendwatcher ingest
# Look for "reddit posts=..." in output
```

---

## 3. Slack Integration (Optional)

**Required for**: Automated trend reports to Slack channels

### Step 1: Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Select **"From scratch"**
4. Enter app name: `Trendwatcher`
5. Select your workspace
6. Click **"Create App"**

### Step 2: Add Bot Permissions

1. In your app settings, go to **"OAuth & Permissions"**
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Click **"Add an OAuth Scope"** and add:
   - `chat:write` - Post messages
   - `channels:read` - List channels
4. Scroll up and click **"Install to Workspace"**
5. Click **"Allow"**

### Step 3: Get Bot Token

After installation:

1. You'll be redirected to **"OAuth & Permissions"**
2. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)

### Step 4: Add Bot to Channel

1. Open Slack and go to your target channel (e.g., `#trendwatcher`)
2. Click channel name → **"Integrations"** → **"Add apps"**
3. Search for "Trendwatcher" and add it

### Step 5: Add to .env

```bash
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_CHANNEL=#trendwatcher
```

### Testing

```bash
# Make sure you have analyzed trends first
python -m trendwatcher analyze --top 10
python -m trendwatcher report --channel slack
```

---

## 4. Email Configuration (Optional)

**Required for**: Email trend reports

### Gmail Setup (Recommended)

#### Step 1: Enable 2-Factor Authentication

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled

#### Step 2: Create App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Select **"Mail"** and your device
3. Click **"Generate"**
4. Copy the 16-character password (remove spaces)

#### Step 3: Add to .env

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=trendwatcher@picnic.nl
TO_EMAIL=analyst@picnic.nl
```

### Other Email Providers

**Outlook/Office 365:**
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
```

**Yahoo Mail:**
```bash
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
```

**Custom SMTP:**
- Contact your IT department for SMTP settings
- Usually requires server address, port, and credentials

### Testing

```bash
python -m trendwatcher report --channel email --recipients your-email@example.com
```

---

## Testing Your Setup

### Complete Test Workflow

```bash
# 1. Test data ingestion (should work without API keys)
python -m trendwatcher ingest

# 2. Test trend extraction
python -m trendwatcher extract

# 3. View trends (no API key needed)
python -m trendwatcher watchlist --top 10

# 4. Test AI analysis (requires ANTHROPIC_API_KEY)
python -m trendwatcher analyze --top 5

# 5. Test product matching (requires ANTHROPIC_API_KEY)
python -m trendwatcher match --top 5

# 6. Test Slack report (requires SLACK_BOT_TOKEN)
python -m trendwatcher report --channel slack

# 7. Test email report (requires SMTP credentials)
python -m trendwatcher report --channel email --recipients your@email.com
```

### Verify Environment Variables

```bash
# Check which variables are set
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('ANTHROPIC_API_KEY:', 'SET' if os.getenv('ANTHROPIC_API_KEY') else 'NOT SET')"
```

---

## Troubleshooting

### "ANTHROPIC_API_KEY not found"

**Cause**: API key not set in `.env` file

**Solution**:
1. Verify `.env` file exists in project root
2. Check for typos in variable name
3. Restart your terminal/IDE after adding the key
4. Use absolute value (no quotes unless key contains special chars)

```bash
# ✅ Correct
ANTHROPIC_API_KEY=sk-ant-api03-abc123...

# ❌ Wrong
ANTHROPIC_API_KEY="sk-ant-api03-abc123..."  # Remove quotes
```

---

### "Reddit credentials not found"

**Cause**: Reddit API keys not configured

**Solution 1** (Enable Reddit):
- Follow [Reddit API setup](#2-reddit-api-optional)
- Add credentials to `.env`

**Solution 2** (Disable Reddit):
- Edit `src/trendwatcher/config/sources.yaml`
- Set `enabled: false` for Reddit sources

---

### "Slack API returned ok=False"

**Common causes**:

1. **Invalid token**: Check `SLACK_BOT_TOKEN` in `.env`
2. **Bot not in channel**: Add Trendwatcher app to your channel
3. **Missing permissions**: Verify `chat:write` scope is enabled
4. **Invalid channel name**: Use format `#channel-name` (with #)

**Fix**:
```bash
# Check channel format
SLACK_CHANNEL=#trendwatcher  # ✅ Correct
SLACK_CHANNEL=trendwatcher   # ❌ Wrong (missing #)
```

---

### "SMTP authentication failed"

**Common causes**:

1. **Wrong password**: Use App Password, not regular Gmail password
2. **2FA not enabled**: Gmail requires 2-Step Verification for app passwords
3. **Wrong port**: Should be 587 for most providers

**Gmail-specific fix**:
1. Ensure 2-Step Verification is ON
2. Generate new App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Use the 16-character password (remove spaces)

---

### "Trends file not found"

**Cause**: No trends have been extracted yet

**Solution**:
```bash
# Must run in order:
python -m trendwatcher ingest   # Fetch data
python -m trendwatcher extract  # Process data
python -m trendwatcher analyze  # Analyze trends
```

---

### Module Import Errors

**Cause**: Dependencies not installed

**Solution**:
```bash
# Reinstall in development mode
pip install -e .

# Or install from requirements (if available)
pip install -r requirements.txt
```

---

### Rate Limit Errors

**Reddit**: Wait 1 minute, then retry
**Claude**: Check usage at [console.anthropic.com](https://console.anthropic.com/)

---

## Security Best Practices

### ✅ Do:
- Store credentials in `.env` (gitignored)
- Use App Passwords for Gmail (not account password)
- Rotate API keys periodically
- Restrict Slack bot to specific channels
- Use read-only Reddit credentials

### ❌ Don't:
- Commit `.env` to git
- Share API keys in Slack/email
- Use personal accounts for production
- Grant unnecessary API permissions

---

## Next Steps

Once setup is complete:

1. **Test the full pipeline** with sample data
2. **Configure scheduler** in `src/trendwatcher/config/scheduler.yaml`
3. **Run daemon** for automated operation
4. **Monitor logs** at `data/logs/scheduler.log`

---

## Getting Help

- **Configuration issues**: Check this guide
- **API errors**: Review error messages and logs
- **Feature requests**: Contact the data team
- **Bugs**: Create an issue in the repository

---

**Setup complete? Return to [README.md](../README.md) for usage examples.**
