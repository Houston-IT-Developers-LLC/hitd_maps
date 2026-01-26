#!/usr/bin/env python3
"""
FIX WITH PROJ STRINGS - Use exact projection definitions
For State Plane coordinates in US Survey Feet
"""

import subprocess
import os
import json
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import multiprocessing
import re
import sys

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

NUM_AGENTS = min(30, multiprocessing.cpu_count() * 2)

# State bounds for validation
STATE_BOUNDS = {
    'AL': {'min_lat': 30.1, 'max_lat': 35.0, 'min_lon': -88.5, 'max_lon': -84.9},
    'AR': {'min_lat': 33.0, 'max_lat': 36.5, 'min_lon': -94.6, 'max_lon': -89.6},
    'FL': {'min_lat': 24.5, 'max_lat': 31.0, 'min_lon': -87.6, 'max_lon': -80.0},
    'ID': {'min_lat': 42.0, 'max_lat': 49.0, 'min_lon': -117.2, 'max_lon': -111.0},
    'MO': {'min_lat': 35.9, 'max_lat': 40.6, 'min_lon': -95.8, 'max_lon': -89.1},
    'MS': {'min_lat': 30.2, 'max_lat': 35.0, 'min_lon': -91.7, 'max_lon': -88.1},
    'MT': {'min_lat': 44.4, 'max_lat': 49.0, 'min_lon': -116.1, 'max_lon': -104.0},
    'NV': {'min_lat': 35.0, 'max_lat': 42.0, 'min_lon': -120.0, 'max_lon': -114.0},
    'OK': {'min_lat': 33.6, 'max_lat': 37.0, 'min_lon': -103.0, 'max_lon': -94.4},
    'SC': {'min_lat': 32.0, 'max_lat': 35.2, 'min_lon': -83.4, 'max_lon': -78.5},
    'SD': {'min_lat': 42.5, 'max_lat': 45.9, 'min_lon': -104.1, 'max_lon': -96.4},
    'VT': {'min_lat': 42.7, 'max_lat': 45.0, 'min_lon': -73.4, 'max_lon': -71.5},
    'WY': {'min_lat': 40.9, 'max_lat': 45.0, 'min_lon': -111.1, 'max_lon': -104.0},
    'GA': {'min_lat': 30.4, 'max_lat': 35.0, 'min_lon': -85.6, 'max_lon': -80.8},
    'MI': {'min_lat': 41.7, 'max_lat': 48.2, 'min_lon': -90.4, 'max_lon': -82.4},
    'MN': {'min_lat': 43.5, 'max_lat': 49.4, 'min_lon': -97.2, 'max_lon': -89.5},
    'OH': {'min_lat': 38.4, 'max_lat': 42.0, 'min_lon': -84.8, 'max_lon': -80.5},
    'WI': {'min_lat': 42.5, 'max_lat': 47.1, 'min_lon': -92.9, 'max_lon': -86.8},
    'CA': {'min_lat': 32.5, 'max_lat': 42.0, 'min_lon': -124.5, 'max_lon': -114.1},
}

# PROJ strings for State Plane coordinate systems (US Survey Feet)
STATE_PROJ_STRINGS = {
    # Missouri - West zone (Kansas City area)
    'MO_WEST': '+proj=tmerc +lat_0=36.16666666666666 +lon_0=-94.5 +k=0.9999411764705882 +x_0=850000 +y_0=0 +datum=NAD83 +units=us-ft +no_defs',
    # Missouri - Central zone
    'MO_CENTRAL': '+proj=tmerc +lat_0=35.83333333333334 +lon_0=-92.5 +k=0.9999333333333333 +x_0=500000 +y_0=0 +datum=NAD83 +units=us-ft +no_defs',
    # Missouri - East zone
    'MO_EAST': '+proj=tmerc +lat_0=35.83333333333334 +lon_0=-90.5 +k=0.9999333333333333 +x_0=250000 +y_0=0 +datum=NAD83 +units=us-ft +no_defs',

    # Georgia - West zone
    'GA_WEST': '+proj=tmerc +lat_0=30 +lon_0=-84.16666666666667 +k=0.9999 +x_0=700000 +y_0=0 +datum=NAD83 +units=us-ft +no_defs',
    # Georgia - East zone
    'GA_EAST': '+proj=tmerc +lat_0=30 +lon_0=-82.16666666666667 +k=0.9999 +x_0=200000 +y_0=0 +datum=NAD83 +units=us-ft +no_defs',

    # Michigan - South zone
    'MI_SOUTH': '+proj=lcc +lat_1=42.1 +lat_2=43.66666666666666 +lat_0=41.5 +lon_0=-84.36666666666666 +x_0=4000000 +y_0=0 +datum=NAD83 +units=us-ft +no_defs',
    # Michigan - Central
    'MI_CENTRAL': '+proj=lcc +lat_1=44.18333333333333 +lat_2=45.7 +lat_0=43.31666666666667 +lon_0=-84.36666666666666 +x_0=6000000 +y_0=0 +datum=NAD83 +units=us-ft +no_defs',

    # Minnesota - South
    'MN_SOUTH': '+proj=lcc +lat_1=43.78333333333333 +lat_2=45.21666666666667 +lat_0=43 +lon_0=-94 +x_0=800000 +y_0=100000 +datum=NAD83 +units=us-ft +no_defs',
    # Minnesota - Central
    'MN_CENTRAL': '+proj=lcc +lat_1=45.61666666666667 +lat_2=47.05 +lat_0=45 +lon_0=-94.25 +x_0=800000 +y_0=100000 +datum=NAD83 +units=us-ft +no_defs',

    # Wisconsin - South
    'WI_SOUTH': '+proj=lcc +lat_1=42.73333333333333 +lat_2=44.06666666666667 +lat_0=42 +lon_0=-90 +x_0=600000 +y_0=0 +datum=NAD83 +units=us-ft +no_defs',

    # Ohio - South
    'OH_SOUTH': '+proj=lcc +lat_1=38.73333333333333 +lat_2=40.03333333333333 +lat_0=38 +lon_0=-82.5 +x_0=600000 +y_0=0 +datum=NAD83 +units=us-ft +no_defs',
    # Ohio - North
    'OH_NORTH': '+proj=lcc +lat_1=40.43333333333333 +lat_2=41.7 +lat_0=39.66666666666666 +lon_0=-82.5 +x_0=600000 +y_0=0 +datum=NAD83 +units=us-ft +no_defs',

    # California zones
    'CA_ZONE3': '+proj=lcc +lat_1=37.06666666666667 +lat_2=38.43333333333333 +lat_0=36.5 +lon_0=-120.5 +x_0=2000000 +y_0=500000 +datum=NAD83 +units=us-ft +no_defs',
    'CA_ZONE5': '+proj=lcc +lat_1=34.03333333333333 +lat_2=35.46666666666667 +lat_0=33.5 +lon_0=-118 +x_0=2000000 +y_0=500000 +datum=NAD83 +units=us-ft +no_defs',

    # Also include standard EPSG codes
    'EPSG_3857': 'EPSG:3857',
    'EPSG_4326': 'EPSG:4326',
}

# Files to process with their likely projection zones
FILES_TO_FIX = [
    # Missouri files (West zone based on coordinates)
    {'name': 'parcels_mo_kansas_city', 'state': 'MO', 'proj_keys': ['MO_WEST', 'MO_CENTRAL', 'MO_EAST']},
    {'name': 'parcels_mo_clay', 'state': 'MO', 'proj_keys': ['MO_WEST', 'MO_CENTRAL']},
    {'name': 'parcels_mo_jackson', 'state': 'MO', 'proj_keys': ['MO_WEST', 'MO_CENTRAL']},
    {'name': 'parcels_mo_christian', 'state': 'MO', 'proj_keys': ['MO_WEST', 'MO_CENTRAL']},
    {'name': 'parcels_mo_st_charles', 'state': 'MO', 'proj_keys': ['MO_EAST', 'MO_CENTRAL']},
    {'name': 'parcels_mo_st_charles_v2', 'state': 'MO', 'proj_keys': ['MO_EAST', 'MO_CENTRAL']},

    # Minnesota files
    {'name': 'parcels_mn_anoka', 'state': 'MN', 'proj_keys': ['MN_CENTRAL', 'MN_SOUTH']},
    {'name': 'parcels_mn_dakota', 'state': 'MN', 'proj_keys': ['MN_SOUTH', 'MN_CENTRAL']},
    {'name': 'parcels_mn_hennepin', 'state': 'MN', 'proj_keys': ['MN_SOUTH', 'MN_CENTRAL']},
    {'name': 'parcels_mn_ramsey', 'state': 'MN', 'proj_keys': ['MN_SOUTH', 'MN_CENTRAL']},

    # Georgia files
    {'name': 'parcels_ga_chatham', 'state': 'GA', 'proj_keys': ['GA_EAST', 'GA_WEST']},
    {'name': 'parcels_ga_cobb', 'state': 'GA', 'proj_keys': ['GA_WEST', 'GA_EAST']},
    {'name': 'parcels_ga_gwinnett', 'state': 'GA', 'proj_keys': ['GA_WEST', 'GA_EAST']},
    {'name': 'parcels_ga_gwinnett_v2', 'state': 'GA', 'proj_keys': ['GA_WEST', 'GA_EAST']},
    {'name': 'parcels_ga_richmond', 'state': 'GA', 'proj_keys': ['GA_EAST', 'GA_WEST']},

    # Michigan files
    {'name': 'parcels_mi_kent', 'state': 'MI', 'proj_keys': ['MI_SOUTH', 'MI_CENTRAL']},
    {'name': 'parcels_mi_kent_v2', 'state': 'MI', 'proj_keys': ['MI_SOUTH', 'MI_CENTRAL']},
    {'name': 'parcels_mi_macomb', 'state': 'MI', 'proj_keys': ['MI_SOUTH', 'MI_CENTRAL']},
    {'name': 'parcels_mi_oakland', 'state': 'MI', 'proj_keys': ['MI_SOUTH', 'MI_CENTRAL']},
    {'name': 'parcels_mi_oakland_v2', 'state': 'MI', 'proj_keys': ['MI_SOUTH', 'MI_CENTRAL']},
    {'name': 'parcels_mi_ottawa', 'state': 'MI', 'proj_keys': ['MI_SOUTH', 'MI_CENTRAL']},
    {'name': 'parcels_mi_wayne', 'state': 'MI', 'proj_keys': ['MI_SOUTH', 'MI_CENTRAL']},

    # Ohio files
    {'name': 'parcels_oh_cuyahoga', 'state': 'OH', 'proj_keys': ['OH_NORTH', 'OH_SOUTH']},
    {'name': 'parcels_oh_hamilton', 'state': 'OH', 'proj_keys': ['OH_SOUTH', 'OH_NORTH']},
    {'name': 'parcels_oh_statewide', 'state': 'OH', 'proj_keys': ['OH_NORTH', 'OH_SOUTH']},
    {'name': 'parcels_oh_montgomery', 'state': 'OH', 'proj_keys': ['OH_SOUTH', 'OH_NORTH']},
    {'name': 'parcels_oh_summit', 'state': 'OH', 'proj_keys': ['OH_NORTH', 'OH_SOUTH']},
    {'name': 'parcels_oh_summit_v2', 'state': 'OH', 'proj_keys': ['OH_NORTH', 'OH_SOUTH']},

    # New York
    {'name': 'parcels_ny_statewide', 'state': 'NY', 'proj_keys': ['EPSG_3857', 'EPSG_4326']},
    {'name': 'parcels_ny_statewide_v2', 'state': 'NY', 'proj_keys': ['EPSG_3857', 'EPSG_4326']},
]

def run_aws(args):
    env = {**os.environ, 'AWS_ACCESS_KEY_ID': AWS_ACCESS_KEY, 'AWS_SECRET_ACCESS_KEY': AWS_SECRET_KEY}
    return subprocess.run(['aws', 's3'] + args + ['--endpoint-url', R2_ENDPOINT], capture_output=True, text=True, env=env)

def check_coords(geojson_path, state):
    """Check if coordinates are valid for state"""
    try:
        with open(geojson_path, 'r') as f:
            data = json.load(f)

        if not data.get('features'):
            return False, None, None

        feat = data['features'][0]
        geom = feat['geometry']

        if geom['type'] == 'Polygon':
            coords = geom['coordinates'][0][0]
        elif geom['type'] == 'MultiPolygon':
            coords = geom['coordinates'][0][0][0]
        else:
            return False, None, None

        lon, lat = coords[0], coords[1]

        # Check if valid WGS84
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            return False, lon, lat

        # Check if in state bounds
        if state in STATE_BOUNDS:
            b = STATE_BOUNDS[state]
            tolerance = 3.0
            if not (b['min_lon'] - tolerance <= lon <= b['max_lon'] + tolerance and
                    b['min_lat'] - tolerance <= lat <= b['max_lat'] + tolerance):
                return False, lon, lat

        return True, lon, lat
    except Exception as e:
        return False, None, None

def try_reproject(input_path, output_path, proj_string):
    """Try reprojection with a PROJ string"""
    try:
        if proj_string.startswith('EPSG:'):
            cmd = ['ogr2ogr', '-f', 'GeoJSON', '-s_srs', proj_string, '-t_srs', 'EPSG:4326', output_path, input_path]
        else:
            cmd = ['ogr2ogr', '-f', 'GeoJSON', '-s_srs', proj_string, '-t_srs', 'EPSG:4326', output_path, input_path]

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return proc.returncode == 0 and os.path.exists(output_path)
    except:
        return False

def convert_pmtiles(geojson_path, pmtiles_path):
    """Convert to PMTiles"""
    try:
        proc = subprocess.run([
            'tippecanoe', '-o', pmtiles_path, '-l', 'parcels',
            '--minimum-zoom=5', '--maximum-zoom=15',
            '--drop-densest-as-needed', '--extend-zooms-if-still-dropping',
            '--simplification=10', '--force', geojson_path
        ], capture_output=True, text=True, timeout=3600)

        if proc.returncode != 0:
            return False, 0

        verify = subprocess.run(['pmtiles', 'show', pmtiles_path], capture_output=True, text=True, timeout=30)
        match = re.search(r'tile entries count:\s*(\d+)', verify.stdout)
        if match:
            return True, int(match.group(1))
        return False, 0
    except:
        return False, 0

def process_file(file_info):
    """Process a single file"""
    name = file_info['name']
    state = file_info['state']
    proj_keys = file_info['proj_keys']

    result = {'name': name, 'state': state, 'success': False, 'proj': None, 'coords': None, 'tiles': 0, 'error': None}

    work_dir = tempfile.mkdtemp(prefix=f"fix_{name}_")

    try:
        geojson_path = os.path.join(work_dir, f"{name}.geojson")

        # Download GeoJSON
        dl = run_aws(['cp', f's3://{R2_BUCKET}/parcels/{name}.geojson', geojson_path])
        if dl.returncode != 0 or not os.path.exists(geojson_path):
            result['error'] = "No GeoJSON on R2"
            return result

        # Check if already valid
        valid, lon, lat = check_coords(geojson_path, state)
        if valid:
            result['coords'] = f"({lon:.2f}, {lat:.2f})"
            final_geojson = geojson_path
            result['proj'] = 'already_valid'
        else:
            # Try each projection
            reprojected_path = os.path.join(work_dir, f"{name}_wgs84.geojson")
            found = False

            for proj_key in proj_keys:
                proj_string = STATE_PROJ_STRINGS.get(proj_key)
                if not proj_string:
                    continue

                if os.path.exists(reprojected_path):
                    os.remove(reprojected_path)

                if try_reproject(geojson_path, reprojected_path, proj_string):
                    valid, lon, lat = check_coords(reprojected_path, state)
                    if valid:
                        result['proj'] = proj_key
                        result['coords'] = f"({lon:.2f}, {lat:.2f})"
                        final_geojson = reprojected_path
                        found = True
                        break

            if not found:
                result['error'] = f"No projection worked"
                return result

        # Convert to PMTiles
        pmtiles_path = os.path.join(work_dir, f"{name}.pmtiles")
        success, tiles = convert_pmtiles(final_geojson, pmtiles_path)
        if not success or tiles == 0:
            result['error'] = "PMTiles failed"
            return result

        result['tiles'] = tiles

        # Upload
        ul = run_aws(['cp', pmtiles_path, f's3://{R2_BUCKET}/parcels/{name}.pmtiles'])
        if ul.returncode != 0:
            result['error'] = "Upload failed"
            return result

        result['success'] = True

    except Exception as e:
        result['error'] = str(e)[:100]
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return result

def main():
    start = datetime.now()
    print("=" * 80)
    print("FIX WITH PROJ STRINGS")
    print("=" * 80)
    print(f"Started: {start}")
    print(f"Files to fix: {len(FILES_TO_FIX)}")
    print(f"Agents: {NUM_AGENTS}")
    print("=" * 80 + "\n")

    results = []
    with ThreadPoolExecutor(max_workers=NUM_AGENTS) as executor:
        futures = {executor.submit(process_file, f): f for f in FILES_TO_FIX}

        for i, future in enumerate(as_completed(futures), 1):
            r = future.result()
            results.append(r)

            icon = "✓" if r['success'] else "✗"
            print(f"[{i}/{len(FILES_TO_FIX)}] {icon} {r['name']} ({r['state']})")
            if r['success']:
                print(f"    {r['proj']} -> {r['coords']} ({r['tiles']:,} tiles)")
            else:
                print(f"    Error: {r['error']}")

    # Summary
    elapsed = datetime.now() - start
    successful = [r for r in results if r['success']]

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Time: {elapsed}")
    print(f"Successful: {len(successful)}/{len(results)}")
    print(f"Total tiles: {sum(r['tiles'] for r in successful):,}")

    if successful:
        by_state = {}
        for r in successful:
            if r['state'] not in by_state:
                by_state[r['state']] = []
            by_state[r['state']].append(r)

        print(f"\nFixed states ({len(by_state)}):")
        for state in sorted(by_state.keys()):
            files = by_state[state]
            print(f"  {state}: {len(files)} files, {sum(f['tiles'] for f in files):,} tiles")

    return 0 if successful else 1

if __name__ == '__main__':
    sys.exit(main())
