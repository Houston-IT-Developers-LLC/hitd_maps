#!/usr/bin/env python3
"""
Download St. Clair County parcels using OID-based chunking
(since pagination is not supported)
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

def get_oid_range(url):
    """Get min and max OID values."""
    params = {
        'where': '1=1',
        'returnIdsOnly': 'true',
        'f': 'json'
    }

    response = requests.get(f"{url}/query", params=params, timeout=120)
    if response.status_code == 200:
        data = response.json()
        oids = data.get('objectIds', [])
        if oids:
            return min(oids), max(oids), len(oids)
    return None, None, 0

def download_by_oid_range(url, output_path, chunk_size=1000):
    """Download using OID range queries."""
    print("Getting OID range...")
    min_oid, max_oid, total_oids = get_oid_range(url)

    if not min_oid:
        print("Failed to get OID range")
        return False

    print(f"  Min OID: {min_oid}, Max OID: {max_oid}, Total: {total_oids:,}")

    all_features = []
    current_oid = min_oid

    while current_oid <= max_oid:
        end_oid = current_oid + chunk_size - 1
        print(f"  Downloading OIDs {current_oid} to {end_oid}...")

        params = {
            'where': f'OBJECTID >= {current_oid} AND OBJECTID <= {end_oid}',
            'outFields': '*',
            'geometryPrecision': 6,
            'outSR': '4326',
            'f': 'geojson'
        }

        try:
            response = requests.get(f"{url}/query", params=params, timeout=120)

            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])

                if features:
                    all_features.extend(features)
                    print(f"    Got {len(features)} features (total: {len(all_features):,})")

                time.sleep(0.5)  # Be nice to the server
            else:
                print(f"    HTTP {response.status_code}, skipping...")

            current_oid += chunk_size

        except Exception as e:
            print(f"    Error: {e}")
            current_oid += chunk_size
            continue

    # Write combined GeoJSON
    if all_features:
        geojson = {
            "type": "FeatureCollection",
            "features": all_features
        }

        with open(output_path, 'w') as f:
            json.dump(geojson, f)

        print(f"✓ Saved {len(all_features):,} features to {output_path}")
        return True

    return False

def main():
    url = 'https://arcgispublicmap.co.st-clair.il.us/server/rest/services/SCC_parcel_map_data/MapServer/29'
    output_dir = Path(__file__).parent.parent / 'downloads' / 'illinois_counties'
    output_path = output_dir / 'parcels_il_st_clair.geojson'

    print("=" * 60)
    print("St. Clair County IL Parcel Downloader")
    print("=" * 60)
    print(f"URL: {url}")
    print()

    success = download_by_oid_range(url, output_path, chunk_size=500)

    if success and output_path.exists():
        size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"\n✓ Success! File size: {size_mb:.1f} MB")
        return 0
    else:
        print("\n✗ Download failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
