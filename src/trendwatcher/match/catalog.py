"""
Product catalog loader and utilities.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any


def load_catalog(catalog_file: Path) -> List[Dict[str, Any]]:
    """
    Load product catalog from JSON file.

    Args:
        catalog_file: Path to catalog JSON file

    Returns:
        List of product dictionaries

    Expected catalog format:
        [
            {
                "product_id": "12345",
                "name": "Organic Matcha Powder",
                "category": "Tea & Coffee",
                "tags": ["matcha", "green tea", "organic"],
                "available_in": ["NL", "DE", "FR"]
            },
            ...
        ]
    """
    if not catalog_file.exists():
        raise FileNotFoundError(f"Catalog file not found: {catalog_file}")

    catalog = json.loads(catalog_file.read_text(encoding="utf-8"))

    # Validate catalog structure
    if not isinstance(catalog, list):
        raise ValueError("Catalog must be a JSON array of products")

    for i, product in enumerate(catalog):
        if not isinstance(product, dict):
            raise ValueError(f"Product at index {i} must be a dictionary")

        # Check for required fields
        required = ["product_id", "name"]
        for field in required:
            if field not in product:
                raise ValueError(f"Product at index {i} missing required field: {field}")

    return catalog


def filter_catalog_by_country(
    catalog: List[Dict[str, Any]],
    countries: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter catalog to products available in specified countries.

    Args:
        catalog: Full product catalog
        countries: List of country codes (e.g., ["NL", "DE"])

    Returns:
        Filtered catalog
    """
    if not countries:
        return catalog

    filtered = []
    for product in catalog:
        available_in = product.get("available_in", [])
        if any(country in available_in for country in countries):
            filtered.append(product)

    return filtered


# TODO: Replace with actual Picnic API integration
# Once Picnic API access is established, create a PicnicCatalogClient class here
# that fetches products from the API instead of reading from JSON files
#
# class PicnicCatalogClient:
#     def __init__(self, api_key: str, api_url: str):
#         self.api_key = api_key
#         self.api_url = api_url
#
#     def get_products(self, category: str = None, limit: int = 100) -> List[Dict]:
#         # Implement API call to fetch products
#         pass
#
#     def search_products(self, query: str) -> List[Dict]:
#         # Implement product search via API
#         pass
