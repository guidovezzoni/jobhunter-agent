#!/usr/bin/env python3
"""
Job Hunter Agent: search jobs by role/location, extract key info, and show tailored summaries.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

_DEFAULT_CONFIG = Path(__file__).resolve().parent / "config.yaml"

from src.config import (
    EUROPE_LOCATION_TRIGGERS,
    OUTPUT_CHOICES,
    collect_preferences,
    load_preferences_from_yaml,
)
from src.data_source import fetch_jobs
from src.normalize import normalize_response
from src.extract import extract_all
from src.summary import print_summaries, export_json, export_csv, export_html
from src.filtering import filter_jobs


def _slug(s: str) -> str:
    """Sanitise a string for use as a filename segment.

    Lowercases, replaces any character that is not alphanumeric or underscore
    with '_' (covers all chars forbidden on Linux/Windows: / \\ : * ? " < > |
    and control characters), collapses consecutive underscores, and strips
    leading/trailing underscores.
    """
    s = s.strip().lower() or "any"
    s = re.sub(r"[^\w]", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_") or "any"


def _open_in_system(path: Path) -> None:
    """
    Open a file with the OS-associated application (CSV/JSON launch).

    Best-effort only: failures are printed as warnings and do not abort the run.
    """
    try:
        resolved = path.resolve()
        if sys.platform.startswith("win"):
            os.startfile(str(resolved))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(resolved)], check=False)
        else:
            subprocess.run(["xdg-open", str(resolved)], check=False)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Warning: could not open '{path}' via the operating system: {exc}")


def _format_exported_paths(prefix: str, generated: Iterable[str]) -> str:
    """
    Build a human-readable export message listing only generated files.

    Example: "Exported to results/foo.json and results/foo.html"
    """
    paths = [f"results/{prefix}_jobs.{ext}" for ext in generated]
    if not paths:
        return ""
    if len(paths) == 1:
        return f"Exported to {paths[0]}"
    return f"Exported to {', '.join(paths[:-1])} and {paths[-1]}"


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
        yaml_defaults = None
        if _DEFAULT_CONFIG.exists():
            try:
                yaml_defaults = load_preferences_from_yaml(_DEFAULT_CONFIG)
            except (OSError, ValueError):
                pass
        prefs = collect_preferences(defaults=yaml_defaults)

    if prefs.location.lower() in EUROPE_LOCATION_TRIGGERS and not prefs.europe_countries:
        print(
            "Error: European search mode requires at least one country code. "
            "Add at least one entry to 'europe_countries' in config.yaml, "
            "or enter country codes at the prompt."
        )
        raise SystemExit(1)

    if not prefs.output:
        allowed = ", ".join(sorted(OUTPUT_CHOICES))
        print(
            "Error: output configuration is empty. Please set at least one value in the "
            "'output' field of your YAML config (allowed values: "
            f"{allowed})."
        )
        raise SystemExit(1)

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
        location_slug = "europe" if prefs.europe_countries else _slug(prefs.location or "any")
        prefix = f"{_slug(prefs.role)}-{location_slug}-{_slug(prefs.date_posted)}-{timestamp}"

        outputs = {mode.upper() for mode in prefs.output}
        want_json = "JSON" in outputs or "JSON_LAUNCH" in outputs
        want_csv = "CSV" in outputs or "CSV_LAUNCH" in outputs
        want_html = "HTML" in outputs or "HTML_LAUNCH" in outputs

        launch_json = "JSON_LAUNCH" in outputs
        launch_csv = "CSV_LAUNCH" in outputs
        launch_html = "HTML_LAUNCH" in outputs

        generated_exts: list[str] = []

        json_path = results_dir / f"{prefix}_jobs.json"
        csv_path = results_dir / f"{prefix}_jobs.csv"
        html_path = results_dir / f"{prefix}_jobs.html"

        if want_json:
            export_json(filtered, json_path)
            generated_exts.append("json")
        if want_csv:
            export_csv(filtered, csv_path)
            generated_exts.append("csv")
        if want_html:
            export_html(
                filtered,
                html_path,
                prefs=prefs,
                timestamp=timestamp,
            )
            generated_exts.append("html")

        if launch_json and json_path.exists():
            _open_in_system(json_path)
        if launch_csv and csv_path.exists():
            _open_in_system(csv_path)
        if launch_html and html_path.exists():
            # Prefer browser for HTML launch (new window/tab where possible).
            try:
                import webbrowser

                webbrowser.open(html_path.resolve().as_uri(), new=2)
            except Exception as exc:  # pragma: no cover - defensive
                print(f"Warning: could not open HTML results in browser: {exc}")

        message = _format_exported_paths(prefix, generated_exts)
        if message:
            print(message)


if __name__ == "__main__":
    main()
