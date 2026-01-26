#!/usr/bin/env python3
"""
Deploy St. Louis County, Missouri parcels
Source: St. Louis County GIS (maps.stlouisco.com)
Records: 401,471 parcels
Population: 989,000
"""

import requests
import json
import time
from pathlib import Path

# Configuration
SOURCE_NAME = "mo_stlouis_county"
BASE_URL = "https://maps.stlouisco.com/hosting/rest/services/Maps/AGS_Parcels/MapServer/0"
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/downloads")
OUTPUT_FILE = OUTPUT_DIR / f"parcels_{SOURCE_NAME}.geojson"

# ArcGIS REST API settings
MAX_RECORD_COUNT = 2000  # Standard limit for most ArcGIS services
TOTAL_RECORDS = 401471  # Known from count query

def download_chunk(offset, chunk_num, total_chunks):
    """Download a chunk of features using resultOffset pagination"""
    url = f"{BASE_URL}/query"

    params = {
        'where': '1=1',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'geojson',
        'outSR': '4326',  # Request WGS84
        'resultOffset': offset,
        'resultRecordCount': MAX_RECORD_COUNT
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            features = data.get('features', [])
            print(f"  Chunk {chunk_num}/{total_chunks}: {len(features)} features downloaded")
            return features

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s: {str(e)[:100]}")
                time.sleep(wait_time)
            else:
                print(f"  Failed after {max_retries} attempts: {str(e)}")
                raise

def download_all():
    """Download all parcels in chunks"""
    print(f"\n{'='*60}")
    print(f"St. Louis County, Missouri Parcel Download")
    print(f"{'='*60}")
    print(f"Source: {BASE_URL}")
    print(f"Expected records: {TOTAL_RECORDS:,}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    # Calculate number of chunks needed
    total_chunks = (TOTAL_RECORDS + MAX_RECORD_COUNT - 1) // MAX_RECORD_COUNT
    print(f"Downloading in {total_chunks} chunks of {MAX_RECORD_COUNT} features each")
    print()

    # Download all chunks using resultOffset pagination
    all_features = []
    start_time = time.time()

    for i in range(total_chunks):
        offset = i * MAX_RECORD_COUNT
        chunk_features = download_chunk(offset, i + 1, total_chunks)
        all_features.extend(chunk_features)

        # Progress update
        elapsed = time.time() - start_time
        rate = len(all_features) / elapsed if elapsed > 0 else 0
        remaining = (TOTAL_RECORDS - len(all_features)) / rate if rate > 0 else 0

        print(f"  Progress: {len(all_features):,}/{TOTAL_RECORDS:,} ({len(all_features)/TOTAL_RECORDS*100:.1f}%) "
              f"| Rate: {rate:.0f} features/sec | ETA: {remaining/60:.1f} min")

        # Rate limiting - be nice to the server
        time.sleep(0.5)

    # Create GeoJSON
    geojson = {
        'type': 'FeatureCollection',
        'features': all_features,
        'metadata': {
            'source': 'St. Louis County GIS',
            'url': BASE_URL,
            'download_date': time.strftime('%Y-%m-%d'),
            'total_features': len(all_features),
            'state': 'MO',
            'county': 'St. Louis County'
        }
    }

    # Write to file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nWriting {len(all_features):,} features to {OUTPUT_FILE}")

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(geojson, f)

    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    elapsed_min = (time.time() - start_time) / 60

    print(f"\n{'='*60}")
    print(f"✓ Download complete!")
    print(f"{'='*60}")
    print(f"Features downloaded: {len(all_features):,}")
    print(f"File size: {file_size_mb:.1f} MB")
    print(f"Time elapsed: {elapsed_min:.1f} minutes")
    print(f"Output file: {OUTPUT_FILE}")
    print()

    return OUTPUT_FILE

if __name__ == '__main__':
    try:
        output_file = download_all()
        print(f"\nNext steps:")
        print(f"1. Verify CRS: ogrinfo {output_file} -al -so | grep 'SRS'")
        print(f"2. Convert to PMTiles: tippecanoe -o parcels_{SOURCE_NAME}.pmtiles {output_file} -Z8 -z13 --drop-densest-as-needed")
        print(f"3. Upload to R2: aws s3 cp parcels_{SOURCE_NAME}.pmtiles s3://gspot-tiles/parcels/ --endpoint-url $R2_ENDPOINT")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
