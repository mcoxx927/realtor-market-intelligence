"""
Runner for the Roanoke 4-hour Market Radar.

Simple flow:
1. Read markets from seed CSV
2. Generate radar summary (reads directly from master TSV)
3. Output to market_radar/outputs/

Usage:
    python market_radar/run_roanoke_radar.py
    python market_radar/run_roanoke_radar.py --month 2025-01
    python market_radar/run_roanoke_radar.py --limit 5  # Quick test
"""

import argparse
import sys
from pathlib import Path

# Add parent to path for imports
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from market_radar.radar_summary import run_radar


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Roanoke 4-hour Market Radar.")
    parser.add_argument("--config", default="market_radar/roanoke_radar_config.yaml",
                        help="Path to radar config YAML")
    parser.add_argument("--seeds", default="market_radar/seeds_roanoke_4hr.csv",
                        help="Path to seed CSV with markets")
    parser.add_argument("--month", default=None,
                        help="Report month YYYY-MM (defaults to latest in data)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of markets for quick tests")
    args = parser.parse_args()

    run_radar(
        config_path=Path(args.config),
        seed_path=Path(args.seeds),
        month=args.month,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
