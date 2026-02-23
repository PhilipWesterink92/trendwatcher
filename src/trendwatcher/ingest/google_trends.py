from __future__ import annotations

import random
import time
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
    # We'll do retries with exponential backoff and random delays.
    tries = 3
    last_err = None

    # Rotate between realistic user agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    ]

    for attempt in range(1, tries + 1):
        try:
            # Random delay before each attempt (2-5 seconds)
            if attempt > 1:
                delay = random.uniform(2.0, 5.0) * attempt  # Exponential backoff
                print(f"[dim]google_trends {cc}: waiting {delay:.1f}s before retry {attempt}...[/dim]")
                time.sleep(delay)
            else:
                # Small initial delay to be polite
                time.sleep(random.uniform(0.5, 1.5))

            # Rotate user agent
            ua = random.choice(user_agents)

            pytrends = TrendReq(
                hl=settings["hl"],
                tz=settings["tz"],
                timeout=(10, 25),  # (connect, read) timeouts
                retries=2,
                backoff_factor=0.5,
                requests_args={
                    "headers": {
                        "User-Agent": ua,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": settings["hl"].split("-")[0] + ",en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                    }
                }
            )

            df = pytrends.trending_searches(pn=pn)

            # Success! Add small delay before returning to avoid rapid-fire requests
            time.sleep(random.uniform(0.5, 1.0))

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

    # After retries, give up but don't crash the whole pipeline.
    print(f"[red]google_trends[/red] {cc} failed after {tries} tries: {last_err}")
    return []