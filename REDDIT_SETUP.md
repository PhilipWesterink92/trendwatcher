# Reddit API Setup Guide

## Why Reddit?

Reddit is a goldmine for early trend detection:
- 🔥 **Real-time signals**: Viral posts hours before they hit blogs
- 🌍 **Geographic diversity**: r/UKFood, r/EatCheapAndHealthy, etc.
- 💬 **Community validation**: Upvotes = genuine interest
- 🆓 **Free API**: 60 requests/minute, plenty for our needs

---

## Step 1: Create Reddit App (3 minutes)

1. **Go to Reddit Apps**: https://www.reddit.com/prefs/apps
2. **Scroll to bottom** and click **"create another app..."**
3. **Fill in details**:
   - **Name**: `Trendwatcher Bot`
   - **App type**: Select **"script"** (radio button)
   - **Description**: `Food trend monitoring for Picnic Technologies`
   - **About URL**: Leave blank or use: `https://github.com/PhilipWesterink92/trendwatcher`
   - **Redirect URI**: `http://localhost:8080` (required but not used)
4. **Click "create app"**

---

## Step 2: Get API Credentials

After creating the app, you'll see:

```
Trendwatcher Bot
personal use script
[Your Client ID - 14 characters]

secret              [Your Secret - 27 characters]
edit    delete
```

**Copy these two values:**
- **Client ID**: The string directly under "personal use script" (14 chars)
- **Client Secret**: The string next to "secret" (27 chars)

---

## Step 3: Provide Credentials to Claude

Once you have both values, provide:

1. **Reddit Client ID**: `<14-character ID>`
2. **Reddit Client Secret**: `<27-character secret>`

Claude will then:
- Add credentials to your `.env` file
- Enable Reddit sources in `sources.yaml`
- Test the connection
- Run a sample ingestion

---

## What Reddit Sources Will Be Enabled

### US Food Trends
**Subreddits**: r/food, r/FoodPorn, r/52weeksofcooking, r/EatCheapAndHealthy
- **Posts per run**: Top 50 from past week
- **Expected volume**: ~200 posts/week
- **Focus**: Recipes, cooking techniques, budget meals

### UK Food Trends
**Subreddits**: r/food, r/UKFood, r/recipes
- **Posts per run**: Top 50 from past week
- **Expected volume**: ~150 posts/week
- **Focus**: British cuisine, local ingredients

**Total**: ~350 Reddit posts/week + 350 blog posts/week = **700 trend signals/week**

---

## Rate Limits

Reddit OAuth allows:
- ✅ **60 requests per minute** (very generous)
- ✅ **No daily limits** for authenticated apps
- ✅ **Stable performance** (unlike Google Trends)

Our usage: ~7 requests per ingestion run = **well within limits**

---

## Security Notes

- ✅ Credentials stored in `.env` (gitignored, never committed)
- ✅ OAuth 2.0 authentication (secure)
- ✅ Read-only access (can't post or modify anything)
- ✅ No personal data collected (only public post titles/scores)

---

## Example Output

After enabling Reddit, you'll see in your Slack reports:

```
#1. Air Fryer Chicken Wings
📊 Score: 1,245 | 🌍 US
From: r/food (842 upvotes)

#2. Budget Meal Prep Ideas
📊 Score: 890 | 🌍 US
From: r/EatCheapAndHealthy (890 upvotes)
```

---

## Troubleshooting

**"invalid_grant" error?**
- Make sure you selected **"script"** app type (not "web app")
- Verify Client ID is exactly 14 characters
- Verify Client Secret is exactly 27 characters

**"401 Unauthorized"?**
- Check credentials are correct in `.env`
- Restart the Python process to reload environment

**No posts found?**
- Reddit API might be throttling - wait 1 minute and try again
- Check subreddit names are spelled correctly

---

## Ready to Configure?

Provide your **Client ID** and **Client Secret** and we'll complete the setup!

**Format**:
- Client ID: `<your-14-char-id>`
- Client Secret: `<your-27-char-secret>`
