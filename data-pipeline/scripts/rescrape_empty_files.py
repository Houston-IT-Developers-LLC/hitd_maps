#!/usr/bin/env python3
"""
Rescrape Empty Files - Deploy parallel agents to scrape all 89 empty files.
Downloads fresh data from ArcGIS APIs, converts to PMTiles, and uploads to R2.
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.config import Config
import tempfile
import json

# Unbuffered output
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

# Set env vars for AWS CLI
os.environ['AWS_ACCESS_KEY_ID'] = R2_ACCESS_KEY
os.environ['AWS_SECRET_ACCESS_KEY'] = R2_SECRET_KEY

# Files that had "no coordinates found" errors - need fresh scrape
EMPTY_FILES = [
    # Alaska
    "parcels_ak_fairbanks.geojson",
    "parcels_ak_juneau.geojson",
    # Arizona
    "parcels_az_apache.geojson",
    "parcels_az_navajo.geojson",
    "parcels_az_pima.geojson",
    "parcels_az_pinal.geojson",
    # California
    "parcels_ca_fresno.geojson",
    "parcels_ca_los_angeles_v2.geojson",
    "parcels_ca_orange.geojson",
    "parcels_ca_riverside.geojson",
    "parcels_ca_sacramento.geojson",
    "parcels_ca_san_diego.geojson",
    "parcels_ca_sonoma.geojson",
    "parcels_ca_zoning_statewide.geojson",
    # Colorado
    "parcels_co_adams_v2.geojson",
    "parcels_co_arapahoe_v2.geojson",
    "parcels_co_el_paso_v2.geojson",
    "parcels_co_statewide.geojson",
    # Connecticut
    "parcels_ct_statewide.geojson",
    # Florida
    "parcels_fl_statewide.geojson",
    # North Carolina
    "parcels_nc_buncombe.geojson",
    "parcels_nc_cumberland.geojson",
    "parcels_nc_durham.geojson",
    "parcels_nc_forsyth.geojson",
    "parcels_nc_guilford.geojson",
    "parcels_nc_mecklenburg.geojson",
    "parcels_nc_new_hanover.geojson",
    "parcels_nc_pitt.geojson",
    "parcels_nc_statewide.geojson",
    "parcels_nc_wake.geojson",
    # Nevada
    "parcels_nv_clark.geojson",
    "parcels_nv_statewide.geojson",
    "parcels_nv_washoe.geojson",
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
    # South Dakota
    "parcels_sd_beadle.geojson",
    "parcels_sd_clark.geojson",
    "parcels_sd_codington.geojson",
    "parcels_sd_deuel.geojson",
    "parcels_sd_edmunds.geojson",
    "parcels_sd_grant.geojson",
    "parcels_sd_hamlin.geojson",
    "parcels_sd_hand.geojson",
    "parcels_sd_kingsbury.geojson",
    "parcels_sd_lincoln.geojson",
    "parcels_sd_minnehaha.geojson",
    "parcels_sd_miner.geojson",
    "parcels_sd_moody.geojson",
    "parcels_sd_pennington.geojson",
    "parcels_sd_roberts.geojson",
    "parcels_sd_sioux_falls.geojson",
    # Utah
    "parcels_ut_cache.geojson",
    "parcels_ut_davis.geojson",
    "parcels_ut_salt_lake.geojson",
    "parcels_ut_statewide.geojson",
    "parcels_ut_utah.geojson",
    "parcels_ut_washington.geojson",
    "parcels_ut_weber.geojson",
    # Virginia
    "parcels_va_albemarle.geojson",
    "parcels_va_arlington.geojson",
    "parcels_va_fairfax.geojson",
    "parcels_va_henrico.geojson",
    "parcels_va_loudoun.geojson",
    "parcels_va_prince_william.geojson",
    "parcels_va_statewide.geojson",
    "parcels_va_virginia_beach.geojson",
    # Vermont
    "parcels_vt_statewide.geojson",
    # Washington
    "parcels_wa_king.geojson",
    "parcels_wa_spokane.geojson",
    "parcels_wa_statewide.geojson",
    # West Virginia
    "parcels_wv_kanawha.geojson",
    "parcels_wv_statewide.geojson",
    # Wyoming
    "parcels_wy_campbell.geojson",
    "parcels_wy_fremont.geojson",
    "parcels_wy_laramie.geojson",
    "parcels_wy_lincoln.geojson",
    "parcels_wy_park.geojson",
    "parcels_wy_sheridan.geojson",
    "parcels_wy_statewide.geojson",
    "parcels_wy_teton.geojson",
]


def get_config_id_from_filename(filename):
    """Convert filename to config ID."""
    # parcels_tx_harris.geojson -> TX_HARRIS
    base = filename.replace('.geojson', '').replace('parcels_', '')
    return base.upper()


def find_matching_config(config_id):
    """Find a matching config in COUNTY_CONFIGS."""
    # Direct match
    if config_id in COUNTY_CONFIGS:
        return config_id

    # Try with _V2, _V3 suffix
    for suffix in ['_V2', '_V3', '_STATEWIDE', '_STATEWIDE_V2']:
        alt = config_id + suffix
        if alt in COUNTY_CONFIGS:
            return alt

    # Try removing _V2, _V3 suffix
    for suffix in ['_V2', '_V3']:
        if config_id.endswith(suffix):
            base = config_id[:-len(suffix)]
            if base in COUNTY_CONFIGS:
                return base

    return None


def run_cmd(cmd, timeout=3600):
    """Run a shell command."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.returncode == 0, result.stdout, result.stderr


def scrape_config(config_id):
    """Scrape a single config."""
    start = datetime.now()
    result = {"config_id": config_id, "success": False, "message": "", "file_size": 0}

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
            timeout=3600,
            cwd=str(DATA_PIPELINE_DIR)
        )

        # Check if file was created
        output_file = GEOJSON_DIR / f"parcels_{config_id.lower()}.geojson"
        if output_file.exists():
            size = output_file.stat().st_size
            result["file_size"] = size
            if size > 1000:  # More than 1KB = valid data
                result["success"] = True
                result["message"] = f"OK ({size / 1024 / 1024:.1f}MB)"
            else:
                result["message"] = f"Empty file ({size} bytes)"
        else:
            err = proc.stderr[:200] if proc.stderr else ""
            if "403" in err or "401" in err:
                result["message"] = "Access denied"
            elif "404" in err:
                result["message"] = "Not found"
            elif "timeout" in err.lower():
                result["message"] = "Timeout"
            else:
                result["message"] = err[:60] if err else "No output"

    except subprocess.TimeoutExpired:
        result["message"] = "Timeout (1hr)"
    except Exception as e:
        result["message"] = str(e)[:60]

    result["duration"] = (datetime.now() - start).total_seconds()
    return result


def convert_to_pmtiles(geojson_path):
    """Convert GeoJSON to PMTiles."""
    pmtiles_path = str(geojson_path).replace('.geojson', '.pmtiles')

    cmd = f'tippecanoe -o {pmtiles_path} -l parcels ' \
          f'--minimum-zoom=5 --maximum-zoom=15 ' \
          f'--drop-densest-as-needed --extend-zooms-if-still-dropping ' \
          f'--simplification=10 --force {geojson_path}'

    ok, _, err = run_cmd(cmd, timeout=3600)
    if ok and os.path.exists(pmtiles_path):
        return pmtiles_path
    return None


def upload_to_r2(local_path, remote_name):
    """Upload file to R2."""
    cmd = f'aws s3 cp {local_path} s3://{R2_BUCKET}/parcels/{remote_name} --endpoint-url {R2_ENDPOINT}'
    ok, _, err = run_cmd(cmd, timeout=600)
    return ok


def process_file(filename):
    """Full pipeline: scrape -> convert -> upload."""
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

    if not actual_config:
        result["message"] = "No config found"
        print(f"[SKIP] {filename}: No matching config for {config_id}")
        return result

    print(f"[START] {filename} -> config {actual_config}")

    # Step 1: Scrape
    print(f"  [1/3] Scraping {actual_config}...")
    scrape_result = scrape_config(actual_config)

    if not scrape_result["success"]:
        result["message"] = f"Scrape failed: {scrape_result['message']}"
        print(f"  [FAIL] Scrape: {scrape_result['message']}")
        return result

    result["scrape_ok"] = True
    geojson_path = GEOJSON_DIR / f"parcels_{actual_config.lower()}.geojson"
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
    print("  RESCRAPE EMPTY FILES - PARALLEL AGENT DEPLOYMENT")
    print("=" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  Files to process: {len(EMPTY_FILES)}")
    print("=" * 70)

    GEOJSON_DIR.mkdir(parents=True, exist_ok=True)

    # Find which files have valid configs
    valid_files = []
    no_config = []

    for filename in EMPTY_FILES:
        config_id = get_config_id_from_filename(filename)
        actual_config = find_matching_config(config_id)
        if actual_config:
            valid_files.append((filename, actual_config))
        else:
            no_config.append((filename, config_id))

    print(f"\n  With valid configs: {len(valid_files)}")
    print(f"  No config found: {len(no_config)}")

    if no_config:
        print("\n  Files without configs (will be skipped):")
        for f, c in no_config[:10]:
            print(f"    - {f} ({c})")
        if len(no_config) > 10:
            print(f"    ... and {len(no_config) - 10} more")

    print("\n" + "=" * 70)

    if not valid_files:
        print("No valid files to process!")
        return

    # Deploy parallel agents - 20 workers for optimal throughput
    max_workers = 20
    print(f"\nDeploying {max_workers} parallel agents for {len(valid_files)} files...")
    print("=" * 70 + "\n")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, f): f for f, _ in valid_files}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            try:
                result = future.result(timeout=7200)  # 2hr timeout
                results.append(result)
            except Exception as e:
                print(f"[ERR] {futures[future]}: {str(e)[:50]}")

    # Summary
    print("\n" + "=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)

    scrape_ok = sum(1 for r in results if r.get("scrape_ok"))
    pmtiles_ok = sum(1 for r in results if r.get("pmtiles_ok"))
    upload_ok = sum(1 for r in results if r.get("upload_ok"))

    print(f"  Total files: {len(EMPTY_FILES)}")
    print(f"  With configs: {len(valid_files)}")
    print(f"  Scrape OK: {scrape_ok}")
    print(f"  PMTiles OK: {pmtiles_ok}")
    print(f"  Upload OK: {upload_ok}")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("=" * 70)

    # Show failures
    failures = [r for r in results if not r.get("upload_ok")]
    if failures:
        print("\n  FAILURES:")
        for r in failures:
            print(f"    - {r['filename']}: {r.get('message', 'Unknown')}")

    # Verification: List new PMTiles in R2
    print("\n  Verifying R2 uploads...")
    try:
        client = boto3.client('s3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            config=Config(signature_version='s3v4'))

        paginator = client.get_paginator('list_objects_v2')
        r2_files = []
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix='parcels/'):
            for obj in page.get('Contents', []):
                if obj['Key'].endswith('.pmtiles'):
                    r2_files.append(obj['Key'])

        print(f"  Total PMTiles in R2: {len(r2_files)}")
    except Exception as e:
        print(f"  Verification failed: {e}")


if __name__ == "__main__":
    main()
