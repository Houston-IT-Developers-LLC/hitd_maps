#!/usr/bin/env python3
"""
SMART MEGA BLITZ V2 - Direct API Approach
==========================================
Query ArcGIS Hub APIs directly instead of parsing HTML
"""

import requests
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Configuration
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/output")
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def find_arcgis_hub_api(county_name, state_code):
    """Find ArcGIS Hub Open Data API for county"""
    county_slug = county_name.lower().replace(" county", "").replace(" ", "")

    # Common ArcGIS Hub patterns
    hub_patterns = [
        f"https://data-{county_slug}gis.opendata.arcgis.com",
        f"https://data-{county_slug}co.opendata.arcgis.com",
        f"https://opendata.{county_slug}county.gov",
        f"https://{county_slug}-{state_code.lower()}.opendata.arcgis.com",
        f"https://gcgis-{county_slug}county{state_code.lower()}.hub.arcgis.com",
        f"https://gisdata.{county_slug}countyga.gov" if state_code == "GA" else None,
    ]

    for hub_url in hub_patterns:
        if not hub_url:
            continue

        try:
            # Try to access the hub's search API
            api_url = f"{hub_url}/api/v3/datasets"
            resp = requests.get(api_url, params={"q": "parcel", "per_page": 10}, headers=HEADERS, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                if 'data' in data and len(data['data']) > 0:
                    return hub_url, data['data']

        except:
            pass

    return None, None

def extract_featureserver_from_dataset(dataset):
    """Extract FeatureServer URL from dataset metadata"""
    try:
        # Different ArcGIS Hub versions have different structures
        if 'url' in dataset and 'FeatureServer' in dataset['url']:
            return dataset['url']

        if 'attributes' in dataset:
            attrs = dataset['attributes']

            # Check for service URL
            if 'serviceUrl' in attrs:
                return attrs['serviceUrl']

            if 'url' in attrs and 'FeatureServer' in attrs['url']:
                return attrs['url']

        # Check relationships for feature service
        if 'relationships' in dataset and 'featureService' in dataset['relationships']:
            fs = dataset['relationships']['featureService']
            if 'data' in fs and 'url' in fs['data']:
                return fs['data']['url']

    except:
        pass

    return None

def try_direct_rest_service(county_name, state_code):
    """Try common direct ArcGIS REST service patterns"""
    county_slug = county_name.lower().replace(" county", "").replace(" ", "")

    rest_patterns = [
        f"https://gis.{county_slug}county.gov/arcgis/rest/services",
        f"https://gis.{county_slug}county{state_code.lower()}.gov/arcgis/rest/services",
        f"https://maps.{county_slug}county.gov/arcgis/rest/services",
        f"https://gis3.{county_slug}county.com/mapvis/rest/services",
        f"https://services.arcgis.com/{county_slug}/arcgis/rest/services",
    ]

    for base_url in rest_patterns:
        try:
            resp = requests.get(f"{base_url}?f=json", headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()

                # Look for parcel-related services
                services = data.get('services', []) + data.get('folders', [])
                for service in services:
                    if isinstance(service, dict):
                        name = service.get('name', '').lower()
                        stype = service.get('type', '')

                        if any(x in name for x in ['parcel', 'property', 'tax', 'cadastral', 'land']):
                            if stype == 'FeatureServer':
                                service_url = f"{base_url}/{service['name']}/FeatureServer/0"
                                return service_url

        except:
            pass

    return None

def verify_and_get_count(url):
    """Verify endpoint and get feature count"""
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
            elif 'error' in data:
                return False, f"Error: {data['error'].get('message', '')[:50]}"

        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)[:50]

def download_and_deploy(county_info, endpoint_url, feature_count):
    """Download and deploy county data"""
    county_name = county_info['name']
    state = county_info['state']
    source_id = f"{state.lower()}_{county_name.lower().replace(' ', '_').replace('county', '').strip()}"

    # Check if already exists
    try:
        resp = requests.head(f"{CDN_BASE}/parcels/parcels_{source_id}.pmtiles", timeout=10)
        if resp.status_code == 200:
            size = int(resp.headers.get('content-length', 0)) / (1024*1024)
            if size > 1:
                print(f"  ⏭️  SKIP: Already deployed ({size:.1f} MB)")
                return {"status": "skip", "reason": "already exists"}
    except:
        pass

    output_file = OUTPUT_DIR / "geojson" / f"parcels_{source_id}.geojson"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"  📥 Downloading {feature_count:,} parcels...")

    # Download in parallel batches
    all_features = []
    batch_size = 2000
    max_features = min(feature_count, 1000000)  # Cap at 1M for mega counties
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
            resp = requests.get(f"{endpoint_url}/query", params=params, headers=HEADERS, timeout=180)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('features', [])
        except:
            pass
        return None

    with ThreadPoolExecutor(max_workers=24) as executor:
        futures = {executor.submit(fetch, o): o for o in offsets}
        done = 0

        for future in as_completed(futures):
            features = future.result()
            if features:
                all_features.extend(features)
            done += 1

            if done % 20 == 0 or done == len(offsets):
                print(f"    [{done}/{len(offsets)}] {len(all_features):,} features")

    if len(all_features) < 100:
        print(f"  ✗ FAIL: Only {len(all_features)} features")
        return {"status": "fail", "reason": f"insufficient features"}

    # Save GeoJSON
    print(f"  💾 Saving {len(all_features):,} features...")
    with open(output_file, 'w') as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f)

    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"  ✓ GeoJSON: {size_mb:.1f} MB")

    # Convert to PMTiles
    pmtiles_path = OUTPUT_DIR / "pmtiles" / f"parcels_{source_id}.pmtiles"
    pmtiles_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  🔧 Converting to PMTiles...")
    try:
        subprocess.run([
            'tippecanoe', '-o', str(pmtiles_path),
            '-z', '15', '-Z', '10',
            '--drop-densest-as-needed',
            '--extend-zooms-if-still-dropping',
            '--force', '--layer', 'parcels',
            str(output_file)
        ], check=True, capture_output=True, timeout=3600)

        pm_size = pmtiles_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ PMTiles: {pm_size:.1f} MB")
    except Exception as e:
        print(f"  ✗ Tippecanoe failed: {e}")
        return {"status": "fail", "reason": "tippecanoe error"}

    # Upload to R2
    print(f"  ☁️  Uploading to R2...")
    try:
        subprocess.run([
            'aws', 's3', 'cp', str(pmtiles_path),
            f's3://{R2_BUCKET}/parcels/{pmtiles_path.name}',
            '--endpoint-url', R2_ENDPOINT
        ], check=True, capture_output=True, timeout=600)

        # Verify
        cdn_url = f"{CDN_BASE}/parcels/{pmtiles_path.name}"
        result = subprocess.run(
            ['pmtiles', 'show', cdn_url],
            capture_output=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"  ✅ SUCCESS: {cdn_url}")

            # Clean up
            output_file.unlink()
            pmtiles_path.unlink()

            return {
                "status": "success",
                "source_id": source_id,
                "features": len(all_features),
                "url": cdn_url
            }
        else:
            print(f"  ✗ Verification failed")
            return {"status": "fail", "reason": "verification failed"}

    except Exception as e:
        print(f"  ✗ Upload failed: {e}")
        return {"status": "fail", "reason": "upload error"}

def process_county(county_info):
    """Process a single county"""
    county_name = county_info['name']
    state = county_info['state']

    print(f"\n{'='*70}")
    print(f"[{state}] {county_name} County ({county_info['population']:,} pop)")
    print(f"{'='*70}")

    # Try 1: ArcGIS Hub API
    hub_url, datasets = find_arcgis_hub_api(county_name, state)
    if hub_url and datasets:
        print(f"  ✓ Found Hub: {hub_url}")

        # Look for parcel dataset
        for dataset in datasets:
            title = dataset.get('attributes', {}).get('name', '').lower()

            if any(x in title for x in ['parcel', 'property', 'tax', 'land', 'cadastral']):
                endpoint = extract_featureserver_from_dataset(dataset)

                if endpoint and 'FeatureServer' in endpoint:
                    print(f"  📍 Testing: {endpoint}")

                    works, result = verify_and_get_count(endpoint)
                    if works:
                        print(f"  ✅ VERIFIED: {result:,} features")

                        # Deploy it
                        deploy_result = download_and_deploy(county_info, endpoint, result)

                        if deploy_result['status'] in ['success', 'skip']:
                            return {
                                "county": f"{county_name}, {state}",
                                "status": deploy_result['status'],
                                "endpoint": endpoint,
                                "features": result
                            }

    # Try 2: Direct REST service endpoints
    print(f"  🔍 Trying direct REST services...")
    endpoint = try_direct_rest_service(county_name, state)

    if endpoint:
        print(f"  📍 Testing: {endpoint}")
        works, result = verify_and_get_count(endpoint)

        if works:
            print(f"  ✅ VERIFIED: {result:,} features")

            deploy_result = download_and_deploy(county_info, endpoint, result)

            if deploy_result['status'] in ['success', 'skip']:
                return {
                    "county": f"{county_name}, {state}",
                    "status": deploy_result['status'],
                    "endpoint": endpoint,
                    "features": result
                }

    print(f"  ❌ No working endpoint found")
    return {
        "county": f"{county_name}, {state}",
        "status": "no_endpoint"
    }

# Import county list from previous script
from mega_parallel_county_blitz import MEGA_COUNTY_LIST

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=16, help='Parallel workers')
    parser.add_argument('--limit', type=int, help='Process first N counties')
    parser.add_argument('--tier', type=int, help='Only tier 1, 2, or 3')
    args = parser.parse_args()

    counties = MEGA_COUNTY_LIST

    if args.tier == 1:
        counties = counties[:16]
    elif args.tier == 2:
        counties = counties[16:46]
    elif args.tier == 3:
        counties = counties[46:]

    if args.limit:
        counties = counties[:args.limit]

    print("="*80)
    print("  🚀 SMART MEGA BLITZ V2 - Direct API Approach")
    print(f"  Counties: {len(counties)}")
    print(f"  Workers: {args.workers}")
    print("="*80)

    results = {"deployed": [], "skipped": [], "failed": []}

    # Process in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_county, c): c for c in counties}

        for future in as_completed(futures):
            try:
                result = future.result()

                if result['status'] == 'success':
                    results['deployed'].append(result)
                elif result['status'] == 'skip':
                    results['skipped'].append(result)
                else:
                    results['failed'].append(result)

            except Exception as e:
                print(f"  ⚠️  ERROR: {e}")

    # Save results
    output_file = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/smart_blitz_v2_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(counties),
            "deployed": len(results['deployed']),
            "skipped": len(results['skipped']),
            "failed": len(results['failed']),
            "details": results
        }, f, indent=2)

    print("\n" + "="*80)
    print(f"  ✅ DEPLOYED: {len(results['deployed'])}")
    print(f"  ⏭️  SKIPPED: {len(results['skipped'])}")
    print(f"  ❌ FAILED: {len(results['failed'])}")
    print(f"\n  Results: {output_file}")
    print("="*80)

    if results['deployed']:
        print("\n🎉 NEW DEPLOYMENTS:")
        for r in results['deployed']:
            print(f"  • {r['county']} - {r['features']:,} parcels")

if __name__ == '__main__':
    main()
