"""
LLM-powered trend analysis using Anthropic Claude API.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Any

from anthropic import Anthropic
from rich import print as rprint

from .prompts import ANALYSIS_SYSTEM_PROMPT, create_analysis_prompt


def analyze_trends(
    trends_file: Path,
    output_file: Path,
    *,
    top_n: int = 25,
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 1024,
) -> int:
    """
    Analyze top trends using Claude AI.

    Args:
        trends_file: Path to trends.json file
        output_file: Path to write analyzed trends
        top_n: Number of top trends to analyze
        model: Claude model to use
        max_tokens: Maximum tokens per response

    Returns:
        Number of trends analyzed

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set
    """
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. Please set it in your .env file. "
            "See docs/SETUP.md for instructions."
        )

    # Load trends
    if not trends_file.exists():
        raise FileNotFoundError(f"Trends file not found: {trends_file}")

    trends = json.loads(trends_file.read_text(encoding="utf-8"))
    trends_to_analyze = trends[:top_n]

    rprint(f"[cyan]Analyzing {len(trends_to_analyze)} trends with Claude...[/cyan]")

    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)

    analyzed_trends = []

    for i, trend in enumerate(trends_to_analyze, start=1):
        try:
            rprint(f"[dim]  [{i}/{len(trends_to_analyze)}] {trend.get('trend', 'Unknown')[:50]}...[/dim]")

            # Create prompt for this trend
            prompt = create_analysis_prompt(trend)

            # Call Claude API
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=ANALYSIS_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract JSON from response
            response_text = message.content[0].text
            analysis = _extract_json(response_text)

            # Merge analysis with original trend data
            analyzed_trend = {
                **trend,
                "analysis": analysis,
            }
            analyzed_trends.append(analyzed_trend)

        except Exception as e:
            rprint(f"[red]  Error analyzing trend: {e}[/red]")
            # Include trend without analysis
            analyzed_trends.append({
                **trend,
                "analysis": {
                    "error": str(e)
                }
            })
            continue

    # Write results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(analyzed_trends, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    rprint(f"[green]Analysis complete![/green] Wrote {len(analyzed_trends)} trends to {output_file}")

    return len(analyzed_trends)


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Extract JSON object from Claude's response.

    Claude sometimes wraps JSON in markdown code blocks, so we handle that.

    Args:
        text: Response text from Claude

    Returns:
        Parsed JSON object
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
        return json.loads(text)
    except json.JSONDecodeError as e:
        # If parsing fails, return error info
        return {
            "error": f"Failed to parse JSON: {e}",
            "raw_response": text[:200]  # First 200 chars for debugging
        }


def analyze_single_trend(
    trend: Dict[str, Any],
    *,
    model: str = "claude-sonnet-4-5-20250929",
    api_key: str | None = None,
) -> Dict[str, Any]:
    """
    Analyze a single trend (useful for testing or API usage).

    Args:
        trend: Trend dictionary
        model: Claude model to use
        api_key: Optional API key (uses env var if not provided)

    Returns:
        Analysis dictionary
    """
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

    client = Anthropic(api_key=api_key)
    prompt = create_analysis_prompt(trend)

    message = client.messages.create(
        model=model,
        max_tokens=1024,
        system=ANALYSIS_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text
    return _extract_json(response_text)
