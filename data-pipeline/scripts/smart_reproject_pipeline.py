#!/usr/bin/env python3
"""
Smart Reproject Pipeline - Properly reproject GeoJSON files and generate PMTiles

This script:
1. Detects if files need reprojection (coordinates outside WGS84 range)
2. Tries multiple source CRS options (EPSG:3857, state-specific EPSG codes)
3. Generates PMTiles with tippecanoe
4. Uploads to R2 and cleans up local files

Runs multiple workers in parallel.
"""

import subprocess
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.config import Config
import re

DATA_PIPELINE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
REPROJECTED_DIR = OUTPUT_DIR / "geojson" / "reprojected_wgs84"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"
LOGS_DIR = DATA_PIPELINE_DIR / "logs"

# R2 configuration
R2_ENDPOINT = os.environ.get('R2_ENDPOINT', 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com')
R2_ACCESS_KEY = os.environ.get('R2_ACCESS_KEY', 'ecd653afe3300fdc045b9980df0dbb14')
R2_SECRET_KEY = os.environ.get('R2_SECRET_KEY', 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35')
R2_BUCKET = os.environ.get('R2_BUCKET', 'gspot-tiles')

# Common source CRS options to try
COMMON_CRS = [
    "EPSG:3857",   # Web Mercator (most common)
    "EPSG:2227",   # California State Plane Zone 3 (NAD83)
    "EPSG:2276",   # Texas State Plane North Central (NAD83)
    "EPSG:2277",   # Texas State Plane Central
    "EPSG:2278",   # Texas State Plane South Central
    "EPSG:2926",   # Washington State Plane North (NAD83)
    "EPSG:2283",   # Virginia State Plane North (NAD83)
    "EPSG:2264",   # North Carolina State Plane (NAD83)
    "EPSG:2248",   # Maryland State Plane (NAD83)
    "EPSG:3435",   # Illinois State Plane East (NAD83)
    "EPSG:2236",   # Florida State Plane East (NAD83)
    "EPSG:3734",   # Ohio State Plane North (NAD83)
    "EPSG:3433",   # Arkansas State Plane North (NAD83)
    "EPSG:26910",  # UTM Zone 10N
    "EPSG:26911",  # UTM Zone 11N
    "EPSG:26912",  # UTM Zone 12N
    "EPSG:26913",  # UTM Zone 13N
    "EPSG:26914",  # UTM Zone 14N
    "EPSG:26915",  # UTM Zone 15N
    "EPSG:26916",  # UTM Zone 16N
    "EPSG:26917",  # UTM Zone 17N
    "EPSG:26918",  # UTM Zone 18N
    "EPSG:26919",  # UTM Zone 19N
]


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
            # Read just enough to get first feature
            content = f.read(100000)

        # Quick regex to find first coordinates
        match = re.search(r'"coordinates"\s*:\s*\[\s*\[\s*\[\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)', content)
        if match:
            return float(match.group(1)), float(match.group(2))

        match = re.search(r'"coordinates"\s*:\s*\[\s*\[\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)', content)
        if match:
            return float(match.group(1)), float(match.group(2))

        match = re.search(r'"coordinates"\s*:\s*\[\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)', content)
        if match:
            return float(match.group(1)), float(match.group(2))

        match = re.search(r'"coordinates"\s*:\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)', content)
        if match:
            return float(match.group(1)), float(match.group(2))

    except Exception as e:
        print(f"Error reading {geojson_path}: {e}")
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


def try_reproject(input_path: Path, output_path: Path, source_crs: str) -> bool:
    """Try to reproject file with given source CRS."""
    try:
        cmd = [
            "ogr2ogr", "-f", "GeoJSON",
            "-s_srs", source_crs,
            "-t_srs", "EPSG:4326",
            str(output_path), str(input_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=3600)

        if result.returncode == 0 and output_path.exists():
            # Verify coordinates are now in WGS84 range
            lon, lat = get_first_coordinate(output_path)
            if is_wgs84_coords(lon, lat):
                return True
            else:
                output_path.unlink()
                return False
        return False
    except Exception as e:
        if output_path.exists():
            output_path.unlink()
        return False


def reproject_file(geojson_path: Path, output_path: Path) -> str:
    """Reproject file trying multiple source CRS options."""

    # First try auto-detect (if file has CRS info embedded)
    try:
        cmd = [
            "ogr2ogr", "-f", "GeoJSON",
            "-t_srs", "EPSG:4326",
            str(output_path), str(geojson_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=3600)

        if result.returncode == 0 and output_path.exists():
            lon, lat = get_first_coordinate(output_path)
            if is_wgs84_coords(lon, lat):
                return "auto-detect"
            output_path.unlink()
    except:
        if output_path.exists():
            output_path.unlink()

    # Try common CRS options
    for crs in COMMON_CRS:
        if try_reproject(geojson_path, output_path, crs):
            return crs

    return None


def generate_pmtiles(geojson_path: Path, pmtiles_path: Path, name: str) -> bool:
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
        print(f"Tippecanoe error for {name}: {e}")
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
        print(f"Upload error: {e}")
        return False


def process_single_file(geojson_path: Path) -> dict:
    """Process a single GeoJSON file through the full pipeline."""
    start = datetime.now()
    name = geojson_path.stem
    result = {
        "file": name,
        "success": False,
        "steps": [],
        "source_crs": None
    }

    # Check if already in R2
    r2_key = f"parcels/{name}.pmtiles"
    if file_exists_in_r2(r2_key):
        result["success"] = True
        result["steps"].append("Already in R2")
        return result

    try:
        # Step 1: Check if needs reprojection
        if not needs_reprojection(geojson_path):
            # Already WGS84, use directly
            reprojected_path = geojson_path
            result["steps"].append("Already WGS84")
        else:
            # Needs reprojection
            reprojected_path = REPROJECTED_DIR / geojson_path.name

            if reprojected_path.exists():
                # Check if existing reprojected file is valid
                if not needs_reprojection(reprojected_path):
                    result["steps"].append("Using existing reprojected file")
                else:
                    reprojected_path.unlink()

            if not reprojected_path.exists():
                source_crs = reproject_file(geojson_path, reprojected_path)
                if source_crs:
                    result["source_crs"] = source_crs
                    result["steps"].append(f"Reprojected from {source_crs}")
                else:
                    result["steps"].append("FAILED: Could not determine source CRS")
                    result["duration"] = (datetime.now() - start).total_seconds()
                    return result

        # Step 2: Generate PMTiles
        pmtiles_path = PMTILES_DIR / f"{name}.pmtiles"
        if pmtiles_path.exists() and pmtiles_path.stat().st_size > 10000:
            result["steps"].append("PMTiles exists")
        else:
            if generate_pmtiles(reprojected_path, pmtiles_path, name):
                result["steps"].append(f"Generated PMTiles ({pmtiles_path.stat().st_size / 1024 / 1024:.1f} MB)")
            else:
                result["steps"].append("FAILED: Tippecanoe failed")
                result["duration"] = (datetime.now() - start).total_seconds()
                return result

        # Step 3: Upload to R2
        if upload_to_r2(pmtiles_path, r2_key):
            result["steps"].append(f"Uploaded to R2: {r2_key}")

            # Step 4: Cleanup
            try:
                if reprojected_path != geojson_path and reprojected_path.exists():
                    reprojected_path.unlink()
                    result["steps"].append("Cleaned reprojected")
            except:
                pass

            try:
                pmtiles_path.unlink()
                result["steps"].append("Cleaned local PMTiles")
            except:
                pass

            result["success"] = True
        else:
            result["steps"].append("FAILED: Upload failed")

    except Exception as e:
        result["steps"].append(f"Error: {str(e)[:100]}")

    result["duration"] = (datetime.now() - start).total_seconds()
    return result


def main():
    """Main entry point."""
    print("=" * 70)
    print("  SMART REPROJECT & UPLOAD PIPELINE")
    print("=" * 70)
    print(f"  Started: {datetime.now().isoformat()}")

    # Ensure directories exist
    REPROJECTED_DIR.mkdir(parents=True, exist_ok=True)
    PMTILES_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Get all GeoJSON files (both original and previously reprojected)
    geojson_files = []

    # Add original files
    for f in GEOJSON_DIR.glob("parcels_*.geojson"):
        geojson_files.append(f)

    # Add files from the old reprojected directory that might need reprocessing
    old_reprojected = GEOJSON_DIR / "reprojected"
    if old_reprojected.exists():
        for f in old_reprojected.glob("parcels_*.geojson"):
            # Only add if we don't already have an original
            if not (GEOJSON_DIR / f.name).exists():
                geojson_files.append(f)

    print(f"  Files to process: {len(geojson_files)}")
    print("=" * 70)

    if not geojson_files:
        print("No files to process!")
        return

    # Process in parallel
    max_workers = 12
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_file, f): f for f in geojson_files}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            try:
                result = future.result(timeout=14400)
                results.append(result)

                status = "✓" if result["success"] else "✗"
                steps_str = ", ".join(result["steps"][:3])
                print(f"[{completed}/{len(geojson_files)}] {status} {result['file']}: {steps_str}")

            except Exception as e:
                print(f"[{completed}/{len(geojson_files)}] ✗ Error: {e}")

    # Summary
    successful = sum(1 for r in results if r.get("success"))
    crs_counts = {}
    for r in results:
        crs = r.get("source_crs")
        if crs:
            crs_counts[crs] = crs_counts.get(crs, 0) + 1

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Total: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(results) - successful}")

    if crs_counts:
        print("\n  Source CRS detected:")
        for crs, count in sorted(crs_counts.items(), key=lambda x: -x[1]):
            print(f"    {crs}: {count} files")

    print(f"\n  Completed: {datetime.now().isoformat()}")
    print("=" * 70)

    # Show failed files
    failed = [r for r in results if not r.get("success")]
    if failed:
        print("\n  FAILED FILES:")
        for r in failed[:20]:
            print(f"    - {r['file']}: {r['steps'][-1] if r['steps'] else 'Unknown error'}")
        if len(failed) > 20:
            print(f"    ... and {len(failed) - 20} more")


if __name__ == "__main__":
    main()
