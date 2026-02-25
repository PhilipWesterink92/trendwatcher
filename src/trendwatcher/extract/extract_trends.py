from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from rapidfuzz import fuzz
from rapidfuzz.process import extract as rf_extract

from .entity_extractor import extract_entities, should_skip_generic


DOCS_IN = Path("data/raw/docs.jsonl")
TRENDS_OUT = Path("data/processed/trends.json")


# -------------------------
# CONFIG / CONSTANTS
# -------------------------

# Markets that tend to lead food trends
LEAD_MARKETS = {"US", "GB", "KR", "JP"}

# Picnic core markets we care about catching early
TARGET_MARKETS = {"NL", "DE", "FR"}

# Words that generally don't help clustering (not a hard veto on their own)
SOFT_STOPWORDS = {
    "near", "me", "best", "easy", "simple",
    "healthy", "healthier", "calories", "kcal",
    "wat", "wat is", "was ist", "c'est", "comment", "pourquoi",
}

# Food-ish hints (signals; not necessarily required if other strong signals exist)
FOOD_HINTS = {
    # proteins / dairy
    "chicken", "beef", "pork", "salmon", "tuna", "shrimp", "egg", "eggs",
    "tofu", "yoghurt", "yogurt", "cheese", "milk", "butter", "skyr", "kefir",
    "tempeh", "seitan", "halloumi", "feta", "mozzarella", "parmesan",

    # plant-based / alternative proteins (trending)
    "vegan", "plantbased", "plant-based", "veggie", "vegetarian",
    "jackfruit", "chickpea", "lentil", "lentils", "bean", "beans",
    "oat milk", "oatmilk", "almond milk", "soy milk", "coconut milk",

    # carbs & staples
    "bread", "rice", "pasta", "noodle", "noodles", "potato", "potatoes",
    "wrap", "tortilla", "pizza", "burger", "oats", "granola",
    "quinoa", "bulgur", "couscous", "farro", "buckwheat", "soba",

    # produce
    "avocado", "tomato", "tomatoes", "onion", "onions", "garlic",
    "banana", "bananas", "apple", "apples", "spinach", "broccoli", "lemon",
    "kale", "arugula", "cauliflower", "zucchini", "mushroom", "mushrooms",
    "edamame", "bok choy", "ginger", "turmeric", "cilantro", "basil",

    # dishes / cuisines
    "soup", "salad", "curry", "stew", "taco", "ramen", "risotto",
    "lasagna", "lasagne", "paella", "dumpling", "dumplings",
    "poke", "bibimbap", "pad thai", "pho", "bao", "gyoza",
    "shakshuka", "falafel", "bowl", "bowls",

    # fermented & probiotic (trending)
    "kimchi", "kombucha", "sauerkraut", "pickled", "fermented",
    "miso", "tempeh", "kefir", "sourdough",

    # asian ingredients (trending)
    "miso", "matcha", "kimchi", "gochujang", "tahini", "hummus",
    "sriracha", "hoisin", "sesame", "wasabi", "nori", "seaweed",
    "panko", "mirin", "dashi", "yuzu", "shiso",

    # middle eastern / mediterranean (trending)
    "tahini", "za'atar", "sumac", "harissa", "dukkah", "labneh",
    "halloumi", "tzatziki", "hummus", "falafel",

    # health / superfood trends
    "protein", "collagen", "chia", "acai", "spirulina", "moringa",
    "turmeric", "ginger", "hemp", "flax", "nutritional yeast",
    "bone broth", "ghee", "mct", "adaptogens",

    # diet trends
    "keto", "paleo", "low carb", "gluten free", "gluten-free",
    "dairy free", "dairy-free", "sugar free", "organic",

    # form factors
    "sauce", "broth", "paste", "powder", "mix", "dressing", "marinade", "dip",
    "spread", "butter", "oil", "vinegar", "seasoning", "spice",

    # cooking methods (signals intent)
    "roasted", "grilled", "baked", "fried", "steamed", "sauteed",
    "slow cooker", "instant pot", "air fryer", "sous vide",

    # generic food signals (recipes are useful!)
    "recipe", "recipes", "recept", "recepten", "rezept", "rezepte", "recette", "recettes",
    "meal prep", "snack", "snacks", "appetizer", "dessert",
}

# Non-food category veto terms (small, stable; avoids "pistachio" cosmetics traps)
NONFOOD_VETO = {
    # cosmetics / beauty
    "catrice", "maybelline", "loreal", "l'oréal", "nyx", "sephora",
    "mascara", "lipstick", "eyeshadow", "foundation", "concealer",
    "skincare", "serum", "moisturizer", "cleanser",

    # luxury watches (avoid "oyster" = food false positive)
    "rolex", "oyster perpetual", "submariner", "datejust",

    # fashion / apparel
    "nike", "adidas", "zara", "h&m", "uniqlo",
    "sneakers", "shoes", "jacket", "jeans", "dress",

    # electronics
    "iphone", "samsung", "galaxy", "pixel", "macbook",
    "laptop", "tablet", "headphones", "airpods",

    # health (non-food)
    "discharge", "infection", "symptom", "medication",
    "pharmacy", "apotheek", "apotheke", "pharmacie",
}

# Local/venue intent: pattern-based (no city lists)
LOCAL_INTENT_PATTERNS = [
    r"\bnear me\b",
    r"\bin my area\b",
    r"\bopen now\b|\bopening hours\b|\bopeningstijden\b|\bhoraires\b|\böffnungszeiten\b",
    r"\bmenu\b|\bkarte\b|\bcarte\b",
    r"\bdelivery\b|\btakeaway\b|\bdeliveroo\b|\bubereats\b|\bjust eat\b|\bthuisbezorgd\b",
    r"\brestaurant\b|\brestaurants\b|\bresto\b|\bbar\b|\bbistro\b",
    r"\breview(s)?\b|\brezension(en)?\b|\bavis\b",
    # "best X in/near/around <place>" in multiple languages
    r"\b(best|top|good|goede|beste|meilleur|meilleurs|besten)\b.*\b(in|near|around|bei|à|en)\b",
    # Queries ending in "in <place>" (captures NYC, München, Amsterdam, etc.)
    r"\b(in|near|around|bei|à|en)\s+[a-zàâçéèêëîïôùûüÿñæœ\-\s]{2,}$",
]
LOCAL_INTENT_RE = re.compile("|".join(f"(?:{p})" for p in LOCAL_INTENT_PATTERNS), re.IGNORECASE)

# Recipe intent: allowed (we keep recipes), but recipes combined with local intent should be rejected
RECIPE_RE = re.compile(r"\b(recipe|recipes|recept|recepten|rezept|rezepte|recette|recettes)\b", re.IGNORECASE)


# -------------------------
# HELPERS
# -------------------------

def normalize(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^\w\s\-àâçéèêëîïôùûüÿñæœ]", "", t, flags=re.UNICODE)
    t = t.strip("- ").strip()
    return t


def food_intent_score(q: str) -> int:
    """
    Small scoring model:
    +2 if contains recipe keyword (we keep these)
    +2 if contains food hint
    +1 if contains typical pantry/form factor terms
    -3 if local/venue intent is detected (restaurant / "best in <place>")
    -3 if non-food veto detected
    """
    score = 0
    ql = q.lower()

    if NONFOOD_VETO and any(v in ql for v in NONFOOD_VETO):
        score -= 3

    if LOCAL_INTENT_RE.search(ql):
        score -= 3

    if RECIPE_RE.search(ql):
        score += 2

    if any(h in ql for h in FOOD_HINTS):
        score += 2

    # extra weak positives that help even when FOOD_HINTS misses
    pantry = ("sauce", "paste", "powder", "mix", "broth", "marinade", "dressing", "dip")
    if any(p in ql for p in pantry):
        score += 1

    return score


def is_foody(query: str) -> bool:
    if len(query) < 3:
        return False

    q = query.lower().strip()

    # hard veto: local/restaurant intent should not be in the assortment watchlist
    # (recipes are allowed, but not "best ramen in <city>" style)
    if LOCAL_INTENT_RE.search(q):
        return False

    # hard veto: obvious non-food category
    if any(v in q for v in NONFOOD_VETO):
        return False

    # keep if intent score is decent
    return food_intent_score(q) >= 2


@dataclass
class TrendCluster:
    label: str
    queries: List[dict]
    countries: List[str]
    seeds: List[str]
    score: float


def load_trend_rows() -> List[dict]:
    if not DOCS_IN.exists():
        return []
    rows = []
    # Accept multiple source types
    valid_types = {
        "google_trends_rising",
        "reddit_trending",
        "food_blog_post",
        "menu_dish",  # Phase 2: Menu/restaurant tracking
    }
    for line in DOCS_IN.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("type") in valid_types:
            rows.append(obj)
    return rows


def cluster_queries(rows: List[dict], threshold: int = 88) -> List[TrendCluster]:
    """
    Entity-aware clustering:
    - Extract specific entities from queries
    - Group by fuzzy match to existing labels
    - Skip overly generic queries
    """
    agg: Dict[str, List[dict]] = defaultdict(list)
    entity_mapping: Dict[str, str] = {}  # query -> entity name

    for r in rows:
        q = normalize(str(r.get("query", "")))
        if not q:
            continue

        # Skip overly generic single-word queries
        if should_skip_generic(q):
            continue

        # Extract entities (specific products/ingredients)
        entities = extract_entities(q)

        if entities:
            # Use the highest-confidence entity as the label
            best_entity = max(entities, key=lambda e: e.confidence)
            entity_name = normalize(best_entity.name)

            # Store entity metadata in row
            r["entity_name"] = best_entity.name
            r["entity_type"] = best_entity.type
            r["entity_confidence"] = best_entity.confidence

            agg[entity_name].append(r)
            entity_mapping[q] = entity_name
        else:
            # Fallback: use normalized query (with soft stopword removal)
            for w in SOFT_STOPWORDS:
                q = q.replace(f" {w} ", " ")

            q = normalize(q)

            if not q or not is_foody(q):
                continue

            agg[q].append(r)

    unique = list(agg.keys())
    clusters: List[Tuple[str, List[str]]] = []

    for q in unique:
        if not clusters:
            clusters.append((q, [q]))
            continue

        labels = [c[0] for c in clusters]
        best = rf_extract(q, labels, scorer=fuzz.token_set_ratio, limit=1)

        if best and best[0][1] >= threshold:
            best_label = best[0][0]
            new_clusters = []
            for label, members in clusters:
                if label == best_label:
                    members.append(q)
                new_clusters.append((label, members))
            clusters = new_clusters
        else:
            clusters.append((q, [q]))

    out: List[TrendCluster] = []
    for label, members in clusters:
        all_rows = []
        countries = set()
        seeds = set()
        scores = []

        for m in members:
            rs = agg[m]
            all_rows.extend(rs)
            for r in rs:
                countries.add(r.get("country"))
                seeds.add(r.get("seed"))
                v = r.get("score")

                if isinstance(v, str) and v.lower() == "breakout":
                    scores.append(150)
                else:
                    try:
                        scores.append(float(v))
                    except Exception:
                        pass

        base = (sum(scores) / max(1, len(scores))) if scores else 0.0
        breadth = (1 + 0.25 * max(0, len(seeds) - 1)) * (
            1 + 0.5 * max(0, len(countries) - 1)
        )
        final_score = base * breadth

        out.append(
            TrendCluster(
                label=label,
                queries=all_rows,
                countries=sorted([c for c in countries if c]),
                seeds=sorted([s for s in seeds if s]),
                score=final_score,
            )
        )

    out.sort(key=lambda x: x.score, reverse=True)
    return out


def export_clusters(clusters: List[TrendCluster], top_n: int = 50):
    from trendwatcher.score import TrendScorer
    from trendwatcher.store import HistoryStore

    TRENDS_OUT.parent.mkdir(parents=True, exist_ok=True)

    payload = []
    scorer = TrendScorer()

    # Load historical data for velocity scoring
    store = HistoryStore()
    history_map = store.load_all_histories()

    for c in clusters:
        q_counts = Counter([normalize(r.get("query", "")) for r in c.queries])
        examples = [q for q, _ in q_counts.most_common(8)]

        # first_seen per country
        first_seen = {}
        for r in c.queries:
            cc = r.get("country")
            ts = r.get("fetched_at")
            if not cc or not ts:
                continue
            if cc not in first_seen or ts < first_seen[cc]:
                first_seen[cc] = ts

        country_order = [k for k, _ in sorted(first_seen.items(), key=lambda kv: kv[1])]

        # lead vs target
        lead_first = None
        target_first = None

        for cc, ts in first_seen.items():
            if cc in LEAD_MARKETS:
                if lead_first is None or ts < lead_first:
                    lead_first = ts
            if cc in TARGET_MARKETS:
                if target_first is None or ts < target_first:
                    target_first = ts

        lead_lag = {
            "lead_first": lead_first,
            "target_first": target_first,
            "has_lead": lead_first is not None,
            "has_target": target_first is not None,
        }

        # Collect entity metadata (if available)
        entity_types = [r.get("entity_type") for r in c.queries if r.get("entity_type")]
        entity_type = Counter(entity_types).most_common(1)[0][0] if entity_types else None

        entity_confidences = [r.get("entity_confidence") for r in c.queries if r.get("entity_confidence")]
        avg_confidence = sum(entity_confidences) / len(entity_confidences) if entity_confidences else None

        trend_dict = {
            "trend": c.label,
            "countries": c.countries,
            "country_order": country_order,
            "first_seen": first_seen,
            "lead_lag": lead_lag,
            "seed_count": len(c.seeds),
            "seeds": c.seeds[:10],
            "examples": examples,
            "raw_count": len(c.queries),
            "entity_type": entity_type,
            "entity_confidence": round(avg_confidence, 2) if avg_confidence else None,
        }

        payload.append(trend_dict)

    # Apply 5D scoring to all trends with history for velocity
    scored_payload = scorer.score_batch(payload, history_map=history_map)

    # Take top_n after scoring
    scored_payload = scored_payload[:top_n]

    TRENDS_OUT.write_text(
        json.dumps(scored_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_extract():
    rows = load_trend_rows()
    clusters = cluster_queries(rows)
    export_clusters(clusters)
    return len(rows), len(clusters)


if __name__ == "__main__":
    n_rows, n_clusters = run_extract()
    print(f"extract complete rows={n_rows} clusters={n_clusters} out={TRENDS_OUT}")
