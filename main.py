#!/usr/bin/env python3
"""
Job Hunter Agent: search jobs by role/location, extract key info, and show tailored summaries.
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import collect_preferences, load_preferences_from_yaml
from src.data_source import fetch_jobs
from src.normalize import normalize_response
from src.extract import extract_all
from src.summary import print_summaries, export_json, export_csv
from src.filtering import filter_jobs


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Job Hunter Agent: search jobs by role/location, extract key info, "
            "and show tailored summaries."
        )
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        metavar="PATH",
        help=(
            "YAML file with search preferences and filters. "
            "When provided, no interactive prompts are shown."
        ),
    )
    args = parser.parse_args()

    print("Job Hunter Agent")
    print("-" * 40)

    if args.config_file:
        try:
            prefs = load_preferences_from_yaml(args.config_file)
            print(f"Loaded preferences from '{args.config_file}'.")
        except (OSError, ValueError) as e:
            print(f"Error loading config file '{args.config_file}': {e}")
            raise SystemExit(1) from e
    else:
        prefs = collect_preferences()

    print(f"Searching: role='{prefs.role}', location='{prefs.location or 'any'}'")
    print()

    raw, timestamp, used_cache, api_called = fetch_jobs(prefs)
    jobs = normalize_response(raw)
    total_before = len(jobs)

    if not jobs:
        print("No jobs found.")
        extracted = []
        filtered = []
    else:
        print(f"Found {total_before} job(s) before filtering. Extracting key info...")
        print()
        extracted = extract_all(jobs)
        filtered = filter_jobs(extracted, prefs)

    total_after = len(filtered)

    if jobs and not filtered:
        print(
            "No jobs matched your filters. Try relaxing them (e.g. remove minimum "
            "salary or broaden location/position type)."
        )
    elif filtered:
        print_summaries(filtered)

    # Recap run parameters and high-level results after the summaries or messages.
    print()
    print("Run recap")
    print("-" * 40)
    print(f"Role: {prefs.role}")
    print(f"Location: {prefs.location or 'any'}")
    print(f"API called: {'yes' if api_called else 'no'}")
    print(f"Used cache: {'yes' if used_cache else 'no'}")
    print(f"Jobs before filtering: {total_before}")
    print(f"Jobs after filtering: {total_after}")

    if filtered:
        results_dir = Path("results")
        results_dir.mkdir(parents=True, exist_ok=True)
        export_json(filtered, results_dir / f"{timestamp}_jobs.json")
        export_csv(filtered, results_dir / f"{timestamp}_jobs.csv")
        print(
            f"Exported to results/{timestamp}_jobs.json and results/{timestamp}_jobs.csv"
        )


if __name__ == "__main__":
    main()
