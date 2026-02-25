# Job Hunter Agent

A Python CLI that searches job boards via the JSearch API (or a mock response), extracts key job fields, and prints tailored summaries. You can optionally export results to JSON or CSV.

## Workflow

1. **Preferences & filters** – On launch you are prompted for:
   - **Role** (default: "Android Developer") and **Location** (default: empty = any location), used to query jobs.
   - Optional **filters** applied afterwards: location type(s) (`on-site`, `hybrid`, `remote`), position type(s) (`permanent`, `contract`, `freelance`), minimum salary, industry text, and job spec language (default `en`, or `any` for no language filter).
2. **Data source & caching** – If `RAPID_API_KEY` is set in `.env`, the app calls the JSearch RapidAPI using your role/location (with basic country inference for cities like London, Barcelona, Madrid). Otherwise it loads the mock response from `docs/RapidAPIResponse.txt` (Python-style or JSON). Raw responses are cached on disk per `(role, location)` for **60 minutes**, so repeated runs with the same role/location reuse the cached data instead of calling the API again.
3. **Debug save** – The raw API/mock response for the current run is saved under `debug/api-response/` with a timestamped filename (e.g. `YYYYMMDD_HHMMSS_response.json`).
4. **Extraction** – For each job the app derives: location type (on-site/hybrid/remote), position type (permanent/contract/freelance), minimum salary, industry, job ad language, tech stack, requirements, and job link.
5. **Filtering & summary** – The extracted jobs are filtered according to your chosen filters. A short summary per remaining job is printed to the console. Results are always exported to the `results/` folder using the same timestamp as the debug file (e.g. `results/YYYYMMDD_HHMMSS_jobs.json` and `results/YYYYMMDD_HHMMSS_jobs.csv`), so you can match them to the raw response in `debug/api-response/`.

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

Or activate the venv and run `python main.py`. When prompted, enter role/location or press Enter for defaults. Results are always written to `results/` (no confirmation).

## Project structure

| Path | Purpose |
|------|--------|
| `main.py` | Entry point: collects preferences and filters, fetches or reuses cached jobs, normalizes, extracts, filters, prints summaries, and exports results. |
| `src/config.py` | Defines `SearchPreferences` and `collect_preferences()` for role, location, and all post-fetch filters. |
| `src/data_source.py` | Fetches from JSearch API or mock file, applies basic location handling, uses the cache, and saves the raw response to `debug/api-response/`. |
| `src/cache.py` | Simple file-based cache of raw API/mock responses keyed by `(role, location)` with a 60-minute TTL. |
| `src/normalize.py` | Converts raw response into a list of normalized job dicts. |
| `src/extract.py` | Extracts location type, position type, salary, industry, language, tech stack, requirements, job link. |
| `src/filtering.py` | Applies user-selected filters (location type, position type, minimum salary, industry, language) to the extracted jobs. |
| `src/summary.py` | Builds per-job summary text and export (JSON/CSV). |
| `docs/RapidAPIResponse.txt` | Mock JSearch response (used when no API key). |
| `debug/api-response/` | Timestamped raw API responses (`YYYYMMDD_HHMMSS_response.json`). |
| `debug/cache/` | Cache files storing raw responses per `(role, location)`. |
| `results/` | Timestamped exports (`YYYYMMDD_HHMMSS_jobs.json`, `YYYYMMDD_HHMMSS_jobs.csv`); same timestamp as the debug file for the same run. |

## Environment

| Variable | Purpose |
|----------|--------|
| `RAPID_API_KEY` | JSearch API key (RapidAPI). If unset, mock file is used. |

## Keeping this README updated

When you add or change features (e.g. new data sources, CLI flags, env vars, or modules), update this README: **Setup**, **Run**, **Project structure**, and **Environment** so they stay accurate. See also `agents.md` for where to edit when extending the codebase.
