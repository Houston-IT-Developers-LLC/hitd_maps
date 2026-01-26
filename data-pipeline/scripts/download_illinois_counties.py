#!/usr/bin/env python3
"""
Download parcel data for top 5 missing Illinois counties.
Uses ArcGIS REST API to download GeoJSON data.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from urllib.parse import urlencode

# Illinois counties to download
COUNTIES = {
    'peoria': {
        'name': 'Peoria County',
        'population': 181000,
        'url': 'https://gis.peoriacounty.gov/arcgis/rest/services/DP/Cadastral/FeatureServer/1',
        'output': 'parcels_il_peoria.geojson'
    },
    'st_clair': {
        'name': 'St. Clair County',
        'population': 257000,
        'url': 'https://arcgispublicmap.co.st-clair.il.us/server/rest/services/SCC_parcel_map_data/FeatureServer/29',
        'output': 'parcels_il_st_clair.geojson'
    }
}

def get_feature_count(url):
    """Get total feature count from ArcGIS service."""
    params = {
        'where': '1=1',
        'returnCountOnly': 'true',
        'f': 'json'
    }

    query_url = f"{url}/query"
    response = requests.get(query_url, params=params, timeout=30)

    if response.status_code == 200:
        data = response.json()
        return data.get('count', 0)
    return None

def download_geojson_chunks(url, output_path, chunk_size=1000):
    """Download parcel data in chunks using OID pagination."""
    print(f"Getting feature count...")
    total_features = get_feature_count(url)

    if not total_features:
        print("  Could not get feature count, trying direct download...")
        return download_geojson_direct(url, output_path)

    print(f"  Total features: {total_features:,}")

    # Collect all features
    all_features = []
    offset = 0

    while offset < total_features:
        print(f"  Downloading features {offset} to {offset + chunk_size}...")

        params = {
            'where': '1=1',
            'outFields': '*',
            'geometryPrecision': 6,
            'outSR': '4326',  # WGS84
            'f': 'geojson',
            'resultOffset': offset,
            'resultRecordCount': chunk_size
        }

        query_url = f"{url}/query"

        try:
            response = requests.get(query_url, params=params, timeout=120)

            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])

                if not features:
                    break

                all_features.extend(features)
                print(f"    Got {len(features)} features (total: {len(all_features)})")
                offset += chunk_size
                time.sleep(0.5)  # Be nice to the server
            else:
                print(f"    Error: HTTP {response.status_code}")
                break

        except Exception as e:
            print(f"    Error: {e}")
            break

    # Write combined GeoJSON
    if all_features:
        geojson = {
            "type": "FeatureCollection",
            "features": all_features
        }

        with open(output_path, 'w') as f:
            json.dump(geojson, f)

        print(f"  ✓ Saved {len(all_features):,} features to {output_path}")
        return True

    return False

def download_geojson_direct(url, output_path):
    """Try direct download without pagination (for smaller datasets)."""
    params = {
        'where': '1=1',
        'outFields': '*',
        'geometryPrecision': 6,
        'outSR': '4326',  # WGS84
        'f': 'geojson'
    }

    query_url = f"{url}/query"

    try:
        print(f"  Attempting direct download...")
        response = requests.get(query_url, params=params, timeout=300)

        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])

            if features:
                with open(output_path, 'w') as f:
                    json.dump(data, f)

                print(f"  ✓ Downloaded {len(features):,} features")
                return True
        else:
            print(f"  Error: HTTP {response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

    return False

def main():
    """Download all Illinois county parcels."""
    downloads_dir = Path(__file__).parent.parent / 'downloads' / 'illinois_counties'
    downloads_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Illinois Counties Parcel Data Downloader")
    print("=" * 60)

    successful = []
    failed = []

    for county_id, info in COUNTIES.items():
        print(f"\n{info['name']} (pop: {info['population']:,})")
        print(f"  URL: {info['url']}")

        output_path = downloads_dir / info['output']

        # Try download
        success = download_geojson_chunks(info['url'], output_path)

        if success and output_path.exists():
            size_mb = output_path.stat().st_size / 1024 / 1024
            print(f"  ✓ Success! File size: {size_mb:.1f} MB")
            successful.append(county_id)
        else:
            print(f"  ✗ Failed to download {info['name']}")
            failed.append(county_id)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Successful: {len(successful)} counties")
    for county_id in successful:
        print(f"  ✓ {COUNTIES[county_id]['name']}")

    if failed:
        print(f"\nFailed: {len(failed)} counties")
        for county_id in failed:
            print(f"  ✗ {COUNTIES[county_id]['name']}")

    return 0 if not failed else 1

if __name__ == '__main__':
    sys.exit(main())
