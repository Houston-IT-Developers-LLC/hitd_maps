#!/usr/bin/env python3
"""
Reproject local GeoJSON files and convert to PMTiles
Handles State Plane / Web Mercator -> WGS84 conversion
"""

import subprocess
import os
import json
import tempfile
import shutil
from pathlib import Path
import re
import time

# Directories
SCRIPT_DIR = Path(__file__).parent
PIPELINE_DIR = SCRIPT_DIR.parent
DOWNLOADS = PIPELINE_DIR / "data" / "downloads"
OUTPUT = PIPELINE_DIR / "output" / "pmtiles"
OUTPUT.mkdir(parents=True, exist_ok=True)

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# Skip files being converted elsewhere
SKIP_FILES = {'parcels_fl_statewide.geojson'}

# US State bounding boxes for validation
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

# EPSG codes to try for each state (ordered by likelihood)
STATE_EPSG_PRIORITY = {
    'TX': ['EPSG:2278', 'EPSG:2277', 'EPSG:2276', 'EPSG:2279', 'EPSG:2280', 'EPSG:3857'],
    'GA': ['EPSG:2240', 'EPSG:2239', 'EPSG:32616', 'EPSG:32617', 'EPSG:3857'],
    'FL': ['EPSG:2236', 'EPSG:2237', 'EPSG:2238', 'EPSG:3086', 'EPSG:3087', 'EPSG:3857'],
    'CA': ['EPSG:2230', 'EPSG:2229', 'EPSG:2228', 'EPSG:2227', 'EPSG:3310', 'EPSG:6423', 'EPSG:6424', 'EPSG:6425', 'EPSG:6426', 'EPSG:3857'],
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
    'NM': ['EPSG:2903', 'EPSG:2902', 'EPSG:2904', 'EPSG:32613', 'EPSG:3857'],
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
    'ME': ['EPSG:2249', 'EPSG:26919', 'EPSG:32619', 'EPSG:3857'],
    'RI': ['EPSG:2249', 'EPSG:32619', 'EPSG:3857'],
    'DE': ['EPSG:2235', 'EPSG:32618', 'EPSG:3857'],
    'MS': ['EPSG:2254', 'EPSG:32615', 'EPSG:32616', 'EPSG:3857'],
    'AR': ['EPSG:2247', 'EPSG:2248', 'EPSG:32615', 'EPSG:3857'],
    'IA': ['EPSG:2243', 'EPSG:2244', 'EPSG:32615', 'EPSG:3857'],
    'AK': ['EPSG:3338', 'EPSG:32606', 'EPSG:3857'],
    'HI': ['EPSG:2784', 'EPSG:2783', 'EPSG:32604', 'EPSG:3857'],
}

FALLBACK_EPSGS = ['EPSG:3857', 'EPSG:32614', 'EPSG:32615', 'EPSG:32616', 'EPSG:32617', 'EPSG:32618']


def get_state_from_name(name):
    """Extract state code from filename"""
    parts = name.replace('parcels_', '').split('_')
    if parts:
        state = parts[0].upper()
        if len(state) == 2 and state in STATE_BOUNDS:
            return state
    return None


def extract_first_coord(geojson_path):
    """Extract first coordinate from GeoJSON efficiently"""
    try:
        with open(geojson_path, 'r') as f:
            content = f.read(50000)
            match = re.search(r'\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]', content)
            if match:
                return float(match.group(1)), float(match.group(2))
    except:
        pass
    return None, None


def is_wgs84(x, y):
    """Check if coordinates are WGS84"""
    return -180 <= x <= 180 and -90 <= y <= 90


def coords_in_bounds(lon, lat, state):
    """Check if coordinates are within state bounds"""
    if state not in STATE_BOUNDS:
        return -130 <= lon <= -65 and 24 <= lat <= 50
    bounds = STATE_BOUNDS[state]
    tolerance = 2.0
    return (bounds['min_lon'] - tolerance <= lon <= bounds['max_lon'] + tolerance and
            bounds['min_lat'] - tolerance <= lat <= bounds['max_lat'] + tolerance)


def try_reproject(input_path, output_path, source_epsg, state):
    """Try reprojection with given EPSG"""
    try:
        if os.path.exists(output_path):
            os.remove(output_path)

        result = subprocess.run([
            'ogr2ogr', '-f', 'GeoJSON',
            '-t_srs', 'EPSG:4326',
            '-s_srs', source_epsg,
            '-skipfailures',
            output_path, input_path
        ], capture_output=True, text=True, timeout=600)

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
            return False, None, None

        x, y = extract_first_coord(output_path)
        if x is None:
            os.remove(output_path)
            return False, None, None

        if is_wgs84(x, y) and coords_in_bounds(x, y, state):
            return True, x, y

        os.remove(output_path)
        return False, x, y
    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        return False, None, None


def smart_reproject(input_path, output_path, state):
    """Smart reprojection with auto-detection"""
    # Check if already WGS84
    x, y = extract_first_coord(input_path)
    if x is not None and is_wgs84(x, y) and coords_in_bounds(x, y, state):
        shutil.copy(input_path, output_path)
        return True, 'WGS84 (no reprojection)', x, y

    # Get EPSG list for state
    epsg_list = STATE_EPSG_PRIORITY.get(state, []) + FALLBACK_EPSGS
    seen = set()
    epsg_list = [e for e in epsg_list if not (e in seen or seen.add(e))]

    print(f"    Trying {len(epsg_list)} EPSG codes...")

    for epsg in epsg_list:
        success, out_x, out_y = try_reproject(input_path, output_path, epsg, state)
        if success:
            return True, epsg, out_x, out_y

    return False, 'All EPSG codes failed', None, None


def upload_to_r2(local_path, remote_name):
    """Upload file to R2"""
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY
    env['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_KEY

    result = subprocess.run([
        'aws', 's3', 'cp',
        str(local_path),
        f's3://{R2_BUCKET}/parcels/{remote_name}',
        '--endpoint-url', R2_ENDPOINT
    ], capture_output=True, text=True, env=env)

    return result.returncode == 0


def process_file(geojson_path):
    """Process a single GeoJSON file"""
    name = geojson_path.stem
    state = get_state_from_name(name)
    size_mb = geojson_path.stat().st_size / 1024 / 1024

    print(f"\n{'='*60}")
    print(f"PROCESSING: {name} ({size_mb:.1f}MB)")
    print(f"State: {state}")
    print(f"{'='*60}")

    if not state:
        print(f"  SKIP: Could not determine state")
        return "SKIP", None

    # Check original coordinates
    orig_x, orig_y = extract_first_coord(geojson_path)
    print(f"  Original coords: ({orig_x}, {orig_y})")

    # Create temp directory for work
    work_dir = tempfile.mkdtemp(prefix=f"reproject_{name}_")
    reprojected_path = Path(work_dir) / f"{name}_wgs84.geojson"
    pmtiles_path = OUTPUT / f"{name}.pmtiles"

    try:
        # Reproject
        start = time.time()
        success, source_crs, out_x, out_y = smart_reproject(str(geojson_path), str(reprojected_path), state)

        if not success:
            print(f"  FAIL: Reprojection failed - {source_crs}")
            return "FAIL", None

        print(f"  Reprojected from {source_crs} in {time.time()-start:.1f}s")
        print(f"  Output coords: ({out_x:.4f}, {out_y:.4f})")

        # Convert to PMTiles
        print(f"  Converting to PMTiles...")
        start = time.time()
        result = subprocess.run([
            'tippecanoe',
            '-o', str(pmtiles_path),
            '--force',
            '--no-feature-limit', '--no-tile-size-limit',
            '-zg',
            '--drop-densest-as-needed',
            '--extend-zooms-if-still-dropping',
            '-l', 'parcels',
            str(reprojected_path)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  FAIL: tippecanoe error")
            return "FAIL", None

        if not pmtiles_path.exists() or pmtiles_path.stat().st_size < 50000:
            print(f"  FAIL: PMTiles too small")
            return "FAIL", None

        pmtiles_size = pmtiles_path.stat().st_size / 1024 / 1024
        print(f"  PMTiles created: {pmtiles_size:.1f}MB in {time.time()-start:.1f}s")

        # Upload to R2
        print(f"  Uploading to R2...")
        if upload_to_r2(pmtiles_path, f"{name}.pmtiles"):
            print(f"  SUCCESS: {name} uploaded ({pmtiles_size:.1f}MB)")
            return "DONE", pmtiles_size
        else:
            print(f"  FAIL: Upload failed")
            return "UPLOAD_FAIL", None

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def main():
    print("=" * 70)
    print("LOCAL GEOJSON REPROJECTION & CONVERSION PIPELINE")
    print("=" * 70)

    # Get all GeoJSON files sorted by size (smallest first)
    geojson_files = sorted(DOWNLOADS.glob("*.geojson"), key=lambda x: x.stat().st_size)
    geojson_files = [f for f in geojson_files if f.name not in SKIP_FILES]

    total_size = sum(f.stat().st_size for f in geojson_files) / 1024 / 1024 / 1024
    print(f"Found {len(geojson_files)} GeoJSON files ({total_size:.1f}GB)")
    print(f"Skipping: {SKIP_FILES}")

    results = {"DONE": 0, "SKIP": 0, "FAIL": 0, "UPLOAD_FAIL": 0}
    total_uploaded = 0

    for i, geojson_path in enumerate(geojson_files, 1):
        print(f"\n[{i}/{len(geojson_files)}]")
        status, size = process_file(geojson_path)
        results[status] = results.get(status, 0) + 1
        if size:
            total_uploaded += size

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Converted & uploaded: {results['DONE']} ({total_uploaded:.1f}MB)")
    print(f"Skipped: {results['SKIP']}")
    print(f"Failed: {results['FAIL']}")
    print(f"Upload failed: {results['UPLOAD_FAIL']}")


if __name__ == '__main__':
    main()
