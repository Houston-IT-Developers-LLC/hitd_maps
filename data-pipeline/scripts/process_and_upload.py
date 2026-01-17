#!/usr/bin/env python3
"""
Process and Upload Pipeline - Continuous monitoring script

Watches for new GeoJSON files, processes them to PMTiles, uploads to R2, and cleans up.
Runs in a loop until stopped.
"""

import subprocess
import os
import sys
import re
import time
from pathlib import Path
from datetime import datetime
import boto3
from botocore.config import Config

DATA_PIPELINE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"

# R2 configuration
R2_ENDPOINT = 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com'
R2_ACCESS_KEY = 'ecd653afe3300fdc045b9980df0dbb14'
R2_SECRET_KEY = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'
R2_BUCKET = 'gspot-tiles'

MIN_FILE_SIZE = 10000  # 10KB minimum to consider valid


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


def get_first_coordinate(geojson_path: Path) -> tuple:
    """Extract first coordinate from a GeoJSON file."""
    try:
        with open(geojson_path, 'r') as f:
            content = f.read(100000)

        # Try various coordinate patterns
        patterns = [
            r'"coordinates"\s*:\s*\[\s*\[\s*\[\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)',
            r'"coordinates"\s*:\s*\[\s*\[\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)',
            r'"coordinates"\s*:\s*\[\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)',
            r'"coordinates"\s*:\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1)), float(match.group(2))
    except:
        pass
    return None, None


def is_wgs84_coords(lon: float, lat: float) -> bool:
    """Check if coordinates are in WGS84 range."""
    if lon is None or lat is None:
        return False
    return -180 <= lon <= 180 and -90 <= lat <= 90


def needs_reprojection(geojson_path: Path) -> bool:
    """Check if file needs reprojection."""
    lon, lat = get_first_coordinate(geojson_path)
    return not is_wgs84_coords(lon, lat)


def reproject_file(input_path: Path, output_path: Path) -> bool:
    """Reproject file to WGS84."""
    # Try auto-detect first
    try:
        cmd = [
            "ogr2ogr", "-f", "GeoJSON",
            "-t_srs", "EPSG:4326",
            str(output_path), str(input_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=3600)
        if result.returncode == 0 and output_path.exists():
            lon, lat = get_first_coordinate(output_path)
            if is_wgs84_coords(lon, lat):
                return True
            output_path.unlink()
    except:
        if output_path.exists():
            output_path.unlink()

    # Try EPSG:3857 (Web Mercator - most common)
    try:
        cmd = [
            "ogr2ogr", "-f", "GeoJSON",
            "-s_srs", "EPSG:3857",
            "-t_srs", "EPSG:4326",
            str(output_path), str(input_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=3600)
        if result.returncode == 0 and output_path.exists():
            lon, lat = get_first_coordinate(output_path)
            if is_wgs84_coords(lon, lat):
                return True
            output_path.unlink()
    except:
        if output_path.exists():
            output_path.unlink()

    return False


def generate_pmtiles(geojson_path: Path, pmtiles_path: Path) -> bool:
    """Generate PMTiles using tippecanoe."""
    try:
        cmd = [
            "tippecanoe",
            "-o", str(pmtiles_path),
            "-z", "15", "-Z", "5",
            "--drop-densest-as-needed",
            "--extend-zooms-if-still-dropping",
            "-l", "parcels",
            "--force",
            str(geojson_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=7200)
        return result.returncode == 0 and pmtiles_path.exists() and pmtiles_path.stat().st_size > 10000
    except Exception as e:
        print(f"  Tippecanoe error: {e}")
        return False


def upload_to_r2(local_path: Path, r2_key: str) -> bool:
    """Upload file to R2."""
    try:
        client = get_r2_client()
        client.upload_file(
            str(local_path),
            R2_BUCKET,
            r2_key,
            ExtraArgs={'ContentType': 'application/octet-stream'}
        )
        return True
    except Exception as e:
        print(f"  Upload error: {e}")
        return False


def process_file(geojson_path: Path) -> dict:
    """Process a single GeoJSON file through the full pipeline."""
    name = geojson_path.stem
    result = {"file": name, "success": False, "steps": []}

    # Check if already in R2
    r2_key = f"parcels/{name}.pmtiles"
    if file_exists_in_r2(r2_key):
        result["success"] = True
        result["steps"].append("Already in R2")
        # Clean up local file
        try:
            geojson_path.unlink()
            result["steps"].append("Cleaned local GeoJSON")
        except:
            pass
        return result

    try:
        # Step 1: Reproject if needed
        if needs_reprojection(geojson_path):
            reprojected_dir = GEOJSON_DIR / "reprojected_wgs84"
            reprojected_dir.mkdir(parents=True, exist_ok=True)
            reprojected_path = reprojected_dir / geojson_path.name

            if reproject_file(geojson_path, reprojected_path):
                result["steps"].append("Reprojected to WGS84")
                source_geojson = reprojected_path
            else:
                result["steps"].append("FAILED: Reprojection failed")
                return result
        else:
            source_geojson = geojson_path
            result["steps"].append("Already WGS84")

        # Step 2: Generate PMTiles
        PMTILES_DIR.mkdir(parents=True, exist_ok=True)
        pmtiles_path = PMTILES_DIR / f"{name}.pmtiles"

        if generate_pmtiles(source_geojson, pmtiles_path):
            size_mb = pmtiles_path.stat().st_size / 1024 / 1024
            result["steps"].append(f"Generated PMTiles ({size_mb:.1f} MB)")
        else:
            result["steps"].append("FAILED: PMTiles generation failed")
            return result

        # Step 3: Upload to R2
        if upload_to_r2(pmtiles_path, r2_key):
            result["steps"].append(f"Uploaded to R2")
            result["success"] = True

            # Step 4: Cleanup
            try:
                geojson_path.unlink()
                result["steps"].append("Cleaned GeoJSON")
            except:
                pass

            try:
                if source_geojson != geojson_path and source_geojson.exists():
                    source_geojson.unlink()
            except:
                pass

            try:
                pmtiles_path.unlink()
                result["steps"].append("Cleaned PMTiles")
            except:
                pass
        else:
            result["steps"].append("FAILED: Upload failed")

    except Exception as e:
        result["steps"].append(f"Error: {str(e)[:50]}")

    return result


def is_file_complete(path: Path) -> bool:
    """Check if a file is complete (not being written to)."""
    try:
        size1 = path.stat().st_size
        time.sleep(2)
        size2 = path.stat().st_size
        return size1 == size2 and size1 > MIN_FILE_SIZE
    except:
        return False


def main():
    """Main monitoring loop."""
    print("=" * 70)
    print("  PROCESS AND UPLOAD PIPELINE")
    print("=" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  Watching: {GEOJSON_DIR}")
    print("=" * 70)

    GEOJSON_DIR.mkdir(parents=True, exist_ok=True)
    PMTILES_DIR.mkdir(parents=True, exist_ok=True)

    processed = set()

    while True:
        # Find all GeoJSON files
        geojson_files = list(GEOJSON_DIR.glob("parcels_*.geojson"))

        # Filter to complete files not yet processed
        to_process = []
        for f in geojson_files:
            if f.name not in processed and is_file_complete(f):
                to_process.append(f)

        if to_process:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Found {len(to_process)} files to process")

            for geojson_path in to_process:
                print(f"\n  Processing: {geojson_path.name}")
                result = process_file(geojson_path)

                status = "OK" if result["success"] else "FAIL"
                steps = ", ".join(result["steps"][:3])
                print(f"    {status}: {steps}")

                processed.add(geojson_path.name)

        # Sleep before next check
        time.sleep(10)


if __name__ == "__main__":
    main()
