#!/usr/bin/env python3
"""
Deploy St. Bernard Parish, Louisiana parcels to R2 CDN.

Parish Info:
- Name: St. Bernard Parish
- Population: ~47,000
- Major city: Chalmette
- Parcels: 21,761
- Spatial Reference: EPSG:3452 (Louisiana State Plane South)

Data Source: https://lucity.sbpg.net/arcgis/rest/services/ComDev/Parcels3/MapServer/0
Open Data Portal: https://gis-stbernard.opendata.arcgis.com/
"""

import os
import sys
import requests
import json
import subprocess
import time
from pathlib import Path

# Configuration
FEATURE_SERVER = "https://lucity.sbpg.net/arcgis/rest/services/ComDev/Parcels3/MapServer/0"
OUTPUT_NAME = "parcels_la_st_bernard"
PARISH_NAME = "St. Bernard Parish"
STATE = "LA"

# Directories
BASE_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline")
DOWNLOAD_DIR = BASE_DIR / "downloads"
PROCESSED_DIR = BASE_DIR / "processed"
DOWNLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# Output files
GEOJSON_RAW = DOWNLOAD_DIR / f"{OUTPUT_NAME}_raw.geojson"
GEOJSON_REPROJECTED = PROCESSED_DIR / f"{OUTPUT_NAME}_4326.geojson"
PMTILES_FILE = PROCESSED_DIR / f"{OUTPUT_NAME}.pmtiles"

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}\n")

    result = subprocess.run(
        cmd,
        shell=isinstance(cmd, str),
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"❌ Error: Command failed with exit code {result.returncode}")
        sys.exit(1)

    return result

def download_parcels():
    """Download all parcels from ArcGIS MapServer."""
    print(f"\n{'='*60}")
    print(f"STEP 1: Downloading {PARISH_NAME} Parcels")
    print(f"{'='*60}")
    print(f"Source: {FEATURE_SERVER}")
    print(f"Output: {GEOJSON_RAW}")

    # Get total count
    count_url = f"{FEATURE_SERVER}/query?where=1%3D1&returnCountOnly=true&f=json"
    response = requests.get(count_url)
    total_count = response.json()['count']
    print(f"Total parcels: {total_count:,}")

    # Download in batches
    batch_size = 1000
    all_features = []

    for offset in range(0, total_count, batch_size):
        print(f"Downloading records {offset:,} to {min(offset + batch_size, total_count):,}...")

        query_url = f"{FEATURE_SERVER}/query"
        params = {
            'where': '1=1',
            'outFields': '*',
            'returnGeometry': 'true',
            'f': 'geojson',
            'resultOffset': offset,
            'resultRecordCount': batch_size
        }

        response = requests.get(query_url, params=params)
        data = response.json()

        if 'features' in data:
            all_features.extend(data['features'])
            print(f"  Got {len(data['features'])} features")
        else:
            print(f"  Warning: No features in response")

        time.sleep(0.1)  # Be nice to the server

    # Save combined GeoJSON
    geojson = {
        'type': 'FeatureCollection',
        'features': all_features
    }

    with open(GEOJSON_RAW, 'w') as f:
        json.dump(geojson, f)

    print(f"\n✓ Downloaded {len(all_features):,} parcels")
    print(f"✓ Saved to: {GEOJSON_RAW}")

    # File size
    size_mb = GEOJSON_RAW.stat().st_size / (1024 * 1024)
    print(f"✓ File size: {size_mb:.1f} MB")

    return len(all_features)

def reproject_to_wgs84():
    """Check if reprojection is needed - ArcGIS returns GeoJSON in WGS84."""
    print(f"\n{'='*60}")
    print(f"STEP 2: Checking Coordinate System")
    print(f"{'='*60}")

    # Check coordinates in raw file
    import json
    with open(GEOJSON_RAW, 'r') as f:
        data = json.load(f)

    if data['features']:
        first_coord = data['features'][0]['geometry']['coordinates'][0][0]
        lon, lat = first_coord[0], first_coord[1]
        print(f"Sample coordinate: {lon:.6f}, {lat:.6f}")

        # Check if already in WGS84 range
        if -180 <= lon <= 180 and -90 <= lat <= 90:
            print("✓ Data is already in WGS84!")
            print(f"Copying file to {GEOJSON_REPROJECTED}")

            # Just copy the file
            import shutil
            shutil.copy(GEOJSON_RAW, GEOJSON_REPROJECTED)

            size_mb = GEOJSON_REPROJECTED.stat().st_size / (1024 * 1024)
            print(f"✓ File size: {size_mb:.1f} MB")
        else:
            print(f"Data needs reprojection from EPSG:3452")
            cmd = [
                'ogr2ogr',
                '-f', 'GeoJSON',
                '-t_srs', 'EPSG:4326',
                '-s_srs', 'EPSG:3452',
                str(GEOJSON_REPROJECTED),
                str(GEOJSON_RAW)
            ]
            run_command(cmd, "Reprojecting with ogr2ogr")

            size_mb = GEOJSON_REPROJECTED.stat().st_size / (1024 * 1024)
            print(f"\n✓ Reprojected to WGS84")
            print(f"✓ Output: {GEOJSON_REPROJECTED}")
            print(f"✓ File size: {size_mb:.1f} MB")

def convert_to_pmtiles():
    """Convert GeoJSON to PMTiles using tippecanoe."""
    print(f"\n{'='*60}")
    print(f"STEP 3: Converting to PMTiles")
    print(f"{'='*60}")

    cmd = [
        'tippecanoe',
        '-o', str(PMTILES_FILE),
        '-Z', '6',           # Min zoom
        '-z', '16',          # Max zoom
        '-l', 'parcels',     # Layer name
        '--force',           # Overwrite existing
        '--drop-densest-as-needed',
        '--extend-zooms-if-still-dropping',
        '--coalesce-densest-as-needed',
        '--detect-shared-borders',
        '--simplification=10',
        '--name', f'{PARISH_NAME} Parcels',
        '--attribution', 'St. Bernard Parish Government',
        str(GEOJSON_REPROJECTED)
    ]

    run_command(cmd, "Running tippecanoe")

    size_mb = PMTILES_FILE.stat().st_size / (1024 * 1024)
    print(f"\n✓ Created PMTiles file")
    print(f"✓ Output: {PMTILES_FILE}")
    print(f"✓ File size: {size_mb:.1f} MB")

def validate_pmtiles():
    """Validate the PMTiles file."""
    print(f"\n{'='*60}")
    print(f"STEP 4: Validating PMTiles")
    print(f"{'='*60}")

    cmd = ['pmtiles', 'show', str(PMTILES_FILE)]
    result = run_command(cmd, "Running pmtiles show")

    print("\n✓ PMTiles validation successful")

def upload_to_r2():
    """Upload PMTiles to Cloudflare R2."""
    print(f"\n{'='*60}")
    print(f"STEP 5: Uploading to R2")
    print(f"{'='*60}")

    cmd = [
        'aws', 's3', 'cp',
        str(PMTILES_FILE),
        f's3://{R2_BUCKET}/{PMTILES_FILE.name}',
        '--endpoint-url', R2_ENDPOINT,
        '--region', 'auto'
    ]

    run_command(cmd, "Uploading to R2 with AWS CLI")

    public_url = f"{R2_PUBLIC_URL}/{PMTILES_FILE.name}"
    print(f"\n✓ Upload complete!")
    print(f"✓ Public URL: {public_url}")

    return public_url

def update_valid_parcels():
    """Add to valid_parcels.json registry."""
    print(f"\n{'='*60}")
    print(f"STEP 6: Updating valid_parcels.json")
    print(f"{'='*60}")

    registry_file = BASE_DIR / "data" / "valid_parcels.json"

    # Read existing registry
    with open(registry_file, 'r') as f:
        data = json.load(f)

    # Add new entry
    new_entry = {
        "id": OUTPUT_NAME,
        "name": f"{PARISH_NAME}, Louisiana",
        "state": STATE,
        "type": "parish",
        "url": f"https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/{PMTILES_FILE.name}",
        "source": "St. Bernard Parish Government",
        "source_url": "https://gis-stbernard.opendata.arcgis.com/",
        "last_updated": time.strftime("%Y-%m-%d"),
        "record_count": None  # Will be filled in
    }

    # Check if already exists
    existing_ids = [p['id'] for p in data.get('parcels', [])]
    if OUTPUT_NAME in existing_ids:
        print(f"⚠ {OUTPUT_NAME} already exists in registry, skipping...")
    else:
        data['parcels'].append(new_entry)

        # Save updated registry
        with open(registry_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Added {OUTPUT_NAME} to valid_parcels.json")

def main():
    """Main deployment pipeline."""
    print(f"""
    {'='*60}
    St. Bernard Parish, Louisiana Parcel Deployment
    {'='*60}

    Parish: {PARISH_NAME}
    State: {STATE}
    Source: St. Bernard Parish Government
    Portal: https://gis-stbernard.opendata.arcgis.com/

    Output: {OUTPUT_NAME}.pmtiles
    Target: {R2_BUCKET} (Cloudflare R2)
    {'='*60}
    """)

    try:
        # Run pipeline
        parcel_count = download_parcels()
        reproject_to_wgs84()
        convert_to_pmtiles()
        validate_pmtiles()
        public_url = upload_to_r2()
        update_valid_parcels()

        # Success summary
        print(f"""
        {'='*60}
        ✓ DEPLOYMENT SUCCESSFUL
        {'='*60}

        Parish: {PARISH_NAME}
        Parcels: {parcel_count:,}
        File: {PMTILES_FILE.name}
        Size: {PMTILES_FILE.stat().st_size / (1024 * 1024):.1f} MB

        Public URL:
        {public_url}

        Next Steps:
        1. Test in map viewer
        2. Update coverage_status.json
        3. Update documentation
        {'='*60}
        """)

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
