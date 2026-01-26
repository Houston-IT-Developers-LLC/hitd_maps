#!/usr/bin/env python3
"""
SMART PARCEL REPROJECTION PIPELINE
Auto-detects source CRS by testing all possible EPSG codes and validating
that output coordinates land within expected US state bounding boxes.
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

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

NUM_WORKERS = min(8, multiprocessing.cpu_count())

# US State bounding boxes (approximate) for validation
STATE_BOUNDS = {
    'AL': {'min_lat': 30.1, 'max_lat': 35.0, 'min_lon': -88.5, 'max_lon': -84.9},
    'AK': {'min_lat': 51.0, 'max_lat': 71.5, 'min_lon': -180.0, 'max_lon': -130.0},
    'AZ': {'min_lat': 31.3, 'max_lat': 37.0, 'min_lon': -114.8, 'max_lon': -109.0},
    'AR': {'min_lat': 33.0, 'max_lat': 36.5, 'min_lon': -94.6, 'max_lon': -89.6},
    'CA': {'min_lat': 32.5, 'max_lat': 42.0, 'min_lon': -124.5, 'max_lon': -114.1},
    'CO': {'min_lat': 36.9, 'max_lat': 41.0, 'min_lon': -109.1, 'max_lon': -102.0},
    'CT': {'min_lat': 40.9, 'max_lat': 42.1, 'min_lon': -73.7, 'max_lon': -71.8},
    'DE': {'min_lat': 38.4, 'max_lat': 39.8, 'min_lon': -75.8, 'max_lon': -75.0},
    'FL': {'min_lat': 24.5, 'max_lat': 31.0, 'min_lon': -87.6, 'max_lon': -80.0},
    'GA': {'min_lat': 30.4, 'max_lat': 35.0, 'min_lon': -85.6, 'max_lon': -80.8},
    'HI': {'min_lat': 18.9, 'max_lat': 22.2, 'min_lon': -160.3, 'max_lon': -154.8},
    'ID': {'min_lat': 42.0, 'max_lat': 49.0, 'min_lon': -117.2, 'max_lon': -111.0},
    'IL': {'min_lat': 36.9, 'max_lat': 42.5, 'min_lon': -91.5, 'max_lon': -87.0},
    'IN': {'min_lat': 37.8, 'max_lat': 41.8, 'min_lon': -88.1, 'max_lon': -84.8},
    'IA': {'min_lat': 40.4, 'max_lat': 43.5, 'min_lon': -96.6, 'max_lon': -90.1},
    'KS': {'min_lat': 36.9, 'max_lat': 40.0, 'min_lon': -102.1, 'max_lon': -94.6},
    'KY': {'min_lat': 36.5, 'max_lat': 39.1, 'min_lon': -89.6, 'max_lon': -81.9},
    'LA': {'min_lat': 28.9, 'max_lat': 33.0, 'min_lon': -94.0, 'max_lon': -89.0},
    'ME': {'min_lat': 43.0, 'max_lat': 47.5, 'min_lon': -71.1, 'max_lon': -66.9},
    'MD': {'min_lat': 37.9, 'max_lat': 39.7, 'min_lon': -79.5, 'max_lon': -75.0},
    'MA': {'min_lat': 41.2, 'max_lat': 42.9, 'min_lon': -73.5, 'max_lon': -69.9},
    'MI': {'min_lat': 41.7, 'max_lat': 48.2, 'min_lon': -90.4, 'max_lon': -82.4},
    'MN': {'min_lat': 43.5, 'max_lat': 49.4, 'min_lon': -97.2, 'max_lon': -89.5},
    'MS': {'min_lat': 30.2, 'max_lat': 35.0, 'min_lon': -91.7, 'max_lon': -88.1},
    'MO': {'min_lat': 35.9, 'max_lat': 40.6, 'min_lon': -95.8, 'max_lon': -89.1},
    'MT': {'min_lat': 44.4, 'max_lat': 49.0, 'min_lon': -116.0, 'max_lon': -104.0},
    'NE': {'min_lat': 40.0, 'max_lat': 43.0, 'min_lon': -104.1, 'max_lon': -95.3},
    'NV': {'min_lat': 35.0, 'max_lat': 42.0, 'min_lon': -120.0, 'max_lon': -114.0},
    'NH': {'min_lat': 42.7, 'max_lat': 45.3, 'min_lon': -72.6, 'max_lon': -70.7},
    'NJ': {'min_lat': 38.9, 'max_lat': 41.4, 'min_lon': -75.6, 'max_lon': -73.9},
    'NM': {'min_lat': 31.3, 'max_lat': 37.0, 'min_lon': -109.1, 'max_lon': -103.0},
    'NY': {'min_lat': 40.5, 'max_lat': 45.0, 'min_lon': -79.8, 'max_lon': -71.9},
    'NC': {'min_lat': 33.8, 'max_lat': 36.6, 'min_lon': -84.3, 'max_lon': -75.5},
    'ND': {'min_lat': 45.9, 'max_lat': 49.0, 'min_lon': -104.1, 'max_lon': -96.6},
    'OH': {'min_lat': 38.4, 'max_lat': 42.0, 'min_lon': -84.8, 'max_lon': -80.5},
    'OK': {'min_lat': 33.6, 'max_lat': 37.0, 'min_lon': -103.0, 'max_lon': -94.4},
    'OR': {'min_lat': 41.9, 'max_lat': 46.3, 'min_lon': -124.6, 'max_lon': -116.5},
    'PA': {'min_lat': 39.7, 'max_lat': 42.3, 'min_lon': -80.5, 'max_lon': -74.7},
    'RI': {'min_lat': 41.1, 'max_lat': 42.0, 'min_lon': -71.9, 'max_lon': -71.1},
    'SC': {'min_lat': 32.0, 'max_lat': 35.2, 'min_lon': -83.4, 'max_lon': -78.5},
    'SD': {'min_lat': 42.5, 'max_lat': 45.9, 'min_lon': -104.1, 'max_lon': -96.4},
    'TN': {'min_lat': 35.0, 'max_lat': 36.7, 'min_lon': -90.3, 'max_lon': -81.6},
    'TX': {'min_lat': 25.8, 'max_lat': 36.5, 'min_lon': -106.6, 'max_lon': -93.5},
    'UT': {'min_lat': 37.0, 'max_lat': 42.0, 'min_lon': -114.1, 'max_lon': -109.0},
    'VT': {'min_lat': 42.7, 'max_lat': 45.0, 'min_lon': -73.4, 'max_lon': -71.5},
    'VA': {'min_lat': 36.5, 'max_lat': 39.5, 'min_lon': -83.7, 'max_lon': -75.2},
    'WA': {'min_lat': 45.5, 'max_lat': 49.0, 'min_lon': -124.8, 'max_lon': -116.9},
    'WV': {'min_lat': 37.2, 'max_lat': 40.6, 'min_lon': -82.6, 'max_lon': -77.7},
    'WI': {'min_lat': 42.5, 'max_lat': 47.1, 'min_lon': -92.9, 'max_lon': -86.8},
    'WY': {'min_lat': 40.9, 'max_lat': 45.0, 'min_lon': -111.1, 'max_lon': -104.1},
    'DC': {'min_lat': 38.8, 'max_lat': 39.0, 'min_lon': -77.1, 'max_lon': -76.9},
}

# Comprehensive list of EPSG codes to try for each state
# Ordered by likelihood for each state
STATE_EPSG_PRIORITY = {
    'TX': [
        'EPSG:2278',  # TX South Central (Harris, Austin area)
        'EPSG:2277',  # TX North Central (Dallas, Fort Worth)
        'EPSG:2276',  # TX North
        'EPSG:2279',  # TX South
        'EPSG:2280',  # TX Central
        'EPSG:6587',  # TX Centric Albers
        'EPSG:3081',  # TX State Mapping System
        'EPSG:3082',  # TX Centric Lambert
        'EPSG:3083',  # TX Centric Albers
        'EPSG:32614', # UTM Zone 14N
        'EPSG:32613', # UTM Zone 13N
        'EPSG:32615', # UTM Zone 15N
        'EPSG:3857',  # Web Mercator
    ],
    'GA': ['EPSG:2240', 'EPSG:2239', 'EPSG:32616', 'EPSG:32617', 'EPSG:3857'],
    'FL': ['EPSG:2236', 'EPSG:2237', 'EPSG:2238', 'EPSG:3086', 'EPSG:3087', 'EPSG:32617', 'EPSG:3857'],
    'CA': ['EPSG:2227', 'EPSG:2228', 'EPSG:2229', 'EPSG:2230', 'EPSG:2231', 'EPSG:2232', 'EPSG:3310', 'EPSG:32610', 'EPSG:32611', 'EPSG:3857'],
    'NY': ['EPSG:2260', 'EPSG:2261', 'EPSG:2262', 'EPSG:2263', 'EPSG:32618', 'EPSG:3857'],
    'PA': ['EPSG:2271', 'EPSG:2272', 'EPSG:32617', 'EPSG:32618', 'EPSG:3857'],
    'OH': ['EPSG:3734', 'EPSG:3735', 'EPSG:32617', 'EPSG:3857'],
    'MI': ['EPSG:2251', 'EPSG:2252', 'EPSG:2253', 'EPSG:32616', 'EPSG:32617', 'EPSG:3857'],
    'NC': ['EPSG:2264', 'EPSG:32617', 'EPSG:32618', 'EPSG:3857'],
    'VA': ['EPSG:2283', 'EPSG:2284', 'EPSG:32617', 'EPSG:32618', 'EPSG:3857'],
    'WA': ['EPSG:2285', 'EPSG:2286', 'EPSG:32610', 'EPSG:3857'],
    'LA': ['EPSG:3451', 'EPSG:3452', 'EPSG:32615', 'EPSG:3857'],
    'SC': ['EPSG:2273', 'EPSG:32617', 'EPSG:3857'],
    'AL': ['EPSG:26929', 'EPSG:26930', 'EPSG:32616', 'EPSG:3857'],
    'AZ': ['EPSG:2222', 'EPSG:2223', 'EPSG:2224', 'EPSG:32612', 'EPSG:3857'],
    'CO': ['EPSG:2231', 'EPSG:2232', 'EPSG:2233', 'EPSG:32613', 'EPSG:3857'],
    'IL': ['EPSG:3435', 'EPSG:3436', 'EPSG:32616', 'EPSG:3857'],
    'IN': ['EPSG:2965', 'EPSG:2966', 'EPSG:32616', 'EPSG:3857'],
    'MO': ['EPSG:2401', 'EPSG:2402', 'EPSG:2403', 'EPSG:32615', 'EPSG:3857'],
    'TN': ['EPSG:2274', 'EPSG:32616', 'EPSG:3857'],
    'MN': ['EPSG:2243', 'EPSG:2244', 'EPSG:2245', 'EPSG:32615', 'EPSG:3857'],
    'WI': ['EPSG:2287', 'EPSG:2288', 'EPSG:2289', 'EPSG:32616', 'EPSG:3857'],
    'OK': ['EPSG:2267', 'EPSG:2268', 'EPSG:32614', 'EPSG:3857'],
    'KS': ['EPSG:2257', 'EPSG:2258', 'EPSG:32614', 'EPSG:3857'],
    'NE': ['EPSG:32614', 'EPSG:32615', 'EPSG:3857'],
    'NM': ['EPSG:2257', 'EPSG:2258', 'EPSG:2259', 'EPSG:32613', 'EPSG:3857'],
    'NV': ['EPSG:32611', 'EPSG:32610', 'EPSG:3857'],
    'UT': ['EPSG:2280', 'EPSG:2281', 'EPSG:2282', 'EPSG:32612', 'EPSG:3857'],
    'OR': ['EPSG:2269', 'EPSG:2270', 'EPSG:32610', 'EPSG:3857'],
    'ID': ['EPSG:2241', 'EPSG:2242', 'EPSG:32611', 'EPSG:32612', 'EPSG:3857'],
    'MT': ['EPSG:32612', 'EPSG:32613', 'EPSG:3857'],
    'WY': ['EPSG:32612', 'EPSG:32613', 'EPSG:3857'],
    'ND': ['EPSG:32614', 'EPSG:3857'],
    'SD': ['EPSG:32614', 'EPSG:3857'],
    'KY': ['EPSG:2246', 'EPSG:2247', 'EPSG:32616', 'EPSG:3857'],
    'WV': ['EPSG:2250', 'EPSG:32617', 'EPSG:3857'],
    'MD': ['EPSG:2248', 'EPSG:32618', 'EPSG:3857'],
    'NJ': ['EPSG:2256', 'EPSG:32618', 'EPSG:3857'],
    'CT': ['EPSG:2234', 'EPSG:32618', 'EPSG:3857'],
    'MA': ['EPSG:2249', 'EPSG:32619', 'EPSG:3857'],
    'NH': ['EPSG:2255', 'EPSG:32619', 'EPSG:3857'],
    'VT': ['EPSG:2294', 'EPSG:32618', 'EPSG:3857'],
    'ME': ['EPSG:2249', 'EPSG:32619', 'EPSG:3857'],
    'RI': ['EPSG:2249', 'EPSG:32619', 'EPSG:3857'],
    'DE': ['EPSG:2235', 'EPSG:32618', 'EPSG:3857'],
    'MS': ['EPSG:2254', 'EPSG:32615', 'EPSG:32616', 'EPSG:3857'],
    'AR': ['EPSG:2247', 'EPSG:2248', 'EPSG:32615', 'EPSG:3857'],
    'IA': ['EPSG:2243', 'EPSG:2244', 'EPSG:32615', 'EPSG:3857'],
    'AK': ['EPSG:3338', 'EPSG:32606', 'EPSG:3857'],
    'HI': ['EPSG:2784', 'EPSG:2783', 'EPSG:32604', 'EPSG:3857'],
}

# Fallback EPSG list for any state
FALLBACK_EPSGS = [
    'EPSG:3857',   # Web Mercator
    'EPSG:32614',  # UTM Zone 14N
    'EPSG:32615',  # UTM Zone 15N
    'EPSG:32616',  # UTM Zone 16N
    'EPSG:32617',  # UTM Zone 17N
    'EPSG:32618',  # UTM Zone 18N
    'EPSG:32610',  # UTM Zone 10N
    'EPSG:32611',  # UTM Zone 11N
    'EPSG:32612',  # UTM Zone 12N
    'EPSG:32613',  # UTM Zone 13N
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

def get_geojson_files():
    """Get list of all GeoJSON files from R2"""
    result = run_aws(['ls', f's3://{R2_BUCKET}/parcels/', '--recursive'])
    files = []
    for line in result.stdout.strip().split('\n'):
        if '.geojson' in line and 'parcels/' in line:
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3]
                name = path.split('/')[-1].replace('.geojson', '')
                size = int(parts[2])
                files.append({'name': name, 'size': size})
    return files

def get_state_from_name(name):
    """Extract state code from parcel filename"""
    # Handle formats like: parcels_tx, parcels_tx_harris, parcels_tx_statewide
    parts = name.replace('parcels_', '').split('_')
    if parts:
        state = parts[0].upper()
        if len(state) == 2 and state in STATE_BOUNDS:
            return state
    return None

def coords_in_state_bounds(lon, lat, state):
    """Check if coordinates are within state bounds"""
    if state not in STATE_BOUNDS:
        # If no bounds defined, accept if in continental US
        return -130 <= lon <= -65 and 24 <= lat <= 50

    bounds = STATE_BOUNDS[state]
    # Add some tolerance
    tolerance = 2.0
    return (bounds['min_lon'] - tolerance <= lon <= bounds['max_lon'] + tolerance and
            bounds['min_lat'] - tolerance <= lat <= bounds['max_lat'] + tolerance)

def extract_first_coordinate(geojson_path):
    """Extract first coordinate from GeoJSON"""
    try:
        with open(geojson_path, 'r') as f:
            content = f.read(20000)
            match = re.search(r'\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]', content)
            if match:
                return float(match.group(1)), float(match.group(2))
    except:
        pass
    return None, None

def is_wgs84_coords(x, y):
    """Check if coordinates are already in WGS84"""
    return -180 <= x <= 180 and -90 <= y <= 90

def try_reprojection(input_path, output_path, source_epsg, state):
    """Try reprojection with given EPSG and validate output"""
    try:
        # Remove output if exists
        if os.path.exists(output_path):
            os.remove(output_path)

        result = subprocess.run([
            'ogr2ogr',
            '-f', 'GeoJSON',
            '-t_srs', 'EPSG:4326',
            '-s_srs', source_epsg,
            '-skipfailures',
            output_path,
            input_path
        ], capture_output=True, text=True, timeout=600)

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
            return False, None, None

        # Extract and validate coordinates
        x, y = extract_first_coordinate(output_path)
        if x is None:
            os.remove(output_path)
            return False, None, None

        # Check if output is valid WGS84 in the correct state
        if is_wgs84_coords(x, y) and coords_in_state_bounds(x, y, state):
            return True, x, y

        os.remove(output_path)
        return False, x, y

    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        return False, None, None

def smart_reproject(input_path, output_path, state):
    """Smart reprojection that validates output lands in correct state"""

    # First check if already WGS84
    x, y = extract_first_coordinate(input_path)
    if x is not None and is_wgs84_coords(x, y):
        if coords_in_state_bounds(x, y, state):
            shutil.copy(input_path, output_path)
            return True, 'WGS84 (no reprojection)', x, y

    # Get list of EPSG codes to try for this state
    epsg_list = STATE_EPSG_PRIORITY.get(state, []) + FALLBACK_EPSGS
    # Remove duplicates while preserving order
    seen = set()
    epsg_list = [x for x in epsg_list if not (x in seen or seen.add(x))]

    print(f"      Trying {len(epsg_list)} EPSG codes for {state}...")

    for epsg in epsg_list:
        success, out_x, out_y = try_reprojection(input_path, output_path, epsg, state)
        if success:
            return True, epsg, out_x, out_y

    return False, 'All EPSG codes failed', None, None

def process_parcel_file(file_info):
    """Process a single parcel file with smart reprojection"""
    name = file_info['name']
    size = file_info['size']
    work_dir = tempfile.mkdtemp(prefix=f"smart_{name}_")

    result = {
        'name': name,
        'success': False,
        'source_crs': None,
        'output_lon': None,
        'output_lat': None,
        'error': None,
        'new_size': 0
    }

    try:
        print(f"\n  Processing: {name} ({size/(1024*1024):.1f} MB)")
        state = get_state_from_name(name)

        if not state:
            result['error'] = f'Could not determine state from name: {name}'
            return result

        print(f"    State: {state}")

        geojson_url = f"{CDN}/parcels/{name}.geojson"
        geojson_path = os.path.join(work_dir, f"{name}.geojson")
        reprojected_path = os.path.join(work_dir, f"{name}_wgs84.geojson")
        pmtiles_path = os.path.join(work_dir, f"{name}.pmtiles")

        # Download GeoJSON
        print(f"    Downloading...")
        resp = requests.get(geojson_url, stream=True, timeout=1200)
        resp.raise_for_status()

        with open(geojson_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)

        actual_size = os.path.getsize(geojson_path)
        print(f"    Downloaded: {actual_size/(1024*1024):.1f} MB")

        # Check original coordinates
        orig_x, orig_y = extract_first_coordinate(geojson_path)
        print(f"    Original coords: ({orig_x}, {orig_y})")

        # Smart reprojection with validation
        print(f"    Smart reprojecting...")
        success, source_crs, out_x, out_y = smart_reproject(geojson_path, reprojected_path, state)

        result['source_crs'] = source_crs
        result['output_lon'] = out_x
        result['output_lat'] = out_y

        if not success:
            result['error'] = f'Reprojection failed: {source_crs}'
            return result

        print(f"    Reprojected from {source_crs}")
        print(f"    Output coords: ({out_x}, {out_y}) - validated in {state}")

        # Convert to PMTiles
        print(f"    Converting to PMTiles...")
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
            reprojected_path
        ], capture_output=True, text=True, timeout=1800)

        if proc.returncode != 0:
            result['error'] = f'tippecanoe error: {proc.stderr[:200]}'
            return result

        if not os.path.exists(pmtiles_path):
            result['error'] = 'PMTiles not created'
            return result

        pmtiles_size = os.path.getsize(pmtiles_path)
        if pmtiles_size < 1000:
            result['error'] = f'PMTiles too small: {pmtiles_size} bytes'
            return result

        result['new_size'] = pmtiles_size
        print(f"    PMTiles created: {pmtiles_size/(1024*1024):.1f} MB")

        # Verify PMTiles
        verify = subprocess.run(['pmtiles', 'show', pmtiles_path], capture_output=True, text=True)
        if 'pmtiles spec version' not in verify.stdout:
            result['error'] = 'Invalid PMTiles output'
            return result

        # Upload to R2
        print(f"    Uploading to R2...")
        upload = run_aws(['cp', pmtiles_path, f's3://{R2_BUCKET}/parcels/{name}.pmtiles'])

        if upload.returncode != 0:
            result['error'] = f'Upload failed: {upload.stderr[:100]}'
            return result

        result['success'] = True
        print(f"    SUCCESS: {name} ({out_x:.4f}, {out_y:.4f})")

    except requests.exceptions.RequestException as e:
        result['error'] = f'Download error: {str(e)[:100]}'
    except subprocess.TimeoutExpired:
        result['error'] = 'Processing timeout'
    except Exception as e:
        result['error'] = f'Error: {str(e)[:100]}'
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return result

def main():
    start_time = datetime.now()
    print("=" * 80)
    print("SMART PARCEL REPROJECTION PIPELINE")
    print("Auto-detects CRS and validates output coordinates land in correct state")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Workers: {NUM_WORKERS}")
    print("=" * 80)

    # Get all GeoJSON files
    print("\nFetching GeoJSON file list from R2...")
    geojson_files = get_geojson_files()
    print(f"Found {len(geojson_files)} GeoJSON source files")

    if not geojson_files:
        print("No GeoJSON files to process!")
        return

    # Sort by size (smallest first)
    geojson_files.sort(key=lambda x: x['size'])

    # Show summary
    total_size = sum(f['size'] for f in geojson_files)
    print(f"Total: {len(geojson_files)} files, {total_size/(1024*1024*1024):.2f} GB")

    # Process files
    print("\n" + "=" * 80)
    print("PROCESSING FILES WITH SMART REPROJECTION")
    print("=" * 80)

    results = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(process_parcel_file, f): f for f in geojson_files}

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    # Summary
    elapsed = datetime.now() - start_time
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\nTime elapsed: {elapsed}")
    print(f"Total files: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        total_new_size = sum(r['new_size'] for r in successful)
        print(f"\nSuccessfully rebuilt:")
        for r in sorted(successful, key=lambda x: x['name']):
            coords = f"({r['output_lon']:.4f}, {r['output_lat']:.4f})" if r['output_lon'] else "?"
            print(f"  ✓ {r['name']} ({r['new_size']/(1024*1024):.1f} MB) from {r['source_crs']} -> {coords}")
        print(f"\nTotal new PMTiles size: {total_new_size/(1024*1024*1024):.2f} GB")

    if failed:
        print(f"\nFailed files:")
        for r in failed:
            print(f"  ✗ {r['name']}: {r['error']}")

    # Save results
    with open('/tmp/smart_reproject_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': elapsed.total_seconds(),
            'total': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'results': results
        }, f, indent=2)

    print(f"\nResults saved to /tmp/smart_reproject_results.json")

if __name__ == '__main__':
    main()
