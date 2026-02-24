"""Normalize API or mock response into a consistent list of job dicts."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def normalize_response(raw: dict) -> list[dict[str, Any]]:
    """
    Convert raw JSearch-style response into a list of job dicts with consistent keys.
    Skips malformed entries and logs them.
    """
    data = raw.get("data")
    if not isinstance(data, list):
        logger.warning("Response has no 'data' list; returning empty list.")
        return []
    jobs = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            logger.warning("Skipping non-dict item at index %s", i)
            continue
        job_id = item.get("job_id") or item.get("job_title") or str(i)
        if not item.get("job_title"):
            logger.warning("Skipping job at index %s (missing job_title): %s", i, job_id)
            continue
        jobs.append(_normalize_job(item))
    return jobs


def _normalize_job(item: dict) -> dict[str, Any]:
    """Ensure one job entry has standard keys (fill missing with None)."""
    return {
        "job_id": item.get("job_id"),
        "job_title": item.get("job_title"),
        "employer_name": item.get("employer_name"),
        "job_description": item.get("job_description") or "",
        "job_is_remote": item.get("job_is_remote"),
        "job_employment_type": item.get("job_employment_type"),
        "job_employment_types": item.get("job_employment_types") or [],
        "job_location": item.get("job_location"),
        "job_city": item.get("job_city"),
        "job_state": item.get("job_state"),
        "job_country": item.get("job_country"),
        "job_apply_link": item.get("job_apply_link"),
        "job_min_salary": item.get("job_min_salary"),
        "job_max_salary": item.get("job_max_salary"),
        "job_salary_period": item.get("job_salary_period"),
        "job_highlights": item.get("job_highlights") or {},
        "job_benefits": item.get("job_benefits"),
    }
