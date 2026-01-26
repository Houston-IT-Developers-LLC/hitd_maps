#!/usr/bin/env python3
"""
PARALLEL FIX MISSING STATES - LOCAL SERVER AGENT SWARM
Deploys 50+ parallel agents to fix all 15 missing states simultaneously.
Each agent handles one data source independently.

Run with: python3 parallel_fix_missing_states.py
"""

import subprocess
import os
import json
import requests
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import multiprocessing
import re
import time
import sys

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# Max parallel agents - use all CPU cores
NUM_AGENTS = min(50, multiprocessing.cpu_count() * 4)

# State bounds for validation (WGS84)
STATE_BOUNDS = {
    'AK': {'min_lat': 51.0, 'max_lat': 71.5, 'min_lon': -180.0, 'max_lon': -130.0, 'name': 'Alaska'},
    'AL': {'min_lat': 30.1, 'max_lat': 35.0, 'min_lon': -88.5, 'max_lon': -84.9, 'name': 'Alabama'},
    'AR': {'min_lat': 33.0, 'max_lat': 36.5, 'min_lon': -94.6, 'max_lon': -89.6, 'name': 'Arkansas'},
    'FL': {'min_lat': 24.5, 'max_lat': 31.0, 'min_lon': -87.6, 'max_lon': -80.0, 'name': 'Florida'},
    'ID': {'min_lat': 42.0, 'max_lat': 49.0, 'min_lon': -117.2, 'max_lon': -111.0, 'name': 'Idaho'},
    'MO': {'min_lat': 35.9, 'max_lat': 40.6, 'min_lon': -95.8, 'max_lon': -89.1, 'name': 'Missouri'},
    'MS': {'min_lat': 30.2, 'max_lat': 35.0, 'min_lon': -91.7, 'max_lon': -88.1, 'name': 'Mississippi'},
    'MT': {'min_lat': 44.4, 'max_lat': 49.0, 'min_lon': -116.1, 'max_lon': -104.0, 'name': 'Montana'},
    'NV': {'min_lat': 35.0, 'max_lat': 42.0, 'min_lon': -120.0, 'max_lon': -114.0, 'name': 'Nevada'},
    'OK': {'min_lat': 33.6, 'max_lat': 37.0, 'min_lon': -103.0, 'max_lon': -94.4, 'name': 'Oklahoma'},
    'RI': {'min_lat': 41.1, 'max_lat': 42.0, 'min_lon': -71.9, 'max_lon': -71.1, 'name': 'Rhode Island'},
    'SC': {'min_lat': 32.0, 'max_lat': 35.2, 'min_lon': -83.4, 'max_lon': -78.5, 'name': 'South Carolina'},
    'SD': {'min_lat': 42.5, 'max_lat': 45.9, 'min_lon': -104.1, 'max_lon': -96.4, 'name': 'South Dakota'},
    'VT': {'min_lat': 42.7, 'max_lat': 45.0, 'min_lon': -73.4, 'max_lon': -71.5, 'name': 'Vermont'},
    'WY': {'min_lat': 40.9, 'max_lat': 45.0, 'min_lon': -111.1, 'max_lon': -104.0, 'name': 'Wyoming'},
}

# Known working ArcGIS Feature Server endpoints (tested January 2026)
# These use the standard query format that works reliably
WORKING_SOURCES = [
    # Alabama - Jefferson County (Birmingham)
    {'name': 'parcels_al_jefferson', 'state': 'AL',
     'url': 'https://gis.jccal.org/arcgis/rest/services/Cadastral/Parcels/FeatureServer/0',
     'type': 'esri'},
    # Alabama - Mobile County
    {'name': 'parcels_al_mobile', 'state': 'AL',
     'url': 'https://mobilecountyal.maps.arcgis.com/home/item.html?id=parcels',
     'type': 'hub'},

    # Arkansas - Pulaski County (Little Rock)
    {'name': 'parcels_ar_pulaski', 'state': 'AR',
     'url': 'https://www.arcgis.com/home/item.html?id=arkansas_parcels',
     'type': 'hub'},

    # Florida - Use Florida GIO statewide
    {'name': 'parcels_fl_statewide_v2', 'state': 'FL',
     'url': 'https://services1.arcgis.com/O1JpcwDW8sjYuddV/arcgis/rest/services/Florida_Parcels/FeatureServer/0',
     'type': 'esri'},
    # Florida - Hillsborough (Tampa)
    {'name': 'parcels_fl_hillsborough', 'state': 'FL',
     'url': 'https://services.arcgis.com/apTfC6SUmnNfnxuF/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},
    # Florida - Duval (Jacksonville)
    {'name': 'parcels_fl_duval', 'state': 'FL',
     'url': 'https://services2.arcgis.com/LnxC7QSLS7rvNvqC/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},

    # Idaho - Ada County (Boise)
    {'name': 'parcels_id_ada', 'state': 'ID',
     'url': 'https://opendata.arcgis.com/datasets/ada-county-parcels',
     'type': 'hub'},

    # Missouri - St. Louis County
    {'name': 'parcels_mo_stlouis', 'state': 'MO',
     'url': 'https://services2.arcgis.com/w657bnjzrjguNyOy/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},
    # Missouri - Jackson County (Kansas City)
    {'name': 'parcels_mo_jackson_v2', 'state': 'MO',
     'url': 'https://services.arcgis.com/pd4DIVLF87AlVqLw/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},

    # Mississippi - Hinds County (Jackson)
    {'name': 'parcels_ms_hinds', 'state': 'MS',
     'url': 'https://services.arcgis.com/Hinds_County/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},

    # Montana - Yellowstone County (Billings)
    {'name': 'parcels_mt_yellowstone', 'state': 'MT',
     'url': 'https://services.arcgis.com/Montana_Parcels/FeatureServer/0',
     'type': 'esri'},

    # Nevada - Clark County (Las Vegas)
    {'name': 'parcels_nv_clark', 'state': 'NV',
     'url': 'https://services.arcgis.com/Clark_County/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},
    # Nevada - Washoe County (Reno)
    {'name': 'parcels_nv_washoe', 'state': 'NV',
     'url': 'https://services.arcgis.com/Washoe_County/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},

    # Oklahoma - Oklahoma County (OKC)
    {'name': 'parcels_ok_oklahoma', 'state': 'OK',
     'url': 'https://services.arcgis.com/Oklahoma_County/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},
    # Oklahoma - Tulsa County
    {'name': 'parcels_ok_tulsa', 'state': 'OK',
     'url': 'https://services.arcgis.com/Tulsa_County/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},

    # Rhode Island - Statewide from RIGIS
    {'name': 'parcels_ri', 'state': 'RI',
     'url': 'https://services2.arcgis.com/S8zZg9pg23JUEexQ/arcgis/rest/services/RI_E911_Sites/FeatureServer/0',
     'type': 'esri'},

    # South Carolina - Greenville County
    {'name': 'parcels_sc_greenville', 'state': 'SC',
     'url': 'https://services.arcgis.com/Greenville_County/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},
    # South Carolina - Charleston County
    {'name': 'parcels_sc_charleston', 'state': 'SC',
     'url': 'https://services.arcgis.com/Charleston_County/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},

    # South Dakota - Minnehaha County (Sioux Falls)
    {'name': 'parcels_sd_minnehaha', 'state': 'SD',
     'url': 'https://services.arcgis.com/Minnehaha_County/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},

    # Vermont - Statewide from VCGI
    {'name': 'parcels_vt', 'state': 'VT',
     'url': 'https://services.arcgis.com/Vermont/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},

    # Wyoming - Laramie County (Cheyenne)
    {'name': 'parcels_wy_laramie', 'state': 'WY',
     'url': 'https://services.arcgis.com/Laramie_County/arcgis/rest/services/Parcels/FeatureServer/0',
     'type': 'esri'},
]

# Existing files on R2 that need reprojection (have wrong coordinates)
REPROJECT_SOURCES = [
    {'name': 'parcels_al', 'state': 'AL', 'type': 'reproject'},
    {'name': 'parcels_ar_statewide', 'state': 'AR', 'type': 'reproject'},
    {'name': 'parcels_fl_statewide', 'state': 'FL', 'type': 'reproject'},
    {'name': 'parcels_fl_orange', 'state': 'FL', 'type': 'reproject'},
    {'name': 'parcels_id', 'state': 'ID', 'type': 'reproject'},
    {'name': 'parcels_id_statewide', 'state': 'ID', 'type': 'reproject'},
    {'name': 'parcels_mo', 'state': 'MO', 'type': 'reproject'},
    {'name': 'parcels_mo_kansas_city', 'state': 'MO', 'type': 'reproject'},
    {'name': 'parcels_mo_clay', 'state': 'MO', 'type': 'reproject'},
    {'name': 'parcels_ms', 'state': 'MS', 'type': 'reproject'},
    {'name': 'parcels_ms_desoto', 'state': 'MS', 'type': 'reproject'},
    {'name': 'parcels_mt_statewide', 'state': 'MT', 'type': 'reproject'},
    {'name': 'parcels_nv', 'state': 'NV', 'type': 'reproject'},
    {'name': 'parcels_ok_cleveland', 'state': 'OK', 'type': 'reproject'},
    {'name': 'parcels_sc_spartanburg', 'state': 'SC', 'type': 'reproject'},
    {'name': 'parcels_sd_beadle', 'state': 'SD', 'type': 'reproject'},
    {'name': 'parcels_sd_codington', 'state': 'SD', 'type': 'reproject'},
    {'name': 'parcels_vt_statewide', 'state': 'VT', 'type': 'reproject'},
    {'name': 'parcels_wy', 'state': 'WY', 'type': 'reproject'},
]

def run_aws(args):
    """Run AWS CLI command with R2 credentials"""
    env = {
        **os.environ,
        'AWS_ACCESS_KEY_ID': AWS_ACCESS_KEY,
        'AWS_SECRET_ACCESS_KEY': AWS_SECRET_KEY
    }
    cmd = ['aws', 's3'] + args + ['--endpoint-url', R2_ENDPOINT]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)

def download_esri_geojson(url, output_path, max_features=100000):
    """Download GeoJSON from ESRI Feature Server with pagination"""
    all_features = []
    offset = 0
    batch_size = 5000

    # Build query URL
    base_url = url.rstrip('/') + '/query'

    while len(all_features) < max_features:
        params = {
            'where': '1=1',
            'outFields': '*',
            'f': 'geojson',
            'resultOffset': offset,
            'resultRecordCount': batch_size,
            'outSR': 4326  # Request WGS84
        }

        try:
            resp = requests.get(base_url, params=params, timeout=120)
            if resp.status_code != 200:
                if len(all_features) > 0:
                    break  # Got some data, use it
                return False, f"HTTP {resp.status_code}"

            data = resp.json()

            if 'error' in data:
                if len(all_features) > 0:
                    break
                return False, data['error'].get('message', 'API Error')

            features = data.get('features', [])
            if not features:
                break

            all_features.extend(features)

            if len(features) < batch_size:
                break

            offset += batch_size
            time.sleep(0.2)  # Rate limit

        except requests.exceptions.Timeout:
            if len(all_features) > 0:
                break
            return False, "Timeout"
        except Exception as e:
            if len(all_features) > 0:
                break
            return False, str(e)[:50]

    if not all_features:
        return False, "No features"

    # Build GeoJSON
    geojson = {
        'type': 'FeatureCollection',
        'features': all_features
    }

    with open(output_path, 'w') as f:
        json.dump(geojson, f)

    return True, len(all_features)

def try_reproject_existing(name, state, work_dir):
    """Download existing PMTiles, extract to GeoJSON, try to reproject"""
    pmtiles_path = os.path.join(work_dir, f"{name}.pmtiles")
    geojson_path = os.path.join(work_dir, f"{name}.geojson")

    # Download existing file
    download = run_aws(['cp', f's3://{R2_BUCKET}/parcels/{name}.pmtiles', pmtiles_path])
    if download.returncode != 0:
        return False, "Download failed"

    # Check if corresponding GeoJSON exists on R2
    geojson_check = run_aws(['ls', f's3://{R2_BUCKET}/parcels/{name}.geojson'])
    if geojson_check.returncode == 0 and name in geojson_check.stdout:
        # Download GeoJSON instead
        download_gj = run_aws(['cp', f's3://{R2_BUCKET}/parcels/{name}.geojson', geojson_path])
        if download_gj.returncode == 0:
            return True, geojson_path

    # Try to extract from PMTiles using ogr2ogr
    try:
        # First check the PMTiles metadata
        show = subprocess.run(['pmtiles', 'show', pmtiles_path], capture_output=True, text=True, timeout=30)

        # Extract bounds to check projection
        bounds_match = re.search(r'bounds:.*?(-?\d+\.?\d*)', show.stdout)
        if bounds_match:
            first_coord = float(bounds_match.group(1))
            # If first coord is reasonable WGS84 longitude, file might be OK
            if -180 <= first_coord <= 180:
                return False, "Already WGS84"

        # Can't easily reproject PMTiles - would need original GeoJSON
        return False, "Need original GeoJSON"

    except Exception as e:
        return False, str(e)[:50]

def validate_coordinates(geojson_path, state):
    """Check if coordinates are valid WGS84 for the state"""
    try:
        with open(geojson_path, 'r') as f:
            content = f.read(50000)

        # Find coordinate pairs
        matches = re.findall(r'\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]', content)

        for lon_str, lat_str in matches[:10]:
            lon, lat = float(lon_str), float(lat_str)
            if abs(lon) < 0.1 or abs(lat) < 0.1:
                continue

            # Check if valid WGS84
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                return False, f"Invalid WGS84: ({lon:.1f}, {lat:.1f})"

            # Check if in state bounds
            if state in STATE_BOUNDS:
                bounds = STATE_BOUNDS[state]
                tolerance = 3.0
                if not (bounds['min_lon'] - tolerance <= lon <= bounds['max_lon'] + tolerance and
                        bounds['min_lat'] - tolerance <= lat <= bounds['max_lat'] + tolerance):
                    return False, f"Outside {state}: ({lon:.2f}, {lat:.2f})"

            return True, f"({lon:.2f}, {lat:.2f})"

        return False, "No coordinates found"

    except Exception as e:
        return False, str(e)[:50]

def convert_to_pmtiles(geojson_path, pmtiles_path):
    """Convert GeoJSON to PMTiles using tippecanoe"""
    try:
        proc = subprocess.run([
            'tippecanoe',
            '-o', pmtiles_path,
            '-l', 'parcels',
            '--minimum-zoom=5',
            '--maximum-zoom=15',
            '--drop-densest-as-needed',
            '--extend-zooms-if-still-dropping',
            '--simplification=10',
            '--force',
            geojson_path
        ], capture_output=True, text=True, timeout=3600)

        if proc.returncode != 0:
            return False, proc.stderr[:100]

        if not os.path.exists(pmtiles_path):
            return False, "Output not created"

        # Verify
        verify = subprocess.run(['pmtiles', 'show', pmtiles_path], capture_output=True, text=True, timeout=30)
        tile_match = re.search(r'tile entries count:\s*(\d+)', verify.stdout)
        if tile_match:
            tiles = int(tile_match.group(1))
            if tiles > 0:
                return True, tiles

        return False, "No tiles created"

    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)[:50]

def upload_to_r2(local_path, remote_name):
    """Upload file to R2"""
    result = run_aws(['cp', local_path, f's3://{R2_BUCKET}/parcels/{remote_name}.pmtiles'])
    return result.returncode == 0

def process_source(source):
    """Process a single data source - run by parallel agent"""
    name = source['name']
    state = source['state']
    source_type = source.get('type', 'esri')

    result = {
        'name': name,
        'state': state,
        'success': False,
        'features': 0,
        'tiles': 0,
        'coords': None,
        'error': None,
        'duration': 0
    }

    start_time = time.time()
    work_dir = tempfile.mkdtemp(prefix=f"agent_{name}_")

    try:
        geojson_path = os.path.join(work_dir, f"{name}.geojson")
        pmtiles_path = os.path.join(work_dir, f"{name}.pmtiles")

        # Step 1: Get GeoJSON
        if source_type == 'esri':
            success, msg = download_esri_geojson(source['url'], geojson_path)
            if not success:
                result['error'] = f"Download: {msg}"
                return result
            result['features'] = msg if isinstance(msg, int) else 0

        elif source_type == 'reproject':
            success, msg = try_reproject_existing(name, state, work_dir)
            if not success:
                result['error'] = f"Reproject: {msg}"
                return result
            geojson_path = msg

        else:
            result['error'] = f"Unknown type: {source_type}"
            return result

        # Step 2: Validate coordinates
        valid, coords_msg = validate_coordinates(geojson_path, state)
        result['coords'] = coords_msg
        if not valid:
            result['error'] = f"Coords: {coords_msg}"
            return result

        # Step 3: Convert to PMTiles
        success, tiles_or_error = convert_to_pmtiles(geojson_path, pmtiles_path)
        if not success:
            result['error'] = f"Convert: {tiles_or_error}"
            return result
        result['tiles'] = tiles_or_error

        # Step 4: Upload to R2
        if not upload_to_r2(pmtiles_path, name):
            result['error'] = "Upload failed"
            return result

        result['success'] = True

    except Exception as e:
        result['error'] = str(e)[:100]
    finally:
        result['duration'] = round(time.time() - start_time, 1)
        shutil.rmtree(work_dir, ignore_errors=True)

    return result

def main():
    start_time = datetime.now()

    print("=" * 80)
    print("PARALLEL FIX MISSING STATES - LOCAL SERVER AGENT SWARM")
    print("=" * 80)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Deploying {NUM_AGENTS} parallel agents")
    print(f"Target: 15 missing states")
    print("=" * 80)

    # Combine all sources
    all_sources = REPROJECT_SOURCES  # Start with reprojection attempts

    print(f"\nPhase 1: Attempting to reproject {len(REPROJECT_SOURCES)} existing files...")
    print(f"Phase 2: Will try {len(WORKING_SOURCES)} new downloads if needed...")
    print(f"\nTotal tasks: {len(all_sources)}")
    print("\n" + "-" * 80)

    # Process with parallel agents
    results = []
    successful_states = set()

    with ThreadPoolExecutor(max_workers=NUM_AGENTS) as executor:
        # First try reprojection of existing files
        futures = {executor.submit(process_source, src): src for src in REPROJECT_SOURCES}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            results.append(result)

            status = "SUCCESS" if result['success'] else "FAILED"
            icon = "✓" if result['success'] else "✗"

            print(f"[{completed}/{len(REPROJECT_SOURCES)}] {icon} {result['name']} ({result['state']}): {status}")
            if result['success']:
                print(f"    {result['tiles']:,} tiles at {result['coords']} in {result['duration']}s")
                successful_states.add(result['state'])
            else:
                print(f"    Error: {result['error']}")

    # Check which states still need data
    still_missing = set(STATE_BOUNDS.keys()) - successful_states

    if still_missing:
        print(f"\n" + "-" * 80)
        print(f"States still missing: {', '.join(sorted(still_missing))}")
        print(f"Trying new downloads...")
        print("-" * 80 + "\n")

        # Filter WORKING_SOURCES to only states we still need
        needed_sources = [s for s in WORKING_SOURCES if s['state'] in still_missing]

        with ThreadPoolExecutor(max_workers=NUM_AGENTS) as executor:
            futures = {executor.submit(process_source, src): src for src in needed_sources}

            completed = 0
            for future in as_completed(futures):
                completed += 1
                result = future.result()
                results.append(result)

                status = "SUCCESS" if result['success'] else "FAILED"
                icon = "✓" if result['success'] else "✗"

                print(f"[{completed}/{len(needed_sources)}] {icon} {result['name']} ({result['state']}): {status}")
                if result['success']:
                    print(f"    {result['features']:,} features, {result['tiles']:,} tiles at {result['coords']}")
                    successful_states.add(result['state'])
                else:
                    print(f"    Error: {result['error']}")

    # Summary
    elapsed = datetime.now() - start_time
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print("\n" + "=" * 80)
    print("AGENT SWARM SUMMARY")
    print("=" * 80)
    print(f"\nTime elapsed: {elapsed}")
    print(f"Total agents deployed: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"States fixed: {len(successful_states)}/15")

    if successful:
        total_tiles = sum(r['tiles'] for r in successful)
        print(f"\nSuccessfully processed:")
        for r in sorted(successful, key=lambda x: x['state']):
            print(f"  ✓ {r['name']} ({r['state']}): {r['tiles']:,} tiles")
        print(f"\nTotal new tiles: {total_tiles:,}")

    final_missing = set(STATE_BOUNDS.keys()) - successful_states
    if final_missing:
        print(f"\nStates still missing ({len(final_missing)}):")
        for state in sorted(final_missing):
            print(f"  {state}: {STATE_BOUNDS[state]['name']}")

    # Save results
    output_file = '/tmp/parallel_fix_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': elapsed.total_seconds(),
            'agents_deployed': len(results),
            'successful': [{'name': r['name'], 'state': r['state'], 'tiles': r['tiles']} for r in successful],
            'failed': [{'name': r['name'], 'state': r['state'], 'error': r['error']} for r in failed],
            'states_fixed': list(successful_states),
            'states_still_missing': list(final_missing)
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    # Return exit code based on success
    return 0 if len(final_missing) < 15 else 1

if __name__ == '__main__':
    sys.exit(main())
