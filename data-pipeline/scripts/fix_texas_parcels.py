#!/usr/bin/env python3
"""
Fix Texas parcel files - diagnose and repair invalid PMTiles.
Deploys parallel workers to verify and fix all TX parcel files.
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

# Texas parcel files to check
TX_FILES = [
    'parcels_tx',
    'parcels_tx_statewide',
    'parcels_tx_statewide_recent',
    'parcels_tx_harris',
    'parcels_tx_harris_new',
    'parcels_tx_dallas',
    'parcels_tx_bexar',
    'parcels_tx_tarrant',
    'parcels_tx_travis',
    'parcels_tx_denton',
    'parcels_tx_williamson_v2',
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
        'size_mb': 0,
        'valid_pmtiles': False,
        'has_tiles': False,
        'issue': None,
        'source_layer': None,
        'minzoom': None,
        'maxzoom': None
    }

    try:
        # Check if file exists and get size
        resp = requests.head(url, timeout=10)
        if resp.status_code == 404:
            result['issue'] = 'FILE_NOT_FOUND'
            return result

        result['exists'] = True
        result['size'] = int(resp.headers.get('content-length', 0))
        result['size_mb'] = round(result['size'] / (1024*1024), 2)

        if result['size'] < 50000:  # Less than 50KB is suspicious
            result['issue'] = 'FILE_TOO_SMALL'

        # Download first 64KB to check format
        resp = requests.get(url, headers={'Range': 'bytes=0-65535'}, timeout=30)
        content = resp.content

        # Check PMTiles magic number
        if len(content) >= 2 and content[0:2] == b'PM':
            result['valid_pmtiles'] = True

            # Write to temp and check with pmtiles CLI
            tmp_path = f"/tmp/check_{name}.pmtiles"
            with open(tmp_path, 'wb') as f:
                f.write(content)

            proc = subprocess.run(['pmtiles', 'show', tmp_path], capture_output=True, text=True, timeout=10)
            output = proc.stdout + proc.stderr

            if 'pmtiles spec version' in output:
                # Extract metadata
                for line in output.split('\n'):
                    if 'min zoom:' in line:
                        result['minzoom'] = int(line.split(':')[1].strip())
                    if 'max zoom:' in line:
                        result['maxzoom'] = int(line.split(':')[1].strip())
                    if 'tile entries:' in line.lower():
                        entries = line.split(':')[1].strip()
                        if int(entries) > 0:
                            result['has_tiles'] = True

                # Check for source layer
                result['source_layer'] = 'parcels'  # Default

                if result['has_tiles'] and result['size'] > 100000:
                    result['issue'] = None  # Valid file
                elif not result['has_tiles']:
                    result['issue'] = 'NO_TILE_DATA'
                else:
                    result['issue'] = 'SUSPICIOUSLY_SMALL'
            else:
                result['issue'] = 'CORRUPT_PMTILES'

            try:
                os.remove(tmp_path)
            except:
                pass
        else:
            result['issue'] = 'NOT_PMTILES_FORMAT'
            result['first_bytes'] = content[:20].hex()

    except Exception as e:
        result['issue'] = f'ERROR: {str(e)}'

    return result

def convert_geojson_to_pmtiles(name, work_dir):
    """Convert GeoJSON from R2 to PMTiles"""
    geojson_url = f"{CDN}/parcels/{name}.geojson"
    geojson_path = os.path.join(work_dir, f"{name}.geojson")
    pmtiles_path = os.path.join(work_dir, f"{name}.pmtiles")

    # Check if GeoJSON exists
    resp = requests.head(geojson_url, timeout=10)
    if resp.status_code != 200:
        return None, f"No GeoJSON source found at {geojson_url}"

    geojson_size = int(resp.headers.get('content-length', 0))
    print(f"    Downloading {name}.geojson ({geojson_size / (1024*1024):.1f} MB)...")

    # Download GeoJSON
    resp = requests.get(geojson_url, stream=True, timeout=600)
    with open(geojson_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"    Converting to PMTiles with tippecanoe...")

    # Convert with tippecanoe
    result = subprocess.run([
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
    ], capture_output=True, text=True, timeout=1800)  # 30 min timeout

    if result.returncode != 0:
        return None, f"tippecanoe failed: {result.stderr}"

    if os.path.exists(pmtiles_path) and os.path.getsize(pmtiles_path) > 50000:
        return pmtiles_path, None

    return None, "Output file too small or missing"

def upload_to_r2(local_path, name):
    """Upload fixed PMTiles to R2"""
    s3_path = f"s3://{R2_BUCKET}/parcels/{name}.pmtiles"

    print(f"    Uploading to R2...")
    result = run_aws(['cp', local_path, s3_path])

    if result.returncode == 0:
        return True, None
    return False, result.stderr

def fix_file(name, work_dir):
    """Attempt to fix a file"""
    print(f"\n  Attempting to fix: {name}")

    # Try to convert from GeoJSON source
    pmtiles_path, error = convert_geojson_to_pmtiles(name, work_dir)

    if error:
        print(f"    FAILED: {error}")
        return False, error

    # Verify the converted file
    result = subprocess.run(['pmtiles', 'show', pmtiles_path], capture_output=True, text=True)
    if 'pmtiles spec version' not in result.stdout:
        return False, "Converted file is not valid PMTiles"

    # Upload to R2
    success, error = upload_to_r2(pmtiles_path, name)
    if success:
        print(f"    SUCCESS: Fixed and uploaded!")
        return True, None

    return False, error

def main():
    print("=" * 70)
    print("TEXAS PARCEL FIXER - Parallel Diagnostic & Repair Agent")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Phase 1: Diagnose all files
    print("\n" + "=" * 70)
    print("PHASE 1: DIAGNOSING ALL TEXAS PARCEL FILES")
    print("=" * 70 + "\n")

    diagnoses = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(diagnose_file, name): name for name in TX_FILES}
        for future in as_completed(futures):
            diag = future.result()
            diagnoses.append(diag)

            status = "VALID" if not diag['issue'] else diag['issue']
            size_str = f"{diag['size_mb']:.1f} MB" if diag['size_mb'] else "N/A"
            print(f"  [{status}] {diag['name']} - {size_str}")
            if diag['minzoom'] is not None:
                print(f"       Zoom: {diag['minzoom']}-{diag['maxzoom']}, Tiles: {'Yes' if diag['has_tiles'] else 'No'}")

    # Identify files needing fixes
    valid = [d for d in diagnoses if not d['issue']]
    invalid = [d for d in diagnoses if d['issue']]

    print(f"\n  Valid files: {len(valid)}/{len(TX_FILES)}")
    print(f"  Invalid files: {len(invalid)}/{len(TX_FILES)}")

    if not invalid:
        print("\n  All Texas files are valid!")
        return

    # Phase 2: Fix invalid files
    print("\n" + "=" * 70)
    print("PHASE 2: FIXING INVALID FILES")
    print("=" * 70)

    fixed = []
    failed = []

    for diag in invalid:
        work_dir = tempfile.mkdtemp(prefix=f"fix_tx_{diag['name']}_")
        try:
            success, error = fix_file(diag['name'], work_dir)
            if success:
                fixed.append(diag['name'])
            else:
                failed.append({'name': diag['name'], 'reason': error})
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Originally valid: {len(valid)}")
    print(f"  Fixed: {len(fixed)}")
    print(f"  Failed: {len(failed)}")

    if fixed:
        print(f"\n  Fixed files:")
        for name in fixed:
            print(f"    ✓ {name}")

    if failed:
        print(f"\n  Failed files:")
        for f in failed:
            print(f"    ✗ {f['name']}: {f['reason']}")

    # Final verification
    print("\n" + "=" * 70)
    print("PHASE 3: FINAL VERIFICATION")
    print("=" * 70 + "\n")

    final_diagnoses = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(diagnose_file, name): name for name in TX_FILES}
        for future in as_completed(futures):
            diag = future.result()
            final_diagnoses.append(diag)

            status = "✓ VALID" if not diag['issue'] else f"✗ {diag['issue']}"
            size_str = f"{diag['size_mb']:.1f} MB" if diag['size_mb'] else "N/A"
            print(f"  [{status}] {diag['name']} - {size_str}")

    final_valid = len([d for d in final_diagnoses if not d['issue']])
    print(f"\n  Final status: {final_valid}/{len(TX_FILES)} Texas parcel files are valid")

    # Save results
    with open('/tmp/tx_fix_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_files': len(TX_FILES),
            'originally_valid': len(valid),
            'fixed': fixed,
            'failed': [f['name'] for f in failed],
            'final_diagnoses': final_diagnoses
        }, f, indent=2)

    print(f"\n  Results saved to /tmp/tx_fix_results.json")

if __name__ == '__main__':
    main()
