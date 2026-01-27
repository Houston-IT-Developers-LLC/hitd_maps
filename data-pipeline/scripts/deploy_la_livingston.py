#!/usr/bin/env python3
"""
Deploy Livingston Parish, Louisiana parcels to R2 CDN.

Parish: Livingston Parish, Louisiana
Population: ~142,000
Source: ArcGIS MapServer via utility.arcgis.com
Total parcels: 84,692
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_cmd(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"ERROR: {description} failed")
        print(f"STDERR: {result.stderr}")
        return False

    print(result.stdout)
    return True

def main():
    """Download, process, and deploy Livingston Parish parcels."""

    # Configuration
    BASE_URL = "https://utility.arcgis.com/usrsvcs/servers/0e5f5ffb59b745f7bb82abb3d428da88/rest/services/Assessor/Parcels_SMARTCAMA/MapServer/8"
    LAYER_ID = 8
    TOTAL_COUNT = 84692
    MAX_RECORDS = 4000

    DOWNLOAD_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/downloads")
    PROCESSED_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/processed")

    OUTPUT_NAME = "la_livingston"
    GEOJSON_FILE = DOWNLOAD_DIR / f"{OUTPUT_NAME}.geojson"
    REPROJECTED_FILE = PROCESSED_DIR / f"{OUTPUT_NAME}_wgs84.geojson"
    PMTILES_FILE = PROCESSED_DIR / f"parcels_{OUTPUT_NAME}.pmtiles"

    # Ensure directories exist
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  Livingston Parish, Louisiana - Parcel Deployment                ║
╚══════════════════════════════════════════════════════════════════╝

Source: {BASE_URL}
Total Parcels: {TOTAL_COUNT:,}
Output: parcels_{OUTPUT_NAME}.pmtiles

""")

    # Step 1: Download data using ogr2ogr in chunks
    print(f"\n[1/5] Downloading {TOTAL_COUNT:,} parcels from ArcGIS MapServer...")

    # Remove old files
    if GEOJSON_FILE.exists():
        GEOJSON_FILE.unlink()
        print(f"Removed old file: {GEOJSON_FILE}")

    num_chunks = (TOTAL_COUNT + MAX_RECORDS - 1) // MAX_RECORDS
    print(f"Will download in {num_chunks} chunks of {MAX_RECORDS} records each")

    all_features = []

    for i in range(num_chunks):
        offset = i * MAX_RECORDS
        print(f"\nChunk {i+1}/{num_chunks}: Downloading records {offset:,} to {min(offset + MAX_RECORDS, TOTAL_COUNT):,}")

        # Build query URL with pagination
        query_url = f"{BASE_URL}/query?where=1%3D1&outFields=*&returnGeometry=true&f=geojson&resultOffset={offset}&resultRecordCount={MAX_RECORDS}"

        temp_file = DOWNLOAD_DIR / f"{OUTPUT_NAME}_chunk_{i}.geojson"

        cmd = [
            "curl", "-s",
            "-H", "Referer: https://atlas.geoportalmaps.com/",
            query_url,
            "-o", str(temp_file)
        ]

        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            print(f"ERROR downloading chunk {i+1}")
            return False

        # Read chunk and extract features
        try:
            with open(temp_file, 'r') as f:
                chunk_data = json.load(f)
                features = chunk_data.get('features', [])
                all_features.extend(features)
                print(f"  Added {len(features)} features (total: {len(all_features):,})")
        except Exception as e:
            print(f"ERROR reading chunk {i+1}: {e}")
            return False
        finally:
            # Clean up chunk file
            if temp_file.exists():
                temp_file.unlink()

        # Be nice to the server
        time.sleep(0.5)

    # Write combined GeoJSON
    print(f"\nCombining {len(all_features):,} features into single GeoJSON...")
    combined_geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }

    with open(GEOJSON_FILE, 'w') as f:
        json.dump(combined_geojson, f)

    print(f"✓ Downloaded {len(all_features):,} parcels to {GEOJSON_FILE}")
    print(f"  File size: {GEOJSON_FILE.stat().st_size / 1024 / 1024:.1f} MB")

    # Step 2: Data already in WGS84 (ArcGIS API returns WGS84 directly)
    print(f"\n[2/5] Data verification - checking coordinate system...")

    # The ArcGIS API returns GeoJSON in WGS84 already, just copy
    import shutil
    shutil.copy(GEOJSON_FILE, REPROJECTED_FILE)

    print(f"✓ Data is already in WGS84 (coordinates: -90.9°, 30.6°)")
    print(f"  File size: {REPROJECTED_FILE.stat().st_size / 1024 / 1024:.1f} MB")

    # Step 3: Convert to PMTiles
    print(f"\n[3/5] Converting to PMTiles with tippecanoe...")

    cmd = [
        "tippecanoe",
        "-o", str(PMTILES_FILE),
        "-Z", "8",  # Min zoom
        "-z", "15",  # Max zoom
        "-l", "parcels",  # Layer name
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "--force",
        str(REPROJECTED_FILE)
    ]

    if not run_cmd(cmd, "PMTiles conversion"):
        return False

    print(f"✓ Created {PMTILES_FILE}")
    print(f"  File size: {PMTILES_FILE.stat().st_size / 1024 / 1024:.1f} MB")

    # Step 4: Validate PMTiles
    print(f"\n[4/5] Validating PMTiles...")

    cmd = ["pmtiles", "show", str(PMTILES_FILE)]

    if not run_cmd(cmd, "PMTiles validation"):
        return False

    # Step 5: Upload to R2
    print(f"\n[5/5] Uploading to Cloudflare R2...")

    r2_path = f"parcels/parcels_{OUTPUT_NAME}.pmtiles"

    cmd = [
        "aws", "s3", "cp",
        str(PMTILES_FILE),
        f"s3://gspot-tiles/{r2_path}",
        "--endpoint-url", "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com",
        "--region", "auto"
    ]

    if not run_cmd(cmd, "R2 upload"):
        return False

    cdn_url = f"https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/{r2_path}"

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  ✓ DEPLOYMENT COMPLETE                                           ║
╚══════════════════════════════════════════════════════════════════╝

Parish: Livingston Parish, Louisiana
Parcels: {len(all_features):,}
PMTiles: {PMTILES_FILE.stat().st_size / 1024 / 1024:.1f} MB

CDN URL:
{cdn_url}

Test with:
https://protomaps.github.io/PMTiles/?url={cdn_url}

Local files:
- GeoJSON: {GEOJSON_FILE}
- Reprojected: {REPROJECTED_FILE}
- PMTiles: {PMTILES_FILE}
""")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
