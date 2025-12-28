# Roanoke 4-hour Market Radar

## What it does

The Roanoke Market Radar is a lightweight add-on that:

1. Builds a candidate universe of markets within ~4 hours of Roanoke City, VA.
2. Updates `metro_config.json` with that universe.
3. Runs the existing pipeline (`run_market_analysis.py`).
4. Produces a ranked Market Radar summary.

## Universe generation (4-hour drive shed)

**Primary source:** the Redfin `city_market_tracker.tsv000.gz` file (not committed to the repo).

When `universe_source: "api"` is enabled in `market_radar/roanoke_radar_config.yaml`, the universe
builder does the following:

1. Reads the Redfin TSV to enumerate all metros (name + metro code + lat/lon).  
   This uses the metro-level columns embedded in the city tracker file.
2. Calls the OpenRouteService isochrone API (`ORS_API_KEY`) to get a 4-hour drive polygon.
3. Filters the full metro list to those that fall inside the polygon.

**Fallback:** if the Redfin TSV is missing columns or the API key is unavailable, the
builder falls back to `market_radar/seeds_roanoke_4hr.csv`.

## Running the radar

```bash
python market_radar/run_roanoke_radar.py
```

Useful flags:
- `--month YYYY-MM` for output file naming
- `--dry-run` to preview config updates without writing
- `--skip-pipeline` to build the radar summary from existing outputs
- `--limit N` for quick local tests

## Outputs

Generated outputs land in:

```
outputs/YYYY-MM/
├── Market_Radar_Roanoke_4hr_YYYY-MM.csv
└── Market_Radar_Roanoke_4hr_YYYY-MM.md
```

## Configuration

- `market_radar/roanoke_radar_config.yaml` controls:
  - home base location
  - drive time minutes
  - OpenRouteService API settings
  - target price band and scoring weights
  - paths to the Redfin TSV + pipeline config

- `market_radar/seeds_roanoke_4hr.csv` provides a seed list with lat/lon coordinates
  for fallback operation.
