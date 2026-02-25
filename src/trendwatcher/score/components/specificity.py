"""
Specificity scoring component (0-5 points).

Measures how specific the trend entity is.
Specific products/ingredients score higher than generic categories.
"""
from __future__ import annotations

import re
from typing import Dict


def score_specificity(trend: Dict) -> float:
    """
    Score based on entity specificity.

    Args:
        trend: Trend dict with entity_type and entity_confidence

    Returns:
        Score 0-5 (5 = very specific, 0 = generic)
    """
    entity_type = trend.get("entity_type")
    entity_confidence = trend.get("entity_confidence", 0.0)
    trend_name = trend.get("trend", "").lower()

    # If we have entity extraction metadata
    if entity_type:
        # Branded products = highest specificity
        if entity_type == "branded_product":
            return min(5.0, 4.0 + entity_confidence)

        # Equipment = very specific
        if entity_type == "equipment":
            return 5.0

        # Ingredient varieties = high specificity
        if entity_type == "ingredient_variety":
            return min(5.0, 3.5 + entity_confidence)

        # Product formats = medium specificity
        if entity_type == "product_format":
            return min(5.0, 3.0 + entity_confidence)

    # Fallback: heuristic scoring
    words = trend_name.split()
    word_count = len(words)

    # Multi-word is more specific than single word
    if word_count >= 3:
        base_score = 3.0
    elif word_count == 2:
        base_score = 2.5
    else:
        base_score = 1.0

    # Boost for proper nouns (capitalized words in middle of phrase)
    if re.search(r"\b[A-Z][a-z]+\b", trend.get("trend", "")):
        base_score += 1.0

    # Generic food terms get penalty
    generic_terms = {"recipe", "recipes", "food", "cooking", "dinner", "lunch"}
    if any(term in trend_name for term in generic_terms):
        base_score -= 1.0

    return max(0.0, min(5.0, base_score))
