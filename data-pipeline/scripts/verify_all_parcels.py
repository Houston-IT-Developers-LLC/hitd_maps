#!/usr/bin/env python3
"""
Verify all parcel PMTiles files on R2 are valid and accessible.
Checks HTTP response, PMTiles magic number, and extracts metadata.
"""

import subprocess
import json
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from datetime import datetime

CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

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
                size = int(parts[2])
                parcels.append({'name': filename, 'size': size})
    return parcels

def verify_parcel(parcel):
    """Verify a single parcel file is valid"""
    name = parcel['name']
    url = f"{CDN}/parcels/{name}.pmtiles"

    result = {
        'name': name,
        'size_mb': round(parcel['size'] / (1024*1024), 2),
        'http_ok': False,
        'pmtiles_valid': False,
        'source_layer': None,
        'minzoom': None,
        'maxzoom': None,
        'error': None
    }

    try:
        # Check HTTP HEAD
        resp = requests.head(url, timeout=10)
        result['http_ok'] = resp.status_code == 200

        if not result['http_ok']:
            result['error'] = f"HTTP {resp.status_code}"
            return result

        # Download first 64KB to check PMTiles header
        resp = requests.get(url, headers={'Range': 'bytes=0-65535'}, timeout=15)

        # Write to temp file and check with pmtiles
        tmp_path = f"/tmp/verify_{name}.pmtiles"
        with open(tmp_path, 'wb') as f:
            f.write(resp.content)

        # Run pmtiles show
        proc = subprocess.run(['pmtiles', 'show', tmp_path], capture_output=True, text=True, timeout=10)
        output = proc.stdout + proc.stderr

        if 'pmtiles spec version' in output:
            result['pmtiles_valid'] = True

            # Extract minzoom
            for line in output.split('\n'):
                if 'min zoom:' in line:
                    result['minzoom'] = int(line.split(':')[1].strip())
                if 'max zoom:' in line:
                    result['maxzoom'] = int(line.split(':')[1].strip())

            # Extract source layer from generator_options
            if '--layer ' in output or '-l ' in output:
                result['source_layer'] = 'parcels'  # All use 'parcels' layer
            elif '"id":"' in output:
                import re
                match = re.search(r'"id":"([^"]+)"', output)
                if match:
                    result['source_layer'] = match.group(1)
        else:
            result['error'] = "Invalid PMTiles format"

        # Cleanup
        try:
            os.remove(tmp_path)
        except:
            pass

    except Exception as e:
        result['error'] = str(e)

    return result

def get_state_from_name(name):
    """Extract state code from parcel filename"""
    parts = name.replace('parcels_', '').split('_')
    if parts:
        state = parts[0].upper()
        if len(state) == 2:
            return state
    return None

def main():
    print(f"=== HITD Maps Parcel Verification ===")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get all parcels
    print("Fetching parcel list from R2...")
    parcels = get_all_parcels()
    print(f"Found {len(parcels)} parcel files")
    print()

    # Verify in parallel
    print("Verifying all parcels (this may take a few minutes)...")
    results = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(verify_parcel, p): p for p in parcels}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            results.append(result)
            status = "✓" if result['pmtiles_valid'] else "✗"
            print(f"[{completed}/{len(parcels)}] {status} {result['name']}", end='\r')

    print("\n")

    # Analyze results
    valid = [r for r in results if r['pmtiles_valid']]
    invalid = [r for r in results if not r['pmtiles_valid']]

    # Group by state
    states = {}
    for r in valid:
        state = get_state_from_name(r['name'])
        if state:
            if state not in states:
                states[state] = []
            states[state].append(r)

    # Print summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Total files:     {len(parcels)}")
    print(f"Valid PMTiles:   {len(valid)}")
    print(f"Invalid/Missing: {len(invalid)}")
    print(f"States covered:  {len(states)}")
    print()

    # List states with coverage
    all_states = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
                  'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
                  'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
                  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
                  'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']

    print("STATE COVERAGE:")
    print("-" * 60)
    covered = []
    missing = []
    for state in all_states:
        if state in states:
            count = len(states[state])
            files = [r['name'] for r in states[state]]
            covered.append(state)
            # Find best file (prefer statewide)
            best = next((f for f in files if 'statewide' in f), files[0])
            print(f"  {state}: {count} files (best: {best})")
        else:
            missing.append(state)

    print()
    print(f"Covered: {len(covered)}/50 states")
    if missing:
        print(f"Missing: {', '.join(missing)}")

    print()

    # Print invalid files
    if invalid:
        print("INVALID FILES:")
        print("-" * 60)
        for r in invalid:
            print(f"  {r['name']}: {r['error']}")

    # Generate JavaScript array for demo
    print()
    print("=" * 60)
    print("RECOMMENDED PARCEL LIST FOR demo/index.html:")
    print("=" * 60)

    # Pick best file per state (prefer statewide, then state-level, then largest county)
    best_per_state = {}
    for state, files in states.items():
        # Sort by preference
        statewide = [f for f in files if 'statewide' in f['name']]
        state_level = [f for f in files if f['name'] == f'parcels_{state.lower()}']
        counties = [f for f in files if f not in statewide and f not in state_level]
        counties.sort(key=lambda x: x['size_mb'], reverse=True)

        best = statewide + state_level + counties[:3]  # Top 3 counties
        best_per_state[state] = best

    # Generate JS array
    all_files = []
    for state in sorted(best_per_state.keys()):
        for f in best_per_state[state]:
            if f['name'] not in all_files:
                all_files.append(f['name'])

    print(f"\nvar PARCELS = [")
    for i, name in enumerate(all_files):
        comma = "," if i < len(all_files) - 1 else ""
        print(f"    '{name}'{comma}")
    print("];")

    # Save to file
    with open('/tmp/verified_parcels.json', 'w') as f:
        json.dump({
            'total': len(parcels),
            'valid': len(valid),
            'invalid': len(invalid),
            'states_covered': len(states),
            'results': results,
            'best_per_state': {k: [f['name'] for f in v] for k, v in best_per_state.items()},
            'recommended_list': all_files
        }, f, indent=2)

    print(f"\nFull results saved to /tmp/verified_parcels.json")

    return len(valid), len(invalid), len(states)

if __name__ == '__main__':
    main()
