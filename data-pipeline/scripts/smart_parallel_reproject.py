#!/usr/bin/env python3
"""
SMART PARALLEL REPROJECT - Auto-detect CRS and reproject to WGS84
Downloads GeoJSON from R2, tries multiple EPSG codes, validates output, rebuilds PMTiles

Run: python3 smart_parallel_reproject.py
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
CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

NUM_AGENTS = min(30, multiprocessing.cpu_count() * 2)

# State bounds for validation
STATE_BOUNDS = {
    'AL': {'min_lat': 30.1, 'max_lat': 35.0, 'min_lon': -88.5, 'max_lon': -84.9, 'name': 'Alabama'},
    'AR': {'min_lat': 33.0, 'max_lat': 36.5, 'min_lon': -94.6, 'max_lon': -89.6, 'name': 'Arkansas'},
    'FL': {'min_lat': 24.5, 'max_lat': 31.0, 'min_lon': -87.6, 'max_lon': -80.0, 'name': 'Florida'},
    'ID': {'min_lat': 42.0, 'max_lat': 49.0, 'min_lon': -117.2, 'max_lon': -111.0, 'name': 'Idaho'},
    'MO': {'min_lat': 35.9, 'max_lat': 40.6, 'min_lon': -95.8, 'max_lon': -89.1, 'name': 'Missouri'},
    'MS': {'min_lat': 30.2, 'max_lat': 35.0, 'min_lon': -91.7, 'max_lon': -88.1, 'name': 'Mississippi'},
    'MT': {'min_lat': 44.4, 'max_lat': 49.0, 'min_lon': -116.1, 'max_lon': -104.0, 'name': 'Montana'},
    'NV': {'min_lat': 35.0, 'max_lat': 42.0, 'min_lon': -120.0, 'max_lon': -114.0, 'name': 'Nevada'},
    'OK': {'min_lat': 33.6, 'max_lat': 37.0, 'min_lon': -103.0, 'max_lon': -94.4, 'name': 'Oklahoma'},
    'SC': {'min_lat': 32.0, 'max_lat': 35.2, 'min_lon': -83.4, 'max_lon': -78.5, 'name': 'South Carolina'},
    'SD': {'min_lat': 42.5, 'max_lat': 45.9, 'min_lon': -104.1, 'max_lon': -96.4, 'name': 'South Dakota'},
    'VT': {'min_lat': 42.7, 'max_lat': 45.0, 'min_lon': -73.4, 'max_lon': -71.5, 'name': 'Vermont'},
    'WY': {'min_lat': 40.9, 'max_lat': 45.0, 'min_lon': -111.1, 'max_lon': -104.0, 'name': 'Wyoming'},
    # Also include states we might have bad data for
    'AK': {'min_lat': 51.0, 'max_lat': 71.5, 'min_lon': -180.0, 'max_lon': -130.0, 'name': 'Alaska'},
    'CA': {'min_lat': 32.5, 'max_lat': 42.0, 'min_lon': -124.5, 'max_lon': -114.1, 'name': 'California'},
    'GA': {'min_lat': 30.4, 'max_lat': 35.0, 'min_lon': -85.6, 'max_lon': -80.8, 'name': 'Georgia'},
    'HI': {'min_lat': 18.9, 'max_lat': 22.2, 'min_lon': -160.3, 'max_lon': -154.8, 'name': 'Hawaii'},
    'MI': {'min_lat': 41.7, 'max_lat': 48.2, 'min_lon': -90.4, 'max_lon': -82.4, 'name': 'Michigan'},
    'MN': {'min_lat': 43.5, 'max_lat': 49.4, 'min_lon': -97.2, 'max_lon': -89.5, 'name': 'Minnesota'},
    'OH': {'min_lat': 38.4, 'max_lat': 42.0, 'min_lon': -84.8, 'max_lon': -80.5, 'name': 'Ohio'},
    'WI': {'min_lat': 42.5, 'max_lat': 47.1, 'min_lon': -92.9, 'max_lon': -86.8, 'name': 'Wisconsin'},
}

# Common EPSG codes by state - feet-based State Plane projections
STATE_EPSG_CODES = {
    'AL': [26729, 26730, 102629, 102630, 3465, 3466],  # Alabama State Plane
    'AR': [26751, 26752, 102651, 102652, 3484, 3485],  # Arkansas
    'FL': [2236, 2237, 2238, 3086, 3087, 102258, 102659, 102660],  # Florida
    'ID': [2241, 2242, 2243, 102668, 102669, 102670],  # Idaho
    'MO': [26796, 26797, 26798, 102696, 102697, 102698, 6511, 6512, 6513],  # Missouri
    'MS': [2254, 2255, 102700, 102701, 6507, 6508],  # Mississippi
    'MT': [2256, 102700, 32100],  # Montana
    'NV': [2257, 2258, 2259, 102707, 102708, 102709],  # Nevada
    'OK': [2267, 2268, 102715, 102716],  # Oklahoma
    'SC': [2273, 102733, 32133],  # South Carolina
    'SD': [2274, 2275, 102734, 102735],  # South Dakota
    'VT': [2295, 102745, 32145],  # Vermont
    'WY': [2283, 2284, 2285, 2286, 102744, 102745],  # Wyoming
    'GA': [2239, 2240, 102667, 102668],  # Georgia
    'MI': [2251, 2252, 2253, 102689, 102690, 102691],  # Michigan
    'MN': [2243, 2244, 2245, 102689, 102690, 102691],  # Minnesota
    'OH': [3734, 3735, 102722, 102723],  # Ohio
    'WI': [2287, 2288, 2289, 102741, 102742, 102743],  # Wisconsin
    'CA': [2225, 2226, 2227, 2228, 2229, 2230, 2231, 2232, 3310],  # California
}

# Universal EPSG codes to try
UNIVERSAL_EPSG = [3857, 4326, 32610, 32611, 32612, 32613, 32614, 32615, 32616, 32617, 32618]

def run_aws(args):
    """Run AWS CLI command with R2 credentials"""
    env = {
        **os.environ,
        'AWS_ACCESS_KEY_ID': AWS_ACCESS_KEY,
        'AWS_SECRET_ACCESS_KEY': AWS_SECRET_KEY
    }
    cmd = ['aws', 's3'] + args + ['--endpoint-url', R2_ENDPOINT]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)

def get_state_from_name(name):
    """Extract state code from filename"""
    match = re.match(r'parcels_([a-z]{2})(?:_|$)', name.lower())
    if match:
        return match.group(1).upper()
    return None

def check_coordinates(geojson_path, state):
    """Check first coordinates in GeoJSON and return (is_valid, lon, lat)"""
    try:
        with open(geojson_path, 'r') as f:
            content = f.read(100000)

        matches = re.findall(r'\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]', content)
        for lon_str, lat_str in matches[:20]:
            lon, lat = float(lon_str), float(lat_str)
            if abs(lon) < 1 or abs(lat) < 1:
                continue

            # Check if valid WGS84
            if -180 <= lon <= 180 and -90 <= lat <= 90:
                if state in STATE_BOUNDS:
                    bounds = STATE_BOUNDS[state]
                    tolerance = 3.0
                    if (bounds['min_lon'] - tolerance <= lon <= bounds['max_lon'] + tolerance and
                        bounds['min_lat'] - tolerance <= lat <= bounds['max_lat'] + tolerance):
                        return True, lon, lat
                else:
                    return True, lon, lat

            return False, lon, lat

    except:
        pass
    return False, None, None

def try_reproject(input_path, output_path, source_epsg):
    """Try to reproject with ogr2ogr using specific EPSG"""
    try:
        proc = subprocess.run([
            'ogr2ogr',
            '-f', 'GeoJSON',
            '-s_srs', f'EPSG:{source_epsg}',
            '-t_srs', 'EPSG:4326',
            output_path,
            input_path
        ], capture_output=True, text=True, timeout=300)

        return proc.returncode == 0 and os.path.exists(output_path)
    except:
        return False

def smart_reproject(input_path, output_path, state):
    """Try multiple EPSG codes until coordinates are valid"""
    # Get state-specific EPSG codes
    epsg_codes = STATE_EPSG_CODES.get(state, []) + UNIVERSAL_EPSG

    for epsg in epsg_codes:
        # Clean up previous attempt
        if os.path.exists(output_path):
            os.remove(output_path)

        if try_reproject(input_path, output_path, epsg):
            valid, lon, lat = check_coordinates(output_path, state)
            if valid:
                return True, epsg, lon, lat

    return False, None, None, None

def convert_to_pmtiles(geojson_path, pmtiles_path):
    """Convert GeoJSON to PMTiles"""
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
            return False, 0

        # Get tile count
        verify = subprocess.run(['pmtiles', 'show', pmtiles_path], capture_output=True, text=True, timeout=30)
        match = re.search(r'tile entries count:\s*(\d+)', verify.stdout)
        if match:
            return True, int(match.group(1))

        return False, 0
    except:
        return False, 0

def process_file(file_info):
    """Process a single file - download, reproject, convert, upload"""
    name = file_info['name']
    state = get_state_from_name(name)

    result = {
        'name': name,
        'state': state,
        'success': False,
        'action': None,
        'epsg': None,
        'coords': None,
        'tiles': 0,
        'error': None
    }

    if not state or state not in STATE_BOUNDS:
        result['error'] = f"Unknown state: {state}"
        return result

    work_dir = tempfile.mkdtemp(prefix=f"reproject_{name}_")

    try:
        geojson_path = os.path.join(work_dir, f"{name}.geojson")
        reprojected_path = os.path.join(work_dir, f"{name}_wgs84.geojson")
        pmtiles_path = os.path.join(work_dir, f"{name}.pmtiles")

        # Download GeoJSON from R2
        download = run_aws(['cp', f's3://{R2_BUCKET}/parcels/{name}.geojson', geojson_path])
        if download.returncode != 0 or not os.path.exists(geojson_path):
            result['error'] = "GeoJSON not on R2"
            return result

        # Check if already valid WGS84
        valid, lon, lat = check_coordinates(geojson_path, state)
        if valid:
            result['action'] = 'already_valid'
            result['coords'] = f"({lon:.2f}, {lat:.2f})"
            final_geojson = geojson_path
        else:
            # Need to reproject
            success, epsg, lon, lat = smart_reproject(geojson_path, reprojected_path, state)
            if not success:
                result['error'] = f"No EPSG worked for {state}"
                return result

            result['action'] = 'reprojected'
            result['epsg'] = epsg
            result['coords'] = f"({lon:.2f}, {lat:.2f})"
            final_geojson = reprojected_path

        # Convert to PMTiles
        success, tiles = convert_to_pmtiles(final_geojson, pmtiles_path)
        if not success or tiles == 0:
            result['error'] = "PMTiles conversion failed"
            return result

        result['tiles'] = tiles

        # Upload to R2
        upload = run_aws(['cp', pmtiles_path, f's3://{R2_BUCKET}/parcels/{name}.pmtiles'])
        if upload.returncode != 0:
            result['error'] = "Upload failed"
            return result

        result['success'] = True

    except Exception as e:
        result['error'] = str(e)[:100]
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return result

def main():
    start_time = datetime.now()

    print("=" * 80)
    print("SMART PARALLEL REPROJECT - Auto-detect CRS")
    print("=" * 80)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Agents: {NUM_AGENTS}")
    print("=" * 80)

    # Get list of GeoJSON files on R2
    print("\nFetching GeoJSON files from R2...")
    listing = run_aws(['ls', f's3://{R2_BUCKET}/parcels/'])

    files_to_process = []
    for line in listing.stdout.strip().split('\n'):
        if '.geojson' in line:
            parts = line.split()
            if len(parts) >= 4:
                name = parts[3].replace('.geojson', '').split('/')[-1]
                state = get_state_from_name(name)
                # Only process files from missing states
                if state in ['AL', 'AR', 'FL', 'ID', 'MO', 'MS', 'MT', 'NV', 'OK', 'SC', 'SD', 'VT', 'WY']:
                    files_to_process.append({'name': name, 'state': state})

    print(f"Found {len(files_to_process)} GeoJSON files from missing states\n")

    if not files_to_process:
        print("No GeoJSON files to process")
        return 0

    # Process in parallel
    results = []
    with ThreadPoolExecutor(max_workers=NUM_AGENTS) as executor:
        futures = {executor.submit(process_file, f): f for f in files_to_process}

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)

            icon = "✓" if result['success'] else "✗"
            print(f"[{i}/{len(files_to_process)}] {icon} {result['name']} ({result['state']})")
            if result['success']:
                action = result['action']
                if action == 'reprojected':
                    print(f"    Reprojected from EPSG:{result['epsg']} -> {result['coords']} ({result['tiles']:,} tiles)")
                else:
                    print(f"    Already valid at {result['coords']} ({result['tiles']:,} tiles)")
            else:
                print(f"    Error: {result['error']}")

    # Summary
    elapsed = datetime.now() - start_time
    successful = [r for r in results if r['success']]
    reprojected = [r for r in successful if r['action'] == 'reprojected']

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Time: {elapsed}")
    print(f"Processed: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Reprojected: {len(reprojected)}")
    print(f"Total tiles: {sum(r['tiles'] for r in successful):,}")

    if successful:
        # Group by state
        by_state = {}
        for r in successful:
            state = r['state']
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(r)

        print(f"\nStates fixed ({len(by_state)}):")
        for state in sorted(by_state.keys()):
            files = by_state[state]
            total_tiles = sum(f['tiles'] for f in files)
            print(f"  {state}: {len(files)} files, {total_tiles:,} tiles")

    # Save results
    with open('/tmp/smart_reproject_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'successful': [r['name'] for r in successful],
            'reprojected': [{'name': r['name'], 'epsg': r['epsg']} for r in reprojected]
        }, f, indent=2)

    print(f"\nResults: /tmp/smart_reproject_results.json")

    return 0 if len(successful) > 0 else 1

if __name__ == '__main__':
    sys.exit(main())
