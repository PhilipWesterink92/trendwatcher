"""
Google Trends v2 - Multi-market intelligence with config-driven keywords.

Monitors specific food keywords across 9 markets to detect emerging trends.
Keywords are now defined per-market in sources.yaml for better signal quality.
"""
from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pytrends.request import TrendReq
from rich import print


def fetch_trending_keywords(
    country_code: str,
    keywords: List[str],
    batch_size: int = 5,
    timeframe: str = 'today 1-m',
) -> List[Dict]:
    """
    Fetch interest data for food keywords and identify trending ones.

    Args:
        country_code: Country code (e.g., "US", "NL", "DE")
        keywords: List of keywords to check (required, from config)
        batch_size: Number of keywords per API call (max 5)
        timeframe: Time period to check ('today 1-m', 'today 3-m', etc.)

    Returns:
        List of dictionaries with trending keywords and scores
    """
    if not keywords:
        print(f"[yellow]google_trends_v2[/yellow] {country_code}: no keywords provided, skipping")
        return []

    cc = country_code.upper()
    results = []

    # Process keywords in batches (Google Trends API limit: 5 keywords per request)
    for i in range(0, len(keywords), batch_size):
        batch = keywords[i:i + batch_size]

        try:
            # Longer delays to avoid rate limiting (429 errors)
            if i > 0:
                delay = random.uniform(3.0, 6.0)  # Increased from 1-2 to 3-6 seconds
                time.sleep(delay)

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


def fetch_rising_searches(
    country_code: str,
    keywords: Optional[List[str]] = None
) -> List[Dict]:
    """
    Fetch trending searches for a specific market.

    Args:
        country_code: Country code (e.g., "US", "NL", "DE")
        keywords: List of keywords to monitor (required)

    Returns:
        List of trending keyword data
    """
    if not keywords:
        print(f"[yellow]google_trends_v2[/yellow] {country_code}: no keywords provided, skipping")
        return []

    results = fetch_trending_keywords(
        country_code=country_code,
        keywords=keywords,
        batch_size=5,
        timeframe='today 1-m'
    )

    print(f"[green]google_trends_v2[/green] {country_code}: found {len(results)} trending keywords from {len(keywords)} monitored")
    return results
