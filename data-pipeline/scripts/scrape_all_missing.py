#!/usr/bin/env python3
"""
Master scraping script for ALL missing parcel data.
Priority: Hunting states first, then all others.

Usage:
    python3 scrape_all_missing.py --workers 50 --all
    python3 scrape_all_missing.py --workers 30 --hunting-only
    python3 scrape_all_missing.py --source ga_fulton --workers 20
"""

import os
import sys
import json
import time
import argparse
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

# Configuration
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/output/geojson")
PMTILES_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/output/pmtiles")
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

# All discovered API sources - HUNTING STATES FIRST
SOURCES = {
    # ============ PRIORITY 1: HUNTING STATES ============
    "ga_fulton": {
        "name": "Georgia - Fulton County (Atlanta)",
        "url": "https://services1.arcgis.com/AQDHTHDrZzfsFsB5/arcgis/rest/services/Tax_Parcels_2025/FeatureServer/0",
        "state": "GA",
        "records": 369847,
        "priority": 1,
        "hunting_state": True,
        "notes": "Downtown Atlanta - CRITICAL GAP"
    },
    "al_jefferson": {
        "name": "Alabama - Jefferson County (Birmingham)",
        "url": "https://jccgis.jccal.org/server/rest/services/BOE/BasemapERing/MapServer/0",
        "state": "AL",
        "records": 409509,
        "priority": 1,
        "hunting_state": True,
        "notes": "Birmingham metro - Major hunting region"
    },
    "ok_oklahoma": {
        "name": "Oklahoma - Oklahoma County (OKC)",
        "url": "https://services8.arcgis.com/euhkr1dAJeQBIjV0/arcgis/rest/services/TaxParcelsPublics_view/FeatureServer/0",
        "state": "OK",
        "records": 335695,
        "priority": 1,
        "hunting_state": True,
        "notes": "Oklahoma City metro"
    },
    "sd_minnehaha": {
        "name": "South Dakota - Minnehaha County (Sioux Falls)",
        "url": "https://gis.siouxfalls.gov/arcgis/rest/services/Data/Property/MapServer/1",
        "state": "SD",
        "records": 66527,
        "priority": 1,
        "hunting_state": True,
        "notes": "Sioux Falls area - pheasant hunting"
    },

    # ============ PRIORITY 2: RHODE ISLAND (MISSING STATE) ============
    "ri_statewide": {
        "name": "Rhode Island - Statewide",
        "url": "https://risegis.ri.gov/hosting/rest/services/RIDEM/Tax_Parcels/MapServer/0",
        "state": "RI",
        "records": 394167,
        "priority": 2,
        "hunting_state": False,
        "notes": "ONLY MISSING STATE - Must complete!"
    },

    # ============ PRIORITY 3: LOUISIANA PARISHES ============
    "la_caddo": {
        "name": "Louisiana - Caddo Parish (Shreveport)",
        "url": "https://gis.caddo.org/arcgis/rest/services/Cadastral/Parcels/MapServer/0",
        "state": "LA",
        "records": 150000,
        "priority": 3,
        "hunting_state": True,
        "notes": "Shreveport - duck hunting"
    },
    "la_calcasieu": {
        "name": "Louisiana - Calcasieu Parish (Lake Charles)",
        "url": "https://maps.calcasieuparish.gov/arcgis/rest/services/Parcels/Parcels/MapServer/0",
        "state": "LA",
        "records": 100000,
        "priority": 3,
        "hunting_state": True,
        "notes": "Lake Charles area"
    },
    "la_ouachita": {
        "name": "Louisiana - Ouachita Parish (Monroe)",
        "url": "https://gis.opconline.us/arcgis/rest/services/Parcels/MapServer/0",
        "state": "LA",
        "records": 80000,
        "priority": 3,
        "hunting_state": True,
        "notes": "Monroe area - deer hunting"
    },
    "la_rapides": {
        "name": "Louisiana - Rapides Parish (Alexandria)",
        "url": "https://maps.rapidesparish.org/arcgis/rest/services/Parcels/MapServer/0",
        "state": "LA",
        "records": 70000,
        "priority": 3,
        "hunting_state": True,
        "notes": "Alexandria - central LA hunting"
    },

    # ============ PRIORITY 4: OTHER MAJOR METROS ============
    "ky_fayette": {
        "name": "Kentucky - Fayette County (Lexington)",
        "url": "https://maps.lexingtonky.gov/lfucggis/rest/services/Property/PropertyInformation/MapServer/0",
        "state": "KY",
        "records": 140000,
        "priority": 4,
        "hunting_state": True,
        "notes": "Lexington metro"
    },
    "mo_stlouis_city": {
        "name": "Missouri - St. Louis City",
        "url": "https://services2.arcgis.com/w657bnjzrjguNyOy/arcgis/rest/services/prcl/FeatureServer/0",
        "state": "MO",
        "records": 130000,
        "priority": 4,
        "hunting_state": False,
        "notes": "St. Louis City - separate from county"
    },
    "mo_stlouis_county": {
        "name": "Missouri - St. Louis County",
        "url": "https://gis.stlouisco.com/arcgis/rest/services/OpenData/LocatorParcels/MapServer/0",
        "state": "MO",
        "records": 400000,
        "priority": 4,
        "hunting_state": False,
        "notes": "St. Louis County"
    },

    # ============ PRIORITY 5: CALIFORNIA MAJOR COUNTIES ============
    "ca_san_bernardino": {
        "name": "California - San Bernardino County",
        "url": "https://services1.arcgis.com/iyJY0nTUG0wwEF7J/arcgis/rest/services/Parcels/FeatureServer/0",
        "state": "CA",
        "records": 800000,
        "priority": 5,
        "hunting_state": False,
        "notes": "Largest county by area in USA"
    },
    "ca_alameda": {
        "name": "California - Alameda County (Oakland)",
        "url": "https://services3.arcgis.com/i2dkYWmb4wHvYQGi/arcgis/rest/services/AC_Parcels/FeatureServer/0",
        "state": "CA",
        "records": 500000,
        "priority": 5,
        "hunting_state": False,
        "notes": "Oakland, Berkeley"
    },
    "ca_santa_clara": {
        "name": "California - Santa Clara County (San Jose)",
        "url": "https://services5.arcgis.com/XDDI5k5RkDCOa8ng/arcgis/rest/services/Parcels/FeatureServer/0",
        "state": "CA",
        "records": 500000,
        "priority": 5,
        "hunting_state": False,
        "notes": "Silicon Valley"
    },
    "ca_contra_costa": {
        "name": "California - Contra Costa County",
        "url": "https://services1.arcgis.com/j9oXuKXY0mWPZu3o/arcgis/rest/services/Parcels/FeatureServer/0",
        "state": "CA",
        "records": 380000,
        "priority": 5,
        "hunting_state": False,
        "notes": "East Bay"
    },
    "ca_kern": {
        "name": "California - Kern County (Bakersfield)",
        "url": "https://maps.kerncounty.com/kcgis/rest/services/ParcelsPublic/MapServer/0",
        "state": "CA",
        "records": 350000,
        "priority": 5,
        "hunting_state": True,
        "notes": "Bakersfield - Central Valley hunting"
    },
    "ca_ventura": {
        "name": "California - Ventura County",
        "url": "https://maps.ventura.org/arcgis/rest/services/Parcels/MapServer/0",
        "state": "CA",
        "records": 280000,
        "priority": 5,
        "hunting_state": False,
        "notes": "Ventura, Oxnard"
    },

    # ============ PRIORITY 6: MORE HUNTING STATES ============
    "mi_genesee": {
        "name": "Michigan - Genesee County (Flint)",
        "url": "https://services1.arcgis.com/6X0xvnFh7Iit9DzO/arcgis/rest/services/Parcels/FeatureServer/0",
        "state": "MI",
        "records": 180000,
        "priority": 6,
        "hunting_state": True,
        "notes": "Flint area"
    },
    "mi_washtenaw": {
        "name": "Michigan - Washtenaw County (Ann Arbor)",
        "url": "https://gisservices.ewashtenaw.org/arcgis/rest/services/Parcels/MapServer/0",
        "state": "MI",
        "records": 140000,
        "priority": 6,
        "hunting_state": True,
        "notes": "Ann Arbor"
    },
    "mi_ingham": {
        "name": "Michigan - Ingham County (Lansing)",
        "url": "https://services1.arcgis.com/VD1dLqy4vxfEgEfZ/arcgis/rest/services/Parcels/FeatureServer/0",
        "state": "MI",
        "records": 120000,
        "priority": 6,
        "hunting_state": True,
        "notes": "State capital"
    },
    "wi_dane": {
        "name": "Wisconsin - Dane County (Madison)",
        "url": "https://gis.countyofdane.com/arcgis/rest/services/Parcels/MapServer/0",
        "state": "WI",
        "records": 200000,
        "priority": 6,
        "hunting_state": True,
        "notes": "Madison - already have statewide but adding detail"
    },
    "mn_statewide": {
        "name": "Minnesota - Statewide Parcels",
        "url": "https://services.arcgis.com/8df8p0NlLFEShl0r/arcgis/rest/services/MNDNR_Parcels/FeatureServer/0",
        "state": "MN",
        "records": 3000000,
        "priority": 6,
        "hunting_state": True,
        "notes": "Minnesota statewide - major hunting state!"
    },

    # ============ PRIORITY 7: OREGON STATEWIDE ============
    "or_statewide": {
        "name": "Oregon - Statewide Tax Lots",
        "url": "https://gis.oregon.gov/arcgis/rest/services/Cadastre/TaxLots/MapServer/0",
        "state": "OR",
        "records": 1800000,
        "priority": 7,
        "hunting_state": True,
        "notes": "Oregon statewide - elk hunting"
    },

    # ============ PRIORITY 8: WYOMING STATEWIDE ============
    "wy_statewide": {
        "name": "Wyoming - Statewide Parcels",
        "url": "https://services.arcgis.com/HRPe58bUyBqyyiCt/arcgis/rest/services/Wyoming_Parcels/FeatureServer/0",
        "state": "WY",
        "records": 400000,
        "priority": 8,
        "hunting_state": True,
        "notes": "Wyoming - antelope, elk hunting"
    },

    # ============ PRIORITY 9: SOUTH CAROLINA STATEWIDE ============
    "sc_statewide": {
        "name": "South Carolina - Statewide",
        "url": "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/SC_Parcels/FeatureServer/0",
        "state": "SC",
        "records": 2500000,
        "priority": 9,
        "hunting_state": True,
        "notes": "SC statewide - deer hunting"
    },

    # ============ PRIORITY 10: KANSAS STATEWIDE ============
    "ks_statewide": {
        "name": "Kansas - Statewide Parcels",
        "url": "https://services.kansasgis.org/arcgis8/rest/services/DASC/Parcels/MapServer/0",
        "state": "KS",
        "records": 1500000,
        "priority": 10,
        "hunting_state": True,
        "notes": "Kansas - pheasant hunting"
    },
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_feature_count(url):
    """Get the actual feature count from an ArcGIS service."""
    try:
        query_url = f"{url}/query?where=1%3D1&returnCountOnly=true&f=json"
        resp = requests.get(query_url, timeout=30, headers=HEADERS)
        data = resp.json()
        return data.get('count', 0)
    except Exception as e:
        print(f"  Error getting count: {e}")
        return 0

def download_features(source_id, source_info, workers=20, batch_size=2000):
    """Download all features from an ArcGIS service."""
    url = source_info['url']
    output_file = OUTPUT_DIR / f"parcels_{source_info['state'].lower()}_{source_id.split('_', 1)[1] if '_' in source_id else source_id}.geojson"

    print(f"\n{'='*60}")
    print(f"Downloading: {source_info['name']}")
    print(f"URL: {url}")
    print(f"Expected records: {source_info['records']:,}")
    print(f"Output: {output_file}")
    print(f"{'='*60}")

    # Get actual count
    actual_count = get_feature_count(url)
    if actual_count == 0:
        print(f"  WARNING: Could not get feature count, using estimate")
        actual_count = source_info['records']
    else:
        print(f"  Actual feature count: {actual_count:,}")

    # Calculate batches
    num_batches = (actual_count + batch_size - 1) // batch_size
    print(f"  Will download in {num_batches} batches of {batch_size}")

    all_features = []
    failed_batches = []

    def download_batch(offset):
        """Download a single batch."""
        query_url = f"{url}/query"
        params = {
            'where': '1=1',
            'outFields': '*',
            'outSR': '4326',
            'f': 'geojson',
            'resultOffset': offset,
            'resultRecordCount': batch_size
        }

        for attempt in range(3):
            try:
                resp = requests.get(query_url, params=params, timeout=120, headers=HEADERS)
                if resp.status_code == 200:
                    data = resp.json()
                    features = data.get('features', [])
                    return offset, features, None
                else:
                    return offset, [], f"HTTP {resp.status_code}"
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    return offset, [], str(e)
        return offset, [], "Max retries exceeded"

    # Download in parallel
    offsets = list(range(0, actual_count, batch_size))
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(download_batch, offset): offset for offset in offsets}

        for future in as_completed(futures):
            offset, features, error = future.result()
            completed += 1

            if error:
                failed_batches.append((offset, error))
                print(f"  [{completed}/{num_batches}] Batch {offset}: FAILED - {error}")
            else:
                all_features.extend(features)
                if completed % 10 == 0 or completed == num_batches:
                    print(f"  [{completed}/{num_batches}] Downloaded {len(all_features):,} features...")

    # Retry failed batches
    if failed_batches:
        print(f"\n  Retrying {len(failed_batches)} failed batches...")
        for offset, _ in failed_batches:
            _, features, error = download_batch(offset)
            if features:
                all_features.extend(features)
                print(f"  Retry batch {offset}: OK ({len(features)} features)")
            else:
                print(f"  Retry batch {offset}: STILL FAILED - {error}")

    # Save GeoJSON
    print(f"\n  Saving {len(all_features):,} features to {output_file}...")
    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(geojson, f)

    file_size = output_file.stat().st_size / (1024 * 1024)
    print(f"  Saved: {file_size:.1f} MB")

    return output_file, len(all_features)

def convert_to_pmtiles(geojson_file):
    """Convert GeoJSON to PMTiles using tippecanoe."""
    pmtiles_file = PMTILES_DIR / geojson_file.name.replace('.geojson', '.pmtiles')
    PMTILES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n  Converting to PMTiles: {pmtiles_file.name}")

    cmd = [
        'tippecanoe',
        '-o', str(pmtiles_file),
        '-z', '14',
        '-Z', '5',
        '--drop-densest-as-needed',
        '--extend-zooms-if-still-dropping',
        '--force',
        '-l', 'parcels',
        str(geojson_file)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            file_size = pmtiles_file.stat().st_size / (1024 * 1024)
            print(f"  Created: {pmtiles_file.name} ({file_size:.1f} MB)")
            return pmtiles_file
        else:
            print(f"  ERROR: {result.stderr}")
            return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def upload_to_r2(pmtiles_file):
    """Upload PMTiles file to Cloudflare R2."""
    remote_path = f"s3://{R2_BUCKET}/parcels/{pmtiles_file.name}"

    print(f"\n  Uploading to R2: {pmtiles_file.name}")

    cmd = [
        'aws', 's3', 'cp',
        str(pmtiles_file),
        remote_path,
        '--endpoint-url', R2_ENDPOINT
    ]

    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
    env['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=1800)
        if result.returncode == 0:
            public_url = f"{R2_PUBLIC}/parcels/{pmtiles_file.name}"
            print(f"  Uploaded: {public_url}")
            return public_url
        else:
            print(f"  ERROR: {result.stderr}")
            return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def verify_upload(pmtiles_name):
    """Verify the file exists and is accessible on R2."""
    url = f"{R2_PUBLIC}/parcels/{pmtiles_name}"
    try:
        resp = requests.head(url, timeout=10)
        if resp.status_code == 200:
            size_mb = int(resp.headers.get('content-length', 0)) / (1024 * 1024)
            print(f"  Verified: {pmtiles_name} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"  NOT FOUND: {pmtiles_name} (HTTP {resp.status_code})")
            return False
    except Exception as e:
        print(f"  ERROR verifying: {e}")
        return False

def cleanup_local(geojson_file, pmtiles_file):
    """Delete local files after successful upload."""
    try:
        if geojson_file and geojson_file.exists():
            geojson_file.unlink()
            print(f"  Deleted local: {geojson_file.name}")
        if pmtiles_file and pmtiles_file.exists():
            pmtiles_file.unlink()
            print(f"  Deleted local: {pmtiles_file.name}")
    except Exception as e:
        print(f"  Error cleaning up: {e}")

def process_source(source_id, source_info, workers=20, skip_existing=True):
    """Full pipeline: download -> convert -> upload -> cleanup."""
    pmtiles_name = f"parcels_{source_info['state'].lower()}_{source_id.split('_', 1)[1] if '_' in source_id else source_id}.pmtiles"

    # Check if already exists on R2
    if skip_existing:
        url = f"{R2_PUBLIC}/parcels/{pmtiles_name}"
        try:
            resp = requests.head(url, timeout=10)
            if resp.status_code == 200:
                size_mb = int(resp.headers.get('content-length', 0)) / (1024 * 1024)
                if size_mb > 1:  # Skip if > 1MB (not empty)
                    print(f"\n  SKIPPING {source_id}: Already exists on R2 ({size_mb:.1f} MB)")
                    return True
        except:
            pass

    start_time = time.time()

    # Download
    geojson_file, feature_count = download_features(source_id, source_info, workers)
    if feature_count == 0:
        print(f"  FAILED: No features downloaded")
        return False

    # Convert
    pmtiles_file = convert_to_pmtiles(geojson_file)
    if not pmtiles_file:
        print(f"  FAILED: Could not convert to PMTiles")
        return False

    # Upload
    public_url = upload_to_r2(pmtiles_file)
    if not public_url:
        print(f"  FAILED: Could not upload to R2")
        return False

    # Verify
    if not verify_upload(pmtiles_file.name):
        print(f"  WARNING: Could not verify upload")
        return False

    # Cleanup
    cleanup_local(geojson_file, pmtiles_file)

    elapsed = time.time() - start_time
    print(f"\n  SUCCESS: {source_id} completed in {elapsed/60:.1f} minutes")
    return True

def main():
    parser = argparse.ArgumentParser(description='Scrape all missing parcel data')
    parser.add_argument('--workers', type=int, default=30, help='Number of parallel workers')
    parser.add_argument('--all', action='store_true', help='Process all sources')
    parser.add_argument('--hunting-only', action='store_true', help='Only process hunting states')
    parser.add_argument('--source', type=str, help='Process specific source')
    parser.add_argument('--priority', type=int, help='Process sources up to this priority level')
    parser.add_argument('--list', action='store_true', help='List all available sources')
    parser.add_argument('--no-skip', action='store_true', help='Do not skip existing files')
    args = parser.parse_args()

    if args.list:
        print("\nAvailable sources:")
        print("=" * 80)
        for priority in sorted(set(s['priority'] for s in SOURCES.values())):
            print(f"\n--- Priority {priority} ---")
            for source_id, info in sorted(SOURCES.items(), key=lambda x: x[1]['priority']):
                if info['priority'] == priority:
                    hunting = "🦌" if info.get('hunting_state') else "  "
                    print(f"  {hunting} {source_id}: {info['name']} ({info['records']:,} records)")
        return

    # Select sources to process
    sources_to_process = []

    if args.source:
        if args.source in SOURCES:
            sources_to_process = [(args.source, SOURCES[args.source])]
        else:
            print(f"Unknown source: {args.source}")
            return
    elif args.hunting_only:
        sources_to_process = [(k, v) for k, v in SOURCES.items() if v.get('hunting_state')]
    elif args.priority:
        sources_to_process = [(k, v) for k, v in SOURCES.items() if v['priority'] <= args.priority]
    elif args.all:
        sources_to_process = list(SOURCES.items())
    else:
        print("Specify --all, --hunting-only, --source, or --priority")
        parser.print_help()
        return

    # Sort by priority
    sources_to_process.sort(key=lambda x: x[1]['priority'])

    print(f"\n{'='*80}")
    print(f"HITD Maps - Missing Parcel Data Scraper")
    print(f"{'='*80}")
    print(f"Sources to process: {len(sources_to_process)}")
    print(f"Workers per source: {args.workers}")
    print(f"Skip existing: {not args.no_skip}")
    print(f"{'='*80}")

    total_records = sum(s['records'] for _, s in sources_to_process)
    print(f"Total estimated records: {total_records:,}")

    # Process each source
    results = []
    for source_id, source_info in sources_to_process:
        success = process_source(source_id, source_info, args.workers, not args.no_skip)
        results.append((source_id, success))

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    successes = [r for r in results if r[1]]
    failures = [r for r in results if not r[1]]

    print(f"Successful: {len(successes)}")
    for source_id, _ in successes:
        print(f"  ✓ {source_id}")

    if failures:
        print(f"\nFailed: {len(failures)}")
        for source_id, _ in failures:
            print(f"  ✗ {source_id}")

    print(f"\n{'='*80}")
    print("Done! Update COVERAGE_STATUS.md with new data.")

if __name__ == '__main__':
    main()
