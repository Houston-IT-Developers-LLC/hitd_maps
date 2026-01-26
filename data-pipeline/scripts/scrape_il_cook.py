#!/usr/bin/env python3
"""
HITD Maps - Illinois Cook County Parcel Scraper
1.43M parcels (Chicago metro area)
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

# AWS/R2 credentials
os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Illinois Cook County - Chicago metro
SOURCES = {
    "il_cook": {
        "name": "Illinois - Cook County (Chicago)",
        "url": "https://gis.cookcountyil.gov/hosting/rest/services/Hosted/Parcel_2020/FeatureServer/0",
        "state": "IL",
        "records": 1430137,
        "priority": 1,
    },
}

def get_feature_count(url):
    """Get actual feature count from ArcGIS service"""
    try:
        count_url = f"{url}/query?where=1%3D1&returnCountOnly=true&f=json"
        resp = requests.get(count_url, headers=HEADERS, timeout=30)
        data = resp.json()
        return data.get('count', 0)
    except Exception as e:
        print(f"  Error getting count: {e}")
        return 0

def download_arcgis_features(source_id, source, workers=40, batch_size=2000):
    """Download features from ArcGIS REST service"""
    url = source['url']
    name = source['name']
    output_file = f"{OUTPUT_DIR}/geojson/parcels_{source_id}.geojson"

    print(f"\n{'='*60}")
    print(f"Downloading: {name}")
    print(f"URL: {url}")
    print(f"Expected records: {source['records']:,}")
    print(f"Output: {output_file}")
    print(f"{'='*60}")

    # Get actual feature count
    count = get_feature_count(url)
    print(f"  Actual feature count: {count:,}")

    if count == 0:
        print(f"  ERROR: No features found!")
        return False

    # Calculate batches
    num_batches = (count + batch_size - 1) // batch_size
    print(f"  Will download in {num_batches} batches of {batch_size}")

    all_features = []
    failed_batches = []

    def fetch_batch(offset):
        """Fetch a single batch of features"""
        try:
            query_url = f"{url}/query"
            params = {
                'where': '1=1',
                'outFields': '*',
                'f': 'geojson',
                'resultOffset': offset,
                'resultRecordCount': batch_size,
                'outSR': '4326'  # WGS84
            }
            resp = requests.get(query_url, params=params, headers=HEADERS, timeout=180)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('features', [])
            else:
                return None
        except Exception as e:
            return None

    # Download batches in parallel
    offsets = list(range(0, count, batch_size))
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_batch, offset): offset for offset in offsets}

        for future in as_completed(futures):
            offset = futures[future]
            try:
                features = future.result()
                if features:
                    all_features.extend(features)
                else:
                    failed_batches.append(offset)
            except Exception as e:
                failed_batches.append(offset)

            completed += 1
            if completed % 50 == 0 or completed == len(offsets):
                print(f"  [{completed}/{len(offsets)}] Downloaded {len(all_features):,} features...")

    # Retry failed batches
    for retry in range(3):
        if not failed_batches:
            break
        print(f"  Retrying {len(failed_batches)} failed batches (attempt {retry + 1})...")
        new_failed = []
        for offset in failed_batches:
            time.sleep(0.5)
            features = fetch_batch(offset)
            if features:
                all_features.extend(features)
            else:
                new_failed.append(offset)
        failed_batches = new_failed

    if failed_batches:
        print(f"  WARNING: {len(failed_batches)} batches still failed")

    print(f"\n  Saving {len(all_features):,} features to {output_file}...")

    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(geojson, f)

    file_size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"  Saved: {file_size:.1f} MB")

    return output_file if len(all_features) > 0 else None

def convert_to_pmtiles(geojson_path, source_id):
    """Convert GeoJSON to PMTiles using tippecanoe"""
    pmtiles_name = f"parcels_{source_id}.pmtiles"
    pmtiles_path = f"{OUTPUT_DIR}/pmtiles/{pmtiles_name}"

    print(f"\n  Converting to PMTiles: {pmtiles_name}")

    os.makedirs(os.path.dirname(pmtiles_path), exist_ok=True)

    cmd = [
        'tippecanoe',
        '-o', pmtiles_path,
        '-z', '15',
        '-Z', '10',
        '--drop-densest-as-needed',
        '--extend-zooms-if-still-dropping',
        '--force',
        '--layer', 'parcels',
        geojson_path
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        file_size = os.path.getsize(pmtiles_path) / (1024 * 1024)
        print(f"  Created: {pmtiles_name} ({file_size:.1f} MB)")
        return pmtiles_path
    except subprocess.CalledProcessError as e:
        print(f"  ERROR: tippecanoe failed: {e.stderr.decode()}")
        return None

def upload_to_r2(pmtiles_path, source_id):
    """Upload PMTiles file to R2"""
    pmtiles_name = f"parcels_{source_id}.pmtiles"
    r2_key = f"parcels/{pmtiles_name}"

    print(f"\n  Uploading to R2: {pmtiles_name}")

    cmd = [
        'aws', 's3', 'cp',
        pmtiles_path,
        f's3://{R2_BUCKET}/{r2_key}',
        '--endpoint-url', R2_ENDPOINT
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        cdn_url = f"{CDN_BASE}/{r2_key}"
        print(f"  Uploaded: {cdn_url}")
        return cdn_url
    except subprocess.CalledProcessError as e:
        print(f"  ERROR: Upload failed: {e.stderr.decode()}")
        return None

def verify_upload(source_id):
    """Verify the uploaded file works"""
    pmtiles_name = f"parcels_{source_id}.pmtiles"
    url = f"{CDN_BASE}/parcels/{pmtiles_name}"

    try:
        cmd = ['pmtiles', 'show', url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"  Verified: {pmtiles_name}")
            return True
        else:
            print(f"  Verification failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  Verification error: {e}")
        return False

def cleanup_local(geojson_path, pmtiles_path):
    """Delete local files after successful upload"""
    for path in [geojson_path, pmtiles_path]:
        if path and os.path.exists(path):
            os.remove(path)
            print(f"  Deleted local: {os.path.basename(path)}")

def process_source(source_id, source, skip_existing=True, workers=40):
    """Process a single source: download, convert, upload, cleanup"""
    pmtiles_name = f"parcels_{source_id}.pmtiles"

    # Check if already exists
    if skip_existing:
        try:
            check_url = f"{CDN_BASE}/parcels/{pmtiles_name}"
            resp = requests.head(check_url, timeout=10)
            if resp.status_code == 200:
                size = int(resp.headers.get('content-length', 0)) / (1024 * 1024)
                print(f"\n  SKIP: {pmtiles_name} already exists ({size:.1f} MB)")
                return True
        except:
            pass

    start = time.time()

    # Download
    geojson_path = download_arcgis_features(source_id, source, workers=workers)
    if not geojson_path:
        return False

    # Convert
    pmtiles_path = convert_to_pmtiles(geojson_path, source_id)
    if not pmtiles_path:
        return False

    # Upload
    cdn_url = upload_to_r2(pmtiles_path, source_id)
    if not cdn_url:
        return False

    # Verify
    if not verify_upload(source_id):
        return False

    # Cleanup
    cleanup_local(geojson_path, pmtiles_path)

    elapsed = (time.time() - start) / 60
    print(f"\n  SUCCESS: {source_id} completed in {elapsed:.1f} minutes")

    return True

def main():
    parser = argparse.ArgumentParser(description='HITD Maps IL Cook County Scraper')
    parser.add_argument('--list', action='store_true', help='List available sources')
    parser.add_argument('--source', type=str, help='Specific source to process')
    parser.add_argument('--workers', type=int, default=40, help='Parallel workers per source')
    parser.add_argument('--no-skip', action='store_true', help='Re-download even if exists')
    args = parser.parse_args()

    if args.list:
        print("\nAvailable sources:")
        for sid, src in sorted(SOURCES.items(), key=lambda x: x[1]['priority']):
            print(f"  {sid}: {src['name']} ({src['records']:,} records)")
        return

    print("\n" + "="*80)
    print("HITD Maps - Illinois Cook County (Chicago) Scraper")
    print("="*80)

    sources_to_process = SOURCES
    if args.source:
        if args.source in SOURCES:
            sources_to_process = {args.source: SOURCES[args.source]}
        else:
            print(f"Unknown source: {args.source}")
            return

    print(f"Sources to process: {len(sources_to_process)}")
    print(f"Workers per source: {args.workers}")
    print(f"Skip existing: {not args.no_skip}")
    print("="*80)

    total = sum(s['records'] for s in sources_to_process.values())
    print(f"Total estimated records: {total:,}")

    successful = []
    failed = []

    for source_id, source in sorted(sources_to_process.items(), key=lambda x: x[1]['priority']):
        try:
            if process_source(source_id, source, skip_existing=not args.no_skip, workers=args.workers):
                successful.append(source_id)
            else:
                failed.append(source_id)
        except Exception as e:
            print(f"  ERROR: {source_id} failed with exception: {e}")
            failed.append(source_id)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    if successful:
        print(f"Successful: {len(successful)}")
        for s in successful:
            print(f"  ✓ {s}")
    if failed:
        print(f"Failed: {len(failed)}")
        for f in failed:
            print(f"  ✗ {f}")

    print("\n" + "="*80)
    print("Done! Update COVERAGE_STATUS.md with new data.")

if __name__ == '__main__':
    main()
