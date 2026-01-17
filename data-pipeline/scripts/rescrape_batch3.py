#!/usr/bin/env python3
"""
Batch 3: Additional parallel workers - remaining files
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.config import Config

sys.stdout.reconfigure(line_buffering=True)

sys.path.insert(0, str(Path(__file__).parent))
from export_county_parcels import COUNTY_CONFIGS

DATA_PIPELINE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"
GEOJSON_DIR = OUTPUT_DIR / "geojson"

R2_ENDPOINT = 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com'
R2_ACCESS_KEY = 'ecd653afe3300fdc045b9980df0dbb14'
R2_SECRET_KEY = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'
R2_BUCKET = 'gspot-tiles'

os.environ['AWS_ACCESS_KEY_ID'] = R2_ACCESS_KEY
os.environ['AWS_SECRET_ACCESS_KEY'] = R2_SECRET_KEY

# Batch 3: Oregon, South Carolina, and remaining stragglers
BATCH3_FILES = [
    # Oregon
    "parcels_or_benton.geojson",
    "parcels_or_clackamas.geojson",
    "parcels_or_deschutes.geojson",
    "parcels_or_douglas.geojson",
    "parcels_or_lane.geojson",
    "parcels_or_marion.geojson",
    "parcels_or_multnomah.geojson",
    "parcels_or_statewide.geojson",
    "parcels_or_washington.geojson",
    # South Carolina
    "parcels_sc_charleston.geojson",
    "parcels_sc_dorchester.geojson",
    "parcels_sc_greenville.geojson",
    "parcels_sc_horry.geojson",
    "parcels_sc_lexington.geojson",
    "parcels_sc_richland.geojson",
    "parcels_sc_spartanburg.geojson",
    "parcels_sc_york.geojson",
    # California remaining
    "parcels_ca_alameda.geojson",
    "parcels_ca_fresno.geojson",
    "parcels_ca_los_angeles_v2.geojson",
    "parcels_ca_orange.geojson",
    "parcels_ca_riverside.geojson",
    "parcels_ca_sacramento.geojson",
    "parcels_ca_san_diego.geojson",
    "parcels_ca_san_francisco.geojson",
    "parcels_ca_sonoma.geojson",
    "parcels_ca_zoning_statewide.geojson",
    # Colorado
    "parcels_co_el_paso_v2.geojson",
    "parcels_co_statewide.geojson",
    # Connecticut
    "parcels_ct_statewide.geojson",
    # Florida
    "parcels_fl_statewide.geojson",
]


def get_config_id_from_filename(filename):
    base = filename.replace('.geojson', '').replace('parcels_', '')
    return base.upper()


def find_matching_config(config_id):
    if config_id in COUNTY_CONFIGS:
        return config_id
    for suffix in ['_V2', '_V3', '_STATEWIDE', '_STATEWIDE_V2']:
        alt = config_id + suffix
        if alt in COUNTY_CONFIGS:
            return alt
    for suffix in ['_V2', '_V3']:
        if config_id.endswith(suffix):
            base = config_id[:-len(suffix)]
            if base in COUNTY_CONFIGS:
                return base
    return None


def run_cmd(cmd, timeout=3600):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.returncode == 0, result.stdout, result.stderr


def scrape_config(config_id):
    start = datetime.now()
    result = {"config_id": config_id, "success": False, "message": "", "file_size": 0}
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


def process_file(filename):
    config_id = get_config_id_from_filename(filename)
    actual_config = find_matching_config(config_id)

    result = {
        "filename": filename,
        "config_id": config_id,
        "actual_config": actual_config,
        "scrape_ok": False,
        "pmtiles_ok": False,
        "upload_ok": False,
        "message": ""
    }

    cfg_lower = actual_config.lower() if actual_config else config_id.lower()
    output_file = GEOJSON_DIR / f"parcels_{cfg_lower}.geojson"
    pmtiles_file = GEOJSON_DIR / f"parcels_{cfg_lower}.pmtiles"

    # Check if already uploaded
    if pmtiles_file.exists() and pmtiles_file.stat().st_size > 1000:
        print(f"[SKIP] {filename}: Already converted")
        return result

    # Check if already scraped
    if output_file.exists() and output_file.stat().st_size > 1000:
        print(f"[RESUME] {filename}: Converting existing file")
        result["scrape_ok"] = True
        print(f"  [2/3] Converting to PMTiles...")
        pmtiles_path = convert_to_pmtiles(output_file)
        if pmtiles_path:
            result["pmtiles_ok"] = True
            pmtiles_size = os.path.getsize(pmtiles_path) / 1024 / 1024
            print(f"  [3/3] Uploading to R2...")
            remote_name = f"parcels_{cfg_lower}.pmtiles"
            if upload_to_r2(pmtiles_path, remote_name):
                result["upload_ok"] = True
                result["message"] = f"Success ({pmtiles_size:.1f}MB)"
                print(f"[DONE] {filename} -> {remote_name}")
        return result

    if not actual_config:
        result["message"] = "No config found"
        print(f"[SKIP] {filename}: No matching config for {config_id}")
        return result

    print(f"[START] {filename} -> config {actual_config}")

    print(f"  [1/3] Scraping {actual_config}...")
    scrape_result = scrape_config(actual_config)

    if not scrape_result["success"]:
        result["message"] = f"Scrape failed: {scrape_result['message']}"
        print(f"  [FAIL] Scrape: {scrape_result['message']}")
        return result

    result["scrape_ok"] = True
    geojson_path = GEOJSON_DIR / f"parcels_{actual_config.lower()}.geojson"
    print(f"  [OK] Scraped {scrape_result['file_size'] / 1024 / 1024:.1f}MB in {scrape_result['duration']:.0f}s")

    print(f"  [2/3] Converting to PMTiles...")
    pmtiles_path = convert_to_pmtiles(geojson_path)

    if not pmtiles_path:
        result["message"] = "PMTiles conversion failed"
        print(f"  [FAIL] PMTiles conversion failed")
        return result

    result["pmtiles_ok"] = True
    pmtiles_size = os.path.getsize(pmtiles_path) / 1024 / 1024
    print(f"  [OK] PMTiles: {pmtiles_size:.1f}MB")

    print(f"  [3/3] Uploading to R2...")
    remote_name = f"parcels_{actual_config.lower()}.pmtiles"
    if upload_to_r2(pmtiles_path, remote_name):
        result["upload_ok"] = True
        result["message"] = f"Success ({pmtiles_size:.1f}MB)"
        print(f"[DONE] {filename} -> {remote_name}")
    else:
        result["message"] = "Upload failed"
        print(f"  [FAIL] Upload failed")

    return result


def main():
    print("=" * 70)
    print("  BATCH 3: ADDITIONAL PARALLEL WORKERS (OR/SC/CA/CO/CT/FL)")
    print("=" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  Files to process: {len(BATCH3_FILES)}")
    print("=" * 70)

    GEOJSON_DIR.mkdir(parents=True, exist_ok=True)

    max_workers = 30  # More workers
    print(f"\nDeploying {max_workers} parallel agents for {len(BATCH3_FILES)} files...")
    print("=" * 70 + "\n")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, f): f for f in BATCH3_FILES}
        for future in as_completed(futures):
            try:
                result = future.result(timeout=7200)
                results.append(result)
            except Exception as e:
                print(f"[ERR] {futures[future]}: {str(e)[:50]}")

    print("\n" + "=" * 70)
    print("  BATCH 3 SUMMARY")
    print("=" * 70)
    upload_ok = sum(1 for r in results if r.get("upload_ok"))
    print(f"  Total files: {len(BATCH3_FILES)}")
    print(f"  Upload OK: {upload_ok}")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
