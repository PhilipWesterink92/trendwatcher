"""
JSONL-based history storage.

Stores weekly snapshots in data/history/ as JSONL files.
Format: data/history/trends_YYYY_wWW.jsonl
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from rich import print


class HistoryStore:
    """Store and retrieve weekly trend snapshots."""

    def __init__(
        self,
        history_dir: Path = None,
        trends_file: Path = None,
    ):
        """
        Initialize history store.

        Args:
            history_dir: Directory for history snapshots (default: data/history)
            trends_file: Path to current trends.json (default: data/processed/trends.json)
        """
        self.history_dir = history_dir or Path("data/history")
        self.trends_file = trends_file or Path("data/processed/trends.json")

        self.history_dir.mkdir(parents=True, exist_ok=True)

    def snapshot(self, week: str = None) -> None:
        """
        Save current trends.json as a weekly snapshot.

        Args:
            week: Week identifier (e.g., "2026_w08"). If None, uses current week.
        """
        if week is None:
            # Auto-generate week identifier: YYYY_wWW
            now = datetime.now()
            week = now.strftime("%Y_w%U")

        if not self.trends_file.exists():
            print(f"[yellow]No trends file found at {self.trends_file}[/yellow]")
            return

        # Load current trends
        trends = json.loads(self.trends_file.read_text(encoding="utf-8"))

        # Snapshot file path
        snapshot_file = self.history_dir / f"trends_{week}.jsonl"

        # Write snapshot (one trend per line)
        with snapshot_file.open("w", encoding="utf-8") as f:
            for t in trends:
                snapshot_entry = {
                    "week": week,
                    "trend": t["trend"],
                    "score": t.get("score", 0),
                    "score_breakdown": t.get("score_breakdown", {}),
                    "countries": t.get("countries", []),
                    "raw_count": t.get("raw_count", 0),
                    "entity_type": t.get("entity_type"),
                }
                f.write(json.dumps(snapshot_entry, ensure_ascii=False) + "\n")

        print(f"[green][OK][/green] Saved {len(trends)} trends to {snapshot_file}")

    def load_history(self, trend_label: str) -> List[Dict]:
        """
        Load all weekly snapshots for a specific trend.

        Args:
            trend_label: Trend name

        Returns:
            List of weekly snapshots, sorted by week
        """
        history = []

        for snapshot_file in sorted(self.history_dir.glob("trends_*.jsonl")):
            for line in snapshot_file.read_text(encoding="utf-8").splitlines():
                try:
                    entry = json.loads(line)
                    if entry.get("trend") == trend_label:
                        history.append(entry)
                except json.JSONDecodeError:
                    continue

        return sorted(history, key=lambda x: x.get("week", ""))

    def load_all_histories(self) -> Dict[str, List[Dict]]:
        """
        Load all trend histories.

        Returns:
            Dict mapping trend labels to their history lists
        """
        history_map = defaultdict(list)

        for snapshot_file in sorted(self.history_dir.glob("trends_*.jsonl")):
            for line in snapshot_file.read_text(encoding="utf-8").splitlines():
                try:
                    entry = json.loads(line)
                    trend_label = entry.get("trend")
                    if trend_label:
                        history_map[trend_label].append(entry)
                except json.JSONDecodeError:
                    continue

        # Sort each trend's history by week
        for trend_label in history_map:
            history_map[trend_label].sort(key=lambda x: x.get("week", ""))

        return dict(history_map)
