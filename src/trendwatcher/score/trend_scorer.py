"""
Trend scoring orchestrator.

Combines 5 scoring components into final 0-25 score.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from .components.recency import score_recency
from .components.breadth import score_breadth
from .components.velocity import score_velocity
from .components.specificity import score_specificity
from .components.diversity import score_diversity


class TrendScorer:
    """Orchestrates 5-dimensional trend scoring."""

    def score(
        self,
        trend: Dict,
        history: List[Dict] = None,
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate 5-dimensional score for a trend.

        Args:
            trend: Trend dictionary
            history: Optional list of historical weekly snapshots

        Returns:
            Tuple of (total_score, breakdown_dict)
            - total_score: 0-25 (sum of 5 components)
            - breakdown: dict with individual component scores
        """
        if history is None:
            history = []

        # Calculate individual components (each 0-5)
        breakdown = {
            "recency": score_recency(trend),
            "breadth": score_breadth(trend),
            "velocity": score_velocity(trend, history),
            "specificity": score_specificity(trend),
            "diversity": score_diversity(trend),
        }

        # Total score (0-25)
        total = sum(breakdown.values())

        return round(total, 2), {k: round(v, 2) for k, v in breakdown.items()}

    def score_batch(
        self,
        trends: List[Dict],
        history_map: Dict[str, List[Dict]] = None,
    ) -> List[Dict]:
        """
        Score multiple trends at once.

        Args:
            trends: List of trend dicts
            history_map: Optional dict mapping trend names to history lists

        Returns:
            List of trends with added 'score' and 'score_breakdown' fields
        """
        if history_map is None:
            history_map = {}

        scored_trends = []

        for trend in trends:
            trend_name = trend.get("trend", "")
            history = history_map.get(trend_name, [])

            total_score, breakdown = self.score(trend, history)

            # Add scoring to trend
            trend["score"] = total_score
            trend["score_breakdown"] = breakdown

            scored_trends.append(trend)

        # Re-sort by new score
        scored_trends.sort(key=lambda t: t["score"], reverse=True)

        return scored_trends
