#!/usr/bin/env python3
"""
Deploy La Paz County, Arizona parcels to R2 CDN
Downloads from ArcGIS MapServer, reprojects, converts to PMTiles, uploads
"""

import os
import sys
import json
import subprocess
import requests
from pathlib import Path

# Configuration
ENDPOINT = "https://azwatermaps.azwater.gov/arcgis/rest/services/General/Parcels_for_TEST/MapServer/4"
COUNTY_NAME = "La Paz County"
STATE = "Arizona"
OUTPUT_NAME = "parcels_az_la_paz"
TOTAL_RECORDS = 16176
MAX_RECORDS = 2000  # MapServer limit

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_CDN = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# Paths
BASE_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline")
DOWNLOAD_DIR = BASE_DIR / "downloads"
PROCESSED_DIR = BASE_DIR / "processed"
DOWNLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

GEOJSON_FILE = DOWNLOAD_DIR / f"{OUTPUT_NAME}.geojson"
REPROJECTED_FILE = PROCESSED_DIR / f"{OUTPUT_NAME}_wgs84.geojson"
PMTILES_FILE = PROCESSED_DIR / f"{OUTPUT_NAME}.pmtiles"


def log(msg):
    """Print timestamped log message"""
    print(f"[{OUTPUT_NAME}] {msg}", flush=True)


def download_parcels():
    """Download all parcels from MapServer with pagination"""
    log(f"Downloading {TOTAL_RECORDS:,} parcels from {COUNTY_NAME}, {STATE}...")

    all_features = []
    offset = 0

    while offset < TOTAL_RECORDS:
        log(f"  Fetching records {offset:,} to {offset + MAX_RECORDS:,}...")

        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": MAX_RECORDS,
            "returnGeometry": "true",
            "outSR": "26912"  # Keep original EPSG:26912 (UTM Zone 12N)
        }

        try:
            response = requests.get(f"{ENDPOINT}/query", params=params, timeout=300)
            response.raise_for_status()
            data = response.json()

            if "features" in data:
                features = data["features"]
                all_features.extend(features)
                log(f"    Got {len(features)} features (total: {len(all_features):,})")

                if len(features) < MAX_RECORDS:
                    break  # Last page
            else:
                log(f"    No features in response: {data}")
                break

        except Exception as e:
            log(f"    ERROR: {e}")
            if len(all_features) > 0:
                log(f"    Continuing with {len(all_features):,} features downloaded so far...")
                break
            else:
                raise

        offset += MAX_RECORDS

    log(f"Downloaded {len(all_features):,} features")

    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": all_features,
        "crs": {
            "type": "name",
            "properties": {"name": "EPSG:26912"}
        }
    }

    with open(GEOJSON_FILE, "w") as f:
        json.dump(geojson, f)

    file_size_mb = GEOJSON_FILE.stat().st_size / 1024 / 1024
    log(f"Saved to {GEOJSON_FILE} ({file_size_mb:.1f} MB)")

    return len(all_features)


def reproject_to_wgs84():
    """Reproject from EPSG:26912 (UTM Zone 12N) to EPSG:4326 (WGS84)"""
    log("Reprojecting from EPSG:26912 to EPSG:4326...")

    cmd = [
        "ogr2ogr",
        "-f", "GeoJSON",
        "-t_srs", "EPSG:4326",
        "-s_srs", "EPSG:26912",
        str(REPROJECTED_FILE),
        str(GEOJSON_FILE)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        log(f"ERROR: ogr2ogr failed: {result.stderr}")
        raise RuntimeError(f"Reprojection failed: {result.stderr}")

    file_size_mb = REPROJECTED_FILE.stat().st_size / 1024 / 1024
    log(f"Reprojected to {REPROJECTED_FILE} ({file_size_mb:.1f} MB)")


def convert_to_pmtiles():
    """Convert GeoJSON to PMTiles using tippecanoe"""
    log("Converting to PMTiles...")

    cmd = [
        "tippecanoe",
        "-o", str(PMTILES_FILE),
        "-Z8", "-z16",  # Zoom levels 8-16
        "-l", "parcels",
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "--force",
        str(REPROJECTED_FILE)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        log(f"ERROR: tippecanoe failed: {result.stderr}")
        raise RuntimeError(f"PMTiles conversion failed: {result.stderr}")

    file_size_mb = PMTILES_FILE.stat().st_size / 1024 / 1024
    log(f"Created PMTiles: {PMTILES_FILE} ({file_size_mb:.1f} MB)")

    return file_size_mb


def upload_to_r2():
    """Upload PMTiles to Cloudflare R2"""
    log("Uploading to R2...")

    s3_path = f"s3://{R2_BUCKET}/parcels/{OUTPUT_NAME}.pmtiles"

    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY
    env["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_KEY

    cmd = [
        "aws", "s3", "cp",
        str(PMTILES_FILE),
        s3_path,
        "--endpoint-url", R2_ENDPOINT,
        "--content-type", "application/vnd.pmtiles"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        log(f"ERROR: Upload failed: {result.stderr}")
        raise RuntimeError(f"R2 upload failed: {result.stderr}")

    cdn_url = f"{R2_CDN}/parcels/{OUTPUT_NAME}.pmtiles"
    log(f"Uploaded to R2: {cdn_url}")

    return cdn_url


def verify_on_cdn(cdn_url):
    """Verify file is accessible on CDN"""
    log("Verifying CDN access...")

    try:
        response = requests.head(cdn_url, timeout=30)
        if response.status_code == 200:
            content_length = int(response.headers.get("content-length", 0))
            log(f"✓ CDN accessible: {content_length:,} bytes")
            return True
        else:
            log(f"✗ CDN check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        log(f"✗ CDN verification error: {e}")
        return False


def update_valid_parcels():
    """Add to valid_parcels.json"""
    valid_parcels_file = BASE_DIR / "data" / "valid_parcels.json"

    try:
        with open(valid_parcels_file, "r") as f:
            parcels = json.load(f)

        if OUTPUT_NAME not in parcels:
            parcels.append(OUTPUT_NAME)
            parcels.sort()

            with open(valid_parcels_file, "w") as f:
                json.dump(parcels, f, indent=2)

            log(f"Added '{OUTPUT_NAME}' to valid_parcels.json")
        else:
            log(f"'{OUTPUT_NAME}' already in valid_parcels.json")
    except Exception as e:
        log(f"Warning: Could not update valid_parcels.json: {e}")


def main():
    """Main deployment pipeline"""
    log("=" * 60)
    log(f"Starting deployment: {COUNTY_NAME}, {STATE}")
    log(f"Endpoint: {ENDPOINT}")
    log(f"Expected records: {TOTAL_RECORDS:,}")
    log("=" * 60)

    try:
        # Step 1: Download
        count = download_parcels()

        # Step 2: Reproject
        reproject_to_wgs84()

        # Step 3: Convert to PMTiles
        file_size_mb = convert_to_pmtiles()

        # Step 4: Upload to R2
        cdn_url = upload_to_r2()

        # Step 5: Verify
        verify_on_cdn(cdn_url)

        # Step 6: Update registry
        update_valid_parcels()

        # Final summary
        log("=" * 60)
        log("DEPLOYMENT COMPLETE!")
        log("=" * 60)
        log(f"County: {COUNTY_NAME}, {STATE}")
        log(f"Endpoint: {ENDPOINT}")
        log(f"Parcel count: {count:,}")
        log(f"File size: {file_size_mb:.1f} MB")
        log(f"CDN URL: {cdn_url}")
        log(f"Registry: {OUTPUT_NAME}")
        log("=" * 60)

        return 0

    except Exception as e:
        log(f"DEPLOYMENT FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
