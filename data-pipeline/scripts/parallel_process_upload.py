#!/usr/bin/env python3
"""
Parallel processing: reproject, convert to PMTiles, upload to R2, and cleanup.
Uses multiple workers for parallel processing of large parcel datasets.
"""

import os
import json
import subprocess
import boto3
from botocore.config import Config
from datetime import datetime
from pathlib import Path
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

# Directories
BASE_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline")
GEOJSON_DIR = BASE_DIR / "output" / "geojson" / "counties"
REPROJECTED_DIR = BASE_DIR / "output" / "geojson" / "reprojected"
PMTILES_DIR = BASE_DIR / "output" / "pmtiles"
DOCS_DIR = BASE_DIR / "docs"
LOGS_DIR = BASE_DIR / "logs"

# Tracking
MANIFEST_FILE = DOCS_DIR / "PARCEL_DATA_MANIFEST.json"
PROCESSED_FILE = LOGS_DIR / "processed_files.json"

def load_processed():
    """Load list of already processed files."""
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_processed(processed):
    """Save list of processed files."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(list(processed), f)

def load_manifest():
    """Load manifest."""
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

def needs_reprojection(geojson_path):
    """Check if file needs reprojection by sampling first coordinate."""
    try:
        with open(geojson_path, 'r') as f:
            # Read first 50KB to find coordinates
            chunk = f.read(50000)
            import re
            # Look for coordinate pattern: [[[-118.xxx, 34.xxx or [[[[-118.xxx, 34.xxx
            match = re.search(r'\[\[\[+([-\d.]+)', chunk)
            if match:
                x = float(match.group(1))
                # If |X| > 180, it's in a projected CRS (Web Mercator, State Plane, etc.)
                if abs(x) > 180:
                    return True
            return False
    except Exception as e:
        print(f"  Warning: Could not check coordinates: {e}")
        return False

def get_feature_count(geojson_path):
    """Get feature count from GeoJSON."""
    try:
        result = subprocess.run(
            ['ogrinfo', '-so', '-al', str(geojson_path)],
            capture_output=True, text=True, timeout=60
        )
        for line in result.stdout.split('\n'):
            if 'Feature Count:' in line:
                return int(line.split(':')[1].strip())
    except:
        pass
    return 0

def get_next_quarter():
    """Get next quarter date."""
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    if quarter == 4:
        return datetime(now.year + 1, 1, 1)
    return datetime(now.year, (quarter * 3) + 1, 1)

def process_single_file(geojson_path_str):
    """Process a single GeoJSON file: reproject, convert, upload, cleanup."""
    geojson_path = Path(geojson_path_str)
    basename = geojson_path.stem  # e.g., parcels_tx_harris
    log_file = LOGS_DIR / f"process_{basename}.log"

    def log(msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}"
        print(line)
        with open(log_file, 'a') as f:
            f.write(line + "\n")

    log(f"Starting: {basename}")
    log(f"File size: {geojson_path.stat().st_size / (1024*1024):.1f} MB")

    try:
        # Get metadata before processing
        file_size = geojson_path.stat().st_size
        mod_time = datetime.fromtimestamp(geojson_path.stat().st_mtime)
        feature_count = get_feature_count(geojson_path)
        log(f"Feature count: {feature_count:,}")

        # Check if reprojection needed
        reprojected_path = REPROJECTED_DIR / f"{basename}_wgs84.geojson"
        REPROJECTED_DIR.mkdir(parents=True, exist_ok=True)

        if needs_reprojection(geojson_path):
            log("Reprojecting from EPSG:3857 to WGS84...")
            # Force source CRS to EPSG:3857 (Web Mercator) since many ArcGIS exports
            # incorrectly label Web Mercator coordinates as WGS84
            result = subprocess.run([
                'ogr2ogr', '-f', 'GeoJSON',
                '-s_srs', 'EPSG:3857',  # Source: Web Mercator
                '-t_srs', 'EPSG:4326',   # Target: WGS84
                str(reprojected_path),
                str(geojson_path)
            ], capture_output=True, text=True, timeout=7200)

            if result.returncode != 0:
                log(f"Reprojection failed: {result.stderr}")
                return {"success": False, "file": basename, "error": "reprojection failed"}

            input_file = reprojected_path
            log("Reprojection complete")
        else:
            input_file = geojson_path
            log("Already in WGS84")

        # Convert to PMTiles
        PMTILES_DIR.mkdir(parents=True, exist_ok=True)
        pmtiles_path = PMTILES_DIR / f"{basename}.pmtiles"

        log("Converting to PMTiles...")
        # Use fixed zoom levels instead of -zg to avoid "can't guess maxzoom" errors
        result = subprocess.run([
            'tippecanoe',
            '-o', str(pmtiles_path),
            '--force',
            '--no-feature-limit',
            '--no-tile-size-limit',
            '-z14',  # Max zoom 14 for parcel data
            '--drop-densest-as-needed',
            '--extend-zooms-if-still-dropping',
            '--layer', 'parcels',
            '--name', f'parcels_{basename}',
            '--attribution', 'GSpot Outdoors',
            str(input_file)
        ], capture_output=True, text=True, timeout=7200)

        if result.returncode != 0:
            log(f"tippecanoe failed: {result.stderr}")
            return {"success": False, "file": basename, "error": "tippecanoe failed"}

        pmtiles_size = pmtiles_path.stat().st_size
        log(f"PMTiles created: {pmtiles_size / (1024*1024):.1f} MB")

        # Upload to R2
        log("Uploading to R2...")
        client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            config=Config(
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                connect_timeout=60,
                read_timeout=600
            )
        )

        s3_key = f"parcels/{basename}.pmtiles"
        config = boto3.s3.transfer.TransferConfig(
            multipart_threshold=100 * 1024 * 1024,
            max_concurrency=10,
            multipart_chunksize=50 * 1024 * 1024
        )

        client.upload_file(str(pmtiles_path), R2_BUCKET, s3_key, Config=config)
        log(f"Uploaded to r2://{R2_BUCKET}/{s3_key}")

        # Cleanup local files
        log("Cleaning up local files...")
        geojson_path.unlink()
        if reprojected_path.exists():
            reprojected_path.unlink()
        pmtiles_path.unlink()

        log("DONE!")

        # Return metadata
        return {
            "success": True,
            "file": basename,
            "dataset_id": basename.replace('parcels_', ''),
            "feature_count": feature_count,
            "geojson_size_bytes": file_size,
            "pmtiles_size_bytes": pmtiles_size,
            "extracted_at": mod_time.isoformat(),
            "uploaded_at": datetime.now().isoformat(),
            "r2_key": s3_key
        }

    except Exception as e:
        log(f"ERROR: {e}")
        return {"success": False, "file": basename, "error": str(e)}

def main():
    """Main processing loop."""
    # Number of parallel workers (memory-intensive, so limit)
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4

    print("=" * 60)
    print("Parallel Parcel Data Processing & Upload")
    print("=" * 60)
    print(f"Workers: {workers}")
    print(f"R2 Bucket: {R2_BUCKET}")
    print()

    # Create directories
    REPROJECTED_DIR.mkdir(parents=True, exist_ok=True)
    PMTILES_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Load tracking
    processed = load_processed()
    manifest = load_manifest()

    # Find files to process (skip already processed)
    geojson_files = list(GEOJSON_DIR.glob("*.geojson"))
    to_process = [f for f in geojson_files if f.stem not in processed]

    # Sort by size (smallest first for quick wins)
    to_process.sort(key=lambda f: f.stat().st_size)

    print(f"Found {len(to_process)} files to process")
    print(f"Already processed: {len(processed)}")
    print()

    if not to_process:
        print("Nothing to process!")
        return

    # Process in parallel
    success_count = 0
    fail_count = 0

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_single_file, str(f)): f for f in to_process}

        for future in as_completed(futures):
            result = future.result()

            if result["success"]:
                success_count += 1
                processed.add(result["file"])
                save_processed(processed)

                # Update manifest
                dataset_id = result["dataset_id"]
                parts = dataset_id.split('_')
                state = parts[0].upper() if parts else "UNKNOWN"
                county = '_'.join(parts[1:]).replace('_v2', '').replace('_v3', '') if len(parts) > 1 else "statewide"

                manifest["datasets"][dataset_id] = {
                    "state": state,
                    "county": county.replace('_', ' ').title(),
                    "pmtiles_file": f"{result['file']}.pmtiles",
                    "r2_key": result["r2_key"],
                    "feature_count": result["feature_count"],
                    "geojson_size_bytes": result["geojson_size_bytes"],
                    "pmtiles_size_bytes": result["pmtiles_size_bytes"],
                    "extracted_at": result["extracted_at"],
                    "uploaded_at": result["uploaded_at"],
                    "source_type": "arcgis_rest_api",
                    "update_frequency": "quarterly",
                    "next_update_estimate": get_next_quarter().isoformat()
                }
                manifest["total_size_bytes"] += result["pmtiles_size_bytes"]
                save_manifest(manifest)

                print(f"[{success_count}/{len(to_process)}] SUCCESS: {result['file']}")
            else:
                fail_count += 1
                print(f"[FAILED] {result['file']}: {result.get('error', 'unknown')}")

    print()
    print("=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total datasets: {len(manifest['datasets'])}")
    print(f"Total size: {manifest['total_size_bytes'] / (1024**3):.2f} GB")
    print(f"Manifest: {MANIFEST_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
