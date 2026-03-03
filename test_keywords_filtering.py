"""Tests for keyword-based filtering and YAML parsing."""

from pathlib import Path

from src.config import SearchPreferences, load_preferences_from_yaml
from src.filtering import filter_jobs


def _make_prefs_with_keywords(keywords):
    return SearchPreferences(
        role="Test",
        location="",
        date_posted="today",
        location_types=[],
        position_types=[],
        minimum_salary=None,
        industry_filter=None,
        language_filter="en",
        output=[],
        europe_countries=[],
        keywords=keywords,
    )


def test_filter_jobs_no_keywords_does_not_filter():
    prefs = _make_prefs_with_keywords([])
    jobs = [
        {"requirements": "Android and Kotlin experience", "tech_stack": ["kotlin", "jetpack"]},
        {"requirements": "iOS Swift developer"},
    ]

    result = filter_jobs(jobs, prefs)
    assert result == jobs


def test_filter_jobs_with_keywords_matches_on_requirements_and_tech_stack():
    prefs = _make_prefs_with_keywords(["android", "kotlin"])
    jobs = [
        {"requirements": "Android and Kotlin experience", "tech_stack": []},
        {"requirements": "Something else", "tech_stack": ["kotlin"]},
        {"requirements": "No match here", "tech_stack": []},
    ]

    result = filter_jobs(jobs, prefs)
    assert len(result) == 2
    assert jobs[0] in result
    assert jobs[1] in result


def test_filter_jobs_with_keywords_is_case_insensitive():
    prefs = _make_prefs_with_keywords(["AnDrOiD"])
    jobs = [
        {"requirements": "android developer"},
    ]

    result = filter_jobs(jobs, prefs)
    assert len(result) == 1
    assert result[0] == jobs[0]


def test_filter_jobs_rejects_when_no_fields_and_keywords_present():
    prefs = _make_prefs_with_keywords(["android"])
    jobs = [
        {},  # no searchable fields
    ]

    result = filter_jobs(jobs, prefs)
    assert result == []


def test_load_preferences_from_yaml_parses_keywords_list_and_string(tmp_path):
    yaml_content = """
role: "Android Developer"
location: ""
keywords:
  - "android"
  - " kotlin "
"""
    path = tmp_path / "config_keywords_list.yaml"
    path.write_text(yaml_content, encoding="utf-8")

    prefs = load_preferences_from_yaml(path)
    assert prefs.keywords == ["android", " kotlin "].copy() or ["android", "kotlin"]

    yaml_content_single = """
role: "Android Developer"
location: ""
keywords: "android"
"""
    path_single = tmp_path / "config_keywords_single.yaml"
    path_single.write_text(yaml_content_single, encoding="utf-8")

    prefs_single = load_preferences_from_yaml(path_single)
    assert prefs_single.keywords == ["android"]

