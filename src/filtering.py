"""Filtering layer for extracted job data based on user preferences."""

from typing import Any

from src.config import SearchPreferences


def filter_jobs(extracted_jobs: list[dict[str, Any]], prefs: SearchPreferences) -> list[dict[str, Any]]:
    """
    Apply post-fetch filters to the extracted jobs according to user preferences.
    If a given filter is effectively \"empty\", it is not applied.
    """
    filtered = []
    for job in extracted_jobs:
        if not _passes_location_type(job, prefs):
            continue
        if not _passes_position_type(job, prefs):
            continue
        if not _passes_minimum_salary(job, prefs):
            continue
        if not _passes_industry(job, prefs):
            continue
        if not _passes_language(job, prefs):
            continue
        filtered.append(job)
    return filtered


def _passes_location_type(job: dict[str, Any], prefs: SearchPreferences) -> bool:
    """Location type filter: if none selected, accept all."""
    if not prefs.location_types:
        return True
    loc_type = (job.get("location_type") or "").lower()
    return loc_type in {t.lower() for t in prefs.location_types}


def _passes_position_type(job: dict[str, Any], prefs: SearchPreferences) -> bool:
    """Position type filter: if none selected, accept all."""
    if not prefs.position_types:
        return True
    pos_type = (job.get("position_type") or "").lower()
    return pos_type in {t.lower() for t in prefs.position_types}


def _passes_minimum_salary(job: dict[str, Any], prefs: SearchPreferences) -> bool:
    """
    Minimum salary filter:
    - If no minimum is set, accept all.
    - If set, accept only jobs with a defined minimum_salary >= given minimum.
    """
    if prefs.minimum_salary is None:
        return True
    job_min = job.get("minimum_salary")
    if job_min is None:
        return False
    try:
        return int(job_min) >= int(prefs.minimum_salary)
    except (TypeError, ValueError):
        return False


def _passes_industry(job: dict[str, Any], prefs: SearchPreferences) -> bool:
    """Industry filter: empty / not defined means no filter."""
    if not prefs.industry_filter:
        return True
    industry = (job.get("industry") or "").lower()
    if not industry:
        return False
    return prefs.industry_filter.lower() in industry


def _passes_language(job: dict[str, Any], prefs: SearchPreferences) -> bool:
    """
    Job spec language filter:
    - Default is \"en\" (English only)
    - If set to \"any\", accept all.
    - Otherwise, check that job_spec_language starts with the provided code (case-insensitive).
    """
    lang_pref = (prefs.language_filter or "").lower()
    if not lang_pref:
        # Treat missing as default English-only
        lang_pref = "en"
    if lang_pref == "any":
        return True
    job_lang = (job.get("job_spec_language") or "").lower()
    if not job_lang:
        return False
    return job_lang.startswith(lang_pref)

