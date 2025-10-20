# Repository Guidelines

## Project Structure & Module Organization
- Root Python pipeline scripts: `extract_metros.py`, `process_market_data.py`, `generate_dashboards_v2.py`, and the orchestrator `run_market_analysis.py`.
- Configuration lives in `metro_config.json`; update metro codes or data paths here before running the pipeline.
- Source data (`city_market_tracker.tsv000.gz`, `county_market_tracker.tsv000.gz`) sits at the repo root; monthly outputs land in metro folders like `charlotte/2025-09/` and `roanoke/2025-09/`.
- Reference docs (`README.md`, `DATA_SOURCES_AND_AUTOMATION_GUIDE.md`) summarize workflow expectations and data lineage.

## Build, Test, and Development Commands
- `python3 run_market_analysis.py` — executes the full pipeline (extract → process → dashboard generation) using configuration in `metro_config.json`.
- `python3 extract_metros.py` — reruns only the metro extraction step; useful after updating raw TSVs or metro list.
- `python3 process_market_data.py` and `python3 generate_dashboards_v2.py` — run individual stages when debugging intermediate outputs.

## Coding Style & Naming Conventions
- Python code follows PEP 8 basics: 4-space indentation, snake_case for functions/variables, and descriptive docstrings.
- Prefer explicit helper functions with short, single-purpose blocks; maintain existing structured logging (`[EXTRACTING]`, `[OK]`, etc.) for pipeline visibility.
- External dependencies are limited to the standard library plus `pandas`; keep imports grouped (stdlib first, then third-party).

## Testing Guidelines
- No formal test suite exists; validate changes by running `python3 run_market_analysis.py` and confirming TSV/JSON/HTML outputs are regenerated without errors.
- Spot-check generated dashboards in a browser and inspect console output for JavaScript warnings.
- When adjusting data transformations, compare old vs. new JSON snapshots to ensure expected metric deltas.

## Commit & Pull Request Guidelines
- Use imperative, descriptive commit messages (e.g., `Adjust metro extractor for quoted headers`); group related pipeline changes together.
- Pull requests should outline the pipeline steps exercised, list regenerated artifacts, and mention any manual validation (browser checks, data comparisons).
- Include screenshots or key metrics when UI or dashboard behavior changes to speed up verification.
