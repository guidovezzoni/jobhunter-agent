# Agent guidance for Job Hunter Agent

This file helps AI agents (and humans) understand the codebase and where to make changes when adding features or fixing bugs. **Keep this file updated when you add modules, change the workflow, or introduce new conventions.**

## Codebase layout

- **Entry**: `main.py` – orchestrates the pipeline (parses CLI args, preferences & filters → fetch or reuse cached data → normalize → extract → filter → summarize → export to `results/`). Exports are controlled by the `output` modes on `SearchPreferences` (parsed from YAML) and may optionally auto-launch (HTML in the browser, CSV/JSON via the OS). Add new pipeline steps here or call new modules from here.
- **Config**: `src/config.py` – `SearchPreferences`, `EUROPE_LOCATION_TRIGGERS`, `DEFAULT_EUROPE_COUNTRIES`, `collect_preferences(defaults=None)` for interactive role/location/date_posted and post-fetch filters, and `load_preferences_from_yaml()` for YAML-based configurations (same fields as interactive mode), plus `OUTPUT_CHOICES` and the `output` list on `SearchPreferences` that drives which exports run and which are launched. `collect_preferences` accepts an optional `SearchPreferences` object; when provided, its field values are shown as per-prompt defaults (pressing Enter accepts them). In `main.py`, `config.yaml` from the project root is loaded and passed as `defaults` before the interactive prompts run. The `europe_countries` field on `SearchPreferences` is non-empty when multi-country European search mode is active; if a Europe-trigger location is used but `europe_countries` is empty, `main.py` aborts with an error before fetching. Add new user-facing options (e.g. extra filters, output format) here or in a dedicated config module.
- **Data**: `src/data_source.py` – JSearch API vs mock file selection. For single-location searches uses `_fetch_jsearch_single()`; for multi-country European searches uses `_fetch_jsearch_multi_country()` which loops over `prefs.europe_countries`, makes one API call per country code, and merges + deduplicates results by `job_id` into a single synthetic response. Basic location→country inference (`_infer_country`) is used for single-location calls only. Raw response saved to `debug/api-response/<timestamp>_response.json`. The `MAX_PAGES` constant controls pages per API call; in multi-country mode the total requests = `len(europe_countries) × MAX_PAGES`. Add new job sources here; keep the same return contract.
- **Cache**: `src/cache.py` – file-based cache of raw responses keyed by `(role, location, date_posted)` with a 60-minute TTL. When `europe_countries` is non-empty the sorted country codes are appended to the location slug so changing the list busts the cache. Change cache behavior here (e.g. TTL, key strategy).
- **Normalize**: `src/normalize.py` – raw response → list of job dicts with consistent keys. When adding a new data source, either map its shape to the same keys here or add a source-specific normalizer and call it from `main.py`.
- **Extract**: `src/extract.py` – one normalized job dict → extracted fields (location_type, position_type, minimum_salary, industry, job_spec_language, tech_stack, requirements, job_link, job_country). Add new extracted fields here and in `extract_job_info()`; extend `TECH_KEYWORDS` or pattern lists as needed.
- **Filtering**: `src/filtering.py` – applies user-selected filters (location type, position type, minimum salary, industry, language) to the extracted jobs. Update this when changing filter semantics.
- **Summary**: `src/summary.py` – builds human-readable summary per job and handles export (JSON/CSV/HTML). Add new output formats or summary sections here; update `build_summary()` and export helpers (`export_json`, `export_csv`, `export_html`).

## Conventions

- **Paths**: Use `Path` from `pathlib`. Paths to mock and debug dirs are in `src/data_source.py` (`MOCK_PATH`, `DEBUG_DIR`).
- **Pagination**: `MAX_PAGES` in `src/data_source.py` sets the number of pages requested from the JSearch API per call (default 5, yielding up to 50 results). It is not part of the cache key, so changing it will take effect only after the cache expires or is cleared. In multi-country mode total requests = `len(europe_countries) × MAX_PAGES`.
- **Multi-country Europe mode**: Triggered when `prefs.europe_countries` is non-empty (set by `config.py` when location matches `EUROPE_LOCATION_TRIGGERS`). The merged result is treated as a single response by all downstream modules.
- **Env**: Load via `python-dotenv` in `data_source.py`; read `os.environ` only after `load_dotenv()`.
- **Mock file**: May be Python literal (single quotes, `None`, trailing commas). Parsing is in `_parse_mock_content()` in `data_source.py`.
- **Types**: Prefer type hints and `list[...]` / `dict[str, Any]` where helpful. Extracted job is a dict; no custom class required.

## Where to update when adding changes

| Change | Files to update |
|--------|------------------|
| New user preference or filter (e.g. salary min, remote-only) | `src/config.py` (and possibly `src/filtering.py` if it affects filtering, or `src/data_source.py` if it affects API params, or `src/cache.py` if it must be part of the cache key); for export behaviour use the `output` list / modes in `src/config.py` + `main.py`. |
| New job data source (API or scraper) | `src/data_source.py`; keep saving raw response under `debug/api-response/` with timestamp; add caching strategy in `src/cache.py` if needed |
| New field to extract (e.g. benefits, posted date) | `src/extract.py` (`extract_job_info`, `_raw` excluded from export), then `src/summary.py` (`build_summary`, export columns if CSV/JSON) |
| New output format (e.g. Markdown export) | `src/summary.py` (add an `export_*` function) and `main.py` (call it alongside `export_json`/`export_csv`/`export_html`; always exports to `results/` with run timestamp) |
| New CLI flag or non-interactive mode | `main.py` (arg parsing / control flow), `src/config.py` if parsing from YAML or adding new preference fields |
| Change in JSearch API params or response shape | `src/data_source.py` (request), `src/normalize.py` (keys from response), `src/cache.py` (if cache keys or TTL must change) |
| Change `date_posted` values or add new posting-date options | `src/config.py` (`DATE_POSTED_CHOICES`, `collect_preferences`, `load_preferences_from_yaml`), `src/data_source.py` (API param), `src/cache.py` (cache key), `config.yaml` (default value) |
| Add or change European countries for multi-country search | `src/config.py` (`DEFAULT_EUROPE_COUNTRIES`, `EUROPE_LOCATION_TRIGGERS`), `src/data_source.py` (`_fetch_jsearch_multi_country`), `config.yaml` (`europe_countries`) |

After making such changes, update **README.md** (and this **agents.md** if you add modules or change the layout) so the docs stay in sync.
