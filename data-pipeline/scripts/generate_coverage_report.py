#!/usr/bin/env python3
"""
Generate comprehensive USA parcel coverage report.

This script:
1. Reads all PMTiles files from valid_parcels.json
2. Analyzes coverage by state
3. Identifies gaps and missing data
4. Generates coverage_status.json with detailed metadata
5. Can optionally update CLAUDE.md with current stats

Usage:
    python3 generate_coverage_report.py [--update-claude-md]
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# All 50 US states + DC
US_STATES = {
    'AL': {'name': 'Alabama', 'counties': 67},
    'AK': {'name': 'Alaska', 'counties': 30},
    'AZ': {'name': 'Arizona', 'counties': 15},
    'AR': {'name': 'Arkansas', 'counties': 75},
    'CA': {'name': 'California', 'counties': 58},
    'CO': {'name': 'Colorado', 'counties': 64},
    'CT': {'name': 'Connecticut', 'counties': 8},
    'DE': {'name': 'Delaware', 'counties': 3},
    'DC': {'name': 'District of Columbia', 'counties': 1},
    'FL': {'name': 'Florida', 'counties': 67},
    'GA': {'name': 'Georgia', 'counties': 159},
    'HI': {'name': 'Hawaii', 'counties': 5},
    'ID': {'name': 'Idaho', 'counties': 44},
    'IL': {'name': 'Illinois', 'counties': 102},
    'IN': {'name': 'Indiana', 'counties': 92},
    'IA': {'name': 'Iowa', 'counties': 99},
    'KS': {'name': 'Kansas', 'counties': 105},
    'KY': {'name': 'Kentucky', 'counties': 120},
    'LA': {'name': 'Louisiana', 'counties': 64},
    'ME': {'name': 'Maine', 'counties': 16},
    'MD': {'name': 'Maryland', 'counties': 24},
    'MA': {'name': 'Massachusetts', 'counties': 14},
    'MI': {'name': 'Michigan', 'counties': 83},
    'MN': {'name': 'Minnesota', 'counties': 87},
    'MS': {'name': 'Mississippi', 'counties': 82},
    'MO': {'name': 'Missouri', 'counties': 115},
    'MT': {'name': 'Montana', 'counties': 56},
    'NE': {'name': 'Nebraska', 'counties': 93},
    'NV': {'name': 'Nevada', 'counties': 17},
    'NH': {'name': 'New Hampshire', 'counties': 10},
    'NJ': {'name': 'New Jersey', 'counties': 21},
    'NM': {'name': 'New Mexico', 'counties': 33},
    'NY': {'name': 'New York', 'counties': 62},
    'NC': {'name': 'North Carolina', 'counties': 100},
    'ND': {'name': 'North Dakota', 'counties': 53},
    'OH': {'name': 'Ohio', 'counties': 88},
    'OK': {'name': 'Oklahoma', 'counties': 77},
    'OR': {'name': 'Oregon', 'counties': 36},
    'PA': {'name': 'Pennsylvania', 'counties': 67},
    'RI': {'name': 'Rhode Island', 'counties': 5},
    'SC': {'name': 'South Carolina', 'counties': 46},
    'SD': {'name': 'South Dakota', 'counties': 66},
    'TN': {'name': 'Tennessee', 'counties': 95},
    'TX': {'name': 'Texas', 'counties': 254},
    'UT': {'name': 'Utah', 'counties': 29},
    'VT': {'name': 'Vermont', 'counties': 14},
    'VA': {'name': 'Virginia', 'counties': 133},
    'WA': {'name': 'Washington', 'counties': 39},
    'WV': {'name': 'West Virginia', 'counties': 55},
    'WI': {'name': 'Wisconsin', 'counties': 72},
    'WY': {'name': 'Wyoming', 'counties': 23},
}

# Known statewide data sources
STATEWIDE_SOURCES = {
    'AK': {'url': 'https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/AK_Parcels/FeatureServer/0', 'records': 410000},
    'AR': {'url': 'https://gis.arkansas.gov', 'records': 2100000},
    'CO': {'url': 'https://coloradogeo.org', 'records': 2500000},
    'CT': {'url': 'https://ct.gov/gis', 'records': 1200000},
    'DE': {'url': 'https://firstmap.delaware.gov', 'records': 350000},
    'FL': {'url': 'https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0', 'records': 10800000},
    'HI': {'url': 'https://geoportal.hawaii.gov', 'records': 400000},
    'IA': {'url': 'https://geodata.iowa.gov', 'records': 1500000},
    'ID': {'url': 'https://services1.arcgis.com/CNPdEkvnGl65jCX8/arcgis/rest/services/Public_Idaho_Parcels/FeatureServer/0', 'records': 381000},
    'IN': {'url': 'https://gis.in.gov', 'records': 3200000},
    'MA': {'url': 'https://massgis.maps.arcgis.com', 'records': 2100000},
    'MD': {'url': 'https://imap.maryland.gov', 'records': 2400000},
    'ME': {'url': 'https://maine.gov/geolib', 'records': 700000},
    'MT': {'url': 'https://services.arcgis.com/iTQUx5ZpNUh47Geb/arcgis/rest/services/Montana_Parcel_Earliest_Build_Year/FeatureServer/0', 'records': 607000},
    'NC': {'url': 'https://ncgis.maps.arcgis.com', 'records': 4500000},
    'ND': {'url': 'https://ndgishub.nd.gov', 'records': 745000},
    'NH': {'url': 'https://granit.unh.edu', 'records': 500000},
    'NJ': {'url': 'https://njgin.nj.gov', 'records': 2800000},
    'NM': {'url': 'https://rgis.unm.edu', 'records': 1100000},
    'NV': {'url': 'https://arcgis.water.nv.gov/arcgis/rest/services/BaseLayers/County_Parcels_in_Nevada/MapServer/0', 'records': 1400000},
    'NY': {'url': 'https://gis.ny.gov', 'records': 9000000},
    'OH': {'url': 'https://gis.ohio.gov', 'records': 6300000},
    'PA': {'url': 'https://pasda.psu.edu', 'records': 5600000},
    'RI': {'url': 'https://rigis.org', 'records': 400000},  # Needs discovery
    'TN': {'url': 'https://tn.gov/gis', 'records': 3000000},
    'TX': {'url': 'https://tnris.org/stratmap/', 'records': 28000000},
    'UT': {'url': 'https://gis.utah.gov', 'records': 1100000},
    'VA': {'url': 'https://vgin.vdem.virginia.gov', 'records': 4100000},
    'VT': {'url': 'https://services1.arcgis.com/BkFxaEFNwHqX3tAw/arcgis/rest/services/', 'records': 344000},
    'WA': {'url': 'https://geo.wa.gov', 'records': 3200000},
    'WI': {'url': 'https://sco.wisc.edu', 'records': 3500000},
    'WV': {'url': 'https://wvgis.wvu.edu', 'records': 1000000},
}


def parse_parcel_file(filename: str) -> dict:
    """Parse parcel filename to extract state and county info."""
    # Remove 'parcels_' prefix
    name = filename.replace('parcels_', '')

    # Special cases
    if name == 'counties':
        return {'type': 'overlay', 'state': None, 'county': None}
    if name == 'montgomery':
        return {'type': 'county', 'state': 'unknown', 'county': 'montgomery'}

    # Extract state code (first 2 chars)
    state = name[:2].upper()

    # Check if it's a statewide file
    if 'statewide' in name.lower():
        return {'type': 'statewide', 'state': state, 'county': None}

    # Check if it's just the state code
    if len(name) == 2:
        return {'type': 'state', 'state': state, 'county': None}

    # Extract county name
    county_part = name[3:] if len(name) > 2 else None  # Skip state code and underscore

    # Clean up county name (remove _v2, _wgs84, etc.)
    if county_part:
        county_part = county_part.replace('_v2', '').replace('_wgs84', '').replace('_new', '')

    return {'type': 'county', 'state': state, 'county': county_part}


def load_valid_parcels() -> list:
    """Load valid parcels list."""
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data'
    valid_parcels_path = data_dir / 'valid_parcels.json'

    if valid_parcels_path.exists():
        with open(valid_parcels_path) as f:
            return json.load(f)
    return []


def generate_coverage_report() -> dict:
    """Generate comprehensive coverage report."""
    valid_parcels = load_valid_parcels()

    # Initialize state tracking
    state_data = {}
    for state_code, info in US_STATES.items():
        state_data[state_code] = {
            'name': info['name'],
            'total_counties': info['counties'],
            'status': 'missing',
            'completeness_pct': 0,
            'has_statewide': False,
            'statewide_file': None,
            'county_files': [],
            'files': [],
            'missing_counties': [],
            'data_source': STATEWIDE_SOURCES.get(state_code, {}).get('url', 'Unknown'),
            'estimated_total_parcels': STATEWIDE_SOURCES.get(state_code, {}).get('records', 0),
            'last_updated': None,
            'notes': ''
        }

    # Process each parcel file
    for parcel_file in valid_parcels:
        parsed = parse_parcel_file(parcel_file)
        state = parsed.get('state')

        if state and state in state_data:
            state_data[state]['files'].append(parcel_file)

            if parsed['type'] == 'statewide':
                state_data[state]['has_statewide'] = True
                state_data[state]['statewide_file'] = parcel_file
            elif parsed['type'] == 'county' and parsed['county']:
                state_data[state]['county_files'].append(parcel_file)

    # Calculate status for each state
    complete_states = 0
    partial_states = 0
    missing_states = 0

    for state_code, data in state_data.items():
        file_count = len(data['files'])

        if file_count == 0:
            data['status'] = 'missing'
            data['completeness_pct'] = 0
            missing_states += 1
        elif data['has_statewide']:
            data['status'] = 'complete'
            data['completeness_pct'] = 100
            complete_states += 1
        else:
            # Partial coverage - estimate based on county files
            county_count = len(data['county_files'])
            total_counties = data['total_counties']
            pct = min(100, int((county_count / total_counties) * 100))
            data['completeness_pct'] = pct

            if pct >= 80:
                data['status'] = 'mostly_complete'
                complete_states += 1
            else:
                data['status'] = 'partial'
                partial_states += 1

    # Build summary
    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_states': 51,  # 50 + DC
            'complete_states': complete_states,
            'partial_states': partial_states,
            'missing_states': missing_states,
            'total_files': len(valid_parcels),
            'coverage_pct': round((complete_states / 51) * 100, 1)
        },
        'states': state_data,
        'priority_actions': []
    }

    # Generate priority actions
    for state_code, data in state_data.items():
        if data['status'] == 'missing':
            report['priority_actions'].append({
                'priority': 1,
                'state': state_code,
                'action': f"Find and scrape {data['name']} parcel data source",
                'estimated_parcels': data['estimated_total_parcels']
            })
        elif data['status'] == 'partial' and data['completeness_pct'] < 50:
            report['priority_actions'].append({
                'priority': 2,
                'state': state_code,
                'action': f"Expand {data['name']} coverage ({data['completeness_pct']}% complete)",
                'estimated_parcels': data['estimated_total_parcels']
            })

    # Sort priority actions
    report['priority_actions'].sort(key=lambda x: (x['priority'], -x['estimated_parcels']))

    return report


def save_coverage_status(report: dict):
    """Save coverage status to JSON file."""
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data'
    output_path = data_dir / 'coverage_status.json'

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Coverage status saved to: {output_path}")


def print_coverage_summary(report: dict):
    """Print coverage summary to console."""
    summary = report['summary']

    print("\n" + "="*60)
    print("USA PARCEL COVERAGE REPORT")
    print("="*60)
    print(f"Generated: {report['generated_at']}")
    print()
    print(f"Total Files: {summary['total_files']}")
    print(f"Coverage: {summary['coverage_pct']}%")
    print()
    print(f"Complete States: {summary['complete_states']}")
    print(f"Partial States:  {summary['partial_states']}")
    print(f"Missing States:  {summary['missing_states']}")
    print()

    # Show states by status
    print("-"*60)
    print("COMPLETE STATES (statewide coverage):")
    complete = [(k, v) for k, v in report['states'].items() if v['status'] == 'complete']
    for state, data in sorted(complete, key=lambda x: x[1]['name']):
        print(f"  {state}: {data['name']} ({len(data['files'])} files)")

    print()
    print("-"*60)
    print("PARTIAL STATES (county-level only):")
    partial = [(k, v) for k, v in report['states'].items() if v['status'] == 'partial']
    for state, data in sorted(partial, key=lambda x: -x[1]['completeness_pct']):
        print(f"  {state}: {data['name']} - {data['completeness_pct']}% ({len(data['county_files'])} counties)")

    print()
    print("-"*60)
    print("MISSING STATES (no coverage):")
    missing = [(k, v) for k, v in report['states'].items() if v['status'] == 'missing']
    for state, data in sorted(missing, key=lambda x: x[1]['name']):
        print(f"  {state}: {data['name']}")

    print()
    print("-"*60)
    print("PRIORITY ACTIONS:")
    for i, action in enumerate(report['priority_actions'][:10], 1):
        print(f"  {i}. [{action['state']}] {action['action']}")

    print("="*60)


def update_claude_md(report: dict):
    """Update CLAUDE.md with current coverage stats."""
    script_dir = Path(__file__).parent
    claude_md_path = script_dir.parent.parent / 'CLAUDE.md'

    if not claude_md_path.exists():
        print(f"CLAUDE.md not found at {claude_md_path}")
        return

    summary = report['summary']

    # Generate coverage section
    coverage_section = f"""
## Current Coverage Status (Auto-updated: {datetime.now().strftime('%Y-%m-%d')})

| Metric | Value |
|--------|-------|
| Total Files | {summary['total_files']} |
| Coverage | {summary['coverage_pct']}% |
| Complete States | {summary['complete_states']} |
| Partial States | {summary['partial_states']} |
| Missing States | {summary['missing_states']} |

### States with Full Coverage
"""

    complete = [(k, v) for k, v in report['states'].items() if v['status'] == 'complete']
    for state, data in sorted(complete, key=lambda x: x[1]['name']):
        coverage_section += f"- **{state}** ({data['name']}): {len(data['files'])} files\n"

    coverage_section += "\n### States Needing Attention\n"

    for action in report['priority_actions'][:5]:
        coverage_section += f"- **{action['state']}**: {action['action']}\n"

    print("Coverage section generated. Manual update to CLAUDE.md recommended.")
    print(coverage_section)


if __name__ == '__main__':
    import sys

    print("Generating coverage report...")
    report = generate_coverage_report()

    save_coverage_status(report)
    print_coverage_summary(report)

    if '--update-claude-md' in sys.argv:
        update_claude_md(report)
