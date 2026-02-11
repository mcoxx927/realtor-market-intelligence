# Real Estate Market Intelligence Analysis

Automated monthly pipeline for Redfin city-level housing analysis, dashboards, strategic summaries, optional AI narrative generation, and email delivery.

## Analysis Overview

- Markets are defined in `metro_config.json` (currently Charlotte and Roanoke).
- Source data is Redfin `city_market_tracker.tsv000.gz`.
- Processing includes metro-level and city-level trend calculations.
- Output period folders are derived from the latest data month (for example `2025-12`).

## Pipeline Flow

```
city_market_tracker.tsv000.gz
  -> extract_metros.py
  -> process_market_data.py
  -> generate_dashboards_v2.py
  -> extract_summary.py
  -> (optional) ai_narrative.py
  -> (optional) email_reports.py / run_scheduled.py notifications
```

## Key Scripts

- `run_market_analysis.py`: One-off full pipeline (extract, process, dashboard, summary).
- `run_scheduled.py`: Scheduled automation wrapper with optional fetch, optional AI, and email notifications.
- `fetch_redfin_data.py`: Downloads latest Redfin source data.
- `ai_narrative.py`: Generates optional narrative files from summary and trend data.
- `email_reports.py`: Sends test emails or metro report emails manually.

## Quick Start

1. Install dependencies.

```bash
pip install -r requirements.txt
```

2. Put `city_market_tracker.tsv000.gz` in the repo root.

3. Confirm `metro_config.json` has the metros you want and `enabled: true`.

4. Run the pipeline.

```bash
python run_market_analysis.py
```

5. For scheduler-style execution (with notifications), run:

```bash
python run_scheduled.py
```

Useful scheduler flags:

- `--no-fetch`
- `--no-notify`
- `--no-ai`
- `--dry-run`

## Configuration

### `metro_config.json`

Each enabled metro should define:

- `name`: slug used in filenames (example `charlotte`)
- `display_name`: readable label (example `Charlotte, NC`)
- `metro_code`: Redfin metro code
- `output_directory`: where reports are written (example `core_markets/charlotte`)
- `enabled`: include metro in pipeline run

`data_settings.output_file_pattern` controls extracted TSV naming (default `{name}_cities_filtered.tsv`).

### `notifications_config.json` and `.env`

Email and scheduler settings load from `notifications_config.json`, then environment variables override them.

Important email defaults now:

- `include_summary_attachment`: `false`
- `include_dashboard_attachment`: `true`

If `.env` includes `INCLUDE_SUMMARY_ATTACHMENT`, it overrides JSON.

## Output Structure

Extracted TSVs are written to repo root:

- `charlotte_cities_filtered.tsv`
- `roanoke_cities_filtered.tsv`
- additional metros follow `{name}_cities_filtered.tsv`

Per-metro outputs are written to each metro's `output_directory`:

```
core_markets/
  charlotte/
    YYYY-MM/
      charlotte_data.json
      charlotte_summary.json
      dashboard_enhanced_charlotte_YYYY-MM.html
      charlotte_narrative.txt            # optional
      charlotte_narrative.json           # optional
  roanoke/
    YYYY-MM/
      roanoke_data.json
      roanoke_summary.json
      dashboard_enhanced_roanoke_YYYY-MM.html
      roanoke_narrative.txt              # optional
      roanoke_narrative.json             # optional
```

## Email Behavior

`run_scheduled.py` sends:

- Pipeline status email (success or failure based on config).
- Per-metro report emails when pipeline succeeds.

Per-metro email includes:

- HTML + plain-text summary body.
- AI narrative content in body when available.
- Dashboard attachment when enabled and present.
- Summary JSON attachment only when explicitly enabled.

If dashboard attachment delivery fails (size/policy), the sender retries without dashboard, then retries without attachments so the report body still delivers.

## Windows Task Scheduler

You can schedule `run_scheduled.py` directly or use `setup_task_scheduler.ps1`.

Example task command:

```powershell
python C:\path\to\run_scheduled.py --no-fetch
```

Logs are written to `pipeline_runs.log` by default.

## Roanoke 4-Hour Market Radar (Add-on)

Run:

```bash
python market_radar/run_roanoke_radar.py
```

Notes:

- Radar config: `market_radar/roanoke_radar_config.yaml`
- Seed list: `market_radar/seeds_roanoke_4hr.csv`
- Output: `market_radar/outputs/YYYY-MM/`
- The radar uses existing metro outputs from configured metro directories when available.

## Distressed Market Fit (Add-on)

Run:

```bash
python market_radar/run_distressed_fit.py
```

Useful flags:

- `--month YYYY-MM`
- `--limit N`
- `--with-backtest`
- `--competition-csv path/to/competition_proxy.csv`
- `--housing-age-csv path/to/housing_age_proxy.csv`

Notes:

- Config: `market_radar/distressed_fit_config.yaml`
- Optional external proxy inputs: `market_radar/inputs/competition_proxy.csv`, `market_radar/inputs/housing_age_proxy.csv`
- Outputs: `market_radar/outputs_distressed_fit/YYYY-MM/`
  - `distressed_fit_ranked.csv`
  - `distressed_fit_ranked.md`
  - `distressed_fit_diagnostics.json`

## Troubleshooting

- If emails reference the wrong month, verify all scripts are writing to the same `output_directory` tree in `metro_config.json`.
- If detailed market emails are missing, check `pipeline_runs.log` for per-metro `[SKIP]` or `[FAILED]` lines in the notification section.
- If email config appears ignored, check `.env` for override variables.

## Data Source

- Redfin Data Center: https://www.redfin.com/news/data-center/
- Primary file: `city_market_tracker.tsv000.gz`
- Coverage: US city-level monthly housing metrics

---

Last updated: February 10, 2026
