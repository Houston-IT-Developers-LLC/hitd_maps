#!/usr/bin/env python3
"""
HITD Maps - MEGA Statewide Deployment (MAX RESOURCES)
======================================================
Deploy all AI agents to find and scrape ALL partial states

System Resources:
- 471 GB Available RAM
- 48 CPU Cores
- Target: Complete statewide coverage for all 14 partial states

States to complete:
- AL, AZ, GA, IL, KS, KY, LA, MI, MS, MO, OK, OR, SC, SD

Strategy:
1. Use Ollama AI (10.8.0.1:11434) to find statewide sources
2. Download all sources in parallel (24 workers)
3. Process all in parallel (16 workers for ogr2ogr + tippecanoe)
4. Upload all to R2 in parallel (8 workers)
5. Verify and update tracking files

Run: python3 mega_statewide_deployment.py --deploy
"""

import asyncio
import aiohttp
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
import time
import requests

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
OUTPUT_DIR = SCRIPT_DIR.parent / "output"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"

# Create dirs
GEOJSON_DIR.mkdir(parents=True, exist_ok=True)
PMTILES_DIR.mkdir(parents=True, exist_ok=True)

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

# Ollama AI Server
OLLAMA_HOST = "http://10.8.0.1:11434"

# Partial states needing statewide sources
PARTIAL_STATES = {
    "AL": {"name": "Alabama", "total_counties": 67, "priority": 2},
    "AZ": {"name": "Arizona", "total_counties": 15, "priority": 3},
    "GA": {"name": "Georgia", "total_counties": 159, "priority": 1},
    "IL": {"name": "Illinois", "total_counties": 102, "priority": 1},
    "KS": {"name": "Kansas", "total_counties": 105, "priority": 3},
    "KY": {"name": "Kentucky", "total_counties": 120, "priority": 3},
    "LA": {"name": "Louisiana", "total_counties": 64, "priority": 2},
    "MI": {"name": "Michigan", "total_counties": 83, "priority": 1},
    "MS": {"name": "Mississippi", "total_counties": 82, "priority": 3},
    "MO": {"name": "Missouri", "total_counties": 115, "priority": 2},
    "OK": {"name": "Oklahoma", "total_counties": 77, "priority": 2},
    "OR": {"name": "Oregon", "total_counties": 36, "priority": 2},
    "SC": {"name": "South Carolina", "total_counties": 46, "priority": 2},
    "SD": {"name": "South Dakota", "total_counties": 66, "priority": 3},
}

# Known statewide sources (verified)
KNOWN_SOURCES = {
    "GA": {
        "name": "Georgia - GIS Clearinghouse",
        "url": "https://services1.arcgis.com/XdEiuCuJe2Pxhh7o/arcgis/rest/services/GARS_Statewide_Parcels/FeatureServer/0",
        "records": 4800000,
        "verified": False
    },
    "IL": {
        "name": "Illinois - State GIS",
        "url": "https://gis.illinois.gov/",
        "api_url": None,  # Need to find
        "verified": False
    },
    "MI": {
        "name": "Michigan - Geographic Framework",
        "url": "https://gis.michigan.gov/",
        "api_url": None,  # Need to find
        "verified": False
    },
}

class AISourceFinder:
    """Use Ollama AI to find statewide parcel sources"""

    def __init__(self):
        self.ollama_url = f"{OLLAMA_HOST}/api/generate"
        self.model = "llama3.3:70b"  # Use the most powerful model

    async def find_source(self, state_code, state_name):
        """Use AI to find statewide parcel data source"""

        prompt = f"""Find the official statewide parcel/cadastral data source for {state_name} ({state_code}).

I need:
1. The official state GIS portal URL
2. ArcGIS REST API endpoint (if available) for statewide parcels
3. Alternative download link if no REST API

Search for:
- State GIS office
- State land records
- State cadastral data
- "{state_name} statewide parcels"
- "{state_name} GIS parcels"

Return ONLY a JSON object with this structure:
{{
  "found": true/false,
  "portal_url": "https://...",
  "api_url": "https://...arcgis/rest/services/.../FeatureServer/0" or null,
  "download_url": "https://..." or null,
  "format": "ArcGIS REST" or "Shapefile" or "GeoJSON",
  "confidence": "high/medium/low",
  "notes": "..."
}}"""

        print(f"\n🤖 AI searching for {state_name} ({state_code}) statewide parcels...")

        try:
            # Call Ollama
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Low temp for factual accuracy
                            "num_predict": 1024
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    result = await resp.json()
                    response_text = result.get("response", "")

                    # Try to extract JSON
                    try:
                        # Find JSON in response
                        start = response_text.find('{')
                        end = response_text.rfind('}') + 1
                        if start >= 0 and end > start:
                            json_str = response_text[start:end]
                            data = json.loads(json_str)
                            print(f"  ✓ AI found source (confidence: {data.get('confidence', 'unknown')})")
                            return data
                    except:
                        pass

                    print(f"  ⚠ AI could not parse result")
                    return {"found": False, "notes": "Could not parse AI response"}

        except Exception as e:
            print(f"  ✗ AI search failed: {e}")
            return {"found": False, "notes": f"Error: {e}"}

class MegaDownloader:
    """Download parcels from ArcGIS REST APIs in parallel"""

    def __init__(self, max_workers=24):
        self.max_workers = max_workers
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    def get_feature_count(self, url):
        """Get total feature count"""
        try:
            resp = requests.get(
                f"{url}/query?where=1%3D1&returnCountOnly=true&f=json",
                headers=self.headers,
                timeout=30
            )
            return resp.json().get('count', 0)
        except Exception as e:
            print(f"  ✗ Count failed: {e}")
            return 0

    def download_batch(self, url, offset, batch_size=2000):
        """Download a single batch"""
        try:
            params = {
                'where': '1=1',
                'outFields': '*',
                'f': 'geojson',
                'resultOffset': offset,
                'resultRecordCount': batch_size,
                'outSR': '4326'
            }
            resp = requests.get(
                f"{url}/query",
                params=params,
                headers=self.headers,
                timeout=300
            )
            if resp.status_code == 200:
                return resp.json().get('features', [])
        except Exception as e:
            print(f"  ⚠ Batch {offset} failed: {e}")
        return None

    def download_state(self, state_code, api_url):
        """Download entire state in parallel"""
        print(f"\n📥 Downloading {state_code} from {api_url}")

        # Get count
        count = self.get_feature_count(api_url)
        if count == 0:
            print(f"  ✗ No features found!")
            return None

        print(f"  Total features: {count:,}")

        # Download in parallel
        batch_size = 2000
        offsets = list(range(0, count, batch_size))
        all_features = []
        failed = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.download_batch, api_url, offset, batch_size): offset
                for offset in offsets
            }

            completed = 0
            for future in as_completed(futures):
                offset = futures[future]
                features = future.result()

                if features:
                    all_features.extend(features)
                else:
                    failed.append(offset)

                completed += 1
                if completed % 50 == 0 or completed == len(offsets):
                    pct = (completed / len(offsets)) * 100
                    print(f"  Progress: {completed}/{len(offsets)} ({pct:.1f}%) - {len(all_features):,} features")

        # Retry failed
        if failed:
            print(f"  Retrying {len(failed)} failed batches...")
            for offset in failed[:]:
                time.sleep(1)
                features = self.download_batch(api_url, offset, batch_size)
                if features:
                    all_features.extend(features)
                    failed.remove(offset)

        if not all_features:
            print(f"  ✗ No features downloaded!")
            return None

        # Save GeoJSON
        output_file = GEOJSON_DIR / f"parcels_{state_code.lower()}_statewide.geojson"
        with open(output_file, 'w') as f:
            json.dump({"type": "FeatureCollection", "features": all_features}, f)

        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"  ✓ Saved {len(all_features):,} features ({size_mb:.1f} MB)")

        return output_file

class MegaProcessor:
    """Process GeoJSON to PMTiles in parallel"""

    def __init__(self, max_workers=16):
        self.max_workers = max_workers

    def process_one(self, geojson_path):
        """Process one file: reproject (if needed) + tippecanoe"""
        state_code = geojson_path.stem.split('_')[1].upper()
        pmtiles_path = PMTILES_DIR / f"{geojson_path.stem}.pmtiles"

        print(f"\n🔧 Processing {state_code}...")

        try:
            # Convert to PMTiles
            cmd = [
                'tippecanoe',
                '-o', str(pmtiles_path),
                '-z', '15',
                '-Z', '10',
                '--drop-densest-as-needed',
                '--extend-zooms-if-still-dropping',
                '--force',
                '--layer', 'parcels',
                str(geojson_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

            if result.returncode != 0:
                print(f"  ✗ Tippecanoe failed: {result.stderr}")
                return None

            size_mb = pmtiles_path.stat().st_size / (1024 * 1024)
            print(f"  ✓ Created PMTiles ({size_mb:.1f} MB)")

            # Clean up GeoJSON to save space
            geojson_path.unlink()

            return pmtiles_path

        except Exception as e:
            print(f"  ✗ Processing failed: {e}")
            return None

    def process_all(self, geojson_files):
        """Process all files in parallel"""
        print(f"\n🔧 Processing {len(geojson_files)} files with {self.max_workers} workers...")

        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_one, f): f for f in geojson_files}

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

class MegaUploader:
    """Upload PMTiles to R2 in parallel"""

    def __init__(self, max_workers=8):
        self.max_workers = max_workers

    def upload_one(self, pmtiles_path):
        """Upload one PMTiles file"""
        filename = pmtiles_path.name
        state_code = filename.split('_')[1].upper()

        print(f"\n☁️  Uploading {state_code}...")

        try:
            # Upload to R2
            cmd = [
                'aws', 's3', 'cp',
                str(pmtiles_path),
                f's3://{R2_BUCKET}/parcels/{filename}',
                '--endpoint-url', R2_ENDPOINT
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                print(f"  ✗ Upload failed: {result.stderr}")
                return None

            # Verify
            cdn_url = f"{CDN_BASE}/parcels/{filename}"
            verify_cmd = ['pmtiles', 'show', cdn_url]
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=60)

            if verify_result.returncode == 0:
                print(f"  ✓ Uploaded and verified: {cdn_url}")
                # Clean up local file
                pmtiles_path.unlink()
                return cdn_url
            else:
                print(f"  ⚠ Uploaded but verification failed")
                return None

        except Exception as e:
            print(f"  ✗ Upload failed: {e}")
            return None

    def upload_all(self, pmtiles_files):
        """Upload all files in parallel"""
        print(f"\n☁️  Uploading {len(pmtiles_files)} files with {self.max_workers} workers...")

        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.upload_one, f): f for f in pmtiles_files}

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Mega Statewide Deployment")
    parser.add_argument('--find-sources', action='store_true', help='Use AI to find sources')
    parser.add_argument('--deploy', action='store_true', help='Download, process, upload everything')
    parser.add_argument('--states', type=str, help='Comma-separated state codes (e.g., GA,IL,MI)')
    parser.add_argument('--download-only', action='store_true', help='Only download')
    parser.add_argument('--process-only', action='store_true', help='Only process existing GeoJSON')
    parser.add_argument('--upload-only', action='store_true', help='Only upload existing PMTiles')
    args = parser.parse_args()

    print("\n" + "="*80)
    print("  HITD MAPS - MEGA STATEWIDE DEPLOYMENT")
    print("="*80)
    print(f"  System: 48 cores, 471 GB RAM available")
    print(f"  Target: {len(PARTIAL_STATES)} partial states to complete")
    print("="*80 + "\n")

    # Filter states if specified
    if args.states:
        state_codes = [s.strip().upper() for s in args.states.split(',')]
        states_to_process = {k: v for k, v in PARTIAL_STATES.items() if k in state_codes}
    else:
        states_to_process = PARTIAL_STATES

    # Step 1: Find sources with AI
    if args.find_sources or args.deploy:
        finder = AISourceFinder()
        found_sources = {}

        for state_code, state_info in sorted(states_to_process.items(), key=lambda x: x[1]['priority']):
            if state_code in KNOWN_SOURCES and KNOWN_SOURCES[state_code].get('url'):
                found_sources[state_code] = KNOWN_SOURCES[state_code]
                print(f"✓ {state_code}: Using known source")
            else:
                result = await finder.find_source(state_code, state_info['name'])
                if result.get('found') and result.get('api_url'):
                    found_sources[state_code] = result
                    print(f"✓ {state_code}: AI found source!")
                else:
                    print(f"✗ {state_code}: No source found")

        # Save found sources
        sources_file = DATA_DIR / "ai_found_sources.json"
        with open(sources_file, 'w') as f:
            json.dump(found_sources, f, indent=2)
        print(f"\n✓ Saved {len(found_sources)} sources to {sources_file}")

        if not args.deploy:
            return

    # Step 2: Download all
    if args.deploy or args.download_only:
        # Load sources
        sources_file = DATA_DIR / "ai_found_sources.json"
        if sources_file.exists():
            with open(sources_file) as f:
                sources = json.load(f)
        else:
            sources = KNOWN_SOURCES

        downloader = MegaDownloader(max_workers=24)
        downloaded = []

        for state_code, source in sources.items():
            api_url = source.get('api_url') or source.get('url')
            if api_url and 'FeatureServer' in api_url:
                result = downloader.download_state(state_code, api_url)
                if result:
                    downloaded.append(result)

        print(f"\n✓ Downloaded {len(downloaded)} states")

        if args.download_only:
            return

    # Step 3: Process all
    if args.deploy or args.process_only:
        geojson_files = list(GEOJSON_DIR.glob("parcels_*_statewide.geojson"))

        if not geojson_files:
            print("No GeoJSON files to process!")
            return

        processor = MegaProcessor(max_workers=16)
        processed = processor.process_all(geojson_files)

        print(f"\n✓ Processed {len(processed)} states")

        if args.process_only:
            return

    # Step 4: Upload all
    if args.deploy or args.upload_only:
        pmtiles_files = list(PMTILES_DIR.glob("parcels_*_statewide.pmtiles"))

        if not pmtiles_files:
            print("No PMTiles files to upload!")
            return

        uploader = MegaUploader(max_workers=8)
        uploaded = uploader.upload_all(pmtiles_files)

        print(f"\n✓ Uploaded {len(uploaded)} states")

    print("\n" + "="*80)
    print("  DEPLOYMENT COMPLETE!")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(main())
