# Slack Bot Setup Guide

## Step 1: Create Slack App (5 minutes)

1. **Go to Slack Apps**: https://api.slack.com/apps
2. Click **"Create New App"**
3. Select **"From scratch"**
4. Enter details:
   - **App Name**: `Trendwatcher Bot`
   - **Workspace**: Select your Picnic workspace
5. Click **"Create App"**

---

## Step 2: Configure Bot Permissions

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll down to **"Scopes"** section
3. Under **"Bot Token Scopes"**, click **"Add an OAuth Scope"**
4. Add these two scopes:
   - `chat:write` - Post messages to channels
   - `chat:write.public` - Post to public channels without joining them first

---

## Step 3: Install Bot to Workspace

1. Scroll back up to the **"OAuth Tokens for Your Workspace"** section
2. Click **"Install to Workspace"**
3. Review the permissions and click **"Allow"**
4. You'll see a **"Bot User OAuth Token"** (starts with `xoxb-`)
5. **Copy this token** - you'll need it in the next step

---

## Step 4: Create/Choose a Channel

Option A - Create new channel:
1. In Slack, click the **+** next to "Channels"
2. Name it: `trendwatcher`
3. Make it public
4. Click **"Create"**

Option B - Use existing channel:
1. Choose any existing public channel where you want reports
2. Note the channel name (e.g., `#food-trends`)

---

## Step 5: Invite Bot to Channel

1. Go to your chosen channel in Slack
2. Type: `/invite @Trendwatcher Bot`
3. Press Enter
4. The bot should join the channel

---

## Step 6: Provide Credentials to Claude

Once you've completed the above steps, provide:

1. **Bot User OAuth Token**: `xoxb-...` (from Step 3)
2. **Channel name**: e.g., `#trendwatcher` or `#food-trends`

Claude will then:
- Add credentials to your `.env` file
- Test the connection
- Send a test report to verify it works

---

## Troubleshooting

**Bot can't post messages?**
- Verify you added both `chat:write` and `chat:write.public` scopes
- Make sure you invited the bot to the channel with `/invite`

**Token not working?**
- Make sure you copied the **Bot User OAuth Token**, not the App-Level Token
- Token should start with `xoxb-`

**Channel not found?**
- Channel name should include the # symbol: `#trendwatcher`
- Bot can only post to public channels (unless you add `channels:join` scope)

---

## What Reports Will Look Like

Once configured, the bot will send weekly reports with:
- Top 10 trending food topics
- Trend scores and growth percentages
- Lead market indicators (US/GB trends appearing first)
- Target market flags (NL/DE/FR)
- Links to source articles

Example format:
```
📊 Trendwatcher Weekly Report - 2026-02-24

🔥 Top Trending Foods:

1. Dairy-Free Desserts (Score: 850) 🇺🇸 → 🇳🇱
   Plant-based dessert trend growing in US, expected in NL market

2. Air Fryer Recipes (Score: 720) 🇬🇧 → 🇩🇪
   Convenient cooking method trending in UK blogs

[... 8 more trends ...]

📈 Data Sources: 51 food blogs, 24 trend clusters
```

---

## Ready to Configure?

Once you have your Bot Token and Channel name, let Claude know and we'll complete the setup!
