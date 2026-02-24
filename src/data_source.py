"""Job data source: JSearch RapidAPI or mock file. Saves raw response to debug."""

import ast
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from src.config import SearchPreferences

load_dotenv()

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"
MOCK_PATH = Path("docs/RapidAPIResponse.txt")
DEBUG_DIR = Path("debug/api-response")


def _ensure_debug_dir() -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    return DEBUG_DIR


def get_timestamp() -> str:
    """Return timestamp string (YYYYMMDD_HHMMSS) for correlating debug and result files."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _save_raw_response(raw: str | dict, path: Path, timestamp: str) -> None:
    _ensure_debug_dir()
    filepath = path / f"{timestamp}_response.json"
    with open(filepath, "w", encoding="utf-8") as f:
        if isinstance(raw, dict):
            json.dump(raw, f, indent=2, ensure_ascii=False)
        else:
            f.write(raw)
    return None


def _parse_mock_content(content: str) -> Any:
    """Parse Python-style or JSON mock file (single quotes, None, trailing commas)."""
    content = content.strip()
    # Try JSON first (double quotes, no trailing commas)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    # Preprocess for ast.literal_eval: remove trailing commas before ] or }
    content = re.sub(r",\s*]", "]", content)
    content = re.sub(r",\s*}", "}", content)
    try:
        return ast.literal_eval(content)
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Could not parse mock file as JSON or Python literal: {e}") from e


def _fetch_jsearch(api_key: str, prefs: SearchPreferences) -> dict:
    """Call JSearch API with role and optional location."""
    params = {
        "query": prefs.role,
        "page": 1,
        "num_pages": 1,
    }
    if prefs.location:
        params["location"] = prefs.location
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    resp = requests.get(JSEARCH_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _load_mock() -> dict:
    """Load and parse mock response from docs/RapidAPIResponse.txt."""
    path = Path(MOCK_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Mock file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return _parse_mock_content(content)


def fetch_jobs(prefs: SearchPreferences) -> tuple[dict, str]:
    """
    Fetch job data from JSearch API (if RAPID_API_KEY set) or mock file.
    Saves raw response under debug/api-response with a timestamped filename.
    Returns (raw API response dict, timestamp) for correlating with result exports.
    Raises SystemExit (or callers should exit) when no source is available.
    """
    api_key = os.environ.get("RAPID_API_KEY", "").strip()
    raw: dict
    timestamp = get_timestamp()

    if api_key:
        raw = _fetch_jsearch(api_key, prefs)
    else:
        try:
            raw = _load_mock()
        except FileNotFoundError as e:
            print(
                "Warning: RAPID_API_KEY is not set in .env and mock file "
                f"docs/RapidAPIResponse.txt is not present. {e}"
            )
            raise SystemExit(1) from e
        except ValueError as e:
            print(f"Warning: Could not parse mock file: {e}")
            raise SystemExit(1) from e

    _save_raw_response(raw, _ensure_debug_dir(), timestamp)
    return raw, timestamp
