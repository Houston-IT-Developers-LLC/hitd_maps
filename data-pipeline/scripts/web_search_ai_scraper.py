#!/usr/bin/env python3
"""
HITD Maps - Web Search + AI County Scraper
===========================================
1. Use web search to find real county GIS portals
2. Use Ollama AI to extract ArcGIS REST endpoints from those portals
3. Verify endpoints work
4. Deploy parallel scraping

This fixes the hallucination issue by finding REAL sources first.
"""

import asyncio
import aiohttp
import json
import os
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time
import requests
import re

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
OUTPUT_DIR = SCRIPT_DIR.parent / "output"

# R2 Config
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

# Ollama
OLLAMA_HOST = "http://10.8.0.1:11434"
OLLAMA_MODEL = "llama3.3:70b"

HEADERS = {'User-Agent': 'Mozilla/5.0'}

# High-priority counties to target
PRIORITY_COUNTIES = {
    "GA": ["Fulton", "Gwinnett", "Cobb", "DeKalb", "Clayton", "Cherokee", "Forsyth", "Henry"],
    "IL": ["Cook", "DuPage", "Lake", "Will", "Kane", "McHenry", "Madison", "St. Clair"],
    "MI": ["Wayne", "Oakland", "Macomb", "Kent", "Genesee", "Washtenaw", "Ottawa", "Ingham"],
    "MO": ["St. Louis", "Jackson", "St. Charles", "Greene", "Clay", "Jefferson", "Boone"],
    "AL": ["Jefferson", "Mobile", "Madison", "Montgomery", "Shelby", "Tuscaloosa", "Baldwin"],
    "LA": ["East Baton Rouge", "Jefferson", "Orleans", "St. Tammany", "Lafayette", "Caddo"],
    "OK": ["Oklahoma", "Tulsa", "Cleveland", "Canadian", "Comanche", "Rogers"],
    "OR": ["Multnomah", "Washington", "Clackamas", "Lane", "Marion", "Jackson"],
    "SC": ["Greenville", "Charleston", "Richland", "Spartanburg", "Horry", "Lexington"],
    "AZ": ["Maricopa", "Pima", "Pinal", "Yavapai", "Mohave", "Yuma", "Coconino"],
    "KS": ["Johnson", "Sedgwick", "Shawnee", "Wyandotte", "Douglas"],
    "KY": ["Jefferson", "Fayette", "Kenton", "Boone", "Warren", "Hardin"],
    "MS": ["Hinds", "Harrison", "DeSoto", "Rankin", "Jackson", "Madison"],
    "MN": ["Hennepin", "Ramsey", "Dakota", "Anoka", "Washington", "St. Louis"]
}

class WebSearchSourceFinder:
    """Find county GIS portals using actual web search"""

    async def search_county_gis(self, state_code, county_name):
        """Search for county GIS portal"""

        print(f"  🔍 Searching web for {county_name} County, {state_code}...")

        # Common URL patterns to try first (fast check)
        quick_patterns = [
            f"https://gis.{county_name.lower()}county{state_code.lower()}.gov",
            f"https://maps.{county_name.lower()}county.{state_code.lower()}.us",
            f"https://gis.{county_name.lower()}co.{state_code.lower()}.gov",
            f"https://{county_name.lower()}county.gov/gis",
            f"https://www.{county_name.lower()}county.gov/departments/gis",
        ]

        for url in quick_patterns:
            try:
                resp = requests.head(url, timeout=5, allow_redirects=True)
                if resp.status_code == 200:
                    print(f"    ✓ Found portal: {url}")
                    return {"portal_url": url, "method": "pattern_match"}
            except:
                pass

        # If patterns fail, search DuckDuckGo
        try:
            search_query = f"{county_name} County {state_code} GIS parcels ArcGIS"

            # Use requests to search (simple approach)
            search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(search_query)}"
            resp = requests.get(search_url, headers=HEADERS, timeout=10)

            if resp.status_code == 200:
                # Extract URLs from results
                urls = re.findall(r'uddg=([^"&]+)', resp.text)
                for encoded_url in urls[:5]:  # Check first 5
                    try:
                        url = requests.utils.unquote(encoded_url)
                        if any(kw in url.lower() for kw in ['gis', 'maps', 'arcgis', county_name.lower()]):
                            print(f"    ✓ Found via search: {url}")
                            return {"portal_url": url, "method": "web_search"}
                    except:
                        pass
        except Exception as e:
            print(f"    ⚠ Search failed: {e}")

        return None

    async def extract_arcgis_endpoint(self, portal_url, state_code, county_name):
        """Use Ollama AI to extract ArcGIS REST endpoint from portal"""

        print(f"    🤖 AI extracting endpoint from {portal_url[:50]}...")

        prompt = f"""You are analyzing the GIS portal for {county_name} County, {state_code}.
Portal URL: {portal_url}

Find the ArcGIS REST API FeatureServer endpoint for PARCELS.

Common patterns:
- /arcgis/rest/services/.../FeatureServer/0
- /arcgis/rest/services/.../MapServer/0

Look for keywords: parcel, property, cadastral, tax, assessor

Return ONLY a JSON object:
{{
  "found": true/false,
  "endpoint": "https://full.url.here/FeatureServer/0" or null,
  "confidence": "high/medium/low"
}}"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1, "num_predict": 256}
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    result = await resp.json()
                    response_text = result.get("response", "")

                    # Extract JSON
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    if start >= 0 and end > start:
                        try:
                            data = json.loads(response_text[start:end])
                            if data.get('found') and data.get('endpoint'):
                                return data['endpoint']
                        except:
                            pass
        except:
            pass

        # If AI fails, try to scrape the portal directly for ArcGIS REST URLs
        try:
            resp = requests.get(portal_url, timeout=10, headers=HEADERS)
            if resp.status_code == 200:
                # Look for ArcGIS REST URLs
                matches = re.findall(r'https?://[^"\s]+/arcgis/rest/services/[^"\s]+/(?:FeatureServer|MapServer)/\d+', resp.text)
                for match in matches:
                    if any(kw in match.lower() for kw in ['parcel', 'property', 'cadastral', 'tax']):
                        print(f"    ✓ Found via scraping: {match}")
                        return match
        except:
            pass

        return None

    def verify_endpoint(self, url):
        """Verify ArcGIS endpoint actually has parcels"""

        print(f"    ✓ Verifying {url[:60]}...")

        try:
            # Get service info
            resp = requests.get(f"{url}?f=json", headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                return None

            data = resp.json()
            if 'error' in data:
                return None

            # Check if it looks like parcels
            name = data.get('name', '').lower()
            desc = data.get('description', '').lower()

            if not any(kw in name or kw in desc for kw in ['parcel', 'property', 'cadastral', 'tax']):
                print(f"      ⚠ Doesn't look like parcels")
                return None

            # Get count
            count_resp = requests.get(
                f"{url}/query?where=1%3D1&returnCountOnly=true&f=json",
                headers=HEADERS,
                timeout=15
            )

            if count_resp.status_code == 200:
                count = count_resp.json().get('count', 0)
                if count > 1000:  # Must have at least 1k parcels
                    print(f"      ✓ VERIFIED: {count:,} parcels")
                    return {
                        'url': url,
                        'count': count,
                        'name': data.get('name'),
                        'verified': True
                    }
                else:
                    print(f"      ⚠ Only {count} parcels - too few")
        except Exception as e:
            print(f"      ✗ Verification failed: {e}")

        return None

class ParallelScraper:
    """Scrape, process, upload in parallel"""

    def __init__(self):
        pass

    def download_county(self, state_code, county_name, api_url, count):
        """Download one county"""

        county_id = f"{state_code.lower()}_{county_name.lower().replace(' ', '_')}"
        output_file = OUTPUT_DIR / "geojson" / f"parcels_{county_id}.geojson"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n📥 Downloading {state_code} - {county_name} ({count:,} parcels)")

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

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(fetch, o): o for o in offsets}
            done = 0
            for future in as_completed(futures):
                features = future.result()
                if features:
                    all_features.extend(features)
                done += 1
                if done % 20 == 0:
                    print(f"  [{done}/{len(offsets)}] {len(all_features):,} features")

        if not all_features:
            return None

        # Save
        with open(output_file, 'w') as f:
            json.dump({"type": "FeatureCollection", "features": all_features}, f)

        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"  ✓ Saved {len(all_features):,} features ({size_mb:.1f} MB)")

        return output_file

    def process_and_upload(self, geojson_path):
        """Convert and upload one file"""

        pmtiles_path = OUTPUT_DIR / "pmtiles" / f"{geojson_path.stem}.pmtiles"
        pmtiles_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert
        try:
            cmd = [
                'tippecanoe', '-o', str(pmtiles_path),
                '-z', '15', '-Z', '10',
                '--drop-densest-as-needed',
                '--extend-zooms-if-still-dropping',
                '--force', '--layer', 'parcels',
                str(geojson_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True, timeout=1800)
        except Exception as e:
            print(f"  ✗ Convert failed: {e}")
            return False

        # Upload
        try:
            cmd = [
                'aws', 's3', 'cp', str(pmtiles_path),
                f's3://{R2_BUCKET}/parcels/{pmtiles_path.name}',
                '--endpoint-url', R2_ENDPOINT
            ]
            subprocess.run(cmd, check=True, capture_output=True, timeout=600)

            # Verify
            cdn_url = f"{CDN_BASE}/parcels/{pmtiles_path.name}"
            result = subprocess.run(
                ['pmtiles', 'show', cdn_url],
                capture_output=True,
                timeout=60
            )

            if result.returncode == 0:
                print(f"  ✓ Uploaded: {cdn_url}")
                # Clean up
                geojson_path.unlink()
                pmtiles_path.unlink()
                return True
        except Exception as e:
            print(f"  ✗ Upload failed: {e}")

        return False

async def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--find-and-verify', action='store_true', help='Find and verify all sources')
    parser.add_argument('--deploy', action='store_true', help='Deploy scraping')
    parser.add_argument('--state', type=str, help='Single state')
    parser.add_argument('--workers', type=int, default=24, help='Download workers')
    args = parser.parse_args()

    counties = PRIORITY_COUNTIES
    if args.state:
        counties = {args.state.upper(): counties.get(args.state.upper(), [])}

    # Phase 1: Find and verify
    if args.find_and_verify or args.deploy:
        print("\n" + "="*80)
        print("  WEB SEARCH + AI SOURCE FINDER")
        print(f"  Target: {sum(len(v) for v in counties.values())} high-priority counties")
        print("="*80)

        finder = WebSearchSourceFinder()
        verified_sources = {}

        for state_code, county_list in sorted(counties.items()):
            print(f"\n🔍 {state_code} ({len(county_list)} counties)")

            state_sources = {}

            for county_name in county_list:
                # Step 1: Find portal
                portal_result = await finder.search_county_gis(state_code, county_name)

                if not portal_result:
                    print(f"  ✗ {county_name}: No portal found")
                    continue

                # Step 2: Extract endpoint
                endpoint = await finder.extract_arcgis_endpoint(
                    portal_result['portal_url'],
                    state_code,
                    county_name
                )

                if not endpoint:
                    print(f"  ✗ {county_name}: No endpoint found")
                    continue

                # Step 3: Verify
                verified = finder.verify_endpoint(endpoint)

                if verified:
                    state_sources[county_name] = verified
                    print(f"  ✓ {county_name}: READY ({verified['count']:,} parcels)")
                else:
                    print(f"  ✗ {county_name}: Verification failed")

                await asyncio.sleep(1)  # Rate limit

            if state_sources:
                verified_sources[state_code] = state_sources

        # Save
        output_file = DATA_DIR / "verified_county_sources.json"
        with open(output_file, 'w') as f:
            json.dump({
                'verified_at': datetime.now().isoformat(),
                'total_counties': sum(len(v) for v in verified_sources.values()),
                'sources': verified_sources
            }, f, indent=2)

        total = sum(len(v) for v in verified_sources.values())
        print(f"\n✓ VERIFIED {total} counties")
        print(f"  Saved to: {output_file}")

        if not args.deploy:
            return

    # Phase 2: Deploy scraping
    if args.deploy:
        sources_file = DATA_DIR / "verified_county_sources.json"

        if not sources_file.exists():
            print("ERROR: Run --find-and-verify first!")
            return

        with open(sources_file) as f:
            data = json.load(f)

        print("\n" + "="*80)
        print(f"  DEPLOYING {data['total_counties']} VERIFIED COUNTIES")
        print("="*80)

        scraper = ParallelScraper()

        # Collect all tasks
        tasks = []
        for state_code, counties_dict in data['sources'].items():
            for county_name, county_data in counties_dict.items():
                tasks.append((state_code, county_name, county_data['url'], county_data['count']))

        # Download all in parallel
        print(f"\n📥 Downloading {len(tasks)} counties with {args.workers} workers...")

        downloaded = []
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(scraper.download_county, sc, cn, url, count): (sc, cn)
                for sc, cn, url, count in tasks
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    downloaded.append(result)

        print(f"\n✓ Downloaded {len(downloaded)} files")

        # Process and upload
        print(f"\n🔧 Processing and uploading...")

        success = 0
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = {executor.submit(scraper.process_and_upload, gf): gf for gf in downloaded}

            for future in as_completed(futures):
                if future.result():
                    success += 1

        print("\n" + "="*80)
        print(f"  ✓ COMPLETE: {success}/{len(downloaded)} uploaded successfully")
        print("="*80)

if __name__ == '__main__':
    asyncio.run(main())
