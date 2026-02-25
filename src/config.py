"""User preferences for job search and post-fetch filtering."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Mapping, Optional

import yaml

DEFAULT_ROLE = "Android Developer"
DEFAULT_LOCATION = ""
DEFAULT_DATE_POSTED = "today"

LOCATION_TYPE_CHOICES = {"on-site", "hybrid", "remote"}
POSITION_TYPE_CHOICES = {"permanent", "contract", "freelance"}
DATE_POSTED_CHOICES = {"today", "week", "month", "all"}

# Location strings that trigger multi-country European search mode.
EUROPE_LOCATION_TRIGGERS: frozenset[str] = frozenset(
    {"europe", "eu", "european economic area"}
)
# Default European country codes used when none are explicitly provided.
DEFAULT_EUROPE_COUNTRIES: list[str] = ["gb", "es", "pt"]


@dataclass
class SearchPreferences:
    """User-provided search criteria and filters."""

    role: str
    location: str
    date_posted: str  # API-level filter: today, week, month, all

    # Optional filters applied after fetching results
    location_types: List[str]
    position_types: List[str]
    minimum_salary: Optional[int]
    industry_filter: Optional[str]
    language_filter: str  # e.g. "en" or "any"

    # Non-empty when location is a Europe trigger; each entry is a 2-letter
    # ISO country code passed individually to the API (one call per country).
    europe_countries: List[str] = field(default_factory=list)


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
        "Location (leave empty for any, or enter 'europe'/'eu'/'european economic area' "
        f"for a multi-country European search) [{DEFAULT_LOCATION}]: "
    ).strip()

    # Multi-country Europe mode
    europe_countries: list[str] = []
    if location_input.lower() in EUROPE_LOCATION_TRIGGERS:
        default_codes = ",".join(DEFAULT_EUROPE_COUNTRIES)
        raw_countries = input(
            f"European country codes to search (comma-separated ISO codes) [{default_codes}]: "
        ).strip()
        if raw_countries:
            europe_countries = [c.strip().lower() for c in raw_countries.split(",") if c.strip()]
        else:
            europe_countries = list(DEFAULT_EUROPE_COUNTRIES)

    date_posted_raw = input(
        "Posting date filter [today/week/month/all] (default today = past 24 h): "
    ).strip().lower()
    date_posted = date_posted_raw if date_posted_raw in DATE_POSTED_CHOICES else DEFAULT_DATE_POSTED

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
        date_posted=date_posted,
        location_types=location_types,
        position_types=position_types,
        minimum_salary=minimum_salary,
        industry_filter=industry_filter,
        language_filter=language_filter,
        europe_countries=europe_countries,
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

    date_posted_raw = data.get("date_posted")
    if date_posted_raw is None or not str(date_posted_raw).strip():
        date_posted = DEFAULT_DATE_POSTED
    else:
        candidate = str(date_posted_raw).strip().lower()
        date_posted = candidate if candidate in DATE_POSTED_CHOICES else DEFAULT_DATE_POSTED

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

    # Europe multi-country: read explicit list or fall back to default when
    # location is a recognised Europe trigger.
    europe_countries_raw = data.get("europe_countries")
    if europe_countries_raw is not None:
        try:
            europe_countries = [str(c).strip().lower() for c in list(europe_countries_raw) if str(c).strip()]
        except TypeError:
            europe_countries = []
    elif location.lower() in EUROPE_LOCATION_TRIGGERS:
        europe_countries = list(DEFAULT_EUROPE_COUNTRIES)
    else:
        europe_countries = []

    return SearchPreferences(
        role=role,
        location=location,
        date_posted=date_posted,
        location_types=location_types,
        position_types=position_types,
        minimum_salary=minimum_salary,
        industry_filter=industry_filter,
        language_filter=language_filter,
        europe_countries=europe_countries,
    )
