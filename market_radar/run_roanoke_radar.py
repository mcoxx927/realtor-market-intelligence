"""
Runner for the Roanoke 4-hour Market Radar pipeline.
"""

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from market_radar.market_universe import build_universe, load_simple_yaml
from market_radar.update_region_config import update_config
from market_radar.radar_summary import main as radar_summary_main


def run_pipeline() -> None:
    result = subprocess.run([sys.executable, "run_market_analysis.py"], check=False)
    if result.returncode != 0:
        raise RuntimeError("Pipeline run failed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Roanoke 4-hour Market Radar workflow.")
    parser.add_argument("--config", default="market_radar/roanoke_radar_config.yaml")
    parser.add_argument("--month", default=None, help="Report month YYYY-MM (defaults to current month).")
    parser.add_argument("--dry-run", action="store_true", help="Preview config changes without writing.")
    parser.add_argument("--skip-pipeline", action="store_true", help="Skip the base pipeline run.")
    parser.add_argument("--limit", type=int, default=None, help="Limit markets for quick tests.")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_simple_yaml(config_path)
    paths = config.get("paths", {})

    universe_path = Path(paths.get("universe_json", "market_radar/roanoke_4hr_universe.json"))
    seed_path = Path("market_radar/seeds_roanoke_4hr.csv")

    build_universe(config_path, seed_path, universe_path)

    update_config(Path(paths.get("metro_config", "metro_config.json")), universe_path, args.dry_run, args.limit)

    if args.dry_run:
        print(\"[DRY-RUN] Skipping pipeline run due to --dry-run.\")
    elif not args.skip_pipeline:
        run_pipeline()

    sys.argv = [
        sys.argv[0],
        "--config",
        str(config_path),
    ]
    if args.month:
        sys.argv.extend(["--month", args.month])
    if args.limit:
        sys.argv.extend(["--limit", str(args.limit)])
    radar_summary_main()


if __name__ == "__main__":
    main()
