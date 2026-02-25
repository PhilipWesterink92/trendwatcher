"""
Diversity scoring component (0-5 points).

Measures cross-source confirmation.
Trends appearing in multiple source types (search + menu + blogs) score higher.
"""
from __future__ import annotations

from typing import Dict, Set


def score_diversity(trend: Dict) -> float:
    """
    Score based on source diversity.

    Args:
        trend: Trend dict with seeds list

    Returns:
        Score 0-5 (5 = confirmed across many source types)
    """
    seeds = trend.get("seeds", [])

    if not seeds:
        return 0.0

    # Categorize sources by type
    source_types: Set[str] = set()

    for seed in seeds:
        seed_lower = seed.lower()

        if "google_trends" in seed_lower or "trend" in seed_lower:
            source_types.add("search")
        elif "menu" in seed_lower or "resy" in seed_lower or "thefork" in seed_lower:
            source_types.add("menu")
        elif "blog" in seed_lower or "food_blog" in seed_lower:
            source_types.add("blog")
        elif "reddit" in seed_lower or "social" in seed_lower:
            source_types.add("social")
        elif "competitor" in seed_lower or "retail" in seed_lower:
            source_types.add("retail")
        else:
            source_types.add("other")

    diversity_count = len(source_types)

    # Scoring ladder
    if diversity_count >= 4:
        return 5.0
    elif diversity_count == 3:
        return 4.0
    elif diversity_count == 2:
        return 3.0
    elif diversity_count == 1:
        # Bonus if we have multiple sources within same type
        if len(seeds) >= 3:
            return 2.0
        else:
            return 1.0
    else:
        return 0.0
