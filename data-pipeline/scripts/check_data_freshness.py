#!/usr/bin/env python3
"""
Check data freshness across all sources - PASSIVE monitoring only.

This script:
1. Queries known ArcGIS REST APIs for current record counts
2. Compares to our last known counts
3. Identifies sources with potential updates
4. Outputs a report with recommended actions
5. Does NOT automatically update anything

Usage:
    python3 check_data_freshness.py              # Full check
    python3 check_data_freshness.py --quick      # Check only priority sources
    python3 check_data_freshness.py --state TX   # Check specific state
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error
import time

# Sources with known ArcGIS REST APIs we can query
CHECKABLE_SOURCES = {
    'ak_statewide': {
        'name': 'Alaska Statewide',
        'api_url': 'https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/AK_Parcels/FeatureServer/0',
        'state': 'AK',
        'our_file': 'parcels_ak_statewide',
        'last_known_count': 410000
    },
    'fl_statewide': {
        'name': 'Florida Statewide',
        'api_url': 'https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0',
        'state': 'FL',
        'our_file': 'parcels_fl_statewide',
        'last_known_count': 10800000
    },
    'id_statewide': {
        'name': 'Idaho Statewide',
        'api_url': 'https://services1.arcgis.com/CNPdEkvnGl65jCX8/arcgis/rest/services/Public_Idaho_Parcels/FeatureServer/0',
        'state': 'ID',
        'our_file': 'parcels_id_statewide',
        'last_known_count': 381000
    },
    'mt_statewide': {
        'name': 'Montana Statewide',
        'api_url': 'https://services.arcgis.com/iTQUx5ZpNUh47Geb/arcgis/rest/services/Montana_Parcel_Earliest_Build_Year/FeatureServer/0',
        'state': 'MT',
        'our_file': 'parcels_mt_statewide',
        'last_known_count': 607000
    },
    'nv_statewide': {
        'name': 'Nevada Statewide',
        'api_url': 'https://arcgis.water.nv.gov/arcgis/rest/services/BaseLayers/County_Parcels_in_Nevada/MapServer/0',
        'state': 'NV',
        'our_file': 'parcels_nv_statewide',
        'last_known_count': 1400000
    },
    'vt_statewide': {
        'name': 'Vermont Statewide',
        'api_url': 'https://services1.arcgis.com/BkFxaEFNwHqX3tAw/arcgis/rest/services/FS_VCGI_OPENDATA_Cadastral_VTPARCELS_poly_standardized_parcels_SP_v1/FeatureServer/0',
        'state': 'VT',
        'our_file': 'parcels_vt_statewide',
        'last_known_count': 344000
    },
    'dc': {
        'name': 'Washington DC',
        'api_url': 'https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Property_and_Land_WebMercator/MapServer/53',
        'state': 'DC',
        'our_file': 'parcels_dc',
        'last_known_count': 200000
    }
}

# Known update schedules
UPDATE_SCHEDULES = {
    'parcels_statewide': {
        'frequency': 'annual',
        'typical_months': ['January', 'February', 'March'],
        'notes': 'Most states update in Q1'
    },
    'pad_us': {
        'frequency': 'annual',
        'typical_months': ['November'],
        'notes': 'USGS releases in fall'
    },
    'protomaps_planet': {
        'frequency': 'monthly',
        'typical_months': ['1st of month'],
        'notes': 'Monthly OSM updates'
    }
}


def query_arcgis_count(api_url: str, timeout: int = 30) -> dict:
    """Query ArcGIS REST API for record count."""
    count_url = f"{api_url}/query?where=1%3D1&returnCountOnly=true&f=json"

    try:
        req = urllib.request.Request(count_url, headers={'User-Agent': 'HITD-Maps-Freshness-Checker/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode())
            return {
                'success': True,
                'count': data.get('count', 0),
                'error': None
            }
    except urllib.error.URLError as e:
        return {'success': False, 'count': 0, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'count': 0, 'error': str(e)}


def check_all_sources(sources: dict = None, quick: bool = False) -> dict:
    """Check all sources for updates."""
    if sources is None:
        sources = CHECKABLE_SOURCES

    if quick:
        # Only check high-priority sources
        sources = {k: v for k, v in sources.items() if k in ['fl_statewide', 'tx_statewide', 'dc']}

    results = {
        'checked_at': datetime.now().isoformat(),
        'sources_checked': 0,
        'sources_with_updates': [],
        'sources_current': [],
        'sources_error': [],
        'sources_unknown': []
    }

    print(f"\nChecking {len(sources)} data sources...")
    print("-" * 60)

    for source_id, source_info in sources.items():
        print(f"  Checking {source_info['name']}...", end=' ', flush=True)

        result = query_arcgis_count(source_info['api_url'])
        results['sources_checked'] += 1

        if result['success']:
            current_count = result['count']
            last_count = source_info['last_known_count']
            change_pct = ((current_count - last_count) / last_count * 100) if last_count > 0 else 0

            source_result = {
                'source_id': source_id,
                'name': source_info['name'],
                'state': source_info['state'],
                'current_records': current_count,
                'our_records': last_count,
                'change_pct': round(change_pct, 2),
                'our_file': source_info['our_file'],
                'api_url': source_info['api_url']
            }

            if abs(change_pct) > 1:  # More than 1% change
                source_result['recommendation'] = 'UPDATE_AVAILABLE'
                source_result['command_to_run'] = f"python3 download_missing_states.py --source {source_id}"
                results['sources_with_updates'].append(source_result)
                print(f"UPDATE AVAILABLE ({change_pct:+.1f}%)")
            else:
                source_result['recommendation'] = 'CURRENT'
                results['sources_current'].append(source_result)
                print(f"current ({current_count:,} records)")

        else:
            results['sources_error'].append({
                'source_id': source_id,
                'name': source_info['name'],
                'state': source_info['state'],
                'error': result['error']
            })
            print(f"ERROR: {result['error'][:50]}")

        time.sleep(0.5)  # Be nice to APIs

    return results


def load_registry() -> dict:
    """Load the data sources registry."""
    script_dir = Path(__file__).parent
    registry_path = script_dir.parent / 'data' / 'data_sources_registry.json'

    if registry_path.exists():
        with open(registry_path) as f:
            return json.load(f)
    return {}


def save_freshness_report(results: dict):
    """Save freshness report to JSON file."""
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data'
    output_path = data_dir / 'freshness_report.json'

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nReport saved to: {output_path}")


def print_summary(results: dict):
    """Print summary of freshness check."""
    print("\n" + "=" * 60)
    print("DATA FRESHNESS REPORT")
    print("=" * 60)
    print(f"Checked at: {results['checked_at']}")
    print(f"Sources checked: {results['sources_checked']}")
    print()

    if results['sources_with_updates']:
        print("UPDATES AVAILABLE:")
        print("-" * 60)
        for source in results['sources_with_updates']:
            print(f"  [{source['state']}] {source['name']}")
            print(f"      Current: {source['current_records']:,} | Ours: {source['our_records']:,} | Change: {source['change_pct']:+.1f}%")
            print(f"      Run: {source['command_to_run']}")
            print()
    else:
        print("All checked sources are current!")

    if results['sources_error']:
        print("\nSOURCES WITH ERRORS:")
        print("-" * 60)
        for source in results['sources_error']:
            print(f"  [{source['state']}] {source['name']}: {source['error'][:60]}")

    print("\n" + "=" * 60)
    print("RECOMMENDED CHECK SCHEDULE:")
    print("-" * 60)
    print("  Parcel Data:      Monthly (most update Q1 annually)")
    print("  PAD-US:           Annually (November release)")
    print("  Protomaps Planet: Monthly (1st of month)")
    print("  HIFLD Facilities: Quarterly")
    print("=" * 60)


def main():
    quick = '--quick' in sys.argv
    state_filter = None

    for i, arg in enumerate(sys.argv):
        if arg == '--state' and i + 1 < len(sys.argv):
            state_filter = sys.argv[i + 1].upper()

    sources = CHECKABLE_SOURCES

    if state_filter:
        sources = {k: v for k, v in sources.items() if v['state'] == state_filter}
        if not sources:
            print(f"No checkable sources found for state: {state_filter}")
            print("Available states with APIs:", ', '.join(set(v['state'] for v in CHECKABLE_SOURCES.values())))
            sys.exit(1)

    results = check_all_sources(sources, quick=quick)
    save_freshness_report(results)
    print_summary(results)

    # Return exit code based on whether updates are available
    if results['sources_with_updates']:
        print(f"\n{len(results['sources_with_updates'])} source(s) have updates available.")
        sys.exit(0)
    else:
        print("\nAll sources are current. No action needed.")
        sys.exit(0)


if __name__ == '__main__':
    main()
