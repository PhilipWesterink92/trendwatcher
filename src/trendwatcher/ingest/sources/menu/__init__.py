"""
Menu and restaurant tracking sources.

Chef-led trend detection by monitoring menu changes at top restaurants.
"""
from .base import MenuSource
from .resy import ResyMenuSource
from .thefork import TheForkMenuSource

__all__ = ["MenuSource", "ResyMenuSource", "TheForkMenuSource"]
