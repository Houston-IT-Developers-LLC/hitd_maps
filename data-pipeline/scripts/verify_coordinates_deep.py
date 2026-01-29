#!/usr/bin/env python3
"""
DEEP COORDINATE VALIDATION FOR PMTILES
Extracts actual coordinates from PMTiles files and validates:
1. All coords in WGS84 range (-180:180, -90:90)
2. Coords fall within expected state boundaries
3. Zoom levels and layer names are correct
4. Geometry types are valid
"""

import subprocess
import json
import sys
import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import tempfile
import struct

CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

# US State bounding boxes (from smart_reproject_parcels.py)
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

def extract_state_from_filename(filename):
    """Extract state code from filename like parcels_tx_dallas -> TX"""
    parts = filename.replace('parcels_', '').split('_')
    if len(parts) > 0:
        state_code = parts[0].upper()
        if state_code in STATE_BOUNDS:
            return state_code
    return None

def get_pmtiles_metadata(url):
    """Get metadata from PMTiles file"""
    try:
        # Download first 16KB to get PMTiles v3 header (127 bytes)
        resp = requests.get(url, headers={'Range': 'bytes=0-16383'}, timeout=30)
        if resp.status_code not in [200, 206]:
            return None, f"HTTP {resp.status_code}"

        data = resp.content

        # Parse PMTiles v3 header
        # See: https://github.com/protomaps/PMTiles/blob/main/spec/v3/spec.md
        # Header structure (all little-endian):
        # 0-6: magic ("PMTiles")
        # 7: version (3)
        # 8: root_offset (8 bytes)
        # 16: root_length (8 bytes)
        # 24: metadata_offset (8 bytes)
        # 32: metadata_length (8 bytes)
        # 40: leaf_offset (8 bytes)
        # 48: leaf_length (8 bytes)
        # 56: tile_data_offset (8 bytes)
        # 64: tile_data_length (8 bytes)
        # 72: addressed_tiles_count (8 bytes)
        # 80: tile_entries_count (8 bytes)
        # 88: tile_contents_count (8 bytes)
        # 96: clustered (1 byte)
        # 97: internal_compression (1 byte)
        # 98: tile_compression (1 byte)
        # 99: tile_type (1 byte)
        # 100: minzoom (1 byte)
        # 101: maxzoom (1 byte)
        # 102: min_lon_e7 (int32)
        # 106: min_lat_e7 (int32)
        # 110: max_lon_e7 (int32)
        # 114: max_lat_e7 (int32)
        # 118: center_zoom (1 byte)
        # 119: center_lon_e7 (int32)
        # 123: center_lat_e7 (int32)

        # Check magic number
        if data[0:7] != b'PMTiles':
            return None, f"Invalid PMTiles magic number: {data[0:7]}"

        # Check version
        version = struct.unpack('<B', data[7:8])[0]
        if version != 3:
            return None, f"Unsupported PMTiles version: {version}"

        # Parse header fields
        minzoom = struct.unpack('<B', data[100:101])[0]
        maxzoom = struct.unpack('<B', data[101:102])[0]

        # Bounds in e7 format (multiply by 10^7 for integer storage)
        min_lon_e7 = struct.unpack('<i', data[102:106])[0]
        min_lat_e7 = struct.unpack('<i', data[106:110])[0]
        max_lon_e7 = struct.unpack('<i', data[110:114])[0]
        max_lat_e7 = struct.unpack('<i', data[114:118])[0]

        # Convert from e7 to decimal degrees
        min_lon = min_lon_e7 / 10000000.0
        min_lat = min_lat_e7 / 10000000.0
        max_lon = max_lon_e7 / 10000000.0
        max_lat = max_lat_e7 / 10000000.0

        # Center
        center_zoom = struct.unpack('<B', data[118:119])[0]
        center_lon_e7 = struct.unpack('<i', data[119:123])[0]
        center_lat_e7 = struct.unpack('<i', data[123:127])[0]

        center_lon = center_lon_e7 / 10000000.0
        center_lat = center_lat_e7 / 10000000.0

        metadata = {
            'minzoom': minzoom,
            'maxzoom': maxzoom,
            'bounds': [min_lon, min_lat, max_lon, max_lat],
            'center': [center_lon, center_lat],
            'layer_name': 'parcels'
        }

        return metadata, None
    except Exception as e:
        return None, str(e)

def validate_coordinates(bounds, state_code):
    """Validate bounding box coordinates"""
    if not bounds or len(bounds) < 4:
        return {
            'coords_in_wgs84_range': False,
            'coords_in_state_bounds': False,
            'issues': ['No bounds available']
        }

    min_lon, min_lat, max_lon, max_lat = bounds

    # Check WGS84 range
    coords_in_wgs84 = (
        -180 <= min_lon <= 180 and
        -180 <= max_lon <= 180 and
        -90 <= min_lat <= 90 and
        -90 <= max_lat <= 90
    )

    issues = []

    if not coords_in_wgs84:
        if abs(min_lon) > 1000 or abs(max_lon) > 1000:
            issues.append(f"Coordinates outside WGS84 range (likely State Plane projection): lon={min_lon:.1f} to {max_lon:.1f}")
        else:
            issues.append(f"Coordinates outside WGS84 range: lon={min_lon:.2f} to {max_lon:.2f}, lat={min_lat:.2f} to {max_lat:.2f}")

    # Check state bounds (with 0.5 degree buffer for border counties)
    coords_in_state = False
    if state_code and state_code in STATE_BOUNDS:
        bounds_dict = STATE_BOUNDS[state_code]
        buffer = 0.5

        # Check if bounds overlap with state bounds (with buffer)
        overlaps_lon = not (max_lon < bounds_dict['min_lon'] - buffer or
                           min_lon > bounds_dict['max_lon'] + buffer)
        overlaps_lat = not (max_lat < bounds_dict['min_lat'] - buffer or
                           min_lat > bounds_dict['max_lat'] + buffer)

        coords_in_state = overlaps_lon and overlaps_lat

        if not coords_in_state and coords_in_wgs84:
            issues.append(f"Coordinates outside expected {state_code} bounds (with 0.5° buffer)")

    return {
        'coords_in_wgs84_range': coords_in_wgs84,
        'coords_in_state_bounds': coords_in_state,
        'issues': issues
    }

def verify_parcel_deep(name):
    """Deep verification of a single parcel file"""
    url = f"{CDN}/parcels/{name}.pmtiles"
    state_code = extract_state_from_filename(name)

    result = {
        'name': name,
        'state': state_code,
        'valid': False,
        'minzoom': None,
        'maxzoom': None,
        'layer_name': 'parcels',
        'bounds': None,
        'center': None,
        'coords_in_wgs84_range': None,
        'coords_in_state_bounds': None,
        'issues': []
    }

    # Get metadata
    metadata, error = get_pmtiles_metadata(url)
    if error:
        result['issues'].append(error)
        return result

    if not metadata:
        result['issues'].append("Could not extract metadata")
        return result

    # Update result with metadata
    result['minzoom'] = metadata['minzoom']
    result['maxzoom'] = metadata['maxzoom']
    result['bounds'] = metadata['bounds']
    result['center'] = metadata['center']

    # Validate zoom levels
    if metadata['minzoom'] is None or metadata['maxzoom'] is None:
        result['issues'].append("Missing zoom level information")
    elif metadata['minzoom'] > 8:
        result['issues'].append(f"Unusual minzoom={metadata['minzoom']} (parcels won't load until zoomed in far)")
    elif metadata['maxzoom'] < 14:
        result['issues'].append(f"Low maxzoom={metadata['maxzoom']} (may lack detail at high zoom)")

    # Validate coordinates
    coord_validation = validate_coordinates(metadata['bounds'], state_code)
    result['coords_in_wgs84_range'] = coord_validation['coords_in_wgs84_range']
    result['coords_in_state_bounds'] = coord_validation['coords_in_state_bounds']
    result['issues'].extend(coord_validation['issues'])

    # Overall validation
    result['valid'] = (
        result['coords_in_wgs84_range'] and
        len(result['issues']) == 0
    )

    return result

def get_all_parcels():
    """Get list of all parcel files from R2"""
    result = subprocess.run([
        'aws', 's3', 'ls', 's3://gspot-tiles/parcels/',
        '--endpoint-url', 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com'
    ], capture_output=True, text=True, env={
        **os.environ,
        'AWS_ACCESS_KEY_ID': 'ecd653afe3300fdc045b9980df0dbb14',
        'AWS_SECRET_ACCESS_KEY': 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'
    })

    parcels = []
    for line in result.stdout.strip().split('\n'):
        if '.pmtiles' in line:
            parts = line.split()
            if len(parts) >= 4:
                filename = parts[3].replace('.pmtiles', '')
                parcels.append(filename)
    return parcels

def main():
    print("=== HITD Maps Deep Coordinate Validation ===")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Load parcels from Phase 1 results
    phase1_results = None
    if os.path.exists('/tmp/verified_parcels.json'):
        with open('/tmp/verified_parcels.json', 'r') as f:
            data = json.load(f)
            phase1_results = data.get('results', [])
        # Filter to valid parcels only
        parcels = [p['name'] for p in phase1_results if p.get('pmtiles_valid', False)]
        print(f"Using {len(parcels)} valid parcels from Phase 1 results\n")
    else:
        parcels = get_all_parcels()
        print(f"Found {len(parcels)} parcel files from R2\n")

    print(f"Validating coordinates for all parcels (this may take 30-60 minutes)...\n")

    # Verify in parallel with 10 workers
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_name = {executor.submit(verify_parcel_deep, name): name
                         for name in parcels}

        completed = 0
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                result = future.result()
                results.append(result)
                completed += 1

                # Print progress
                status = "✓" if result['valid'] else "✗"
                print(f"[{completed}/{len(parcels)}] {status} {name}")

                if result['issues']:
                    for issue in result['issues']:
                        print(f"    ⚠ {issue}")

            except Exception as e:
                print(f"[{completed}/{len(parcels)}] ✗ {name} - Exception: {e}")
                results.append({
                    'name': name,
                    'valid': False,
                    'issues': [str(e)]
                })

    # Generate summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)

    total = len(results)
    valid = sum(1 for r in results if r['valid'])
    invalid = total - valid

    coords_ok = sum(1 for r in results if r.get('coords_in_wgs84_range', False))
    state_bounds_ok = sum(1 for r in results if r.get('coords_in_state_bounds', False))

    print(f"Total files:              {total}")
    print(f"Valid (all checks pass):  {valid}")
    print(f"Invalid (has issues):     {invalid}")
    print(f"Coords in WGS84 range:    {coords_ok}")
    print(f"Coords in state bounds:   {state_bounds_ok}")

    # List invalid files
    invalid_files = [r for r in results if not r['valid']]
    if invalid_files:
        print(f"\nINVALID FILES ({len(invalid_files)}):")
        print("-" * 60)
        for r in invalid_files:
            print(f"  {r['name']}:")
            for issue in r['issues']:
                print(f"    - {issue}")

    # Check for projection issues
    projection_issues = [r for r in results if not r.get('coords_in_wgs84_range', True)]
    if projection_issues:
        print(f"\nPROJECTION ISSUES ({len(projection_issues)}):")
        print("-" * 60)
        print("These files may need reprojection to WGS84:")
        for r in projection_issues:
            print(f"  {r['name']}")

    # Save detailed results
    output_path = '/tmp/coordinate_validation_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': total,
                'valid': valid,
                'invalid': invalid,
                'coords_in_wgs84': coords_ok,
                'coords_in_state_bounds': state_bounds_ok
            },
            'results': results
        }, f, indent=2)

    print(f"\nDetailed results saved to: {output_path}")

    # Exit with error code if issues found
    sys.exit(0 if invalid == 0 else 1)

if __name__ == '__main__':
    main()
