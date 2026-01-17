#!/usr/bin/env python3
"""
Fix all GeoJSON files on R2 that need reprojection.
Downloads, reprojects to WGS84, converts to PMTiles, and uploads.
"""

import subprocess
import os
import sys
import tempfile
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Unbuffered output for real-time logging
sys.stdout.reconfigure(line_buffering=True)

R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# Set environment variables for AWS CLI
os.environ['AWS_ACCESS_KEY_ID'] = R2_ACCESS_KEY
os.environ['AWS_SECRET_ACCESS_KEY'] = R2_SECRET_KEY

def run_cmd(cmd, timeout=3600):
    """Run a shell command"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.returncode == 0, result.stdout, result.stderr

def detect_crs_from_sample(sample_data):
    """Detect CRS from coordinate sample - handles various state plane projections"""
    coords = re.search(r'\[\[([0-9.-]+),\s*([0-9.-]+)\]', sample_data)
    if not coords:
        coords = re.search(r'"coordinates":\s*\[([0-9.-]+),\s*([0-9.-]+)\]', sample_data)
    if not coords:
        return None

    x, y = float(coords.group(1)), float(coords.group(2))

    # WGS84 (EPSG:4326)
    if -180 <= x <= 180 and -90 <= y <= 90:
        return "EPSG:4326"

    # Web Mercator (EPSG:3857)
    if -20037508 <= x <= 20037508 and -20037508 <= y <= 20037508:
        return "EPSG:3857"

    # Texas State Plane South Central (EPSG:2278) - Harris, Travis, Bexar
    if 2000000 < x < 5000000 and 10000000 < y < 20000000:
        return "EPSG:2278"

    # Texas State Plane North Central (EPSG:2276) - Dallas, Tarrant
    if 2000000 < x < 4000000 and 6000000 < y < 10000000:
        return "EPSG:2276"

    # Michigan Oblique Mercator (EPSG:3078)
    if 10000000 < x < 15000000 and 0 < y < 1500000:
        return "EPSG:3078"

    # Michigan State Plane (EPSG:2253)
    if 5000000 < x < 10000000 and 0 < y < 3000000:
        return "EPSG:2253"

    # Pennsylvania (EPSG:2272)
    if 1000000 < x < 3500000 and 0 < y < 1000000:
        return "EPSG:2272"

    # New York Long Island (EPSG:2263)
    if 800000 < x < 1500000 and 100000 < y < 500000:
        return "EPSG:2263"

    # Georgia (EPSG:2240)
    if 500000 < x < 1500000 and 0 < y < 2000000:
        return "EPSG:2240"

    # Wisconsin Transverse Mercator (EPSG:3071)
    if 0 < x < 1000000 and 0 < y < 1000000:
        return "EPSG:3071"

    # Generic large values - fallback to Web Mercator
    if abs(x) > 100000 or abs(y) > 100000:
        return "EPSG:3857"

    return None

def process_file(filename, tmpdir):
    """Process a single file"""
    print(f"[START] {filename}")

    base_name = filename.replace('.geojson', '')
    local_geojson = os.path.join(tmpdir, filename)
    local_wgs84 = os.path.join(tmpdir, f"{base_name}_wgs84.geojson")
    local_pmtiles = os.path.join(tmpdir, f"{base_name}.pmtiles")

    try:
        # Download from R2
        print(f"  [1/4] Downloading {filename}...")
        ok, _, err = run_cmd(f'aws s3 cp s3://{R2_BUCKET}/parcels/{filename} {local_geojson} --endpoint-url {R2_ENDPOINT}', timeout=1800)
        if not ok:
            print(f"  [ERROR] Download failed: {err[:200]}")
            return False

        # Check file size
        size_mb = os.path.getsize(local_geojson) / (1024 * 1024)
        print(f"  Downloaded {size_mb:.1f}MB")

        # Detect CRS
        with open(local_geojson, 'r') as f:
            sample = f.read(10000)

        source_crs = detect_crs_from_sample(sample)
        if not source_crs:
            print(f"  [ERROR] Could not detect CRS")
            return False

        if source_crs == "EPSG:4326":
            print(f"  Already WGS84, skipping reprojection")
            local_wgs84 = local_geojson
        else:
            # Reproject
            print(f"  [2/4] Reprojecting {source_crs} → EPSG:4326...")
            ok, _, err = run_cmd(f'ogr2ogr -f GeoJSON -s_srs {source_crs} -t_srs EPSG:4326 {local_wgs84} {local_geojson}', timeout=1800)
            if not ok:
                print(f"  [ERROR] Reprojection failed: {err[:200]}")
                return False

        # Convert to PMTiles
        print(f"  [3/4] Converting to PMTiles...")
        ok, _, err = run_cmd(f'tippecanoe -o {local_pmtiles} -l parcels --minimum-zoom=5 --maximum-zoom=15 --drop-densest-as-needed --extend-zooms-if-still-dropping --simplification=10 --force {local_wgs84}', timeout=3600)
        if not ok:
            print(f"  [ERROR] Tippecanoe failed: {err[:200]}")
            return False

        pmtiles_size = os.path.getsize(local_pmtiles) / (1024 * 1024)
        print(f"  PMTiles size: {pmtiles_size:.1f}MB")

        # Upload to R2
        print(f"  [4/4] Uploading to R2...")
        ok, _, err = run_cmd(f'aws s3 cp {local_pmtiles} s3://{R2_BUCKET}/parcels/{base_name}.pmtiles --endpoint-url {R2_ENDPOINT}', timeout=600)
        if not ok:
            print(f"  [ERROR] Upload failed: {err[:200]}")
            return False

        print(f"[DONE] {filename} → {base_name}.pmtiles ({pmtiles_size:.1f}MB)")
        return True

    except Exception as e:
        print(f"  [ERROR] {e}")
        return False
    finally:
        # Cleanup
        for f in [local_geojson, local_wgs84, local_pmtiles]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass

def main():
    # Read files to process
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        with open('/tmp/files_to_reproject.txt') as f:
            files = [line.strip() for line in f if line.strip()]

    print(f"Processing {len(files)} files...")

    # Use a temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Process files (can be parallelized but large files need sequential for memory)
        success = 0
        failed = 0

        for filename in files:
            if process_file(filename, tmpdir):
                success += 1
            else:
                failed += 1

        print(f"\n{'='*60}")
        print(f"Results: {success} succeeded, {failed} failed")

if __name__ == "__main__":
    main()
