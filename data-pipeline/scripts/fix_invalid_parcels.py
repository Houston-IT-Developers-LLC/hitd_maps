#!/usr/bin/env python3
"""
Agent to fix invalid/corrupted parcel files on R2.
Analyzes issues, attempts repairs, and re-uploads fixed files.
"""

import subprocess
import os
import json
import requests
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# Invalid files from verification
INVALID_FILES = [
    'parcels_ak_fnsb_direct',
    'parcels_ak_blm_state',
    'parcels_ca_orange',
    'parcels_ca_sacramento',
    'parcels_co_larimer',
    'parcels_ct_bridgeport',
    'parcels_fl_duval',
    'parcels_fl_orange',
    'parcels_fl_statewide',
    'parcels_id_canyon',
    'parcels_in_statewide',
    'parcels_ky_jefferson',
    'parcels_ky_fayette_v2',
    'parcels_la_ebr',
    'parcels_me',
    'parcels_ms_rankin',
    'parcels_ne_lancaster',
    'parcels_ne_hall',
    'parcels_nh_nashua',
    'parcels_nm_bernalillo',
    'parcels_nm_dona_ana',
    'parcels_nm_santa_fe',
    'parcels_ny_erie',
    'parcels_ny_monroe',
    'parcels_oh_lucas',
    'parcels_ok_creek',
    'parcels_ok_edmond',
    'parcels_ok_osage',
    'parcels_or_marion_v2',
    'parcels_pa_chester',
    'parcels_pa_pasda_statewide',
    'parcels_pa_montgomery',
    'parcels_vt_statewide',
    'parcels_wi_dane',
    'parcels_wv_statewide',
    'parcels_wi_milwaukee_v2',
    'parcels_wv_statewide_v2',
    'parcels_wy_park'
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

def diagnose_file(name):
    """Diagnose what's wrong with a file"""
    url = f"{CDN}/parcels/{name}.pmtiles"
    result = {
        'name': name,
        'exists': False,
        'size': 0,
        'issue': None,
        'fixable': False,
        'fix_action': None
    }

    try:
        # Check if file exists and get size
        resp = requests.head(url, timeout=10)
        if resp.status_code == 404:
            result['issue'] = 'FILE_NOT_FOUND'
            result['fixable'] = False
            return result

        result['exists'] = True
        result['size'] = int(resp.headers.get('content-length', 0))

        if result['size'] < 1000:
            result['issue'] = 'FILE_TOO_SMALL'
            result['fixable'] = False
            return result

        # Download first 100KB to check format
        resp = requests.get(url, headers={'Range': 'bytes=0-102400'}, timeout=30)
        content = resp.content

        # Check PMTiles magic number (first 2 bytes should be 0x50 0x4D = "PM")
        if len(content) >= 2:
            if content[0:2] == b'PM':
                result['issue'] = 'VALID_PMTILES'
                return result
            elif content[0:2] == b'PK':
                result['issue'] = 'IS_ZIP_FILE'
                result['fixable'] = True
                result['fix_action'] = 'EXTRACT_AND_CONVERT'
            elif content[0:4] == b'SQLi' or b'SQLite' in content[:20]:
                result['issue'] = 'IS_MBTILES'
                result['fixable'] = True
                result['fix_action'] = 'CONVERT_MBTILES'
            elif content[0:1] == b'{':
                result['issue'] = 'IS_GEOJSON'
                result['fixable'] = True
                result['fix_action'] = 'CONVERT_GEOJSON'
            else:
                result['issue'] = 'UNKNOWN_FORMAT'
                result['fixable'] = False
                # Show first few bytes for debugging
                result['first_bytes'] = content[:20].hex()
        else:
            result['issue'] = 'EMPTY_OR_CORRUPT'
            result['fixable'] = False

    except Exception as e:
        result['issue'] = f'ERROR: {str(e)}'
        result['fixable'] = False

    return result

def fix_mbtiles(name, work_dir):
    """Convert MBTiles to PMTiles"""
    url = f"{CDN}/parcels/{name}.pmtiles"
    mbtiles_path = os.path.join(work_dir, f"{name}.mbtiles")
    pmtiles_path = os.path.join(work_dir, f"{name}.pmtiles")

    print(f"    Downloading {name}...")
    resp = requests.get(url, stream=True, timeout=300)
    with open(mbtiles_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"    Converting MBTiles to PMTiles...")
    result = subprocess.run(
        ['pmtiles', 'convert', mbtiles_path, pmtiles_path],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        return None, f"Conversion failed: {result.stderr}"

    if os.path.exists(pmtiles_path):
        return pmtiles_path, None
    return None, "Output file not created"

def fix_zip(name, work_dir):
    """Extract ZIP and convert contents to PMTiles"""
    url = f"{CDN}/parcels/{name}.pmtiles"
    zip_path = os.path.join(work_dir, f"{name}.zip")
    extract_dir = os.path.join(work_dir, f"{name}_extracted")
    pmtiles_path = os.path.join(work_dir, f"{name}.pmtiles")

    print(f"    Downloading {name}...")
    resp = requests.get(url, stream=True, timeout=300)
    with open(zip_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"    Extracting ZIP...")
    os.makedirs(extract_dir, exist_ok=True)
    result = subprocess.run(['unzip', '-o', zip_path, '-d', extract_dir], capture_output=True)

    # Find shapefiles or geojson
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            if f.endswith('.shp'):
                shp_path = os.path.join(root, f)
                geojson_path = os.path.join(work_dir, f"{name}.geojson")

                print(f"    Converting shapefile to GeoJSON...")
                result = subprocess.run(
                    ['ogr2ogr', '-f', 'GeoJSON', '-t_srs', 'EPSG:4326', geojson_path, shp_path],
                    capture_output=True
                )

                if os.path.exists(geojson_path):
                    print(f"    Converting GeoJSON to PMTiles...")
                    result = subprocess.run([
                        'tippecanoe', '-o', pmtiles_path,
                        '-l', 'parcels',
                        '--minimum-zoom=5', '--maximum-zoom=15',
                        '--drop-densest-as-needed',
                        '--extend-zooms-if-still-dropping',
                        '--simplification=10',
                        '--force',
                        geojson_path
                    ], capture_output=True)

                    if os.path.exists(pmtiles_path):
                        return pmtiles_path, None

            elif f.endswith('.geojson') or f.endswith('.json'):
                geojson_path = os.path.join(root, f)
                print(f"    Converting GeoJSON to PMTiles...")
                result = subprocess.run([
                    'tippecanoe', '-o', pmtiles_path,
                    '-l', 'parcels',
                    '--minimum-zoom=5', '--maximum-zoom=15',
                    '--drop-densest-as-needed',
                    '--extend-zooms-if-still-dropping',
                    '--simplification=10',
                    '--force',
                    geojson_path
                ], capture_output=True)

                if os.path.exists(pmtiles_path):
                    return pmtiles_path, None

    return None, "No convertible files found in ZIP"

def upload_fixed_file(pmtiles_path, name):
    """Upload fixed PMTiles to R2"""
    s3_path = f"s3://{R2_BUCKET}/parcels/{name}.pmtiles"

    print(f"    Uploading to R2...")
    result = run_aws(['cp', pmtiles_path, s3_path])

    if result.returncode == 0:
        return True, None
    return False, result.stderr

def verify_upload(name):
    """Verify the uploaded file is valid"""
    url = f"{CDN}/parcels/{name}.pmtiles"

    try:
        resp = requests.get(url, headers={'Range': 'bytes=0-65535'}, timeout=30)
        if resp.content[:2] == b'PM':
            return True
    except:
        pass
    return False

def process_file(name):
    """Process a single invalid file"""
    print(f"\n{'='*60}")
    print(f"Processing: {name}")
    print('='*60)

    # Diagnose
    diagnosis = diagnose_file(name)
    print(f"  Issue: {diagnosis['issue']}")
    print(f"  Size: {diagnosis['size']:,} bytes")
    print(f"  Fixable: {diagnosis['fixable']}")

    if not diagnosis['fixable']:
        print(f"  SKIPPED: Cannot fix this file")
        return {'name': name, 'status': 'skipped', 'reason': diagnosis['issue']}

    # Create temp directory for work
    work_dir = tempfile.mkdtemp(prefix=f"fix_{name}_")

    try:
        pmtiles_path = None
        error = None

        if diagnosis['fix_action'] == 'CONVERT_MBTILES':
            pmtiles_path, error = fix_mbtiles(name, work_dir)
        elif diagnosis['fix_action'] == 'EXTRACT_AND_CONVERT':
            pmtiles_path, error = fix_zip(name, work_dir)

        if error:
            print(f"  FAILED: {error}")
            return {'name': name, 'status': 'failed', 'reason': error}

        if pmtiles_path and os.path.exists(pmtiles_path):
            # Verify the converted file
            result = subprocess.run(['pmtiles', 'show', pmtiles_path], capture_output=True, text=True)
            if 'pmtiles spec version' not in result.stdout:
                print(f"  FAILED: Converted file is not valid PMTiles")
                return {'name': name, 'status': 'failed', 'reason': 'Invalid conversion'}

            # Upload
            success, error = upload_fixed_file(pmtiles_path, name)
            if success:
                # Verify upload
                if verify_upload(name):
                    print(f"  SUCCESS: Fixed and uploaded!")
                    return {'name': name, 'status': 'fixed'}
                else:
                    print(f"  FAILED: Upload verification failed")
                    return {'name': name, 'status': 'failed', 'reason': 'Verification failed'}
            else:
                print(f"  FAILED: Upload failed - {error}")
                return {'name': name, 'status': 'failed', 'reason': error}

        print(f"  FAILED: No output file generated")
        return {'name': name, 'status': 'failed', 'reason': 'No output'}

    finally:
        # Cleanup
        shutil.rmtree(work_dir, ignore_errors=True)

def main():
    print("="*60)
    print("HITD Maps - Invalid Parcel File Fixer")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print(f"\nFiles to process: {len(INVALID_FILES)}")

    # First, diagnose all files
    print("\n" + "="*60)
    print("DIAGNOSIS PHASE")
    print("="*60)

    diagnoses = []
    for name in INVALID_FILES:
        diag = diagnose_file(name)
        diagnoses.append(diag)
        status = "FIXABLE" if diag['fixable'] else "SKIP"
        print(f"  [{status}] {name}: {diag['issue']}")

    fixable = [d for d in diagnoses if d['fixable']]
    print(f"\nFixable files: {len(fixable)}/{len(INVALID_FILES)}")

    # Process fixable files
    print("\n" + "="*60)
    print("REPAIR PHASE")
    print("="*60)

    results = []
    for diag in diagnoses:
        if diag['fixable']:
            result = process_file(diag['name'])
            results.append(result)
        else:
            results.append({'name': diag['name'], 'status': 'skipped', 'reason': diag['issue']})

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    fixed = [r for r in results if r['status'] == 'fixed']
    failed = [r for r in results if r['status'] == 'failed']
    skipped = [r for r in results if r['status'] == 'skipped']

    print(f"Fixed:   {len(fixed)}")
    print(f"Failed:  {len(failed)}")
    print(f"Skipped: {len(skipped)}")

    if fixed:
        print("\nFixed files:")
        for r in fixed:
            print(f"  ✓ {r['name']}")

    if failed:
        print("\nFailed files:")
        for r in failed:
            print(f"  ✗ {r['name']}: {r.get('reason', 'Unknown')}")

    if skipped:
        print("\nSkipped files (not fixable):")
        for r in skipped:
            print(f"  - {r['name']}: {r.get('reason', 'Unknown')}")

    # Save results
    with open('/tmp/fix_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total': len(INVALID_FILES),
            'fixed': len(fixed),
            'failed': len(failed),
            'skipped': len(skipped),
            'results': results
        }, f, indent=2)

    print(f"\nResults saved to /tmp/fix_results.json")
    return len(fixed), len(failed), len(skipped)

if __name__ == '__main__':
    main()
