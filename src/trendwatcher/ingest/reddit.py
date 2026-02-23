"""
Reddit ingestion module for trendwatcher.

Fetches posts from food-related subreddits using PRAW (Python Reddit API Wrapper).
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import List, Dict, Any, Optional

import praw
from praw.models import Subreddit


def fetch_reddit_posts(
    subreddits: List[str],
    *,
    country: str = "US",
    limit: int = 50,
    time_filter: str = "week",
) -> List[Dict[str, Any]]:
    """
    Fetch trending posts from specified subreddits.

    Args:
        subreddits: List of subreddit names (without "r/" prefix)
        country: Country code for context (default: US)
        limit: Maximum number of posts per subreddit
        time_filter: Time filter for top posts ("day", "week", "month", "year", "all")

    Returns:
        List of document dictionaries compatible with trendwatcher pipeline

    Raises:
        ValueError: If Reddit credentials are not configured
    """
    # Check for required environment variables
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "trendwatcher/0.1")

    if not client_id or not client_secret:
        raise ValueError(
            "Reddit credentials not found. Please set REDDIT_CLIENT_ID and "
            "REDDIT_CLIENT_SECRET environment variables. "
            "See docs/SETUP.md for instructions."
        )

    # Initialize Reddit API client
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )

    results = []

    for subreddit_name in subreddits:
        try:
            subreddit: Subreddit = reddit.subreddit(subreddit_name)

            # Fetch top posts from the specified time period
            for submission in subreddit.top(time_filter=time_filter, limit=limit):
                # Skip posts without titles or that are NSFW
                if not submission.title or submission.over_18:
                    continue

                doc = {
                    "type": "reddit_trending",
                    "country": country,
                    "query": submission.title.strip(),
                    "score": submission.score,
                    "seed": f"r/{subreddit_name}",
                    "fetched_at": datetime.utcnow().isoformat() + "Z",
                    "metadata": {
                        "post_id": submission.id,
                        "url": f"https://reddit.com{submission.permalink}",
                        "num_comments": submission.num_comments,
                        "created_utc": submission.created_utc,
                    }
                }
                results.append(doc)

        except Exception as e:
            # Log error but continue with other subreddits
            print(f"[Warning] Failed to fetch from r/{subreddit_name}: {e}")
            continue

    return results


def is_valid_food_post(title: str) -> bool:
    """
    Optional: Pre-filter posts that are likely food-related.

    Note: The existing is_foody() function in extract_trends.py will handle
    final filtering, but this can reduce noise early.

    Args:
        title: Post title

    Returns:
        True if post appears to be food-related
    """
    food_keywords = [
        "recipe", "food", "cook", "bake", "dish", "meal", "eat",
        "restaurant", "cuisine", "flavor", "ingredient", "sauce",
        "dessert", "dinner", "lunch", "breakfast", "snack"
    ]

    title_lower = title.lower()
    return any(keyword in title_lower for keyword in food_keywords)
