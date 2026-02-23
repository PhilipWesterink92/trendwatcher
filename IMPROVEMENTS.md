# Trendwatcher Quality Improvements

**Date**: 2026-02-23
**Commit**: cbaa761

---

## ✅ Completed Improvements

### 1. Expanded Food Keyword Dictionary (+80 terms)

**File**: `src/trendwatcher/extract/extract_trends.py`

**Added Categories**:
- **Plant-based alternatives**: oat milk, almond milk, jackfruit, tempeh, seitan
- **Fermented foods**: kombucha, sauerkraut, kimchi (already had), sourdough
- **Asian ingredients**: gochujang, yuzu, dashi, shiso, mirin, panko
- **Middle Eastern**: za'atar, sumac, harissa, dukkah, labneh
- **Health/Superfood**: collagen, chia, acai, spirulina, moringa, adaptogens
- **Diet trends**: keto, paleo, low carb, gluten-free, dairy-free
- **Cooking methods**: air fryer, instant pot, sous vide, slow cooker
- **Meal types**: meal prep, snack, appetizer, dessert

**Expanded Non-Food Veto List**:
- Cosmetics: mascara, lipstick, serum, moisturizer
- Electronics: laptop, tablet, headphones
- Health non-food: discharge, medication, pharmacy
- Fashion: sneakers, jacket, jeans

**Impact**:
- ✅ Better detection of trending ingredients (matcha, kimchi detected in test)
- ✅ Fewer false negatives (won't miss plant-based trends)
- ✅ Fewer false positives (better non-food filtering)

---

### 2. Fixed Google Trends Retry Logic

**File**: `src/trendwatcher/ingest/google_trends.py`

**Improvements**:
- ✅ Exponential backoff (2-5 sec * attempt number)
- ✅ User agent rotation (4 realistic browsers)
- ✅ Realistic browser headers (Accept, Accept-Language, DNT)
- ✅ Polite delays between requests (0.5-1.5 sec)
- ✅ Connection timeouts (10 sec connect, 25 sec read)

**Status**:
- ⚠️ **Google Trends still returning 404**
- ✅ Retry logic working correctly (delays visible in logs)
- 🔴 **Root cause**: Google API may have changed or aggressive blocking

**Recommendation**:
- Continue using food blogs as primary reliable source
- Consider alternative Google Trends APIs or paid services
- Reddit integration (once configured) can replace Google Trends data

---

### 3. Enhanced Competitor Scraping

**File**: `src/trendwatcher/ingest/fetch.py`

**Improvements**:
- ✅ 5 realistic user agents (Chrome, Firefox, Safari on Windows/Mac/Linux)
- ✅ Full browser header set:
  - Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site
  - Accept, Accept-Language, Accept-Encoding
  - DNT, Cache-Control, Upgrade-Insecure-Requests
- ✅ Dynamic Referer header (matches domain)
- ✅ Random delays (1-3 seconds) to avoid rate limiting
- ✅ Proper redirect handling

**Status**:
- ⚠️ **Still getting 403 from some sites** (expected - anti-bot protection)
- ✅ Headers now look like real browser
- 🟡 **May need**: Proxy rotation, Selenium/Playwright for JS-heavy sites

**Recommendation**:
- Focus on food blogs (working reliably)
- Consider paid scraping services for competitors (ScrapingBee, Bright Data)
- Or implement Selenium with browser automation (slower but more reliable)

---

## 📊 Current Data Source Status

| Source | Status | Success Rate | Data Quality |
|--------|--------|--------------|--------------|
| **Food Blogs (RSS)** | ✅ **WORKING** | 100% (51 articles) | Excellent |
| Google Trends | ❌ **404 ERRORS** | 0% | N/A |
| Competitor Sites | ⚠️ **403 BLOCKED** | ~30% | Mixed |
| Reddit | ⏸️ **NOT CONFIGURED** | N/A | Expected: Good |

**Primary Reliable Source**: Food Blogs
**Secondary Source to Enable**: Reddit (needs OAuth credentials)

---

## 🎯 Impact on Trend Quality

### Test Run Comparison

**Before Improvements**:
- Trends detected: 175
- Top trend: "miso soup me" (116,737)
- Food keywords: ~60 terms
- Non-food filtering: Basic

**Expected After Improvements**:
- ✅ More accurate trend detection (+80 food keywords)
- ✅ Better Asian ingredient coverage
- ✅ Better plant-based trend detection
- ✅ Fewer false positives (expanded veto list)
- ✅ More resilient scraping (though still blocked by some sites)

---

## 🚀 Next Steps for Further Improvement

### High Priority (Recommended)

1. **Enable Reddit Integration** ⭐
   - Configure OAuth credentials in `.env`
   - Expected: 50-100 high-quality food posts per run
   - Would replace Google Trends as primary signal source

   ```bash
   # Add to .env:
   REDDIT_CLIENT_ID=your_id
   REDDIT_CLIENT_SECRET=your_secret

   # Enable in sources.yaml:
   - id: reddit_food_us
     enabled: true  # Change from false
   ```

2. **Alternative Google Trends Solutions**
   - Try SerpAPI (https://serpapi.com/) - $50/mo for 5k searches
   - Try Google Trends Unofficial API alternatives
   - Use TikTok trends via Apify as replacement

### Medium Priority

3. **Add Selenium for Competitor Sites**
   - Use Playwright or Selenium for JS-heavy sites
   - Slower but bypasses 403 blocks
   - Cost: More CPU/memory usage

4. **Blog Deduplication** (Task #22)
   - Filter out duplicate posts across sources
   - Use fuzzy matching on titles
   - Reduce noise in clustering

5. **Optimize Clustering Threshold** (Task #23)
   - Test 85%, 88%, 90%, 92% thresholds
   - Find optimal balance
   - May vary by trend type

### Low Priority

6. **Add TikTok Data Source**
   - Use Apify API ($30/mo)
   - Track #foodtok hashtags
   - High volume, need good filtering

7. **Proxy Rotation for Scraping**
   - Use residential proxies (Bright Data, Smartproxy)
   - Cost: $75-150/mo
   - Bypasses IP-based blocks

---

## 💡 Alternative Approach: Focus on What Works

Given the blocking issues with Google Trends and competitors, consider this strategy:

### Primary Sources (Reliable):
1. ✅ **Food Blog RSS** (working perfectly)
2. ⏸️ **Reddit** (enable with OAuth - highly reliable)
3. ⏸️ **TikTok via Apify** (optional - good signal quality)

### Benefits:
- No scraping blocks (RSS and APIs are designed for access)
- Better signal quality (curated content)
- Lower maintenance (no cat-and-mouse with anti-bot systems)
- More cost-effective ($0-30/mo vs $100+ for proxies)

### Trade-offs:
- Miss some competitor "new products" pages
- Miss some Google Trends signals
- But: Reddit and TikTok provide similar early-trend detection

---

## 📈 Recommended Action Plan

### Immediate (This Week):
1. ✅ **DONE**: Expand food keywords
2. ✅ **DONE**: Improve scraping headers
3. ⏸️ **TODO**: Enable Reddit (5 min setup)
4. ⏸️ **TODO**: Test with new sources

### Short Term (Next 2 Weeks):
5. Monitor trend quality with new keywords
6. Fine-tune clustering threshold if needed
7. Add blog deduplication if too noisy

### Long Term (Optional):
8. Evaluate TikTok vs Google Trends trade-off
9. Consider paid scraping service for competitors
10. Build dashboard for trend visualization

---

## 🔍 Testing Recommendations

### Quick Test (5 min):
```bash
# Enable Reddit in sources.yaml first
python -m trendwatcher ingest
python -m trendwatcher extract
python -m trendwatcher watchlist --top 20
```

### Full Pipeline Test (with API key):
```bash
python -m trendwatcher ingest
python -m trendwatcher extract
python -m trendwatcher analyze --top 10
python -m trendwatcher watchlist --top 20
```

### Monitor Trend Quality:
- Check if new food keywords appear (e.g., "oat milk", "air fryer", "tempeh")
- Verify false positives are reduced (no cosmetics, electronics)
- Compare trend count: should be similar or higher with better quality

---

## 📝 Summary

**Completed**: 3 major quality improvements
**Committed**: 2 commits pushed to GitHub
**Status**: Core improvements done, data source reliability is main challenge

**Key Insight**: Food blogs + Reddit (when enabled) provide the most reliable trend signals. Google Trends and competitors are nice-to-have but problematic due to anti-bot measures.

**Next Action**: Enable Reddit integration for immediate quality boost! 🚀
