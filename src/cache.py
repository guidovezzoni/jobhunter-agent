"""Simple file-based cache for raw job search responses keyed by (role, location)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

CACHE_DIR = Path("debug/cache")
CACHE_TTL = timedelta(minutes=60)


@dataclass
class CacheEntry:
    role: str
    location: str
    timestamp: str  # ISO8601 string in UTC
    raw_response: dict[str, Any]


def _ensure_cache_dir() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def _key_to_path(role: str, location: str) -> Path:
    def slug(s: str) -> str:
        s = s.strip().lower() or "any"
        return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s)[:80]

    role_slug = slug(role)
    loc_slug = slug(location or "any")
    return _ensure_cache_dir() / f"{role_slug}__{loc_slug}.json"


def load_cache(role: str, location: str) -> Optional[dict[str, Any]]:
    """
    Return cached raw_response if present and not older than CACHE_TTL.
    Otherwise return None.
    """
    path = _key_to_path(role, location)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    ts_str = data.get("timestamp")
    if not ts_str:
        return None
    try:
        ts = datetime.fromisoformat(ts_str)
    except ValueError:
        return None

    now = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if now - ts > CACHE_TTL:
        return None

    raw = data.get("raw_response")
    if not isinstance(raw, dict):
        return None
    return raw


def save_cache(role: str, location: str, raw_response: dict[str, Any]) -> None:
    """Save raw_response to cache with current UTC timestamp."""
    entry = CacheEntry(
        role=role,
        location=location,
        timestamp=datetime.now(timezone.utc).isoformat(),
        raw_response=raw_response,
    )
    path = _key_to_path(role, location)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(entry), f, indent=2, ensure_ascii=False)

