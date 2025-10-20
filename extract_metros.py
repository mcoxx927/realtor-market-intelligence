"""
Metro Extraction Script
Extracts metro-specific data from raw Redfin city_market_tracker TSV file.
Reads configuration from metro_config.json to support multiple metros.
"""

import pandas as pd
import gzip
import json
from pathlib import Path
import sys

def load_config(config_path: str = 'metro_config.json') -> dict:
    """Load metro configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)

def extract_metro(source_file: str, metro_code: str, output_file: str, property_type: str = 'All Residential'):
    """
    Extract a single metro's data from the source TSV file.

    Args:
        source_file: Path to city_market_tracker.tsv000.gz
        metro_code: Metro code to filter (e.g., '16740' for Charlotte)
        output_file: Path to output filtered TSV file
        property_type: Property type to filter (default: 'All Residential')
    """
    print(f"\n[EXTRACTING] Metro Code: {metro_code}")
    print(f"  Source: {source_file}")
    print(f"  Output: {output_file}")

    # Open gzipped file and read in chunks to manage memory
    chunk_size = 50000
    filtered_chunks = []
    total_rows = 0
    filtered_rows = 0

    try:
        with gzip.open(source_file, 'rt', encoding='utf-8') as f:
            # Read in chunks
            for chunk_num, chunk in enumerate(pd.read_csv(f, sep='\t', chunksize=chunk_size, low_memory=False)):
                total_rows += len(chunk)

                # Filter by metro code and property type
                filtered = chunk[
                    (chunk['parent_metro_region_metro_code'].astype(str) == str(metro_code)) &
                    (chunk['property_type'] == property_type)
                ]

                if len(filtered) > 0:
                    filtered_chunks.append(filtered)
                    filtered_rows += len(filtered)

                # Progress indicator
                if (chunk_num + 1) % 10 == 0:
                    print(f"  Processed {total_rows:,} rows, found {filtered_rows:,} matches...")

        if not filtered_chunks:
            print(f"  [WARNING] No data found for metro code {metro_code}")
            return False

        # Combine all filtered chunks
        result_df = pd.concat(filtered_chunks, ignore_index=True)

        # Sort by period (most recent first)
        result_df = result_df.sort_values('period', ascending=False)

        # Write to output file
        result_df.to_csv(output_file, sep='\t', index=False)

        # Summary statistics
        unique_cities = result_df['region'].nunique()
        date_range = f"{result_df['period'].min()} to {result_df['period'].max()}"

        print(f"  [OK] Extraction complete:")
        print(f"       Total rows: {len(result_df):,}")
        print(f"       Unique cities: {unique_cities}")
        print(f"       Date range: {date_range}")

        return True

    except FileNotFoundError:
        print(f"  [ERROR] Source file not found: {source_file}")
        return False
    except Exception as e:
        print(f"  [ERROR] Extraction failed: {str(e)}")
        return False

def main():
    """Main extraction workflow."""
    print("=" * 80)
    print("METRO EXTRACTION PIPELINE")
    print("=" * 80)

    # Load configuration
    try:
        config = load_config()
        print(f"\n[CONFIG] Loaded metro_config.json")
        print(f"  Enabled metros: {sum(1 for m in config['metros'] if m.get('enabled', True))}")
    except FileNotFoundError:
        print("[ERROR] metro_config.json not found")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to load config: {str(e)}")
        sys.exit(1)

    # Get data settings
    data_settings = config.get('data_settings', {})
    source_file = data_settings.get('source_file', 'city_market_tracker.tsv000.gz')
    property_type = data_settings.get('property_type_filter', 'All Residential')
    output_pattern = data_settings.get('output_file_pattern', '{name}_cities_filtered.tsv')

    # Check if source file exists
    if not Path(source_file).exists():
        print(f"\n[ERROR] Source file not found: {source_file}")
        print("Please download the latest city_market_tracker.tsv000.gz from Redfin")
        sys.exit(1)

    # Extract each enabled metro
    success_count = 0
    fail_count = 0

    for metro in config['metros']:
        if not metro.get('enabled', True):
            print(f"\n[SKIPPED] {metro['display_name']} (disabled in config)")
            continue

        # Build output file path
        output_file = output_pattern.format(name=metro['name'])

        # Extract metro data
        success = extract_metro(
            source_file=source_file,
            metro_code=metro['metro_code'],
            output_file=output_file,
            property_type=property_type
        )

        if success:
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")

    if fail_count > 0:
        print("\n[WARNING] Some extractions failed. Check errors above.")
        sys.exit(1)
    else:
        print("\n[OK] ALL METROS EXTRACTED SUCCESSFULLY")

if __name__ == '__main__':
    main()
