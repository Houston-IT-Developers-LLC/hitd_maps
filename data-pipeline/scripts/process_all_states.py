#!/usr/bin/env python3
"""
Process all state GeoJSON files to PMTiles and upload to R2.
- Detects and reprojects Web Mercator data to WGS84
- Generates MBTiles with tippecanoe
- Converts to PMTiles
- Uploads to Cloudflare R2
"""

import json
import os
import glob
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "output"
GEOJSON_DIR = DATA_DIR / "geojson"
TILES_DIR = DATA_DIR / "tiles"
TIPPECANOE = "/opt/homebrew/bin/tippecanoe"

def check_coordinate_system(geojson_path):
    """Check if coordinates are WGS84 or Web Mercator."""
    try:
        with open(geojson_path, 'r') as f:
            data = json.load(f)
            if not data.get('features'):
                return None, 0

            coords = data['features'][0].get('geometry', {}).get('coordinates', [])
            while isinstance(coords, list) and coords and isinstance(coords[0], list):
                coords = coords[0]

            if coords and len(coords) >= 2:
                x, y = coords[0], coords[1]
                is_wgs84 = -180 <= x <= 180 and -90 <= y <= 90
                return 'WGS84' if is_wgs84 else 'WebMercator', len(data['features'])
    except Exception as e:
        print(f"  Error checking {geojson_path}: {e}")
    return None, 0

def reproject_file(input_path, output_path):
    """Reproject a GeoJSON file from Web Mercator to WGS84."""
    try:
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

        def transform_coords(coords):
            if isinstance(coords[0], (int, float)):
                lng, lat = transformer.transform(coords[0], coords[1])
                return [lng, lat] if len(coords) == 2 else [lng, lat, coords[2]]
            return [transform_coords(c) for c in coords]

        with open(input_path, 'r') as f:
            data = json.load(f)

        for feature in data.get('features', []):
            geom = feature.get('geometry')
            if geom and geom.get('coordinates'):
                geom['coordinates'] = transform_coords(geom['coordinates'])

        with open(output_path, 'w') as f:
            json.dump(data, f)

        return True
    except Exception as e:
        print(f"  Reproject error: {e}")
        return False

def generate_tiles(input_files, output_mbtiles, layer_name="parcels"):
    """Generate MBTiles from GeoJSON files using tippecanoe."""
    cmd = [
        TIPPECANOE,
        "-o", str(output_mbtiles),
        "-Z10", "-z16",
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "--coalesce-densest-as-needed",
        "--detect-shared-borders",
        "--simplification=10",
        "-l", layer_name,
        "--force",
        "--read-parallel",
    ] + [str(f) for f in input_files]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

def convert_to_pmtiles(mbtiles_path, pmtiles_path):
    """Convert MBTiles to PMTiles."""
    try:
        from pmtiles.convert import mbtiles_to_pmtiles
        import sqlite3

        conn = sqlite3.connect(str(mbtiles_path))
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE name='maxzoom'")
        row = cursor.fetchone()
        maxzoom = int(row[0]) if row else 16
        conn.close()

        mbtiles_to_pmtiles(str(mbtiles_path), str(pmtiles_path), maxzoom)
        return True
    except Exception as e:
        print(f"  PMTiles conversion error: {e}")
        return False

def upload_to_r2(local_path, remote_name):
    """Upload file to Cloudflare R2."""
    upload_script = SCRIPT_DIR / "upload_to_r2.sh"
    result = subprocess.run(
        [str(upload_script), str(local_path), remote_name],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def process_state(state_code, files):
    """Process a single state's parcel data."""
    state_code = state_code.lower()
    print(f"\n{'='*50}")
    print(f"Processing: {state_code.upper()}")
    print(f"{'='*50}")

    # Check coordinate systems and gather files to process
    wgs84_files = []
    mercator_files = []
    total_parcels = 0

    for f in files:
        coord_sys, count = check_coordinate_system(f)
        total_parcels += count
        if coord_sys == 'WGS84':
            wgs84_files.append(f)
        elif coord_sys == 'WebMercator':
            mercator_files.append(f)

    print(f"  Files: {len(files)}, Parcels: {total_parcels:,}")
    print(f"  WGS84: {len(wgs84_files)}, WebMercator: {len(mercator_files)}")

    # Reproject Web Mercator files
    reprojected_dir = GEOJSON_DIR / f"{state_code}_wgs84"
    if mercator_files:
        reprojected_dir.mkdir(exist_ok=True)
        print(f"  Reprojecting {len(mercator_files)} files...")

        for f in mercator_files:
            output_file = reprojected_dir / Path(f).name
            if reproject_file(f, output_file):
                wgs84_files.append(output_file)
            else:
                print(f"    Failed: {f}")

    if not wgs84_files:
        print(f"  ERROR: No valid files to process")
        return None

    # Generate MBTiles
    mbtiles_path = TILES_DIR / f"parcels_{state_code}.mbtiles"
    print(f"  Generating MBTiles...")

    if not generate_tiles(wgs84_files, mbtiles_path):
        print(f"  ERROR: MBTiles generation failed")
        return None

    # Convert to PMTiles
    pmtiles_path = TILES_DIR / f"parcels_{state_code}.pmtiles"
    print(f"  Converting to PMTiles...")

    if not convert_to_pmtiles(mbtiles_path, pmtiles_path):
        print(f"  ERROR: PMTiles conversion failed")
        return None

    size_mb = pmtiles_path.stat().st_size / (1024 * 1024)
    print(f"  Output: {pmtiles_path.name} ({size_mb:.1f}MB)")

    # Upload to R2
    print(f"  Uploading to R2...")
    remote_name = f"parcels/parcels_{state_code}.pmtiles"

    if upload_to_r2(pmtiles_path, remote_name):
        print(f"  SUCCESS: {state_code.upper()} uploaded!")
        return {
            'state': state_code,
            'parcels': total_parcels,
            'size_mb': size_mb,
            'url': f"https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/{remote_name}"
        }
    else:
        print(f"  WARNING: Upload failed, file saved locally")
        return {
            'state': state_code,
            'parcels': total_parcels,
            'size_mb': size_mb,
            'url': None
        }

def main():
    """Process all states."""
    TILES_DIR.mkdir(exist_ok=True)

    # Gather all state directories
    state_files = {}

    # State directories
    for state_dir in GEOJSON_DIR.iterdir():
        if state_dir.is_dir() and not state_dir.name.endswith('_wgs84'):
            state_code = state_dir.name
            files = list(state_dir.glob("*.geojson"))
            if files:
                state_files[state_code] = files

    # Root-level state files (parcels_XX_*.geojson)
    for f in GEOJSON_DIR.glob("parcels_*.geojson"):
        parts = f.stem.split('_')
        if len(parts) >= 2:
            state_code = parts[1]
            if state_code not in state_files:
                state_files[state_code] = []
            state_files[state_code].append(f)

    print(f"Found {len(state_files)} states to process")
    print(f"States: {', '.join(sorted(state_files.keys()))}")

    # Skip already processed
    skip_states = {'va', 'wi'}  # Already done

    results = []
    for state_code in sorted(state_files.keys()):
        if state_code in skip_states:
            print(f"\nSkipping {state_code.upper()} (already processed)")
            continue

        result = process_state(state_code, state_files[state_code])
        if result:
            results.append(result)

    # Summary
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)

    total_parcels = sum(r['parcels'] for r in results)
    total_size = sum(r['size_mb'] for r in results)

    print(f"\nProcessed: {len(results)} states")
    print(f"Total Parcels: {total_parcels:,}")
    print(f"Total Size: {total_size:.1f}MB")

    print("\nUploaded files:")
    for r in results:
        status = "✓" if r['url'] else "✗"
        print(f"  {status} {r['state'].upper()}: {r['parcels']:,} parcels, {r['size_mb']:.1f}MB")

if __name__ == "__main__":
    main()
