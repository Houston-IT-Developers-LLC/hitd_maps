#!/usr/bin/env python3
"""
REBUILD ALL PARCELS
Downloads GeoJSON sources, reprojects to WGS84, converts to PMTiles, uploads to R2.
Uses all available CPU cores for parallel processing.
"""

import subprocess
import os
import json
import requests
import tempfile
import shutil
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
import multiprocessing
import sys
import re

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# Number of parallel workers (limited by I/O and memory)
NUM_WORKERS = min(8, multiprocessing.cpu_count())

# State Plane EPSG codes by state (most common ones)
STATE_PLANE_CODES = {
    'TX': ['EPSG:2278', 'EPSG:2277', 'EPSG:2276', 'EPSG:2279', 'EPSG:2280'],  # TX zones
    'GA': ['EPSG:2240', 'EPSG:2239'],  # GA East/West
    'FL': ['EPSG:2236', 'EPSG:2237', 'EPSG:2238'],  # FL zones
    'CA': ['EPSG:2227', 'EPSG:2228', 'EPSG:2229', 'EPSG:2230', 'EPSG:2231', 'EPSG:2232'],  # CA zones
    'NY': ['EPSG:2260', 'EPSG:2261', 'EPSG:2262', 'EPSG:2263'],  # NY zones
    'PA': ['EPSG:2271', 'EPSG:2272'],  # PA North/South
    'OH': ['EPSG:3734', 'EPSG:3735'],  # OH North/South
    'MI': ['EPSG:2251', 'EPSG:2252', 'EPSG:2253'],  # MI zones
    'MN': ['EPSG:2243', 'EPSG:2244', 'EPSG:2245'],  # MN zones
    'MO': ['EPSG:2401', 'EPSG:2402', 'EPSG:2403'],  # MO zones
    'NC': ['EPSG:2264'],  # NC
    'VA': ['EPSG:2283', 'EPSG:2284'],  # VA North/South
    'WA': ['EPSG:2285', 'EPSG:2286'],  # WA North/South
    'CO': ['EPSG:2231', 'EPSG:2232', 'EPSG:2233'],  # CO zones
}

# Common fallback projections to try
FALLBACK_EPSGS = [
    'EPSG:3857',   # Web Mercator
    'EPSG:32614',  # UTM Zone 14N
    'EPSG:32615',  # UTM Zone 15N
    'EPSG:32616',  # UTM Zone 16N
    'EPSG:32617',  # UTM Zone 17N
    'EPSG:32618',  # UTM Zone 18N
    'EPSG:32610',  # UTM Zone 10N (West Coast)
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
    parts = name.replace('parcels_', '').split('_')
    if parts:
        state = parts[0].upper()
        if len(state) == 2:
            return state
    return None

def detect_crs_from_coordinates(geojson_path):
    """Try to detect CRS from coordinate ranges"""
    try:
        with open(geojson_path, 'r') as f:
            # Read just enough to find first coordinate
            content = f.read(10000)
            match = re.search(r'\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]', content)
            if match:
                x, y = float(match.group(1)), float(match.group(2))

                # WGS84 bounds
                if -180 <= x <= 180 and -90 <= y <= 90:
                    return 'WGS84'

                # US State Plane (feet) - typically x: 0-3M, y: 0-15M
                if 0 < x < 4000000 and 0 < y < 16000000:
                    return 'STATE_PLANE_FEET'

                # UTM (meters) - typically x: 100k-900k, y: 0-10M
                if 100000 < x < 1000000 and 0 < y < 10000000:
                    return 'UTM'

                # Web Mercator - x: -20M to 20M
                if -20037508 < x < 20037508:
                    return 'WEB_MERCATOR'

        return 'UNKNOWN'
    except:
        return 'UNKNOWN'

def reproject_geojson(input_path, output_path, state=None):
    """Reproject GeoJSON to WGS84, trying multiple source CRS"""
    crs_type = detect_crs_from_coordinates(input_path)
    print(f"      Detected CRS type: {crs_type}")

    # Build list of projections to try
    projections_to_try = []

    if crs_type == 'WGS84':
        # Already in WGS84, just copy
        shutil.copy(input_path, output_path)
        return True, 'WGS84 (no reprojection needed)'

    if crs_type == 'WEB_MERCATOR':
        projections_to_try = ['EPSG:3857']
    elif state and state in STATE_PLANE_CODES:
        projections_to_try = STATE_PLANE_CODES[state]

    projections_to_try.extend(FALLBACK_EPSGS)

    for epsg in projections_to_try:
        try:
            result = subprocess.run([
                'ogr2ogr',
                '-f', 'GeoJSON',
                '-t_srs', 'EPSG:4326',
                '-s_srs', epsg,
                '-skipfailures',
                output_path,
                input_path
            ], capture_output=True, text=True, timeout=600)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                # Verify output has valid WGS84 coordinates
                with open(output_path, 'r') as f:
                    content = f.read(5000)
                    match = re.search(r'\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]', content)
                    if match:
                        x, y = float(match.group(1)), float(match.group(2))
                        if -180 <= x <= 180 and -90 <= y <= 90:
                            return True, epsg

                # Invalid output, remove and try next
                os.remove(output_path)
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)

    return False, 'Failed all projections'

def process_parcel_file(file_info):
    """Process a single parcel file: download, reproject, convert, upload"""
    name = file_info['name']
    size = file_info['size']
    work_dir = tempfile.mkdtemp(prefix=f"parcel_{name}_")

    result = {
        'name': name,
        'success': False,
        'source_crs': None,
        'error': None,
        'new_size': 0
    }

    try:
        print(f"\n  Processing: {name} ({size/(1024*1024):.1f} MB)")
        state = get_state_from_name(name)

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

        # Reproject to WGS84
        print(f"    Reprojecting...")
        success, source_crs = reproject_geojson(geojson_path, reprojected_path, state)
        result['source_crs'] = source_crs

        if not success:
            result['error'] = f'Reprojection failed: {source_crs}'
            return result

        print(f"    Reprojected from {source_crs}")

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
        print(f"    SUCCESS: {name}")

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
    print("REBUILD ALL PARCELS - PARALLEL PROCESSING PIPELINE")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Workers: {NUM_WORKERS}")
    print(f"CPU Cores: {multiprocessing.cpu_count()}")
    print("=" * 80)

    # Get all GeoJSON files
    print("\nFetching GeoJSON file list from R2...")
    geojson_files = get_geojson_files()
    print(f"Found {len(geojson_files)} GeoJSON source files")

    if not geojson_files:
        print("No GeoJSON files to process!")
        return

    # Sort by size (smallest first for faster initial feedback)
    geojson_files.sort(key=lambda x: x['size'])

    # Show what we're processing
    print("\nFiles to process:")
    total_size = sum(f['size'] for f in geojson_files)
    print(f"  Total: {len(geojson_files)} files, {total_size/(1024*1024*1024):.2f} GB")

    # Process files
    print("\n" + "=" * 80)
    print("PROCESSING FILES")
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
        for r in successful:
            print(f"  ✓ {r['name']} ({r['new_size']/(1024*1024):.1f} MB, from {r['source_crs']})")
        print(f"\nTotal new PMTiles size: {total_new_size/(1024*1024*1024):.2f} GB")

    if failed:
        print(f"\nFailed files:")
        for r in failed:
            print(f"  ✗ {r['name']}: {r['error']}")

    # Save results
    with open('/tmp/rebuild_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': elapsed.total_seconds(),
            'total': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'results': results
        }, f, indent=2)

    print(f"\nResults saved to /tmp/rebuild_results.json")

if __name__ == '__main__':
    main()
