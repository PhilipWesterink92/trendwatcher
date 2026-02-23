from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from pytrends.request import TrendReq
from rich import print


# pytrends expects "pn" slugs (NOT country codes).
PN_BY_COUNTRY: Dict[str, str] = {
    "NL": "netherlands",
    "DE": "germany",
    "FR": "france",
    "US": "united_states",
    "GB": "united_kingdom",
    "KR": "south_korea",
    "JP": "japan",
    "AU": "australia",
    "CA": "canada",
    "SG": "singapore",
}

# UI language and timezone offset minutes (roughly fine for our use)
SETTINGS_BY_COUNTRY: Dict[str, Dict] = {
    "NL": {"hl": "nl-NL", "tz": 60},
    "DE": {"hl": "de-DE", "tz": 60},
    "FR": {"hl": "fr-FR", "tz": 60},
    "US": {"hl": "en-US", "tz": -300},
    "GB": {"hl": "en-GB", "tz": 0},
    "KR": {"hl": "ko-KR", "tz": 540},
    "JP": {"hl": "ja-JP", "tz": 540},
    "AU": {"hl": "en-AU", "tz": 600},
    "CA": {"hl": "en-CA", "tz": -300},
    "SG": {"hl": "en-SG", "tz": 480},
}


def fetch_rising_searches(country_code: str) -> List[Dict]:
    """
    Returns a list of dict rows like:
    {
      "type": "google_trends_rising",
      "country": "NL",
      "query": "...",
      "score": 100,
      "seed": "trending_searches",
      "fetched_at": "..."
    }
    """
    cc = (country_code or "").upper().strip()
    pn = PN_BY_COUNTRY.get(cc)

    if not pn:
        print(f"[yellow]google_trends[/yellow] unknown country_code={country_code!r} (skipping)")
        return []

    settings = SETTINGS_BY_COUNTRY.get(cc, {"hl": "en-US", "tz": 360})

    # TrendReq can be flaky (Google blocks/rate limits sometimes).
    # We'll do a couple tries and *log the error* so you can see what's going on.
    tries = 3
    last_err = None

    for attempt in range(1, tries + 1):
        try:
            pytrends = TrendReq(
                hl=settings["hl"],
                tz=settings["tz"],
                # Keep it simple; no proxies, no fancy headers.
                # If Google rate-limits, we’ll see it in the error log now.
            )

            df = pytrends.trending_searches(pn=pn)

            now = datetime.now(timezone.utc).isoformat()
            out: List[Dict] = []

            # df is typically 1 column of strings
            for _, row in df.iterrows():
                query = str(row[0]).strip()
                if not query:
                    continue

                out.append(
                    {
                        "type": "google_trends_rising",
                        "country": cc,
                        "query": query,
                        "score": 100,  # trending_searches has no breakout score
                        "seed": "trending_searches",
                        "fetched_at": now,
                    }
                )

            return out

        except Exception as e:
            last_err = e
            print(
                f"[yellow]google_trends[/yellow] {cc} attempt {attempt}/{tries} failed: {type(e).__name__}: {e}"
            )

    # After retries, give up but don’t crash the whole pipeline.
    print(f"[red]google_trends[/red] {cc} failed after {tries} tries: {last_err}")
    return []