#!/usr/bin/env python3
"""
Deploy Mega Counties (500K+ population)
========================================
Priority deployment for maximum coverage impact
"""

import requests
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Configuration
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/output")
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

HEADERS = {'User-Agent': 'Mozilla/5.0'}

# VERIFIED MEGA COUNTY SOURCES
MEGA_COUNTIES = {
    "ky_jefferson": {
        "name": "Kentucky - Jefferson County (Louisville)",
        "url": "https://gis.lojic.org/maps/rest/services/LojicSolutions/OpenDataPVA/MapServer/1",
        "state": "KY",
        "population": 782000,
        "count": 293067,
        "notes": "Daily updates, use LRSN as unique ID"
    },
}

def check_if_exists(source_id):
    """Check if file already exists on R2"""
    try:
        resp = requests.head(f"{CDN_BASE}/parcels/parcels_{source_id}.pmtiles", timeout=10)
        if resp.status_code == 200:
            size = int(resp.headers.get('content-length', 0)) / (1024*1024)
            if size > 1:
                return True, size
    except:
        pass
    return False, 0

def download_source(source_id, source, workers=24):
    """Download a single source"""

    exists, size = check_if_exists(source_id)
    if exists:
        print(f"\n  ✓ SKIP: {source_id} ({size:.1f} MB already on R2)")
        return None

    url = source['url']
    count = source['count']
    output_file = OUTPUT_DIR / "geojson" / f"parcels_{source_id}.geojson"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"{source['name']}")
    print(f"Population: {source['population']:,}")
    print(f"URL: {url}")
    print(f"Features: {count:,}")
    print(f"{'='*70}")

    # Download in parallel
    all_features = []
    batch_size = 2000
    offsets = list(range(0, count, batch_size))

    def fetch(offset):
        try:
            params = {
                'where': '1=1',
                'outFields': '*',
                'f': 'geojson',
                'resultOffset': offset,
                'resultRecordCount': batch_size,
                'outSR': '4326'
            }
            resp = requests.get(f"{url}/query", params=params, headers=HEADERS, timeout=180)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('features', [])
        except Exception as e:
            print(f"  ✗ Batch error at offset {offset}: {e}")
        return None

    print(f"  Downloading in {len(offsets)} batches with {workers} workers...")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch, o): o for o in offsets}
        done = 0
        for future in as_completed(futures):
            features = future.result()
            if features:
                all_features.extend(features)
            done += 1
            if done % 10 == 0 or done == len(offsets):
                pct = (done / len(offsets)) * 100
                print(f"  [{done}/{len(offsets)}] {pct:.1f}% - {len(all_features):,} features")

    if not all_features:
        print(f"  ✗ No features downloaded!")
        return None

    # Save
    with open(output_file, 'w') as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f)

    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"  ✓ Saved {len(all_features):,} features ({size_mb:.1f} MB)")

    return output_file

def process_and_upload(geojson_path):
    """Convert to PMTiles and upload"""

    pmtiles_path = OUTPUT_DIR / "pmtiles" / f"{geojson_path.stem}.pmtiles"
    pmtiles_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n  🔧 Converting to PMTiles...")

    try:
        cmd = [
            'tippecanoe', '-o', str(pmtiles_path),
            '-z', '15', '-Z', '10',
            '--drop-densest-as-needed',
            '--extend-zooms-if-still-dropping',
            '--force', '--layer', 'parcels',
            str(geojson_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=3600)

        pm_size = pmtiles_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Created PMTiles ({pm_size:.1f} MB)")
    except Exception as e:
        print(f"  ✗ Conversion failed: {e}")
        return False

    print(f"  ☁️  Uploading to R2...")

    try:
        cmd = [
            'aws', 's3', 'cp', str(pmtiles_path),
            f's3://{R2_BUCKET}/parcels/{pmtiles_path.name}',
            '--endpoint-url', R2_ENDPOINT
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)

        # Verify
        cdn_url = f"{CDN_BASE}/parcels/{pmtiles_path.name}"
        result = subprocess.run(
            ['pmtiles', 'show', cdn_url],
            capture_output=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"  ✓ SUCCESS: {cdn_url}")
            # Clean up
            geojson_path.unlink()
            pmtiles_path.unlink()
            return True
    except Exception as e:
        print(f"  ✗ Upload failed: {e}")

    return False

def main():
    print("\n" + "="*80)
    print("  🚀 MEGA COUNTY BLITZ - Deploy 500K+ Population Counties")
    print(f"  Total sources: {len(MEGA_COUNTIES)}")
    print("="*80)

    downloaded = []

    # Download all
    for source_id, source in MEGA_COUNTIES.items():
        try:
            result = download_source(source_id, source, workers=24)
            if result:
                downloaded.append(result)
        except Exception as e:
            print(f"  ✗ {source_id} ERROR: {e}")

    print(f"\n✓ Downloaded {len(downloaded)} new files")

    # Process and upload
    if downloaded:
        print(f"\n🔧 Processing and uploading {len(downloaded)} files...")

        success = 0
        for gf in downloaded:
            if process_and_upload(gf):
                success += 1

        print("\n" + "="*80)
        print(f"  ✓ COMPLETE: {success}/{len(downloaded)} uploaded successfully")
        print(f"  New parcels: {sum(s['count'] for s in MEGA_COUNTIES.values() if not check_if_exists(k)[0] for k in MEGA_COUNTIES):,}")
        print("="*80)

if __name__ == '__main__':
    main()
