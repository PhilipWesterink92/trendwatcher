from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from rich import print
from rich.table import Table
from dotenv import load_dotenv

from trendwatcher.ingest.fetch import fetch_url
from trendwatcher.ingest.google_trends_v2 import fetch_rising_searches  # Using v2 (works around 404)
from trendwatcher.ingest.reddit import fetch_reddit_posts
from trendwatcher.ingest.food_blogs import fetch_food_blogs
from trendwatcher.extract.extract_trends import run_extract
from trendwatcher.analyze import analyze_trends

# Load environment variables from .env file
load_dotenv()


app = typer.Typer(help="Trendwatcher CLI")

CONFIG_PATH = Path("src/trendwatcher/config/sources.yaml")
SCHEDULER_CONFIG_PATH = Path("src/trendwatcher/config/scheduler.yaml")
DOCS_OUT = Path("data/raw/docs.jsonl")
TRENDS_OUT = Path("data/processed/trends.json")
TRENDS_ANALYZED_OUT = Path("data/processed/trends_analyzed.json")
TRENDS_MATCHED_OUT = Path("data/processed/trends_matched.json")


# =========================
# INGEST
# =========================

@app.command()
def ingest():
    """Fetch configured sources and store raw documents."""
    import yaml

    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    sources = [s for s in cfg.get("sources", []) if s.get("enabled")]

    DOCS_OUT.parent.mkdir(parents=True, exist_ok=True)

    total_written = 0

    with DOCS_OUT.open("a", encoding="utf-8") as f:
        for s in sources:
            stype = s.get("type")

            # --- Google Trends ---
            if stype == "google_trends":
                country = s.get("country")
                rows = fetch_rising_searches(country)

                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
                    total_written += 1

                print(f"[cyan]{s['id']}[/cyan] trends rows={len(rows)}")
                continue

            # --- Competitor pages ---
            if stype == "competitor_new":
                url = s.get("url")
                if not url:
                    continue

                doc = fetch_url(url, source_id=s["id"], country=s.get("country"))
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
                total_written += 1
                print(f"[cyan]{s['id']}[/cyan] {doc.get('status_code')} len={doc.get('text_len')}")
                continue

            # --- Reddit posts ---
            if stype == "reddit":
                try:
                    rows = fetch_reddit_posts(
                        s.get("subreddits", []),
                        country=s.get("country", "US"),
                        limit=s.get("limit", 50),
                        time_filter=s.get("time_filter", "week"),
                    )

                    for r in rows:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                        total_written += 1

                    print(f"[cyan]{s['id']}[/cyan] reddit posts={len(rows)}")
                except Exception as e:
                    print(f"[red]{s['id']} failed:[/red] {e}")
                continue

            # --- Food blog RSS feeds ---
            if stype == "food_blog":
                try:
                    rows = fetch_food_blogs(
                        s.get("feeds", []),
                        country=s.get("country", "US"),
                        max_age_days=s.get("max_age_days", 30),
                    )

                    for r in rows:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                        total_written += 1

                    print(f"[cyan]{s['id']}[/cyan] blog posts={len(rows)}")
                except Exception as e:
                    print(f"[red]{s['id']} failed:[/red] {e}")
                continue

    print(f"[green]ingest complete[/green] wrote={total_written} output={DOCS_OUT}")


# =========================
# EXTRACT
# =========================

@app.command()
def extract():
    """Cluster and score food trends."""
    rows, clusters = run_extract()
    print(f"[green]extract complete[/green] rows={rows} clusters={clusters} out={TRENDS_OUT}")


# =========================
# WATCHLIST ⭐ (NEW)
# =========================

@app.command()
def watchlist(top: int = 25):
    """Show most promising early food trends."""
    if not TRENDS_OUT.exists():
        print("[red]No trends file found. Run extract first.[/red]")
        raise typer.Exit(1)

    data = json.loads(TRENDS_OUT.read_text(encoding="utf-8"))

    table = Table(title="Picnic Trend Watchlist")

    table.add_column("Rank", justify="right")
    table.add_column("Trend")
    table.add_column("Score", justify="right")
    table.add_column("Lead->Target")
    table.add_column("Countries")

    for i, row in enumerate(data[:top], start=1):
        lead = row.get("lead_lag", {})
        lead_flag = "[Y]" if lead.get("has_lead") else "[-]"
        target_flag = "[T]" if lead.get("has_target") else "[-]"

        table.add_row(
            str(i),
            row.get("trend", "")[:40],
            str(row.get("score", "")),
            f"{lead_flag} -> {target_flag}",
            ",".join(row.get("countries", [])),
        )

    print(table)


# =========================
# ANALYZE 🧠 (NEW - Feature 1)
# =========================

@app.command()
def analyze(top: int = 25):
    """Analyze trends using AI to evaluate product fit and market readiness."""
    if not TRENDS_OUT.exists():
        print("[red]No trends file found. Run extract first.[/red]")
        raise typer.Exit(1)

    try:
        count = analyze_trends(
            trends_file=TRENDS_OUT,
            output_file=TRENDS_ANALYZED_OUT,
            top_n=top,
        )
        print(f"[green]✓ Analyzed {count} trends[/green]")
        print(f"[dim]Output: {TRENDS_ANALYZED_OUT}[/dim]")
    except Exception as e:
        print(f"[red]Analysis failed:[/red] {e}")
        raise typer.Exit(1)


# =========================
# MATCH 🎯 (NEW - Feature 3)
# =========================

@app.command()
def match(
    catalog: str = "data/catalog/products.example.json",
    top: int = 25,
):
    """Match trends to Picnic product catalog."""
    from trendwatcher.match import match_trends_to_catalog

    catalog_path = Path(catalog)
    if not catalog_path.exists():
        print(f"[red]Catalog not found:[/red] {catalog_path}")
        print("[yellow]Hint:[/yellow] Create a product catalog JSON file or use --catalog to specify a path")
        raise typer.Exit(1)

    # Use analyzed trends if available, otherwise use raw trends
    input_file = TRENDS_ANALYZED_OUT if TRENDS_ANALYZED_OUT.exists() else TRENDS_OUT

    if not input_file.exists():
        print("[red]No trends file found. Run extract (and optionally analyze) first.[/red]")
        raise typer.Exit(1)

    try:
        count = match_trends_to_catalog(
            trends_file=input_file,
            catalog_file=catalog_path,
            output_file=TRENDS_MATCHED_OUT,
            top_n=top,
        )
        print(f"[green]✓ Matched {count} trends[/green]")
        print(f"[dim]Output: {TRENDS_MATCHED_OUT}[/dim]")
    except Exception as e:
        print(f"[red]Matching failed:[/red] {e}")
        raise typer.Exit(1)


# =========================
# DAEMON 🤖 (NEW - Feature 4)
# =========================

@app.command()
def daemon():
    """Start background scheduler for automated job execution."""
    from trendwatcher.scheduler import start_daemon

    if not SCHEDULER_CONFIG_PATH.exists():
        print(f"[red]Scheduler config not found:[/red] {SCHEDULER_CONFIG_PATH}")
        print("[yellow]Create scheduler.yaml to configure automated jobs[/yellow]")
        raise typer.Exit(1)

    # Start daemon (blocking - will run until interrupted)
    start_daemon(SCHEDULER_CONFIG_PATH)


# =========================
# REPORT 📊 (NEW - Feature 5)
# =========================

@app.command()
def report(
    channel: str = typer.Option("slack", help="Report channel: slack or email"),
    recipients: str = typer.Option(None, help="Email recipients (comma-separated)"),
    top: int = typer.Option(10, help="Number of top trends to include"),
):
    """Send trend report via Slack or email."""
    # Use analyzed trends if available, otherwise use raw trends
    input_file = TRENDS_ANALYZED_OUT if TRENDS_ANALYZED_OUT.exists() else TRENDS_OUT

    if not input_file.exists():
        print("[red]No trends file found. Run extract (and optionally analyze) first.[/red]")
        raise typer.Exit(1)

    if channel == "slack":
        from trendwatcher.report import send_slack_report

        try:
            send_slack_report(
                trends_file=input_file,
                channel=os.getenv("SLACK_CHANNEL", "#trendwatcher"),
                top_n=top,
            )
            print(f"[green][OK] Slack report sent[/green]")
        except Exception as e:
            print(f"[red]Slack report failed:[/red] {e}")
            raise typer.Exit(1)

    elif channel == "email":
        from trendwatcher.report import send_email_report

        if not recipients:
            recipients = os.getenv("TO_EMAIL")
            if not recipients:
                print("[red]No email recipients specified.[/red]")
                print("[yellow]Use --recipients or set TO_EMAIL in .env[/yellow]")
                raise typer.Exit(1)

        recipient_list = [r.strip() for r in recipients.split(",")]

        try:
            send_email_report(
                trends_file=input_file,
                recipients=recipient_list,
                top_n=top,
            )
            print(f"[green]✓ Email report sent to {len(recipient_list)} recipient(s)[/green]")
        except Exception as e:
            print(f"[red]Email report failed:[/red] {e}")
            raise typer.Exit(1)

    else:
        print(f"[red]Unknown channel:[/red] {channel}")
        print("[yellow]Use 'slack' or 'email'[/yellow]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
