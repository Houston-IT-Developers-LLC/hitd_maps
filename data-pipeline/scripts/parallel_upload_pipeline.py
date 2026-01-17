#!/usr/bin/env python3
"""
Parallel Upload Pipeline - Process and upload GeoJSON files to R2

Steps for each file:
1. Reproject to WGS84 (EPSG:4326)
2. Generate PMTiles using tippecanoe
3. Upload to Cloudflare R2
4. Delete local file to free space

Runs multiple workers in parallel.
"""

import asyncio
import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import boto3
from botocore.config import Config

DATA_PIPELINE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
REPROJECTED_DIR = GEOJSON_DIR / "reprojected"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"

# R2 configuration
R2_ENDPOINT = os.environ.get('R2_ENDPOINT', 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com')
R2_ACCESS_KEY = os.environ.get('R2_ACCESS_KEY', 'ecd653afe3300fdc045b9980df0dbb14')
R2_SECRET_KEY = os.environ.get('R2_SECRET_KEY', 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35')
R2_BUCKET = os.environ.get('R2_BUCKET', 'gspot-tiles')


def get_r2_client():
    """Get R2 client."""
    return boto3.client('s3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version='s3v4')
    )


def file_exists_in_r2(key: str) -> bool:
    """Check if file exists in R2."""
    try:
        client = get_r2_client()
        client.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False


def process_single_file(geojson_path: Path) -> dict:
    """Process a single GeoJSON file through the full pipeline."""
    start = datetime.now()
    name = geojson_path.stem
    result = {
        "file": name,
        "success": False,
        "steps": []
    }

    # Check if already in R2
    r2_key = f"parcels/{name}.pmtiles"
    if file_exists_in_r2(r2_key):
        result["success"] = True
        result["steps"].append("Already in R2")
        # Delete local file
        try:
            geojson_path.unlink()
            result["steps"].append("Deleted local GeoJSON")
        except:
            pass
        return result

    try:
        # Step 1: Reproject to WGS84
        reprojected_path = REPROJECTED_DIR / geojson_path.name
        if not reprojected_path.exists():
            cmd = [
                "ogr2ogr", "-f", "GeoJSON",
                "-t_srs", "EPSG:4326",
                str(reprojected_path), str(geojson_path)
            ]
            proc = subprocess.run(cmd, capture_output=True, timeout=3600)
            if proc.returncode != 0:
                result["steps"].append(f"Reproject failed: {proc.stderr[:200]}")
                return result
            result["steps"].append("Reprojected")
        else:
            result["steps"].append("Already reprojected")

        # Step 2: Generate PMTiles
        pmtiles_path = PMTILES_DIR / f"{name}.pmtiles"
        if not pmtiles_path.exists():
            cmd = [
                "tippecanoe",
                "-o", str(pmtiles_path),
                "-z", "15", "-Z", "5",
                "--drop-densest-as-needed",
                "--extend-zooms-if-still-dropping",
                "-l", "parcels",
                "--force",
                str(reprojected_path)
            ]
            proc = subprocess.run(cmd, capture_output=True, timeout=7200)
            if proc.returncode != 0:
                result["steps"].append(f"Tippecanoe failed: {proc.stderr[:200]}")
                return result
            result["steps"].append("Generated PMTiles")
        else:
            result["steps"].append("PMTiles exists")

        # Step 3: Upload to R2
        if pmtiles_path.exists():
            client = get_r2_client()
            client.upload_file(
                str(pmtiles_path),
                R2_BUCKET,
                r2_key,
                ExtraArgs={'ContentType': 'application/octet-stream'}
            )
            result["steps"].append(f"Uploaded to R2: {r2_key}")

            # Step 4: Cleanup local files
            try:
                geojson_path.unlink()
                result["steps"].append("Deleted local GeoJSON")
            except:
                pass

            try:
                reprojected_path.unlink()
                result["steps"].append("Deleted reprojected")
            except:
                pass

            try:
                pmtiles_path.unlink()
                result["steps"].append("Deleted local PMTiles")
            except:
                pass

        result["success"] = True

    except Exception as e:
        result["steps"].append(f"Error: {str(e)[:200]}")

    result["duration"] = (datetime.now() - start).total_seconds()
    return result


def main():
    """Main entry point."""
    print("=" * 60)
    print("  PARALLEL UPLOAD PIPELINE")
    print("=" * 60)
    print(f"  Started: {datetime.now().isoformat()}")

    # Ensure directories exist
    REPROJECTED_DIR.mkdir(parents=True, exist_ok=True)
    PMTILES_DIR.mkdir(parents=True, exist_ok=True)

    # Get all GeoJSON files
    geojson_files = list(GEOJSON_DIR.glob("parcels_*.geojson"))
    print(f"  Files to process: {len(geojson_files)}")
    print("=" * 60)

    if not geojson_files:
        print("No files to process!")
        return

    # Process in parallel
    max_workers = 8  # Balance between speed and memory
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_file, f): f for f in geojson_files}

        for i, future in enumerate(futures):
            try:
                result = future.result(timeout=14400)  # 4 hour timeout
                results.append(result)

                status = "✓" if result["success"] else "✗"
                print(f"[{i+1}/{len(geojson_files)}] {status} {result['file']}: {', '.join(result['steps'][:3])}")

            except Exception as e:
                print(f"[{i+1}/{len(geojson_files)}] ✗ Error: {e}")

    # Summary
    successful = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Total: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(results) - successful}")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
