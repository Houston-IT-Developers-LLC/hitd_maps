#!/usr/bin/env python3
"""
Download parcel data for priority Alabama counties.
Based on download_ga_counties.py but customized for AL counties.
"""

import requests
import json
import os
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Output directory
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/downloads/al_counties")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Alabama county endpoints
AL_COUNTIES = {
    'parcels_al_montgomery_v2': {
        'url': 'https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/ArcGIS/rest/services/Montgomery_County_Parcels/FeatureServer/0',
        'county': 'Montgomery',
        'population': 228000,
        'max_per_request': 2000,
        'notes': 'State capital - Montgomery County GIS tax parcels 2025'
    },
    # Note: The following need API discovery
    # 'parcels_al_madison_huntsville': {
    #     'url': 'TBD',
    #     'county': 'Madison',
    #     'population': 388000,
    #     'max_per_request': 2000,
    #     'notes': 'Huntsville - need to find REST API endpoint'
    # },
    # 'parcels_al_shelby_v2': {
    #     'url': 'https://maps.shelbyal.com/gisserver/rest/services/ISV/ISV_Parcels/MapServer/0',
    #     'county': 'Shelby',
    #     'population': 223000,
    #     'max_per_request': 2000,
    #     'notes': 'Birmingham metro - requires authentication token'
    # },
    # 'parcels_al_baldwin': {
    #     'url': 'TBD',
    #     'county': 'Baldwin',
    #     'population': 231000,
    #     'max_per_request': 2000,
    #     'notes': 'Gulf coast - need to find REST API endpoint'
    # },
    # 'parcels_al_tuscaloosa': {
    #     'url': 'TBD',
    #     'county': 'Tuscaloosa',
    #     'population': 209000,
    #     'max_per_request': 2000,
    #     'notes': 'University of Alabama - need to find REST API endpoint'
    # },
}


def get_feature_count(url):
    """Get total feature count from service."""
    params = {
        'where': '1=1',
        'returnCountOnly': 'true',
        'f': 'json'
    }
    try:
        r = requests.get(f'{url}/query', params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            return data.get('count', 0)
    except Exception as e:
        print(f"Error getting count: {e}")
    return 0


def get_service_info(url):
    """Get service info including spatial reference."""
    try:
        r = requests.get(url, params={'f': 'json'}, timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Error getting service info: {e}")
    return {}


def download_batch(url, offset, limit, out_sr=4326):
    """Download a batch of features."""
    params = {
        'where': '1=1',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'geojson',
        'resultOffset': offset,
        'resultRecordCount': limit,
        'outSR': out_sr
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.get(f'{url}/query', params=params, timeout=120)
            if r.status_code == 200:
                data = r.json()
                if 'features' in data:
                    return data['features']
                elif 'error' in data:
                    print(f"  API error at offset {offset}: {data['error']}")
                    return []
        except requests.exceptions.Timeout:
            print(f"  Timeout at offset {offset}, attempt {attempt + 1}/{max_retries}")
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f"  Error at offset {offset}: {e}")
            time.sleep(1)

    return []


def download_service(name, config, max_workers=10):
    """Download all features from a service."""
    url = config['url']
    max_per_request = config.get('max_per_request', 2000)

    print(f"\n{'='*60}")
    print(f"Downloading: {name}")
    print(f"County: {config['county']} (pop: {config['population']:,})")
    print(f"URL: {url}")
    print(f"Notes: {config.get('notes', 'N/A')}")
    print(f"{'='*60}")

    # Get total count
    total = get_feature_count(url)
    if total == 0:
        print("  No features found or service unavailable")
        return None

    print(f"  Total features: {total:,}")

    # Get service info
    info = get_service_info(url)
    extent = info.get('extent', {})
    sr = extent.get('spatialReference', {})
    wkid = sr.get('wkid') or sr.get('latestWkid')
    print(f"  Source WKID: {wkid}")

    # Calculate batches
    num_batches = math.ceil(total / max_per_request)
    print(f"  Batches: {num_batches} ({max_per_request} features per batch)")

    # Download in parallel
    all_features = []
    completed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i in range(num_batches):
            offset = i * max_per_request
            future = executor.submit(download_batch, url, offset, max_per_request)
            futures[future] = offset

        for future in as_completed(futures):
            offset = futures[future]
            try:
                features = future.result()
                all_features.extend(features)
                completed += 1

                # Progress update
                pct = (completed / num_batches) * 100
                elapsed = time.time() - start_time
                rate = len(all_features) / elapsed if elapsed > 0 else 0
                eta = (total - len(all_features)) / rate if rate > 0 else 0

                print(f"\r  Progress: {completed}/{num_batches} batches ({pct:.1f}%) - {len(all_features):,} features - {rate:.0f}/sec - ETA: {eta:.0f}s    ", end='', flush=True)
            except Exception as e:
                print(f"\n  Error processing batch at offset {offset}: {e}")

    print()  # Newline after progress

    elapsed = time.time() - start_time
    print(f"  Downloaded {len(all_features):,} features in {elapsed:.1f}s")

    if len(all_features) == 0:
        return None

    # Create GeoJSON
    geojson = {
        'type': 'FeatureCollection',
        'features': all_features
    }

    # Save to file
    output_path = OUTPUT_DIR / f"{name}.geojson"
    print(f"  Saving to: {output_path}")

    with open(output_path, 'w') as f:
        json.dump(geojson, f)

    file_size = output_path.stat().st_size / (1024 * 1024)
    print(f"  File size: {file_size:.1f} MB")

    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Download parcel data for Alabama counties')
    parser.add_argument('--county', type=str, help='Download specific county only')
    parser.add_argument('--workers', type=int, default=10, help='Max parallel workers')
    parser.add_argument('--list', action='store_true', help='List available counties')
    args = parser.parse_args()

    if args.list:
        print("Available Alabama counties:")
        for name, config in AL_COUNTIES.items():
            print(f"  {name}")
            print(f"    County: {config['county']}")
            print(f"    Population: {config['population']:,}")
            print(f"    Notes: {config.get('notes', 'N/A')}")
            print()
        return

    counties_to_download = AL_COUNTIES
    if args.county:
        # Allow matching by county name or full key
        matched = None
        for key, config in AL_COUNTIES.items():
            if args.county.lower() in key.lower() or args.county.lower() == config['county'].lower():
                matched = {key: config}
                break

        if matched:
            counties_to_download = matched
        else:
            print(f"Unknown county: {args.county}")
            print(f"Available: {[c['county'] for c in AL_COUNTIES.values()]}")
            return

    print("="*60)
    print("ALABAMA COUNTY PARCEL DOWNLOADER")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Counties to download: {len(counties_to_download)}")
    print("="*60)

    results = []
    for name, config in counties_to_download.items():
        try:
            path = download_service(name, config, max_workers=args.workers)
            if path:
                results.append((name, config['county'], path))
        except Exception as e:
            print(f"Failed to download {name}: {e}")

    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)
    print(f"Successfully downloaded: {len(results)} counties")
    for name, county, path in results:
        file_size = path.stat().st_size / (1024 * 1024)
        print(f"  {county} County: {path.name} ({file_size:.1f} MB)")

    print("\nNext steps:")
    print("1. Reproject to WGS84: python3 scripts/smart_reproject_parcels.py")
    print("2. Convert to PMTiles: python3 scripts/batch_convert_pmtiles.py")
    print("3. Upload to R2: python3 scripts/upload_to_r2_boto3.py")


if __name__ == '__main__':
    main()
