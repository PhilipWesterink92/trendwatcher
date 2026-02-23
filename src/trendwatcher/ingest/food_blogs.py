"""
Food blog RSS feed ingestion module for trendwatcher.

Fetches recent articles from food blog RSS feeds using feedparser.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import List, Dict, Any

import feedparser


def fetch_food_blogs(
    feeds: List[Dict[str, str]],
    *,
    country: str = "US",
    max_age_days: int = 30,
    default_score: int = 100,
) -> List[Dict[str, Any]]:
    """
    Fetch recent articles from food blog RSS feeds.

    Args:
        feeds: List of feed dictionaries with 'name' and 'url' keys
        country: Country code for context (default: US)
        max_age_days: Only include articles published within this many days
        default_score: Score to assign to blog posts (upvotes equivalent)

    Returns:
        List of document dictionaries compatible with trendwatcher pipeline

    Example feeds format:
        [
            {"name": "serious_eats", "url": "https://www.seriouseats.com/feeds/latest"},
            {"name": "bon_appetit", "url": "https://www.bonappetit.com/feed/rss"}
        ]
    """
    results = []
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60

    for feed_config in feeds:
        feed_name = feed_config.get("name", "unknown")
        feed_url = feed_config.get("url")

        if not feed_url:
            print(f"[Warning] No URL provided for feed: {feed_name}")
            continue

        try:
            # Parse RSS feed
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                # Feed has parsing errors
                print(f"[Warning] Failed to parse feed {feed_name}: {feed.bozo_exception}")
                continue

            # Process each entry
            for entry in feed.entries:
                # Extract publication date
                published_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_time = time.mktime(entry.published_parsed)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_time = time.mktime(entry.updated_parsed)

                # Skip old articles
                if published_time and (current_time - published_time) > max_age_seconds:
                    continue

                # Extract title
                title = entry.get('title', '').strip()
                if not title:
                    continue

                # Clean title (remove HTML tags if any)
                title = _clean_html_tags(title)

                doc = {
                    "type": "food_blog_post",
                    "country": country,
                    "query": title,
                    "score": default_score,
                    "seed": feed_name,
                    "fetched_at": datetime.utcnow().isoformat() + "Z",
                    "metadata": {
                        "url": entry.get('link', ''),
                        "published": entry.get('published', ''),
                        "author": entry.get('author', ''),
                        "summary": entry.get('summary', '')[:200],  # First 200 chars
                    }
                }
                results.append(doc)

        except Exception as e:
            print(f"[Warning] Failed to fetch feed {feed_name}: {e}")
            continue

    return results


def _clean_html_tags(text: str) -> str:
    """
    Remove HTML tags from text.

    Args:
        text: Text potentially containing HTML tags

    Returns:
        Cleaned text without HTML tags
    """
    import re
    # Simple regex to remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    clean = ' '.join(clean.split())
    return clean


# Common food blog RSS feeds
POPULAR_FOOD_BLOGS = {
    "serious_eats": "https://www.seriouseats.com/feeds/latest",
    "bon_appetit": "https://www.bonappetit.com/feed/rss",
    "budget_bytes": "https://www.budgetbytes.com/feed/",
    "minimalist_baker": "https://minimalistbaker.com/feed/",
    "smitten_kitchen": "https://smittenkitchen.com/feed/",
    "cookie_and_kate": "https://cookieandkate.com/feed/",
    "pinch_of_yum": "https://pinchofyum.com/feed",
    "half_baked_harvest": "https://www.halfbakedharvest.com/feed/",
}
