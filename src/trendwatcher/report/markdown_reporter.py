"""
Weekly Markdown report generator.

Generates actionable trend reports with:
- Executive Summary
- Act Now (score >= 18): 0-3 months
- Near-term Bets (12-17): 3-6 months
- Watchlist (8-11): 6-12 months
- Fads to Ignore: Low specificity + high recency decay
- Appendix: Full CSV table
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from rich import print


def generate_weekly_report(
    trends_file: Path,
    output_file: Path,
    week: str = None,
) -> None:
    """
    Generate weekly Markdown report from trends.json.

    Args:
        trends_file: Path to trends.json
        output_file: Path to output .md file
        week: Week identifier (default: current week)
    """
    if not trends_file.exists():
        print(f"[red]Trends file not found:[/red] {trends_file}")
        return

    if week is None:
        week = datetime.now().strftime("%Y_w%U")

    # Load trends
    trends = json.loads(trends_file.read_text(encoding="utf-8"))

    # Tier trends by score
    act_now = [t for t in trends if t.get("score", 0) >= 18]
    near_term = [t for t in trends if 12 <= t.get("score", 0) < 18]
    watchlist = [t for t in trends if 8 <= t.get("score", 0) < 12]
    fads = identify_fads(trends)

    # Generate report sections
    md_lines = []

    md_lines.extend(generate_header(week))
    md_lines.extend(generate_executive_summary(trends, act_now, near_term))
    md_lines.extend(generate_act_now_section(act_now))
    md_lines.extend(generate_near_term_section(near_term))
    md_lines.extend(generate_watchlist_section(watchlist))
    md_lines.extend(generate_fads_section(fads))
    md_lines.extend(generate_appendix_table(trends))

    # Write to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"[green][OK][/green] Weekly report generated: {output_file}")


def generate_header(week: str) -> List[str]:
    """Generate report header."""
    year, week_num = week.split("_w")
    return [
        f"# Picnic Food Trends Report - Week {week_num}, {year}",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
    ]


def generate_executive_summary(
    trends: List[Dict],
    act_now: List[Dict],
    near_term: List[Dict],
) -> List[str]:
    """Generate executive summary section."""
    lines = [
        "## Executive Summary",
        "",
    ]

    # Top 3 themes
    themes = identify_themes(act_now + near_term)
    if themes:
        for theme in themes[:3]:
            lines.append(f"- {theme}")
        lines.append("")

    # Quick stats
    lines.extend([
        f"**Action Items:** {len(act_now)} trends require immediate attention (0-3 months)",
        f"**Near-term Bets:** {len(near_term)} trends to watch closely (3-6 months)",
        "",
        "---",
        "",
    ])

    return lines


def identify_themes(trends: List[Dict]) -> List[str]:
    """
    Identify high-level themes from trends.

    Returns:
        List of theme statements
    """
    themes = []

    # Group by entity type
    branded_count = len([t for t in trends if t.get("entity_type") == "branded_product"])
    ingredient_count = len([t for t in trends if t.get("entity_type") == "ingredient_variety"])
    equipment_count = len([t for t in trends if t.get("entity_type") == "equipment"])

    if ingredient_count >= 3:
        themes.append(f"Premium ingredients gaining traction ({ingredient_count} varieties)")

    if equipment_count >= 2:
        themes.append(f"Kitchen equipment driving format innovation ({equipment_count} items)")

    if branded_count >= 2:
        themes.append(f"Viral branded products emerging ({branded_count} products)")

    # Market flow themes
    kr_jp_trends = [t for t in trends if any(c in ["KR", "JP"] for c in t.get("countries", []))]
    if kr_jp_trends:
        themes.append(f"Asian-led trends mainstreaming ({len(kr_jp_trends)} items from KR/JP)")

    return themes


def generate_act_now_section(trends: List[Dict]) -> List[str]:
    """Generate Act Now section (0-3 months)."""
    lines = [
        "## Act Now (0-3 months)",
        "",
        f"*{len(trends)} trends with score >= 18*",
        "",
    ]

    if not trends:
        lines.append("*No high-urgency trends this week.*")
        lines.append("")
        return lines

    for i, trend in enumerate(trends[:12], start=1):
        lines.extend(format_detailed_trend(i, trend, urgency="high"))

    return lines


def generate_near_term_section(trends: List[Dict]) -> List[str]:
    """Generate Near-term Bets section (3-6 months)."""
    lines = [
        "## Near-term Bets (3-6 months)",
        "",
        f"*{len(trends)} trends with score 12-17*",
        "",
    ]

    if not trends:
        lines.append("*No medium-priority trends this week.*")
        lines.append("")
        return lines

    for i, trend in enumerate(trends[:12], start=1):
        lines.extend(format_compact_trend(i, trend))

    return lines


def generate_watchlist_section(trends: List[Dict]) -> List[str]:
    """Generate Watchlist section (6-12 months)."""
    lines = [
        "## Watchlist (6-12 months)",
        "",
        f"*{len(trends)} trends with score 8-11*",
        "",
    ]

    if not trends:
        lines.append("*No watchlist trends this week.*")
        lines.append("")
        return lines

    for i, trend in enumerate(trends[:20], start=1):
        name = trend.get("trend", "")[:50]
        score = trend.get("score", 0)
        countries = ", ".join(trend.get("countries", []))
        entity_type = trend.get("entity_type", "N/A")

        lines.append(f"{i}. **{name}** (Score: {score}, Type: {entity_type}, Markets: {countries})")

    lines.append("")
    return lines


def generate_fads_section(fads: List[Dict]) -> List[str]:
    """Generate Fads to Ignore section."""
    lines = [
        "## Fads to Ignore",
        "",
        "*Low specificity or recipe-only trends (no SKU potential)*",
        "",
    ]

    if not fads:
        lines.append("*No fads identified this week.*")
        lines.append("")
        return lines

    for fad in fads[:8]:
        name = fad.get("trend", "")[:50]
        reason = fad.get("fad_reason", "Low actionability")
        lines.append(f"- **{name}** - {reason}")

    lines.append("")
    return lines


def identify_fads(trends: List[Dict]) -> List[Dict]:
    """
    Identify fads (trends to ignore).

    Criteria:
    - Low specificity (< 2)
    - Recipe-only (contains "recipe" but no specific product)
    - Single-market only
    """
    fads = []

    for trend in trends:
        specificity = trend.get("score_breakdown", {}).get("specificity", 0)
        trend_name = trend.get("trend", "").lower()
        countries = trend.get("countries", [])
        entity_type = trend.get("entity_type")

        # Fad criteria
        is_recipe_only = "recipe" in trend_name and not entity_type
        low_specificity = specificity < 2.0
        single_market = len(countries) == 1

        if is_recipe_only:
            trend["fad_reason"] = "Recipe fad, no new SKU"
            fads.append(trend)
        elif low_specificity and single_market:
            trend["fad_reason"] = "Too generic, single market only"
            fads.append(trend)

    return fads


def format_detailed_trend(rank: int, trend: Dict, urgency: str = "high") -> List[str]:
    """
    Format a trend with full details (for Act Now section).

    Args:
        rank: Trend rank
        trend: Trend dict
        urgency: high/medium/low

    Returns:
        List of markdown lines
    """
    name = trend.get("trend", "")
    score = trend.get("score", 0)
    breakdown = trend.get("score_breakdown", {})
    countries = trend.get("countries", [])
    entity_type = trend.get("entity_type", "N/A")
    raw_count = trend.get("raw_count", 0)

    # Market flow
    lead_lag = trend.get("lead_lag", {})
    has_lead = lead_lag.get("has_lead", False)
    has_target = lead_lag.get("has_target", False)

    market_flow = ""
    if has_lead and has_target:
        market_flow = " (Lead → Target markets)"
    elif has_lead:
        market_flow = " (Lead markets only)"
    elif has_target:
        market_flow = " (Target markets: act fast!)"

    lines = [
        f"### {rank}. {name} (Score: {score}/25){market_flow}",
        "",
        f"**Type:** {entity_type or 'General'}  ",
        f"**Markets:** {', '.join(countries)}  ",
        f"**Signals:** {raw_count} data points  ",
        "",
        "**Score Breakdown:**",
        f"- Recency: {breakdown.get('recency', 0)}/5",
        f"- Breadth: {breakdown.get('breadth', 0)}/5",
        f"- Velocity: {breakdown.get('velocity', 0)}/5",
        f"- Specificity: {breakdown.get('specificity', 0)}/5",
        f"- Diversity: {breakdown.get('diversity', 0)}/5",
        "",
        "---",
        "",
    ]

    return lines


def format_compact_trend(rank: int, trend: Dict) -> List[str]:
    """Format a trend compactly (for Near-term section)."""
    name = trend.get("trend", "")[:60]
    score = trend.get("score", 0)
    countries = ", ".join(trend.get("countries", []))
    entity_type = trend.get("entity_type", "N/A")

    return [
        f"**{rank}. {name}** (Score: {score}, Type: {entity_type})",
        f"  - Markets: {countries}",
        "",
    ]


def generate_appendix_table(trends: List[Dict]) -> List[str]:
    """Generate appendix CSV table."""
    lines = [
        "## Appendix: All Candidates",
        "",
        "| Rank | Trend | Score | R | B | V | S | D | Markets |",
        "|------|-------|-------|---|---|---|---|---|---------|",
    ]

    for i, t in enumerate(trends[:50], start=1):
        name = t.get("trend", "")[:40]
        score = t.get("score", 0)
        sb = t.get("score_breakdown", {})
        countries = ", ".join(t.get("countries", [])[:3])

        lines.append(
            f"| {i} | {name} | {score} | "
            f"{sb.get('recency', 0)} | {sb.get('breadth', 0)} | "
            f"{sb.get('velocity', 0)} | {sb.get('specificity', 0)} | "
            f"{sb.get('diversity', 0)} | {countries} |"
        )

    lines.append("")
    return lines
