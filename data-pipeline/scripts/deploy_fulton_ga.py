#!/usr/bin/env python3
"""
Deploy Fulton County, GA - Atlanta
370,567 parcels
"""

import requests
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/output")
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

HEADERS = {'User-Agent': 'Mozilla/5.0'}

SOURCE = {
    "ga_fulton": {
        "name": "Georgia - Fulton County (Atlanta)",
        "url": "https://services1.arcgis.com/AQDHTHDrZzfsFsB5/arcgis/rest/services/Tax_Parcels/FeatureServer/0",
        "state": "GA",
        "count": 370567,
    }
}

def download_source(source_id, source, workers=32):
    url = source['url']
    count = source['count']
    output_file = OUTPUT_DIR / "geojson" / f"parcels_{source_id}.geojson"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"{source['name']}")
    print(f"URL: {url}")
    print(f"Features: {count:,}")
    print(f"{'='*70}")

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
            print(f"  ✗ Batch error at {offset}: {e}")
        return None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch, o): o for o in offsets}
        done = 0
        for future in as_completed(futures):
            features = future.result()
            if features:
                all_features.extend(features)
            done += 1
            if done % 25 == 0 or done == len(offsets):
                print(f"  [{done}/{len(offsets)}] {len(all_features):,} features")

    if not all_features:
        print(f"  ✗ No features downloaded!")
        return None

    with open(output_file, 'w') as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f)

    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"  ✓ Saved {len(all_features):,} features ({size_mb:.1f} MB)")

    return output_file

def process_and_upload(geojson_path):
    pmtiles_path = OUTPUT_DIR / "pmtiles" / f"{geojson_path.stem}.pmtiles"
    pmtiles_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  🔧 Converting to PMTiles...")

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

        cdn_url = f"{CDN_BASE}/parcels/{pmtiles_path.name}"
        result = subprocess.run(
            ['pmtiles', 'show', cdn_url],
            capture_output=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"  ✅ SUCCESS: {cdn_url}")
            geojson_path.unlink()
            pmtiles_path.unlink()
            return True
    except Exception as e:
        print(f"  ✗ Upload failed: {e}")

    return False

def main():
    print("\n" + "="*80)
    print("  DEPLOY FULTON COUNTY, GA (ATLANTA)")
    print("="*80)

    for source_id, source in SOURCE.items():
        geojson_file = download_source(source_id, source, workers=32)

        if geojson_file:
            if process_and_upload(geojson_file):
                print(f"\n✅ Fulton County deployed successfully!")
            else:
                print(f"\n❌ Upload failed")

if __name__ == '__main__':
    main()
