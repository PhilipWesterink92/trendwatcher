"""
Resy menu scraper.

Resy is a popular reservation platform used by high-end restaurants,
particularly strong in NYC, LA, and major US cities.

Since Resy doesn't have a public API, we scrape restaurant pages.
"""
from __future__ import annotations

import re
from typing import Dict, List

from bs4 import BeautifulSoup
from rich import print

from trendwatcher.ingest.fetch import fetch_url
from .base import MenuSource


class ResyMenuSource(MenuSource):
    """Scrape menu items from Resy restaurant pages."""

    BASE_URL = "https://resy.com"

    def fetch_dishes(self, city: str, limit: int = 100) -> List[Dict]:
        """
        Fetch dishes from top Resy restaurants in a city.

        Note: Resy's website structure may change. This is a best-effort scraper.

        Args:
            city: City slug (e.g., "ny", "la", "sf")
            limit: Maximum dishes to return

        Returns:
            List of dish documents
        """
        dishes = []

        # City-specific restaurant discovery URLs
        # Format: /cities/{city_slug}/venues
        city_url = f"{self.BASE_URL}/cities/{city.lower()}/venues"

        try:
            # Fetch city venue list
            doc = fetch_url(city_url, source_id=self.source_id, country=self.country)

            if doc.get("status_code") != 200:
                print(f"[yellow]{self.source_id}[/yellow] failed to fetch {city_url}: {doc.get('status_code')}")
                return []

            html = doc.get("text", "")
            soup = BeautifulSoup(html, "html.parser")

            # Find restaurant links
            # Resy structure: look for venue cards
            venue_links = soup.find_all("a", href=re.compile(r"/venues/"))

            restaurant_urls = []
            for link in venue_links[:20]:  # Limit to top 20 restaurants
                href = link.get("href", "")
                if href and href.startswith("/"):
                    restaurant_urls.append(f"{self.BASE_URL}{href}")

            # Fetch menu from each restaurant
            for rest_url in restaurant_urls:
                if len(dishes) >= limit:
                    break

                rest_dishes = self._scrape_restaurant_menu(rest_url, city)
                dishes.extend(rest_dishes)

        except Exception as e:
            print(f"[yellow]{self.source_id}[/yellow] error fetching {city}: {e}")
            return []

        return dishes[:limit]

    def _scrape_restaurant_menu(self, url: str, city: str) -> List[Dict]:
        """
        Scrape menu items from a single restaurant page.

        Args:
            url: Restaurant page URL
            city: City name

        Returns:
            List of dish documents
        """
        dishes = []

        try:
            doc = fetch_url(url, source_id=self.source_id, country=self.country)

            if doc.get("status_code") != 200:
                return []

            html = doc.get("text", "")
            soup = BeautifulSoup(html, "html.parser")

            # Extract restaurant name
            # Resy uses h1 or specific class for restaurant name
            restaurant_name = ""
            name_tag = soup.find("h1")
            if name_tag:
                restaurant_name = name_tag.get_text(strip=True)

            # Extract cuisine type
            cuisine = ""
            cuisine_tag = soup.find(string=re.compile(r"Cuisine", re.I))
            if cuisine_tag and cuisine_tag.parent:
                cuisine = cuisine_tag.parent.get_text(strip=True)

            # Menu items structure varies - look for common patterns
            # Option 1: Menu sections with dish names
            menu_items = soup.find_all(["h3", "h4", "div"], class_=re.compile(r"menu|dish|item", re.I))

            for item in menu_items[:10]:  # Limit per restaurant
                dish_text = item.get_text(strip=True)

                # Skip section headers (too generic)
                if len(dish_text) < 5 or len(dish_text) > 100:
                    continue

                # Skip if it's just a category name
                if dish_text.lower() in ["appetizers", "mains", "desserts", "drinks", "starters"]:
                    continue

                # Extract price if present
                price_match = re.search(r"\$[\d.,]+", dish_text)
                price = price_match.group(0) if price_match else ""

                # Clean dish name (remove price)
                dish_name = re.sub(r"\$[\d.,]+", "", dish_text).strip()

                if dish_name:
                    dishes.append(
                        self._make_dish_doc(
                            restaurant=restaurant_name or "Unknown Restaurant",
                            dish_name=dish_name,
                            city=city,
                            url=url,
                            cuisine=cuisine,
                            price=price,
                        )
                    )

        except Exception as e:
            print(f"[yellow]{self.source_id}[/yellow] error scraping {url}: {e}")

        return dishes
