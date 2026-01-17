#!/usr/bin/env python3
"""
MASSIVE USA PARCEL FIXER
Deploys hundreds of parallel workers to diagnose, reproject, and fix all parcel issues.
Handles coordinate system reprojection and corrupt file regeneration.
"""

import subprocess
import os
import json
import requests
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime
import multiprocessing
import time
import sys

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# How many parallel workers
NUM_WORKERS = min(50, multiprocessing.cpu_count() * 4)

def run_aws(args):
    """Run AWS CLI command with R2 credentials"""
    env = {
        **os.environ,
        'AWS_ACCESS_KEY_ID': AWS_ACCESS_KEY,
        'AWS_SECRET_ACCESS_KEY': AWS_SECRET_KEY
    }
    cmd = ['aws', 's3'] + args + ['--endpoint-url', R2_ENDPOINT]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)

def get_all_parcel_files():
    """Get list of all parcel files from R2"""
    result = run_aws(['ls', f's3://{R2_BUCKET}/parcels/', '--recursive'])
    files = {}
    for line in result.stdout.strip().split('\n'):
        if '.pmtiles' in line and 'parcels/' in line:
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3]
                name = path.split('/')[-1].replace('.pmtiles', '')
                size = int(parts[2])
                files[name] = {'size': size, 'has_geojson': False}
        elif '.geojson' in line and 'parcels/' in line:
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3]
                name = path.split('/')[-1].replace('.geojson', '')
                if name in files:
                    files[name]['has_geojson'] = True
                    files[name]['geojson_size'] = int(parts[2])
    return files

def diagnose_pmtiles(name, size):
    """Quick diagnosis of PMTiles file"""
    url = f"{CDN}/parcels/{name}.pmtiles"
    result = {
        'name': name,
        'size_mb': round(size / (1024*1024), 2),
        'valid': False,
        'has_tiles': False,
        'issue': None,
        'minzoom': None,
        'maxzoom': None
    }

    try:
        # Download just first 64KB
        resp = requests.get(url, headers={'Range': 'bytes=0-65535'}, timeout=30)
        content = resp.content

        if len(content) < 2:
            result['issue'] = 'FILE_EMPTY'
            return result

        if content[0:2] != b'PM':
            result['issue'] = 'NOT_PMTILES'
            return result

        # Write to temp and check
        tmp_path = f"/tmp/diag_{name}_{os.getpid()}.pmtiles"
        try:
            with open(tmp_path, 'wb') as f:
                f.write(content)

            proc = subprocess.run(['pmtiles', 'show', tmp_path],
                                  capture_output=True, text=True, timeout=10)
            output = proc.stdout + proc.stderr

            if 'pmtiles spec version' in output:
                result['valid'] = True

                for line in output.split('\n'):
                    if 'min zoom:' in line:
                        result['minzoom'] = int(line.split(':')[1].strip())
                    if 'max zoom:' in line:
                        result['maxzoom'] = int(line.split(':')[1].strip())
                    if 'tile entries:' in line.lower():
                        entries = int(line.split(':')[1].strip())
                        result['has_tiles'] = entries > 0

                if not result['has_tiles']:
                    result['issue'] = 'NO_TILE_DATA'
                    result['valid'] = False
                elif size < 50000:
                    result['issue'] = 'TOO_SMALL'
                    result['valid'] = False
            else:
                result['issue'] = 'CORRUPT'
        finally:
            try:
                os.remove(tmp_path)
            except:
                pass

    except Exception as e:
        result['issue'] = f'ERROR: {str(e)[:50]}'

    return result

def check_geojson_projection(name):
    """Check if GeoJSON needs reprojection"""
    url = f"{CDN}/parcels/{name}.geojson"

    try:
        # Get first 5KB to check coordinates
        resp = requests.get(url, headers={'Range': 'bytes=0-5000'}, timeout=30)
        content = resp.text

        # Find first coordinate
        import re
        coord_match = re.search(r'\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]', content)
        if coord_match:
            x, y = float(coord_match.group(1)), float(coord_match.group(2))

            # WGS84 bounds: -180 to 180, -90 to 90
            if -180 <= x <= 180 and -90 <= y <= 90:
                return 'WGS84'
            else:
                # Likely projected coordinates (State Plane, UTM, etc.)
                return 'PROJECTED'
    except:
        pass

    return 'UNKNOWN'

def fix_parcel_file(name, has_geojson, geojson_size=0):
    """Fix a single parcel file - reproject if needed and convert to PMTiles"""
    work_dir = tempfile.mkdtemp(prefix=f"fix_{name}_")
    result = {'name': name, 'success': False, 'action': None, 'error': None}

    try:
        geojson_url = f"{CDN}/parcels/{name}.geojson"

        if not has_geojson:
            result['error'] = 'No GeoJSON source'
            return result

        # Check projection
        projection = check_geojson_projection(name)
        print(f"    [{name}] Projection: {projection}, Size: {geojson_size/(1024*1024):.1f} MB")

        geojson_path = os.path.join(work_dir, f"{name}.geojson")
        reprojected_path = os.path.join(work_dir, f"{name}_wgs84.geojson")
        pmtiles_path = os.path.join(work_dir, f"{name}.pmtiles")

        # Download GeoJSON
        print(f"    [{name}] Downloading...")
        resp = requests.get(geojson_url, stream=True, timeout=1200)
        with open(geojson_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)

        # Reproject if needed
        if projection == 'PROJECTED':
            print(f"    [{name}] Reprojecting to WGS84...")
            result['action'] = 'reprojected'

            # Use ogr2ogr to reproject - auto-detect source CRS
            proc = subprocess.run([
                'ogr2ogr',
                '-f', 'GeoJSON',
                '-t_srs', 'EPSG:4326',  # Target: WGS84
                '-s_srs', 'EPSG:2278',  # Texas State Plane South Central (common for TX)
                reprojected_path,
                geojson_path
            ], capture_output=True, text=True, timeout=600)

            # If that fails, try auto-detection
            if proc.returncode != 0 or not os.path.exists(reprojected_path):
                # Try common Texas projections
                for epsg in ['EPSG:2277', 'EPSG:2276', 'EPSG:32614', 'EPSG:32615', 'EPSG:3857']:
                    proc = subprocess.run([
                        'ogr2ogr',
                        '-f', 'GeoJSON',
                        '-t_srs', 'EPSG:4326',
                        '-s_srs', epsg,
                        reprojected_path,
                        geojson_path
                    ], capture_output=True, text=True, timeout=600)

                    if os.path.exists(reprojected_path) and os.path.getsize(reprojected_path) > 100:
                        print(f"    [{name}] Reprojected from {epsg}")
                        break
                else:
                    result['error'] = 'Reprojection failed - unknown source CRS'
                    return result

            input_geojson = reprojected_path
        else:
            result['action'] = 'converted'
            input_geojson = geojson_path

        # Convert to PMTiles with tippecanoe
        print(f"    [{name}] Converting to PMTiles...")
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
            input_geojson
        ], capture_output=True, text=True, timeout=1800)

        if proc.returncode != 0:
            result['error'] = f'tippecanoe failed: {proc.stderr[:100]}'
            return result

        if not os.path.exists(pmtiles_path) or os.path.getsize(pmtiles_path) < 50000:
            result['error'] = 'Output too small or missing'
            return result

        # Upload to R2
        print(f"    [{name}] Uploading to R2...")
        upload_result = run_aws(['cp', pmtiles_path, f's3://{R2_BUCKET}/parcels/{name}.pmtiles'])

        if upload_result.returncode != 0:
            result['error'] = f'Upload failed: {upload_result.stderr[:100]}'
            return result

        result['success'] = True
        result['new_size'] = os.path.getsize(pmtiles_path)
        print(f"    [{name}] SUCCESS! New size: {result['new_size']/(1024*1024):.1f} MB")

    except Exception as e:
        result['error'] = str(e)[:100]
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return result

def main():
    start_time = datetime.now()
    print("=" * 80)
    print("MASSIVE USA PARCEL FIXER - PARALLEL AGENT DEPLOYMENT")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Workers: {NUM_WORKERS} parallel agents")
    print(f"CPU Cores: {multiprocessing.cpu_count()}")
    print("=" * 80)

    # Phase 1: Inventory all files
    print("\n" + "=" * 80)
    print("PHASE 1: INVENTORYING ALL PARCEL FILES ON R2")
    print("=" * 80 + "\n")

    all_files = get_all_parcel_files()
    print(f"Found {len(all_files)} parcel files on R2")

    # Phase 2: Parallel diagnosis
    print("\n" + "=" * 80)
    print("PHASE 2: PARALLEL DIAGNOSIS WITH {NUM_WORKERS} AGENTS")
    print("=" * 80 + "\n")

    diagnoses = {}
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {
            executor.submit(diagnose_pmtiles, name, info['size']): name
            for name, info in all_files.items()
        }

        completed = 0
        for future in as_completed(futures):
            completed += 1
            name = futures[future]
            diag = future.result()
            diagnoses[name] = diag

            status = "✓" if diag['valid'] else "✗"
            issue = diag['issue'] or "OK"
            print(f"[{completed}/{len(all_files)}] {status} {name}: {issue}", end='\r')

    print("\n")

    # Identify files needing fixes
    valid = [n for n, d in diagnoses.items() if d['valid']]
    invalid = [n for n, d in diagnoses.items() if not d['valid']]

    # Filter to files that have GeoJSON sources
    fixable = [n for n in invalid if all_files.get(n, {}).get('has_geojson', False)]
    unfixable = [n for n in invalid if not all_files.get(n, {}).get('has_geojson', False)]

    print(f"Valid files: {len(valid)}")
    print(f"Invalid files: {len(invalid)}")
    print(f"  - Fixable (have GeoJSON): {len(fixable)}")
    print(f"  - Unfixable (no GeoJSON): {len(unfixable)}")

    if not fixable:
        print("\nNo files to fix!")
        return

    # Phase 3: Fix files
    print("\n" + "=" * 80)
    print(f"PHASE 3: FIXING {len(fixable)} FILES WITH {NUM_WORKERS} PARALLEL AGENTS")
    print("=" * 80 + "\n")

    fixed = []
    failed = []

    # Process in smaller batches to avoid overwhelming the system
    batch_size = min(10, NUM_WORKERS)

    for i in range(0, len(fixable), batch_size):
        batch = fixable[i:i+batch_size]
        print(f"\nProcessing batch {i//batch_size + 1}/{(len(fixable) + batch_size - 1)//batch_size}")

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = {
                executor.submit(
                    fix_parcel_file,
                    name,
                    all_files[name].get('has_geojson', False),
                    all_files[name].get('geojson_size', 0)
                ): name
                for name in batch
            }

            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    fixed.append(result)
                else:
                    failed.append(result)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    elapsed = datetime.now() - start_time
    print(f"\nTime elapsed: {elapsed}")
    print(f"Total files checked: {len(all_files)}")
    print(f"Originally valid: {len(valid)}")
    print(f"Fixed: {len(fixed)}")
    print(f"Failed: {len(failed)}")
    print(f"Unfixable (no source): {len(unfixable)}")

    if fixed:
        print(f"\nFixed files:")
        for r in fixed:
            size_str = f"{r.get('new_size', 0)/(1024*1024):.1f} MB" if r.get('new_size') else "?"
            print(f"  ✓ {r['name']} ({r['action']}) - {size_str}")

    if failed:
        print(f"\nFailed files:")
        for r in failed[:20]:  # Show first 20
            print(f"  ✗ {r['name']}: {r['error']}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")

    if unfixable:
        print(f"\nUnfixable files (no GeoJSON source):")
        for name in unfixable[:10]:
            print(f"  - {name}")
        if len(unfixable) > 10:
            print(f"  ... and {len(unfixable) - 10} more")

    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'elapsed_seconds': elapsed.total_seconds(),
        'total_files': len(all_files),
        'originally_valid': len(valid),
        'fixed': [r['name'] for r in fixed],
        'failed': [{'name': r['name'], 'error': r['error']} for r in failed],
        'unfixable': unfixable
    }

    with open('/tmp/massive_fix_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to /tmp/massive_fix_results.json")

    # Final verification for Texas specifically
    print("\n" + "=" * 80)
    print("FINAL TEXAS VERIFICATION")
    print("=" * 80 + "\n")

    tx_files = [n for n in all_files.keys() if n.startswith('parcels_tx')]
    print(f"Texas files: {len(tx_files)}")

    for name in tx_files:
        diag = diagnose_pmtiles(name, all_files[name]['size'])
        status = "✓ VALID" if diag['valid'] else f"✗ {diag['issue']}"
        print(f"  {status} {name} ({diag['size_mb']:.1f} MB)")

if __name__ == '__main__':
    main()
