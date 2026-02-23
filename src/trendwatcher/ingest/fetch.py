from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests

DEFAULT_UA = "trendwatcher/0.1 (+https://github.com/)"


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

    headers = {"User-Agent": DEFAULT_UA}

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

    time.sleep(min_delay_s)

    try:
        resp = requests.get(url, headers=headers, timeout=timeout_s)
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
