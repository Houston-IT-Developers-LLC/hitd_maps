#!/usr/bin/env python3
"""
Deploy ALL Mississippi Counties (82 counties)
==============================================
From MS_Parcels_Aprl2024 MapServer
All 82 counties in layers 1-81
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

# Base URL for Mississippi MapServer
BASE_URL = "https://gis.mississippi.edu/server/rest/services/Cadastral/MS_Parcels_Aprl2024/MapServer"

# All county layers (id 1-81, layer 0 is county boundaries, 82-83 are city layers)
MS_COUNTIES = list(range(1, 82))

def check_if_exists(layer_id):
    """Check if file already exists on R2"""
    try:
        source_id = f"ms_layer_{layer_id}"
        resp = requests.head(f"{CDN_BASE}/parcels/parcels_{source_id}.pmtiles", timeout=10)
        if resp.status_code == 200:
            size = int(resp.headers.get('content-length', 0)) / (1024*1024)
            if size > 1:
                return True, size
    except:
        pass
    return False, 0

def download_county_layer(layer_id, workers=50):
    """Download a single MS county layer"""

    # Check if exists
    exists, size = check_if_exists(layer_id)
    if exists:
        print(f"  ✓ SKIP: Layer {layer_id} ({size:.1f} MB already on R2)")
        return None

    url = f"{BASE_URL}/{layer_id}"

    # Get layer info first
    try:
        resp = requests.get(f"{url}?f=json", headers=HEADERS, timeout=30)
        layer_info = resp.json()
        county_name = layer_info.get('name', f'Layer_{layer_id}')
    except:
        county_name = f"Layer_{layer_id}"

    output_file = OUTPUT_DIR / "geojson" / f"parcels_ms_layer_{layer_id}.geojson"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Layer {layer_id}: {county_name}")
    print(f"{'='*60}")

    # Get count
    try:
        resp = requests.get(f"{url}/query?where=1%3D1&returnCountOnly=true&f=json",
                           headers=HEADERS, timeout=30)
        result = resp.json()
        count = result.get('count', 0)

        if 'error' in result:
            print(f"  ✗ ERROR: {result['error']}")
            return None
    except Exception as e:
        print(f"  ✗ ERROR getting count: {e}")
        return None

    if count == 0:
        print(f"  ✗ No features!")
        return None

    print(f"  Feature count: {count:,}")

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
        except:
            pass
        return None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch, o): o for o in offsets}
        done = 0
        for future in as_completed(futures):
            features = future.result()
            if features:
                all_features.extend(features)
            done += 1
            if done % 10 == 0 or done == len(offsets):
                print(f"  [{done}/{len(offsets)}] {len(all_features):,} features")

    if not all_features:
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

    print(f"  🔧 Converting {geojson_path.name} to PMTiles...")

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
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=24, help='Download workers per layer')
    parser.add_argument('--parallel-layers', type=int, default=8, help='Number of layers to download in parallel')
    parser.add_argument('--layers', type=str, help='Specific layer IDs to download (comma-separated, e.g., 11,51,8)')
    args = parser.parse_args()

    # Filter layers if specified
    if args.layers:
        layers_to_download = [int(x.strip()) for x in args.layers.split(',')]
    else:
        layers_to_download = MS_COUNTIES

    print("\n" + "="*80)
    print("  MISSISSIPPI STATEWIDE PARCEL DEPLOYMENT")
    print(f"  Total layers: {len(layers_to_download)}")
    print(f"  Parallel layers: {args.parallel_layers}")
    print("="*80)

    downloaded = []
    skipped = 0
    failed = 0

    # Download layers in parallel batches
    with ThreadPoolExecutor(max_workers=args.parallel_layers) as executor:
        futures = {executor.submit(download_county_layer, layer_id, workers=args.workers): layer_id
                   for layer_id in layers_to_download}

        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    downloaded.append(result)
                elif result is None:
                    skipped += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                failed += 1

    print(f"\n✓ Downloaded {len(downloaded)} new files ({skipped} skipped, {failed} failed)")

    # Process and upload
    if downloaded:
        print(f"\n🔧 Processing and uploading {len(downloaded)} files...")

        success = 0
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = {executor.submit(process_and_upload, gf): gf for gf in downloaded}

            for future in as_completed(futures):
                if future.result():
                    success += 1

        print("\n" + "="*80)
        print(f"  ✓ COMPLETE: {success}/{len(downloaded)} uploaded successfully")
        print(f"  Mississippi coverage: {success}/82 counties")
        print("="*80)

if __name__ == '__main__':
    main()
