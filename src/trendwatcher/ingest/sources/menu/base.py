"""
Base interface for menu data sources.

Menu sources track restaurant dishes to detect chef-led trends before they
hit retail/consumer search patterns.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List


class MenuSource(ABC):
    """Abstract base class for menu data sources."""

    def __init__(self, source_id: str, country: str):
        """
        Initialize menu source.

        Args:
            source_id: Unique identifier for this source (e.g., "menu_resy_nyc")
            country: Country code (e.g., "US", "FR")
        """
        self.source_id = source_id
        self.country = country

    @abstractmethod
    def fetch_dishes(self, city: str, limit: int = 100) -> List[Dict]:
        """
        Fetch new/trending dishes from restaurants.

        Args:
            city: City to search (e.g., "NYC", "Paris", "Amsterdam")
            limit: Maximum number of dishes to return

        Returns:
            List of dish dictionaries with structure:
            {
                "type": "menu_dish",
                "country": str,
                "city": str,
                "restaurant": str,
                "dish_name": str,
                "cuisine": str,
                "url": str,
                "fetched_at": ISO timestamp,
                "seed": source_id,
                "metadata": {
                    "price": Optional[str],
                    "category": Optional[str],  # appetizer, main, dessert
                }
            }
        """
        pass

    def _make_dish_doc(
        self,
        restaurant: str,
        dish_name: str,
        city: str,
        url: str,
        cuisine: str = "",
        price: str = "",
        category: str = "",
    ) -> Dict:
        """
        Helper to create standardized dish document.

        Args:
            restaurant: Restaurant name
            dish_name: Name of the dish
            city: City name
            url: URL to restaurant/dish page
            cuisine: Cuisine type (optional)
            price: Price string (optional)
            category: Dish category (optional)

        Returns:
            Standardized dish document
        """
        return {
            "type": "menu_dish",
            "country": self.country,
            "city": city,
            "restaurant": restaurant,
            "dish_name": dish_name,
            "cuisine": cuisine,
            "url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat() + "Z",
            "seed": self.source_id,
            "query": dish_name,  # For extraction pipeline compatibility
            "metadata": {
                "price": price,
                "category": category,
            },
        }
