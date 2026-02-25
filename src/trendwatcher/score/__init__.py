"""
5-Dimensional trend scoring system.

Replaces uniform score=100 with meaningful 0-25 scale based on:
  1. Recency (0-5): How recent is the trend?
  2. Breadth (0-5): How many markets/sources?
  3. Velocity (0-5): Week-over-week growth rate
  4. Specificity (0-5): How specific is the entity?
  5. Diversity (0-5): Cross-source confirmation?

Total: 0-25 points
"""
from .trend_scorer import TrendScorer

__all__ = ["TrendScorer"]
