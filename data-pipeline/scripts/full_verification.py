#!/usr/bin/env python3
"""
FULL USA PARCEL VERIFICATION
Downloads and verifies each PMTiles file completely.
"""

import subprocess
import os
import json
import requests
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import multiprocessing
from collections import defaultdict

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

NUM_WORKERS = min(20, multiprocessing.cpu_count() * 2)

# US State bounding boxes
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

def verify_pmtiles(file_info):
    """Download and verify PMTiles file"""
    name = file_info['name']
    size = file_info['size']
    url = f"{CDN}/parcels/{name}.pmtiles"
    tmp_path = f"/tmp/verify_{name}_{os.getpid()}.pmtiles"

    result = {
        'name': name,
        'state': get_state_from_name(name),
        'size_bytes': size,
        'size_mb': round(size / (1024*1024), 2),
        'valid': False,
        'has_tiles': False,
        'tile_count': 0,
        'minzoom': None,
        'maxzoom': None,
        'bounds': None,
        'center_lon': None,
        'center_lat': None,
        'coords_valid': False,
        'issue': None,
    }

    try:
        # Download full file
        resp = requests.get(url, timeout=300)
        if resp.status_code == 404:
            result['issue'] = 'FILE_NOT_FOUND'
            return result

        with open(tmp_path, 'wb') as f:
            f.write(resp.content)

        # Verify with pmtiles CLI
        proc = subprocess.run(['pmtiles', 'show', tmp_path],
                            capture_output=True, text=True, timeout=30)
        output = proc.stdout + proc.stderr

        if 'pmtiles spec version' not in output:
            result['issue'] = 'INVALID_PMTILES'
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
            elif 'tile entries count:' in line_lower:
                try:
                    result['tile_count'] = int(line.split(':')[1].strip())
                    result['has_tiles'] = result['tile_count'] > 0
                except:
                    pass
            elif 'bounds:' in line_lower and 'min' not in line_lower and 'max' not in line_lower:
                try:
                    # Parse bounds like: bounds: (long: -97.037618, lat: 32.580578) (long: -96.438039, lat: 33.044991)
                    import re
                    coords = re.findall(r'[-\d.]+', line)
                    if len(coords) >= 4:
                        result['bounds'] = [float(c) for c in coords[:4]]
                        result['center_lon'] = (result['bounds'][0] + result['bounds'][2]) / 2
                        result['center_lat'] = (result['bounds'][1] + result['bounds'][3]) / 2
                except:
                    pass
            elif 'center:' in line_lower and 'zoom' not in line_lower:
                try:
                    import re
                    coords = re.findall(r'[-\d.]+', line)
                    if len(coords) >= 2:
                        result['center_lon'] = float(coords[0])
                        result['center_lat'] = float(coords[1])
                except:
                    pass

        # Validate coordinates
        if result['center_lon'] and result['center_lat'] and result['state']:
            state = result['state']
            if state in STATE_BOUNDS:
                bounds = STATE_BOUNDS[state]
                tolerance = 5.0
                lon_ok = bounds['min_lon'] - tolerance <= result['center_lon'] <= bounds['max_lon'] + tolerance
                lat_ok = bounds['min_lat'] - tolerance <= result['center_lat'] <= bounds['max_lat'] + tolerance
                result['coords_valid'] = lon_ok and lat_ok

        # Check for issues
        if not result['has_tiles']:
            result['issue'] = 'NO_TILE_DATA'
            result['valid'] = False
        elif size < 5000:
            result['issue'] = 'FILE_TOO_SMALL'
            result['valid'] = False
        elif not result['coords_valid'] and result['center_lon']:
            result['issue'] = f'WRONG_COORDS ({result["center_lon"]:.2f}, {result["center_lat"]:.2f})'

    except requests.exceptions.Timeout:
        result['issue'] = 'TIMEOUT'
    except Exception as e:
        result['issue'] = f'ERROR: {str(e)[:50]}'
    finally:
        try:
            os.remove(tmp_path)
        except:
            pass

    return result

def main():
    start_time = datetime.now()
    print("=" * 80)
    print("FULL USA PARCEL VERIFICATION")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Workers: {NUM_WORKERS}")
    print("=" * 80)

    # Get all files
    print("\nFetching file list from R2...")
    all_files = get_all_pmtiles()
    print(f"Found {len(all_files)} PMTiles files")

    # Verify files
    print("\n" + "=" * 80)
    print(f"VERIFYING {len(all_files)} FILES")
    print("=" * 80 + "\n")

    results = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(verify_pmtiles, f): f for f in all_files}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            results.append(result)

            if result['valid'] and result['has_tiles']:
                coords = f"({result['center_lon']:.2f}, {result['center_lat']:.2f})" if result['center_lon'] else ""
                tiles = f"{result['tile_count']} tiles"
                status = "✓" if result['coords_valid'] else "⚠"
                print(f"[{completed}/{len(all_files)}] {status} {result['name']}: {tiles} {coords}")
            else:
                print(f"[{completed}/{len(all_files)}] ✗ {result['name']}: {result['issue']}")

    # Summary
    elapsed = datetime.now() - start_time
    valid = [r for r in results if r['valid'] and r['has_tiles']]
    valid_coords = [r for r in valid if r['coords_valid']]
    invalid = [r for r in results if not r['valid'] or not r['has_tiles']]

    # Group by state
    by_state = defaultdict(list)
    for r in valid_coords:
        if r['state']:
            by_state[r['state']].append(r)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTime elapsed: {elapsed}")
    print(f"Total files: {len(results)}")
    print(f"Valid with tiles: {len(valid)}")
    print(f"Valid with correct coords: {len(valid_coords)}")
    print(f"Invalid/empty: {len(invalid)}")
    print(f"States covered: {len(by_state)}/51")

    print("\n" + "=" * 80)
    print("COVERAGE BY STATE")
    print("=" * 80)
    for state in sorted(STATE_BOUNDS.keys()):
        files = by_state.get(state, [])
        if files:
            total_tiles = sum(f['tile_count'] for f in files)
            print(f"  {state} ({STATE_BOUNDS[state]['name']}): {len(files)} files, {total_tiles:,} tiles")
        else:
            print(f"  {state} ({STATE_BOUNDS[state]['name']}): NO COVERAGE")

    # Save results
    output_dir = '/home/exx/Documents/C/hitd_maps/data-pipeline/data'
    os.makedirs(output_dir, exist_ok=True)

    # Valid files list
    valid_list = sorted([r['name'] for r in valid_coords])
    with open(f'{output_dir}/valid_parcels.json', 'w') as f:
        json.dump(valid_list, f, indent=2)

    # Full results
    with open(f'{output_dir}/verification_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Data moat
    data_moat = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_files': len(results),
            'valid_files': len(valid_coords),
            'invalid_files': len(invalid),
            'states_covered': len(by_state),
            'total_tiles': sum(r['tile_count'] for r in valid_coords),
        },
        'by_state': {
            state: {
                'name': STATE_BOUNDS[state]['name'],
                'files': len(files),
                'tiles': sum(f['tile_count'] for f in files),
                'file_names': [f['name'] for f in files]
            }
            for state, files in by_state.items()
        },
        'valid_files': valid_list,
    }

    with open(f'{output_dir}/data_moat.json', 'w') as f:
        json.dump(data_moat, f, indent=2)

    print(f"\n✓ Results saved to {output_dir}/")
    print(f"  - valid_parcels.json: {len(valid_list)} valid files")
    print(f"  - verification_results.json: Full results")
    print(f"  - data_moat.json: Coverage analytics")

    return valid_list

if __name__ == '__main__':
    main()
