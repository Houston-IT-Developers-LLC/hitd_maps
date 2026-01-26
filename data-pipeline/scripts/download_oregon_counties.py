#!/usr/bin/env python3
"""
Download parcel data for top missing Oregon counties.

Priority counties:
1. Clackamas (421K pop) - Portland metro
2. Lane (382K pop) - Eugene
3. Marion (345K pop) - Salem
4. Jackson (223K pop)
5. Deschutes (198K pop)
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

# Oregon county parcel/taxlot services
SERVICES = {
    'parcels_or_lane': {
        'url': 'https://lcmaps.lanecounty.org/arcgis/rest/services/PlanMaps/AddressParcel/MapServer/1',
        'county': 'Lane',
        'population': 382000,
        'max_per_request': 2000,
        'notes': 'Lane County parcels (Eugene) - 159K features'
    },
    'parcels_or_clackamas_odf': {
        'url': 'https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/2',
        'county': 'Clackamas',
        'population': 421000,
        'max_per_request': 2000,
        'notes': 'Clackamas County taxlots via Oregon Dept of Forestry (Portland metro)'
    },
    'parcels_or_marion_odf': {
        'url': 'https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/23',
        'county': 'Marion',
        'population': 345000,
        'max_per_request': 2000,
        'notes': 'Marion County taxlots via Oregon Dept of Forestry (Salem)'
    },
    'parcels_or_jackson_odf': {
        'url': 'https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/14',
        'county': 'Jackson',
        'population': 223000,
        'max_per_request': 2000,
        'notes': 'Jackson County taxlots via Oregon Dept of Forestry'
    },
    'parcels_or_deschutes_odf': {
        'url': 'https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/8',
        'county': 'Deschutes',
        'population': 198000,
        'max_per_request': 2000,
        'notes': 'Deschutes County taxlots via Oregon Dept of Forestry (Bend)'
    },
}


def get_feature_count(url):
    """Get total feature count from service."""
    params = {
        'where': '1=1',
        'returnCountOnly': 'true',
        'f': 'json'
    }
    try:
        response = requests.get(f"{url}/query", params=params, timeout=30)
        data = response.json()
        if 'count' in data:
            return data['count']
        elif 'error' in data:
            print(f"  Error getting count: {data['error'].get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"  Exception getting count: {e}")
        return None


def download_batch(url, offset, max_per_request, service_name):
    """Download a batch of features."""
    params = {
        'where': '1=1',
        'outFields': '*',
        'returnGeometry': 'true',
        'outSR': '4326',  # WGS84
        'resultOffset': offset,
        'resultRecordCount': max_per_request,
        'f': 'geojson'
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{url}/query", params=params, timeout=120)
            if response.status_code == 200:
                data = response.json()
                if 'features' in data:
                    return data['features']
                elif 'error' in data:
                    print(f"    API Error at offset {offset}: {data['error'].get('message', 'Unknown')}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return []
            else:
                print(f"    HTTP {response.status_code} at offset {offset}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return []
        except Exception as e:
            print(f"    Error at offset {offset} (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return []
    return []


def download_service(service_name, config, workers=4):
    """Download all features from a service."""
    url = config['url']
    max_per_request = config['max_per_request']

    print(f"\n{'='*80}")
    print(f"Downloading: {service_name}")
    print(f"County: {config['county']} (pop: {config['population']:,})")
    print(f"URL: {url}")
    print(f"Notes: {config['notes']}")
    print(f"{'='*80}")

    # Get total count
    print("Getting feature count...")
    total_features = get_feature_count(url)

    if total_features is None:
        print(f"⚠️  Could not determine feature count. Skipping {service_name}")
        return False

    if total_features == 0:
        print(f"⚠️  No features found in {service_name}")
        return False

    print(f"✓ Total features: {total_features:,}")

    # Calculate batches
    num_batches = math.ceil(total_features / max_per_request)
    print(f"Downloading in {num_batches} batches of {max_per_request} features...")

    # Download in parallel
    all_features = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for i in range(num_batches):
            offset = i * max_per_request
            future = executor.submit(download_batch, url, offset, max_per_request, service_name)
            futures[future] = (i, offset)

        completed = 0
        for future in as_completed(futures):
            batch_num, offset = futures[future]
            features = future.result()
            all_features.extend(features)
            completed += 1

            elapsed = time.time() - start_time
            rate = completed / elapsed if elapsed > 0 else 0
            remaining = num_batches - completed
            eta = remaining / rate if rate > 0 else 0

            print(f"  Batch {completed}/{num_batches} ({len(features)} features, "
                  f"{len(all_features):,} total) - {rate:.1f} batches/sec, "
                  f"ETA: {int(eta)}s")

    # Create GeoJSON
    geojson = {
        'type': 'FeatureCollection',
        'features': all_features,
        'metadata': {
            'service_name': service_name,
            'county': config['county'],
            'population': config['population'],
            'source_url': url,
            'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_features': len(all_features),
            'notes': config['notes']
        }
    }

    # Save to file
    output_file = OUTPUT_DIR / f"{service_name}.geojson"
    print(f"\nSaving to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(geojson, f)

    file_size_mb = output_file.stat().st_size / 1024 / 1024
    elapsed_time = time.time() - start_time

    print(f"✅ Downloaded {len(all_features):,} features in {elapsed_time:.1f}s")
    print(f"   File size: {file_size_mb:.1f} MB")
    print(f"   Rate: {len(all_features) / elapsed_time:.1f} features/sec")

    return True


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description='Download Oregon county parcel data')
    parser.add_argument('--county', type=str, help='Download specific county only')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--list', action='store_true', help='List available services')

    args = parser.parse_args()

    if args.list:
        print("\nAvailable Oregon county services:")
        print(f"{'='*100}")
        for name, config in SERVICES.items():
            print(f"{name:30} | {config['county']:15} | Pop: {config['population']:>7,} | {config['notes']}")
        print(f"{'='*100}")
        return

    # Filter services
    services_to_download = SERVICES
    if args.county:
        services_to_download = {
            name: config for name, config in SERVICES.items()
            if args.county.lower() in config['county'].lower()
        }
        if not services_to_download:
            print(f"❌ No services found for county: {args.county}")
            print(f"\nAvailable counties: {', '.join(set(c['county'] for c in SERVICES.values()))}")
            return

    # Download all
    print(f"\n🚀 Starting download of {len(services_to_download)} Oregon county services")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Workers: {args.workers}")

    results = {}
    start_time = time.time()

    for service_name, config in services_to_download.items():
        try:
            success = download_service(service_name, config, workers=args.workers)
            results[service_name] = 'SUCCESS' if success else 'FAILED'
        except Exception as e:
            print(f"❌ Error downloading {service_name}: {e}")
            results[service_name] = f'ERROR: {e}'

    # Summary
    total_time = time.time() - start_time
    successful = sum(1 for status in results.values() if status == 'SUCCESS')

    print(f"\n{'='*80}")
    print(f"DOWNLOAD SUMMARY")
    print(f"{'='*80}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Successful: {successful}/{len(results)}")
    print(f"\nResults:")
    for service_name, status in results.items():
        icon = '✅' if status == 'SUCCESS' else '❌'
        print(f"  {icon} {service_name}: {status}")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
