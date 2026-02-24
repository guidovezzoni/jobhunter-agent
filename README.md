# Job Hunter Agent

A Python CLI that searches job boards via the JSearch API (or a mock response), extracts key job fields, and prints tailored summaries. You can optionally export results to JSON or CSV.

## Workflow

1. **Preferences** – On launch you are prompted for **Role** (default: "Android Developer") and **Location** (default: empty = any location).
2. **Data source** – If `RAPID_API_KEY` is set in `.env`, the app calls the JSearch RapidAPI with your role and location. Otherwise it loads the mock response from `docs/RapidAPIResponse.txt` (Python-style or JSON). If neither is available, it warns and exits.
3. **Debug save** – The raw API/mock response is saved under `debug/api-response/` with a timestamped filename (e.g. `YYYYMMDD_HHMMSS_response.json`).
4. **Extraction** – For each job the app derives: location type (on-site/hybrid/remote), position type (permanent/contract/freelance), minimum salary, industry, job ad language, tech stack, requirements, and job link.
5. **Summary** – A short summary per job is printed to the console; you can then export to `debug/jobs_export.json` and `debug/jobs_export.csv` if prompted.

## Setup

- **Python**: 3.10+ (tested on 3.13).
- Create a virtual environment:

```bash
python3 -m venv .venv && source .venv/bin/activate
```

- Install dependencies:

```bash
pip install -r requirements.txt
```

- **Optional**: Add a `.env` in the project root with `RAPID_API_KEY=your_key` to use the live JSearch API. Without it, the app uses `docs/RapidAPIResponse.txt` if present.

## Run

From the project root:

```bash
.venv/bin/python main.py
```

Or activate the venv and run `python main.py`. When prompted, enter role/location or press Enter for defaults; at the end you can answer `y` to export results.

## Project structure

| Path | Purpose |
|------|--------|
| `main.py` | Entry point: collects preferences, fetches jobs, normalizes, extracts, prints summaries, optional export. |
| `src/config.py` | User preferences (role, location) and `collect_preferences()`. |
| `src/data_source.py` | Fetches from JSearch API or mock file; saves raw response to `debug/api-response/`. |
| `src/normalize.py` | Converts raw response into a list of normalized job dicts. |
| `src/extract.py` | Extracts location type, position type, salary, industry, language, tech stack, requirements, job link. |
| `src/summary.py` | Builds per-job summary text and export (JSON/CSV). |
| `docs/RapidAPIResponse.txt` | Mock JSearch response (used when no API key). |
| `debug/api-response/` | Timestamped raw API responses. |
| `debug/` | Optional export files: `jobs_export.json`, `jobs_export.csv`. |

## Environment

| Variable | Purpose |
|----------|--------|
| `RAPID_API_KEY` | JSearch API key (RapidAPI). If unset, mock file is used. |

## Keeping this README updated

When you add or change features (e.g. new data sources, CLI flags, env vars, or modules), update this README: **Setup**, **Run**, **Project structure**, and **Environment** so they stay accurate. See also `agents.md` for where to edit when extending the codebase.
