"""
Weekly trend history storage.

Enables week-over-week tracking for velocity scoring.
"""
from .jsonl_store import HistoryStore

__all__ = ["HistoryStore"]
