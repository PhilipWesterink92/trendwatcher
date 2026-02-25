"""
Velocity scoring component (0-5 points).

Measures week-over-week growth rate.
Requires historical data from weekly snapshots.
"""
from __future__ import annotations

from typing import Dict, List


def score_velocity(trend: Dict, history: List[Dict]) -> float:
    """
    Score based on week-over-week growth.

    Args:
        trend: Current trend dict
        history: List of historical snapshots for this trend (ordered by week)

    Returns:
        Score 0-5 (5 = rapid growth, 0 = declining)
    """
    if not history or len(history) < 2:
        # No history yet - give neutral score
        return 2.5

    # Compare latest two weeks
    current_week = history[-1]
    previous_week = history[-2]

    current_count = current_week.get("raw_count", 0)
    previous_count = previous_week.get("raw_count", 0)

    if previous_count == 0:
        # New trend - give high score if it exists now
        return 4.0 if current_count > 0 else 0.0

    # Calculate growth rate
    growth_rate = (current_count - previous_count) / previous_count

    # Scoring ladder
    if growth_rate > 0.5:  # 50%+ growth
        return 5.0
    elif growth_rate > 0.3:  # 30-50% growth
        return 4.0
    elif growth_rate > 0.1:  # 10-30% growth
        return 3.0
    elif growth_rate > 0:  # Positive growth
        return 2.0
    elif growth_rate > -0.1:  # Slight decline
        return 1.0
    else:  # Declining
        return 0.5
