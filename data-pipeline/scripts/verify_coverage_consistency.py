#!/usr/bin/env python3
"""
COVERAGE CONSISTENCY CHECK
Cross-references multiple data sources to ensure consistency:
1. valid_parcels.json vs actual R2 listing
2. coverage_status.json accuracy
3. data_sources_registry.json sync
4. Duplicate version detection
"""

import subprocess
import json
import sys
import os
from datetime import datetime
from collections import defaultdict
import re

# Paths
VALID_PARCELS_JSON = "data/valid_parcels.json"
COVERAGE_STATUS_JSON = "data/coverage_status.json"
DATA_SOURCES_REGISTRY_JSON = "data/data_sources_registry.json"

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

def get_r2_parcels():
    """Get list of all parcel files from R2"""
    result = subprocess.run([
        'aws', 's3', 'ls', 's3://gspot-tiles/parcels/',
        '--endpoint-url', R2_ENDPOINT
    ], capture_output=True, text=True, env={
        **os.environ,
        'AWS_ACCESS_KEY_ID': AWS_ACCESS_KEY,
        'AWS_SECRET_ACCESS_KEY': AWS_SECRET_KEY
    })

    parcels = {}
    for line in result.stdout.strip().split('\n'):
        if '.pmtiles' in line:
            parts = line.split()
            if len(parts) >= 4:
                filename = parts[3].replace('.pmtiles', '')
                size_mb = int(parts[2]) / (1024*1024)
                parcels[filename] = {
                    'size_mb': round(size_mb, 2),
                    'date': f"{parts[0]} {parts[1]}"
                }
    return parcels

def load_valid_parcels():
    """Load valid_parcels.json"""
    if not os.path.exists(VALID_PARCELS_JSON):
        return []
    with open(VALID_PARCELS_JSON, 'r') as f:
        return json.load(f)

def load_coverage_status():
    """Load coverage_status.json"""
    if not os.path.exists(COVERAGE_STATUS_JSON):
        return None
    with open(COVERAGE_STATUS_JSON, 'r') as f:
        return json.load(f)

def extract_state_from_filename(filename):
    """Extract state code from filename like parcels_tx_dallas -> TX"""
    parts = filename.replace('parcels_', '').split('_')
    if len(parts) > 0:
        state_code = parts[0].upper()
        # Check if valid US state code (2 letters)
        if len(state_code) == 2 and state_code.isalpha():
            return state_code
    return None

def normalize_filename(filename):
    """Remove version suffixes like _v2, _v3, _wgs84"""
    # Remove common version suffixes
    filename = re.sub(r'_v\d+$', '', filename)
    filename = re.sub(r'_wgs84$', '', filename)
    filename = re.sub(r'_recent$', '', filename)
    filename = re.sub(r'_new$', '', filename)
    return filename

def find_duplicates(parcels):
    """Find files with multiple versions"""
    # Group by normalized name
    groups = defaultdict(list)
    for name in parcels:
        normalized = normalize_filename(name)
        groups[normalized].append(name)

    # Find duplicates (groups with >1 file)
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    return duplicates

def check_file_existence():
    """Check consistency between valid_parcels.json and R2"""
    print("=== FILE EXISTENCE CHECK ===\n")

    r2_parcels = get_r2_parcels()
    valid_parcels = load_valid_parcels()

    print(f"Files in R2:                {len(r2_parcels)}")
    print(f"Files in valid_parcels.json: {len(valid_parcels)}")

    # Check for files in valid_parcels.json but missing from R2
    missing_from_r2 = [p for p in valid_parcels if p not in r2_parcels]

    # Check for files in R2 but not in valid_parcels.json
    missing_from_json = [p for p in r2_parcels if p not in valid_parcels]

    issues = []

    if missing_from_r2:
        print(f"\n⚠ Files in valid_parcels.json but MISSING from R2: {len(missing_from_r2)}")
        for f in missing_from_r2:
            print(f"  - {f}")
            issues.append(f"Missing from R2: {f}")

    if missing_from_json:
        print(f"\n⚠ Files in R2 but NOT in valid_parcels.json: {len(missing_from_json)}")
        for f in missing_from_json:
            size = r2_parcels[f]['size_mb']
            print(f"  - {f} ({size} MB)")
            issues.append(f"Not in valid_parcels.json: {f}")

    if not missing_from_r2 and not missing_from_json:
        print("\n✓ All files in sync between R2 and valid_parcels.json")

    return {
        'r2_count': len(r2_parcels),
        'json_count': len(valid_parcels),
        'missing_from_r2': missing_from_r2,
        'missing_from_json': missing_from_json,
        'issues': issues
    }

def check_duplicates():
    """Check for duplicate versions of files"""
    print("\n\n=== DUPLICATE VERSION CHECK ===\n")

    r2_parcels = get_r2_parcels()
    duplicates = find_duplicates(r2_parcels.keys())

    if not duplicates:
        print("✓ No duplicate versions found")
        return {'duplicates': {}, 'issues': []}

    print(f"Found {len(duplicates)} base files with multiple versions:\n")

    issues = []
    for base, versions in sorted(duplicates.items()):
        print(f"{base}:")
        for v in sorted(versions):
            size = r2_parcels[v]['size_mb']
            date = r2_parcels[v]['date']
            print(f"  - {v} ({size} MB, {date})")
        issues.append(f"Multiple versions: {', '.join(versions)}")
        print()

    print(f"💡 Consider keeping only the latest/largest version for each base file")

    return {
        'duplicates': duplicates,
        'issues': issues
    }

def check_coverage_accuracy():
    """Verify coverage_status.json matches actual files"""
    print("\n\n=== COVERAGE STATUS ACCURACY CHECK ===\n")

    coverage = load_coverage_status()
    if not coverage:
        print("⚠ coverage_status.json not found")
        return {'issues': ['coverage_status.json not found']}

    valid_parcels = load_valid_parcels()

    # Count files per state
    state_files = defaultdict(list)
    for filename in valid_parcels:
        state = extract_state_from_filename(filename)
        if state:
            state_files[state].append(filename)

    # Check for discrepancies
    issues = []
    print("Checking state-by-state accuracy...\n")

    for state, data in coverage['states'].items():
        actual_count = len(state_files.get(state, []))
        reported_count = len(data.get('county_files', []))
        if data.get('has_statewide'):
            reported_count += 1  # Add statewide file to count

        if actual_count != reported_count:
            print(f"⚠ {state}: Reported {reported_count} files, actually have {actual_count}")
            issues.append(f"{state}: Count mismatch (reported {reported_count}, actual {actual_count})")

    coverage_timestamp = coverage.get('timestamp', 'unknown')
    print(f"\nCoverage status last updated: {coverage_timestamp}")

    if not issues:
        print("\n✓ Coverage status matches actual files")

    return {
        'issues': issues,
        'coverage_timestamp': coverage_timestamp
    }

def check_state_coverage_completeness():
    """Check which states are complete vs partial"""
    print("\n\n=== STATE COVERAGE COMPLETENESS ===\n")

    valid_parcels = load_valid_parcels()

    # Count files per state
    state_files = defaultdict(list)
    statewide_files = []

    for filename in valid_parcels:
        state = extract_state_from_filename(filename)
        if state:
            state_files[state].append(filename)
            if 'statewide' in filename:
                statewide_files.append(filename)

    # US states (50 + DC)
    all_states = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
    ]

    complete_states = []
    partial_states = []
    missing_states = []

    for state in all_states:
        files = state_files.get(state, [])
        has_statewide = any('statewide' in f for f in files)

        if not files:
            missing_states.append(state)
        elif has_statewide:
            complete_states.append((state, len(files)))
        else:
            partial_states.append((state, len(files)))

    print(f"Complete states (with statewide): {len(complete_states)}")
    for state, count in sorted(complete_states):
        statewide = [f for f in state_files[state] if 'statewide' in f][0]
        print(f"  ✓ {state}: {count} files (statewide: {statewide})")

    print(f"\nPartial states (county-level only): {len(partial_states)}")
    for state, count in sorted(partial_states):
        print(f"  • {state}: {count} counties")

    if missing_states:
        print(f"\nMissing states: {len(missing_states)}")
        print(f"  {', '.join(sorted(missing_states))}")

    return {
        'complete': len(complete_states),
        'partial': len(partial_states),
        'missing': len(missing_states),
        'complete_list': [s for s, _ in complete_states],
        'partial_list': [s for s, _ in partial_states],
        'missing_list': missing_states
    }

def main():
    print("=== HITD Maps Coverage Consistency Check ===")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Change to data-pipeline directory if needed
    if not os.path.exists(VALID_PARCELS_JSON):
        if os.path.exists('data-pipeline/' + VALID_PARCELS_JSON):
            os.chdir('data-pipeline')

    # Run all checks
    results = {}

    results['file_existence'] = check_file_existence()
    results['duplicates'] = check_duplicates()
    results['coverage_accuracy'] = check_coverage_accuracy()
    results['state_coverage'] = check_state_coverage_completeness()

    # Summary
    print("\n\n" + "="*60)
    print("CONSISTENCY CHECK SUMMARY")
    print("="*60)

    total_issues = (
        len(results['file_existence']['issues']) +
        len(results['duplicates']['issues']) +
        len(results['coverage_accuracy']['issues'])
    )

    print(f"\nTotal issues found: {total_issues}")

    if total_issues == 0:
        print("\n✓ All consistency checks passed!")
    else:
        print("\n⚠ Issues require attention:")
        for category in ['file_existence', 'duplicates', 'coverage_accuracy']:
            if results[category]['issues']:
                print(f"\n{category.replace('_', ' ').title()}:")
                for issue in results[category]['issues'][:5]:  # Show first 5
                    print(f"  - {issue}")
                if len(results[category]['issues']) > 5:
                    print(f"  ... and {len(results[category]['issues']) - 5} more")

    # Save detailed results
    output_path = '/tmp/consistency_check_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_issues': total_issues,
                'complete_states': results['state_coverage']['complete'],
                'partial_states': results['state_coverage']['partial'],
                'missing_states': results['state_coverage']['missing']
            },
            'results': results
        }, f, indent=2)

    print(f"\nDetailed results saved to: {output_path}")

    # Exit with error code if issues found
    sys.exit(0 if total_issues == 0 else 1)

if __name__ == '__main__':
    main()
