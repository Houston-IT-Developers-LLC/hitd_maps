#!/usr/bin/env python3
"""
HITD Maps - Smart Source Verifier & Deployer
=============================================
Verify all potential statewide sources, then deploy downloads

Run: python3 verify_and_deploy_statewide.py --verify-all
     python3 verify_and_deploy_statewide.py --deploy-verified
"""

import requests
import json
import subprocess
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
OUTPUT_DIR = SCRIPT_DIR.parent / "output"

# R2 Config
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

class SourceVerifier:
    """Verify ArcGIS REST endpoints"""

    def __init__(self):
        self.verified_sources = {}

    def check_arcgis_endpoint(self, url, timeout=30):
        """Check if ArcGIS endpoint has parcels"""
        try:
            # Try to get service info
            resp = requests.get(f"{url}?f=json", headers=HEADERS, timeout=timeout)
            if resp.status_code != 200:
                return None

            data = resp.json()

            # Check for error
            if 'error' in data:
                return None

            # Look for parcel-related keywords
            name = data.get('name', '').lower()
            desc = data.get('description', '').lower()

            parcel_keywords = ['parcel', 'cadastral', 'property', 'tax', 'lot']
            is_parcel = any(kw in name or kw in desc for kw in parcel_keywords)

            if not is_parcel:
                return None

            # Try to get count
            count_resp = requests.get(
                f"{url}/query?where=1%3D1&returnCountOnly=true&f=json",
                headers=HEADERS,
                timeout=timeout
            )

            if count_resp.status_code == 200:
                count_data = count_resp.json()
                count = count_data.get('count', 0)

                if count > 10000:  # Must have at least 10k parcels
                    return {
                        'url': url,
                        'name': data.get('name'),
                        'count': count,
                        'verified': True,
                        'timestamp': datetime.now().isoformat()
                    }

        except Exception as e:
            pass

        return None

    def search_arcgis_services(self, base_url, state_code):
        """Recursively search for parcel services"""
        print(f"  🔍 Searching {base_url}...")

        found = []

        try:
            # Check if it's a MapServer or FeatureServer
            for service_type in ['MapServer', 'FeatureServer']:
                # Try layers 0-5
                for layer in range(6):
                    url = f"{base_url}/{service_type}/{layer}"
                    result = self.check_arcgis_endpoint(url)
                    if result:
                        print(f"    ✓ Found: {url} ({result['count']:,} features)")
                        found.append(result)

            # Also try the base as a service directory
            try:
                resp = requests.get(f"{base_url}?f=json", headers=HEADERS, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()

                    # Check for services or folders
                    if 'services' in data:
                        for svc in data['services'][:10]:  # Limit to first 10
                            svc_url = f"{base_url.rsplit('/rest', 1)[0]}/rest/services/{svc['name']}"
                            for service_type in ['MapServer', 'FeatureServer']:
                                url = f"{svc_url}/{service_type}/0"
                                result = self.check_arcgis_endpoint(url)
                                if result:
                                    print(f"    ✓ Found: {url} ({result['count']:,} features)")
                                    found.append(result)
            except:
                pass

        except Exception as e:
            pass

        return found

    def verify_state(self, state_code, state_data):
        """Verify all URLs for a state"""
        print(f"\n{'='*60}")
        print(f"Verifying {state_data['state']} ({state_code})")
        print(f"{'='*60}")

        urls = state_data.get('urls_to_check', [])
        found_services = []

        for base_url in urls:
            results = self.search_arcgis_services(base_url, state_code)
            found_services.extend(results)

        # Pick the best one (highest count)
        if found_services:
            best = max(found_services, key=lambda x: x['count'])
            print(f"\n  ✓ BEST: {best['url']}")
            print(f"    Features: {best['count']:,}")
            return best

        print(f"  ✗ No valid sources found")
        return None

def download_and_process(state_code, api_url, workers=50):
    """Download, convert, and upload a state"""
    print(f"\n{'='*60}")
    print(f"DEPLOYING {state_code}")
    print(f"{'='*60}")

    # Use existing mega_parallel script logic
    output_file = OUTPUT_DIR / "geojson" / f"parcels_{state_code.lower()}_statewide.geojson"
    pmtiles_file = OUTPUT_DIR / "pmtiles" / f"parcels_{state_code.lower()}_statewide.pmtiles"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    pmtiles_file.parent.mkdir(parents=True, exist_ok=True)

    # Get count
    try:
        resp = requests.get(
            f"{api_url}/query?where=1%3D1&returnCountOnly=true&f=json",
            headers=HEADERS,
            timeout=30
        )
        count = resp.json().get('count', 0)
    except:
        print(f"  ✗ Failed to get count")
        return False

    print(f"  Features: {count:,}")

    # Download in parallel
    print(f"  📥 Downloading...")

    all_features = []
    batch_size = 2000
    offsets = list(range(0, count, batch_size))

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
            resp = requests.get(f"{api_url}/query", params=params, headers=HEADERS, timeout=180)
            if resp.status_code == 200:
                return resp.json().get('features', [])
        except:
            pass
        return None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch, o): o for o in offsets}
        done = 0
        for future in as_completed(futures):
            features = future.result()
            if features:
                all_features.extend(features)
            done += 1
            if done % 50 == 0 or done == len(offsets):
                print(f"    [{done}/{len(offsets)}] {len(all_features):,} features")

    if not all_features:
        print(f"  ✗ No features downloaded")
        return False

    # Save GeoJSON
    print(f"  💾 Saving GeoJSON...")
    with open(output_file, 'w') as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f)

    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"    Saved: {size_mb:.1f} MB")

    # Convert to PMTiles
    print(f"  🔧 Converting to PMTiles...")
    cmd = [
        'tippecanoe', '-o', str(pmtiles_file),
        '-z', '15', '-Z', '10',
        '--drop-densest-as-needed',
        '--extend-zooms-if-still-dropping',
        '--force',
        '--layer', 'parcels',
        str(output_file)
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=3600)
        pm_size_mb = pmtiles_file.stat().st_size / (1024 * 1024)
        print(f"    Created: {pm_size_mb:.1f} MB")
    except Exception as e:
        print(f"  ✗ Conversion failed: {e}")
        return False

    # Upload to R2
    print(f"  ☁️  Uploading to R2...")
    cmd = [
        'aws', 's3', 'cp',
        str(pmtiles_file),
        f's3://{R2_BUCKET}/parcels/parcels_{state_code.lower()}_statewide.pmtiles',
        '--endpoint-url', R2_ENDPOINT
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
    except Exception as e:
        print(f"  ✗ Upload failed: {e}")
        return False

    # Verify
    cdn_url = f"{CDN_BASE}/parcels/parcels_{state_code.lower()}_statewide.pmtiles"
    try:
        result = subprocess.run(
            ['pmtiles', 'show', cdn_url],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f"  ✓ SUCCESS: {cdn_url}")
            # Clean up
            output_file.unlink()
            pmtiles_file.unlink()
            return True
    except:
        pass

    print(f"  ⚠ Uploaded but verification failed")
    return False

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-all', action='store_true', help='Verify all sources')
    parser.add_argument('--deploy-verified', action='store_true', help='Deploy verified sources')
    parser.add_argument('--state', type=str, help='Single state to process')
    args = parser.parse_args()

    # Load sources
    sources_file = DATA_DIR / "statewide_sources_verified.json"
    with open(sources_file) as f:
        data = json.load(f)

    sources = data['sources']

    if args.state:
        sources = {args.state.upper(): sources[args.state.upper()]}

    # Verify
    if args.verify_all:
        print("\n" + "="*80)
        print("  VERIFYING ALL STATEWIDE SOURCES")
        print("="*80)

        verifier = SourceVerifier()
        verified = {}

        for state_code, state_data in sorted(sources.items()):
            result = verifier.verify_state(state_code, state_data)
            if result:
                verified[state_code] = result

        # Save verified sources
        verified_file = DATA_DIR / "verified_statewide_apis.json"
        with open(verified_file, 'w') as f:
            json.dump({
                'verified_at': datetime.now().isoformat(),
                'sources': verified
            }, f, indent=2)

        print(f"\n✓ Verified {len(verified)}/{len(sources)} states")
        print(f"  Saved to: {verified_file}")

    # Deploy
    if args.deploy_verified:
        verified_file = DATA_DIR / "verified_statewide_apis.json"

        if not verified_file.exists():
            print("ERROR: Run --verify-all first!")
            return

        with open(verified_file) as f:
            verified_data = json.load(f)

        verified = verified_data['sources']

        print("\n" + "="*80)
        print(f"  DEPLOYING {len(verified)} VERIFIED STATES")
        print("="*80)

        success = []
        failed = []

        for state_code, source in sorted(verified.items()):
            try:
                if download_and_process(state_code, source['url'], workers=50):
                    success.append(state_code)
                else:
                    failed.append(state_code)
            except Exception as e:
                print(f"  ✗ {state_code} ERROR: {e}")
                failed.append(state_code)

        print("\n" + "="*80)
        print("  DEPLOYMENT SUMMARY")
        print("="*80)
        print(f"  Success: {len(success)} - {', '.join(success)}")
        print(f"  Failed: {len(failed)} - {', '.join(failed)}")
        print("="*80)

if __name__ == '__main__':
    main()
