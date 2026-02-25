"""Base interface for history storage."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class HistoryStore(ABC):
    """Abstract base class for trend history storage."""

    @abstractmethod
    def snapshot(self, week: str) -> None:
        """
        Save current trends as a weekly snapshot.

        Args:
            week: Week identifier (e.g., "2026_w08")
        """
        pass

    @abstractmethod
    def load_history(self, trend_label: str) -> List[Dict]:
        """
        Load all weekly snapshots for a specific trend.

        Args:
            trend_label: Trend name to load history for

        Returns:
            List of weekly snapshots, sorted by week
        """
        pass

    @abstractmethod
    def load_all_histories(self) -> Dict[str, List[Dict]]:
        """
        Load all trend histories.

        Returns:
            Dict mapping trend labels to their history lists
        """
        pass
