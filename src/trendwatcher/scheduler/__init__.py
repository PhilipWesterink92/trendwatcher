"""
Scheduling module for automated trendwatcher jobs.
"""
from .daemon import start_daemon

__all__ = ["start_daemon"]
