#!/usr/bin/env python3
"""
Convert downloaded GeoJSON files to PMTiles and upload to R2.
Uses parallel processing for speed.
"""

import subprocess
import os
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

DOWNLOAD_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/downloads")
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_BUCKET = "gspot-tiles"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

# Load R2 credentials
def load_env():
    env_path = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/.env")
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env[key] = value
    return env


def convert_to_pmtiles(geojson_path):
    """Convert a GeoJSON file to PMTiles."""
    pmtiles_path = geojson_path.with_suffix('.pmtiles')
    name = geojson_path.stem

    print(f"\n[{name}] Converting to PMTiles...")

    cmd = [
        'tippecanoe',
        '-o', str(pmtiles_path),
        '-l', 'parcels',
        '--force',
        '--no-feature-limit',
        '--no-tile-size-limit',
        '-z15',
        '--drop-densest-as-needed',
        str(geojson_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            size_mb = pmtiles_path.stat().st_size / (1024 * 1024)
            print(f"[{name}] Created {pmtiles_path.name} ({size_mb:.1f} MB)")
            return pmtiles_path
        else:
            print(f"[{name}] Error: {result.stderr[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"[{name}] Timeout during conversion")
        return None
    except Exception as e:
        print(f"[{name}] Error: {e}")
        return None


def upload_to_r2(pmtiles_path, env):
    """Upload PMTiles file to R2."""
    name = pmtiles_path.stem
    print(f"[{name}] Uploading to R2...")

    # Set AWS credentials
    aws_env = os.environ.copy()
    aws_env['AWS_ACCESS_KEY_ID'] = env['R2_ACCESS_KEY']
    aws_env['AWS_SECRET_ACCESS_KEY'] = env['R2_SECRET_KEY']

    cmd = [
        'aws', 's3', 'cp',
        str(pmtiles_path),
        f's3://{R2_BUCKET}/{pmtiles_path.name}',
        '--endpoint-url', R2_ENDPOINT,
        '--content-type', 'application/octet-stream'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=aws_env)
        if result.returncode == 0:
            url = f"{R2_PUBLIC_URL}/{pmtiles_path.name}"
            print(f"[{name}] Uploaded: {url}")
            return url
        else:
            print(f"[{name}] Upload error: {result.stderr[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"[{name}] Upload timeout")
        return None
    except Exception as e:
        print(f"[{name}] Upload error: {e}")
        return None


def verify_pmtiles(pmtiles_path):
    """Verify PMTiles file is valid."""
    try:
        result = subprocess.run(['pmtiles', 'show', str(pmtiles_path)],
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and 'bounds' in result.stdout:
            # Extract bounds
            for line in result.stdout.split('\n'):
                if 'bounds' in line:
                    return True
        return False
    except:
        return False


def process_geojson(geojson_path, env):
    """Process a single GeoJSON file: convert and upload."""
    name = geojson_path.stem

    # Skip Vermont since we already processed it
    if 'vt_statewide' in name and (DOWNLOAD_DIR / 'parcels_vt_statewide.pmtiles').exists():
        print(f"[{name}] Already processed, skipping")
        return name, f"{R2_PUBLIC_URL}/parcels_vt_statewide.pmtiles"

    # Convert to PMTiles
    pmtiles_path = convert_to_pmtiles(geojson_path)
    if not pmtiles_path:
        return name, None

    # Verify
    if not verify_pmtiles(pmtiles_path):
        print(f"[{name}] PMTiles verification failed")
        return name, None

    # Upload
    url = upload_to_r2(pmtiles_path, env)
    return name, url


def main():
    print("=" * 60)
    print("BATCH PMTILES CONVERTER AND UPLOADER")
    print("=" * 60)

    # Load credentials
    env = load_env()

    # Find all GeoJSON files
    geojson_files = list(DOWNLOAD_DIR.glob('*.geojson'))
    print(f"Found {len(geojson_files)} GeoJSON files to process")

    # Process files (sequentially for tippecanoe which is already parallel internally)
    results = []
    for geojson_path in sorted(geojson_files):
        name, url = process_geojson(geojson_path, env)
        results.append((name, url))

    # Summary
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)

    successful = [(n, u) for n, u in results if u]
    failed = [n for n, u in results if not u]

    print(f"\nSuccessful: {len(successful)}")
    for name, url in successful:
        print(f"  {name}: {url}")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for name in failed:
            print(f"  {name}")

    # Return list of successful parcel names
    return [name for name, url in successful]


if __name__ == '__main__':
    main()
