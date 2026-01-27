#!/usr/bin/env python3
"""
Download Ascension Parish, LA parcels from ArcGIS REST API
"""

import json
import time
import requests
from pathlib import Path

# Configuration
SERVICE_URL = "https://gis.ascensionparishla.gov/server/rest/services/AssessorData/Assessor_Parcels/FeatureServer/317"
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/downloads")
OUTPUT_FILE = OUTPUT_DIR / "ascension_la_parcels.geojson"
MAX_RECORD_COUNT = 2000  # Server limit per request

def get_total_count():
    """Get total record count"""
    params = {
        'where': '1=1',
        'returnCountOnly': 'true',
        'f': 'json'
    }

    response = requests.get(f"{SERVICE_URL}/query", params=params)
    response.raise_for_status()
    data = response.json()

    return data.get('count', 0)

def download_parcels():
    """Download all parcels with pagination"""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading Ascension Parish parcels...")
    print(f"Service: {SERVICE_URL}")

    # Get total count
    total_count = get_total_count()
    print(f"Total parcels: {total_count:,}")

    if total_count == 0:
        print("No parcels found!")
        return False

    # Initialize feature collection
    feature_collection = {
        "type": "FeatureCollection",
        "features": []
    }

    # Download in batches
    offset = 0
    batch = 0

    while offset < total_count:
        batch += 1
        print(f"\nBatch {batch}: Downloading records {offset:,} to {min(offset + MAX_RECORD_COUNT, total_count):,}...")

        params = {
            'where': '1=1',
            'outFields': '*',
            'returnGeometry': 'true',
            'outSR': '102682',  # Keep original CRS for now
            'resultOffset': str(offset),
            'resultRecordCount': str(MAX_RECORD_COUNT),
            'f': 'geojson'
        }

        try:
            response = requests.get(f"{SERVICE_URL}/query", params=params, timeout=120)
            response.raise_for_status()

            data = response.json()

            if 'features' in data:
                features = data['features']
                feature_collection['features'].extend(features)
                print(f"  Downloaded {len(features):,} features (Total so far: {len(feature_collection['features']):,})")

                if len(features) < MAX_RECORD_COUNT:
                    print("  Last batch received")
                    break
            else:
                print(f"  No features in response: {data}")
                break

            offset += MAX_RECORD_COUNT
            time.sleep(0.5)  # Be nice to the server

        except Exception as e:
            print(f"  Error downloading batch: {e}")
            if offset > 0:
                print("  Saving partial data...")
                break
            else:
                raise

    # Save to file
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(feature_collection, f)

    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"Successfully downloaded {len(feature_collection['features']):,} parcels")
    print(f"File size: {file_size_mb:.1f} MB")
    print(f"Saved to: {OUTPUT_FILE}")

    return True

if __name__ == "__main__":
    try:
        success = download_parcels()
        if success:
            print("\n✓ Download complete!")
        else:
            print("\n✗ Download failed")
            exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
