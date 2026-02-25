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
from src.filtering import filter_jobs


def main() -> None:
    print("Job Hunter Agent")
    print("-" * 40)
    prefs = collect_preferences()
    print(f"Searching: role='{prefs.role}', location='{prefs.location or 'any'}'")
    print()

    raw, timestamp = fetch_jobs(prefs)
    jobs = normalize_response(raw)
    if not jobs:
        print("No jobs found.")
        return
    print(f"Found {len(jobs)} job(s) before filtering. Extracting key info...")
    print()

    extracted = extract_all(jobs)
    filtered = filter_jobs(extracted, prefs)

    if not filtered:
        print("No jobs matched your filters. Try relaxing them (e.g. remove minimum salary or broaden location/position type).")
        return

    print(f"{len(filtered)} job(s) remain after filtering.")
    print()
    print_summaries(filtered)

    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    export_json(filtered, results_dir / f"{timestamp}_jobs.json")
    export_csv(filtered, results_dir / f"{timestamp}_jobs.csv")
    print(f"Exported to results/{timestamp}_jobs.json and results/{timestamp}_jobs.csv")


if __name__ == "__main__":
    main()
