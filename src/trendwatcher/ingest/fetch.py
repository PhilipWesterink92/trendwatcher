from __future__ import annotations

import hashlib
import random
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests

# Realistic browser user agents (rotate to avoid detection)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]


def _safe_filename(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def fetch_url(
    url: str,
    *,
    source_id: Optional[str] = None,
    country: Optional[str] = None,
    cache_dir: str = "data/cache",
    timeout_s: int = 20,
    min_delay_s: float = 0.5,
) -> Dict[str, Any]:
    """
    Fetch a URL with basic caching using ETag/Last-Modified when possible.

    Returns a JSON-serializable dict (NOT a dataclass) so the CLI can write JSONL safely.
    """
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    key = _safe_filename(url)
    meta_path = Path(cache_dir) / f"{key}.meta"
    body_path = Path(cache_dir) / f"{key}.txt"

    # Realistic browser headers to avoid 403 blocks
    user_agent = random.choice(USER_AGENTS)
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,nl;q=0.8,de;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    if meta_path.exists():
        meta_lines = meta_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        meta_map = {}
        for line in meta_lines:
            if ":" in line:
                k, v = line.split(":", 1)
                meta_map[k.strip()] = v.strip()

        if "etag" in meta_map:
            headers["If-None-Match"] = meta_map["etag"]
        if "last_modified" in meta_map:
            headers["If-Modified-Since"] = meta_map["last_modified"]

    # Random delay (1-3 seconds) to avoid rate limiting
    delay = random.uniform(1.0, 3.0) if min_delay_s > 0 else min_delay_s
    time.sleep(delay)

    try:
        # Add referer from same domain to look more legitimate
        from urllib.parse import urlparse
        parsed = urlparse(url)
        headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"

        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout_s,
            allow_redirects=True,
            verify=True,
        )
    except Exception as e:
        return {
            "type": "competitor_new",
            "source_id": source_id,
            "country": country,
            "url": url,
            "status_code": 0,
            "from_cache": False,
            "text_len": 0,
            "error": str(e),
            "text": "",
        }

    if resp.status_code == 304 and body_path.exists():
        text = body_path.read_text(encoding="utf-8", errors="ignore")
        return {
            "type": "competitor_new",
            "source_id": source_id,
            "country": country,
            "url": url,
            "status_code": 304,
            "from_cache": True,
            "etag": None,
            "last_modified": None,
            "text_len": len(text),
            "text": text,
        }

    text = resp.text or ""
    body_path.write_text(text, encoding="utf-8", errors="ignore")

    etag = resp.headers.get("ETag")
    last_modified = resp.headers.get("Last-Modified")

    meta_out = []
    if etag:
        meta_out.append(f"etag:{etag}")
    if last_modified:
        meta_out.append(f"last_modified:{last_modified}")
    meta_path.write_text("\n".join(meta_out), encoding="utf-8")

    return {
        "type": "competitor_new",
        "source_id": source_id,
        "country": country,
        "url": url,
        "status_code": resp.status_code,
        "from_cache": False,
        "etag": etag,
        "last_modified": last_modified,
        "text_len": len(text),
        "text": text,
    }
