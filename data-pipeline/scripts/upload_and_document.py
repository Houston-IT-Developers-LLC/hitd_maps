#!/usr/bin/env python3
"""
Upload parcel data to Cloudflare R2 with documentation.
Converts GeoJSON to PMTiles, uploads, documents metadata, and cleans up.
"""

import os
import json
import subprocess
import boto3
from botocore.config import Config
from datetime import datetime
from pathlib import Path
import hashlib
import sys

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

# Directories
BASE_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline")
GEOJSON_DIR = BASE_DIR / "output" / "geojson" / "counties"
PMTILES_DIR = BASE_DIR / "output" / "pmtiles"
DOCS_DIR = BASE_DIR / "docs"

# Metadata tracking
METADATA_FILE = DOCS_DIR / "PARCEL_DATA_MANIFEST.json"

def get_r2_client():
    """Create R2 client with retry config."""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            connect_timeout=30,
            read_timeout=120
        )
    )

def get_file_hash(filepath):
    """Get MD5 hash of file for verification."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_geojson_stats(filepath):
    """Get feature count from GeoJSON file."""
    try:
        result = subprocess.run(
            ['ogrinfo', '-so', str(filepath), 'OGRGeoJSON'],
            capture_output=True, text=True, timeout=60
        )
        for line in result.stdout.split('\n'):
            if 'Feature Count:' in line:
                return int(line.split(':')[1].strip())
    except:
        pass

    # Fallback: count features manually (slower)
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return len(data.get('features', []))
    except:
        return 0

def convert_to_pmtiles(geojson_path, pmtiles_path):
    """Convert GeoJSON to PMTiles using tippecanoe."""
    name = geojson_path.stem.replace('parcels_', '')

    cmd = [
        'tippecanoe',
        '-o', str(pmtiles_path),
        '--force',
        '--no-feature-limit',
        '--no-tile-size-limit',
        '-zg',  # Auto-select max zoom
        '--drop-densest-as-needed',
        '--extend-zooms-if-still-dropping',
        '--layer', 'parcels',
        '--name', f'parcels_{name}',
        '--attribution', 'GSpot Outdoors',
        str(geojson_path)
    ]

    print(f"  Converting {geojson_path.name} to PMTiles...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)

    if result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
        return False
    return True

def upload_to_r2(filepath, s3_key):
    """Upload file to R2 with progress."""
    client = get_r2_client()
    file_size = filepath.stat().st_size

    print(f"  Uploading {filepath.name} ({file_size / (1024*1024):.1f} MB)...")

    # Use multipart upload for large files
    config = boto3.s3.transfer.TransferConfig(
        multipart_threshold=100 * 1024 * 1024,  # 100MB
        max_concurrency=10,
        multipart_chunksize=100 * 1024 * 1024
    )

    client.upload_file(
        str(filepath),
        R2_BUCKET,
        s3_key,
        Config=config
    )

    return True

def load_metadata():
    """Load existing metadata manifest."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "manifest_version": "1.0",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "total_parcels": 0,
        "total_size_bytes": 0,
        "datasets": {}
    }

def save_metadata(metadata):
    """Save metadata manifest."""
    metadata["updated_at"] = datetime.now().isoformat()
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def process_and_upload(geojson_file, delete_local=True):
    """Process a single GeoJSON file: convert, upload, document, cleanup."""
    name = geojson_file.stem  # e.g., parcels_tx_harris
    pmtiles_file = PMTILES_DIR / f"{name}.pmtiles"

    print(f"\nProcessing: {geojson_file.name}")

    # Get stats before processing
    file_size = geojson_file.stat().st_size
    mod_time = datetime.fromtimestamp(geojson_file.stat().st_mtime)

    # Get feature count
    print(f"  Getting feature count...")
    feature_count = get_geojson_stats(geojson_file)
    print(f"  Features: {feature_count:,}")

    # Convert to PMTiles
    if not pmtiles_file.exists():
        if not convert_to_pmtiles(geojson_file, pmtiles_file):
            return None
    else:
        print(f"  PMTiles already exists, skipping conversion")

    pmtiles_size = pmtiles_file.stat().st_size

    # Upload PMTiles to R2
    s3_key = f"parcels/{pmtiles_file.name}"
    try:
        upload_to_r2(pmtiles_file, s3_key)
        print(f"  Uploaded to r2://{R2_BUCKET}/{s3_key}")
    except Exception as e:
        print(f"  Upload failed: {e}")
        return None

    # Create metadata entry
    metadata_entry = {
        "name": name.replace('parcels_', ''),
        "source_file": geojson_file.name,
        "pmtiles_file": pmtiles_file.name,
        "r2_key": s3_key,
        "r2_url": f"https://gspot-tiles.{R2_ENDPOINT.split('//')[1].split('.')[0]}.r2.cloudflarestorage.com/{s3_key}",
        "feature_count": feature_count,
        "geojson_size_bytes": file_size,
        "pmtiles_size_bytes": pmtiles_size,
        "extracted_at": mod_time.isoformat(),
        "uploaded_at": datetime.now().isoformat(),
        "source_type": "arcgis_rest_api",
        "update_frequency": "quarterly",  # Most parcel data updates quarterly
        "next_update_estimate": get_next_quarter().isoformat()
    }

    # Cleanup local files if requested
    if delete_local:
        print(f"  Deleting local files...")
        geojson_file.unlink()
        pmtiles_file.unlink()
        print(f"  Cleaned up local files")

    return metadata_entry

def get_next_quarter():
    """Get the first day of next quarter."""
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    if quarter == 4:
        return datetime(now.year + 1, 1, 1)
    else:
        return datetime(now.year, (quarter * 3) + 1, 1)

def main():
    """Main processing loop."""
    # Parse arguments
    delete_local = "--keep-local" not in sys.argv
    single_file = None
    for arg in sys.argv[1:]:
        if arg.endswith('.geojson'):
            single_file = arg

    print("=" * 60)
    print("Parcel Data Upload and Documentation Script")
    print("=" * 60)
    print(f"Delete local files after upload: {delete_local}")
    print(f"R2 Bucket: {R2_BUCKET}")
    print(f"GeoJSON Dir: {GEOJSON_DIR}")
    print()

    # Load existing metadata
    metadata = load_metadata()

    # Get list of GeoJSON files to process
    if single_file:
        geojson_files = [Path(single_file)]
    else:
        geojson_files = sorted(GEOJSON_DIR.glob("*.geojson"))

    print(f"Found {len(geojson_files)} GeoJSON files to process")

    processed = 0
    failed = 0

    for geojson_file in geojson_files:
        try:
            entry = process_and_upload(geojson_file, delete_local=delete_local)
            if entry:
                metadata["datasets"][entry["name"]] = entry
                metadata["total_parcels"] += entry["feature_count"]
                metadata["total_size_bytes"] += entry["pmtiles_size_bytes"]
                processed += 1

                # Save metadata after each successful upload
                save_metadata(metadata)
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Processing complete!")
    print(f"  Processed: {processed}")
    print(f"  Failed: {failed}")
    print(f"  Total parcels: {metadata['total_parcels']:,}")
    print(f"  Total size: {metadata['total_size_bytes'] / (1024**3):.2f} GB")
    print(f"  Metadata saved to: {METADATA_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
