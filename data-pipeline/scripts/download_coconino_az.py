#!/usr/bin/env python3
"""
Download Coconino County, Arizona parcels from ArcGIS REST API
"""

import requests
import json
import sys
from pathlib import Path

# Configuration
MAPSERVER_URL = "https://azwatermaps.azwater.gov/arcgis/rest/services/General/Parcels/MapServer/2"
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/downloads")
OUTPUT_FILE = OUTPUT_DIR / "coconino_az_parcels.geojson"
MAX_RECORDS = 2000

def get_total_count():
    """Get total parcel count"""
    url = f"{MAPSERVER_URL}/query"
    params = {
        'where': '1=1',
        'returnCountOnly': 'true',
        'f': 'json'
    }

    print("Fetching total count...")
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    if 'count' in data:
        return data['count']
    else:
        raise Exception(f"Failed to get count: {data}")

def download_parcels_batch(total_count):
    """Download parcels in batches using resultOffset"""
    url = f"{MAPSERVER_URL}/query"

    all_features = []
    offset = 0

    while offset < total_count:
        batch_num = (offset // MAX_RECORDS) + 1
        total_batches = (total_count + MAX_RECORDS - 1) // MAX_RECORDS

        print(f"Downloading batch {batch_num}/{total_batches} (offset {offset})...")

        params = {
            'where': '1=1',
            'outFields': '*',
            'outSR': '4326',  # WGS84
            'resultOffset': str(offset),
            'resultRecordCount': str(MAX_RECORDS),
            'f': 'geojson'
        }

        try:
            response = requests.get(url, params=params, timeout=120)
            response.raise_for_status()
            data = response.json()

            if 'features' in data:
                batch_size = len(data['features'])
                all_features.extend(data['features'])
                print(f"  ✓ Got {batch_size} features (total: {len(all_features)})")

                # If we got fewer records than requested, we're done
                if batch_size < MAX_RECORDS:
                    break

                offset += batch_size
            else:
                print(f"  ✗ No features in response: {data}")
                break

        except Exception as e:
            print(f"  ✗ Error downloading batch: {e}")
            # Try to continue with next batch
            offset += MAX_RECORDS
            continue

    return all_features

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"Coconino County, Arizona Parcel Download")
    print(f"Source: {MAPSERVER_URL}")
    print("=" * 60)

    # Get total count
    total_count = get_total_count()
    print(f"Total parcels to download: {total_count}")

    # Download all parcels
    features = download_parcels_batch(total_count)

    if not features:
        print("ERROR: No features downloaded!")
        sys.exit(1)

    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    # Save to file
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(geojson, f)

    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"✓ Downloaded {len(features)} parcels")
    print(f"✓ File size: {file_size_mb:.1f} MB")
    print(f"✓ Output: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
