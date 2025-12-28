"""
Build the Roanoke 4-hour market universe list.

Seed list is the default and can be validated later with a drive-time API.
"""

import argparse
import csv
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Tuple


def _parse_scalar(value: str):
    if value is None:
        return None
    cleaned = value.strip().strip('"').strip("'")
    if cleaned.lower() in {"true", "false"}:
        return cleaned.lower() == "true"
    if cleaned.isdigit():
        return int(cleaned)
    try:
        return float(cleaned)
    except ValueError:
        return cleaned


def load_simple_yaml(path: Path) -> dict:
    """Load a minimal YAML config (mapping + nested mapping)."""
    config = {}
    stack = [(0, config)]

    for raw_line in path.read_text().splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue
        line = raw_line.split("#", 1)[0].rstrip()
        indent = len(line) - len(line.lstrip(" "))
        key, _, value = line.lstrip().partition(":")
        key = key.strip()
        value = value.strip()

        while stack and indent <= stack[-1][0] and len(stack) > 1:
            stack.pop()
        parent = stack[-1][1]

        if value == "":
            parent[key] = {}
            stack.append((indent, parent[key]))
        else:
            parent[key] = _parse_scalar(value)

    return config


def load_seed_universe(seed_csv: Path) -> list:
    """Load the universe list from a seed CSV."""
    markets = []
    with seed_csv.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            markets.append({
                "market_name": row.get("market_name", "").strip(),
                "state": row.get("state", "").strip(),
                "preferred_region_type": row.get("preferred_region_type", "metro").strip() or "metro",
                "metro_code": row.get("metro_code", "").strip(),
                "display_name": row.get("display_name", "").strip(),
                "output_directory": row.get("output_directory", "").strip(),
                "lat": _parse_scalar(row.get("lat", "")),
                "lon": _parse_scalar(row.get("lon", "")),
                "notes": row.get("notes", "").strip(),
                "source": row.get("source", "seeds").strip(),
            })
    return markets


def _point_in_polygon(point: Tuple[float, float], polygon: Iterable[Tuple[float, float]]) -> bool:
    """Ray casting point-in-polygon check."""
    x, y = point
    inside = False
    vertices = list(polygon)
    n = len(vertices)
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        intersects = ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1)
        if intersects:
            inside = not inside
    return inside


def _load_isochrone_polygon(endpoint: str, api_key: str, lat: float, lon: float, minutes: int) -> list:
    payload = json.dumps({
        "locations": [[lon, lat]],
        "range": [minutes * 60],
        "range_type": "time",
    }).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    features = data.get("features", [])
    if not features:
        raise ValueError("Isochrone API response missing features.")
    coordinates = features[0]["geometry"]["coordinates"]
    if not coordinates:
        raise ValueError("Isochrone API response missing polygon coordinates.")
    return coordinates[0]


def _filter_markets_by_isochrone(markets: list, polygon: list) -> list:
    filtered = []
    for market in markets:
        lat = market.get("lat")
        lon = market.get("lon")
        if lat is None or lon is None:
            continue
        if _point_in_polygon((lon, lat), polygon):
            filtered.append(market)
    return filtered


def build_universe(config_path: Path, seed_csv: Path, output_path: Path) -> dict:
    """Build and write the universe JSON file."""
    config = load_simple_yaml(config_path)
    universe_source = config.get("universe_source", "seeds")
    markets = load_seed_universe(seed_csv)

    if universe_source == "api":
        api_config = config.get("api", {})
        env_var = api_config.get("env_var", "ORS_API_KEY")
        endpoint = api_config.get("endpoint", "")
        api_key = os.environ.get(env_var)
        home_base = config.get("home_base_location", {})
        lat = home_base.get("lat")
        lon = home_base.get("lon")

        if not api_key or not endpoint or lat is None or lon is None:
            universe_source = "seeds_fallback"
            print("[WARN] Missing API config or key; falling back to seed list.")
        else:
            polygon = _load_isochrone_polygon(endpoint, api_key, float(lat), float(lon), int(config.get("drive_time_minutes", 240)))
            markets = _filter_markets_by_isochrone(markets, polygon)
            for market in markets:
                market["notes"] = f"Within {config.get('drive_time_minutes', 240)} min isochrone"
                market["source"] = api_config.get("provider", "api")

    payload = {
        "home_base": config.get("home_base", "Roanoke City, VA"),
        "drive_time_minutes": config.get("drive_time_minutes", 240),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": universe_source,
        "markets": markets,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Roanoke 4-hour market universe list.")
    parser.add_argument(
        "--config",
        default="market_radar/roanoke_radar_config.yaml",
        help="Path to the Roanoke radar YAML config.",
    )
    parser.add_argument(
        "--seeds",
        default="market_radar/seeds_roanoke_4hr.csv",
        help="Seed CSV file for the Roanoke 4-hour universe.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path (defaults to config paths.universe_json).",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    seed_csv = Path(args.seeds)
    config = load_simple_yaml(config_path)
    output_path = Path(args.output or config.get("paths", {}).get("universe_json", "market_radar/roanoke_4hr_universe.json"))

    payload = build_universe(config_path, seed_csv, output_path)
    print(f"[OK] Universe built with {len(payload['markets'])} markets -> {output_path}")


if __name__ == "__main__":
    main()
