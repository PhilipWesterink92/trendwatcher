"""
Recency scoring component (0-5 points).

Measures how recently the trend was first observed.
Newer = higher score.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict


def score_recency(trend: Dict) -> float:
    """
    Score based on how recent the trend is.

    Args:
        trend: Trend dict with first_seen data

    Returns:
        Score 0-5 (5 = very recent, 0 = old)
    """
    first_seen_dict = trend.get("first_seen", {})

    if not first_seen_dict:
        return 0.0

    # Get earliest first_seen across all countries
    timestamps = []
    for ts_str in first_seen_dict.values():
        try:
            # Parse ISO timestamp
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            timestamps.append(ts)
        except (ValueError, AttributeError):
            continue

    if not timestamps:
        return 0.0

    earliest = min(timestamps)
    now = datetime.now(timezone.utc)
    age_days = (now - earliest).days

    # Scoring ladder
    if age_days <= 7:
        return 5.0
    elif age_days <= 14:
        return 4.0
    elif age_days <= 30:
        return 3.0
    elif age_days <= 60:
        return 2.0
    elif age_days <= 90:
        return 1.0
    else:
        return 0.5
