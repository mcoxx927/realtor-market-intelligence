"""
Master Automation Script for Real Estate Market Analysis
Runs the complete pipeline: Metro Extraction -> Data Processing -> Dashboard Generation
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name):
    """Run a Python script and check for errors"""
    print(f"\n{'='*60}")
    print(f"RUNNING: {script_name}")
    print('='*60)

    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=False,
        text=True
    )

    if result.returncode != 0:
        print(f"\n[ERROR] {script_name} failed with return code {result.returncode}")
        sys.exit(1)

    print(f"\n[OK] {script_name} completed successfully")
    return result.returncode

def main():
    """Run the complete market analysis pipeline"""

    base_dir = Path(__file__).parent

    print("\n" + "="*60)
    print("REAL ESTATE MARKET ANALYSIS PIPELINE")
    print("="*60)

    # Step 1: Extract metros from raw TSV file
    run_script(str(base_dir / 'extract_metros.py'))

    # Step 2: Process market data
    run_script(str(base_dir / 'process_market_data.py'))

    # Step 3: Generate enhanced dashboards
    run_script(str(base_dir / 'generate_dashboards_v2.py'))

    print("\n" + "="*60)
    print("[OK] PIPELINE COMPLETE!")
    print("="*60)
    print("\nExtracted Files:")
    print("  - charlotte_cities_filtered.tsv")
    print("  - roanoke_cities_filtered.tsv")
    print("\nGenerated Files:")
    print("  - charlotte/2025-09/charlotte_data.json")
    print("  - charlotte/2025-09/dashboard_enhanced_charlotte_2025-09.html")
    print("  - roanoke/2025-09/roanoke_data.json")
    print("  - roanoke/2025-09/dashboard_enhanced_roanoke_2025-09.html")
    print("\nTo add new metros:")
    print("  1. Edit metro_config.json to add new metro definitions")
    print("  2. Re-run this pipeline")
    print("\nNext: Use the agent to analyze the data and generate reports")

if __name__ == '__main__':
    main()
