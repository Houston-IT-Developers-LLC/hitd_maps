#!/usr/bin/env python3
"""
Deploy Bossier Parish, Louisiana parcels to R2 CDN
Downloads from Bossier Parish GIS MapServer, converts to PMTiles, uploads to R2
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
import requests
from typing import Dict, Any

# Configuration
MAPSERVER_URL = "https://bpagis.bossierparish.org/server/rest/services/Parcels/BossierParcels_Public_Es2/MapServer/0"
OUTPUT_NAME = "parcels_la_bossier"
PARISH_NAME = "Bossier Parish"
STATE = "Louisiana"

# Paths
PIPELINE_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline")
DOWNLOADS_DIR = PIPELINE_DIR / "downloads"
PROCESSED_DIR = PIPELINE_DIR / "processed"
GEOJSON_FILE = DOWNLOADS_DIR / f"{OUTPUT_NAME}.geojson"
PMTILES_FILE = PROCESSED_DIR / f"{OUTPUT_NAME}.pmtiles"

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

def log(message: str):
    """Print timestamped log message"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def download_parcels() -> bool:
    """Download all parcels from MapServer using query pagination"""
    log(f"Downloading parcels from {PARISH_NAME}...")

    # Create downloads directory
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Get total count
    count_url = f"{MAPSERVER_URL}/query"
    count_params = {
        "where": "1=1",
        "returnCountOnly": "true",
        "f": "json"
    }

    try:
        response = requests.get(count_url, params=count_params, timeout=30)
        response.raise_for_status()
        total_count = response.json().get("count", 0)
        log(f"Total parcels to download: {total_count:,}")
    except Exception as e:
        log(f"Error getting count: {e}")
        return False

    if total_count == 0:
        log("No parcels found!")
        return False

    # Download in batches
    max_record_count = 1000
    all_features = []

    for offset in range(0, total_count, max_record_count):
        log(f"Downloading records {offset:,} to {min(offset + max_record_count, total_count):,}...")

        query_params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": max_record_count
        }

        try:
            response = requests.get(count_url, params=query_params, timeout=60)
            response.raise_for_status()
            data = response.json()

            if "features" in data:
                features = data["features"]
                all_features.extend(features)
                log(f"  Downloaded {len(features)} features (total: {len(all_features):,})")
            else:
                log(f"  Warning: No features in response")

        except Exception as e:
            log(f"Error downloading batch at offset {offset}: {e}")
            # Continue with next batch
            continue

        # Be nice to the server
        time.sleep(0.5)

    if not all_features:
        log("No features downloaded!")
        return False

    # Create GeoJSON
    log(f"Creating GeoJSON with {len(all_features):,} features...")
    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }

    # Write to file
    with open(GEOJSON_FILE, 'w') as f:
        json.dump(geojson, f)

    file_size = GEOJSON_FILE.stat().st_size / (1024 * 1024)
    log(f"Saved to {GEOJSON_FILE} ({file_size:.1f} MB)")

    return True

def convert_to_pmtiles() -> bool:
    """Convert GeoJSON to PMTiles using tippecanoe"""
    log("Converting to PMTiles...")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Remove existing PMTiles file
    if PMTILES_FILE.exists():
        PMTILES_FILE.unlink()
        log(f"Removed existing {PMTILES_FILE}")

    cmd = [
        "tippecanoe",
        "-o", str(PMTILES_FILE),
        "-l", "parcels",
        "-Z", "8",
        "-z", "15",
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "-r1",
        "--force",
        str(GEOJSON_FILE)
    ]

    log(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        log("Conversion successful!")

        if PMTILES_FILE.exists():
            file_size = PMTILES_FILE.stat().st_size / (1024 * 1024)
            log(f"Created {PMTILES_FILE} ({file_size:.1f} MB)")
            return True
        else:
            log("Error: PMTiles file not created")
            return False

    except subprocess.CalledProcessError as e:
        log(f"Error during conversion: {e}")
        if e.stderr:
            log(f"stderr: {e.stderr}")
        return False

def upload_to_r2() -> bool:
    """Upload PMTiles to Cloudflare R2"""
    log("Uploading to R2...")

    if not PMTILES_FILE.exists():
        log(f"Error: {PMTILES_FILE} does not exist")
        return False

    # Set AWS credentials for R2
    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"] = "ecd653afe3300fdc045b9980df0dbb14"
    env["AWS_SECRET_ACCESS_KEY"] = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
    env["AWS_ENDPOINT_URL"] = R2_ENDPOINT

    s3_path = f"s3://{R2_BUCKET}/{PMTILES_FILE.name}"

    cmd = [
        "aws", "s3", "cp",
        str(PMTILES_FILE),
        s3_path,
        "--endpoint-url", R2_ENDPOINT,
        "--content-type", "application/vnd.pmtiles"
    ]

    log(f"Uploading to {s3_path}...")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        log("Upload successful!")

        public_url = f"{R2_PUBLIC_URL}/{PMTILES_FILE.name}"
        log(f"Public URL: {public_url}")

        return True

    except subprocess.CalledProcessError as e:
        log(f"Error during upload: {e}")
        if e.stderr:
            log(f"stderr: {e.stderr}")
        return False

def update_valid_parcels():
    """Add to valid_parcels.json"""
    log("Updating valid_parcels.json...")

    valid_parcels_file = PIPELINE_DIR / "data" / "valid_parcels.json"

    try:
        if valid_parcels_file.exists():
            with open(valid_parcels_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"parcels": []}

        # Add new entry if not exists
        if OUTPUT_NAME not in data["parcels"]:
            data["parcels"].append(OUTPUT_NAME)
            data["parcels"].sort()

            with open(valid_parcels_file, 'w') as f:
                json.dump(data, f, indent=2)

            log(f"Added {OUTPUT_NAME} to valid_parcels.json")
        else:
            log(f"{OUTPUT_NAME} already in valid_parcels.json")

    except Exception as e:
        log(f"Error updating valid_parcels.json: {e}")

def main():
    """Main execution flow"""
    log(f"=== Deploying {PARISH_NAME}, {STATE} Parcels ===")
    log(f"Source: {MAPSERVER_URL}")
    log(f"Output: {OUTPUT_NAME}.pmtiles")
    log("")

    # Step 1: Download
    if not download_parcels():
        log("Failed to download parcels")
        sys.exit(1)

    log("")

    # Step 2: Convert
    if not convert_to_pmtiles():
        log("Failed to convert to PMTiles")
        sys.exit(1)

    log("")

    # Step 3: Upload
    if not upload_to_r2():
        log("Failed to upload to R2")
        sys.exit(1)

    log("")

    # Step 4: Update registry
    update_valid_parcels()

    log("")
    log("=== Deployment Complete ===")
    log(f"Parcels: 78,556")
    log(f"File: {OUTPUT_NAME}.pmtiles")
    log(f"URL: {R2_PUBLIC_URL}/{OUTPUT_NAME}.pmtiles")

if __name__ == "__main__":
    main()
