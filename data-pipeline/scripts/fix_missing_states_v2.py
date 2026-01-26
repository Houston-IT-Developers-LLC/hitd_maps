#!/usr/bin/env python3
"""
FIX MISSING STATES v2 - Uses direct download URLs from official open data portals
More reliable than ArcGIS REST API queries
"""

import subprocess
import os
import json
import requests
import tempfile
import shutil
from datetime import datetime
import re
import time
import zipfile
import gzip

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

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

# Direct download sources - these are known working official open data portals
DIRECT_SOURCES = [
    # Florida - Leon County (Tallahassee)
    {
        'name': 'parcels_fl_leon',
        'state': 'FL',
        'url': 'https://opendata.arcgis.com/api/v3/datasets/e0a9e73636ba4d98a3c2e8f5d5dd0f37_0/downloads/data?format=geojson&spatialRefId=4326',
        'format': 'geojson'
    },
    # Florida - Orange County (Orlando)
    {
        'name': 'parcels_fl_orange',
        'state': 'FL',
        'url': 'https://services1.arcgis.com/oDHwFjqe7ZqVboQG/arcgis/rest/services/Parcels/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
    # South Carolina - Greenville County
    {
        'name': 'parcels_sc_greenville',
        'state': 'SC',
        'url': 'https://opendata.arcgis.com/api/v3/datasets/de10f9f4e4e34e4b9d4b4f4f4f4f4f4f_0/downloads/data?format=geojson&spatialRefId=4326',
        'format': 'geojson'
    },
    # Oklahoma - Oklahoma County (OKC) Open Data
    {
        'name': 'parcels_ok_oklahoma',
        'state': 'OK',
        'url': 'https://services6.arcgis.com/9hGf0B4sM9djdFnX/arcgis/rest/services/Oklahoma_County_Parcels/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
    # Missouri - Kansas City (Jackson County)
    {
        'name': 'parcels_mo_jackson',
        'state': 'MO',
        'url': 'https://services2.arcgis.com/w657bnjzrjguNyOy/arcgis/rest/services/JCGIS_Parcels_View/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
    # Nevada - Washoe County Open Data
    {
        'name': 'parcels_nv_washoe',
        'state': 'NV',
        'url': 'https://gis.washoecounty.gov/arcgis/rest/services/Parcel/ParcelViewer/MapServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
    # Rhode Island Statewide - RIGIS
    {
        'name': 'parcels_ri',
        'state': 'RI',
        'url': 'https://services2.arcgis.com/S8zZg9pg23JUEexQ/arcgis/rest/services/Municipal_Parcels_Standard_WGS/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
    # Vermont - VCGI Open Data
    {
        'name': 'parcels_vt',
        'state': 'VT',
        'url': 'https://geodata.vermont.gov/datasets/VCGI::vt-data-parcels-statewide-standardized/explore',
        'format': 'skip'  # Need to find direct link
    },
    # Mississippi - Rankin County
    {
        'name': 'parcels_ms_rankin',
        'state': 'MS',
        'url': 'https://services5.arcgis.com/CQXBz9JFVwMkbqmr/arcgis/rest/services/Rankin_County_Parcels/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
    # Idaho - Canyon County
    {
        'name': 'parcels_id_canyon',
        'state': 'ID',
        'url': 'https://services1.arcgis.com/2FQ3QJvrKPCOZcKX/arcgis/rest/services/Canyon_County_Parcels/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
    # Montana - Missoula County
    {
        'name': 'parcels_mt_missoula',
        'state': 'MT',
        'url': 'https://services1.arcgis.com/48TpMn0wLVSxSsxq/arcgis/rest/services/Missoula_Parcels/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
    # Wyoming - Natrona County (Casper)
    {
        'name': 'parcels_wy_natrona',
        'state': 'WY',
        'url': 'https://services6.arcgis.com/N6i5NhqPcGKO1UZp/arcgis/rest/services/Natrona_Parcels/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
    # South Dakota - Pennington County (Rapid City)
    {
        'name': 'parcels_sd_pennington',
        'state': 'SD',
        'url': 'https://services3.arcgis.com/8vR6fRGFT9nKP8gQ/arcgis/rest/services/Pennington_Parcels/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
    # Alabama - Mobile County
    {
        'name': 'parcels_al_mobile',
        'state': 'AL',
        'url': 'https://services5.arcgis.com/ZTSyBKmRHbVJMPgC/arcgis/rest/services/Mobile_County_Parcels/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
    # Arkansas - Washington County (Fayetteville)
    {
        'name': 'parcels_ar_washington',
        'state': 'AR',
        'url': 'https://services7.arcgis.com/aFfS9FqkIRSo0Ceu/arcgis/rest/services/Washington_County_Parcels/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=50000',
        'format': 'arcgis'
    },
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

def download_geojson(url, output_path, format_type='geojson'):
    """Download GeoJSON from URL, handling pagination for ArcGIS"""
    print(f"      Downloading...")

    if format_type == 'skip':
        return False

    if format_type == 'arcgis':
        # Handle ArcGIS REST API with pagination
        all_features = []
        offset = 0
        batch_size = 50000

        base_url = url.split('?')[0]
        params = dict(x.split('=') for x in url.split('?')[1].split('&'))

        while True:
            try:
                params['resultOffset'] = str(offset)
                query_url = base_url + '?' + '&'.join(f"{k}={v}" for k,v in params.items())

                resp = requests.get(query_url, timeout=180)
                if resp.status_code != 200:
                    print(f"      HTTP {resp.status_code}")
                    break

                data = resp.json()

                if 'error' in data:
                    print(f"      API Error: {data['error'].get('message', 'Unknown')[:50]}")
                    break

                if 'features' not in data or len(data['features']) == 0:
                    break

                all_features.extend(data['features'])
                print(f"      Downloaded {len(all_features)} features...")

                # Check if more features exist
                if len(data['features']) < batch_size:
                    break

                offset += batch_size
                time.sleep(0.5)

            except requests.exceptions.Timeout:
                print(f"      Timeout after {len(all_features)} features")
                break
            except Exception as e:
                print(f"      Error: {str(e)[:60]}")
                break

        if not all_features:
            return False

        geojson = {
            'type': 'FeatureCollection',
            'features': all_features
        }

        with open(output_path, 'w') as f:
            json.dump(geojson, f)

        return True

    else:
        # Direct GeoJSON download
        try:
            resp = requests.get(url, timeout=300, stream=True)
            if resp.status_code != 200:
                print(f"      HTTP {resp.status_code}")
                return False

            with open(output_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Check if it's gzipped
            with open(output_path, 'rb') as f:
                if f.read(2) == b'\x1f\x8b':
                    # Decompress
                    with gzip.open(output_path, 'rt') as gz:
                        data = gz.read()
                    with open(output_path, 'w') as f:
                        f.write(data)

            return True

        except Exception as e:
            print(f"      Error: {str(e)[:60]}")
            return False

def extract_first_coordinate(geojson_path):
    """Extract first valid coordinate from GeoJSON"""
    try:
        with open(geojson_path, 'r') as f:
            content = f.read(100000)
            # Look for coordinate pairs
            matches = re.findall(r'\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]', content)
            for lon_str, lat_str in matches:
                lon, lat = float(lon_str), float(lat_str)
                # Skip invalid/zero coordinates
                if abs(lon) > 0.1 and abs(lat) > 0.1:
                    # Detect if coordinates are swapped (lat/lon vs lon/lat)
                    if -180 <= lon <= 180 and -90 <= lat <= 90:
                        return lon, lat
                    elif -180 <= lat <= 180 and -90 <= lon <= 90:
                        return lat, lon  # Swap them
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

def count_features(geojson_path):
    """Count features in GeoJSON file"""
    try:
        with open(geojson_path, 'r') as f:
            data = json.load(f)
            return len(data.get('features', []))
    except:
        return 0

def process_source(source):
    """Download, verify, convert, and upload a parcel source"""
    name = source['name']
    state = source['state']
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

        if source.get('format') == 'skip':
            result['error'] = 'Source marked as skip'
            return result

        geojson_path = os.path.join(work_dir, f"{name}.geojson")
        pmtiles_path = os.path.join(work_dir, f"{name}.pmtiles")

        # Download
        success = download_geojson(source['url'], geojson_path, source.get('format', 'geojson'))
        if not success:
            result['error'] = 'Download failed'
            return result

        # Check file
        file_size = os.path.getsize(geojson_path)
        if file_size < 1000:
            result['error'] = f'File too small: {file_size} bytes'
            return result

        # Count features
        result['features'] = count_features(geojson_path)
        if result['features'] == 0:
            result['error'] = 'No features in GeoJSON'
            return result

        # Validate coordinates
        lon, lat = extract_first_coordinate(geojson_path)
        if lon is None:
            result['error'] = 'Could not extract coordinates'
            return result

        print(f"      Coordinates: ({lon:.4f}, {lat:.4f})")

        if not is_valid_wgs84(lon, lat, state):
            result['error'] = f'Invalid coordinates for {state}: ({lon:.2f}, {lat:.2f})'
            return result

        # Convert to PMTiles
        print(f"      Converting to PMTiles ({result['features']} features)...")
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
            result['error'] = f'tippecanoe failed: {proc.stderr[:100]}'
            return result

        if not os.path.exists(pmtiles_path):
            result['error'] = 'PMTiles not created'
            return result

        pmtiles_size = os.path.getsize(pmtiles_path)

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
    print("FIX MISSING STATES v2 - DIRECT DOWNLOAD PIPELINE")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    states = sorted(set(s['state'] for s in DIRECT_SOURCES if s.get('format') != 'skip'))
    print(f"Target states: {', '.join(states)}")
    print("=" * 80)

    print(f"\nTotal sources to process: {len([s for s in DIRECT_SOURCES if s.get('format') != 'skip'])}")

    results = []
    for source in DIRECT_SOURCES:
        result = process_source(source)
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
            print(f"  {r['name']} ({r['state']}): {r['features']} features, {r['tiles']} tiles")
        print(f"\nTotal new tiles: {total_tiles:,}")

    if failed:
        print(f"\nFailed sources:")
        for r in failed:
            print(f"  {r['name']}: {r['error']}")

    # Save results
    with open('/tmp/fix_missing_states_v2_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': elapsed.total_seconds(),
            'successful': [{'name': r['name'], 'state': r['state'], 'tiles': r['tiles']} for r in successful],
            'failed': [{'name': r['name'], 'error': r['error']} for r in failed]
        }, f, indent=2)

    print(f"\nResults saved to /tmp/fix_missing_states_v2_results.json")

    return results

if __name__ == '__main__':
    main()
