#!/usr/bin/env python3
"""
HITD Maps - Multi-State Parallel Scraper
Launch multiple state scrapers for maximum throughput
"""

import requests
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import argparse

# Configuration
OUTPUT_DIR = "/home/exx/Documents/C/hitd_maps/data-pipeline/output"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# More verified working sources - county level for partial states
SOURCES = {
    # Kentucky - Louisville/Jefferson (found by agents)
    "ky_jefferson": {
        "name": "Kentucky - Jefferson County (Louisville)",
        "url": "https://gis.lojic.org/maps/rest/services/LojicSolutions/OpenDataPVA/MapServer/1",
        "state": "KY",
        "records": 293067,
        "priority": 1,
    },
    # Georgia - Forsyth County
    "ga_forsyth": {
        "name": "Georgia - Forsyth County",
        "url": "https://geo.forsythco.com/gis/rest/services/Public/Tax_Parcel/FeatureServer/0",
        "state": "GA",
        "records": 100000,
        "priority": 2,
    },
    # Georgia - Chatham/Savannah (SAGIS)
    "ga_chatham": {
        "name": "Georgia - Chatham County (Savannah)",
        "url": "https://pub.sagis.org/arcgis/rest/services/OpenData/Parcels/FeatureServer/0",
        "state": "GA",
        "records": 120000,
        "priority": 2,
    },
    # Missouri - St. Louis City
    "mo_stlouis_city": {
        "name": "Missouri - St. Louis City",
        "url": "https://maps6.stlouis-mo.gov/arcgis/rest/services/CITYWORKS/CW_BASE/MapServer/5",
        "state": "MO",
        "records": 150000,
        "priority": 1,
    },
    # South Carolina - York County
    "sc_york": {
        "name": "South Carolina - York County",
        "url": "https://services1.arcgis.com/xGOuQppWi0xFKm7B/arcgis/rest/services/Parcels/FeatureServer/0",
        "state": "SC",
        "records": 140000,
        "priority": 3,
    },
}

def get_feature_count(url):
    try:
        resp = requests.get(f"{url}/query?where=1%3D1&returnCountOnly=true&f=json",
                          headers=HEADERS, timeout=30)
        return resp.json().get('count', 0)
    except:
        return 0

def download_arcgis_features(source_id, source, workers=50, batch_size=2000):
    url = source['url']
    output_file = f"{OUTPUT_DIR}/geojson/parcels_{source_id}.geojson"

    print(f"\n{'='*60}")
    print(f"Downloading: {source['name']}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    count = get_feature_count(url)
    print(f"  Feature count: {count:,}")

    if count == 0:
        print(f"  ERROR: No features!")
        return None

    all_features = []
    failed = []

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
                return resp.json().get('features', [])
        except:
            pass
        return None

    offsets = list(range(0, count, batch_size))
    done = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch, o): o for o in offsets}
        for future in as_completed(futures):
            offset = futures[future]
            try:
                features = future.result()
                if features:
                    all_features.extend(features)
                else:
                    failed.append(offset)
            except:
                failed.append(offset)
            done += 1
            if done % 20 == 0 or done == len(offsets):
                print(f"  [{done}/{len(offsets)}] {len(all_features):,} features")

    # Retry failed
    for offset in failed[:]:
        time.sleep(0.5)
        features = fetch(offset)
        if features:
            all_features.extend(features)
            failed.remove(offset)

    print(f"\n  Saving {len(all_features):,} features...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f)

    size = os.path.getsize(output_file) / (1024*1024)
    print(f"  Saved: {size:.1f} MB")
    return output_file if all_features else None

def convert_upload(geojson_path, source_id):
    pmtiles = f"{OUTPUT_DIR}/pmtiles/parcels_{source_id}.pmtiles"
    os.makedirs(os.path.dirname(pmtiles), exist_ok=True)

    print(f"  Converting to PMTiles...")
    cmd = ['tippecanoe', '-o', pmtiles, '-z', '15', '-Z', '10',
           '--drop-densest-as-needed', '--extend-zooms-if-still-dropping',
           '--force', '--layer', 'parcels', geojson_path]
    subprocess.run(cmd, check=True, capture_output=True)

    size = os.path.getsize(pmtiles) / (1024*1024)
    print(f"  Created: {size:.1f} MB")

    print(f"  Uploading to R2...")
    cmd = ['aws', 's3', 'cp', pmtiles, f's3://{R2_BUCKET}/parcels/parcels_{source_id}.pmtiles',
           '--endpoint-url', R2_ENDPOINT]
    subprocess.run(cmd, check=True, capture_output=True)

    print(f"  Verifying...")
    result = subprocess.run(['pmtiles', 'show', f'{CDN_BASE}/parcels/parcels_{source_id}.pmtiles'],
                          capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        print(f"  SUCCESS!")
        os.remove(geojson_path)
        os.remove(pmtiles)
        return True
    return False

def process(source_id, source, skip_existing=True):
    pmtiles_name = f"parcels_{source_id}.pmtiles"
    if skip_existing:
        try:
            resp = requests.head(f"{CDN_BASE}/parcels/{pmtiles_name}", timeout=10)
            if resp.status_code == 200:
                size = int(resp.headers.get('content-length', 0)) / (1024*1024)
                if size > 1:  # Skip if > 1MB (not placeholder)
                    print(f"\n  SKIP: {pmtiles_name} exists ({size:.1f} MB)")
                    return True
        except:
            pass

    geojson = download_arcgis_features(source_id, source)
    if not geojson:
        return False
    return convert_upload(geojson, source_id)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--source', type=str)
    parser.add_argument('--no-skip', action='store_true')
    args = parser.parse_args()

    if args.list:
        for sid, src in sorted(SOURCES.items(), key=lambda x: x[1]['priority']):
            print(f"  {sid}: {src['name']} ({src['records']:,})")
        return

    print("\n" + "="*80)
    print("HITD Maps - Multi-State Scraper")
    print("="*80)

    sources = {args.source: SOURCES[args.source]} if args.source else SOURCES

    for sid, src in sorted(sources.items(), key=lambda x: x[1]['priority']):
        try:
            process(sid, src, skip_existing=not args.no_skip)
        except Exception as e:
            print(f"  ERROR: {sid} - {e}")

    print("\nDone!")

if __name__ == '__main__':
    main()
