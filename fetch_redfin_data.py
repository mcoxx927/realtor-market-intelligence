"""
Automated Redfin Data Fetcher
Downloads the latest city market tracker TSV from Redfin's S3 bucket.

Usage:
    python fetch_redfin_data.py [--force]

Options:
    --force     Download even if file exists and is recent
"""

import os
import sys
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Redfin Data Center URL for city-level market tracker
REDFIN_URL = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz"

# Output filename
OUTPUT_FILE = "city_market_tracker.tsv000.gz"

# Redfin typically releases data on Friday of the third full week of each month
# We consider data "stale" if it's older than 35 days
STALE_DAYS = 35


def get_file_info(filepath):
    """Get file size and modification date if file exists."""
    if not os.path.exists(filepath):
        return None, None

    stat = os.stat(filepath)
    mod_time = datetime.fromtimestamp(stat.st_mtime)
    size_mb = stat.st_size / (1024 * 1024)
    return mod_time, size_mb


def calculate_file_hash(filepath, block_size=65536):
    """Calculate MD5 hash of file for comparison."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            hasher.update(block)
    return hasher.hexdigest()


def is_file_stale(filepath, stale_days=STALE_DAYS):
    """Check if existing file is older than threshold."""
    mod_time, _ = get_file_info(filepath)
    if mod_time is None:
        return True

    age = datetime.now() - mod_time
    return age.days >= stale_days


def backup_existing_file(filepath):
    """Create backup of existing file before downloading new one."""
    if not os.path.exists(filepath):
        return None

    mod_time, _ = get_file_info(filepath)
    if mod_time:
        backup_name = f"{filepath}.backup_{mod_time.strftime('%Y%m%d')}"
        if not os.path.exists(backup_name):
            shutil.copy2(filepath, backup_name)
            print(f"[BACKUP] Created backup: {backup_name}")
            return backup_name
    return None


def download_with_progress(url, output_path, chunk_size=1024*1024):
    """Download file with progress indicator."""
    print(f"\n[DOWNLOAD] Starting download from Redfin S3...")
    print(f"[URL] {url}")

    try:
        # Create request with user agent
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

        with urlopen(request, timeout=300) as response:
            # Get file size if available
            total_size = response.headers.get('Content-Length')
            if total_size:
                total_size = int(total_size)
                total_mb = total_size / (1024 * 1024)
                print(f"[SIZE] Expected file size: {total_mb:.1f} MB")
            else:
                print("[SIZE] File size unknown, downloading...")

            # Download with progress
            downloaded = 0
            temp_path = output_path + ".tmp"

            with open(temp_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    f.write(chunk)
                    downloaded += len(chunk)

                    # Progress indicator
                    downloaded_mb = downloaded / (1024 * 1024)
                    if total_size:
                        pct = (downloaded / total_size) * 100
                        print(f"\r[PROGRESS] {downloaded_mb:.1f} MB / {total_mb:.1f} MB ({pct:.1f}%)", end='', flush=True)
                    else:
                        print(f"\r[PROGRESS] {downloaded_mb:.1f} MB downloaded", end='', flush=True)

            print()  # New line after progress

            # Move temp file to final location
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_path, output_path)

            final_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"[OK] Download complete: {output_path} ({final_size:.1f} MB)")
            return True

    except HTTPError as e:
        print(f"\n[ERROR] HTTP Error {e.code}: {e.reason}")
        return False
    except URLError as e:
        print(f"\n[ERROR] URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Download failed: {str(e)}")
        # Clean up temp file if it exists
        temp_path = output_path + ".tmp"
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False


def fetch_redfin_data(force=False):
    """
    Main function to fetch Redfin data.

    Args:
        force: If True, download even if file exists and is recent

    Returns:
        dict with status information
    """
    base_dir = Path(__file__).parent
    output_path = str(base_dir / OUTPUT_FILE)

    result = {
        'success': False,
        'downloaded': False,
        'file_path': output_path,
        'file_size_mb': None,
        'message': ''
    }

    print("\n" + "="*60)
    print("REDFIN DATA FETCHER")
    print("="*60)

    # Check existing file
    mod_time, size_mb = get_file_info(output_path)

    if mod_time:
        print(f"\n[INFO] Existing file found:")
        print(f"       Modified: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"       Size: {size_mb:.1f} MB")

        if not force and not is_file_stale(output_path):
            age_days = (datetime.now() - mod_time).days
            print(f"\n[SKIP] File is only {age_days} days old (threshold: {STALE_DAYS} days)")
            print("       Use --force to download anyway")
            result['success'] = True
            result['downloaded'] = False
            result['file_size_mb'] = size_mb
            result['message'] = f"Using existing file ({age_days} days old)"
            return result
        else:
            if force:
                print("\n[INFO] Force flag set, downloading fresh copy...")
            else:
                age_days = (datetime.now() - mod_time).days
                print(f"\n[INFO] File is {age_days} days old, downloading fresh copy...")
    else:
        print("\n[INFO] No existing file found, downloading...")

    # Backup existing file
    backup_existing_file(output_path)

    # Download new file
    if download_with_progress(REDFIN_URL, output_path):
        _, new_size = get_file_info(output_path)
        result['success'] = True
        result['downloaded'] = True
        result['file_size_mb'] = new_size
        result['message'] = f"Downloaded successfully ({new_size:.1f} MB)"

        print(f"\n[OK] Redfin data ready: {output_path}")
    else:
        result['message'] = "Download failed"

        # Restore from backup if available
        backup_files = sorted(Path(base_dir).glob(f"{OUTPUT_FILE}.backup_*"), reverse=True)
        if backup_files:
            print(f"\n[RESTORE] Restoring from latest backup...")
            shutil.copy2(str(backup_files[0]), output_path)
            _, restored_size = get_file_info(output_path)
            result['success'] = True
            result['file_size_mb'] = restored_size
            result['message'] = f"Download failed, restored from backup ({restored_size:.1f} MB)"

    return result


def main():
    """Command-line entry point."""
    force = '--force' in sys.argv or '-f' in sys.argv

    result = fetch_redfin_data(force=force)

    print("\n" + "="*60)
    if result['success']:
        print("[OK] FETCH COMPLETE")
        if result['downloaded']:
            print("     New data downloaded and ready for processing")
        else:
            print("     Using existing data file")
    else:
        print("[FAILED] FETCH FAILED")
        print(f"     {result['message']}")
    print("="*60)

    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
