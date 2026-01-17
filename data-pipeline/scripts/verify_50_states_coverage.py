#!/usr/bin/env python3
"""
Verify complete coverage of all 50 US states on R2.
Checks for missing states and reports data quality.
"""

import boto3
from botocore.config import Config
from datetime import datetime
import sys

sys.stdout.reconfigure(line_buffering=True)

R2_ENDPOINT = 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com'
R2_ACCESS_KEY = 'ecd653afe3300fdc045b9980df0dbb14'
R2_SECRET_KEY = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'
R2_BUCKET = 'gspot-tiles'

# All 50 US states
ALL_STATES = {
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming',
}


def get_r2_client():
    return boto3.client('s3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version='s3v4'))


def list_all_pmtiles():
    """List all PMTiles files in R2."""
    client = get_r2_client()
    paginator = client.get_paginator('list_objects_v2')

    files = []
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix='parcels/'):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('.pmtiles') and 'parcels_' in key:
                filename = key.split('/')[-1]
                files.append({
                    'key': key,
                    'filename': filename,
                    'size': obj['Size'],
                    'last_modified': obj['LastModified']
                })
    return files


def extract_state_from_filename(filename):
    """Extract state code from filename like parcels_tx_harris.pmtiles"""
    # Remove prefix and extension
    base = filename.replace('parcels_', '').replace('.pmtiles', '')
    # Get state code (first part before underscore, or the whole thing for statewide)
    parts = base.split('_')
    state = parts[0].upper()
    return state if len(state) == 2 else None


def main():
    print("=" * 80)
    print("  VERIFY 50 STATES COVERAGE ON R2")
    print("=" * 80)
    print(f"  Started: {datetime.now().isoformat()}")
    print()

    # List all files
    print("Listing all PMTiles files in R2...")
    files = list_all_pmtiles()
    print(f"  Total PMTiles files: {len(files)}")
    print()

    # Group by state
    by_state = {}
    unknown = []

    for f in files:
        state = extract_state_from_filename(f['filename'])
        if state and state in ALL_STATES:
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(f)
        else:
            unknown.append(f)

    # Check coverage
    print("=" * 80)
    print("  STATE COVERAGE ANALYSIS")
    print("=" * 80)
    print()

    covered_states = set(by_state.keys())
    missing_states = set(ALL_STATES.keys()) - covered_states

    print(f"  States with data: {len(covered_states)}/50")
    print(f"  States missing: {len(missing_states)}")
    print()

    # Detail by state
    print("-" * 80)
    print(f"{'State':<6} {'Name':<20} {'Files':<6} {'Size (MB)':<12} {'Status'}")
    print("-" * 80)

    total_size = 0
    states_with_real_data = 0
    empty_states = []

    for state_code in sorted(ALL_STATES.keys()):
        state_name = ALL_STATES[state_code]

        if state_code in by_state:
            state_files = by_state[state_code]
            state_size = sum(f['size'] for f in state_files) / 1024 / 1024
            total_size += state_size

            # Check if files have actual data (> 1KB)
            has_data = any(f['size'] > 1024 for f in state_files)

            if has_data and state_size > 0.1:  # More than 100KB
                status = "OK"
                states_with_real_data += 1
            elif state_size > 0:
                status = "MINIMAL"
                empty_states.append((state_code, state_name, state_size))
            else:
                status = "EMPTY"
                empty_states.append((state_code, state_name, 0))

            print(f"{state_code:<6} {state_name:<20} {len(state_files):<6} {state_size:>10.1f}  {status}")
        else:
            print(f"{state_code:<6} {state_name:<20} {'0':<6} {'0.0':>10}  MISSING")
            empty_states.append((state_code, state_name, 0))

    print("-" * 80)
    print(f"{'TOTAL':<6} {'':<20} {len(files):<6} {total_size:>10.1f} MB")
    print()

    # Summary
    print("=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print()
    print(f"  Total states: 50")
    print(f"  States with files: {len(covered_states)}")
    print(f"  States with real data (>100KB): {states_with_real_data}")
    print(f"  States missing or empty: {len(empty_states)}")
    print(f"  Total data size: {total_size / 1024:.1f} GB")
    print()

    if missing_states:
        print("  MISSING STATES (no files at all):")
        for state in sorted(missing_states):
            print(f"    - {state}: {ALL_STATES[state]}")
        print()

    if empty_states:
        print("  STATES WITH NO/MINIMAL DATA:")
        for state_code, state_name, size in sorted(empty_states):
            if size == 0:
                print(f"    - {state_code}: {state_name} (NO DATA)")
            else:
                print(f"    - {state_code}: {state_name} ({size:.1f} MB - minimal)")
        print()

    # Files with 0 bytes
    empty_files = [f for f in files if f['size'] == 0]
    if empty_files:
        print(f"  EMPTY FILES (0 bytes): {len(empty_files)}")
        for f in empty_files[:20]:
            print(f"    - {f['filename']}")
        if len(empty_files) > 20:
            print(f"    ... and {len(empty_files) - 20} more")
        print()

    # Unknown files
    if unknown:
        print(f"  UNRECOGNIZED FILES: {len(unknown)}")
        for f in unknown[:10]:
            print(f"    - {f['filename']} ({f['size'] / 1024 / 1024:.1f} MB)")
        print()

    print("=" * 80)
    print("  VERIFICATION COMPLETE")
    print("=" * 80)

    # Return summary for programmatic use
    return {
        'total_files': len(files),
        'covered_states': len(covered_states),
        'states_with_data': states_with_real_data,
        'missing_states': list(missing_states),
        'empty_states': [(s[0], s[1]) for s in empty_states],
        'total_size_gb': total_size / 1024
    }


if __name__ == "__main__":
    result = main()

    # Exit with error if not all states covered
    if result['states_with_data'] < 50:
        print(f"\n  WARNING: Only {result['states_with_data']}/50 states have real data!")
        sys.exit(1)
