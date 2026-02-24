"""Generate tailored job summaries and output (console, optional export)."""

import csv
import json
from pathlib import Path
from typing import Any


def build_summary(extracted: dict[str, Any], index: int) -> str:
    """Build one human-readable summary from extracted job info."""
    lines = [
        f"{'='*60}",
        f"Job #{index + 1}: {extracted.get('role', 'N/A')}",
        f"Company: {extracted.get('employer_name', 'N/A')}",
        f"Location: {extracted.get('location') or 'Not specified'}",
        f"Location type: {extracted.get('location_type', 'not defined')}",
        f"Position type: {extracted.get('position_type', 'not defined')}",
    ]
    min_sal = extracted.get("minimum_salary")
    if min_sal is not None:
        lines.append(f"Minimum salary: {min_sal:,} (annual)")
    industry = extracted.get("industry")
    if industry:
        lines.append(f"Industry: {industry}")
    lang = extracted.get("job_spec_language")
    if lang and lang != "not defined":
        lines.append(f"Job ad language: {lang}")
    tech = extracted.get("tech_stack") or []
    if tech:
        lines.append(f"Tech stack: {', '.join(tech)}")
    reqs = extracted.get("requirements") or []
    if reqs:
        lines.append("Key requirements:")
        for r in reqs[:8]:
            lines.append(f"  - {r[:200]}{'...' if len(r) > 200 else ''}")
    link = extracted.get("job_link")
    if link:
        lines.append(f"Apply: {link}")
    lines.append("")
    return "\n".join(lines)


def print_summaries(extracted_list: list[dict[str, Any]]) -> None:
    """Print tailored summaries to console."""
    for i, ex in enumerate(extracted_list):
        print(build_summary(ex, i))


def export_json(extracted_list: list[dict[str, Any]], path: Path) -> None:
    """Export extracted job list to JSON (without _raw if present for brevity)."""
    out = []
    for ex in extracted_list:
        d = {k: v for k, v in ex.items() if k != "_raw"}
        out.append(d)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


def export_csv(extracted_list: list[dict[str, Any]], path: Path) -> None:
    """Export flattened job list to CSV (one row per job; requirements/tech as joined string)."""
    if not extracted_list:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = [
        "role", "employer_name", "location", "location_type", "position_type",
        "minimum_salary", "industry", "job_spec_language", "tech_stack", "requirements", "job_link",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for ex in extracted_list:
            row = {k: ex.get(k) for k in keys}
            if isinstance(row.get("tech_stack"), list):
                row["tech_stack"] = "; ".join(row["tech_stack"]) if row["tech_stack"] else ""
            if isinstance(row.get("requirements"), list):
                row["requirements"] = "; ".join(str(x)[:100] for x in row["requirements"]) if row["requirements"] else ""
            w.writerow(row)
