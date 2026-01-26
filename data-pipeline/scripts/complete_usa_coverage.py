#!/usr/bin/env python3
"""
COMPLETE USA COVERAGE - 100% Mission
====================================
Systematically find and deploy ALL missing counties across USA
Work autonomously until 100% coverage achieved
"""

import requests
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from pathlib import Path
import re

# Configuration
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/output")
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# ALL US COUNTIES - Complete list organized by partial states
ALL_MISSING_COUNTIES = {
    # Format: "County Name": {"state": "XX", "population": int, "priority": 1-3}
    # Priority 1: 500K+, Priority 2: 100K-500K, Priority 3: <100K

    # ARIZONA (11 missing from 15 total)
    "Yuma": {"state": "AZ", "population": 213000, "priority": 2},
    "Mohave": {"state": "AZ", "population": 214000, "priority": 2},
    "Cochise": {"state": "AZ", "population": 126000, "priority": 2},
    "Navajo": {"state": "AZ", "population": 112000, "priority": 2},
    "Apache": {"state": "AZ", "population": 72000, "priority": 3},
    "Gila": {"state": "AZ", "population": 54000, "priority": 3},
    "La Paz": {"state": "AZ", "population": 20000, "priority": 3},
    "Santa Cruz": {"state": "AZ", "population": 47000, "priority": 3},
    "Graham": {"state": "AZ", "population": 38000, "priority": 3},
    "Greenlee": {"state": "AZ", "population": 10000, "priority": 3},

    # GEORGIA (151 missing from 159 total - we have 8)
    "Clayton": {"state": "GA", "population": 297000, "priority": 2},
    "Hall": {"state": "GA", "population": 208000, "priority": 2},
    "Columbia": {"state": "GA", "population": 156000, "priority": 2},
    "Muscogee": {"state": "GA", "population": 206000, "priority": 2},
    "Bibb": {"state": "GA", "population": 153000, "priority": 2},
    "Clarke": {"state": "GA", "population": 128000, "priority": 2},
    "Glynn": {"state": "GA", "population": 85000, "priority": 3},
    "Lowndes": {"state": "GA", "population": 118000, "priority": 2},
    "Houston": {"state": "GA", "population": 163000, "priority": 2},
    "Bartow": {"state": "GA", "population": 108000, "priority": 2},
    # ... (add all 151 GA counties systematically)

    # ILLINOIS (95 missing from 102 total - we have 7)
    "Kane": {"state": "IL", "population": 516000, "priority": 1},
    "Winnebago": {"state": "IL", "population": 285000, "priority": 2},
    "St. Clair": {"state": "IL", "population": 257000, "priority": 2},
    "Madison": {"state": "IL", "population": 265000, "priority": 2},
    "Champaign": {"state": "IL", "population": 209000, "priority": 2},
    "Sangamon": {"state": "IL", "population": 196000, "priority": 2},
    "Peoria": {"state": "IL", "population": 181000, "priority": 2},
    "Tazewell": {"state": "IL", "population": 131000, "priority": 2},
    "Rock Island": {"state": "IL", "population": 144000, "priority": 2},
    "McLean": {"state": "IL", "population": 170000, "priority": 2},
    # ... (add all IL counties)

    # MISSOURI (106 missing from 115 total - we have 9)
    "St. Louis": {"state": "MO", "population": 989000, "priority": 1},
    "St. Charles": {"state": "MO", "population": 407000, "priority": 2},
    "Clay": {"state": "MO", "population": 253000, "priority": 2},
    "Jefferson": {"state": "MO", "population": 226000, "priority": 2},
    "Platte": {"state": "MO", "population": 106000, "priority": 2},
    "Cass": {"state": "MO", "population": 107000, "priority": 2},
    "Franklin": {"state": "MO", "population": 104000, "priority": 2},
    # ... (add all MO counties)

    # KANSAS (103 missing from 105 total - we have 2)
    "Johnson": {"state": "KS", "population": 610000, "priority": 1},
    "Shawnee": {"state": "KS", "population": 178000, "priority": 2},
    "Wyandotte": {"state": "KS", "population": 165000, "priority": 2},
    "Douglas": {"state": "KS", "population": 122000, "priority": 2},
    "Leavenworth": {"state": "KS", "population": 82000, "priority": 3},
    "Riley": {"state": "KS", "population": 75000, "priority": 3},
    # ... (add all KS counties)

    # LOUISIANA (57 missing from 64 parishes - we have 7)
    "St. Tammany": {"state": "LA", "population": 265000, "priority": 2},
    "Livingston": {"state": "LA", "population": 142000, "priority": 2},
    "Tangipahoa": {"state": "LA", "population": 133000, "priority": 2},
    "Rapides": {"state": "LA", "population": 130000, "priority": 2},
    "Bossier": {"state": "LA", "population": 128000, "priority": 2},
    "St. Bernard": {"state": "LA", "population": 47000, "priority": 3},
    "Plaquemines": {"state": "LA", "population": 23000, "priority": 3},
    "Iberia": {"state": "LA", "population": 69000, "priority": 3},
    "Vermilion": {"state": "LA", "population": 58000, "priority": 3},
    "Lafourche": {"state": "LA", "population": 97000, "priority": 3},
    # ... (add all LA parishes)

    # MICHIGAN (73 missing from 83 total - we have 10)
    "Ingham": {"state": "MI", "population": 284000, "priority": 2},
    "Saginaw": {"state": "MI", "population": 190000, "priority": 2},
    "Berrien": {"state": "MI", "population": 154000, "priority": 2},
    "Jackson": {"state": "MI", "population": 160000, "priority": 2},
    "Bay": {"state": "MI", "population": 103000, "priority": 2},
    "Muskegon": {"state": "MI", "population": 175000, "priority": 2},
    "Monroe": {"state": "MI", "population": 154000, "priority": 2},
    "Midland": {"state": "MI", "population": 83000, "priority": 3},
    # ... (add all MI counties)

    # KENTUCKY (115 missing from 120 total - we have 5)
    "Kenton": {"state": "KY", "population": 169000, "priority": 2},
    "Boone": {"state": "KY", "population": 135000, "priority": 2},
    "Warren": {"state": "KY", "population": 134000, "priority": 2},
    "Hardin": {"state": "KY", "population": 110000, "priority": 2},
    "Daviess": {"state": "KY", "population": 102000, "priority": 2},
    # ... (add all KY counties)

    # OKLAHOMA (73 missing from 77 total - we have 4)
    "Cleveland": {"state": "OK", "population": 295000, "priority": 2},
    "Canadian": {"state": "OK", "population": 154000, "priority": 2},
    "Comanche": {"state": "OK", "population": 121000, "priority": 2},
    "Rogers": {"state": "OK", "population": 95000, "priority": 3},
    # ... (add all OK counties)

    # OREGON (34 missing from 36 total - we have 2)
    "Washington": {"state": "OR", "population": 606000, "priority": 1},
    "Clackamas": {"state": "OR", "population": 421000, "priority": 2},
    "Lane": {"state": "OR", "population": 382000, "priority": 2},
    "Marion": {"state": "OR", "population": 345000, "priority": 2},
    "Jackson": {"state": "OR", "population": 223000, "priority": 2},
    "Deschutes": {"state": "OR", "population": 198000, "priority": 2},
    # ... (add all OR counties)

    # SOUTH CAROLINA (43 missing from 46 total - we have 3)
    "Richland": {"state": "SC", "population": 416000, "priority": 2},
    "Spartanburg": {"state": "SC", "population": 327000, "priority": 2},
    "Horry": {"state": "SC", "population": 351000, "priority": 2},
    "York": {"state": "SC", "population": 282000, "priority": 2},
    "Lexington": {"state": "SC", "population": 296000, "priority": 2},
    # ... (add all SC counties)

    # ALABAMA (63 missing from 67 total - we have 4)
    "Madison": {"state": "AL", "population": 388000, "priority": 2},
    "Montgomery": {"state": "AL", "population": 228000, "priority": 2},
    "Shelby": {"state": "AL", "population": 223000, "priority": 2},
    "Tuscaloosa": {"state": "AL", "population": 209000, "priority": 2},
    "Baldwin": {"state": "AL", "population": 231000, "priority": 2},
    # ... (add all AL counties)

    # MISSISSIPPI (77 missing from 82 total - we have 5)
    "Hinds": {"state": "MS", "population": 230000, "priority": 2},
    "Harrison": {"state": "MS", "population": 208000, "priority": 2},
    "DeSoto": {"state": "MS", "population": 185000, "priority": 2},
    "Rankin": {"state": "MS", "population": 157000, "priority": 2},
    "Madison": {"state": "MS", "population": 109000, "priority": 2},
    # ... (add all MS counties)

    # SOUTH DAKOTA (60 missing from 66 total - we have 6)
    "Meade": {"state": "SD", "population": 29000, "priority": 3},
    "Codington": {"state": "SD", "population": 28000, "priority": 3},
    "Yankton": {"state": "SD", "population": 23000, "priority": 3},
    "Lawrence": {"state": "SD", "population": 25000, "priority": 3},
    # ... (add all SD counties)

    # NEBRASKA (92 missing from 93 total - we have 1: Douglas)
    "Lancaster": {"state": "NE", "population": 322000, "priority": 2},
    "Sarpy": {"state": "NE", "population": 190000, "priority": 2},
    "Hall": {"state": "NE", "population": 62000, "priority": 3},
    "Buffalo": {"state": "NE", "population": 50000, "priority": 3},
    # ... (add all NE counties)
}

def find_endpoints_multi_method(county_name, state_code):
    """Try multiple methods to find FeatureServer endpoint"""
    endpoints = []

    # Method 1: ArcGIS Hub API
    hub_patterns = [
        f"https://data-{county_name.lower().replace(' ', '')}gis.opendata.arcgis.com",
        f"https://gisdata.{county_name.lower().replace(' ', '')}county{state_code.lower()}.gov",
        f"https://{county_name.lower().replace(' ', '')}-{state_code.lower()}.opendata.arcgis.com",
    ]

    for hub_url in hub_patterns:
        try:
            api_url = f"{hub_url}/api/v3/datasets"
            resp = requests.get(api_url, params={"q": "parcel OR property OR tax", "per_page": 20},
                              headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'data' in data:
                    for dataset in data['data']:
                        url = dataset.get('attributes', {}).get('url', '')
                        if 'FeatureServer' in url:
                            endpoints.append(url)
        except:
            pass

    # Method 2: Direct REST service patterns
    rest_patterns = [
        f"https://gis.{county_name.lower().replace(' ', '')}county.gov/arcgis/rest/services",
        f"https://gis.co.{county_name.lower().replace(' ', '')}.{state_code.lower()}.us/arcgis/rest/services",
        f"https://gisservices.{county_name.lower().replace(' ', '')}county.gov/arcgis/rest/services",
    ]

    for base_url in rest_patterns:
        try:
            resp = requests.get(f"{base_url}?f=json", headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for service in data.get('services', []):
                    if isinstance(service, dict):
                        name = service.get('name', '').lower()
                        if any(x in name for x in ['parcel', 'property', 'tax', 'cadastral']):
                            if service.get('type') == 'FeatureServer':
                                endpoints.append(f"{base_url}/{service['name']}/FeatureServer/0")
        except:
            pass

    # Method 3: State-level services
    state_patterns = {
        "IL": "https://gis.carlisillinois.org/arcgis/rest/services",
        "MO": "https://msdis.missouri.edu/data/",
        "KS": "https://www.kansasgis.org/",
        # ... add more state patterns
    }

    return list(set(endpoints))  # Remove duplicates

def verify_endpoint(url):
    """Verify endpoint and get count"""
    try:
        resp = requests.get(
            f"{url}/query",
            params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
            headers=HEADERS,
            timeout=20
        )
        if resp.status_code == 200:
            data = resp.json()
            if 'count' in data and data['count'] > 0:
                return True, data['count']
    except:
        pass
    return False, 0

def download_county(county_name, state_code, endpoint, feature_count):
    """Download, convert, and upload county data"""
    source_id = f"{state_code.lower()}_{county_name.lower().replace(' ', '_')}"

    # Check if exists
    try:
        resp = requests.head(f"{CDN_BASE}/parcels/parcels_{source_id}.pmtiles", timeout=10)
        if resp.status_code == 200:
            return {"status": "skip", "message": "already exists"}
    except:
        pass

    output_file = OUTPUT_DIR / "geojson" / f"parcels_{source_id}.geojson"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"  📥 Downloading {county_name}, {state_code} ({feature_count:,} parcels)")

    # Download in parallel batches
    all_features = []
    batch_size = 2000
    max_features = min(feature_count, 2000000)  # Cap at 2M
    offsets = list(range(0, max_features, batch_size))

    def fetch(offset):
        try:
            params = {
                'where': '1=1',
                'outFields': '*',
                'f': 'geojson',
                'resultOffset': offset,
                'resultRecordCount': batch_size,
                'outSR': '4326'
            }
            resp = requests.get(f"{endpoint}/query", params=params, headers=HEADERS, timeout=180)
            if resp.status_code == 200:
                return resp.json().get('features', [])
        except:
            pass
        return None

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(fetch, o): o for o in offsets}
        done = 0
        for future in as_completed(futures):
            features = future.result()
            if features:
                all_features.extend(features)
            done += 1
            if done % 50 == 0:
                print(f"    [{done}/{len(offsets)}] {len(all_features):,} features")

    if len(all_features) < 100:
        return {"status": "fail", "message": f"only {len(all_features)} features"}

    # Save GeoJSON
    with open(output_file, 'w') as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f)

    # Convert to PMTiles
    pmtiles_path = OUTPUT_DIR / "pmtiles" / f"parcels_{source_id}.pmtiles"
    pmtiles_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run([
            'tippecanoe', '-o', str(pmtiles_path),
            '-z', '15', '-Z', '10',
            '--drop-densest-as-needed',
            '--extend-zooms-if-still-dropping',
            '--force', '--layer', 'parcels',
            str(output_file)
        ], check=True, capture_output=True, timeout=3600)
    except Exception as e:
        return {"status": "fail", "message": f"tippecanoe: {e}"}

    # Upload to R2
    try:
        subprocess.run([
            'aws', 's3', 'cp', str(pmtiles_path),
            f's3://{R2_BUCKET}/parcels/{pmtiles_path.name}',
            '--endpoint-url', R2_ENDPOINT
        ], check=True, capture_output=True, timeout=600)

        # Verify
        cdn_url = f"{CDN_BASE}/parcels/{pmtiles_path.name}"
        result = subprocess.run(['pmtiles', 'show', cdn_url], capture_output=True, timeout=60)

        if result.returncode == 0:
            # Clean up
            output_file.unlink()
            pmtiles_path.unlink()

            print(f"  ✅ SUCCESS: {source_id}")
            return {
                "status": "success",
                "source_id": source_id,
                "features": len(all_features),
                "url": cdn_url
            }
    except Exception as e:
        return {"status": "fail", "message": f"upload: {e}"}

    return {"status": "fail", "message": "unknown error"}

def process_county(county_name, county_info):
    """Full pipeline for one county"""
    state = county_info['state']

    print(f"\n{'='*70}")
    print(f"[{state}] {county_name} County (pop: {county_info['population']:,})")
    print(f"{'='*70}")

    # Find endpoints
    endpoints = find_endpoints_multi_method(county_name, state)

    if not endpoints:
        print(f"  ❌ No endpoints found")
        return {"county": county_name, "state": state, "status": "no_endpoint"}

    print(f"  📍 Found {len(endpoints)} potential endpoints")

    # Test each endpoint
    for endpoint in endpoints[:5]:  # Test up to 5 endpoints
        works, count = verify_endpoint(endpoint)
        if works:
            print(f"  ✅ VERIFIED: {endpoint} ({count:,} features)")

            # Download and deploy
            result = download_county(county_name, state, endpoint, count)
            if result['status'] == 'success':
                return {
                    "county": county_name,
                    "state": state,
                    "status": "success",
                    "features": result['features'],
                    "source_id": result['source_id']
                }

    print(f"  ❌ No working endpoints")
    return {"county": county_name, "state": state, "status": "no_working_endpoint"}

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=48, help='Parallel county workers')
    parser.add_argument('--priority', type=int, help='Only process priority level (1, 2, or 3)')
    parser.add_argument('--state', type=str, help='Only process specific state')
    parser.add_argument('--limit', type=int, help='Limit to first N counties')
    args = parser.parse_args()

    # Filter counties
    counties = ALL_MISSING_COUNTIES.copy()

    if args.priority:
        counties = {k: v for k, v in counties.items() if v['priority'] == args.priority}

    if args.state:
        counties = {k: v for k, v in counties.items() if v['state'] == args.state.upper()}

    if args.limit:
        counties = dict(list(counties.items())[:args.limit])

    # Sort by priority and population
    sorted_counties = sorted(counties.items(),
                            key=lambda x: (x[1]['priority'], -x[1]['population']))

    print("="*80)
    print("  🚀 COMPLETE USA COVERAGE MISSION")
    print(f"  Counties to process: {len(sorted_counties)}")
    print(f"  Parallel workers: {args.workers}")
    print("="*80)

    results = {"success": [], "failed": [], "skipped": []}

    # Process in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_county, name, info): name
                  for name, info in sorted_counties}

        for future in as_completed(futures):
            try:
                result = future.result()
                if result['status'] == 'success':
                    results['success'].append(result)
                elif result['status'] == 'skip':
                    results['skipped'].append(result)
                else:
                    results['failed'].append(result)
            except Exception as e:
                print(f"  ⚠️  ERROR: {e}")

    # Save results
    output_file = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/complete_usa_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(sorted_counties),
            "success": len(results['success']),
            "failed": len(results['failed']),
            "skipped": len(results['skipped']),
            "details": results
        }, f, indent=2)

    print("\n" + "="*80)
    print(f"  ✅ SUCCESS: {len(results['success'])}")
    print(f"  ⏭️  SKIPPED: {len(results['skipped'])}")
    print(f"  ❌ FAILED: {len(results['failed'])}")
    print(f"\n  Results: {output_file}")
    print("="*80)

    if results['success']:
        print("\n🎉 NEW DEPLOYMENTS:")
        for r in results['success'][:20]:  # Show first 20
            print(f"  • {r['county']}, {r['state']} - {r['features']:,} parcels")

if __name__ == '__main__':
    main()
