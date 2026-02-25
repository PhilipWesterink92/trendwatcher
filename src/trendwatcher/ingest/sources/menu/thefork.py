"""
TheFork (LaFourchette) menu scraper.

TheFork is the leading restaurant reservation platform in Europe,
particularly strong in France, Netherlands, and Spain.

Brand names by market:
- France: LaFourchette
- Netherlands: TheFork
- Spain/Italy: ElTenedor/TheFork
"""
from __future__ import annotations

import re
from typing import Dict, List

from bs4 import BeautifulSoup
from rich import print

from trendwatcher.ingest.fetch import fetch_url
from .base import MenuSource


class TheForkMenuSource(MenuSource):
    """Scrape menu items from TheFork restaurant pages."""

    # Market-specific base URLs
    BASE_URLS = {
        "FR": "https://www.lafourchette.com",
        "NL": "https://www.thefork.nl",
        "DE": "https://www.thefork.de",
        "ES": "https://www.eltenedor.es",
        "IT": "https://www.thefork.it",
    }

    def __init__(self, source_id: str, country: str):
        super().__init__(source_id, country)
        self.base_url = self.BASE_URLS.get(country, "https://www.thefork.com")

    def fetch_dishes(self, city: str, limit: int = 100) -> List[Dict]:
        """
        Fetch dishes from top TheFork restaurants in a city.

        Args:
            city: City name (e.g., "Paris", "Amsterdam", "Berlin")
            limit: Maximum dishes to return

        Returns:
            List of dish documents
        """
        dishes = []

        # TheFork search URL format
        # Format: /city/{city-slug}/restaurants
        city_slug = city.lower().replace(" ", "-")
        search_url = f"{self.base_url}/city/{city_slug}/restaurants"

        try:
            # Fetch restaurant list
            doc = fetch_url(search_url, source_id=self.source_id, country=self.country)

            if doc.get("status_code") != 200:
                print(f"[yellow]{self.source_id}[/yellow] failed to fetch {search_url}: {doc.get('status_code')}")
                return []

            html = doc.get("text", "")
            soup = BeautifulSoup(html, "html.parser")

            # Find restaurant links
            # TheFork uses data-restaurant-id or specific link patterns
            restaurant_links = soup.find_all("a", href=re.compile(r"/restaurant/"))

            restaurant_urls = []
            seen_urls = set()

            for link in restaurant_links:
                href = link.get("href", "")
                if href and href not in seen_urls:
                    if not href.startswith("http"):
                        href = f"{self.base_url}{href}"
                    seen_urls.add(href)
                    restaurant_urls.append(href)

                if len(restaurant_urls) >= 20:  # Limit to top 20
                    break

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
            restaurant_name = ""
            name_tag = soup.find("h1", class_=re.compile(r"restaurant|name", re.I))
            if not name_tag:
                name_tag = soup.find("h1")
            if name_tag:
                restaurant_name = name_tag.get_text(strip=True)

            # Extract cuisine type
            cuisine = ""
            cuisine_tag = soup.find(string=re.compile(r"Cuisine|Cucina|Cocina", re.I))
            if cuisine_tag:
                # Get next element which often contains the actual cuisine
                if cuisine_tag.parent and cuisine_tag.parent.next_sibling:
                    cuisine = cuisine_tag.parent.next_sibling.get_text(strip=True)

            # TheFork often has menu sections
            # Look for menu items in typical structures
            menu_sections = soup.find_all(["div", "li"], class_=re.compile(r"menu|dish|plate|plat", re.I))

            for item in menu_sections[:15]:  # Limit per restaurant
                dish_text = item.get_text(strip=True)

                # Skip if too short or too long
                if len(dish_text) < 5 or len(dish_text) > 120:
                    continue

                # Skip section headers
                skip_terms = [
                    "appetizers", "starters", "mains", "desserts", "drinks",
                    "entrées", "plats", "desserts", "boissons",
                    "antipasti", "primi", "secondi", "dolci",
                    "vorspeisen", "hauptgerichte", "nachtisch",
                ]
                if dish_text.lower() in skip_terms:
                    continue

                # Extract price (various currency formats)
                price_match = re.search(r"[€$£]\s*[\d.,]+|[\d.,]+\s*[€$£]", dish_text)
                price = price_match.group(0) if price_match else ""

                # Clean dish name
                dish_name = re.sub(r"[€$£]\s*[\d.,]+|[\d.,]+\s*[€$£]", "", dish_text).strip()

                # Detect category from context
                category = ""
                if "dessert" in str(item.parent).lower() or "dolci" in str(item.parent).lower():
                    category = "dessert"
                elif "main" in str(item.parent).lower() or "plat" in str(item.parent).lower():
                    category = "main"
                elif "starter" in str(item.parent).lower() or "entrée" in str(item.parent).lower():
                    category = "starter"

                if dish_name and len(dish_name) > 3:
                    dishes.append(
                        self._make_dish_doc(
                            restaurant=restaurant_name or "Unknown Restaurant",
                            dish_name=dish_name,
                            city=city,
                            url=url,
                            cuisine=cuisine,
                            price=price,
                            category=category,
                        )
                    )

        except Exception as e:
            print(f"[yellow]{self.source_id}[/yellow] error scraping {url}: {e}")

        return dishes
