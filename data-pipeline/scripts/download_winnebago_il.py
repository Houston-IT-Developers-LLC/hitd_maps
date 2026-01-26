#!/usr/bin/env python3
"""
Download Winnebago County, Illinois parcel data from WinGIS MapServer.
Population: 285K, Expected parcels: ~120K
"""

import requests
import json
import os
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Output directory
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/downloads")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# WinGIS MapServer endpoint for Tax Parcels layer
SERVICE_URL = 'https://maps.wingis.org/public/rest/services/PropertySearch/MapServer/11'
OUTPUT_FILE = OUTPUT_DIR / 'parcels_il_winnebago.geojson'

# MapServer parameters
MAX_RECORD_COUNT = 2000  # MapServer limit
WORKERS = 8  # Parallel download workers


def get_feature_count(url):
    """Get total feature count from service."""
    params = {
        'where': '1=1',
        'returnCountOnly': 'true',
        'f': 'json'
    }

    print(f"Getting feature count from {url}...")
    response = requests.get(f"{url}/query", params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if 'count' in data:
        return data['count']
    elif 'error' in data:
        raise Exception(f"Error getting count: {data['error']}")
    else:
        raise Exception(f"Unexpected response: {data}")


def download_chunk(url, offset, max_records, chunk_id, total_chunks):
    """Download a chunk of features."""
    params = {
        'where': '1=1',
        'outFields': '*',
        'geometryPrecision': 6,
        'returnGeometry': 'true',
        'outSR': '4326',  # WGS84
        'resultOffset': offset,
        'resultRecordCount': max_records,
        'f': 'geojson'
    }

    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"  [{chunk_id}/{total_chunks}] Downloading offset {offset} (attempt {attempt + 1})...")
            response = requests.get(f"{url}/query", params=params, timeout=60)
            response.raise_for_status()

            data = response.json()

            if 'error' in data:
                print(f"  [{chunk_id}/{total_chunks}] Error: {data['error']}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise Exception(f"Failed after {max_retries} attempts: {data['error']}")

            feature_count = len(data.get('features', []))
            print(f"  [{chunk_id}/{total_chunks}] ✓ Got {feature_count} features")
            return data

        except requests.exceptions.RequestException as e:
            print(f"  [{chunk_id}/{total_chunks}] Request error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                raise

    return None


def download_all_features(url, total_count, max_records, workers):
    """Download all features in parallel chunks."""
    num_chunks = math.ceil(total_count / max_records)
    print(f"\nDownloading {total_count} features in {num_chunks} chunks using {workers} workers...")

    all_features = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for i in range(num_chunks):
            offset = i * max_records
            future = executor.submit(download_chunk, url, offset, max_records, i + 1, num_chunks)
            futures.append(future)

        for future in as_completed(futures):
            try:
                data = future.result()
                if data and 'features' in data:
                    all_features.extend(data['features'])
            except Exception as e:
                print(f"Chunk failed: {e}")

    return all_features


def main():
    print("=" * 80)
    print("Winnebago County, Illinois Parcel Download")
    print("Source: WinGIS PropertySearch MapServer")
    print("=" * 80)

    try:
        # Get total count
        total_count = get_feature_count(SERVICE_URL)
        print(f"\n✓ Total features: {total_count:,}")

        # Download all features
        features = download_all_features(SERVICE_URL, total_count, MAX_RECORD_COUNT, WORKERS)

        print(f"\n✓ Downloaded {len(features):,} features")

        # Create GeoJSON
        geojson = {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'source': 'WinGIS PropertySearch MapServer',
                'url': SERVICE_URL,
                'county': 'Winnebago County, Illinois',
                'downloaded': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_features': len(features),
                'crs': 'EPSG:4326'
            }
        }

        # Save to file
        print(f"\nSaving to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(geojson, f)

        file_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f"✓ Saved {len(features):,} features ({file_size_mb:.1f} MB)")
        print(f"\nOutput: {OUTPUT_FILE}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
