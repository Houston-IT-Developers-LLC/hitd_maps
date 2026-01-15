#!/usr/bin/env python3
"""
Upload PMTiles files to Cloudflare R2 and generate metadata manifest.
Runs continuously, uploading new files as they become available.
"""

import os
import json
import boto3
from botocore.config import Config
from datetime import datetime
from pathlib import Path
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

# Directories
BASE_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline")
PMTILES_DIR = BASE_DIR / "output" / "pmtiles"
GEOJSON_DIR = BASE_DIR / "output" / "geojson" / "counties"
DOCS_DIR = BASE_DIR / "docs"

# Tracking files
UPLOADED_TRACKER = BASE_DIR / "logs" / "uploaded_files.json"
MANIFEST_FILE = DOCS_DIR / "PARCEL_DATA_MANIFEST.json"

def get_r2_client():
    """Create R2 client."""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            connect_timeout=60,
            read_timeout=300
        )
    )

def load_uploaded_tracker():
    """Load list of already uploaded files."""
    if UPLOADED_TRACKER.exists():
        with open(UPLOADED_TRACKER, 'r') as f:
            return set(json.load(f))
    return set()

def save_uploaded_tracker(uploaded):
    """Save list of uploaded files."""
    UPLOADED_TRACKER.parent.mkdir(parents=True, exist_ok=True)
    with open(UPLOADED_TRACKER, 'w') as f:
        json.dump(list(uploaded), f)

def load_manifest():
    """Load existing manifest."""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, 'r') as f:
            return json.load(f)
    return {
        "manifest_version": "1.0",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "r2_bucket": R2_BUCKET,
        "r2_endpoint": R2_ENDPOINT,
        "total_datasets": 0,
        "total_size_bytes": 0,
        "datasets": {}
    }

def save_manifest(manifest):
    """Save manifest."""
    manifest["updated_at"] = datetime.now().isoformat()
    manifest["total_datasets"] = len(manifest["datasets"])
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)

def get_next_quarter():
    """Get the first day of next quarter."""
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    if quarter == 4:
        return datetime(now.year + 1, 1, 1)
    return datetime(now.year, (quarter * 3) + 1, 1)

def get_geojson_mod_time(pmtiles_name):
    """Get modification time of corresponding GeoJSON file."""
    geojson_name = pmtiles_name.replace('.pmtiles', '.geojson')
    geojson_path = GEOJSON_DIR / geojson_name
    if geojson_path.exists():
        return datetime.fromtimestamp(geojson_path.stat().st_mtime)
    return datetime.now()

def upload_file(pmtiles_path, client=None):
    """Upload a single PMTiles file to R2."""
    if client is None:
        client = get_r2_client()

    filename = pmtiles_path.name
    s3_key = f"parcels/{filename}"
    file_size = pmtiles_path.stat().st_size

    print(f"  Uploading {filename} ({file_size / (1024*1024):.1f} MB)...")

    try:
        # Use multipart for files > 100MB
        config = boto3.s3.transfer.TransferConfig(
            multipart_threshold=100 * 1024 * 1024,
            max_concurrency=10,
            multipart_chunksize=50 * 1024 * 1024
        )

        client.upload_file(
            str(pmtiles_path),
            R2_BUCKET,
            s3_key,
            Config=config
        )

        return {
            "success": True,
            "filename": filename,
            "s3_key": s3_key,
            "size_bytes": file_size
        }
    except Exception as e:
        print(f"  ERROR uploading {filename}: {e}")
        return {
            "success": False,
            "filename": filename,
            "error": str(e)
        }

def parse_dataset_name(filename):
    """Parse dataset info from filename like parcels_tx_harris.pmtiles"""
    name = filename.replace('parcels_', '').replace('.pmtiles', '')
    parts = name.split('_')

    state = parts[0].upper() if parts else "UNKNOWN"
    county = '_'.join(parts[1:]) if len(parts) > 1 else "statewide"

    # Clean up county name
    county = county.replace('_v2', '').replace('_v3', '')

    return {
        "state": state,
        "county": county.replace('_', ' ').title(),
        "dataset_id": name
    }

def main():
    """Main upload loop."""
    delete_after = "--delete" in sys.argv
    continuous = "--watch" in sys.argv
    parallel = 4  # Upload 4 files in parallel

    print("=" * 60)
    print("PMTiles Upload to Cloudflare R2")
    print("=" * 60)
    print(f"R2 Bucket: {R2_BUCKET}")
    print(f"Delete after upload: {delete_after}")
    print(f"Watch mode: {continuous}")
    print(f"Parallel uploads: {parallel}")
    print()

    uploaded = load_uploaded_tracker()
    manifest = load_manifest()

    while True:
        # Find PMTiles files not yet uploaded
        pmtiles_files = list(PMTILES_DIR.glob("*.pmtiles"))
        to_upload = [f for f in pmtiles_files if f.name not in uploaded]

        if not to_upload:
            if continuous:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No new files. Waiting...")
                time.sleep(30)
                continue
            else:
                print("No new files to upload.")
                break

        print(f"\nFound {len(to_upload)} files to upload")

        # Upload files in parallel
        client = get_r2_client()

        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {executor.submit(upload_file, f, client): f for f in to_upload}

            for future in as_completed(futures):
                pmtiles_path = futures[future]
                result = future.result()

                if result["success"]:
                    filename = result["filename"]
                    uploaded.add(filename)
                    save_uploaded_tracker(uploaded)

                    # Update manifest
                    dataset_info = parse_dataset_name(filename)
                    extracted_at = get_geojson_mod_time(filename)

                    manifest["datasets"][dataset_info["dataset_id"]] = {
                        "state": dataset_info["state"],
                        "county": dataset_info["county"],
                        "pmtiles_file": filename,
                        "r2_key": result["s3_key"],
                        "size_bytes": result["size_bytes"],
                        "extracted_at": extracted_at.isoformat(),
                        "uploaded_at": datetime.now().isoformat(),
                        "source_type": "arcgis_rest_api",
                        "update_frequency": "quarterly",
                        "next_update_estimate": get_next_quarter().isoformat()
                    }
                    manifest["total_size_bytes"] += result["size_bytes"]
                    save_manifest(manifest)

                    print(f"  DONE: {filename}")

                    # Delete local files if requested
                    if delete_after:
                        pmtiles_path.unlink()
                        geojson_path = GEOJSON_DIR / filename.replace('.pmtiles', '.geojson')
                        if geojson_path.exists():
                            geojson_path.unlink()
                        print(f"  Deleted local files for {filename}")

        if not continuous:
            break

    # Final summary
    print()
    print("=" * 60)
    print("Upload Summary")
    print("=" * 60)
    print(f"Total datasets: {len(manifest['datasets'])}")
    print(f"Total size: {manifest['total_size_bytes'] / (1024**3):.2f} GB")
    print(f"Manifest saved to: {MANIFEST_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
