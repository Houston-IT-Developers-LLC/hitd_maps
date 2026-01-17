#!/usr/bin/env python3
"""
Download Terrain RGB tiles and Houston GTFS Transit data
Converts to PMTiles, uploads to Cloudflare R2, and cleans up local files

Terrain Sources:
- Mapzen Terrain Tiles (now hosted by Stadia/AWS)
- Pre-rendered terrain-rgb format for MapLibre 3D terrain

GTFS Sources:
- Houston METRO: https://www.ridemetro.org/Pages/GTFSRealTime.aspx
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Tuple

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"
TERRAIN_DIR = OUTPUT_DIR / "terrain"
GTFS_DIR = OUTPUT_DIR / "gtfs"
LOG_DIR = DATA_PIPELINE_DIR / "logs"

# R2 Configuration
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY", "ecd653afe3300fdc045b9980df0dbb14")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY", "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35")
R2_BUCKET = os.environ.get("R2_BUCKET", "gspot-tiles")
R2_ENDPOINT = os.environ.get("R2_ENDPOINT", "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com")
R2_PUBLIC_URL = os.environ.get("R2_PUBLIC_URL", "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev")

# Terrain Tile Sources
TERRAIN_SOURCES = {
    "aws": {
        "name": "AWS Terrain Tiles",
        "url_template": "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png",
        "format": "terrarium",  # Mapzen encoding: (red * 256 + green + blue / 256) - 32768
        "max_zoom": 15,
        "attribution": "Mapzen, AWS"
    },
    "stadia": {
        "name": "Stadia Alidade Satellite (terrain)",
        "url_template": "https://tiles.stadiamaps.com/data/terrarium/{z}/{x}/{y}.png",
        "format": "terrarium",
        "max_zoom": 14,
        "api_key_required": True,
        "attribution": "Stadia Maps, Mapzen"
    }
}

# GTFS Transit Feeds
GTFS_FEEDS = {
    "houston_metro": {
        "name": "Houston METRO",
        "url": "https://metro.resourcespace.com/pages/download.php?ref=4835&ext=zip",
        "region": "TX",
        "agency_id": "houston_metro"
    },
    "houston_metro_alt": {
        "name": "Houston METRO (legacy)",
        "url": "http://www.ridemetro.org/Downloads/google_transit.zip",
        "region": "TX",
        "agency_id": "houston_metro"
    }
}

# Bounding boxes for regions (minx, miny, maxx, maxy)
REGION_BBOXES = {
    "texas": (-106.65, 25.8, -93.5, 36.5),
    "houston": (-95.8, 29.5, -95.0, 30.1),
    "usa": (-125.0, 24.0, -66.0, 50.0),
    "usa_contiguous": (-125.0, 24.0, -66.0, 50.0),
}


def log(message: str, level: str = "INFO") -> None:
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories() -> None:
    """Create necessary directories"""
    for dir_path in [TERRAIN_DIR, GTFS_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def get_s3_client():
    """Create S3 client for R2"""
    try:
        import boto3
        return boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )
    except ImportError:
        log("boto3 not installed. Run: pip install boto3", "ERROR")
        return None


def upload_to_r2(local_path: str, r2_key: str, content_type: str = None) -> Optional[str]:
    """Upload file to R2 and return public URL"""
    s3_client = get_s3_client()
    if not s3_client:
        return None

    if content_type is None:
        if local_path.endswith('.pmtiles'):
            content_type = 'application/octet-stream'
        elif local_path.endswith('.geojson'):
            content_type = 'application/geo+json'
        elif local_path.endswith('.json'):
            content_type = 'application/json'
        else:
            content_type = 'application/octet-stream'

    file_size = os.path.getsize(local_path) / (1024 * 1024)
    log(f"Uploading {os.path.basename(local_path)} ({file_size:.1f}MB) to {r2_key}")

    try:
        s3_client.upload_file(
            local_path,
            R2_BUCKET,
            r2_key,
            ExtraArgs={'ContentType': content_type}
        )
        public_url = f"{R2_PUBLIC_URL}/{r2_key}"
        log(f"  Uploaded: {public_url}")
        return public_url
    except Exception as e:
        log(f"  Upload error: {e}", "ERROR")
        return None


def check_r2_exists(r2_key: str) -> bool:
    """Check if a file exists in R2"""
    s3_client = get_s3_client()
    if not s3_client:
        return False

    try:
        s3_client.head_object(Bucket=R2_BUCKET, Key=r2_key)
        return True
    except:
        return False


def download_file(url: str, output_path: str, timeout: int = 300) -> bool:
    """Download file from URL"""
    log(f"Downloading: {os.path.basename(output_path)}")
    log(f"  From: {url}")

    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'HITD-Maps-DataPipeline/1.0')

        with urllib.request.urlopen(req, timeout=timeout) as response:
            file_size = response.headers.get('Content-Length')
            if file_size:
                log(f"  Size: {int(file_size) / (1024*1024):.1f} MB")

            with open(output_path, 'wb') as f:
                shutil.copyfileobj(response, f)

        log(f"  Saved: {output_path}")
        return True

    except urllib.error.HTTPError as e:
        log(f"  HTTP Error: {e.code} - {e.reason}", "ERROR")
        return False
    except urllib.error.URLError as e:
        log(f"  URL Error: {e.reason}", "ERROR")
        return False
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return False


# =============================================================================
# TERRAIN RGB TILES
# =============================================================================

def get_tile_coords(bbox: Tuple[float, float, float, float], zoom: int) -> List[Tuple[int, int]]:
    """Get tile coordinates for a bounding box at a specific zoom level"""
    import math

    def lon_to_tile_x(lon: float, z: int) -> int:
        return int((lon + 180.0) / 360.0 * (1 << z))

    def lat_to_tile_y(lat: float, z: int) -> int:
        lat_rad = math.radians(lat)
        n = 1 << z
        return int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)

    min_x = lon_to_tile_x(bbox[0], zoom)
    max_x = lon_to_tile_x(bbox[2], zoom)
    min_y = lat_to_tile_y(bbox[3], zoom)  # Note: y is inverted
    max_y = lat_to_tile_y(bbox[1], zoom)

    tiles = []
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            tiles.append((x, y))

    return tiles


def download_terrain_tile(url: str, output_path: str) -> bool:
    """Download a single terrain tile"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'HITD-Maps-DataPipeline/1.0')

        with urllib.request.urlopen(req, timeout=30) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        return True
    except:
        return False


def download_terrain_tiles(
    bbox: Tuple[float, float, float, float],
    output_dir: Path,
    source: str = "aws",
    min_zoom: int = 0,
    max_zoom: int = 12,
    max_workers: int = 8
) -> str:
    """
    Download terrain tiles for a bounding box

    Returns path to directory containing tiles
    """
    source_info = TERRAIN_SOURCES.get(source)
    if not source_info:
        log(f"Unknown terrain source: {source}", "ERROR")
        return None

    log(f"Downloading terrain tiles from {source_info['name']}")
    log(f"  Bbox: {bbox}")
    log(f"  Zoom range: {min_zoom}-{max_zoom}")

    tiles_dir = output_dir / "tiles"
    tiles_dir.mkdir(parents=True, exist_ok=True)

    # Calculate total tiles
    total_tiles = 0
    for z in range(min_zoom, max_zoom + 1):
        tiles = get_tile_coords(bbox, z)
        total_tiles += len(tiles)

    log(f"  Total tiles to download: {total_tiles}")

    # Download tiles
    downloaded = 0
    failed = 0

    for z in range(min_zoom, max_zoom + 1):
        zoom_dir = tiles_dir / str(z)
        zoom_dir.mkdir(exist_ok=True)

        tiles = get_tile_coords(bbox, z)
        log(f"  Zoom {z}: {len(tiles)} tiles")

        def download_single(tile):
            x, y = tile
            x_dir = zoom_dir / str(x)
            x_dir.mkdir(exist_ok=True)

            tile_path = x_dir / f"{y}.png"
            if tile_path.exists():
                return True

            url = source_info['url_template'].format(z=z, x=x, y=y)
            return download_terrain_tile(url, str(tile_path))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(download_single, tile): tile for tile in tiles}
            for future in as_completed(futures):
                if future.result():
                    downloaded += 1
                else:
                    failed += 1

    log(f"  Downloaded: {downloaded}, Failed: {failed}")

    return str(tiles_dir)


def create_terrain_mbtiles(tiles_dir: str, output_path: str) -> Optional[str]:
    """Convert terrain tiles directory to MBTiles"""
    log(f"Creating MBTiles from tiles directory")

    # Check for mb-util
    try:
        subprocess.run(["mb-util", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("mb-util not found. Install with: pip install mbutil", "WARNING")
        log("Trying alternative method with Python...", "INFO")
        return create_mbtiles_python(tiles_dir, output_path)

    try:
        cmd = [
            "mb-util",
            "--scheme=xyz",
            tiles_dir,
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            log(f"  Created: {output_path}")
            return output_path
        else:
            log(f"  mb-util error: {result.stderr}", "ERROR")
            return None
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def create_mbtiles_python(tiles_dir: str, output_path: str) -> Optional[str]:
    """Create MBTiles using pure Python (fallback if mb-util not available)"""
    import sqlite3

    log(f"Creating MBTiles with Python...")

    try:
        conn = sqlite3.connect(output_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                name TEXT,
                value TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tiles (
                zoom_level INTEGER,
                tile_column INTEGER,
                tile_row INTEGER,
                tile_data BLOB
            )
        """)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS tile_index
            ON tiles (zoom_level, tile_column, tile_row)
        """)

        # Add metadata
        metadata = [
            ("name", "terrain-rgb"),
            ("format", "png"),
            ("type", "baselayer"),
            ("version", "1.0"),
            ("description", "Terrain RGB elevation tiles"),
        ]
        cursor.executemany("INSERT INTO metadata VALUES (?, ?)", metadata)

        # Insert tiles
        tiles_path = Path(tiles_dir)
        tile_count = 0

        for z_dir in sorted(tiles_path.iterdir()):
            if not z_dir.is_dir():
                continue
            z = int(z_dir.name)

            for x_dir in sorted(z_dir.iterdir()):
                if not x_dir.is_dir():
                    continue
                x = int(x_dir.name)

                for tile_file in sorted(x_dir.iterdir()):
                    if not tile_file.suffix == '.png':
                        continue
                    y = int(tile_file.stem)

                    # TMS uses flipped Y
                    tms_y = (1 << z) - 1 - y

                    with open(tile_file, 'rb') as f:
                        tile_data = f.read()

                    cursor.execute(
                        "INSERT OR REPLACE INTO tiles VALUES (?, ?, ?, ?)",
                        (z, x, tms_y, tile_data)
                    )
                    tile_count += 1

        conn.commit()
        conn.close()

        log(f"  Created MBTiles with {tile_count} tiles")
        return output_path

    except Exception as e:
        log(f"  Error creating MBTiles: {e}", "ERROR")
        return None


def convert_mbtiles_to_pmtiles(mbtiles_path: str, pmtiles_path: str) -> Optional[str]:
    """Convert MBTiles to PMTiles"""
    log(f"Converting to PMTiles: {pmtiles_path}")

    try:
        subprocess.run(["pmtiles", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("pmtiles CLI not found. Install with: npm install -g pmtiles OR cargo install pmtiles", "ERROR")
        return None

    try:
        cmd = ["pmtiles", "convert", mbtiles_path, pmtiles_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            log(f"  Created: {pmtiles_path}")
            return pmtiles_path
        else:
            log(f"  pmtiles error: {result.stderr}", "ERROR")
            return None
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def download_terrain_full(
    region: str = "usa",
    max_zoom: int = 12,
    upload: bool = True,
    cleanup: bool = True
) -> Dict:
    """
    Full terrain download pipeline:
    1. Download terrain RGB tiles
    2. Convert to MBTiles
    3. Convert to PMTiles
    4. Upload to R2
    5. Cleanup local files
    """
    log("=" * 70)
    log("TERRAIN RGB DOWNLOAD PIPELINE")
    log("=" * 70)

    bbox = REGION_BBOXES.get(region)
    if not bbox:
        log(f"Unknown region: {region}. Available: {list(REGION_BBOXES.keys())}", "ERROR")
        return {"success": False, "error": "Unknown region"}

    ensure_directories()

    result = {
        "success": False,
        "region": region,
        "bbox": bbox,
        "files_created": [],
        "uploaded": [],
        "cleaned_up": []
    }

    # Check if already on R2
    r2_key = f"terrain/terrain-rgb-{region}.pmtiles"
    if check_r2_exists(r2_key):
        log(f"Terrain already exists on R2: {r2_key}")
        result["success"] = True
        result["uploaded"].append(f"{R2_PUBLIC_URL}/{r2_key}")
        return result

    try:
        # 1. Download tiles
        tiles_dir = download_terrain_tiles(
            bbox=bbox,
            output_dir=TERRAIN_DIR,
            source="aws",
            min_zoom=0,
            max_zoom=max_zoom
        )

        if not tiles_dir:
            return result

        result["files_created"].append(tiles_dir)

        # 2. Create MBTiles
        mbtiles_path = str(TERRAIN_DIR / f"terrain-rgb-{region}.mbtiles")
        mbtiles_result = create_terrain_mbtiles(tiles_dir, mbtiles_path)

        if not mbtiles_result:
            return result

        result["files_created"].append(mbtiles_path)

        # 3. Convert to PMTiles
        pmtiles_path = str(TERRAIN_DIR / f"terrain-rgb-{region}.pmtiles")
        pmtiles_result = convert_mbtiles_to_pmtiles(mbtiles_path, pmtiles_path)

        if not pmtiles_result:
            return result

        result["files_created"].append(pmtiles_path)

        # 4. Upload to R2
        if upload:
            url = upload_to_r2(pmtiles_path, r2_key)
            if url:
                result["uploaded"].append(url)

        # 5. Cleanup
        if cleanup:
            for path in [tiles_dir, mbtiles_path, pmtiles_path]:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    log(f"  Cleaned up: {path}")
                elif os.path.isfile(path):
                    os.remove(path)
                    log(f"  Cleaned up: {path}")
                result["cleaned_up"].append(path)

        result["success"] = True

    except Exception as e:
        log(f"Pipeline error: {e}", "ERROR")
        result["error"] = str(e)

    return result


# =============================================================================
# GTFS TRANSIT DATA
# =============================================================================

def download_gtfs_feed(feed_id: str, output_dir: Path) -> Optional[str]:
    """Download GTFS feed ZIP file"""
    feed_info = GTFS_FEEDS.get(feed_id)
    if not feed_info:
        log(f"Unknown GTFS feed: {feed_id}", "ERROR")
        return None

    log(f"Downloading GTFS feed: {feed_info['name']}")

    output_path = output_dir / f"{feed_id}.zip"

    if download_file(feed_info['url'], str(output_path)):
        return str(output_path)

    # Try alternate URL if primary fails
    alt_feed_id = f"{feed_id}_alt"
    if alt_feed_id in GTFS_FEEDS:
        log("  Trying alternate URL...")
        alt_info = GTFS_FEEDS[alt_feed_id]
        if download_file(alt_info['url'], str(output_path)):
            return str(output_path)

    return None


def extract_gtfs(zip_path: str, output_dir: Path) -> Optional[str]:
    """Extract GTFS ZIP to directory"""
    log(f"Extracting GTFS: {zip_path}")

    extract_dir = output_dir / Path(zip_path).stem
    extract_dir.mkdir(exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
        log(f"  Extracted to: {extract_dir}")
        return str(extract_dir)
    except Exception as e:
        log(f"  Error extracting: {e}", "ERROR")
        return None


def gtfs_to_geojson(gtfs_dir: str, output_path: str) -> Optional[str]:
    """
    Convert GTFS data to GeoJSON
    Extracts routes and stops as features
    """
    log(f"Converting GTFS to GeoJSON...")

    gtfs_path = Path(gtfs_dir)
    features = []

    # Process stops.txt
    stops_file = gtfs_path / "stops.txt"
    if stops_file.exists():
        import csv
        with open(stops_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    lat = float(row.get('stop_lat', 0))
                    lon = float(row.get('stop_lon', 0))
                    if lat and lon:
                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat]
                            },
                            "properties": {
                                "type": "stop",
                                "stop_id": row.get('stop_id', ''),
                                "stop_name": row.get('stop_name', ''),
                                "stop_code": row.get('stop_code', ''),
                                "location_type": row.get('location_type', '0'),
                                "wheelchair_boarding": row.get('wheelchair_boarding', '')
                            }
                        }
                        features.append(feature)
                except (ValueError, KeyError):
                    continue
        log(f"  Processed {len(features)} stops")

    # Process shapes.txt for route lines
    shapes_file = gtfs_path / "shapes.txt"
    if shapes_file.exists():
        import csv
        shapes = {}
        with open(shapes_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    shape_id = row.get('shape_id', '')
                    lat = float(row.get('shape_pt_lat', 0))
                    lon = float(row.get('shape_pt_lon', 0))
                    seq = int(row.get('shape_pt_sequence', 0))

                    if shape_id not in shapes:
                        shapes[shape_id] = []
                    shapes[shape_id].append((seq, lon, lat))
                except (ValueError, KeyError):
                    continue

        # Convert shapes to LineString features
        for shape_id, points in shapes.items():
            if len(points) >= 2:
                # Sort by sequence
                points.sort(key=lambda x: x[0])
                coords = [[p[1], p[2]] for p in points]

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coords
                    },
                    "properties": {
                        "type": "route_shape",
                        "shape_id": shape_id
                    }
                }
                features.append(feature)

        log(f"  Processed {len(shapes)} route shapes")

    # Load route info
    routes_file = gtfs_path / "routes.txt"
    routes_info = {}
    if routes_file.exists():
        import csv
        with open(routes_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                routes_info[row.get('route_id', '')] = {
                    "route_short_name": row.get('route_short_name', ''),
                    "route_long_name": row.get('route_long_name', ''),
                    "route_type": row.get('route_type', ''),
                    "route_color": row.get('route_color', ''),
                }

    # Write GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "name": "gtfs_transit",
        "features": features
    }

    with open(output_path, 'w') as f:
        json.dump(geojson, f)

    log(f"  Created GeoJSON with {len(features)} features")
    return output_path


def gtfs_to_pmtiles(geojson_path: str, pmtiles_path: str) -> Optional[str]:
    """Convert GTFS GeoJSON to PMTiles using tippecanoe"""
    log(f"Converting to PMTiles: {pmtiles_path}")

    try:
        subprocess.run(["tippecanoe", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("tippecanoe not found", "ERROR")
        return None

    cmd = [
        "tippecanoe",
        "-o", pmtiles_path,
        "-z", "14",
        "-Z", "8",
        "--drop-densest-as-needed",
        "-l", "transit",
        "--force",
        geojson_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            log(f"  Created: {pmtiles_path}")
            return pmtiles_path
        else:
            log(f"  tippecanoe error: {result.stderr}", "ERROR")
            return None
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def download_gtfs_full(
    feed_id: str = "houston_metro",
    upload: bool = True,
    cleanup: bool = True
) -> Dict:
    """
    Full GTFS download pipeline:
    1. Download GTFS ZIP
    2. Extract and parse
    3. Convert to GeoJSON
    4. Convert to PMTiles
    5. Upload to R2
    6. Cleanup local files
    """
    log("=" * 70)
    log("GTFS TRANSIT DOWNLOAD PIPELINE")
    log("=" * 70)

    ensure_directories()

    result = {
        "success": False,
        "feed_id": feed_id,
        "files_created": [],
        "uploaded": [],
        "cleaned_up": []
    }

    # Check if already on R2
    r2_key = f"transit/{feed_id}.pmtiles"
    if check_r2_exists(r2_key):
        log(f"GTFS already exists on R2: {r2_key}")
        result["success"] = True
        result["uploaded"].append(f"{R2_PUBLIC_URL}/{r2_key}")
        return result

    try:
        # 1. Download GTFS
        zip_path = download_gtfs_feed(feed_id, GTFS_DIR)
        if not zip_path:
            return result
        result["files_created"].append(zip_path)

        # 2. Extract
        gtfs_dir = extract_gtfs(zip_path, GTFS_DIR)
        if not gtfs_dir:
            return result
        result["files_created"].append(gtfs_dir)

        # 3. Convert to GeoJSON
        geojson_path = str(GTFS_DIR / f"{feed_id}.geojson")
        geojson_result = gtfs_to_geojson(gtfs_dir, geojson_path)
        if not geojson_result:
            return result
        result["files_created"].append(geojson_path)

        # 4. Convert to PMTiles
        pmtiles_path = str(GTFS_DIR / f"{feed_id}.pmtiles")
        pmtiles_result = gtfs_to_pmtiles(geojson_path, pmtiles_path)
        if not pmtiles_result:
            return result
        result["files_created"].append(pmtiles_path)

        # 5. Upload to R2
        if upload:
            url = upload_to_r2(pmtiles_path, r2_key)
            if url:
                result["uploaded"].append(url)

            # Also upload the original GTFS ZIP for reference
            gtfs_zip_key = f"transit/{feed_id}_gtfs.zip"
            zip_url = upload_to_r2(zip_path, gtfs_zip_key, "application/zip")
            if zip_url:
                result["uploaded"].append(zip_url)

        # 6. Cleanup
        if cleanup:
            for path in result["files_created"]:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    log(f"  Cleaned up: {path}")
                elif os.path.isfile(path):
                    os.remove(path)
                    log(f"  Cleaned up: {path}")
                result["cleaned_up"].append(path)

        result["success"] = True

    except Exception as e:
        log(f"Pipeline error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        result["error"] = str(e)

    return result


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Download Terrain RGB and GTFS Transit data for HITD Maps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download terrain for USA (zoom 0-12)
  python3 download_terrain_gtfs.py --terrain --region usa --max-zoom 12

  # Download Houston METRO GTFS
  python3 download_terrain_gtfs.py --gtfs --feed houston_metro

  # Download both terrain and GTFS
  python3 download_terrain_gtfs.py --all

  # Download without uploading (keep local)
  python3 download_terrain_gtfs.py --all --no-upload --no-cleanup

  # Check available feeds
  python3 download_terrain_gtfs.py --list

Terrain Sources:
  AWS Terrain Tiles (Mapzen terrarium format) - Free, no API key

GTFS Feeds:
  houston_metro - Houston METRO public transit
        """
    )

    parser.add_argument("--terrain", action="store_true",
                        help="Download terrain RGB tiles")
    parser.add_argument("--gtfs", action="store_true",
                        help="Download GTFS transit data")
    parser.add_argument("--all", action="store_true",
                        help="Download both terrain and GTFS")

    parser.add_argument("--region", default="usa",
                        help="Region for terrain: usa, texas, houston")
    parser.add_argument("--max-zoom", type=int, default=12,
                        help="Maximum zoom level for terrain (default: 12)")
    parser.add_argument("--feed", default="houston_metro",
                        help="GTFS feed ID (default: houston_metro)")

    parser.add_argument("--no-upload", action="store_true",
                        help="Skip uploading to R2")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="Keep local files after upload")

    parser.add_argument("--list", action="store_true",
                        help="List available regions and feeds")

    args = parser.parse_args()

    if args.list:
        print("\nAvailable Regions:")
        for region, bbox in REGION_BBOXES.items():
            print(f"  {region}: {bbox}")

        print("\nAvailable GTFS Feeds:")
        for feed_id, info in GTFS_FEEDS.items():
            if not feed_id.endswith("_alt"):
                print(f"  {feed_id}: {info['name']}")
        return

    if not args.terrain and not args.gtfs and not args.all:
        parser.print_help()
        return

    upload = not args.no_upload
    cleanup = not args.no_cleanup

    results = []

    # Download terrain
    if args.terrain or args.all:
        result = download_terrain_full(
            region=args.region,
            max_zoom=args.max_zoom,
            upload=upload,
            cleanup=cleanup
        )
        results.append(("Terrain", result))

    # Download GTFS
    if args.gtfs or args.all:
        result = download_gtfs_full(
            feed_id=args.feed,
            upload=upload,
            cleanup=cleanup
        )
        results.append(("GTFS", result))

    # Summary
    log("")
    log("=" * 70)
    log("PIPELINE COMPLETE")
    log("=" * 70)

    for name, result in results:
        status = "SUCCESS" if result.get("success") else "FAILED"
        log(f"{name}: {status}")
        if result.get("uploaded"):
            for url in result["uploaded"]:
                log(f"  - {url}")
        if result.get("error"):
            log(f"  Error: {result['error']}")


if __name__ == "__main__":
    main()
