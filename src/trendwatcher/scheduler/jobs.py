"""
Job implementations for scheduled trendwatcher tasks.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from rich import print as rprint

# Import CLI functions to reuse existing logic
from trendwatcher.ingest.fetch import fetch_url
from trendwatcher.ingest.google_trends import fetch_rising_searches
from trendwatcher.ingest.reddit import fetch_reddit_posts
from trendwatcher.ingest.food_blogs import fetch_food_blogs
from trendwatcher.extract.extract_trends import run_extract
from trendwatcher.analyze import analyze_trends

# Set up logging
logger = logging.getLogger("trendwatcher.scheduler")


def job_ingest(config_path: Path, output_path: Path):
    """
    Scheduled ingest job - fetches all enabled sources.

    Args:
        config_path: Path to sources.yaml
        output_path: Path to docs.jsonl output file
    """
    import yaml
    import json

    logger.info("Starting scheduled ingest job")
    rprint(f"[cyan]🔄 Running ingest job at {datetime.now().isoformat()}[/cyan]")

    try:
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        sources = [s for s in cfg.get("sources", []) if s.get("enabled")]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        total_written = 0

        with output_path.open("a", encoding="utf-8") as f:
            for s in sources:
                stype = s.get("type")

                try:
                    # Google Trends
                    if stype == "google_trends":
                        country = s.get("country")
                        rows = fetch_rising_searches(country)
                        for r in rows:
                            f.write(json.dumps(r, ensure_ascii=False) + "\n")
                            total_written += 1
                        logger.info(f"{s['id']}: {len(rows)} trends")

                    # Competitor pages
                    elif stype == "competitor_new":
                        url = s.get("url")
                        if url:
                            doc = fetch_url(url, source_id=s["id"], country=s.get("country"))
                            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
                            total_written += 1
                            logger.info(f"{s['id']}: status={doc.get('status_code')}")

                    # Reddit
                    elif stype == "reddit":
                        rows = fetch_reddit_posts(
                            s.get("subreddits", []),
                            country=s.get("country", "US"),
                            limit=s.get("limit", 50),
                            time_filter=s.get("time_filter", "week"),
                        )
                        for r in rows:
                            f.write(json.dumps(r, ensure_ascii=False) + "\n")
                            total_written += 1
                        logger.info(f"{s['id']}: {len(rows)} posts")

                    # Food blogs
                    elif stype == "food_blog":
                        rows = fetch_food_blogs(
                            s.get("feeds", []),
                            country=s.get("country", "US"),
                            max_age_days=s.get("max_age_days", 30),
                        )
                        for r in rows:
                            f.write(json.dumps(r, ensure_ascii=False) + "\n")
                            total_written += 1
                        logger.info(f"{s['id']}: {len(rows)} articles")

                except Exception as e:
                    logger.error(f"Failed to fetch {s['id']}: {e}")
                    continue

        logger.info(f"Ingest job complete: {total_written} documents written")
        rprint(f"[green]✓ Ingest complete: {total_written} documents[/green]")

    except Exception as e:
        logger.error(f"Ingest job failed: {e}", exc_info=True)
        rprint(f"[red]✗ Ingest job failed: {e}[/red]")
        raise


def job_extract(trends_output: Path):
    """
    Scheduled extract job - clusters trends from raw documents.

    Args:
        trends_output: Path to trends.json output file
    """
    logger.info("Starting scheduled extract job")
    rprint(f"[cyan]🔄 Running extract job at {datetime.now().isoformat()}[/cyan]")

    try:
        rows, clusters = run_extract()
        logger.info(f"Extract job complete: {rows} rows, {clusters} clusters")
        rprint(f"[green]✓ Extract complete: {clusters} trends[/green]")

    except Exception as e:
        logger.error(f"Extract job failed: {e}", exc_info=True)
        rprint(f"[red]✗ Extract job failed: {e}[/red]")
        raise


def job_analyze(
    trends_file: Path,
    output_file: Path,
    top_n: int = 25,
):
    """
    Scheduled analyze job - runs LLM analysis on top trends.

    Args:
        trends_file: Path to trends.json
        output_file: Path to trends_analyzed.json output
        top_n: Number of top trends to analyze
    """
    logger.info("Starting scheduled analyze job")
    rprint(f"[cyan]🔄 Running analyze job at {datetime.now().isoformat()}[/cyan]")

    try:
        if not trends_file.exists():
            logger.warning("Trends file not found, skipping analysis")
            return

        count = analyze_trends(
            trends_file=trends_file,
            output_file=output_file,
            top_n=top_n,
        )
        logger.info(f"Analyze job complete: {count} trends analyzed")
        rprint(f"[green]✓ Analyze complete: {count} trends[/green]")

    except Exception as e:
        logger.error(f"Analyze job failed: {e}", exc_info=True)
        rprint(f"[red]✗ Analyze job failed: {e}[/red]")
        raise


def job_report_slack(trends_file: Path, channel: str):
    """
    Scheduled Slack report job.

    Args:
        trends_file: Path to trends JSON (analyzed if available)
        channel: Slack channel to post to
    """
    logger.info("Starting scheduled Slack report job")
    rprint(f"[cyan]🔄 Running Slack report job at {datetime.now().isoformat()}[/cyan]")

    try:
        from trendwatcher.report import send_slack_report

        if not trends_file.exists():
            logger.warning("Trends file not found, skipping report")
            return

        send_slack_report(
            trends_file=trends_file,
            channel=channel,
            top_n=10,
        )
        logger.info("Slack report sent successfully")
        rprint(f"[green]✓ Slack report sent to {channel}[/green]")

    except Exception as e:
        logger.error(f"Slack report job failed: {e}", exc_info=True)
        rprint(f"[red]✗ Slack report failed: {e}[/red]")
        raise
