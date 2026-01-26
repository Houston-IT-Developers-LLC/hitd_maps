#!/usr/bin/env python3
"""
Wave 3 Mega Scraper - Newly Discovered Sources
===============================================
OH Statewide: 6.3M parcels
WI Statewide: 3.56M parcels
TX Bexar: 710K parcels
NE Lancaster: 121K parcels
NV Washoe: 193K parcels
SD Lincoln: 66K parcels
SD Pennington: 54K parcels
WI Milwaukee: 280K parcels
WI Dane: 340K parcels
WI Waukesha: 38K parcels
WI Brown: 114K parcels
"""

import os
import sys
import json
import argparse
import subprocess
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Configuration
OUTPUT_DIR = "/home/exx/Documents/C/hitd_maps/data-pipeline/output"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

# Data sources - verified working APIs
SOURCES = {
    # MASSIVE: Ohio Statewide - 6.3M parcels
    "oh_statewide": {
        "url": "https://gis.ohiodnr.gov/arcgis_site2/rest/services/OIT_Services/odnr_landbase_v2/MapServer/4",
        "name": "Ohio Statewide",
        "estimated": 6318338,
        "batch_size": 2000,
    },
    # MASSIVE: Wisconsin Statewide - 3.56M parcels
    "wi_statewide": {
        "url": "https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels/FeatureServer/0",
        "name": "Wisconsin Statewide",
        "estimated": 3562907,
        "batch_size": 2000,
    },
    # LARGE: Texas Bexar County - 710K parcels
    "tx_bexar": {
        "url": "https://maps.bexar.org/arcgis/rest/services/Parcels/MapServer/0",
        "name": "Texas - Bexar County (San Antonio)",
        "estimated": 710772,
        "batch_size": 2000,
    },
    # WI Counties
    "wi_milwaukee": {
        "url": "https://lio.milwaukeecountywi.gov/arcgis/rest/services/PropertyInfo/Parcels_EagleView/MapServer/0",
        "name": "Wisconsin - Milwaukee County",
        "estimated": 280679,
        "batch_size": 2000,
    },
    "wi_dane": {
        "url": "https://maps.cityofmadison.com/arcgis/rest/services/Planning/GFLU_current/MapServer/2",
        "name": "Wisconsin - Dane County (Madison)",
        "estimated": 340669,
        "batch_size": 2000,
    },
    "wi_waukesha": {
        "url": "https://gis.waukeshacounty.gov/host/rest/services/Web_Tax_Parcel/FeatureServer/0",
        "name": "Wisconsin - Waukesha County",
        "estimated": 38000,
        "batch_size": 1000,
    },
    "wi_brown": {
        "url": "https://gis.browncountywi.gov/arcgis/rest/services/ParcelAndAddressFeatures/FeatureServer/22",
        "name": "Wisconsin - Brown County (Green Bay)",
        "estimated": 114265,
        "batch_size": 2000,
    },
    # NE/NV/SD Counties
    "ne_lancaster": {
        "url": "https://gis.lincoln.ne.gov/public/rest/services/Assessor/TaxParcels/FeatureServer/0",
        "name": "Nebraska - Lancaster County (Lincoln)",
        "estimated": 121851,
        "batch_size": 2000,
    },
    "nv_washoe": {
        "url": "https://wcgisweb.washoecounty.us/arcgis/rest/services/OpenData/OpenData/MapServer/0",
        "name": "Nevada - Washoe County (Reno)",
        "estimated": 192990,
        "batch_size": 1000,
    },
    "sd_lincoln": {
        "url": "https://gis.siouxfalls.gov/arcgis/rest/services/Data/Property/MapServer/1",
        "name": "South Dakota - Lincoln County (Sioux Falls)",
        "estimated": 66527,
        "batch_size": 2000,
    },
    "sd_pennington": {
        "url": "https://gis.rcgov.org/server/rest/services/OpenData/TaxParcels/MapServer/0",
        "name": "South Dakota - Pennington County (Rapid City)",
        "estimated": 54476,
        "batch_size": 2000,
    },
    # OH Counties (backup if statewide fails)
    "oh_franklin": {
        "url": "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0",
        "name": "Ohio - Franklin County (Columbus)",
        "estimated": 492206,
        "batch_size": 2000,
    },
    "oh_hamilton": {
        "url": "https://cagisonline.hamilton-co.org/arcgis/rest/services/COUNTYWIDE/Cadastral/MapServer/0",
        "name": "Ohio - Hamilton County (Cincinnati)",
        "estimated": 420209,
        "batch_size": 2000,
    },
}

def get_feature_count(base_url, timeout=30):
    """Get total feature count from service."""
    try:
        query_url = f"{base_url}/query"
        params = {
            'where': '1=1',
            'returnCountOnly': 'true',
            'f': 'json'
        }
        r = requests.get(query_url, params=params, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            if 'count' in data:
                return data['count']
    except Exception as e:
        print(f"  Error getting count: {e}")
    return None

def fetch_batch(args):
    """Fetch a batch of features."""
    url, offset, batch_size, batch_num, total_batches = args
    query_url = f"{url}/query"
    params = {
        'where': '1=1',
        'outFields': '*',
        'outSR': '4326',  # WGS84
        'f': 'geojson',
        'resultOffset': offset,
        'resultRecordCount': batch_size,
    }

    for attempt in range(3):
        try:
            r = requests.get(query_url, params=params, timeout=120)
            if r.status_code == 200:
                data = r.json()
                features = data.get('features', [])
                return features
        except Exception as e:
            if attempt < 2:
                continue
    return []

def download_source(source_key, source_info, workers=40, skip_existing=True):
    """Download a single source."""
    name = source_info['name']
    url = source_info['url']
    batch_size = source_info.get('batch_size', 2000)

    output_file = f"parcels_{source_key}.geojson"
    output_path = Path(OUTPUT_DIR) / output_file
    pmtiles_file = f"parcels_{source_key}.pmtiles"
    pmtiles_path = Path(OUTPUT_DIR) / pmtiles_file

    print(f"\n{'='*60}")
    print(f"Downloading: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    # Check if already exists in R2
    if skip_existing:
        try:
            r = requests.head(f"{CDN_BASE}/{pmtiles_file}", timeout=10)
            if r.status_code == 200:
                size_mb = int(r.headers.get('content-length', 0)) / (1024 * 1024)
                if size_mb > 1:  # More than 1MB
                    print(f"  SKIP: {pmtiles_file} exists ({size_mb:.1f} MB)")
                    return True
        except:
            pass

    # Get feature count
    count = get_feature_count(url)
    if not count:
        print(f"  ERROR: Could not get feature count")
        return False

    print(f"  Feature count: {count:,}")

    # Calculate batches
    total_batches = (count + batch_size - 1) // batch_size

    # Prepare batch args
    batch_args = [
        (url, i * batch_size, batch_size, i + 1, total_batches)
        for i in range(total_batches)
    ]

    # Download in parallel
    all_features = []
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_batch, args): args for args in batch_args}

        for future in as_completed(futures):
            features = future.result()
            all_features.extend(features)
            completed += 1

            if completed % 20 == 0 or completed == total_batches:
                print(f"  [{completed}/{total_batches}] {len(all_features):,} features")

    if not all_features:
        print(f"  ERROR: No features downloaded")
        return False

    print(f"\n  Saving {len(all_features):,} features...")

    # Save GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }

    with open(output_path, 'w') as f:
        json.dump(geojson, f)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Saved: {size_mb:.1f} MB")

    # Convert to PMTiles
    print(f"  Converting to PMTiles...")
    cmd = [
        'tippecanoe',
        '-o', str(pmtiles_path),
        '-l', 'parcels',
        '-zg',
        '--drop-densest-as-needed',
        '--extend-zooms-if-still-dropping',
        '--force',
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: tippecanoe failed: {result.stderr}")
        return False

    pmtiles_size = pmtiles_path.stat().st_size / (1024 * 1024)
    print(f"  Created: {pmtiles_size:.1f} MB")

    # Upload to R2
    print(f"  Uploading to R2...")
    upload_cmd = [
        'aws', 's3', 'cp',
        str(pmtiles_path),
        f's3://{R2_BUCKET}/{pmtiles_file}',
        '--endpoint-url', R2_ENDPOINT
    ]

    result = subprocess.run(upload_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: Upload failed: {result.stderr}")
        return False

    # Verify
    print(f"  Verifying...")
    try:
        r = requests.head(f"{CDN_BASE}/{pmtiles_file}", timeout=10)
        if r.status_code == 200:
            print(f"  SUCCESS!")
            # Clean up local files
            output_path.unlink(missing_ok=True)
            return True
    except:
        pass

    print(f"  WARNING: Verification failed")
    return False

def main():
    parser = argparse.ArgumentParser(description='Wave 3 Mega Scraper')
    parser.add_argument('--source', type=str, help='Specific source to download')
    parser.add_argument('--list', action='store_true', help='List available sources')
    parser.add_argument('--workers', type=int, default=40, help='Number of parallel workers')
    parser.add_argument('--no-skip', action='store_true', help='Download even if exists')
    parser.add_argument('--small-first', action='store_true', help='Process smaller sources first')
    parser.add_argument('--large-only', action='store_true', help='Only process OH and WI statewide')
    args = parser.parse_args()

    if args.list:
        print("\nAvailable sources:")
        print("-" * 80)
        for key, info in sorted(SOURCES.items(), key=lambda x: x[1]['estimated'], reverse=True):
            print(f"  {key:20} | {info['estimated']:>10,} features | {info['name']}")
        return

    print("\n" + "=" * 80)
    print("HITD Maps - Wave 3 Mega Scraper")
    print("=" * 80)

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    if args.source:
        if args.source not in SOURCES:
            print(f"Unknown source: {args.source}")
            print("Use --list to see available sources")
            return
        sources = {args.source: SOURCES[args.source]}
    elif args.large_only:
        sources = {k: v for k, v in SOURCES.items() if k in ['oh_statewide', 'wi_statewide']}
    elif args.small_first:
        sources = dict(sorted(SOURCES.items(), key=lambda x: x[1]['estimated']))
    else:
        sources = SOURCES

    results = []
    for key, info in sources.items():
        success = download_source(key, info, workers=args.workers, skip_existing=not args.no_skip)
        results.append((key, info['name'], success))

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    for key, name, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"  {key:20} | {status:8} | {name}")

    print("\nDone!")

if __name__ == '__main__':
    main()
