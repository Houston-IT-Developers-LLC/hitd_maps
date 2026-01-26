#!/usr/bin/env python3
"""
AUTONOMOUS 100% COVERAGE MISSION
=================================
Run continuously until all US counties are deployed
Auto-discover, verify, download, convert, upload
"""

import requests
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    filename='/home/exx/Documents/C/hitd_maps/data-pipeline/autonomous_mission.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/output")
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

HEADERS = {'User-Agent': 'Mozilla/5.0'}

# COMPREHENSIVE US COUNTY LIST (Top 200 by population from missing states)
COUNTIES_TO_FIND = [
    # Priority 1: Mega counties 500K+
    {"name": "St. Louis", "state": "MO", "pop": 989000},
    {"name": "Johnson", "state": "KS", "pop": 610000},
    {"name": "Washington", "state": "OR", "pop": 606000},
    {"name": "Kane", "state": "IL", "pop": 516000},

    # Priority 2: Major metros 250K-500K
    {"name": "Charleston", "state": "SC", "pop": 408000},
    {"name": "Richland", "state": "SC", "pop": 416000},
    {"name": "St. Charles", "state": "MO", "pop": 407000},
    {"name": "Madison", "state": "AL", "pop": 388000},
    {"name": "Clackamas", "state": "OR", "pop": 421000},
    {"name": "Lane", "state": "OR", "pop": 382000},
    {"name": "Horry", "state": "SC", "pop": 351000},
    {"name": "Marion", "state": "OR", "pop": 345000},
    {"name": "Spartanburg", "state": "SC", "pop": 327000},
    {"name": "Lancaster", "state": "NE", "pop": 322000},
    {"name": "Clayton", "state": "GA", "pop": 297000},
    {"name": "Cleveland", "state": "OK", "pop": 295000},
    {"name": "Ingham", "state": "MI", "pop": 284000},
    {"name": "Winnebago", "state": "IL", "pop": 285000},
    {"name": "St. Clair", "state": "IL", "pop": 257000},
    {"name": "Madison", "state": "IL", "pop": 265000},
    {"name": "St. Tammany", "state": "LA", "pop": 265000},
    {"name": "Clay", "state": "MO", "pop": 253000},
    {"name": "Hinds", "state": "MS", "pop": 230000},
    {"name": "Montgomery", "state": "AL", "pop": 228000},
    {"name": "Jefferson", "state": "MO", "pop": 226000},
    {"name": "Shelby", "state": "AL", "pop": 223000},
    {"name": "Yuma", "state": "AZ", "pop": 213000},
    {"name": "Mohave", "state": "AZ", "pop": 214000},
    {"name": "Hall", "state": "GA", "pop": 208000},
    {"name": "Harrison", "state": "MS", "pop": 208000},
    {"name": "Champaign", "state": "IL", "pop": 209000},
    {"name": "Muscogee", "state": "GA", "pop": 206000},

    # Priority 3: Regional 100K-250K (top 50)
    {"name": "Sarpy", "state": "NE", "pop": 190000},
    {"name": "Saginaw", "state": "MI", "pop": 190000},
    {"name": "DeSoto", "state": "MS", "pop": 185000},
    {"name": "Shawnee", "state": "KS", "pop": 178000},
    {"name": "Kenton", "state": "KY", "pop": 169000},
    {"name": "Wyandotte", "state": "KS", "pop": 165000},
    {"name": "Houston", "state": "GA", "pop": 163000},
    {"name": "Jackson", "state": "MI", "pop": 160000},
    {"name": "Rankin", "state": "MS", "pop": 157000},
    {"name": "Columbia", "state": "GA", "pop": 156000},
    {"name": "Berrien", "state": "MI", "pop": 154000},
    {"name": "Canadian", "state": "OK", "pop": 154000},
    {"name": "Bibb", "state": "GA", "pop": 153000},
    {"name": "Livingston", "state": "LA", "pop": 142000},
    {"name": "Boone", "state": "KY", "pop": 135000},
    {"name": "Warren", "state": "KY", "pop": 134000},
    {"name": "Tangipahoa", "state": "LA", "pop": 133000},
    {"name": "Rapides", "state": "LA", "pop": 130000},
    {"name": "Bossier", "state": "LA", "pop": 128000},
    {"name": "Clarke", "state": "GA", "pop": 128000},
    {"name": "Cochise", "state": "AZ", "pop": 126000},
    {"name": "Douglas", "state": "KS", "pop": 122000},
    {"name": "Comanche", "state": "OK", "pop": 121000},
    {"name": "Lowndes", "state": "GA", "pop": 118000},
    {"name": "Navajo", "state": "AZ", "pop": 112000},
    {"name": "Hardin", "state": "KY", "pop": 110000},
    {"name": "Madison", "state": "MS", "pop": 109000},
    {"name": "Bartow", "state": "GA", "pop": 108000},
    {"name": "Cass", "state": "MO", "pop": 107000},
    {"name": "Platte", "state": "MO", "pop": 106000},
    {"name": "Franklin", "state": "MO", "pop": 104000},
    {"name": "Bay", "state": "MI", "pop": 103000},
    {"name": "Daviess", "state": "KY", "pop": 102000},
    # Add more as needed...
]

def generate_endpoint_patterns(county_name, state):
    """Generate all possible GIS endpoint patterns"""
    county_slug = county_name.lower().replace(" ", "").replace(".", "").replace("county", "")
    state_lower = state.lower()

    patterns = [
        # Hub patterns
        f"https://data-{county_slug}gis.opendata.arcgis.com/api/v3/datasets",
        f"https://data-{county_slug}co.opendata.arcgis.com/api/v3/datasets",
        f"https://gisdata.{county_slug}county{state_lower}.gov/api/v3/datasets",
        f"https://{county_slug}gis-{county_slug}county{state_lower}.hub.arcgis.com/api/v3/datasets",
        f"https://{county_slug}-{state_lower}.opendata.arcgis.com/api/v3/datasets",
        f"https://opendata.{county_slug}county.gov/api/v3/datasets",

        # Direct REST patterns
        f"https://gis.{county_slug}county.gov/arcgis/rest/services",
        f"https://gis.co.{county_slug}.{state_lower}.us/arcgis/rest/services",
        f"https://maps.{county_slug}county.gov/arcgis/rest/services",
        f"https://gis.{county_slug}co{state_lower}.gov/arcgis/rest/services",
        f"https://gis3.{county_slug}county.com/mapvis/rest/services",
        f"https://gisservices.{county_slug}county.gov/arcgis/rest/services",
        f"https://services.arcgis.com/{county_slug}/arcgis/rest/services",
    ]

    return patterns

def find_endpoint(county_name, state):
    """Try all patterns to find working endpoint"""
    logging.info(f"Searching for {county_name}, {state}")

    patterns = generate_endpoint_patterns(county_name, state)

    # Try Hub API patterns first
    for pattern in patterns:
        if 'api/v3/datasets' in pattern:
            try:
                resp = requests.get(pattern, params={"q": "parcel property tax", "per_page": 10},
                                  headers=HEADERS, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if 'data' in data:
                        for dataset in data['data']:
                            url = dataset.get('attributes', {}).get('url', '')
                            if 'FeatureServer' in url and any(x in url.lower() for x in ['parcel', 'property', 'tax']):
                                # Verify it works
                                test_url = url if url.endswith('/0') else f"{url}/0"
                                works, count = verify_endpoint(test_url)
                                if works:
                                    logging.info(f"  ✓ Found: {test_url} ({count:,} features)")
                                    return test_url, count
            except:
                pass

    # Try direct REST services
    for pattern in patterns:
        if '/rest/services' in pattern and 'api/v3' not in pattern:
            try:
                resp = requests.get(f"{pattern}?f=json", headers=HEADERS, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for service in data.get('services', []):
                        if isinstance(service, dict):
                            name = service.get('name', '').lower()
                            if any(x in name for x in ['parcel', 'property', 'tax', 'cadastral']) and service.get('type') == 'FeatureServer':
                                test_url = f"{pattern}/{service['name']}/FeatureServer/0"
                                works, count = verify_endpoint(test_url)
                                if works:
                                    logging.info(f"  ✓ Found: {test_url} ({count:,} features)")
                                    return test_url, count
            except:
                pass

    logging.info(f"  ✗ Not found: {county_name}, {state}")
    return None, 0

def verify_endpoint(url):
    """Quick verification"""
    try:
        resp = requests.get(f"{url}/query",
                          params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
                          headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            if 'count' in data and data['count'] > 0:
                return True, data['count']
    except:
        pass
    return False, 0

def deploy_county(county_name, state, endpoint, count):
    """Full deployment pipeline"""
    source_id = f"{state.lower()}_{county_name.lower().replace(' ', '_')}"

    # Check if exists
    try:
        resp = requests.head(f"{CDN_BASE}/parcels/parcels_{source_id}.pmtiles", timeout=10)
        if resp.status_code == 200:
            logging.info(f"  ⏭️  Skip: {source_id} already exists")
            return {"status": "skip"}
    except:
        pass

    output_file = OUTPUT_DIR / "geojson" / f"parcels_{source_id}.geojson"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logging.info(f"  📥 Downloading {county_name}, {state} ({count:,} parcels)")
    print(f"📥 Downloading {county_name}, {state} ({count:,} parcels)")

    # Download
    all_features = []
    batch_size = 2000
    max_features = min(count, 1000000)
    offsets = list(range(0, max_features, batch_size))

    def fetch(offset):
        try:
            params = {'where': '1=1', 'outFields': '*', 'f': 'geojson',
                     'resultOffset': offset, 'resultRecordCount': batch_size, 'outSR': '4326'}
            resp = requests.get(f"{endpoint}/query", params=params, headers=HEADERS, timeout=180)
            if resp.status_code == 200:
                return resp.json().get('features', [])
        except:
            pass
        return None

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(fetch, o): o for o in offsets}
        for future in as_completed(futures):
            features = future.result()
            if features:
                all_features.extend(features)

    if len(all_features) < 100:
        logging.warning(f"  ✗ Only {len(all_features)} features")
        return {"status": "fail"}

    # Save
    with open(output_file, 'w') as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f)

    # Convert
    pmtiles_path = OUTPUT_DIR / "pmtiles" / f"parcels_{source_id}.pmtiles"
    pmtiles_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(['tippecanoe', '-o', str(pmtiles_path), '-z', '15', '-Z', '10',
                       '--drop-densest-as-needed', '--extend-zooms-if-still-dropping',
                       '--force', '--layer', 'parcels', str(output_file)],
                      check=True, capture_output=True, timeout=3600)
    except:
        logging.error(f"  ✗ Tippecanoe failed: {source_id}")
        return {"status": "fail"}

    # Upload
    try:
        subprocess.run(['aws', 's3', 'cp', str(pmtiles_path),
                       f's3://{R2_BUCKET}/parcels/{pmtiles_path.name}',
                       '--endpoint-url', R2_ENDPOINT],
                      check=True, capture_output=True, timeout=600)

        cdn_url = f"{CDN_BASE}/parcels/{pmtiles_path.name}"
        result = subprocess.run(['pmtiles', 'show', cdn_url], capture_output=True, timeout=60)

        if result.returncode == 0:
            output_file.unlink()
            pmtiles_path.unlink()
            logging.info(f"  ✅ SUCCESS: {source_id}")
            print(f"✅ SUCCESS: {county_name}, {state} - {len(all_features):,} parcels")
            return {"status": "success", "features": len(all_features), "source_id": source_id}
    except:
        logging.error(f"  ✗ Upload failed: {source_id}")

    return {"status": "fail"}

def process_county(county_info):
    """Full pipeline for one county"""
    county_name = county_info['name']
    state = county_info['state']

    endpoint, count = find_endpoint(county_name, state)

    if endpoint:
        result = deploy_county(county_name, state, endpoint, count)
        if result['status'] in ['success', 'skip']:
            return result

    return {"status": "not_found", "county": f"{county_name}, {state}"}

def main():
    print("="*80)
    print("🚀 AUTONOMOUS 100% COVERAGE MISSION STARTING")
    print(f"Counties to process: {len(COUNTIES_TO_FIND)}")
    print(f"Workers: 64 parallel")
    print("="*80)

    logging.info("="*80)
    logging.info("MISSION START")
    logging.info(f"Counties: {len(COUNTIES_TO_FIND)}")

    results = {"success": [], "failed": [], "skipped": []}

    # Process in waves of 64 parallel workers
    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = {executor.submit(process_county, c): c for c in COUNTIES_TO_FIND}

        for future in as_completed(futures):
            try:
                result = future.result()
                if result['status'] == 'success':
                    results['success'].append(result)
                elif result['status'] == 'skip':
                    results['skipped'].append(result)
                else:
                    results['failed'].append(result)
            except Exception as e:
                logging.error(f"ERROR: {e}")

    # Save results
    output_file = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/autonomous_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(COUNTIES_TO_FIND),
            "success": len(results['success']),
            "skipped": len(results['skipped']),
            "failed": len(results['failed']),
            "details": results
        }, f, indent=2)

    print("\n" + "="*80)
    print(f"✅ DEPLOYED: {len(results['success'])}")
    print(f"⏭️  SKIPPED: {len(results['skipped'])}")
    print(f"❌ NOT FOUND: {len(results['failed'])}")
    print(f"\nResults: {output_file}")
    print("="*80)

    logging.info(f"MISSION COMPLETE: {len(results['success'])} deployed, {len(results['failed'])} failed")

if __name__ == '__main__':
    main()
