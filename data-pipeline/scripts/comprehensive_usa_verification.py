#!/usr/bin/env python3
"""
COMPREHENSIVE USA PARCEL VERIFICATION SYSTEM
Deploys parallel agents to verify all PMTiles files across all 50 states.
Validates coordinates, tile data, and coverage for complete USA map support.
Also builds proprietary data moats (metadata, statistics, quality scores).
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
import hashlib
from collections import defaultdict

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

NUM_WORKERS = min(50, multiprocessing.cpu_count() * 4)

# US State bounding boxes for validation
STATE_BOUNDS = {
    'AL': {'min_lat': 30.1, 'max_lat': 35.0, 'min_lon': -88.5, 'max_lon': -84.9, 'name': 'Alabama'},
    'AK': {'min_lat': 51.0, 'max_lat': 71.5, 'min_lon': -180.0, 'max_lon': -130.0, 'name': 'Alaska'},
    'AZ': {'min_lat': 31.3, 'max_lat': 37.0, 'min_lon': -114.8, 'max_lon': -109.0, 'name': 'Arizona'},
    'AR': {'min_lat': 33.0, 'max_lat': 36.5, 'min_lon': -94.6, 'max_lon': -89.6, 'name': 'Arkansas'},
    'CA': {'min_lat': 32.5, 'max_lat': 42.0, 'min_lon': -124.5, 'max_lon': -114.1, 'name': 'California'},
    'CO': {'min_lat': 36.9, 'max_lat': 41.0, 'min_lon': -109.1, 'max_lon': -102.0, 'name': 'Colorado'},
    'CT': {'min_lat': 40.9, 'max_lat': 42.1, 'min_lon': -73.7, 'max_lon': -71.8, 'name': 'Connecticut'},
    'DE': {'min_lat': 38.4, 'max_lat': 39.8, 'min_lon': -75.8, 'max_lon': -75.0, 'name': 'Delaware'},
    'FL': {'min_lat': 24.5, 'max_lat': 31.0, 'min_lon': -87.6, 'max_lon': -80.0, 'name': 'Florida'},
    'GA': {'min_lat': 30.4, 'max_lat': 35.0, 'min_lon': -85.6, 'max_lon': -80.8, 'name': 'Georgia'},
    'HI': {'min_lat': 18.9, 'max_lat': 22.2, 'min_lon': -160.3, 'max_lon': -154.8, 'name': 'Hawaii'},
    'ID': {'min_lat': 42.0, 'max_lat': 49.0, 'min_lon': -117.2, 'max_lon': -111.0, 'name': 'Idaho'},
    'IL': {'min_lat': 36.9, 'max_lat': 42.5, 'min_lon': -91.5, 'max_lon': -87.0, 'name': 'Illinois'},
    'IN': {'min_lat': 37.8, 'max_lat': 41.8, 'min_lon': -88.1, 'max_lon': -84.8, 'name': 'Indiana'},
    'IA': {'min_lat': 40.4, 'max_lat': 43.5, 'min_lon': -96.6, 'max_lon': -90.1, 'name': 'Iowa'},
    'KS': {'min_lat': 36.9, 'max_lat': 40.0, 'min_lon': -102.1, 'max_lon': -94.6, 'name': 'Kansas'},
    'KY': {'min_lat': 36.5, 'max_lat': 39.1, 'min_lon': -89.6, 'max_lon': -81.9, 'name': 'Kentucky'},
    'LA': {'min_lat': 28.9, 'max_lat': 33.0, 'min_lon': -94.0, 'max_lon': -89.0, 'name': 'Louisiana'},
    'ME': {'min_lat': 43.0, 'max_lat': 47.5, 'min_lon': -71.1, 'max_lon': -66.9, 'name': 'Maine'},
    'MD': {'min_lat': 37.9, 'max_lat': 39.7, 'min_lon': -79.5, 'max_lon': -75.0, 'name': 'Maryland'},
    'MA': {'min_lat': 41.2, 'max_lat': 42.9, 'min_lon': -73.5, 'max_lon': -69.9, 'name': 'Massachusetts'},
    'MI': {'min_lat': 41.7, 'max_lat': 48.2, 'min_lon': -90.4, 'max_lon': -82.4, 'name': 'Michigan'},
    'MN': {'min_lat': 43.5, 'max_lat': 49.4, 'min_lon': -97.2, 'max_lon': -89.5, 'name': 'Minnesota'},
    'MS': {'min_lat': 30.2, 'max_lat': 35.0, 'min_lon': -91.7, 'max_lon': -88.1, 'name': 'Mississippi'},
    'MO': {'min_lat': 35.9, 'max_lat': 40.6, 'min_lon': -95.8, 'max_lon': -89.1, 'name': 'Missouri'},
    'MT': {'min_lat': 44.4, 'max_lat': 49.0, 'min_lon': -116.0, 'max_lon': -104.0, 'name': 'Montana'},
    'NE': {'min_lat': 40.0, 'max_lat': 43.0, 'min_lon': -104.1, 'max_lon': -95.3, 'name': 'Nebraska'},
    'NV': {'min_lat': 35.0, 'max_lat': 42.0, 'min_lon': -120.0, 'max_lon': -114.0, 'name': 'Nevada'},
    'NH': {'min_lat': 42.7, 'max_lat': 45.3, 'min_lon': -72.6, 'max_lon': -70.7, 'name': 'New Hampshire'},
    'NJ': {'min_lat': 38.9, 'max_lat': 41.4, 'min_lon': -75.6, 'max_lon': -73.9, 'name': 'New Jersey'},
    'NM': {'min_lat': 31.3, 'max_lat': 37.0, 'min_lon': -109.1, 'max_lon': -103.0, 'name': 'New Mexico'},
    'NY': {'min_lat': 40.5, 'max_lat': 45.0, 'min_lon': -79.8, 'max_lon': -71.9, 'name': 'New York'},
    'NC': {'min_lat': 33.8, 'max_lat': 36.6, 'min_lon': -84.3, 'max_lon': -75.5, 'name': 'North Carolina'},
    'ND': {'min_lat': 45.9, 'max_lat': 49.0, 'min_lon': -104.1, 'max_lon': -96.6, 'name': 'North Dakota'},
    'OH': {'min_lat': 38.4, 'max_lat': 42.0, 'min_lon': -84.8, 'max_lon': -80.5, 'name': 'Ohio'},
    'OK': {'min_lat': 33.6, 'max_lat': 37.0, 'min_lon': -103.0, 'max_lon': -94.4, 'name': 'Oklahoma'},
    'OR': {'min_lat': 41.9, 'max_lat': 46.3, 'min_lon': -124.6, 'max_lon': -116.5, 'name': 'Oregon'},
    'PA': {'min_lat': 39.7, 'max_lat': 42.3, 'min_lon': -80.5, 'max_lon': -74.7, 'name': 'Pennsylvania'},
    'RI': {'min_lat': 41.1, 'max_lat': 42.0, 'min_lon': -71.9, 'max_lon': -71.1, 'name': 'Rhode Island'},
    'SC': {'min_lat': 32.0, 'max_lat': 35.2, 'min_lon': -83.4, 'max_lon': -78.5, 'name': 'South Carolina'},
    'SD': {'min_lat': 42.5, 'max_lat': 45.9, 'min_lon': -104.1, 'max_lon': -96.4, 'name': 'South Dakota'},
    'TN': {'min_lat': 35.0, 'max_lat': 36.7, 'min_lon': -90.3, 'max_lon': -81.6, 'name': 'Tennessee'},
    'TX': {'min_lat': 25.8, 'max_lat': 36.5, 'min_lon': -106.6, 'max_lon': -93.5, 'name': 'Texas'},
    'UT': {'min_lat': 37.0, 'max_lat': 42.0, 'min_lon': -114.1, 'max_lon': -109.0, 'name': 'Utah'},
    'VT': {'min_lat': 42.7, 'max_lat': 45.0, 'min_lon': -73.4, 'max_lon': -71.5, 'name': 'Vermont'},
    'VA': {'min_lat': 36.5, 'max_lat': 39.5, 'min_lon': -83.7, 'max_lon': -75.2, 'name': 'Virginia'},
    'WA': {'min_lat': 45.5, 'max_lat': 49.0, 'min_lon': -124.8, 'max_lon': -116.9, 'name': 'Washington'},
    'WV': {'min_lat': 37.2, 'max_lat': 40.6, 'min_lon': -82.6, 'max_lon': -77.7, 'name': 'West Virginia'},
    'WI': {'min_lat': 42.5, 'max_lat': 47.1, 'min_lon': -92.9, 'max_lon': -86.8, 'name': 'Wisconsin'},
    'WY': {'min_lat': 40.9, 'max_lat': 45.0, 'min_lon': -111.1, 'max_lon': -104.1, 'name': 'Wyoming'},
    'DC': {'min_lat': 38.8, 'max_lat': 39.0, 'min_lon': -77.1, 'max_lon': -76.9, 'name': 'District of Columbia'},
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

def get_all_pmtiles():
    """Get list of all PMTiles files from R2"""
    result = run_aws(['ls', f's3://{R2_BUCKET}/parcels/', '--recursive'])
    files = []
    for line in result.stdout.strip().split('\n'):
        if '.pmtiles' in line and 'parcels/' in line:
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3]
                name = path.split('/')[-1].replace('.pmtiles', '')
                size = int(parts[2])
                files.append({'name': name, 'size': size})
    return files

def get_state_from_name(name):
    """Extract state code from filename"""
    parts = name.replace('parcels_', '').split('_')
    if parts:
        state = parts[0].upper()
        if len(state) == 2 and state in STATE_BOUNDS:
            return state
    return None

def get_county_from_name(name):
    """Extract county name from filename"""
    parts = name.replace('parcels_', '').split('_')
    if len(parts) > 1:
        # Remove state code and version suffix
        county_parts = parts[1:]
        county_parts = [p for p in county_parts if not p.startswith('v') and not p == 'statewide']
        if county_parts:
            return '_'.join(county_parts)
    return None

def verify_pmtiles(file_info):
    """Comprehensive verification of a single PMTiles file"""
    name = file_info['name']
    size = file_info['size']
    url = f"{CDN}/parcels/{name}.pmtiles"

    result = {
        'name': name,
        'state': get_state_from_name(name),
        'county': get_county_from_name(name),
        'size_bytes': size,
        'size_mb': round(size / (1024*1024), 2),
        'valid': False,
        'has_tiles': False,
        'minzoom': None,
        'maxzoom': None,
        'tile_count': 0,
        'bounds': None,
        'center_lon': None,
        'center_lat': None,
        'coords_valid': False,
        'quality_score': 0,
        'issue': None,
        'verified_at': datetime.now().isoformat(),
        'content_hash': None
    }

    try:
        # Download header (first 64KB should contain metadata)
        resp = requests.get(url, headers={'Range': 'bytes=0-65535'}, timeout=30)

        if resp.status_code == 404:
            result['issue'] = 'FILE_NOT_FOUND'
            return result

        content = resp.content
        result['content_hash'] = hashlib.md5(content[:1024]).hexdigest()[:16]

        if len(content) < 2:
            result['issue'] = 'FILE_EMPTY'
            return result

        if content[0:2] != b'PM':
            result['issue'] = 'NOT_PMTILES'
            return result

        # Write to temp and analyze with pmtiles CLI
        tmp_path = f"/tmp/verify_{name}_{os.getpid()}.pmtiles"
        try:
            with open(tmp_path, 'wb') as f:
                f.write(content)

            proc = subprocess.run(['pmtiles', 'show', tmp_path],
                                capture_output=True, text=True, timeout=10)
            output = proc.stdout + proc.stderr

            if 'pmtiles spec version' not in output:
                result['issue'] = 'CORRUPT_HEADER'
                return result

            result['valid'] = True

            # Parse metadata
            for line in output.split('\n'):
                line_lower = line.lower()
                if 'min zoom:' in line_lower:
                    try:
                        result['minzoom'] = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'max zoom:' in line_lower:
                    try:
                        result['maxzoom'] = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'tile entries:' in line_lower:
                    try:
                        result['tile_count'] = int(line.split(':')[1].strip())
                        result['has_tiles'] = result['tile_count'] > 0
                    except:
                        pass
                elif 'bounds:' in line_lower and 'min' not in line_lower and 'max' not in line_lower:
                    try:
                        bounds_str = line.split(':')[1].strip()
                        bounds = [float(x.strip()) for x in bounds_str.split(',')]
                        if len(bounds) == 4:
                            result['bounds'] = bounds
                            result['center_lon'] = (bounds[0] + bounds[2]) / 2
                            result['center_lat'] = (bounds[1] + bounds[3]) / 2
                    except:
                        pass
                elif 'center:' in line_lower:
                    try:
                        center_str = line.split(':')[1].strip()
                        parts = center_str.split(',')
                        if len(parts) >= 2:
                            result['center_lon'] = float(parts[0].strip())
                            result['center_lat'] = float(parts[1].strip())
                    except:
                        pass

            # Validate coordinates against state bounds
            if result['center_lon'] and result['center_lat'] and result['state']:
                state = result['state']
                if state in STATE_BOUNDS:
                    bounds = STATE_BOUNDS[state]
                    tolerance = 5.0  # degrees
                    lon_ok = bounds['min_lon'] - tolerance <= result['center_lon'] <= bounds['max_lon'] + tolerance
                    lat_ok = bounds['min_lat'] - tolerance <= result['center_lat'] <= bounds['max_lat'] + tolerance
                    result['coords_valid'] = lon_ok and lat_ok

                    if not result['coords_valid']:
                        result['issue'] = f"COORDS_OUTSIDE_STATE (expected {state})"

            # Check for issues
            if not result['has_tiles']:
                result['issue'] = 'NO_TILE_DATA'
                result['valid'] = False
            elif size < 50000:
                result['issue'] = 'FILE_TOO_SMALL'
                result['valid'] = False

            # Calculate quality score (0-100)
            if result['valid'] and result['has_tiles']:
                score = 0
                # Size score (larger = more data = better)
                if size > 1000000:
                    score += 25
                elif size > 100000:
                    score += 15
                else:
                    score += 5

                # Tile count score
                if result['tile_count'] > 100000:
                    score += 25
                elif result['tile_count'] > 10000:
                    score += 20
                elif result['tile_count'] > 1000:
                    score += 15
                else:
                    score += 5

                # Zoom range score
                zoom_range = (result['maxzoom'] or 0) - (result['minzoom'] or 0)
                if zoom_range >= 10:
                    score += 25
                elif zoom_range >= 5:
                    score += 15
                else:
                    score += 5

                # Coordinates validation score
                if result['coords_valid']:
                    score += 25
                elif result['center_lon'] and result['center_lat']:
                    score += 10

                result['quality_score'] = min(100, score)

        finally:
            try:
                os.remove(tmp_path)
            except:
                pass

    except requests.exceptions.Timeout:
        result['issue'] = 'TIMEOUT'
    except Exception as e:
        result['issue'] = f'ERROR: {str(e)[:50]}'

    return result

def main():
    start_time = datetime.now()
    print("=" * 80)
    print("COMPREHENSIVE USA PARCEL VERIFICATION SYSTEM")
    print("Deploying parallel verification agents across all 50 states")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Parallel Workers: {NUM_WORKERS}")
    print("=" * 80)

    # Phase 1: Get all files
    print("\n" + "=" * 80)
    print("PHASE 1: INVENTORYING ALL PARCEL FILES")
    print("=" * 80 + "\n")

    all_files = get_all_pmtiles()
    print(f"Found {len(all_files)} PMTiles files on R2")

    total_size = sum(f['size'] for f in all_files)
    print(f"Total size: {total_size / (1024*1024*1024):.2f} GB")

    # Phase 2: Parallel verification
    print("\n" + "=" * 80)
    print(f"PHASE 2: PARALLEL VERIFICATION WITH {NUM_WORKERS} AGENTS")
    print("=" * 80 + "\n")

    results = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(verify_pmtiles, f): f for f in all_files}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            results.append(result)

            status = "✓" if result['valid'] and result['coords_valid'] else "⚠" if result['valid'] else "✗"
            coords = f"({result['center_lon']:.2f}, {result['center_lat']:.2f})" if result['center_lon'] else "(?)"
            print(f"[{completed}/{len(all_files)}] {status} {result['name']}: {result['issue'] or 'OK'} {coords}")

    # Phase 3: Analysis & Data Moat Generation
    print("\n" + "=" * 80)
    print("PHASE 3: GENERATING PROPRIETARY DATA MOATS")
    print("=" * 80 + "\n")

    # Group by state
    by_state = defaultdict(list)
    for r in results:
        state = r['state'] or 'UNKNOWN'
        by_state[state].append(r)

    # Count valid/invalid
    valid = [r for r in results if r['valid'] and r['coords_valid']]
    invalid = [r for r in results if not r['valid'] or not r['coords_valid']]

    # Calculate state coverage
    states_with_valid = set()
    for r in valid:
        if r['state']:
            states_with_valid.add(r['state'])

    missing_states = set(STATE_BOUNDS.keys()) - states_with_valid

    # Build proprietary data moat
    data_moat = {
        'generated_at': datetime.now().isoformat(),
        'verification_id': hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:12],
        'summary': {
            'total_files': len(results),
            'valid_files': len(valid),
            'invalid_files': len(invalid),
            'total_size_gb': round(total_size / (1024*1024*1024), 2),
            'states_with_coverage': len(states_with_valid),
            'states_without_coverage': list(missing_states),
            'average_quality_score': round(sum(r['quality_score'] for r in valid) / len(valid), 1) if valid else 0,
        },
        'by_state': {},
        'quality_rankings': [],
        'coverage_gaps': [],
        'proprietary_metrics': {
            'total_tile_count': sum(r['tile_count'] for r in valid),
            'unique_counties_covered': len(set(r['county'] for r in valid if r['county'])),
            'highest_quality_files': [],
            'data_freshness': datetime.now().isoformat(),
            'verification_completeness': round(len(valid) / len(results) * 100, 1) if results else 0,
        }
    }

    # State-by-state analysis
    for state in sorted(STATE_BOUNDS.keys()):
        state_files = by_state.get(state, [])
        valid_state = [f for f in state_files if f['valid'] and f['coords_valid']]

        data_moat['by_state'][state] = {
            'name': STATE_BOUNDS[state]['name'],
            'total_files': len(state_files),
            'valid_files': len(valid_state),
            'total_size_mb': round(sum(f['size_bytes'] for f in valid_state) / (1024*1024), 2),
            'counties_covered': len(set(f['county'] for f in valid_state if f['county'])),
            'average_quality': round(sum(f['quality_score'] for f in valid_state) / len(valid_state), 1) if valid_state else 0,
            'has_statewide': any('statewide' in f['name'] for f in valid_state),
            'files': [f['name'] for f in valid_state]
        }

        # Identify coverage gaps
        if not valid_state:
            data_moat['coverage_gaps'].append({
                'state': state,
                'state_name': STATE_BOUNDS[state]['name'],
                'reason': 'NO_VALID_FILES',
                'available_files': [f['name'] for f in state_files],
                'issues': [f['issue'] for f in state_files if f['issue']]
            })

    # Quality rankings
    data_moat['quality_rankings'] = sorted(
        [{'name': r['name'], 'state': r['state'], 'score': r['quality_score'], 'size_mb': r['size_mb']}
         for r in valid],
        key=lambda x: x['score'],
        reverse=True
    )[:50]

    # Highest quality files
    data_moat['proprietary_metrics']['highest_quality_files'] = [
        r['name'] for r in sorted(valid, key=lambda x: x['quality_score'], reverse=True)[:20]
    ]

    # Summary output
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    elapsed = datetime.now() - start_time
    print(f"\nTime elapsed: {elapsed}")
    print(f"Total files checked: {len(results)}")
    print(f"Valid files: {len(valid)}")
    print(f"Invalid files: {len(invalid)}")
    print(f"States with coverage: {len(states_with_valid)}/{len(STATE_BOUNDS)}")

    if missing_states:
        print(f"\nStates without valid coverage:")
        for state in sorted(missing_states):
            print(f"  - {state}: {STATE_BOUNDS[state]['name']}")

    print(f"\nTop 10 highest quality files:")
    for r in data_moat['quality_rankings'][:10]:
        print(f"  {r['score']}/100 - {r['name']} ({r['state']}, {r['size_mb']} MB)")

    if invalid:
        print(f"\nInvalid/problematic files ({len(invalid)}):")
        for r in invalid[:20]:
            print(f"  ✗ {r['name']}: {r['issue']}")
        if len(invalid) > 20:
            print(f"  ... and {len(invalid) - 20} more")

    # Save results
    output_dir = '/home/exx/Documents/C/hitd_maps/data-pipeline/data'
    os.makedirs(output_dir, exist_ok=True)

    # Full verification results
    with open(f'{output_dir}/verification_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Proprietary data moat
    with open(f'{output_dir}/data_moat.json', 'w') as f:
        json.dump(data_moat, f, indent=2)

    # Valid files list (for use in frontend)
    valid_files_list = sorted([r['name'] for r in valid])
    with open(f'{output_dir}/valid_parcels.json', 'w') as f:
        json.dump(valid_files_list, f, indent=2)

    # State coverage summary
    state_coverage = {
        state: data_moat['by_state'][state]
        for state in sorted(data_moat['by_state'].keys())
    }
    with open(f'{output_dir}/state_coverage.json', 'w') as f:
        json.dump(state_coverage, f, indent=2)

    print(f"\n" + "=" * 80)
    print("OUTPUT FILES GENERATED")
    print("=" * 80)
    print(f"  {output_dir}/verification_results.json - Full verification data")
    print(f"  {output_dir}/data_moat.json - Proprietary analytics")
    print(f"  {output_dir}/valid_parcels.json - Valid file list for frontend")
    print(f"  {output_dir}/state_coverage.json - State-by-state coverage")

    print(f"\n" + "=" * 80)
    print("PROPRIETARY DATA MOAT SUMMARY")
    print("=" * 80)
    print(f"  Total tile count: {data_moat['proprietary_metrics']['total_tile_count']:,}")
    print(f"  Unique counties: {data_moat['proprietary_metrics']['unique_counties_covered']}")
    print(f"  Verification completeness: {data_moat['proprietary_metrics']['verification_completeness']}%")
    print(f"  Average quality score: {data_moat['summary']['average_quality_score']}/100")

    return data_moat

if __name__ == '__main__':
    main()
