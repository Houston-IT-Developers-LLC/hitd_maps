#!/usr/bin/env python3
"""
Wave 4 Turbo Scraper - Additional Sources from Search Agents
=============================================================
TX Harris: 1.54M parcels (Houston)
TX Travis: 374K parcels (Austin)
TX Tarrant: Already have?
WI Dane: 340K parcels (Madison) - needs re-scrape with proper layer
"""

import os
import sys
import json
import argparse
import subprocess
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
OUTPUT_DIR = "/home/exx/Documents/C/hitd_maps/data-pipeline/output"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

# Additional sources from search agents
SOURCES = {
    # TX Harris County (Houston) - 1.54M parcels
    "tx_harris_v2": {
        "url": "https://www.gis.hctx.net/arcgis/rest/services/HCAD/Parcels/MapServer/0",
        "name": "Texas - Harris County (Houston)",
        "estimated": 1538771,
        "batch_size": 1000,  # API max is 1000
    },
    # TX Travis County (Austin) - 374K parcels
    "tx_travis_v2": {
        "url": "https://taxmaps.traviscountytx.gov/arcgis/rest/services/Parcels/MapServer/0",
        "name": "Texas - Travis County (Austin)",
        "estimated": 373683,
        "batch_size": 2000,
    },
    # TX Tarrant County (Fort Worth) - just in case
    "tx_tarrant_v2": {
        "url": "https://mapit.tarrantcounty.com/arcgis/rest/services/Dynamic/TADParcelsApp/MapServer/0",
        "name": "Texas - Tarrant County (Fort Worth)",
        "estimated": 700000,  # estimate
        "batch_size": 2000,
    },
    # WI Dane County (Madison) - proper endpoint
    "wi_dane_v2": {
        "url": "https://geodata.dane.wisc.gov/arcgis/rest/services/OpenData/Parcels/FeatureServer/0",
        "name": "Wisconsin - Dane County (Madison) v2",
        "estimated": 340000,
        "batch_size": 2000,
    },
    # OH Cuyahoga (Cleveland) - historic data
    "oh_cuyahoga": {
        "url": "https://gis.cuyahogacounty.us/server/rest/services/CCFO/APPRAISAL_PARCELS_HISTORIC_WGS84/MapServer/0",
        "name": "Ohio - Cuyahoga County (Cleveland)",
        "estimated": 35683,
        "batch_size": 2000,
    },
}

def get_feature_count(base_url, timeout=30):
    """Get total feature count from service."""
    try:
        query_url = f"{base_url}/query"
        params = {
            'where': '1=1',
            'returnCountOnly': 'true',
            'f': 'json'
        }
        r = requests.get(query_url, params=params, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            if 'count' in data:
                return data['count']
    except Exception as e:
        print(f"  Error getting count: {e}")
    return None

def fetch_batch(args):
    """Fetch a batch of features."""
    url, offset, batch_size, batch_num, total_batches = args
    query_url = f"{url}/query"
    params = {
        'where': '1=1',
        'outFields': '*',
        'outSR': '4326',
        'f': 'geojson',
        'resultOffset': offset,
        'resultRecordCount': batch_size,
    }

    for attempt in range(3):
        try:
            r = requests.get(query_url, params=params, timeout=120)
            if r.status_code == 200:
                data = r.json()
                features = data.get('features', [])
                return features
        except Exception as e:
            if attempt < 2:
                continue
    return []

def download_source(source_key, source_info, workers=40, skip_existing=True):
    """Download a single source."""
    name = source_info['name']
    url = source_info['url']
    batch_size = source_info.get('batch_size', 2000)

    output_file = f"parcels_{source_key}.geojson"
    output_path = Path(OUTPUT_DIR) / output_file
    pmtiles_file = f"parcels_{source_key}.pmtiles"
    pmtiles_path = Path(OUTPUT_DIR) / pmtiles_file

    print(f"\n{'='*60}")
    print(f"Downloading: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    # Check if already exists in R2
    if skip_existing:
        try:
            r = requests.head(f"{CDN_BASE}/{pmtiles_file}", timeout=10)
            if r.status_code == 200:
                size_mb = int(r.headers.get('content-length', 0)) / (1024 * 1024)
                if size_mb > 1:
                    print(f"  SKIP: {pmtiles_file} exists ({size_mb:.1f} MB)")
                    return True
        except:
            pass

    # Get feature count
    count = get_feature_count(url)
    if not count:
        print(f"  ERROR: Could not get feature count")
        return False

    print(f"  Feature count: {count:,}")

    # Calculate batches
    total_batches = (count + batch_size - 1) // batch_size

    # Prepare batch args
    batch_args = [
        (url, i * batch_size, batch_size, i + 1, total_batches)
        for i in range(total_batches)
    ]

    # Download in parallel
    all_features = []
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_batch, args): args for args in batch_args}

        for future in as_completed(futures):
            features = future.result()
            all_features.extend(features)
            completed += 1

            if completed % 20 == 0 or completed == total_batches:
                print(f"  [{completed}/{total_batches}] {len(all_features):,} features")

    if not all_features:
        print(f"  ERROR: No features downloaded")
        return False

    print(f"\n  Saving {len(all_features):,} features...")

    # Save GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }

    with open(output_path, 'w') as f:
        json.dump(geojson, f)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Saved: {size_mb:.1f} MB")

    # Convert to PMTiles
    print(f"  Converting to PMTiles...")
    cmd = [
        'tippecanoe',
        '-o', str(pmtiles_path),
        '-l', 'parcels',
        '-zg',
        '--drop-densest-as-needed',
        '--extend-zooms-if-still-dropping',
        '--force',
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: tippecanoe failed: {result.stderr}")
        return False

    pmtiles_size = pmtiles_path.stat().st_size / (1024 * 1024)
    print(f"  Created: {pmtiles_size:.1f} MB")

    # Upload to R2
    print(f"  Uploading to R2...")
    upload_cmd = [
        'aws', 's3', 'cp',
        str(pmtiles_path),
        f's3://{R2_BUCKET}/{pmtiles_file}',
        '--endpoint-url', R2_ENDPOINT
    ]

    result = subprocess.run(upload_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: Upload failed: {result.stderr}")
        return False

    # Verify
    print(f"  Verifying...")
    try:
        r = requests.head(f"{CDN_BASE}/{pmtiles_file}", timeout=10)
        if r.status_code == 200:
            print(f"  SUCCESS!")
            output_path.unlink(missing_ok=True)
            return True
    except:
        pass

    print(f"  WARNING: Verification failed")
    return False

def main():
    parser = argparse.ArgumentParser(description='Wave 4 Turbo Scraper')
    parser.add_argument('--source', type=str, help='Specific source to download')
    parser.add_argument('--list', action='store_true', help='List available sources')
    parser.add_argument('--workers', type=int, default=40, help='Number of parallel workers')
    parser.add_argument('--no-skip', action='store_true', help='Download even if exists')
    args = parser.parse_args()

    if args.list:
        print("\nAvailable sources:")
        print("-" * 80)
        for key, info in sorted(SOURCES.items(), key=lambda x: x[1]['estimated'], reverse=True):
            print(f"  {key:20} | {info['estimated']:>10,} features | {info['name']}")
        return

    print("\n" + "=" * 80)
    print("HITD Maps - Wave 4 Turbo Scraper")
    print("=" * 80)

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    if args.source:
        if args.source not in SOURCES:
            print(f"Unknown source: {args.source}")
            print("Use --list to see available sources")
            return
        sources = {args.source: SOURCES[args.source]}
    else:
        sources = SOURCES

    results = []
    for key, info in sources.items():
        success = download_source(key, info, workers=args.workers, skip_existing=not args.no_skip)
        results.append((key, info['name'], success))

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    for key, name, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"  {key:20} | {status:8} | {name}")

    print("\nDone!")

if __name__ == '__main__':
    main()
