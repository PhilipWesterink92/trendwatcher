"""
Breadth scoring component (0-5 points).

Measures geographic and source spread.
More markets + lead markets = higher score.
"""
from __future__ import annotations

from typing import Dict, Set


# Markets that tend to lead food trends
LEAD_MARKETS = {"US", "GB", "KR", "JP", "CN"}

# Picnic target markets
TARGET_MARKETS = {"NL", "DE", "FR"}


def score_breadth(trend: Dict) -> float:
    """
    Score based on market coverage and lead market presence.

    Args:
        trend: Trend dict with countries list

    Returns:
        Score 0-5 (5 = wide coverage with lead markets)
    """
    countries = set(trend.get("countries", []))

    if not countries:
        return 0.0

    score = 0.0

    # Component 1: Number of markets (0-2 points)
    market_count = len(countries)
    if market_count >= 5:
        score += 2.0
    elif market_count >= 3:
        score += 1.5
    elif market_count >= 2:
        score += 1.0
    else:
        score += 0.5

    # Component 2: Lead market presence (0-2 points)
    lead_count = len(countries & LEAD_MARKETS)
    if lead_count >= 3:
        score += 2.0
    elif lead_count >= 2:
        score += 1.5
    elif lead_count >= 1:
        score += 1.0

    # Component 3: Target market presence (0-1 point)
    # Already in our markets = act faster
    target_count = len(countries & TARGET_MARKETS)
    if target_count >= 2:
        score += 1.0
    elif target_count >= 1:
        score += 0.5

    return min(5.0, score)
