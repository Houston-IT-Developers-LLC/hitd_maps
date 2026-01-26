#!/usr/bin/env python3
"""
FIX ALL MISSING STATES - AUTONOMOUS PIPELINE
Downloads fresh parcel data from public GIS portals, processes, and uploads to R2.
Targets the 16 missing states: AK, AL, AR, DC, FL, ID, MO, MS, MT, NV, OK, RI, SC, SD, VT, WY
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

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

NUM_WORKERS = min(10, multiprocessing.cpu_count())

# State bounds for validation
STATE_BOUNDS = {
    'AK': {'min_lat': 51.0, 'max_lat': 71.5, 'min_lon': -180.0, 'max_lon': -130.0},
    'AL': {'min_lat': 30.1, 'max_lat': 35.0, 'min_lon': -88.5, 'max_lon': -84.9},
    'AR': {'min_lat': 33.0, 'max_lat': 36.5, 'min_lon': -94.6, 'max_lon': -89.6},
    'DC': {'min_lat': 38.8, 'max_lat': 39.0, 'min_lon': -77.1, 'max_lon': -76.9},
    'FL': {'min_lat': 24.5, 'max_lat': 31.0, 'min_lon': -87.6, 'max_lon': -80.0},
    'ID': {'min_lat': 42.0, 'max_lat': 49.0, 'min_lon': -117.2, 'max_lon': -111.0},
    'MO': {'min_lat': 35.9, 'max_lat': 40.6, 'min_lon': -95.8, 'max_lon': -89.1},
    'MS': {'min_lat': 30.2, 'max_lat': 35.0, 'min_lon': -91.7, 'max_lon': -88.1},
    'MT': {'min_lat': 44.4, 'max_lat': 49.0, 'min_lon': -116.0, 'max_lon': -104.0},
    'NV': {'min_lat': 35.0, 'max_lat': 42.0, 'min_lon': -120.0, 'max_lon': -114.0},
    'OK': {'min_lat': 33.6, 'max_lat': 37.0, 'min_lon': -103.0, 'max_lon': -94.4},
    'RI': {'min_lat': 41.1, 'max_lat': 42.0, 'min_lon': -71.9, 'max_lon': -71.1},
    'SC': {'min_lat': 32.0, 'max_lat': 35.2, 'min_lon': -83.4, 'max_lon': -78.5},
    'SD': {'min_lat': 42.5, 'max_lat': 45.9, 'min_lon': -104.1, 'max_lon': -96.4},
    'VT': {'min_lat': 42.7, 'max_lat': 45.0, 'min_lon': -73.4, 'max_lon': -71.5},
    'WY': {'min_lat': 40.9, 'max_lat': 45.0, 'min_lon': -111.1, 'max_lon': -104.1},
}

# Public ArcGIS REST API endpoints for parcel data
# These are open data portals that provide GeoJSON exports
PARCEL_SOURCES = {
    # Florida - Multiple county sources
    'FL': [
        {
            'name': 'parcels_fl_hillsborough',
            'url': 'https://gis.hillsboroughcounty.org/arcgis/rest/services/OpenData/Parcels_OpenData/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
        {
            'name': 'parcels_fl_pinellas',
            'url': 'https://egis.pinellascounty.org/arcgis/rest/services/Parcels/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # South Carolina
    'SC': [
        {
            'name': 'parcels_sc_richland',
            'url': 'https://gis.richlandcountysc.gov/arcgis/rest/services/Parcels/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
        {
            'name': 'parcels_sc_charleston',
            'url': 'https://gis.charlestoncounty.org/arcgis/rest/services/Parcels/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # Oklahoma
    'OK': [
        {
            'name': 'parcels_ok_tulsa',
            'url': 'https://gismaps.tulsacounty.org/arcgis/rest/services/Parcels/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
        {
            'name': 'parcels_ok_oklahoma_city',
            'url': 'https://data.okc.gov/arcgis/rest/services/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # Missouri
    'MO': [
        {
            'name': 'parcels_mo_st_louis',
            'url': 'https://maps.stlouisco.com/arcgis/rest/services/OpenData/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # Nevada
    'NV': [
        {
            'name': 'parcels_nv_clark',
            'url': 'https://gisgate.co.clark.nv.us/gismo/rest/services/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
        {
            'name': 'parcels_nv_washoe',
            'url': 'https://gis.washoecounty.us/arcgis/rest/services/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # Rhode Island
    'RI': [
        {
            'name': 'parcels_ri_statewide',
            'url': 'https://services2.arcgis.com/S8zZg9pg23JUEexQ/arcgis/rest/services/RI_Parcels/FeatureServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 100000}
        },
    ],
    # Vermont
    'VT': [
        {
            'name': 'parcels_vt_chittenden',
            'url': 'https://maps.vcgi.vermont.gov/arcgis/rest/services/EGC_services/OPENDATA_VCGI_CADASTRAL_SP_NOCACHE_v1/MapServer/3/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # Mississippi
    'MS': [
        {
            'name': 'parcels_ms_hinds',
            'url': 'https://gis.co.hinds.ms.us/arcgis/rest/services/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # Idaho
    'ID': [
        {
            'name': 'parcels_id_ada',
            'url': 'https://gismaps.adacounty.id.gov/arcgis/rest/services/Parcels/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # Montana
    'MT': [
        {
            'name': 'parcels_mt_yellowstone',
            'url': 'https://gis.co.yellowstone.mt.gov/arcgis/rest/services/Cadastral/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # Wyoming
    'WY': [
        {
            'name': 'parcels_wy_laramie',
            'url': 'https://gis.laramiecounty.com/arcgis/rest/services/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # South Dakota
    'SD': [
        {
            'name': 'parcels_sd_minnehaha',
            'url': 'https://gis.minnehahacounty.org/arcgis/rest/services/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # Alabama
    'AL': [
        {
            'name': 'parcels_al_jefferson',
            'url': 'https://gis.jccal.org/arcgis/rest/services/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # Arkansas
    'AR': [
        {
            'name': 'parcels_ar_pulaski',
            'url': 'https://gis.pulaskicounty.net/arcgis/rest/services/Parcels/MapServer/0/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
    # DC
    'DC': [
        {
            'name': 'parcels_dc',
            'url': 'https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Property_and_Land_WebMercator/MapServer/34/query',
            'params': {'where': '1=1', 'outFields': '*', 'f': 'geojson', 'resultRecordCount': 50000}
        },
    ],
}

# Alternative: Direct GeoJSON download URLs (simpler, more reliable)
DIRECT_GEOJSON_SOURCES = {
    'parcels_dc': 'https://opendata.dc.gov/api/download/v1/items/faea4d66ddc14437aa29c92a3e9a7608/geojson?layers=0',
    'parcels_ri_statewide': 'https://opendata.arcgis.com/api/v3/datasets/5b4f4f4b0e9b4b0a8e1e1e1e1e1e1e1e_0/downloads/data?format=geojson&spatialRefId=4326',
}

def run_aws(args):
    """Run AWS CLI command with R2 credentials"""
    env = {
        **os.environ,
        'AWS_ACCESS_KEY_ID': AWS_ACCESS_KEY,
        'AWS_SECRET_ACCESS_KEY': AWS_SECRET_KEY
    }
    cmd = ['aws', 's3'] + args + ['--endpoint-url', R2_ENDPOINT]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)

def download_arcgis_geojson(url, params, output_path, max_records=100000):
    """Download GeoJSON from ArcGIS REST API with pagination"""
    all_features = []
    offset = 0
    batch_size = params.get('resultRecordCount', 5000)

    print(f"      Downloading from ArcGIS API...")

    while len(all_features) < max_records:
        try:
            query_params = {**params, 'resultOffset': offset}
            resp = requests.get(url, params=query_params, timeout=120)

            if resp.status_code != 200:
                print(f"      HTTP {resp.status_code}")
                break

            data = resp.json()

            if 'features' not in data or len(data['features']) == 0:
                break

            all_features.extend(data['features'])
            print(f"      Downloaded {len(all_features)} features...")

            if len(data['features']) < batch_size:
                break

            offset += batch_size
            time.sleep(0.5)  # Be nice to the server

        except Exception as e:
            print(f"      Error: {str(e)[:50]}")
            break

    if not all_features:
        return False

    # Build GeoJSON
    geojson = {
        'type': 'FeatureCollection',
        'features': all_features
    }

    with open(output_path, 'w') as f:
        json.dump(geojson, f)

    print(f"      Saved {len(all_features)} features to GeoJSON")
    return True

def extract_first_coordinate(geojson_path):
    """Extract first coordinate from GeoJSON"""
    try:
        with open(geojson_path, 'r') as f:
            content = f.read(50000)
            match = re.search(r'\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]', content)
            if match:
                return float(match.group(1)), float(match.group(2))
    except:
        pass
    return None, None

def is_valid_wgs84(lon, lat, state):
    """Check if coordinates are valid WGS84 for the state"""
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        return False

    if state in STATE_BOUNDS:
        bounds = STATE_BOUNDS[state]
        tolerance = 3.0
        return (bounds['min_lon'] - tolerance <= lon <= bounds['max_lon'] + tolerance and
                bounds['min_lat'] - tolerance <= lat <= bounds['max_lat'] + tolerance)
    return True

def process_source(state, source_info):
    """Download, verify, convert, and upload a parcel source"""
    name = source_info['name']
    work_dir = tempfile.mkdtemp(prefix=f"fix_{name}_")

    result = {
        'name': name,
        'state': state,
        'success': False,
        'features': 0,
        'tiles': 0,
        'error': None
    }

    try:
        print(f"\n  [{state}] Processing: {name}")

        geojson_path = os.path.join(work_dir, f"{name}.geojson")
        pmtiles_path = os.path.join(work_dir, f"{name}.pmtiles")

        # Download GeoJSON
        if 'url' in source_info:
            success = download_arcgis_geojson(
                source_info['url'],
                source_info.get('params', {}),
                geojson_path
            )
            if not success:
                result['error'] = 'Download failed'
                return result
        else:
            result['error'] = 'No URL provided'
            return result

        # Check file size
        file_size = os.path.getsize(geojson_path)
        if file_size < 1000:
            result['error'] = f'GeoJSON too small: {file_size} bytes'
            return result

        # Count features
        try:
            with open(geojson_path, 'r') as f:
                data = json.load(f)
                result['features'] = len(data.get('features', []))
        except:
            pass

        # Check coordinates
        lon, lat = extract_first_coordinate(geojson_path)
        if lon is None:
            result['error'] = 'Could not extract coordinates'
            return result

        print(f"      Coordinates: ({lon:.4f}, {lat:.4f})")

        if not is_valid_wgs84(lon, lat, state):
            result['error'] = f'Invalid coordinates for {state}: ({lon:.2f}, {lat:.2f})'
            return result

        # Convert to PMTiles
        print(f"      Converting to PMTiles...")
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
        ], capture_output=True, text=True, timeout=1800)

        if proc.returncode != 0:
            result['error'] = f'tippecanoe failed: {proc.stderr[:100]}'
            return result

        if not os.path.exists(pmtiles_path):
            result['error'] = 'PMTiles not created'
            return result

        pmtiles_size = os.path.getsize(pmtiles_path)
        if pmtiles_size < 5000:
            result['error'] = f'PMTiles too small: {pmtiles_size} bytes'
            return result

        # Verify PMTiles
        verify = subprocess.run(['pmtiles', 'show', pmtiles_path], capture_output=True, text=True)
        if 'tile entries count:' in verify.stdout:
            match = re.search(r'tile entries count:\s*(\d+)', verify.stdout)
            if match:
                result['tiles'] = int(match.group(1))

        if result['tiles'] == 0:
            result['error'] = 'PMTiles has no tiles'
            return result

        # Upload to R2
        print(f"      Uploading to R2 ({pmtiles_size/(1024*1024):.1f} MB, {result['tiles']} tiles)...")
        upload = run_aws(['cp', pmtiles_path, f's3://{R2_BUCKET}/parcels/{name}.pmtiles'])

        if upload.returncode != 0:
            result['error'] = f'Upload failed: {upload.stderr[:50]}'
            return result

        result['success'] = True
        print(f"      SUCCESS: {name} ({result['features']} features, {result['tiles']} tiles)")

    except subprocess.TimeoutExpired:
        result['error'] = 'Timeout'
    except Exception as e:
        result['error'] = str(e)[:100]
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return result

def main():
    start_time = datetime.now()
    print("=" * 80)
    print("FIX ALL MISSING STATES - AUTONOMOUS PIPELINE")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target states: {', '.join(sorted(PARCEL_SOURCES.keys()))}")
    print("=" * 80)

    # Build task list
    tasks = []
    for state, sources in PARCEL_SOURCES.items():
        for source in sources:
            tasks.append((state, source))

    print(f"\nTotal sources to process: {len(tasks)}")

    # Process sources
    results = []

    for state, source in tasks:
        result = process_source(state, source)
        results.append(result)

    # Summary
    elapsed = datetime.now() - start_time
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTime elapsed: {elapsed}")
    print(f"Total sources: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print(f"\nSuccessfully added:")
        total_tiles = 0
        for r in successful:
            total_tiles += r['tiles']
            print(f"  ✓ {r['name']} ({r['state']}): {r['features']} features, {r['tiles']} tiles")
        print(f"\nTotal new tiles: {total_tiles:,}")

    if failed:
        print(f"\nFailed sources:")
        for r in failed:
            print(f"  ✗ {r['name']}: {r['error']}")

    # Save results
    with open('/tmp/fix_missing_states_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': elapsed.total_seconds(),
            'successful': [r['name'] for r in successful],
            'failed': [{'name': r['name'], 'error': r['error']} for r in failed]
        }, f, indent=2)

    print(f"\nResults saved to /tmp/fix_missing_states_results.json")

    return results

if __name__ == '__main__':
    main()
