#!/usr/bin/env python3
"""
HITD Maps - AI-Powered County Source Finder & Mega Deployer
============================================================
Use Ollama AI to find ArcGIS REST APIs for EVERY missing county,
then deploy max parallel download/process/upload.

Target: ~1000+ counties across 14 partial states
System: 48 cores, 471 GB RAM

Run: python3 ai_county_finder_deployer.py --find-all-counties
     python3 ai_county_finder_deployer.py --deploy-all
"""

import asyncio
import aiohttp
import json
import os
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime
import time
import requests

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

HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Target states and their major missing counties
TARGET_COUNTIES = {
    "GA": [
        "Fulton", "DeKalb", "Gwinnett", "Cobb", "Clayton", "Cherokee", "Forsyth",
        "Henry", "Hall", "Paulding", "Columbia", "Muscogee", "Bibb", "Clarke",
        # Top 30 counties by population
        "Houston", "Carroll", "Whitfield", "Lowndes", "Bartow", "Richmond",
        "Coweta", "Fayette", "Floyd", "Douglas", "Newton", "Dougherty", "Walton",
        "Rockdale", "Bulloch", "Coffee"
    ],
    "IL": [
        "Cook", "DuPage", "Lake", "Will", "Kane", "McHenry", "Madison", "St. Clair",
        "Sangamon", "Winnebago", "Champaign", "McLean", "Peoria", "Rock Island",
        "Tazewell", "Macon", "Vermilion", "Adams", "LaSalle", "Kankakee"
    ],
    "MI": [
        "Wayne", "Oakland", "Macomb", "Kent", "Genesee", "Washtenaw", "Ottawa",
        "Ingham", "Kalamazoo", "Livingston", "St. Clair", "Saginaw", "Muskegon",
        "Monroe", "Berrien", "Jackson", "Allegan", "Eaton", "Bay", "Calhoun"
    ],
    "MO": [
        "St. Louis City", "St. Louis", "Jackson", "St. Charles", "Greene",
        "Clay", "Jefferson", "Boone", "Cass", "Franklin", "Platte", "Jasper",
        "Cape Girardeau", "Christian", "Buchanan", "Scott", "Pettis", "Cole"
    ],
    "AL": [
        "Jefferson", "Mobile", "Madison", "Montgomery", "Shelby", "Tuscaloosa",
        "Baldwin", "Lee", "Calhoun", "Lauderdale", "Morgan", "Etowah", "Houston",
        "Marshall", "Limestone"
    ],
    "LA": [
        "East Baton Rouge", "Jefferson", "Orleans", "St. Tammany", "Lafayette",
        "Caddo", "Calcasieu", "Livingston", "Ouachita", "Rapides", "Terrebonne",
        "St. Bernard", "Bossier", "Ascension", "St. Landry"
    ],
    "OK": [
        "Oklahoma", "Tulsa", "Cleveland", "Canadian", "Comanche", "Rogers",
        "Wagoner", "Creek", "Pottawatomie", "Payne", "Garfield", "Muskogee"
    ],
    "OR": [
        "Multnomah", "Washington", "Clackamas", "Lane", "Marion", "Jackson",
        "Deschutes", "Linn", "Douglas", "Yamhill", "Benton", "Umatilla"
    ],
    "SC": [
        "Greenville", "Charleston", "Richland", "Spartanburg", "Horry",
        "Lexington", "Anderson", "York", "Beaufort", "Berkeley", "Aiken"
    ],
    "AZ": [
        "Maricopa", "Pima", "Pinal", "Yavapai", "Mohave", "Yuma", "Coconino",
        "Cochise", "Navajo", "Apache", "Gila", "La Paz", "Graham", "Greenlee", "Santa Cruz"
    ],
    "KS": [
        "Johnson", "Sedgwick", "Shawnee", "Wyandotte", "Douglas", "Leavenworth",
        "Riley", "Reno", "Saline", "Butler"
    ],
    "KY": [
        "Jefferson", "Fayette", "Kenton", "Boone", "Warren", "Hardin",
        "Daviess", "Campbell", "Madison", "McCracken"
    ],
    "MS": [
        "Hinds", "Harrison", "DeSoto", "Rankin", "Jackson", "Madison",
        "Lauderdale", "Lee", "Forrest", "Jones"
    ],
    "SD": [
        "Minnehaha", "Pennington", "Lincoln", "Brown", "Brookings", "Codington",
        "Lawrence", "Yankton", "Meade", "Beadle"
    ]
}

class AICountyFinder:
    """Use Ollama to find county parcel APIs"""

    def __init__(self):
        self.ollama_url = f"{OLLAMA_HOST}/api/generate"
        self.model = "llama3.3:70b"

    async def find_county_source(self, state_code, county_name):
        """Find ArcGIS REST API for a specific county"""

        prompt = f"""Find the ArcGIS REST API FeatureServer endpoint for {county_name} County, {state_code} parcel/cadastral/property data.

Search for:
- "{county_name} County {state_code} GIS parcels"
- "{county_name} County assessor GIS"
- "{county_name} County property data ArcGIS"

Look for URLs like:
https://gis.{county_name.lower()}county.gov/arcgis/rest/services/.../FeatureServer/0
https://maps.{county_name.lower()}co.{state_code.lower()}.gov/arcgis/rest/services/.../FeatureServer/0

Return ONLY a JSON object:
{{
  "found": true/false,
  "api_url": "https://...FeatureServer/0" or null,
  "confidence": "high/medium/low",
  "estimated_records": 50000
}}"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1, "num_predict": 512}
                    },
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as resp:
                    result = await resp.json()
                    response_text = result.get("response", "")

                    # Extract JSON
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    if start >= 0 and end > start:
                        try:
                            data = json.loads(response_text[start:end])
                            if data.get('found') and data.get('api_url'):
                                return data
                        except:
                            pass

        except Exception as e:
            pass

        return {"found": False}

class CountyProcessor:
    """Process counties in parallel"""

    def __init__(self, max_download_workers=24, max_process_workers=16):
        self.max_download_workers = max_download_workers
        self.max_process_workers = max_process_workers

    def download_county(self, state_code, county_name, api_url, batch_workers=50):
        """Download one county"""
        county_id = f"{state_code.lower()}_{county_name.lower().replace(' ', '_')}"

        print(f"\n📥 {state_code} - {county_name}")

        # Get count
        try:
            resp = requests.get(
                f"{api_url}/query?where=1%3D1&returnCountOnly=true&f=json",
                headers=HEADERS,
                timeout=30
            )
            count = resp.json().get('count', 0)
        except:
            return None

        if count < 100:  # Skip if too few
            print(f"  ⚠ Only {count} features - skipping")
            return None

        print(f"  Features: {count:,}")

        # Download
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

        with ThreadPoolExecutor(max_workers=batch_workers) as executor:
            futures = {executor.submit(fetch, o): o for o in offsets}
            done = 0
            for future in as_completed(futures):
                features = future.result()
                if features:
                    all_features.extend(features)
                done += 1

        if not all_features:
            return None

        # Save
        output_file = OUTPUT_DIR / "geojson" / f"parcels_{county_id}.geojson"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump({"type": "FeatureCollection", "features": all_features}, f)

        print(f"  ✓ Saved {len(all_features):,} features")
        return output_file

    def process_and_upload(self, geojson_path):
        """Convert to PMTiles and upload"""
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
        except:
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
                # Clean up
                geojson_path.unlink()
                pmtiles_path.unlink()
                return True
        except:
            pass

        return False

async def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--find-all-counties', action='store_true')
    parser.add_argument('--deploy-all', action='store_true')
    parser.add_argument('--state', type=str, help='Single state')
    parser.add_argument('--limit', type=int, default=0, help='Limit counties per state')
    args = parser.parse_args()

    counties = TARGET_COUNTIES
    if args.state:
        counties = {args.state.upper(): counties[args.state.upper()]}

    # Find sources with AI
    if args.find_all_counties:
        print("\n" + "="*80)
        print("  AI COUNTY SOURCE FINDER")
        print(f"  Target: {sum(len(v) for v in counties.values())} counties")
        print("="*80)

        finder = AICountyFinder()
        found_sources = {}

        for state_code, county_list in sorted(counties.items()):
            print(f"\n🤖 Searching {state_code} ({len(county_list)} counties)...")

            state_found = {}
            limit = args.limit if args.limit > 0 else len(county_list)

            for county_name in county_list[:limit]:
                result = await finder.find_county_source(state_code, county_name)

                if result.get('found'):
                    state_found[county_name] = result
                    print(f"  ✓ {county_name}: {result.get('api_url')[:60]}...")
                else:
                    print(f"  ✗ {county_name}: Not found")

                await asyncio.sleep(0.5)  # Rate limit

            found_sources[state_code] = state_found

        # Save
        output_file = DATA_DIR / "ai_found_county_sources.json"
        with open(output_file, 'w') as f:
            json.dump({
                'found_at': datetime.now().isoformat(),
                'total_counties': sum(len(v) for v in found_sources.values()),
                'sources': found_sources
            }, f, indent=2)

        print(f"\n✓ Found {sum(len(v) for v in found_sources.values())} counties")
        print(f"  Saved to: {output_file}")

    # Deploy
    if args.deploy_all:
        sources_file = DATA_DIR / "ai_found_county_sources.json"

        if not sources_file.exists():
            print("ERROR: Run --find-all-counties first!")
            return

        with open(sources_file) as f:
            data = json.load(f)

        all_counties = []
        for state_code, counties_dict in data['sources'].items():
            for county_name, county_data in counties_dict.items():
                all_counties.append((state_code, county_name, county_data['api_url']))

        print("\n" + "="*80)
        print(f"  DEPLOYING {len(all_counties)} COUNTIES")
        print("="*80)

        processor = CountyProcessor()
        success = []
        failed = []

        # Download all in parallel
        print("\n📥 DOWNLOADING ALL COUNTIES...")
        with ThreadPoolExecutor(max_workers=24) as executor:
            futures = {
                executor.submit(processor.download_county, sc, cn, url): (sc, cn)
                for sc, cn, url in all_counties
            }

            geojson_files = []
            for future in as_completed(futures):
                result = future.result()
                if result:
                    geojson_files.append(result)

        print(f"\n✓ Downloaded {len(geojson_files)} counties")

        # Process and upload all
        print("\n🔧 PROCESSING & UPLOADING...")
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = {
                executor.submit(processor.process_and_upload, gf): gf
                for gf in geojson_files
            }

            for future in as_completed(futures):
                if future.result():
                    success.append(future)
                else:
                    failed.append(future)

        print("\n" + "="*80)
        print("  COMPLETE!")
        print(f"  Success: {len(success)}")
        print(f"  Failed: {len(failed)}")
        print("="*80)

if __name__ == '__main__':
    asyncio.run(main())
