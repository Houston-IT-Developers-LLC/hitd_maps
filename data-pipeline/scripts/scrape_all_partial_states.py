#!/usr/bin/env python3
"""
Scrape All Partial States - Fill in missing county data

Scrapes all available county configs for states that have incomplete coverage,
then processes through PMTiles and uploads to R2.
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.config import Config

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))
from export_county_parcels import COUNTY_CONFIGS

DATA_PIPELINE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"

# R2 configuration
R2_ENDPOINT = 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com'
R2_ACCESS_KEY = 'ecd653afe3300fdc045b9980df0dbb14'
R2_SECRET_KEY = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'
R2_BUCKET = 'gspot-tiles'

# Partial states to scrape (sorted by largest gap first)
PARTIAL_STATES = [
    'GA',  # 159 counties, 5% covered - highest priority
    'KY',  # 120 counties, 1.7% covered
    'MO',  # 115 counties, 5.2% covered
    'KS',  # 105 counties, 2.9% covered
    'IL',  # 102 counties, 6.9% covered
    'MI',  # 83 counties, 10.8% covered
    'NE',  # 93 counties, 1.1% covered
    'MS',  # 82 counties, 1.2% covered
    'OK',  # 77 counties, 2.6% covered
    'AL',  # 67 counties, 4.5% covered
    'SD',  # 66 counties, 4.5% covered
    'LA',  # 64 counties, 7.8% covered
    'MN',  # 87 counties, 4.6% covered
    'SC',  # 46 counties, 13% covered
    'OR',  # 36 counties, 13.9% covered
    'AK',  # 30 counties, 16.7% covered
    'WY',  # 23 counties, 8.7% covered
    'AZ',  # 15 counties, 33% covered
    'RI',  # 5 counties, 40% covered
]


def get_r2_client():
    """Get R2 client."""
    return boto3.client('s3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version='s3v4')
    )


def file_exists_in_r2(key: str) -> bool:
    """Check if file exists in R2."""
    try:
        client = get_r2_client()
        client.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False


def get_configs_to_scrape():
    """Get all configs for partial states that aren't already in R2."""
    configs_to_scrape = []

    for config_id, config in COUNTY_CONFIGS.items():
        state = config_id.split('_')[0]
        if state not in PARTIAL_STATES:
            continue

        # Check if already in R2
        r2_key = f"parcels/parcels_{config_id.lower()}.pmtiles"
        if file_exists_in_r2(r2_key):
            print(f"  [skip] {config_id} already in R2")
            continue

        # Check if local GeoJSON exists
        geojson_path = GEOJSON_DIR / f"parcels_{config_id.lower()}.geojson"
        if geojson_path.exists() and geojson_path.stat().st_size > 1000:
            print(f"  [local] {config_id} has local GeoJSON")

        configs_to_scrape.append(config_id)

    return configs_to_scrape


def run_scrape(config_id: str) -> dict:
    """Run a single scrape."""
    start = datetime.now()
    result = {
        "config_id": config_id,
        "success": False,
        "message": ""
    }

    try:
        cmd = [
            sys.executable,
            str(DATA_PIPELINE_DIR / "scripts" / "export_county_parcels.py"),
            config_id
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200,  # 2 hour timeout
            cwd=str(DATA_PIPELINE_DIR)
        )

        if proc.returncode == 0:
            result["success"] = True
            result["message"] = "Scraped successfully"
        else:
            result["message"] = proc.stderr[:200] if proc.stderr else "Unknown error"

    except subprocess.TimeoutExpired:
        result["message"] = "Timeout after 2 hours"
    except Exception as e:
        result["message"] = str(e)[:200]

    result["duration"] = (datetime.now() - start).total_seconds()
    return result


def main():
    """Main entry point."""
    print("=" * 70)
    print("  SCRAPE ALL PARTIAL STATES")
    print("=" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  Target states: {', '.join(PARTIAL_STATES)}")
    print("=" * 70)

    # Ensure directories exist
    GEOJSON_DIR.mkdir(parents=True, exist_ok=True)
    PMTILES_DIR.mkdir(parents=True, exist_ok=True)

    # Get configs to scrape
    print("\nChecking what needs to be scraped...")
    configs = get_configs_to_scrape()

    print(f"\n{len(configs)} configs need scraping")
    print("=" * 70)

    if not configs:
        print("Nothing to scrape!")
        return

    # Scrape in parallel
    max_workers = 16  # Aggressive parallelism
    results = []

    print(f"\nStarting {max_workers} parallel workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_scrape, cfg): cfg for cfg in configs}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            try:
                result = future.result(timeout=7200)
                results.append(result)

                status = "OK" if result["success"] else "FAIL"
                duration = result.get("duration", 0)
                print(f"[{completed}/{len(configs)}] {status} {result['config_id']} ({duration:.0f}s)")

                if not result["success"]:
                    print(f"         Error: {result['message'][:60]}")

            except Exception as e:
                print(f"[{completed}/{len(configs)}] ERROR: {e}")

    # Summary
    successful = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 70)
    print("  SCRAPE SUMMARY")
    print("=" * 70)
    print(f"  Total configs: {len(configs)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(configs) - successful}")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("=" * 70)

    # List new GeoJSON files
    new_files = list(GEOJSON_DIR.glob("parcels_*.geojson"))
    print(f"\n  GeoJSON files ready: {len(new_files)}")

    return results


if __name__ == "__main__":
    main()
