# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Automated pipeline for analyzing Redfin city-level market data for real estate markets (Charlotte, NC and Roanoke, VA). Processes monthly TSV data from Redfin Data Center into JSON and interactive HTML dashboards.

## Commands

**Run complete pipeline:**
```bash
python run_market_analysis.py
```

**Run individual stages:**
```bash
python extract_metros.py           # Step 1: Extract metros from raw TSV
python process_market_data.py      # Step 2: Process TSV to JSON with 12-month trends
python generate_dashboards_v2.py   # Step 3: Generate HTML dashboards
python extract_summary.py          # Step 4: Generate strategic analysis summary
```

**Dependencies:**
```bash
pip install pandas
```

## Architecture

### Data Flow
```
city_market_tracker.tsv000.gz (Redfin national data)
    -> extract_metros.py (reads metro_config.json)
    -> {metro}_cities_filtered.tsv
    -> process_market_data.py
    -> {metro}/YYYY-MM/{metro}_data.json
    -> generate_dashboards_v2.py
    -> {metro}/YYYY-MM/dashboard_enhanced_{metro}_YYYY-MM.html
    -> extract_summary.py
    -> {metro}/YYYY-MM/{metro}_summary.json (strategic analysis)
```

Note: YYYY-MM folder is determined dynamically from the data period, not hardcoded.

### Configuration

**metro_config.json** - Add/modify metros by editing this file (no code changes needed):
- `name`: internal identifier
- `metro_code`: Redfin PARENT_METRO_REGION_METRO_CODE
- `enabled`: boolean to include/exclude

### Output Structure
```
{metro}/
└── YYYY-MM/
    ├── {metro}_data.json                        # Full data with 12-month trends
    ├── dashboard_enhanced_{metro}_YYYY-MM.html  # Interactive charts
    └── {metro}_summary.json                     # Strategic analysis (see below)
```

## Summary JSON Structure

The `{metro}_summary.json` contains Python-generated strategic analysis:
- `market_status`: BULLISH / NEUTRAL / BEARISH classification
- `recommendations`: Seller/buyer/investor guidance
- `city_tiers`: Cities grouped by HOT / BALANCED / BUYER markets
- `alert_cities`: Cities with concerning metrics (sorted by severity)
- `key_metrics`: Weighted averages for price, DOM, health score

This replaces the need for AI agent analysis in most cases.

## Data Source

Redfin Data Center monthly city-level TSV:
- URL: https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz
- Release schedule: Friday of third full week each month
- Place downloaded file in project root before running pipeline

## Validation

No formal test suite. Validate by:
1. Running the full pipeline and confirming no errors
2. Checking generated JSON/HTML outputs exist
3. Opening dashboards in browser to verify charts render
