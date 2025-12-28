"""
Update metro_config.json using the Roanoke market universe list.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from market_radar.market_universe import load_simple_yaml


def slugify(text: str) -> str:
    return (
        text.lower()
        .replace("&", "and")
        .replace(",", "")
        .replace("/", "-")
        .replace("  ", " ")
        .strip()
        .replace(" ", "-")
    )


def load_universe(universe_path: Path) -> list:
    payload = json.loads(universe_path.read_text())
    return payload.get("markets", [])


def build_metro_entry(market: dict) -> dict:
    market_name = market.get("market_name", "").strip()
    state = market.get("state", "").strip()
    display_name = market.get("display_name") or f"{market_name}, {state}".strip(", ")
    output_directory = market.get("output_directory") or slugify(market_name)

    return {
        "name": output_directory,
        "display_name": display_name,
        "metro_code": str(market.get("metro_code", "")).strip(),
        "output_directory": output_directory,
        "enabled": True,
    }


def update_config(config_path: Path, universe_path: Path, dry_run: bool, limit: Optional[int]) -> dict:
    config = json.loads(config_path.read_text())
    existing = {metro["name"]: metro for metro in config.get("metros", [])}

    universe = load_universe(universe_path)
    if limit:
        universe = universe[:limit]

    updated = []
    changes = {"added": [], "updated": [], "skipped": []}

    for market in universe:
        entry = build_metro_entry(market)
        if not entry["metro_code"]:
            changes["skipped"].append(entry["name"])
            continue

        if entry["name"] in existing:
            existing_entry = existing[entry["name"]]
            if existing_entry != entry:
                changes["updated"].append(entry["name"])
                existing[entry["name"]] = entry
        else:
            changes["added"].append(entry["name"])
            existing[entry["name"]] = entry

    updated = list(existing.values())
    updated.sort(key=lambda item: item.get("name", ""))

    if not dry_run:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = config_path.with_suffix(f".json.bak_{timestamp}")
        backup_path.write_text(json.dumps(config, indent=2))

        config["metros"] = updated
        config_path.write_text(json.dumps(config, indent=2))

        print(f"[OK] Backed up config to {backup_path}")
        print(f"[OK] Updated metro config at {config_path}")
    else:
        print("[DRY-RUN] Metro config update preview")

    print(f"  Added: {len(changes['added'])}")
    if changes["added"]:
        print("   - " + ", ".join(changes["added"]))
    print(f"  Updated: {len(changes['updated'])}")
    if changes["updated"]:
        print("   - " + ", ".join(changes["updated"]))
    print(f"  Skipped (missing metro_code): {len(changes['skipped'])}")
    if changes["skipped"]:
        print("   - " + ", ".join(changes["skipped"]))

    return {
        "config": config,
        "changes": changes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Update metro_config.json from the Roanoke universe list.")
    parser.add_argument(
        "--config",
        default="metro_config.json",
        help="Path to metro_config.json",
    )
    parser.add_argument(
        "--universe",
        default=None,
        help="Universe JSON file (defaults to config paths.universe_json).",
    )
    parser.add_argument(
        "--radar-config",
        default="market_radar/roanoke_radar_config.yaml",
        help="Radar YAML config (for defaults).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of markets applied.")
    args = parser.parse_args()

    radar_config = load_simple_yaml(Path(args.radar_config))
    universe_path = Path(args.universe or radar_config.get("paths", {}).get("universe_json", "market_radar/roanoke_4hr_universe.json"))

    update_config(Path(args.config), universe_path, args.dry_run, args.limit)


if __name__ == "__main__":
    main()
