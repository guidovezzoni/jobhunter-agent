#!/usr/bin/env python3
"""
Job Hunter Agent: search jobs by role/location, extract key info, and show tailored summaries.
"""

import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import collect_preferences
from src.data_source import fetch_jobs
from src.normalize import normalize_response
from src.extract import extract_all
from src.summary import print_summaries, export_json, export_csv


def main() -> None:
    print("Job Hunter Agent")
    print("-" * 40)
    prefs = collect_preferences()
    print(f"Searching: role='{prefs.role}', location='{prefs.location or 'any'}'")
    print()

    raw = fetch_jobs(prefs)
    jobs = normalize_response(raw)
    if not jobs:
        print("No jobs found.")
        return
    print(f"Found {len(jobs)} job(s). Extracting key info...")
    print()

    extracted = extract_all(jobs)
    print_summaries(extracted)

    export_prompt = input("Export results to JSON and CSV in debug/? [y/N]: ").strip().lower()
    if export_prompt == "y":
        base = Path("debug")
        base.mkdir(parents=True, exist_ok=True)
        export_json(extracted, base / "jobs_export.json")
        export_csv(extracted, base / "jobs_export.csv")
        print("Exported to debug/jobs_export.json and debug/jobs_export.csv")


if __name__ == "__main__":
    main()
