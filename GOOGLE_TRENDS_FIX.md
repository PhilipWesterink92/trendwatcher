# 🔧 Google Trends Fix - Technical Details

**Date**: 2026-02-23
**Status**: ✅ FIXED AND WORKING

---

## Problem Diagnosis

### Original Error
```
ResponseError: The request failed: Google returned a response with code 404
```

### Root Cause
Google **deprecated the `trending_searches` API endpoint**:
- Old URL: `https://trends.google.com/trends/hottrends/visualize/internal/data`
- Status: Returns 404 (No longer exists)
- Affected methods:
  - `pytrends.trending_searches(pn='country')`
  - `pytrends.realtime_trending_searches(pn='country')`

### Why It Happened
- Google silently deprecated this API (no announcement)
- The `pytrends` library (v4.9.2) still uses the old endpoint
- No fix available in current pytrends version
- Affects all users globally

---

## Solution: Keyword Monitoring Approach

Instead of asking Google "what's trending?", we now monitor **specific food keywords** and identify which ones are growing.

### How It Works

1. **Define Food Keywords** (40+ terms):
   ```python
   FOOD_KEYWORDS = [
       "vegan", "plant based", "oat milk",
       "kimchi", "kombucha", "miso",
       "ramen", "pho", "matcha",
       "air fryer", "instant pot",
       "keto", "gluten free",
       # ... 30+ more
   ]
   ```

2. **Query Interest Over Time**:
   - Use `pytrends.interest_over_time()` (still works!)
   - Get search volume for last month
   - Process in batches of 5 (API limit)

3. **Calculate Trend Score**:
   ```python
   recent_avg = last_7_days.mean()
   earlier_avg = previous_weeks.mean()

   if recent_avg > earlier_avg:
       # It's trending up!
       trend_score = recent_avg
       growth_pct = (recent - earlier) / earlier * 100
   ```

4. **Return Growing Keywords**:
   - Only include keywords with upward trend
   - Include growth percentage
   - Filter out low-interest keywords

---

## Test Results

### Before Fix (Old API)
```
google_trends NL: 404 error
google_trends DE: 404 error
google_trends FR: 404 error
Result: 0 trends collected
```

### After Fix (New Approach)
```
google_trends_v2 NL: found 8 trending keywords
google_trends_v2 DE: found 18 trending keywords
google_trends_v2 US: found 10 trending keywords
Result: 36+ trends collected ✅
```

### Sample Output
```python
[
    {
        "type": "google_trends_rising",
        "country": "US",
        "query": "dumpling",
        "score": 61,
        "metadata": {
            "recent_avg": 61.0,
            "earlier_avg": 42.0,
            "growth": 45.7  # 46% growth!
        }
    },
    {
        "query": "kimchi",
        "score": 66,
        "growth": 2.2
    },
    {
        "query": "ramen",
        "score": 74,
        "growth": 5.3
    }
]
```

---

## Advantages Over Old Approach

| Aspect | Old (trending_searches) | New (keyword monitoring) |
|--------|------------------------|--------------------------|
| **Reliability** | ❌ 404 errors | ✅ Works perfectly |
| **Control** | Random trends | Focused on food |
| **Signal Quality** | Noisy (all topics) | Clean (food only) |
| **Growth Data** | No | Yes (growth %) |
| **Customization** | None | Full keyword control |

---

## Limitations & Considerations

### Rate Limiting
- Google Trends has rate limits (429 errors)
- Occurs when querying too many keywords too fast
- **Mitigation**:
  - Delays between batches (1-2 seconds)
  - Limit to 40 keywords per country
  - Run less frequently

### Keyword Coverage
- Only monitors predefined keywords
- Might miss completely new trends (e.g., "TikTok viral food X")
- **Mitigation**:
  - Reddit integration catches new terms
  - Food blogs mention emerging ingredients
  - Periodically update keyword list

### API Stability
- `interest_over_time` is Google's main API
- Much more stable than trending_searches
- Used by commercial tools (unlikely to deprecate)

---

## Configuration

### Default Keywords (40+)
Located in `google_trends_v2.py`:
```python
FOOD_KEYWORDS = [
    # Proteins
    "chicken recipe", "salmon recipe", "tofu recipe",

    # Plant-based
    "vegan", "oat milk", "plant based",

    # Trending ingredients
    "kimchi", "matcha", "tahini",

    # Cooking methods
    "air fryer", "instant pot", "slow cooker",

    # Diets
    "keto", "gluten free", "paleo",

    # ... more
]
```

### Customization
Add your own keywords:
```python
FOOD_KEYWORDS.extend([
    "your custom keyword",
    "emerging ingredient",
    "trending dish"
])
```

### Batch Size
```python
batch_size = 5  # Max per Google Trends API call
```

### Timeframe
```python
timeframe = 'today 1-m'  # Last month
# Options: 'today 1-m', 'today 3-m', 'today 12-m'
```

---

## Files Changed

1. **`google_trends_v2.py`** (NEW)
   - Replacement for old google_trends.py
   - Uses keyword monitoring approach
   - Calculates growth percentages

2. **`cli.py`** (UPDATED)
   - Changed import: `from google_trends import` → `from google_trends_v2 import`
   - No other changes needed (drop-in replacement)

3. **`google_trends.py`** (DEPRECATED)
   - Kept for reference
   - No longer used
   - Can be deleted

---

## Future Improvements

### 1. Dynamic Keyword Discovery
- Use food blogs + Reddit to discover new terms
- Automatically add to keyword list
- Periodic refresh

### 2. Smart Rate Limiting
- Track API usage
- Implement exponential backoff
- Queue system for large keyword lists

### 3. Trend Scoring
- Weight by growth percentage
- Factor in absolute volume
- Seasonal adjustment

### 4. Multi-Region Analysis
- Compare trends across countries
- Identify lead markets
- Geographic spread patterns

---

## Comparison with Alternatives

### Option A: Paid APIs
- **SerpAPI Google Trends**: $50/mo (5k searches)
- **Bright Data**: $500+/mo
- **Verdict**: Our solution is free and good enough

### Option B: Web Scraping
- Scrape Google Trends website
- High risk of blocks
- Complex to maintain
- **Verdict**: Keyword monitoring is more reliable

### Option C: TikTok/Social
- TikTok API via Apify: $30/mo
- Good for viral trends
- Complements our approach
- **Verdict**: Use alongside Google Trends v2

---

## Monitoring & Maintenance

### Health Check
```bash
python -m trendwatcher ingest
# Look for: "google_trends_v2 XX: found N trending keywords"
# Good: N > 5 per country
# Warning: N < 3 (might need more keywords)
# Error: 429 (rate limited - add delays)
```

### Update Keywords Quarterly
- Review trending food topics
- Add new ingredients/methods
- Remove outdated keywords
- Test growth detection

### Monitor Rate Limits
- Watch for 429 errors
- Reduce batch size if frequent
- Increase delays between requests

---

## Summary

✅ **Google Trends is now working reliably**
✅ **Better signal quality (food-focused)**
✅ **Growth tracking included**
✅ **No external API costs**
⚠️ **Requires keyword curation**
⚠️ **Rate limits exist (manageable)**

**Overall**: Significant improvement over deprecated API. More reliable, more focused, better data.

---

## Next Steps

1. ✅ **DONE**: Fix implemented and tested
2. ✅ **DONE**: Pushed to GitHub
3. ⏸️ **TODO**: Add Reddit integration (complements Google Trends)
4. ⏸️ **TODO**: Test full pipeline with all sources
5. ⏸️ **TODO**: Monitor keyword list and update monthly
