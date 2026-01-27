#!/usr/bin/env python3
"""
Download Santa Cruz County, Arizona parcels from ArcGIS MapServer
Source: Santa Cruz County Assessor's Office
Endpoint: https://mapservices.santacruzcountyaz.gov/wagis01/rest/services/ParcelSearch/Parcels/MapServer/0
Total Features: ~43,184
CRS: EPSG:2223 (NAD83 / Arizona Central State Plane, feet)
"""

import requests
import json
import time
import sys
from pathlib import Path

# Configuration
BASE_URL = "https://mapservices.santacruzcountyaz.gov/wagis01/rest/services/ParcelSearch/Parcels/MapServer/0"
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/downloads")
OUTPUT_FILE = OUTPUT_DIR / "az_santa_cruz_parcels.geojson"
BATCH_SIZE = 1000  # MapServer max record count

def get_total_count():
    """Get total number of features"""
    url = f"{BASE_URL}/query"
    params = {
        'where': '1=1',
        'returnCountOnly': 'true',
        'f': 'json'
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get('count', 0)

def download_batch(offset, batch_size):
    """Download a batch of features"""
    url = f"{BASE_URL}/query"
    params = {
        'where': '1=1',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'geojson',
        'resultOffset': offset,
        'resultRecordCount': batch_size,
        'outSR': '4326'  # Request WGS84 directly
    }

    try:
        response = requests.get(url, params=params, timeout=120)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error downloading batch at offset {offset}: {e}")
        return None

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get total count
    print("Getting total feature count...")
    total = get_total_count()
    print(f"Total features: {total:,}")

    # Download all features
    all_features = []
    offset = 0

    while offset < total:
        print(f"Downloading features {offset:,} to {min(offset + BATCH_SIZE, total):,}...")
        batch = download_batch(offset, BATCH_SIZE)

        if batch and 'features' in batch:
            all_features.extend(batch['features'])
            print(f"  Downloaded {len(batch['features'])} features (total: {len(all_features):,})")
        else:
            print(f"  Failed to download batch at offset {offset}")
            time.sleep(2)
            continue

        offset += BATCH_SIZE
        time.sleep(0.5)  # Be nice to the server

    # Create final GeoJSON
    print(f"\nTotal features downloaded: {len(all_features):,}")

    geojson = {
        "type": "FeatureCollection",
        "features": all_features,
        "metadata": {
            "source": "Santa Cruz County Assessor's Office",
            "url": BASE_URL,
            "downloaded": time.strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(all_features),
            "original_crs": "EPSG:2223",
            "output_crs": "EPSG:4326"
        }
    }

    # Write to file
    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(geojson, f)

    file_size = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"✓ Download complete!")
    print(f"  File: {OUTPUT_FILE}")
    print(f"  Size: {file_size:.1f} MB")
    print(f"  Features: {len(all_features):,}")

if __name__ == "__main__":
    main()
