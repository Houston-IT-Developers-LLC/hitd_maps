#!/usr/bin/env python3
"""
Convert GeoJSON files from R2 to PMTiles format.
- Downloads from R2
- Reprojects to WGS84 using GDAL
- Converts to PMTiles using tippecanoe
- Uploads PMTiles back to R2
"""

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

def run_cmd(cmd, check=True):
    """Run a shell command"""
    print(f"  Running: {' '.join(cmd[:3])}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  Error: {result.stderr}")
        return False
    return True

def get_r2_files():
    """List all GeoJSON files in R2"""
    result = subprocess.run([
        "aws", "s3", "ls", f"s3://{R2_BUCKET}/parcels/",
        "--endpoint-url", R2_ENDPOINT
    ], capture_output=True, text=True)

    files = []
    for line in result.stdout.strip().split('\n'):
        if line and '.geojson' in line:
            parts = line.split()
            if len(parts) >= 4:
                filename = parts[-1]
                size = parts[2]
                files.append((filename, size))
    return files

def download_from_r2(filename, dest_path):
    """Download a file from R2"""
    return run_cmd([
        "aws", "s3", "cp",
        f"s3://{R2_BUCKET}/parcels/{filename}",
        dest_path,
        "--endpoint-url", R2_ENDPOINT
    ])

def detect_projection(geojson_path):
    """Try to detect the projection from coordinate values"""
    with open(geojson_path) as f:
        data = json.load(f)

    if not data.get('features'):
        return None

    # Get first coordinate
    coords = data['features'][0].get('geometry', {}).get('coordinates', [])
    while isinstance(coords, list) and coords and isinstance(coords[0], list):
        coords = coords[0]

    if not coords or len(coords) < 2:
        return None

    x, y = coords[0], coords[1]

    # Already WGS84
    if abs(x) <= 180 and abs(y) <= 90:
        return "EPSG:4326"

    # Web Mercator (large negative X for US, large Y)
    if x < -5000000 and abs(y) > 1000000:
        return "EPSG:3857"

    # Texas State Plane South Central (Harris, Bexar, Travis)
    if 2000000 < x < 5000000 and 10000000 < y < 20000000:
        return "EPSG:2278"

    # Texas State Plane North Central (Dallas, Tarrant, Denton)
    if 2000000 < x < 4000000 and 6000000 < y < 10000000:
        return "EPSG:2276"

    # Texas State Plane Central
    if 500000 < x < 2000000 and 8000000 < y < 12000000:
        return "EPSG:2277"

    # Michigan Oblique Mercator
    if 10000000 < x < 15000000 and 0 < y < 1500000:
        return "EPSG:3078"

    # Michigan State Plane South
    if 5000000 < x < 10000000 and 0 < y < 3000000:
        return "EPSG:2253"

    # Pennsylvania South
    if 1000000 < x < 3500000 and 0 < y < 1000000:
        return "EPSG:2272"

    # Wisconsin Transverse Mercator
    if 0 < x < 1000000 and 0 < y < 1000000:
        return "EPSG:3071"

    # Georgia
    if 500000 < x < 1500000 and 0 < y < 2000000:
        return "EPSG:2240"

    # New York Long Island
    if 800000 < x < 1500000 and 100000 < y < 500000:
        return "EPSG:2263"

    # Fallback - assume Web Mercator for large values
    if abs(x) > 100000 or abs(y) > 100000:
        return "EPSG:3857"

    return None

def reproject_geojson(input_path, output_path, source_crs):
    """Reproject GeoJSON to WGS84 using ogr2ogr"""
    if source_crs == "EPSG:4326":
        # Already in WGS84, just copy
        subprocess.run(["cp", input_path, output_path])
        return True

    cmd = [
        "ogr2ogr",
        "-f", "GeoJSON",
        "-s_srs", source_crs,
        "-t_srs", "EPSG:4326",
        output_path,
        input_path
    ]
    return run_cmd(cmd)

def convert_to_pmtiles(geojson_path, pmtiles_path, layer_name="parcels"):
    """Convert GeoJSON to PMTiles using tippecanoe"""
    cmd = [
        "tippecanoe",
        "-o", pmtiles_path,
        "-l", layer_name,
        "-zg",  # Auto zoom levels
        "--drop-densest-as-needed",  # Handle dense areas
        "--extend-zooms-if-still-dropping",
        "--force",  # Overwrite existing
        geojson_path
    ]
    return run_cmd(cmd)

def upload_to_r2(local_path, remote_name):
    """Upload file to R2"""
    return run_cmd([
        "aws", "s3", "cp",
        local_path,
        f"s3://{R2_BUCKET}/tiles/{remote_name}",
        "--endpoint-url", R2_ENDPOINT,
        "--content-type", "application/x-protobuf"
    ])

def process_file(filename):
    """Process a single GeoJSON file"""
    print(f"\n{'='*60}")
    print(f"Processing: {filename}")
    print('='*60)

    base_name = filename.replace('.geojson', '')
    pmtiles_name = f"{base_name}.pmtiles"

    with tempfile.TemporaryDirectory() as tmpdir:
        geojson_path = os.path.join(tmpdir, filename)
        reprojected_path = os.path.join(tmpdir, "reprojected.geojson")
        pmtiles_path = os.path.join(tmpdir, pmtiles_name)

        # Download
        print("1. Downloading from R2...")
        if not download_from_r2(filename, geojson_path):
            return False

        # Detect projection
        print("2. Detecting projection...")
        source_crs = detect_projection(geojson_path)
        if not source_crs:
            print("  Could not detect projection, skipping")
            return False
        print(f"  Detected: {source_crs}")

        # Reproject
        print("3. Reprojecting to WGS84...")
        if not reproject_geojson(geojson_path, reprojected_path, source_crs):
            return False

        # Convert to PMTiles
        print("4. Converting to PMTiles...")
        if not convert_to_pmtiles(reprojected_path, pmtiles_path):
            return False

        # Get file size
        size_mb = os.path.getsize(pmtiles_path) / (1024 * 1024)
        print(f"  PMTiles size: {size_mb:.1f} MB")

        # Upload
        print("5. Uploading to R2...")
        if not upload_to_r2(pmtiles_path, pmtiles_name):
            return False

        print(f"✓ Complete! URL: {R2_PUBLIC_URL}/tiles/{pmtiles_name}")
        return True

def main():
    if len(sys.argv) > 1:
        # Process specific file(s)
        for filename in sys.argv[1:]:
            if not filename.endswith('.geojson'):
                filename += '.geojson'
            process_file(filename)
    else:
        # List available files
        print("Fetching file list from R2...")
        files = get_r2_files()
        print(f"\nFound {len(files)} GeoJSON files in R2:\n")
        for filename, size in sorted(files)[:20]:
            print(f"  {filename} ({size})")
        if len(files) > 20:
            print(f"  ... and {len(files) - 20} more")
        print("\nUsage: python convert_to_pmtiles.py <filename>")
        print("Example: python convert_to_pmtiles.py parcels_tx_harris.geojson")

if __name__ == "__main__":
    main()
