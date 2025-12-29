# Roanoke 4-hour Market Radar

## What it does

Analyzes markets from your seed list and produces a ranked "dealability" report.

**Simple flow:**
1. Read markets from `seeds_roanoke_4hr.csv`
2. Pull metrics directly from master Redfin TSV
3. Score and rank by dealability
4. Output CSV and Markdown reports

## Files

```
market_radar/
+-- seeds_roanoke_4hr.csv      # Your markets (edit this!)
+-- roanoke_radar_config.yaml  # Scoring weights, price band
+-- run_roanoke_radar.py       # Runner script
+-- radar_summary.py           # Core logic
+-- build_seed_from_tsv.py     # Utility to refresh seed list (yearly)
+-- outputs/
    +-- YYYY-MM/
        +-- Market_Radar_Roanoke_4hr_YYYY-MM.csv
        +-- Market_Radar_Roanoke_4hr_YYYY-MM.md
```

## Usage

```bash
# Run the radar (uses all markets in seed CSV)
python market_radar/run_roanoke_radar.py

# Quick test with 5 markets
python market_radar/run_roanoke_radar.py --limit 5

# Specific month
python market_radar/run_roanoke_radar.py --month 2025-01
```

## Adding/Removing Markets

Edit `seeds_roanoke_4hr.csv` directly. Required columns:
- `metro_code` - Redfin metro code (required)
- `market_name` - Display name
- `state` - State abbreviation
- `display_name` - Full name for reports

The `lat`, `lon` columns are optional (kept for reference).

## Refreshing the Seed List

Run yearly to pick up any new metros in Redfin data:

```bash
python market_radar/build_seed_from_tsv.py --merge-existing market_radar/seeds_roanoke_4hr.csv
```

## Configuration

Edit `roanoke_radar_config.yaml`:
- `target_price_band` - min/max price range for scoring
- `scoring_weights` - weight for liquidity, inventory pressure, price fit
