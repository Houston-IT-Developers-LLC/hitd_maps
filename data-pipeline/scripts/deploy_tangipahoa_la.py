#!/usr/bin/env python3
"""
Deploy Tangipahoa Parish, Louisiana parcels to R2 CDN.

Parish Info:
- Population: ~133,000
- Major city: Hammond
- Source: Tangipahoa Parish GIS (TanGIS)
- API: https://tangis.tangipahoa.org/server/rest/services/Cadastral/TaxParcel_A/FeatureServer/0
- Coordinate System: EPSG:3452 (Louisiana South State Plane)
- Update Frequency: Every 3 weeks
- Output: parcels_la_tangipahoa.pmtiles
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# Configuration
API_URL = "https://tangis.tangipahoa.org/server/rest/services/Cadastral/TaxParcel_A/FeatureServer/0"
PARISH_NAME = "tangipahoa"
OUTPUT_NAME = f"parcels_la_{PARISH_NAME}"
SOURCE_EPSG = "EPSG:3452"  # Louisiana South State Plane
TARGET_EPSG = "EPSG:4326"  # WGS84

# Directories
BASE_DIR = Path(__file__).parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
PROCESSED_DIR = BASE_DIR / "processed"
DOWNLOADS_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# File paths
GEOJSON_FILE = DOWNLOADS_DIR / f"{OUTPUT_NAME}_raw.geojson"
REPROJECTED_FILE = PROCESSED_DIR / f"{OUTPUT_NAME}_wgs84.geojson"
PMTILES_FILE = PROCESSED_DIR / f"{OUTPUT_NAME}.pmtiles"

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"


def log(message):
    """Print timestamped log message."""
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def get_feature_count():
    """Get total number of features from the service."""
    log("Getting feature count from service...")

    query_url = f"{API_URL}/query?where=1=1&returnCountOnly=true&f=json"

    try:
        with urllib.request.urlopen(query_url, timeout=30) as response:
            data = json.loads(response.read().decode())
            count = data.get('count', 0)
            log(f"Found {count:,} parcels in Tangipahoa Parish")
            return count
    except Exception as e:
        log(f"Error getting count: {e}")
        return None


def download_parcels():
    """Download all parcels from the ArcGIS REST API."""
    log(f"Downloading parcels from {API_URL}")

    # Get total count first
    total_count = get_feature_count()
    if total_count is None:
        log("WARNING: Could not determine feature count, proceeding anyway...")
        total_count = 100000  # Estimate

    # Build ogr2ogr command to download directly
    # Using GeoJSON driver with pagination
    cmd = [
        "ogr2ogr",
        "-f", "GeoJSON",
        str(GEOJSON_FILE),
        f"ESRIJSON:{API_URL}/query?where=1=1&outFields=*&f=json&resultOffset={{offset}}&resultRecordCount=2000",
        "-nln", "parcels",
        "-progress"
    ]

    log(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        log("Download complete!")

        # Check file size
        if GEOJSON_FILE.exists():
            size_mb = GEOJSON_FILE.stat().st_size / 1024 / 1024
            log(f"Downloaded file size: {size_mb:.2f} MB")
            return True
        else:
            log("ERROR: Download file not created")
            return False

    except subprocess.CalledProcessError as e:
        log(f"ERROR during download: {e}")
        log(f"STDOUT: {e.stdout}")
        log(f"STDERR: {e.stderr}")
        return False


def reproject_parcels():
    """Reproject from EPSG:3452 to WGS84."""
    log(f"Reprojecting from {SOURCE_EPSG} to {TARGET_EPSG}...")

    cmd = [
        "ogr2ogr",
        "-f", "GeoJSON",
        "-t_srs", TARGET_EPSG,
        "-s_srs", SOURCE_EPSG,
        str(REPROJECTED_FILE),
        str(GEOJSON_FILE),
        "-progress"
    ]

    log(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        log("Reprojection complete!")

        # Check file size
        if REPROJECTED_FILE.exists():
            size_mb = REPROJECTED_FILE.stat().st_size / 1024 / 1024
            log(f"Reprojected file size: {size_mb:.2f} MB")
            return True
        else:
            log("ERROR: Reprojected file not created")
            return False

    except subprocess.CalledProcessError as e:
        log(f"ERROR during reprojection: {e}")
        log(f"STDERR: {e.stderr}")
        return False


def convert_to_pmtiles():
    """Convert GeoJSON to PMTiles using tippecanoe."""
    log("Converting to PMTiles...")

    cmd = [
        "tippecanoe",
        "-o", str(PMTILES_FILE),
        "-Z", "8",
        "-z", "14",
        "-l", "parcels",
        "--force",
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        str(REPROJECTED_FILE)
    ]

    log(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        log("PMTiles conversion complete!")

        # Check file size
        if PMTILES_FILE.exists():
            size_mb = PMTILES_FILE.stat().st_size / 1024 / 1024
            log(f"PMTiles file size: {size_mb:.2f} MB")
            return True
        else:
            log("ERROR: PMTiles file not created")
            return False

    except subprocess.CalledProcessError as e:
        log(f"ERROR during PMTiles conversion: {e}")
        log(f"STDERR: {e.stderr}")
        return False


def upload_to_r2():
    """Upload PMTiles to R2."""
    log("Uploading to R2...")

    # Set AWS credentials for R2
    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"] = "ecd653afe3300fdc045b9980df0dbb14"
    env["AWS_SECRET_ACCESS_KEY"] = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
    env["AWS_ENDPOINT_URL"] = R2_ENDPOINT

    cmd = [
        "aws", "s3", "cp",
        str(PMTILES_FILE),
        f"s3://{R2_BUCKET}/parcels/{PMTILES_FILE.name}",
        "--endpoint-url", R2_ENDPOINT,
        "--content-type", "application/vnd.pmtiles"
    ]

    log(f"Running: aws s3 cp {PMTILES_FILE.name} s3://{R2_BUCKET}/parcels/")

    try:
        subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
        log("Upload complete!")

        public_url = f"{R2_PUBLIC_URL}/parcels/{PMTILES_FILE.name}"
        log(f"Public URL: {public_url}")
        return True

    except subprocess.CalledProcessError as e:
        log(f"ERROR during upload: {e}")
        log(f"STDERR: {e.stderr}")
        return False


def main():
    """Main deployment workflow."""
    log("=" * 60)
    log("Tangipahoa Parish, Louisiana Parcel Deployment")
    log("=" * 60)

    # Step 1: Download
    if not GEOJSON_FILE.exists():
        if not download_parcels():
            log("FAILED: Download step")
            return 1
    else:
        log(f"Using existing file: {GEOJSON_FILE}")

    # Step 2: Reproject
    if not REPROJECTED_FILE.exists():
        if not reproject_parcels():
            log("FAILED: Reprojection step")
            return 1
    else:
        log(f"Using existing file: {REPROJECTED_FILE}")

    # Step 3: Convert to PMTiles
    if not PMTILES_FILE.exists():
        if not convert_to_pmtiles():
            log("FAILED: PMTiles conversion step")
            return 1
    else:
        log(f"Using existing file: {PMTILES_FILE}")

    # Step 4: Upload to R2
    if not upload_to_r2():
        log("FAILED: Upload step")
        return 1

    log("=" * 60)
    log("SUCCESS! Tangipahoa Parish parcels deployed to R2")
    log(f"File: {OUTPUT_NAME}.pmtiles")
    log(f"URL: {R2_PUBLIC_URL}/parcels/{OUTPUT_NAME}.pmtiles")
    log("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
