#!/usr/bin/env python3
"""Process all GeoJSON files in data/downloads/ and upload to R2."""

import os
import subprocess
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import boto3
from botocore.config import Config

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

BASE_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline")
DOWNLOADS_DIR = BASE_DIR / "data" / "downloads"
PMTILES_DIR = BASE_DIR / "output" / "pmtiles"

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version='s3v4')
    )

def file_exists_on_r2(key):
    """Check if file exists on R2."""
    try:
        s3 = get_s3_client()
        s3.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def process_file(geojson_path):
    """Process a single GeoJSON file."""
    name = geojson_path.stem
    pmtiles_name = f"{name}.pmtiles"
    r2_key = f"parcels/{pmtiles_name}"
    
    # Skip if already on R2
    if file_exists_on_r2(r2_key):
        print(f"[SKIP] {name} - already on R2")
        return {"name": name, "status": "skipped"}
    
    pmtiles_path = PMTILES_DIR / pmtiles_name
    PMTILES_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Convert to PMTiles
        print(f"[CONVERT] {name}...")
        result = subprocess.run(
            [
                'tippecanoe',
                '-o', str(pmtiles_path),
                '--force',
                '--no-feature-limit',
                '--no-tile-size-limit',
                '-zg',  # Auto zoom
                '--drop-densest-as-needed',
                '--extend-zooms-if-still-dropping',
                '-l', 'parcels',
                str(geojson_path)
            ],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode != 0:
            print(f"[ERROR] {name}: {result.stderr[:200]}")
            return {"name": name, "status": "failed", "error": result.stderr[:200]}
        
        if not pmtiles_path.exists():
            return {"name": name, "status": "failed", "error": "No output file"}
        
        # Upload to R2
        print(f"[UPLOAD] {name} ({pmtiles_path.stat().st_size / 1024 / 1024:.1f} MB)...")
        s3 = get_s3_client()
        s3.upload_file(
            str(pmtiles_path),
            R2_BUCKET,
            r2_key,
            ExtraArgs={'ContentType': 'application/x-protobuf'}
        )
        
        # Cleanup local PMTiles file
        pmtiles_path.unlink()
        
        print(f"[DONE] {name}")
        return {"name": name, "status": "success"}
        
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {name}")
        return {"name": name, "status": "timeout"}
    except Exception as e:
        print(f"[ERROR] {name}: {str(e)}")
        return {"name": name, "status": "error", "error": str(e)}

def main():
    import sys
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    print("=" * 60)
    print("Processing Downloads Directory")
    print("=" * 60)
    print(f"Workers: {workers}")
    print(f"Source: {DOWNLOADS_DIR}")
    print()
    
    # Find all GeoJSON files
    files = list(DOWNLOADS_DIR.glob("*.geojson"))
    print(f"Found {len(files)} GeoJSON files")
    
    # Sort by size (smallest first for quick wins)
    files.sort(key=lambda f: f.stat().st_size)
    
    results = {"success": 0, "skipped": 0, "failed": 0}
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_file, f): f for f in files}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results[result["status"]] = results.get(result["status"], 0) + 1
            except Exception as e:
                print(f"Exception: {e}")
                results["failed"] += 1
    
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Success: {results['success']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Failed: {results['failed']}")

if __name__ == "__main__":
    main()
