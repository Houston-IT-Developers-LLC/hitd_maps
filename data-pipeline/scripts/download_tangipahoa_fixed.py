#!/usr/bin/env python3
"""
Fixed download script for Tangipahoa Parish parcels with proper pagination.
"""

import json
import time
import urllib.request
from pathlib import Path

# Configuration
API_URL = "https://tangis.tangipahoa.org/server/rest/services/Cadastral/TaxParcel_A/FeatureServer/0"
MAX_RECORDS = 2000  # API limit per request
OUTPUT_FILE = Path(__file__).parent.parent / "downloads" / "parcels_la_tangipahoa_raw.geojson"

def log(message):
    """Print timestamped log message."""
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)

def get_feature_count():
    """Get total number of features."""
    query_url = f"{API_URL}/query?where=1=1&returnCountOnly=true&f=json"

    with urllib.request.urlopen(query_url, timeout=30) as response:
        data = json.loads(response.read().decode())
        return data.get('count', 0)

def download_chunk(offset):
    """Download a chunk of features starting at offset."""
    query_url = (
        f"{API_URL}/query?"
        f"where=1=1&"
        f"outFields=*&"
        f"f=geojson&"
        f"resultOffset={offset}&"
        f"resultRecordCount={MAX_RECORDS}"
    )

    log(f"Downloading features {offset} to {offset + MAX_RECORDS}...")

    with urllib.request.urlopen(query_url, timeout=60) as response:
        return json.loads(response.read().decode())

def main():
    """Download all features with pagination."""
    log("Starting Tangipahoa Parish parcel download...")

    # Get total count
    total_count = get_feature_count()
    log(f"Total features: {total_count:,}")

    # Download all features
    all_features = []
    offset = 0

    while offset < total_count:
        chunk = download_chunk(offset)
        features = chunk.get('features', [])

        if not features:
            log("No more features returned, stopping.")
            break

        all_features.extend(features)
        log(f"Progress: {len(all_features):,} / {total_count:,} ({len(all_features)/total_count*100:.1f}%)")

        offset += MAX_RECORDS
        time.sleep(0.5)  # Be nice to the server

    # Create GeoJSON output
    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }

    # Write to file
    log(f"Writing {len(all_features):,} features to {OUTPUT_FILE}")
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(geojson, f)

    size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
    log(f"Download complete! File size: {size_mb:.2f} MB")
    log(f"Downloaded {len(all_features):,} features")

if __name__ == "__main__":
    main()
