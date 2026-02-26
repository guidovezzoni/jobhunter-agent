"""Generate tailored job summaries and output (console, optional export)."""

import csv
import html as _html_module
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


def export_html(
    extracted_list: list[dict[str, Any]],
    path: Path,
    prefs: Any = None,
    timestamp: str = "",
) -> None:
    """Export job results as a self-contained HTML page viewable in a browser."""

    def esc(value: object) -> str:
        return _html_module.escape(str(value)) if value is not None else ""

    # Build search criteria rows (only show fields that were actually set)
    role = (prefs.role if prefs else "") or ""
    location = (prefs.location if prefs else "") or "any"

    criteria_rows = f'<tr><th>Role</th><td>{esc(role) or "N/A"}</td></tr>'
    criteria_rows += f'<tr><th>Location</th><td>{esc(location)}</td></tr>'

    if prefs:
        criteria_rows += f'<tr><th>Date posted</th><td>{esc(prefs.date_posted)}</td></tr>'
        if prefs.europe_countries:
            criteria_rows += (
                f'<tr><th>Countries</th><td>{esc(", ".join(prefs.europe_countries).upper())}</td></tr>'
            )
        if prefs.location_types:
            criteria_rows += f'<tr><th>Location type</th><td>{esc(", ".join(prefs.location_types))}</td></tr>'
        if prefs.position_types:
            criteria_rows += f'<tr><th>Position type</th><td>{esc(", ".join(prefs.position_types))}</td></tr>'
        if prefs.minimum_salary is not None:
            criteria_rows += f'<tr><th>Min. salary</th><td>{prefs.minimum_salary:,} (annual)</td></tr>'
        if prefs.industry_filter:
            criteria_rows += f'<tr><th>Industry</th><td>{esc(prefs.industry_filter)}</td></tr>'
        if prefs.language_filter and prefs.language_filter != "any":
            criteria_rows += f'<tr><th>Job ad language</th><td>{esc(prefs.language_filter)}</td></tr>'

    cards_html = ""
    for i, ex in enumerate(extracted_list):
        min_sal = ex.get("minimum_salary")
        salary_row = (
            f'<tr><th>Min. salary</th><td>{min_sal:,} (annual)</td></tr>'
            if min_sal is not None
            else ""
        )

        industry = ex.get("industry") or ""
        industry_row = (
            f'<tr><th>Industry</th><td>{esc(industry)}</td></tr>' if industry else ""
        )

        lang = ex.get("job_spec_language") or ""
        lang_row = (
            f'<tr><th>Job ad language</th><td>{esc(lang)}</td></tr>'
            if lang and lang != "not defined"
            else ""
        )

        tech = ex.get("tech_stack") or []
        tech_tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in tech)
        tech_row = (
            f'<tr><th>Tech stack</th><td class="tags">{tech_tags}</td></tr>'
            if tech
            else ""
        )

        reqs = ex.get("requirements") or []
        req_items = "".join(
            f"<li>{esc(r[:200])}{'…' if len(r) > 200 else ''}</li>"
            for r in reqs[:8]
        )
        req_block = (
            f'<div class="reqs"><strong>Key requirements</strong><ul>{req_items}</ul></div>'
            if req_items
            else ""
        )

        link = ex.get("job_link") or ""
        apply_btn = (
            f'<a class="apply-btn" href="{esc(link)}" target="_blank" rel="noopener">Apply</a>'
            if link
            else ""
        )

        cards_html += f"""
        <div class="card">
          <div class="card-header">
            <span class="job-num">#{i + 1}</span>
            <div>
              <div class="job-title">{esc(ex.get("role", "N/A"))}</div>
              <div class="company">{esc(ex.get("employer_name", "N/A"))}</div>
            </div>
          </div>
          <table class="meta">
            <tr><th>Location</th><td>{esc(ex.get("location") or "Not specified")}</td></tr>
            <tr><th>Location type</th><td>{esc(ex.get("location_type", "not defined"))}</td></tr>
            <tr><th>Position type</th><td>{esc(ex.get("position_type", "not defined"))}</td></tr>
            {salary_row}
            {industry_row}
            {lang_row}
            {tech_row}
          </table>
          {req_block}
          {apply_btn}
        </div>
"""

    header_ts = esc(timestamp) if timestamp else ""
    total = len(extracted_list)

    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Job results — {esc(role)}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f4f6f9;
      color: #222;
      padding: 2rem 1rem;
    }}
    header {{
      max-width: 860px;
      margin: 0 auto 2rem;
    }}
    header h1 {{
      font-size: 1.7rem;
      font-weight: 700;
      color: #1a1a2e;
      margin-bottom: 1rem;
    }}
    .criteria {{
      background: #fff;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,.08);
      padding: 1rem 1.4rem;
      margin-bottom: 0.75rem;
    }}
    .criteria table {{
      border-collapse: collapse;
      font-size: 0.88rem;
    }}
    .criteria th {{
      text-align: left;
      width: 140px;
      padding: 0.22rem 0.6rem 0.22rem 0;
      color: #666;
      font-weight: 600;
    }}
    .criteria td {{
      color: #222;
      padding: 0.22rem 0;
    }}
    .run-meta {{
      font-size: 0.8rem;
      color: #888;
      margin-top: 0.5rem;
    }}
    .cards {{
      max-width: 860px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }}
    .card {{
      background: #fff;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,.08);
      padding: 1.4rem 1.6rem;
    }}
    .card-header {{
      display: flex;
      align-items: flex-start;
      gap: 1rem;
      margin-bottom: 1rem;
    }}
    .job-num {{
      background: #e8edf5;
      color: #3a5a8c;
      font-weight: 700;
      font-size: 0.8rem;
      padding: 0.25rem 0.55rem;
      border-radius: 6px;
      white-space: nowrap;
      margin-top: 0.2rem;
    }}
    .job-title {{
      font-size: 1.15rem;
      font-weight: 700;
      color: #1a1a2e;
    }}
    .company {{
      font-size: 0.95rem;
      color: #555;
      margin-top: 0.15rem;
    }}
    table.meta {{
      border-collapse: collapse;
      width: 100%;
      font-size: 0.88rem;
      margin-bottom: 0.9rem;
    }}
    table.meta th {{
      text-align: left;
      width: 140px;
      padding: 0.28rem 0.5rem 0.28rem 0;
      color: #666;
      font-weight: 600;
      vertical-align: top;
    }}
    table.meta td {{
      padding: 0.28rem 0;
      color: #333;
      vertical-align: top;
    }}
    td.tags {{ display: flex; flex-wrap: wrap; gap: 0.35rem; }}
    .tag {{
      background: #e8f0fe;
      color: #2a5aad;
      font-size: 0.78rem;
      padding: 0.18rem 0.55rem;
      border-radius: 20px;
      font-weight: 500;
    }}
    .reqs {{
      font-size: 0.88rem;
      margin-bottom: 1rem;
    }}
    .reqs strong {{
      display: block;
      margin-bottom: 0.4rem;
      color: #444;
    }}
    .reqs ul {{
      padding-left: 1.2rem;
      color: #333;
    }}
    .reqs li {{ margin-bottom: 0.25rem; line-height: 1.45; }}
    .apply-btn {{
      display: inline-block;
      background: #2a5aad;
      color: #fff;
      text-decoration: none;
      padding: 0.45rem 1.1rem;
      border-radius: 7px;
      font-size: 0.88rem;
      font-weight: 600;
      transition: background 0.15s;
    }}
    .apply-btn:hover {{ background: #1e4080; }}
    footer {{
      max-width: 860px;
      margin: 2rem auto 0;
      font-size: 0.8rem;
      color: #999;
      text-align: center;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Job results: {esc(role) or "N/A"}</h1>
    <div class="criteria">
      <table>
        {criteria_rows}
      </table>
    </div>
    <div class="run-meta">{total} job(s) after filtering{f" &nbsp;·&nbsp; Run: {header_ts}" if header_ts else ""}</div>
  </header>
  <div class="cards">
    {cards_html}
  </div>
  <footer>Generated by Job Hunter Agent</footer>
</body>
</html>
"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_page, encoding="utf-8")
