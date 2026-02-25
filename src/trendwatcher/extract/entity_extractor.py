"""
Entity extraction for specific products.

Extracts specific food products and ingredients instead of vague categories.
Examples:
  - "Dubai chocolate" (specific branded product)
  - "Scamorza" (specific cheese variety)
  - "Gochujang" (specific ingredient)

NOT:
  - "Chocolate" (too generic)
  - "Cheese" (too generic)
  - "Spicy sauce" (too generic)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Set


# Ingredient varieties that are specific enough to track
INGREDIENT_VARIETIES = {
    "cheese": [
        "scamorza", "burrata", "stracciatella", "halloumi", "feta",
        "manchego", "gruyere", "comte", "pecorino", "gorgonzola",
        "taleggio", "fontina", "provolone", "mascarpone",
    ],
    "chili": [
        "gochugaru", "gochujang", "calabrian chili", "aleppo pepper",
        "urfa biber", "kashmiri chili", "guajillo", "chipotle",
        "chili crisp", "chili oil", "harissa",
    ],
    "salt": [
        "maldon salt", "fleur de sel", "himalayan pink salt",
        "black lava salt", "smoked salt", "sel gris",
    ],
    "vinegar": [
        "black garlic vinegar", "champagne vinegar", "sherry vinegar",
        "rice vinegar", "apple cider vinegar", "balsamic vinegar",
    ],
    "oil": [
        "truffle oil", "sesame oil", "chili oil", "avocado oil",
        "grapeseed oil", "walnut oil", "pumpkin seed oil",
    ],
    "sauce": [
        "gochujang", "miso", "tahini", "harissa", "sriracha",
        "kimchi", "ponzu", "hoisin", "kewpie mayo", "yuzu kosho",
    ],
    "sweetener": [
        "honey butter", "date syrup", "maple syrup", "agave",
        "monk fruit", "stevia", "coconut sugar",
    ],
}

# Flatten for quick lookup
ALL_SPECIFIC_INGREDIENTS = set()
for category, items in INGREDIENT_VARIETIES.items():
    ALL_SPECIFIC_INGREDIENTS.update([item.lower() for item in items])

# Product format keywords
PRODUCT_FORMATS = {
    "rtd",  # ready-to-drink
    "frozen",
    "tinned",
    "canned",
    "jarred",
    "powdered",
    "instant",
    "dried",
    "smoked",
    "fermented",
    "pickled",
    "protein bar",
    "protein powder",
    "protein pudding",
    "protein ice cream",
    "meal kit",
    "meal prep",
}

# Equipment (already specific enough)
EQUIPMENT = {
    "air fryer",
    "instant pot",
    "sous vide",
    "slow cooker",
    "rice cooker",
    "food processor",
}

# Viral/branded products (high signal)
VIRAL_PRODUCTS = {
    "dubai chocolate",
    "pink sauce",
    "sleepy girl mocktail",
    "internal shower drink",
    "cottage cheese ice cream",
    "cucumber salad",
    "biscoff",
    "kewpie",
    "maldon",
}


@dataclass
class Entity:
    """Extracted food entity."""

    name: str  # Clean entity name
    type: str  # Entity type: branded_product, ingredient_variety, format, equipment
    confidence: float  # 0.0-1.0


def extract_entities(query: str) -> List[Entity]:
    """
    Extract specific food entities from a query.

    Args:
        query: Search query or dish name

    Returns:
        List of extracted entities (may be empty if too generic)
    """
    if not query or len(query) < 3:
        return []

    query_lower = query.lower().strip()
    entities = []

    # Pattern 1: Direct match with viral/branded products
    for product in VIRAL_PRODUCTS:
        if product in query_lower:
            entities.append(
                Entity(
                    name=product,
                    type="branded_product",
                    confidence=1.0,
                )
            )

    # Pattern 2: Equipment (already specific)
    for equip in EQUIPMENT:
        if equip in query_lower:
            entities.append(
                Entity(
                    name=equip,
                    type="equipment",
                    confidence=1.0,
                )
            )

    # Pattern 3: Specific ingredient varieties
    for ingredient in ALL_SPECIFIC_INGREDIENTS:
        if ingredient in query_lower:
            entities.append(
                Entity(
                    name=ingredient,
                    type="ingredient_variety",
                    confidence=0.9,
                )
            )

    # Pattern 4: Product format + food term
    # E.g., "RTD matcha latte", "frozen dumpling", "protein pudding"
    for format_term in PRODUCT_FORMATS:
        if format_term in query_lower:
            # Extract the full phrase (format + following words)
            pattern = rf"\b{re.escape(format_term)}\s+[\w\s]{{3,30}}\b"
            match = re.search(pattern, query_lower)
            if match:
                entities.append(
                    Entity(
                        name=match.group(0).strip(),
                        type="product_format",
                        confidence=0.8,
                    )
                )

    # Pattern 5: Proper noun + food term (branded products)
    # E.g., "Dubai chocolate", "Korean gochujang", "Japanese mayo"
    # Look for Title Case + common food term
    proper_noun_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+([a-z]+)\b"
    matches = re.findall(proper_noun_pattern, query)

    for proper_part, food_part in matches:
        # Check if food_part is actually food-related
        food_terms = {
            "chocolate", "cheese", "sauce", "oil", "salt", "mayo", "mayonnaise",
            "butter", "milk", "cream", "yogurt", "bbq", "chicken", "beef",
            "noodle", "noodles", "curry", "soup", "salad", "tart", "cake",
            "cookie", "ice cream", "pudding", "bar", "drink", "latte", "tea",
        }

        if food_part.lower() in food_terms:
            full_name = f"{proper_part} {food_part}".lower()
            entities.append(
                Entity(
                    name=full_name,
                    type="branded_product",
                    confidence=0.7,
                )
            )

    # Deduplicate (prefer higher confidence)
    seen_names = {}
    for entity in entities:
        if entity.name not in seen_names or entity.confidence > seen_names[entity.name].confidence:
            seen_names[entity.name] = entity

    return list(seen_names.values())


def is_specific_enough(query: str) -> bool:
    """
    Check if a query is specific enough to track.

    Args:
        query: Search query

    Returns:
        True if specific enough, False if too generic
    """
    entities = extract_entities(query)
    return len(entities) > 0


# Generic terms to avoid (if no entities found)
GENERIC_VETO = {
    "chocolate",
    "cheese",
    "chicken",
    "beef",
    "pork",
    "salmon",
    "recipe",
    "recipes",
    "food",
    "cooking",
    "dinner",
    "lunch",
    "breakfast",
    "snack",
    "dessert",
    "appetizer",
}

# Listicle patterns that indicate non-actionable content
LISTICLE_PATTERNS = [
    r"^\d{2,}\s+",  # Starts with 2+ digit number: "31 desserts" (but not "15 bean" which is 15-bean soup)
    r"\d+\s+(ways|recipes|ideas|tips|tricks|hacks|secrets|things|items)",
    r"\s+ideas$",  # Ends with "ideas": "breakfast ideas", "egg ideas"
    r"^best\s+",
    r"^top\s+\d+",
    r"^how to\s+",
    r"^why\s+",
    r"^what\s+",
    r"^has\s+\w+\s+(changed|actually)",  # "has X changed", "has X actually"
    r"^is\s+\w+\s+(still|really)",  # "is X still", "is X really"
    r"^should\s+you",
    r"the\s+best\s+",
    r"the\s+\d{2,}\s+",  # "the 31 recipes"
    r"you\s+need\s+to\s+(know|try|make)",
    r"we\s+(made|love|tested|tried|published)",
    r"our\s+editors",
    r"editors?\s+(picks?|choice|favorite|make)",
    r"guide\s+to",
    r"everything\s+you\s+need",
    r"that\s+(dont|doesn't|wont|won't)\s+taste",  # "desserts that don't taste like"
    r"(more|and)\s+recipes\s+we",  # "more recipes we made"
]


def should_skip_generic(query: str) -> bool:
    """
    Check if query is too generic or non-actionable.

    Filters out:
    - Single generic words
    - Listicle headlines ("10 ways to...", "best X to buy")
    - Content marketing phrases

    Args:
        query: Search query or article title

    Returns:
        True if should skip (not actionable for procurement)
    """
    query_lower = query.lower().strip()

    # If it's just one word and it's in the veto list
    words = query_lower.split()
    if len(words) == 1 and words[0] in GENERIC_VETO:
        return True

    # Check for listicle patterns (content marketing, not product signals)
    for pattern in LISTICLE_PATTERNS:
        if re.search(pattern, query_lower):
            return True

    return False
