#!/usr/bin/env python3
"""Convert all GeoJSON files to PMTiles sequentially (RAM-safe) and upload to R2"""
import os
import subprocess
import sys
from pathlib import Path
import time

# Directories
SCRIPT_DIR = Path(__file__).parent
PIPELINE_DIR = SCRIPT_DIR.parent
DOWNLOADS = PIPELINE_DIR / "data" / "downloads"
OUTPUT = PIPELINE_DIR / "output" / "pmtiles"
OUTPUT.mkdir(parents=True, exist_ok=True)

# R2 config
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

# Files currently being converted by another process
SKIP_FILES = {'parcels_fl_statewide.geojson'}  # FL running separately

def convert_and_upload(geojson_path):
    """Convert GeoJSON to PMTiles and upload to R2"""
    name = geojson_path.stem
    pmtiles_path = OUTPUT / f"{name}.pmtiles"

    size_mb = geojson_path.stat().st_size / 1024/1024

    # Skip if already exists and reasonable size
    if pmtiles_path.exists():
        existing_size = pmtiles_path.stat().st_size
        if existing_size > 100000:  # >100KB
            print(f"SKIP {name} - already exists ({existing_size/1024/1024:.1f}MB)")
            return "SKIP"

    print(f"\n{'='*60}")
    print(f"CONVERTING: {name}")
    print(f"Source: {size_mb:.1f}MB")
    print(f"{'='*60}")

    # Convert with tippecanoe
    start_time = time.time()
    result = subprocess.run([
        'tippecanoe',
        '-o', str(pmtiles_path),
        '--force',
        '--no-feature-limit', '--no-tile-size-limit',
        '-zg',
        '--drop-densest-as-needed',
        '--extend-zooms-if-still-dropping',
        '-l', 'parcels',
        str(geojson_path)
    ], capture_output=False)  # Let output show in terminal

    elapsed = time.time() - start_time

    if result.returncode != 0:
        print(f"FAIL {name}: tippecanoe returned {result.returncode}")
        return "FAIL"

    # Verify file exists and has reasonable size
    if not pmtiles_path.exists():
        print(f"FAIL {name}: output file not created")
        return "FAIL"

    output_size = pmtiles_path.stat().st_size
    if output_size < 50000:  # <50KB is suspicious
        print(f"FAIL {name}: output too small ({output_size} bytes)")
        return "FAIL"

    print(f"Converted in {elapsed:.0f}s: {output_size/1024/1024:.1f}MB")

    # Upload to R2
    print(f"Uploading to R2...")
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
    env['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

    upload = subprocess.run([
        'aws', 's3', 'cp',
        str(pmtiles_path),
        f's3://{R2_BUCKET}/parcels/{pmtiles_path.name}',
        '--endpoint-url', R2_ENDPOINT
    ], capture_output=True, text=True, env=env)

    if upload.returncode != 0:
        print(f"UPLOAD FAIL {name}: {upload.stderr[:200]}")
        return "UPLOAD_FAIL"

    print(f"DONE {name} ({output_size/1024/1024:.1f}MB uploaded)")
    return "DONE"

def main():
    # Get all GeoJSON files sorted by size (smallest first for quick wins)
    geojson_files = sorted(DOWNLOADS.glob("*.geojson"), key=lambda x: x.stat().st_size)
    geojson_files = [f for f in geojson_files if f.name not in SKIP_FILES]

    total_size = sum(f.stat().st_size for f in geojson_files) / 1024/1024/1024
    print(f"Found {len(geojson_files)} GeoJSON files ({total_size:.1f}GB total)")
    print(f"Skipping: {SKIP_FILES}")
    print()

    results = {"DONE": 0, "SKIP": 0, "FAIL": 0, "UPLOAD_FAIL": 0}

    for i, geojson_path in enumerate(geojson_files, 1):
        print(f"\n[{i}/{len(geojson_files)}] ", end="")
        result = convert_and_upload(geojson_path)
        results[result] = results.get(result, 0) + 1

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Converted: {results['DONE']}")
    print(f"Skipped: {results['SKIP']}")
    print(f"Failed: {results['FAIL']}")
    print(f"Upload failed: {results['UPLOAD_FAIL']}")
    print(f"Total processed: {sum(results.values())}")

if __name__ == '__main__':
    main()
