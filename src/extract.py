"""Extract key job fields from normalized job dicts."""

import re
from typing import Any

from langdetect import detect, LangDetectException

# Keywords to infer location type from description
REMOTE_PATTERNS = [
    r"\bremote\b",
    r"work from home",
    r"fully remote",
    r"remote within",
    r"remote opportunity",
    r"100% remote",
]
HYBRID_PATTERNS = [
    r"\bhybrid\b",
    r"hybrid (work|model|way)",
    r"in[- ]?office.*virtual",
    r"primarily in office.*virtual",
    r"flexible.*remote",
]
ONSITE_PATTERNS = [
    r"on[- ]?site",
    r"in[- ]?person",
    r"office location",
    r"locat(e|ion) (requirement|to)",
    r"must be (local|in)",
]

# Position type from API and description
CONTRACT_PATTERNS = [
    r"\bcontract\b",
    r"contractor",
    r"\bcontract:\s*\d+",
    r"12 months",
    r"6 months",
]
FREELANCE_PATTERNS = [r"\bfreelance\b", r"freelancer", r"self[- ]?employed"]
PERMANENT_PATTERNS = [
    r"full[- ]?time",
    r"permanent",
    r"employee",
    r"FULLTIME",
]

# Tech keywords (curated list for Android/software roles)
TECH_KEYWORDS = [
    "Kotlin", "Java", "Android", "Android SDK", "Android Studio", "Gradle",
    "Jetpack", "Compose", "MVVM", "MVI", "Room", "SQLite", "Retrofit",
    "REST", "GraphQL", "JSON", "Coroutines", "RxJava", "Dagger", "Hilt",
    "JUnit", "Espresso", "Mockito", "CI/CD", "Git", "GitHub", "GitLab",
    "Azure", "AWS", "GCP", "Firebase", "NDK", "Python", "C++", "Swift",
    "Objective-C", "React", "Node", "TypeScript", "JavaScript", "RESTful",
]


def _location_type(job: dict[str, Any]) -> str:
    """Infer on-site / hybrid / remote / not defined."""
    desc = (job.get("job_description") or "").lower()
    title = (job.get("job_title") or "").lower()
    combined = f"{title} {desc}"
    is_remote_flag = job.get("job_is_remote") is True

    if is_remote_flag:
        return "remote"
    for p in REMOTE_PATTERNS:
        if re.search(p, combined, re.I):
            return "remote"
    for p in HYBRID_PATTERNS:
        if re.search(p, combined, re.I):
            return "hybrid"
    for p in ONSITE_PATTERNS:
        if re.search(p, combined, re.I):
            return "on-site"
    if job.get("job_location") and not is_remote_flag:
        return "on-site"  # has location and not remote => assume on-site
    return "not defined"


def _position_type(job: dict[str, Any]) -> str:
    """Infer permanent / contract / freelance / not defined."""
    emp_type = (job.get("job_employment_type") or "").lower()
    types_list = [t.upper() for t in (job.get("job_employment_types") or [])]
    desc = (job.get("job_description") or "").lower()
    title = (job.get("job_title") or "").lower()
    combined = f"{title} {desc} {emp_type} {' '.join(types_list)}"

    if "CONTRACTOR" in types_list or any(re.search(p, combined, re.I) for p in CONTRACT_PATTERNS):
        return "contract"
    for p in FREELANCE_PATTERNS:
        if re.search(p, combined, re.I):
            return "freelance"
    if "FULLTIME" in types_list or "PARTTIME" in types_list or any(
        re.search(p, combined, re.I) for p in PERMANENT_PATTERNS
    ):
        return "permanent"
    return "not defined"


def _min_salary(job: dict[str, Any]) -> int | None:
    """Minimum salary if provided."""
    return job.get("job_min_salary")


def _industry(job: dict[str, Any]) -> str | None:
    """Industry if inferable from employer/description (simple heuristic)."""
    emp = (job.get("employer_name") or "").lower()
    desc = (job.get("job_description") or "").lower()[:2000]
    text = f"{emp} {desc}"
    if any(x in text for x in ("fintech", "finance", "bank", "payment", "insurance")):
        return "Finance / Insurance"
    if any(x in text for x in ("retail", "ecommerce", "e-commerce")):
        return "Retail"
    if any(x in text for x in ("defense", "security clearance", "ts/sci", "government")):
        return "Defense / Government"
    if any(x in text for x in ("health", "medical")):
        return "Healthcare"
    return None


def _job_spec_language(job: dict[str, Any]) -> str:
    """Primary language of the job ad (not required candidate language)."""
    desc = job.get("job_description") or ""
    if not desc.strip():
        return "not defined"
    try:
        return detect(desc[:5000])
    except LangDetectException:
        return "not defined"


def _tech_stack(job: dict[str, Any]) -> list[str]:
    """Extract mentioned technologies from description and highlights."""
    desc = job.get("job_description") or ""
    highlights = job.get("job_highlights") or {}
    quals = " ".join(highlights.get("Qualifications", []))
    resp = " ".join(highlights.get("Responsibilities", []))
    combined = f"{desc} {quals} {resp}"
    found = []
    for tech in TECH_KEYWORDS:
        if tech.lower() in combined.lower():
            found.append(tech)
    return list(dict.fromkeys(found))  # preserve order, no dupes


def _requirements(job: dict[str, Any]) -> list[str]:
    """Key requirements from job highlights or description."""
    highlights = job.get("job_highlights") or {}
    quals = list(highlights.get("Qualifications", []))
    if quals:
        return quals[:15]
    desc = job.get("job_description") or ""
    lines = [l.strip() for l in desc.split("\n") if l.strip() and len(l.strip()) > 20]
    requirement_keywords = ["required", "qualifications", "requirements", "must have", "experience"]
    out = []
    for line in lines[:50]:
        if any(k in line.lower() for k in requirement_keywords) or (
            line.endswith(".") and 30 < len(line) < 300
        ):
            out.append(line)
            if len(out) >= 15:
                break
    return out[:15]


def _job_link(job: dict[str, Any]) -> str | None:
    """Canonical apply/link URL."""
    return job.get("job_apply_link")


def extract_job_info(job: dict[str, Any]) -> dict[str, Any]:
    """Extract all required key fields from one normalized job dict."""
    return {
        "role": job.get("job_title"),
        "employer_name": job.get("employer_name"),
        "location": job.get("job_location"),
        "job_country": job.get("job_country"),
        "location_type": _location_type(job),
        "position_type": _position_type(job),
        "minimum_salary": _min_salary(job),
        "industry": _industry(job),
        "job_spec_language": _job_spec_language(job),
        "tech_stack": _tech_stack(job),
        "requirements": _requirements(job),
        "job_link": _job_link(job),
        # keep raw for summary
        "_raw": job,
    }


def extract_all(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract key info for each job."""
    return [extract_job_info(j) for j in jobs]
