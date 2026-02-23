"""
Google Trends v2 - Using interest_over_time instead of deprecated trending_searches API.

The trending_searches API endpoint has been deprecated by Google (404 errors).
This version monitors specific food keywords and identifies which are trending up.
"""
from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Dict, List

from pytrends.request import TrendReq
from rich import print


# Food keywords to monitor for trends
# These cover major food categories that typically trend
FOOD_KEYWORDS = [
    # Proteins
    "chicken recipe", "salmon recipe", "tofu recipe", "beef recipe",

    # Plant-based
    "vegan", "plant based", "oat milk", "almond milk",

    # Fermented
    "kimchi", "kombucha", "sourdough", "miso",

    # Asian
    "ramen", "pho", "bao", "dumpling", "matcha",

    # Middle Eastern
    "tahini", "hummus", "falafel", "halloumi",

    # Cooking methods
    "air fryer", "instant pot", "slow cooker", "meal prep",

    # Diets
    "keto", "gluten free", "dairy free", "paleo",

    # Trending ingredients
    "avocado", "quinoa", "chia seeds", "acai", "tempeh",
]


def fetch_trending_keywords(
    country_code: str,
    keywords: List[str] = None,
    batch_size: int = 5,
    timeframe: str = 'today 1-m',
) -> List[Dict]:
    """
    Fetch interest data for food keywords and identify trending ones.

    Args:
        country_code: Country code (e.g., "US", "NL", "DE")
        keywords: List of keywords to check (uses default if None)
        batch_size: Number of keywords per API call (max 5)
        timeframe: Time period to check ('today 1-m', 'today 3-m', etc.)

    Returns:
        List of dictionaries with trending keywords and scores
    """
    if keywords is None:
        keywords = FOOD_KEYWORDS

    cc = country_code.upper()
    results = []

    # Process keywords in batches (Google Trends API limit: 5 keywords per request)
    for i in range(0, len(keywords), batch_size):
        batch = keywords[i:i + batch_size]

        try:
            # Small delay to be polite
            if i > 0:
                time.sleep(random.uniform(1.0, 2.0))

            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload(batch, timeframe=timeframe, geo=cc)

            # Get interest over time
            df = pytrends.interest_over_time()

            if df.empty:
                continue

            # Calculate trend score (recent interest vs average)
            for keyword in batch:
                if keyword not in df.columns:
                    continue

                values = df[keyword].values
                if len(values) < 2:
                    continue

                # Calculate trend: compare recent week to earlier average
                recent_avg = values[-7:].mean() if len(values) >= 7 else values[-3:].mean()
                earlier_avg = values[:-7].mean() if len(values) >= 14 else values[:len(values)//2].mean()

                # Only include if trending up
                if recent_avg > earlier_avg and recent_avg > 20:  # Threshold: some actual interest
                    trend_score = int(recent_avg)

                    results.append({
                        "type": "google_trends_rising",
                        "country": cc,
                        "query": keyword,
                        "score": trend_score,
                        "seed": "keyword_monitoring",
                        "fetched_at": datetime.now(timezone.utc).isoformat() + "Z",
                        "metadata": {
                            "recent_avg": float(recent_avg),
                            "earlier_avg": float(earlier_avg),
                            "growth": float((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0,
                        }
                    })

        except Exception as e:
            print(f"[yellow]google_trends_v2[/yellow] batch {i//batch_size + 1} failed: {e}")
            continue

    return results


def fetch_rising_searches(country_code: str) -> List[Dict]:
    """
    Compatibility wrapper for existing code.
    Uses keyword monitoring instead of deprecated trending_searches API.
    """
    results = fetch_trending_keywords(
        country_code=country_code,
        keywords=FOOD_KEYWORDS,
        batch_size=5,
        timeframe='today 1-m'
    )

    print(f"[green]google_trends_v2[/green] {country_code}: found {len(results)} trending keywords")
    return results
