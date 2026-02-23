"""
Semantic matching of trends to product catalog using Claude AI.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Any

from anthropic import Anthropic
from rich import print as rprint

from .catalog import load_catalog, filter_catalog_by_country


MATCHING_SYSTEM_PROMPT = """You are a product matching specialist for Picnic Technologies.

Your task is to match food trends to products in Picnic's catalog. For each trend:
1. Identify which products in the catalog are most relevant
2. Explain why each product matches
3. Assign a confidence score (0-100)

Focus on:
- Semantic similarity (e.g., "plant-based protein" matches "vegan burgers")
- Category relevance
- Customer intent (what would they search for?)
- Regional availability

Be conservative with matches - only suggest products that truly fit the trend.
"""


MATCHING_USER_PROMPT_TEMPLATE = """Match this food trend to relevant products:

**Trend**: {trend_name}
**Countries**: {countries}
**Analysis**: {analysis_summary}

**Available Products** (first 50 shown):
{catalog_json}

Return a JSON array of matches (max 5 per trend):

[
  {{
    "product_id": "12345",
    "product_name": "Organic Matcha Powder",
    "confidence": 95,
    "reasoning": "Direct match - matcha is the core trend, organic appeals to health-conscious customers"
  }},
  ...
]

If no good matches exist, return an empty array: []

Only include products with confidence >= 60.
"""


def match_trends_to_catalog(
    trends_file: Path,
    catalog_file: Path,
    output_file: Path,
    *,
    top_n: int = 25,
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 2048,
) -> int:
    """
    Match trends to product catalog using semantic analysis.

    Args:
        trends_file: Path to trends JSON (analyzed or raw)
        catalog_file: Path to product catalog JSON
        output_file: Path to write matched trends
        top_n: Number of top trends to match
        model: Claude model to use
        max_tokens: Maximum tokens per response

    Returns:
        Number of trends matched
    """
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. Please set it in your .env file."
        )

    # Load trends and catalog
    if not trends_file.exists():
        raise FileNotFoundError(f"Trends file not found: {trends_file}")

    trends = json.loads(trends_file.read_text(encoding="utf-8"))
    catalog = load_catalog(catalog_file)

    trends_to_match = trends[:top_n]

    rprint(f"[cyan]Matching {len(trends_to_match)} trends to {len(catalog)} products...[/cyan]")

    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)

    matched_trends = []

    for i, trend in enumerate(trends_to_match, start=1):
        try:
            rprint(f"[dim]  [{i}/{len(trends_to_match)}] {trend.get('trend', 'Unknown')[:50]}...[/dim]")

            # Filter catalog by trend countries (if available)
            trend_countries = trend.get("countries", [])
            filtered_catalog = filter_catalog_by_country(catalog, trend_countries)

            if not filtered_catalog:
                # No products available in these countries
                matched_trends.append({
                    **trend,
                    "product_matches": []
                })
                continue

            # Create matching prompt
            prompt = _create_matching_prompt(trend, filtered_catalog[:50])  # Limit to 50 products

            # Call Claude API
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=MATCHING_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract matches from response
            response_text = message.content[0].text
            matches = _extract_matches(response_text)

            # Add matches to trend
            matched_trends.append({
                **trend,
                "product_matches": matches
            })

        except Exception as e:
            rprint(f"[red]  Error matching trend: {e}[/red]")
            matched_trends.append({
                **trend,
                "product_matches": [],
                "matching_error": str(e)
            })
            continue

    # Write results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(matched_trends, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # Count successful matches
    total_matches = sum(len(t.get("product_matches", [])) for t in matched_trends)

    rprint(f"[green]Matching complete![/green] {total_matches} product matches across {len(matched_trends)} trends")
    rprint(f"[dim]Output: {output_file}[/dim]")

    return len(matched_trends)


def _create_matching_prompt(trend: Dict[str, Any], catalog: List[Dict[str, Any]]) -> str:
    """
    Create matching prompt for a single trend.

    Args:
        trend: Trend dictionary
        catalog: Product catalog (already filtered)

    Returns:
        Formatted prompt string
    """
    # Extract analysis summary if available
    analysis = trend.get("analysis", {})
    analysis_summary = ""
    if analysis and "product_fit" in analysis:
        analysis_summary = f"Product Fit: {analysis.get('product_fit')}, Market Readiness: {analysis.get('market_readiness')}"
    else:
        analysis_summary = "No analysis available"

    # Format catalog as compact JSON
    catalog_json = json.dumps(catalog, indent=2)

    return MATCHING_USER_PROMPT_TEMPLATE.format(
        trend_name=trend.get("trend", "Unknown"),
        countries=", ".join(trend.get("countries", [])),
        analysis_summary=analysis_summary,
        catalog_json=catalog_json,
    )


def _extract_matches(text: str) -> List[Dict[str, Any]]:
    """
    Extract product matches from Claude's response.

    Args:
        text: Response text from Claude

    Returns:
        List of match dictionaries
    """
    # Remove markdown code blocks if present
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # Parse JSON
    try:
        matches = json.loads(text)
        if not isinstance(matches, list):
            return []
        return matches
    except json.JSONDecodeError:
        # If parsing fails, return empty list
        return []
