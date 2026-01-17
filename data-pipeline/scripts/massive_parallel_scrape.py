#!/usr/bin/env python3
"""
Massive Parallel Scrape - Launch ALL missing configs simultaneously
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.config import Config

sys.path.insert(0, str(Path(__file__).parent))
from export_county_parcels import COUNTY_CONFIGS

DATA_PIPELINE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"
GEOJSON_DIR = OUTPUT_DIR / "geojson"

# R2 config
R2_ENDPOINT = 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com'
R2_ACCESS_KEY = 'ecd653afe3300fdc045b9980df0dbb14'
R2_SECRET_KEY = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'
R2_BUCKET = 'gspot-tiles'


def get_r2_existing():
    """Get set of config IDs already in R2."""
    client = boto3.client('s3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version='s3v4'))

    paginator = client.get_paginator('list_objects_v2')
    existing = set()
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix='parcels/'):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if 'parcels_' in key and key.endswith('.pmtiles'):
                config_id = key.split('parcels_')[1].replace('.pmtiles', '').upper()
                existing.add(config_id)
    return existing


def run_scrape(config_id: str) -> dict:
    """Run a single scrape."""
    start = datetime.now()
    result = {"config_id": config_id, "success": False, "message": ""}

    try:
        cmd = [
            sys.executable,
            str(DATA_PIPELINE_DIR / "scripts" / "export_county_parcels.py"),
            config_id,
            "-o", str(GEOJSON_DIR)
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            cwd=str(DATA_PIPELINE_DIR)
        )

        if proc.returncode == 0:
            result["success"] = True
            result["message"] = "OK"
        else:
            err = proc.stderr[:200] if proc.stderr else ""
            if "403" in err or "401" in err:
                result["message"] = "Access denied"
            elif "404" in err:
                result["message"] = "Not found"
            elif "timeout" in err.lower():
                result["message"] = "Timeout"
            else:
                result["message"] = err[:60] if err else "Error"

    except subprocess.TimeoutExpired:
        result["message"] = "Timeout (1hr)"
    except Exception as e:
        result["message"] = str(e)[:60]

    result["duration"] = (datetime.now() - start).total_seconds()
    return result


def main():
    print("=" * 70)
    print("  MASSIVE PARALLEL SCRAPE - ALL MISSING CONFIGS")
    print("=" * 70)
    print(f"  Started: {datetime.now().isoformat()}")

    GEOJSON_DIR.mkdir(parents=True, exist_ok=True)

    # Get missing configs
    print("\nChecking R2 for existing files...")
    existing = get_r2_existing()

    missing = []
    for config_id in COUNTY_CONFIGS.keys():
        if config_id not in existing:
            # Skip if local file exists
            local_file = GEOJSON_DIR / f"parcels_{config_id.lower()}.geojson"
            if not (local_file.exists() and local_file.stat().st_size > 1000):
                missing.append(config_id)

    print(f"  Total configs: {len(COUNTY_CONFIGS)}")
    print(f"  Already in R2: {len(existing)}")
    print(f"  To scrape: {len(missing)}")
    print("=" * 70)

    if not missing:
        print("Nothing to scrape!")
        return

    # MAXIMUM PARALLELISM - 40 workers (leave some CPU headroom)
    max_workers = 40
    print(f"\nLaunching {max_workers} parallel workers for {len(missing)} configs...")
    print("=" * 70)

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_scrape, cfg): cfg for cfg in missing}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            try:
                result = future.result(timeout=3700)
                results.append(result)

                status = "OK" if result["success"] else "FAIL"
                dur = result.get("duration", 0)
                msg = result.get("message", "")[:30]
                print(f"[{completed:3}/{len(missing)}] {status:4} {result['config_id']:25} ({dur:5.0f}s) {msg}")

            except Exception as e:
                print(f"[{completed:3}/{len(missing)}] ERR  ({str(e)[:40]})")

    # Summary
    successful = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 70)
    print("  SCRAPE SUMMARY")
    print("=" * 70)
    print(f"  Attempted: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(results) - successful}")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("=" * 70)

    # Show new files
    new_files = list(GEOJSON_DIR.glob("parcels_*.geojson"))
    total_size = sum(f.stat().st_size for f in new_files) / 1024**3
    print(f"\n  GeoJSON files: {len(new_files)} ({total_size:.1f} GB)")


if __name__ == "__main__":
    main()
