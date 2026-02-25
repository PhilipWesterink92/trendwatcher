"""
Scheduler daemon for automated trendwatcher execution.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from rich import print as rprint
import yaml

from .jobs import job_ingest, job_extract, job_analyze, job_report_slack


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("data/logs/scheduler.log"),
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger("trendwatcher.scheduler")


def start_daemon(config_path: Path):
    """
    Start the scheduler daemon.

    Reads job configurations from scheduler.yaml and schedules them using cron triggers.

    Args:
        config_path: Path to scheduler.yaml configuration file
    """
    # Load scheduler configuration
    if not config_path.exists():
        rprint(f"[red]Scheduler config not found:[/red] {config_path}")
        rprint("[yellow]Create src/trendwatcher/config/scheduler.yaml to configure scheduled jobs[/yellow]")
        sys.exit(1)

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    schedule_config = config.get("schedule", {})

    # Create logs directory
    Path("data/logs").mkdir(parents=True, exist_ok=True)

    # Initialize scheduler
    scheduler = BlockingScheduler(timezone="UTC")

    rprint("[cyan][DAEMON] Starting trendwatcher scheduler daemon[/cyan]")
    rprint("[dim]Press Ctrl+C to stop[/dim]\n")

    # Add jobs based on configuration
    jobs_added = 0

    # Ingest job
    ingest_config = schedule_config.get("ingest", {})
    if ingest_config.get("enabled", False):
        cron = ingest_config.get("cron")
        if cron:
            scheduler.add_job(
                job_ingest,
                trigger=CronTrigger.from_crontab(cron),
                args=[
                    Path("src/trendwatcher/config/sources.yaml"),
                    Path("data/raw/docs.jsonl"),
                ],
                id="ingest",
                name="Ingest data sources",
                misfire_grace_time=300,  # 5 minutes
            )
            rprint(f"[green][OK] Scheduled ingest job:[/green] {cron}")
            jobs_added += 1

    # Extract job
    extract_config = schedule_config.get("extract", {})
    if extract_config.get("enabled", False):
        cron = extract_config.get("cron")
        if cron:
            scheduler.add_job(
                job_extract,
                trigger=CronTrigger.from_crontab(cron),
                args=[Path("data/processed/trends.json")],
                id="extract",
                name="Extract and cluster trends",
                misfire_grace_time=300,
            )
            rprint(f"[green][OK] Scheduled extract job:[/green] {cron}")
            jobs_added += 1

    # Analyze job
    analyze_config = schedule_config.get("analyze", {})
    if analyze_config.get("enabled", False):
        cron = analyze_config.get("cron")
        top_n = analyze_config.get("top_n", 25)
        if cron:
            scheduler.add_job(
                job_analyze,
                trigger=CronTrigger.from_crontab(cron),
                args=[
                    Path("data/processed/trends.json"),
                    Path("data/processed/trends_analyzed.json"),
                    top_n,
                ],
                id="analyze",
                name="Analyze trends with AI",
                misfire_grace_time=600,  # 10 minutes
            )
            rprint(f"[green][OK] Scheduled analyze job:[/green] {cron} (top {top_n})")
            jobs_added += 1

    # Report job (Slack)
    report_config = schedule_config.get("report", {})
    if report_config.get("enabled", False):
        cron = report_config.get("cron")
        channel = report_config.get("channel", "#trendwatcher")
        if cron:
            # Use analyzed trends if available, otherwise raw trends
            trends_file = Path("data/processed/trends_analyzed.json")
            if not trends_file.exists():
                trends_file = Path("data/processed/trends.json")

            scheduler.add_job(
                job_report_slack,
                trigger=CronTrigger.from_crontab(cron),
                args=[trends_file, channel],
                id="report_slack",
                name="Send Slack report",
                misfire_grace_time=300,
            )
            rprint(f"[green][OK] Scheduled Slack report:[/green] {cron} -> {channel}")
            jobs_added += 1

    if jobs_added == 0:
        rprint("[yellow][WARNING] No jobs configured. Check scheduler.yaml[/yellow]")
        sys.exit(1)

    rprint(f"\n[cyan]Running {jobs_added} scheduled jobs...[/cyan]\n")

    # Start scheduler (blocking)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        rprint("\n[yellow]Shutting down scheduler...[/yellow]")
        scheduler.shutdown()
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        rprint(f"[red]Scheduler error: {e}[/red]")
        sys.exit(1)
