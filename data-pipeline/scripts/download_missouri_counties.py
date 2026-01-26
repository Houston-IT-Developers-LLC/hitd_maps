#!/usr/bin/env python3
"""
Download parcel data for priority Missouri counties from ArcGIS REST services.
Uses parallel workers to download quickly while respecting rate limits.

Priority Counties:
1. St. Charles (407K pop) - St. Louis metro
2. Clay (253K pop) - Kansas City metro
3. Jefferson (226K pop) - St. Louis metro
4. Platte (106K pop) - Kansas City metro
5. Cass (107K pop) - Kansas City metro
"""

import requests
import json
import os
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Output directory
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/downloads")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ArcGIS REST service endpoints for Missouri counties
SERVICES = {
    'parcels_mo_st_charles': {
        'url': 'https://gis.sccmo.org/scc_gis/rest/services/open_data/Tax_Information/FeatureServer/3',
        'county': 'St. Charles County',
        'population': 407000,
        'max_per_request': 1000,
        'notes': 'St. Charles County parcels - St. Louis metro'
    },
    'parcels_mo_clay': {
        'url': 'https://services7.arcgis.com/3c8lLdmDNevrTlaV/ArcGIS/rest/services/ClayCountyParcelService/FeatureServer/0',
        'county': 'Clay County',
        'population': 253000,
        'max_per_request': 2000,
        'notes': 'Clay County parcels - Kansas City metro'
    },
    # Jefferson, Platte, and Cass counties - APIs need to be discovered
    # Commenting out until we find working endpoints
    # 'parcels_mo_jefferson': {
    #     'url': 'TBD',
    #     'county': 'Jefferson County',
    #     'population': 226000,
    #     'max_per_request': 2000,
    #     'notes': 'Jefferson County parcels - St. Louis metro - API TBD'
    # },
    # 'parcels_mo_platte': {
    #     'url': 'TBD',
    #     'county': 'Platte County',
    #     'population': 106000,
    #     'max_per_request': 2000,
    #     'notes': 'Platte County parcels - Kansas City metro - API TBD'
    # },
    # 'parcels_mo_cass': {
    #     'url': 'TBD',
    #     'county': 'Cass County',
    #     'population': 107000,
    #     'max_per_request': 2000,
    #     'notes': 'Cass County parcels - Kansas City metro - API TBD'
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
    print(f"County: {config.get('county', 'N/A')}")
    print(f"Population: {config.get('population', 'N/A'):,}")
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
    parser = argparse.ArgumentParser(description='Download parcel data for priority Missouri counties')
    parser.add_argument('--county', type=str, help='Download specific county only')
    parser.add_argument('--workers', type=int, default=10, help='Max parallel workers')
    parser.add_argument('--list', action='store_true', help='List available counties')
    args = parser.parse_args()

    if args.list:
        print("\nAvailable Missouri Counties:")
        print("=" * 80)
        for name, config in SERVICES.items():
            status = "READY" if not config['url'].startswith('TBD') else "API TBD"
            print(f"{name:30s} - {config['county']:20s} - Pop: {config['population']:,} - {status}")
        print()
        return

    # Filter services
    services_to_download = {}
    if args.county:
        key = f"parcels_mo_{args.county.lower()}"
        if key in SERVICES:
            services_to_download[key] = SERVICES[key]
        else:
            print(f"Error: County '{args.county}' not found")
            print("Available counties:", list(SERVICES.keys()))
            return
    else:
        # Download only services with valid URLs
        services_to_download = {k: v for k, v in SERVICES.items() if not v['url'].startswith('TBD')}

    print(f"\nMissouri County Parcel Downloader")
    print(f"Will download {len(services_to_download)} counties")
    print(f"Max workers: {args.workers}")

    # Download all services
    results = {}
    for name, config in services_to_download.items():
        try:
            result = download_service(name, config, args.workers)
            results[name] = result
        except Exception as e:
            print(f"\nError downloading {name}: {e}")
            results[name] = None

    # Summary
    print("\n" + "=" * 60)
    print("Download Summary:")
    print("=" * 60)
    successful = [k for k, v in results.items() if v is not None]
    failed = [k for k, v in results.items() if v is None]

    print(f"Successful: {len(successful)}")
    for name in successful:
        print(f"  ✓ {name}")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for name in failed:
            print(f"  ✗ {name}")

    print(f"\nOutput directory: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
