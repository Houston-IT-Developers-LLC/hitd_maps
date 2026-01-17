#!/usr/bin/env python3
"""
Scrape missing states: Rhode Island and Washington
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(line_buffering=True)

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

os.environ['AWS_ACCESS_KEY_ID'] = R2_ACCESS_KEY
os.environ['AWS_SECRET_ACCESS_KEY'] = R2_SECRET_KEY

# Configs to scrape for missing states
CONFIGS_TO_SCRAPE = [
    # Rhode Island
    "RI_STATEWIDE",
    "RI_PROVIDENCE",
    "RI_CRANSTON",
    "RI_EAST_PROVIDENCE",
    "RI_SOUTH_KINGSTOWN",
    # Washington
    "WA_STATEWIDE_V2",
    "WA_KING",
    "WA_KING_COUNTY",
    "WA_SPOKANE",
]


def run_cmd(cmd, timeout=3600):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.returncode == 0, result.stdout, result.stderr


def scrape_config(config_id):
    start = datetime.now()
    result = {"config_id": config_id, "success": False, "message": "", "file_size": 0}

    if config_id not in COUNTY_CONFIGS:
        result["message"] = "Config not found"
        return result

    try:
        cmd = [
            sys.executable,
            str(DATA_PIPELINE_DIR / "scripts" / "export_county_parcels.py"),
            config_id,
            "-o", str(GEOJSON_DIR)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd=str(DATA_PIPELINE_DIR))

        output_file = GEOJSON_DIR / f"parcels_{config_id.lower()}.geojson"
        if output_file.exists():
            size = output_file.stat().st_size
            result["file_size"] = size
            if size > 1000:
                result["success"] = True
                result["message"] = f"OK ({size / 1024 / 1024:.1f}MB)"
            else:
                result["message"] = f"Empty file ({size} bytes)"
        else:
            err = proc.stderr[:200] if proc.stderr else ""
            result["message"] = err[:60] if err else "No output"
    except subprocess.TimeoutExpired:
        result["message"] = "Timeout (1hr)"
    except Exception as e:
        result["message"] = str(e)[:60]

    result["duration"] = (datetime.now() - start).total_seconds()
    return result


def convert_to_pmtiles(geojson_path):
    pmtiles_path = str(geojson_path).replace('.geojson', '.pmtiles')
    cmd = f'tippecanoe -o {pmtiles_path} -l parcels --minimum-zoom=5 --maximum-zoom=15 --drop-densest-as-needed --extend-zooms-if-still-dropping --simplification=10 --force {geojson_path}'
    ok, _, err = run_cmd(cmd, timeout=3600)
    if ok and os.path.exists(pmtiles_path):
        return pmtiles_path
    return None


def upload_to_r2(local_path, remote_name):
    cmd = f'aws s3 cp {local_path} s3://{R2_BUCKET}/parcels/{remote_name} --endpoint-url {R2_ENDPOINT}'
    ok, _, err = run_cmd(cmd, timeout=600)
    return ok


def process_config(config_id):
    print(f"[START] {config_id}")

    result = {
        "config_id": config_id,
        "scrape_ok": False,
        "pmtiles_ok": False,
        "upload_ok": False,
        "message": ""
    }

    # Step 1: Scrape
    print(f"  [1/3] Scraping {config_id}...")
    scrape_result = scrape_config(config_id)

    if not scrape_result["success"]:
        result["message"] = f"Scrape failed: {scrape_result['message']}"
        print(f"  [FAIL] Scrape: {scrape_result['message']}")
        return result

    result["scrape_ok"] = True
    geojson_path = GEOJSON_DIR / f"parcels_{config_id.lower()}.geojson"
    print(f"  [OK] Scraped {scrape_result['file_size'] / 1024 / 1024:.1f}MB in {scrape_result['duration']:.0f}s")

    # Step 2: Convert to PMTiles
    print(f"  [2/3] Converting to PMTiles...")
    pmtiles_path = convert_to_pmtiles(geojson_path)

    if not pmtiles_path:
        result["message"] = "PMTiles conversion failed"
        print(f"  [FAIL] PMTiles conversion failed")
        return result

    result["pmtiles_ok"] = True
    pmtiles_size = os.path.getsize(pmtiles_path) / 1024 / 1024
    print(f"  [OK] PMTiles: {pmtiles_size:.1f}MB")

    # Step 3: Upload to R2
    print(f"  [3/3] Uploading to R2...")
    remote_name = f"parcels_{config_id.lower()}.pmtiles"
    if upload_to_r2(pmtiles_path, remote_name):
        result["upload_ok"] = True
        result["message"] = f"Success ({pmtiles_size:.1f}MB)"
        print(f"[DONE] {config_id} -> {remote_name}")
    else:
        result["message"] = "Upload failed"
        print(f"  [FAIL] Upload failed")

    return result


def main():
    print("=" * 70)
    print("  SCRAPE MISSING STATES: RHODE ISLAND & WASHINGTON")
    print("=" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  Configs to scrape: {len(CONFIGS_TO_SCRAPE)}")
    print("=" * 70)

    GEOJSON_DIR.mkdir(parents=True, exist_ok=True)

    # Verify configs exist
    valid_configs = [c for c in CONFIGS_TO_SCRAPE if c in COUNTY_CONFIGS]
    print(f"\n  Valid configs: {len(valid_configs)}")
    for c in valid_configs:
        print(f"    - {c}: {COUNTY_CONFIGS[c]['name']}")
    print()

    # Deploy parallel workers
    max_workers = 10
    print(f"Deploying {max_workers} parallel agents...")
    print("=" * 70 + "\n")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_config, c): c for c in valid_configs}
        for future in as_completed(futures):
            try:
                result = future.result(timeout=7200)
                results.append(result)
            except Exception as e:
                print(f"[ERR] {futures[future]}: {str(e)[:50]}")

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)

    scrape_ok = sum(1 for r in results if r.get("scrape_ok"))
    upload_ok = sum(1 for r in results if r.get("upload_ok"))

    print(f"  Configs attempted: {len(valid_configs)}")
    print(f"  Scrape OK: {scrape_ok}")
    print(f"  Upload OK: {upload_ok}")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("=" * 70)

    # Show results by state
    print("\n  Results:")
    for r in results:
        status = "OK" if r.get("upload_ok") else "FAIL"
        print(f"    {r['config_id']}: {status} - {r.get('message', '')}")


if __name__ == "__main__":
    main()
