"""User preferences for job search and post-fetch filtering."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Mapping, Optional

import yaml

DEFAULT_ROLE = "Android Developer"
DEFAULT_LOCATION = ""

LOCATION_TYPE_CHOICES = {"on-site", "hybrid", "remote"}
POSITION_TYPE_CHOICES = {"permanent", "contract", "freelance"}


@dataclass
class SearchPreferences:
    """User-provided search criteria and filters."""

    role: str
    location: str

    # Optional filters applied after fetching results
    location_types: List[str]
    position_types: List[str]
    minimum_salary: Optional[int]
    industry_filter: Optional[str]
    language_filter: str  # e.g. "en" or "any"


def _parse_multi_choice(raw: str, valid: set[str]) -> list[str]:
    """
    Parse a comma-separated list of choices, keeping only valid entries.
    Returns an empty list when the user leaves it blank or nothing valid is provided.
    """
    if not raw.strip():
        return []
    parts = [p.strip().lower() for p in raw.split(",")]
    selected = []
    for p in parts:
        if p in valid and p not in selected:
            selected.append(p)
    return selected


def _normalize_choice_list(value: Any, valid_choices: set[str]) -> list[str]:
    """
    Normalize a YAML-provided value into a list of valid lowercase strings.
    Accepts a single string or a sequence of strings; ignores invalid entries.
    """
    if value is None:
        return []
    if isinstance(value, str):
        candidates = [value]
    else:
        try:
            candidates = list(value)
        except TypeError:
            return []
    normalized: list[str] = []
    for item in candidates:
        if not isinstance(item, str):
            continue
        s = item.strip().lower()
        if s and s in valid_choices and s not in normalized:
            normalized.append(s)
    return normalized


def _coerce_minimum_salary(value: Any) -> Optional[int]:
    """Coerce YAML value into an integer minimum salary, or None."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return None
        try:
            return int(v)
        except ValueError:
            return None
    return None


def collect_preferences() -> SearchPreferences:
    """
    Prompt user for role/location (used for the API call and caching)
    and additional filters applied after fetching results.
    """
    # Core search parameters
    role_input = input(f"Role [{DEFAULT_ROLE}]: ").strip() or DEFAULT_ROLE
    location_input = input(
        f"Location (leave empty for any) [{DEFAULT_LOCATION}]: "
    ).strip()

    # Filters
    loc_types_raw = input(
        "Location types filter (comma-separated: on-site, hybrid, remote; "
        "leave empty for no filtering): "
    )
    location_types = _parse_multi_choice(loc_types_raw, LOCATION_TYPE_CHOICES)

    pos_types_raw = input(
        "Position types filter (comma-separated: permanent, contract, freelance; "
        "leave empty for no filtering): "
    )
    position_types = _parse_multi_choice(pos_types_raw, POSITION_TYPE_CHOICES)

    min_salary_raw = input(
        "Minimum salary filter (number, leave empty for no minimum): "
    ).strip()
    minimum_salary: Optional[int]
    if min_salary_raw:
        try:
            minimum_salary = int(min_salary_raw)
        except ValueError:
            minimum_salary = None
    else:
        minimum_salary = None

    industry_raw = input(
        "Industry filter (free text, leave empty for no filtering): "
    ).strip()
    industry_filter = industry_raw or None

    lang_raw = input(
        "Job spec language filter [en/any] (default en = English only): "
    ).strip().lower()
    if not lang_raw:
        language_filter = "en"
    elif lang_raw in {"en", "any"}:
        language_filter = lang_raw
    else:
        # Allow arbitrary language codes but default to lowercased value
        language_filter = lang_raw

    return SearchPreferences(
        role=role_input,
        location=location_input,
        location_types=location_types,
        position_types=position_types,
        minimum_salary=minimum_salary,
        industry_filter=industry_filter,
        language_filter=language_filter,
    )


def load_preferences_from_yaml(path: str | Path) -> SearchPreferences:
    """
    Load search preferences and filters from a YAML file.

    The YAML is expected to contain keys matching SearchPreferences fields, e.g.:

        role: "Android Developer"
        location: ""
        location_types: ["remote"]
        position_types: ["permanent"]
        minimum_salary: 60000
        industry_filter: "fintech"
        language_filter: "en"

    Missing keys fall back to the same defaults as interactive input.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, Mapping):
        raise ValueError("YAML config must define a mapping at the top level.")

    role = str(data.get("role") or DEFAULT_ROLE)
    location = str(data.get("location") or DEFAULT_LOCATION)

    location_types = _normalize_choice_list(
        data.get("location_types"), LOCATION_TYPE_CHOICES
    )
    position_types = _normalize_choice_list(
        data.get("position_types"), POSITION_TYPE_CHOICES
    )

    minimum_salary = _coerce_minimum_salary(data.get("minimum_salary"))

    industry_raw = data.get("industry_filter")
    if industry_raw is None:
        industry_filter: Optional[str] = None
    else:
        s = str(industry_raw).strip()
        industry_filter = s or None

    lang_raw = data.get("language_filter")
    if lang_raw is None or not str(lang_raw).strip():
        language_filter = "en"
    else:
        language_filter = str(lang_raw).strip().lower()

    return SearchPreferences(
        role=role,
        location=location,
        location_types=location_types,
        position_types=position_types,
        minimum_salary=minimum_salary,
        industry_filter=industry_filter,
        language_filter=language_filter,
    )
