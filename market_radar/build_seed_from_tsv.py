"""
One-time utility to extract all unique metros from the Redfin TSV
and generate/update the seed CSV file.

Run this yearly (or when you suspect new metros were added) to refresh the seed list.

Usage:
    python market_radar/build_seed_from_tsv.py
    python market_radar/build_seed_from_tsv.py --output market_radar/seeds_roanoke_4hr.csv
"""

import argparse
import csv
import gzip
from pathlib import Path

import pandas as pd


def extract_metros_from_tsv(tsv_path: Path) -> list:
    """Extract unique metros from the Redfin TSV file."""
    print(f"[INFO] Reading {tsv_path}...")

    # Read only the columns we need to save memory
    cols_to_read = ["PARENT_METRO_REGION", "PARENT_METRO_REGION_METRO_CODE"]

    df = pd.read_csv(
        tsv_path,
        sep="\t",
        compression="gzip",
        usecols=cols_to_read,
        low_memory=False
    )

    # Get unique metros
    metros = df.drop_duplicates().dropna()

    print(f"[INFO] Found {len(metros)} unique metros")

    results = []
    for _, row in metros.iterrows():
        name = str(row["PARENT_METRO_REGION"]).strip()
        code = str(row["PARENT_METRO_REGION_METRO_CODE"]).strip()

        # Skip invalid entries
        if not name or not code or code == "nan":
            continue

        # Parse state from metro name (e.g., "Charlotte-Concord-Gastonia, NC-SC" -> "NC-SC")
        state = ""
        if ", " in name:
            parts = name.rsplit(", ", 1)
            state = parts[1] if len(parts) > 1 else ""
            market_name = parts[0]
        else:
            market_name = name

        results.append({
            "market_name": market_name,
            "state": state,
            "metro_code": code,
            "display_name": name,
            "lat": "",  # User fills in manually
            "lon": "",  # User fills in manually
        })

    # Sort by market name
    results.sort(key=lambda x: x["market_name"])
    return results


def load_existing_seed(seed_path: Path) -> dict:
    """Load existing seed CSV to preserve manually-added lat/lon."""
    if not seed_path.exists():
        return {}

    existing = {}
    with seed_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("metro_code", "").strip()
            if code:
                existing[code] = row

    print(f"[INFO] Loaded {len(existing)} existing entries from {seed_path}")
    return existing


def merge_and_write(metros: list, existing: dict, output_path: Path) -> None:
    """Merge new metros with existing (preserving lat/lon) and write CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    merged = []
    new_count = 0

    for metro in metros:
        code = metro["metro_code"]

        if code in existing:
            # Preserve existing lat/lon and notes
            old = existing[code]
            metro["lat"] = old.get("lat", "")
            metro["lon"] = old.get("lon", "")
            metro["notes"] = old.get("notes", "")
            metro["source"] = old.get("source", "tsv_extract")
        else:
            metro["notes"] = "New from TSV - needs lat/lon"
            metro["source"] = "tsv_extract"
            new_count += 1

        # Add default fields
        metro.setdefault("preferred_region_type", "metro")
        metro.setdefault("output_directory", "")

        merged.append(metro)

    # Write CSV
    fieldnames = [
        "market_name", "state", "preferred_region_type", "metro_code",
        "display_name", "output_directory", "lat", "lon", "notes", "source"
    ]

    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)

    print(f"[OK] Wrote {len(merged)} metros to {output_path}")
    print(f"     New metros added: {new_count}")
    print(f"     Metros with lat/lon: {sum(1 for m in merged if m.get('lat'))}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract metros from Redfin TSV and update seed CSV"
    )
    parser.add_argument(
        "--tsv",
        default="city_market_tracker.tsv000.gz",
        help="Path to Redfin TSV file"
    )
    parser.add_argument(
        "--output",
        default="market_radar/all_metros_seed.csv",
        help="Output seed CSV path"
    )
    parser.add_argument(
        "--merge-existing",
        default=None,
        help="Existing seed CSV to merge (preserves lat/lon)"
    )
    args = parser.parse_args()

    tsv_path = Path(args.tsv)
    output_path = Path(args.output)

    if not tsv_path.exists():
        print(f"[ERROR] TSV file not found: {tsv_path}")
        return 1

    # Extract metros from TSV
    metros = extract_metros_from_tsv(tsv_path)

    # Load existing seed to preserve lat/lon
    existing = {}
    if args.merge_existing:
        existing = load_existing_seed(Path(args.merge_existing))
    elif output_path.exists():
        existing = load_existing_seed(output_path)

    # Merge and write
    merge_and_write(metros, existing, output_path)

    print("\n[NEXT STEPS]")
    print("1. Open the CSV and add lat/lon for metros in your target region")
    print("2. Copy relevant rows to your regional seed file (e.g., seeds_roanoke_4hr.csv)")
    print("3. Or update roanoke_radar_config.yaml to point to this file")

    return 0


if __name__ == "__main__":
    exit(main())
