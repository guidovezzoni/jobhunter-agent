# Agent guidance for Job Hunter Agent

This file helps AI agents (and humans) understand the codebase and where to make changes when adding features or fixing bugs. **Keep this file updated when you add modules, change the workflow, or introduce new conventions.**

## Codebase layout

- **Entry**: `main.py` – orchestrates the pipeline (preferences → fetch → normalize → extract → summarize → export to `results/`). Exports always run (no user confirm). Add new pipeline steps here or call new modules from here.
- **Config**: `src/config.py` – `SearchPreferences` and `collect_preferences()`. Add new user-facing options (e.g. filters, output format) here or in a dedicated config module.
- **Data**: `src/data_source.py` – JSearch API vs mock file selection, raw response save to `debug/api-response/<timestamp>_response.json`. Returns `(raw, timestamp)` so `main` can export to `results/<timestamp>_jobs.json` and `results/<timestamp>_jobs.csv` with the same timestamp. Add new job sources (other APIs, scrapers) here; keep the same contract: return (raw response dict, timestamp) and let `normalize`/`extract` stay source-agnostic.
- **Normalize**: `src/normalize.py` – raw response → list of job dicts with consistent keys. When adding a new data source, either map its shape to the same keys here or add a source-specific normalizer and call it from `main.py`.
- **Extract**: `src/extract.py` – one normalized job dict → extracted fields (location_type, position_type, minimum_salary, industry, job_spec_language, tech_stack, requirements, job_link). Add new extracted fields here and in `extract_job_info()`; extend `TECH_KEYWORDS` or pattern lists as needed.
- **Summary**: `src/summary.py` – builds human-readable summary per job and handles export (JSON/CSV). Add new output formats or summary sections here; update `build_summary()` and export helpers.

## Conventions

- **Paths**: Use `Path` from `pathlib`. Paths to mock and debug dirs are in `src/data_source.py` (`MOCK_PATH`, `DEBUG_DIR`).
- **Env**: Load via `python-dotenv` in `data_source.py`; read `os.environ` only after `load_dotenv()`.
- **Mock file**: May be Python literal (single quotes, `None`, trailing commas). Parsing is in `_parse_mock_content()` in `data_source.py`.
- **Types**: Prefer type hints and `list[...]` / `dict[str, Any]` where helpful. Extracted job is a dict; no custom class required.

## Where to update when adding changes

| Change | Files to update |
|--------|------------------|
| New user preference (e.g. salary min, remote-only) | `src/config.py` (and possibly `data_source` if it affects API params) |
| New job data source (API or scraper) | `src/data_source.py`; keep saving raw response under `debug/api-response/` with timestamp |
| New field to extract (e.g. benefits, posted date) | `src/extract.py` (`extract_job_info`, `_raw` excluded from export), then `src/summary.py` (`build_summary`, export columns if CSV/JSON) |
| New output format (e.g. Markdown export) | `src/summary.py` and `main.py` (always exports to `results/` with run timestamp) |
| New CLI flag or non-interactive mode | `main.py`, optionally `src/config.py` if parsing args |
| Change in JSearch API params or response shape | `src/data_source.py` (request), `src/normalize.py` (keys from response) |

After making such changes, update **README.md** (and this **agents.md** if you add modules or change the layout) so the docs stay in sync.
