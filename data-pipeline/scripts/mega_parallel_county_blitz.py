#!/usr/bin/env python3
"""
MEGA PARALLEL COUNTY BLITZ - Maximum Resource Utilization
==========================================================
Deploy ALL missing counties across USA using full system resources
- 32 parallel county searches
- Real web search for GIS portals
- Local AI endpoint extraction
- Auto-verification and deployment
"""

import requests
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse, urljoin
import re

# Configuration
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/output")
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

OLLAMA_HOST = "http://10.8.0.1:11434"
MODEL = "llama3.3:70b"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# ALL MISSING COUNTIES (extracted from MISSING_COUNTIES_NATIONWIDE.md)
MEGA_COUNTY_LIST = [
    # Tier 1: Mega Counties (500K+)
    {"name": "Fulton", "state": "GA", "population": 1100000, "city": "Atlanta"},
    {"name": "St. Louis County", "state": "MO", "population": 989000, "city": "St. Louis"},
    {"name": "Gwinnett", "state": "GA", "population": 957000, "city": "Atlanta"},
    {"name": "Multnomah", "state": "OR", "population": 815000, "city": "Portland"},
    {"name": "Oklahoma", "state": "OK", "population": 797000, "city": "Oklahoma City"},
    {"name": "Jefferson", "state": "KY", "population": 782000, "city": "Louisville"},
    {"name": "Cobb", "state": "GA", "population": 767000, "city": "Marietta"},
    {"name": "DeKalb", "state": "GA", "population": 764000, "city": "Decatur"},
    {"name": "Tulsa", "state": "OK", "population": 669000, "city": "Tulsa"},
    {"name": "Jefferson", "state": "AL", "population": 659000, "city": "Birmingham"},
    {"name": "Johnson", "state": "KS", "population": 610000, "city": "Overland Park"},
    {"name": "Washington", "state": "OR", "population": 606000, "city": "Hillsboro"},
    {"name": "Greenville", "state": "SC", "population": 525000, "city": "Greenville"},
    {"name": "Sedgwick", "state": "KS", "population": 523000, "city": "Wichita"},
    {"name": "Pinal", "state": "AZ", "population": 523000, "city": "Casa Grande"},
    {"name": "Kane", "state": "IL", "population": 516000, "city": "Aurora"},

    # Tier 2: Major Metros (250K-500K)
    {"name": "Charleston", "state": "SC", "population": 408000, "city": "Charleston"},
    {"name": "Richland", "state": "SC", "population": 416000, "city": "Columbia"},
    {"name": "Mobile", "state": "AL", "population": 414000, "city": "Mobile"},
    {"name": "St. Charles", "state": "MO", "population": 407000, "city": "St. Charles"},
    {"name": "Madison", "state": "AL", "population": 388000, "city": "Huntsville"},
    {"name": "Clackamas", "state": "OR", "population": 421000, "city": "Oregon City"},
    {"name": "Lane", "state": "OR", "population": 382000, "city": "Eugene"},
    {"name": "Horry", "state": "SC", "population": 351000, "city": "Myrtle Beach"},
    {"name": "Marion", "state": "OR", "population": 345000, "city": "Salem"},
    {"name": "Spartanburg", "state": "SC", "population": 327000, "city": "Spartanburg"},
    {"name": "Fayette", "state": "KY", "population": 323000, "city": "Lexington"},
    {"name": "Lancaster", "state": "NE", "population": 322000, "city": "Lincoln"},
    {"name": "Clayton", "state": "GA", "population": 297000, "city": "Jonesboro"},
    {"name": "Cleveland", "state": "OK", "population": 295000, "city": "Norman"},
    {"name": "Ingham", "state": "MI", "population": 284000, "city": "Lansing"},
    {"name": "Winnebago", "state": "IL", "population": 285000, "city": "Rockford"},
    {"name": "St. Clair", "state": "IL", "population": 257000, "city": "Belleville"},
    {"name": "Madison", "state": "IL", "population": 265000, "city": "Edwardsville"},
    {"name": "St. Tammany", "state": "LA", "population": 265000, "city": "Slidell"},
    {"name": "Clay", "state": "MO", "population": 253000, "city": "Liberty"},
    {"name": "Hinds", "state": "MS", "population": 230000, "city": "Jackson"},
    {"name": "Montgomery", "state": "AL", "population": 228000, "city": "Montgomery"},
    {"name": "Jefferson", "state": "MO", "population": 226000, "city": "Hillsboro"},
    {"name": "Shelby", "state": "AL", "population": 223000, "city": "Columbiana"},
    {"name": "Yuma", "state": "AZ", "population": 213000, "city": "Yuma"},
    {"name": "Mohave", "state": "AZ", "population": 214000, "city": "Kingman"},
    {"name": "Hall", "state": "GA", "population": 208000, "city": "Gainesville"},
    {"name": "Harrison", "state": "MS", "population": 208000, "city": "Gulfport"},
    {"name": "Champaign", "state": "IL", "population": 209000, "city": "Urbana"},

    # Tier 3: Regional (100K-250K)
    {"name": "Sarpy", "state": "NE", "population": 190000, "city": "Papillion"},
    {"name": "Saginaw", "state": "MI", "population": 190000, "city": "Saginaw"},
    {"name": "DeSoto", "state": "MS", "population": 185000, "city": "Southaven"},
    {"name": "Shawnee", "state": "KS", "population": 178000, "city": "Topeka"},
    {"name": "Kenton", "state": "KY", "population": 169000, "city": "Covington"},
    {"name": "Wyandotte", "state": "KS", "population": 165000, "city": "Kansas City"},
    {"name": "Jackson", "state": "MI", "population": 160000, "city": "Jackson"},
    {"name": "Rankin", "state": "MS", "population": 157000, "city": "Brandon"},
    {"name": "Berrien", "state": "MI", "population": 154000, "city": "St. Joseph"},
    {"name": "Canadian", "state": "OK", "population": 154000, "city": "Yukon"},
    {"name": "Livingston", "state": "LA", "population": 142000, "city": "Livingston"},
    {"name": "Boone", "state": "KY", "population": 135000, "city": "Florence"},
    {"name": "Warren", "state": "KY", "population": 134000, "city": "Bowling Green"},
    {"name": "Tangipahoa", "state": "LA", "population": 133000, "city": "Hammond"},
    {"name": "Rapides", "state": "LA", "population": 130000, "city": "Alexandria"},
    {"name": "Bossier", "state": "LA", "population": 128000, "city": "Bossier City"},
    {"name": "Cochise", "state": "AZ", "population": 126000, "city": "Sierra Vista"},
    {"name": "Douglas", "state": "KS", "population": 122000, "city": "Lawrence"},
    {"name": "Comanche", "state": "OK", "population": 121000, "city": "Lawton"},
    {"name": "Navajo", "state": "AZ", "population": 112000, "city": "Show Low"},
    {"name": "Madison", "state": "MS", "population": 109000, "city": "Canton"},
    {"name": "Platte", "state": "MO", "population": 106000, "city": "Platte City"},
    {"name": "Bay", "state": "MI", "population": 103000, "city": "Bay City"},
]

def web_search_gis_portal(county_name, state_code):
    """Use DuckDuckGo-like search via requests to find GIS portal"""
    try:
        # Try common patterns first (faster than full web search)
        county_slug = county_name.lower().replace(" ", "")
        patterns = [
            f"https://gis.{county_slug}county{state_code.lower()}.gov",
            f"https://gis.{county_slug}co{state_code.lower()}.gov",
            f"https://maps.{county_slug}county.gov",
            f"https://gis.{county_slug}.gov",
            f"https://{county_slug}gis.com",
            f"https://data-{county_slug}gis.opendata.arcgis.com",
            f"https://gcgis-{county_slug}county{state_code.lower()}.hub.arcgis.com",
        ]

        for url in patterns:
            try:
                resp = requests.head(url, headers=HEADERS, timeout=5, allow_redirects=True)
                if resp.status_code == 200:
                    return url
            except:
                continue

    except:
        pass

    return None

def download_portal_html(url):
    """Download GIS portal page"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code == 200 and len(resp.text) > 1000:
            return resp.text
    except:
        pass
    return None

def extract_endpoints_with_ai(html, county_name, state):
    """Use local AI to extract REST endpoints from portal HTML"""
    html_sample = html[:50000]  # Limit to 50K chars

    prompt = f"""Analyze this HTML from {county_name} County, {state} GIS portal.

Find ArcGIS REST API endpoints for parcel/property/tax data. Look for:
1. URLs containing "/arcgis/rest/services/" or "/server/rest/services/"
2. FeatureServer endpoints (preferred) or MapServer
3. Layer numbers (e.g., /0, /1, /2)
4. Services with names like: Parcels, Property, Tax, Cadastral, Land, Assessment

HTML Content:
{html_sample}

Return ONLY valid JSON (no markdown):
{{
  "endpoints": [
    {{"url": "complete_url_with_layer", "type": "FeatureServer or MapServer", "layer_name": "name"}},
    ...
  ]
}}

If none found: {{"endpoints": []}}"""

    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 800}
            },
            timeout=90
        )

        if resp.status_code == 200:
            response_text = resp.json().get('response', '').strip()

            # Extract JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                return []

            result = json.loads(json_str)
            return result.get("endpoints", [])
    except:
        pass

    return []

def verify_endpoint(url):
    """Quick verification - check if endpoint responds with count"""
    try:
        # Handle both FeatureServer and MapServer
        test_url = url.rstrip('/') + '/query' if not url.endswith('/query') else url

        resp = requests.get(
            test_url,
            params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
            headers=HEADERS,
            timeout=20
        )

        if resp.status_code == 200:
            data = resp.json()
            if 'count' in data and data['count'] > 0:
                return True, data['count']
            elif 'error' in data:
                return False, f"API Error: {data['error'].get('message', 'Unknown')[:50]}"

        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)[:50]

def quick_download_and_deploy(county_info, endpoint_url, feature_count):
    """Quick download and deploy a county"""
    county_name = county_info['name']
    state = county_info['state']
    source_id = f"{state.lower()}_{county_name.lower().replace(' ', '_')}"

    # Check if already exists
    try:
        resp = requests.head(f"{CDN_BASE}/parcels/parcels_{source_id}.pmtiles", timeout=10)
        if resp.status_code == 200:
            return {"status": "skip", "reason": "already exists"}
    except:
        pass

    output_file = OUTPUT_DIR / "geojson" / f"parcels_{source_id}.geojson"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"  📥 Downloading {county_name}, {state} ({feature_count:,} parcels)")

    # Download in parallel
    all_features = []
    batch_size = 2000
    offsets = list(range(0, min(feature_count, 500000), batch_size))  # Cap at 500K for speed

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
                return resp.json().get('features', [])
        except:
            pass
        return None

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(fetch, o): o for o in offsets}
        for future in as_completed(futures):
            features = future.result()
            if features:
                all_features.extend(features)

    if len(all_features) < 100:
        return {"status": "fail", "reason": f"only {len(all_features)} features downloaded"}

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
        ], check=True, capture_output=True, timeout=1800)
    except:
        return {"status": "fail", "reason": "tippecanoe failed"}

    # Upload to R2
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
            # Clean up
            output_file.unlink()
            pmtiles_path.unlink()

            return {
                "status": "success",
                "source_id": source_id,
                "features": len(all_features),
                "url": cdn_url
            }
    except:
        pass

    return {"status": "fail", "reason": "upload failed"}

def process_county(county_info):
    """Process a single county: find portal → extract endpoints → verify → deploy"""
    county_name = county_info['name']
    state = county_info['state']

    print(f"\n🔍 [{state}] {county_name} County ({county_info['population']:,} pop)")

    # 1. Find GIS portal
    portal_url = web_search_gis_portal(county_name, state)
    if not portal_url:
        return {"county": f"{county_name}, {state}", "status": "no_portal"}

    print(f"  ✓ Portal: {portal_url}")

    # 2. Download portal HTML
    html = download_portal_html(portal_url)
    if not html:
        return {"county": f"{county_name}, {state}", "status": "download_failed"}

    # 3. Extract endpoints with AI
    endpoints = extract_endpoints_with_ai(html, county_name, state)
    if not endpoints:
        return {"county": f"{county_name}, {state}", "status": "no_endpoints"}

    print(f"  📍 Found {len(endpoints)} potential endpoints")

    # 4. Verify and deploy first working endpoint
    for ep in endpoints:
        url = ep.get('url', '').strip()
        if not url or 'rest/services' not in url:
            continue

        works, result = verify_endpoint(url)
        if works:
            print(f"  ✓ VERIFIED: {url} ({result:,} features)")

            # Auto-deploy
            deploy_result = quick_download_and_deploy(county_info, url, result)
            if deploy_result['status'] == 'success':
                print(f"  🚀 DEPLOYED: {deploy_result['source_id']}")
                return {
                    "county": f"{county_name}, {state}",
                    "status": "deployed",
                    "endpoint": url,
                    "features": deploy_result['features'],
                    "source_id": deploy_result['source_id']
                }
            else:
                return {
                    "county": f"{county_name}, {state}",
                    "status": "deploy_failed",
                    "endpoint": url,
                    "reason": deploy_result.get('reason')
                }

    return {"county": f"{county_name}, {state}", "status": "verification_failed"}

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=32, help='Parallel county workers (default: 32)')
    parser.add_argument('--limit', type=int, help='Limit to first N counties')
    parser.add_argument('--tier', type=int, help='Only process tier 1 (first 16), tier 2 (next 30), etc.')
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
    print("  🚀 MEGA PARALLEL COUNTY BLITZ")
    print(f"  Counties to process: {len(counties)}")
    print(f"  Parallel workers: {args.workers}")
    print("="*80)

    results = {
        "deployed": [],
        "failed": [],
        "no_portal": [],
        "no_endpoints": [],
    }

    # Process all counties in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_county, county): county for county in counties}

        for future in as_completed(futures):
            try:
                result = future.result()
                status = result.get('status')

                if status == 'deployed':
                    results['deployed'].append(result)
                elif status == 'no_portal':
                    results['no_portal'].append(result)
                elif status == 'no_endpoints':
                    results['no_endpoints'].append(result)
                else:
                    results['failed'].append(result)

            except Exception as e:
                print(f"  ✗ ERROR: {e}")

    # Save results
    output_file = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/mega_blitz_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_processed": len(counties),
            "deployed": len(results['deployed']),
            "summary": results
        }, f, indent=2)

    print("\n" + "="*80)
    print(f"  ✅ DEPLOYED: {len(results['deployed'])}")
    print(f"  ❌ NO PORTAL: {len(results['no_portal'])}")
    print(f"  ⚠️  NO ENDPOINTS: {len(results['no_endpoints'])}")
    print(f"  ✗ FAILED: {len(results['failed'])}")
    print(f"\n  Results saved: {output_file}")
    print("="*80)

    if results['deployed']:
        print("\n🎉 SUCCESSFULLY DEPLOYED:")
        for r in results['deployed']:
            print(f"  • {r['county']} - {r['features']:,} parcels ({r['source_id']})")

if __name__ == '__main__':
    main()
