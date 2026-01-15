#!/usr/bin/env python3
"""
Download USFS Motor Vehicle Use Map (MVUM) Roads and Trails

Priority: 3 (High - Critical for off-road/overland users)
Source: USDA Forest Service Enterprise Data Warehouse (EDW)

Data Sources:
  - MVUM Roads: https://data.fs.usda.gov/geodata/edw/edw_resources/shp/Trans_MVUM_Road.zip (214 MB)
  - MVUM Trails: https://data.fs.usda.gov/geodata/edw/edw_resources/shp/Trans_MVUM_Trail.zip (53 MB)
  - Full Road Network: https://data.fs.usda.gov/geodata/edw/edw_resources/shp/Trans_RoadCore_FS.zip (337 MB)

Key Fields Preserved:
  - SEASONAL: Seasonal restrictions/closures
  - PASSENGERVEHICLE: Highway legal vehicles allowed
  - HIGHCLEARANCEVEHICLE: High clearance vehicles allowed
  - ATV: ATVs allowed
  - MOTORCYCLE: Motorcycles allowed
  - OPERATIONALMAINTENANCELEVEL: 1-5 maintenance scale

Update Frequency: Annual (typically spring)
Date Added: 2026-01-13

Usage:
  python3 download_mvum.py --roads --trails --state TX --pmtiles --upload
"""

import os
import sys
import json
import urllib.request
import urllib.error
import zipfile
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
RAW_DIR = OUTPUT_DIR / "raw" / "mvum"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

# USFS Data Download URLs
MVUM_DATA_SOURCES = {
    "roads": {
        "url": "https://data.fs.usda.gov/geodata/edw/edw_resources/shp/Trans_MVUM_Road.zip",
        "filename": "Trans_MVUM_Road.zip",
        "shapefile": "S_USA.Trans_MVUM_Road.shp",
        "layer_name": "mvum_roads",
        "description": "MVUM Roads - Motor vehicle routes on National Forest System lands",
        "size_mb": 214
    },
    "trails": {
        "url": "https://data.fs.usda.gov/geodata/edw/edw_resources/shp/Trans_MVUM_Trail.zip",
        "filename": "Trans_MVUM_Trail.zip",
        "shapefile": "S_USA.Trans_MVUM_Trail.shp",
        "layer_name": "mvum_trails",
        "description": "MVUM Trails - Motorized trails on National Forest System lands",
        "size_mb": 53
    },
    "road_core": {
        "url": "https://data.fs.usda.gov/geodata/edw/edw_resources/shp/Trans_RoadCore_FS.zip",
        "filename": "Trans_RoadCore_FS.zip",
        "shapefile": "S_USA.Trans_RoadCore_FS.shp",
        "layer_name": "usfs_roads",
        "description": "Full USFS Road Network (includes non-motorized)",
        "size_mb": 337
    }
}

# Key fields to preserve from MVUM data
MVUM_FIELDS = [
    # Identification
    "ID", "NAME", "RTE_CN", "SEG_CN",
    # Road/trail info
    "ROUTE_STATUS", "SYSTEM", "SURFACE_TYPE", "JURISDICTION",
    # Vehicle access fields (critical)
    "SEASONAL",
    "PASSENGERVEHICLE",
    "HIGHCLEARANCEVEHICLE",
    "ATV",
    "MOTORCYCLE",
    "FOURWD_GT50",  # 4WD > 50" width
    "FOURWD_LT50",  # 4WD < 50" width
    "TRACKED_OHV",
    "OTHER_OHV",
    # Maintenance
    "OPERATIONALMAINTENANCELEVEL",
    "OBJECTIVE_MAINT_LEVEL",
    # Location
    "ADMIN_ORG", "MANAGING_ORG",
    "FORESTNAME", "DISTRICTNAME",
    "STATE",
    # Other
    "GIS_MILES", "SHAPE_Length"
]

# State bounding boxes for filtering (approximate, WGS84)
# Format: [min_lon, min_lat, max_lon, max_lat]
STATE_BBOXES = {
    "AL": [-88.5, 30.2, -84.9, 35.0],
    "AK": [-180.0, 51.2, -130.0, 71.4],
    "AZ": [-114.8, 31.3, -109.0, 37.0],
    "AR": [-94.6, 33.0, -89.6, 36.5],
    "CA": [-124.4, 32.5, -114.1, 42.0],
    "CO": [-109.1, 36.9, -102.0, 41.0],
    "CT": [-73.7, 40.9, -71.8, 42.1],
    "DE": [-75.8, 38.4, -75.0, 39.8],
    "FL": [-87.6, 24.5, -80.0, 31.0],
    "GA": [-85.6, 30.4, -80.8, 35.0],
    "HI": [-160.2, 18.9, -154.8, 22.2],
    "ID": [-117.2, 42.0, -111.0, 49.0],
    "IL": [-91.5, 36.9, -87.5, 42.5],
    "IN": [-88.1, 37.8, -84.8, 41.8],
    "IA": [-96.6, 40.4, -90.1, 43.5],
    "KS": [-102.1, 36.9, -94.6, 40.0],
    "KY": [-89.6, 36.5, -81.9, 39.2],
    "LA": [-94.0, 28.9, -89.0, 33.0],
    "ME": [-71.1, 43.0, -66.9, 47.5],
    "MD": [-79.5, 37.9, -75.0, 39.7],
    "MA": [-73.5, 41.2, -69.9, 42.9],
    "MI": [-90.4, 41.7, -82.4, 48.2],
    "MN": [-97.2, 43.5, -89.5, 49.4],
    "MS": [-91.7, 30.2, -88.1, 35.0],
    "MO": [-95.8, 36.0, -89.1, 40.6],
    "MT": [-116.0, 44.4, -104.0, 49.0],
    "NE": [-104.1, 40.0, -95.3, 43.0],
    "NV": [-120.0, 35.0, -114.0, 42.0],
    "NH": [-72.6, 42.7, -70.7, 45.3],
    "NJ": [-75.6, 38.9, -73.9, 41.4],
    "NM": [-109.1, 31.3, -103.0, 37.0],
    "NY": [-79.8, 40.5, -71.9, 45.0],
    "NC": [-84.3, 33.8, -75.5, 36.6],
    "ND": [-104.1, 45.9, -96.6, 49.0],
    "OH": [-84.8, 38.4, -80.5, 42.0],
    "OK": [-103.0, 33.6, -94.4, 37.0],
    "OR": [-124.6, 42.0, -116.5, 46.3],
    "PA": [-80.5, 39.7, -74.7, 42.3],
    "RI": [-71.9, 41.1, -71.1, 42.0],
    "SC": [-83.4, 32.0, -78.5, 35.2],
    "SD": [-104.1, 42.5, -96.4, 46.0],
    "TN": [-90.3, 35.0, -81.6, 36.7],
    "TX": [-106.6, 25.8, -93.5, 36.5],
    "UT": [-114.1, 37.0, -109.0, 42.0],
    "VT": [-73.4, 42.7, -71.5, 45.0],
    "VA": [-83.7, 36.5, -75.2, 39.5],
    "WA": [-124.8, 45.5, -116.9, 49.0],
    "WV": [-82.6, 37.2, -77.7, 40.6],
    "WI": [-92.9, 42.5, -86.8, 47.1],
    "WY": [-111.1, 41.0, -104.1, 45.0]
}

# State names for logging
STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming"
}


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories"""
    for dir_path in [RAW_DIR, GEOJSON_DIR, PMTILES_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def check_dependencies():
    """Check for required tools"""
    missing = []

    # Check ogr2ogr (GDAL)
    try:
        result = subprocess.run(["ogr2ogr", "--version"], capture_output=True)
        if result.returncode != 0:
            missing.append("ogr2ogr (GDAL)")
    except FileNotFoundError:
        missing.append("ogr2ogr (GDAL) - Install: sudo apt-get install gdal-bin")

    # Check tippecanoe
    try:
        result = subprocess.run(["tippecanoe", "--version"], capture_output=True)
        if result.returncode != 0:
            missing.append("tippecanoe")
    except FileNotFoundError:
        missing.append("tippecanoe - Install: see https://github.com/felt/tippecanoe")

    if missing:
        log("Missing dependencies:", "WARNING")
        for dep in missing:
            log(f"  - {dep}", "WARNING")
        return False

    return True


def download_file(url, dest_path, description=""):
    """Download a file with progress indication"""
    log(f"Downloading: {description or url}")
    log(f"  Destination: {dest_path}")

    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

        with urllib.request.urlopen(req, timeout=600) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            block_size = 1024 * 1024  # 1MB blocks

            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        print(f"\r  Progress: {downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB ({pct:.1f}%)", end="", flush=True)

            print()  # New line after progress
            log(f"  Download complete: {dest_path}")
            return True

    except urllib.error.HTTPError as e:
        log(f"  HTTP Error {e.code}: {e.reason}", "ERROR")
        return False
    except urllib.error.URLError as e:
        log(f"  URL Error: {e.reason}", "ERROR")
        return False
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return False


def extract_zip(zip_path, dest_dir):
    """Extract a zip file"""
    log(f"Extracting: {zip_path}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(dest_dir)
        log(f"  Extracted to: {dest_dir}")
        return True
    except Exception as e:
        log(f"  Extract error: {e}", "ERROR")
        return False


def download_mvum_data(data_type, force=False):
    """
    Download MVUM shapefile data from USFS

    Args:
        data_type: 'roads', 'trails', or 'road_core'
        force: Force re-download even if exists

    Returns:
        Path to extracted shapefile directory or None
    """
    if data_type not in MVUM_DATA_SOURCES:
        log(f"Unknown data type: {data_type}", "ERROR")
        return None

    source = MVUM_DATA_SOURCES[data_type]
    zip_path = RAW_DIR / source["filename"]
    extract_dir = RAW_DIR / data_type

    # Check if already downloaded
    if not force and extract_dir.exists():
        shapefile_path = extract_dir / source["shapefile"]
        if shapefile_path.exists():
            log(f"Using existing data: {extract_dir}")
            return extract_dir

    log("=" * 60)
    log(f"Downloading {source['description']}")
    log(f"  Size: ~{source['size_mb']} MB")
    log("=" * 60)

    # Download
    if not download_file(source["url"], zip_path, source["description"]):
        return None

    # Extract
    extract_dir.mkdir(parents=True, exist_ok=True)
    if not extract_zip(zip_path, extract_dir):
        return None

    return extract_dir


def convert_to_geojson(shapefile_dir, shapefile_name, output_path,
                       state_filter=None, bbox=None, fields=None):
    """
    Convert shapefile to GeoJSON with optional filtering

    Args:
        shapefile_dir: Directory containing shapefile
        shapefile_name: Name of the .shp file
        output_path: Output GeoJSON path
        state_filter: Optional state abbreviation to filter by
        bbox: Optional bounding box [min_lon, min_lat, max_lon, max_lat]
        fields: List of fields to include (None = all)

    Returns:
        True on success, False on failure
    """
    shapefile_path = shapefile_dir / shapefile_name

    if not shapefile_path.exists():
        log(f"Shapefile not found: {shapefile_path}", "ERROR")
        return False

    log(f"Converting to GeoJSON: {shapefile_path}")

    cmd = [
        "ogr2ogr",
        "-f", "GeoJSON",
        "-t_srs", "EPSG:4326",  # Reproject to WGS84
    ]

    # Add bounding box filter (spatial clip)
    if bbox:
        cmd.extend([
            "-spat", str(bbox[0]), str(bbox[1]), str(bbox[2]), str(bbox[3]),
            "-spat_srs", "EPSG:4326"
        ])
        log(f"  Filtering by bbox: {bbox}")

    # Add SQL filter for state if provided
    # MVUM data has a STATE field we can filter on
    if state_filter:
        state_upper = state_filter.upper()
        # Use SQL to filter by STATE field
        cmd.extend([
            "-sql", f"SELECT * FROM \"{Path(shapefile_name).stem}\" WHERE STATE LIKE '%{state_upper}%'"
        ])
        log(f"  Filtering by state: {state_upper}")

    # Limit fields if specified
    if fields:
        # Use -select to limit fields (only if not using -sql)
        if not state_filter:
            field_list = ",".join(fields)
            cmd.extend(["-select", field_list])

    # Progress option
    cmd.append("-progress")

    # Output and input
    cmd.append(str(output_path))
    cmd.append(str(shapefile_path))

    try:
        log(f"  Running: {' '.join(cmd[:8])}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        if result.returncode == 0:
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                log(f"  Created: {output_path} ({size_mb:.1f} MB)")
                return True
            else:
                log(f"  No output created (possibly no features in area)", "WARNING")
                return False
        else:
            log(f"  ogr2ogr error: {result.stderr}", "ERROR")
            return False

    except subprocess.TimeoutExpired:
        log("  Conversion timed out after 1 hour", "ERROR")
        return False
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return False


def convert_with_spatial_filter(shapefile_dir, shapefile_name, output_path, state_abbrev):
    """
    Convert shapefile to GeoJSON using state bbox spatial filter

    This is more efficient than SQL filtering for large datasets.
    Uses ogr2ogr's spatial filter capabilities.
    """
    shapefile_path = shapefile_dir / shapefile_name

    if not shapefile_path.exists():
        log(f"Shapefile not found: {shapefile_path}", "ERROR")
        return False

    state_upper = state_abbrev.upper()
    bbox = STATE_BBOXES.get(state_upper)

    if not bbox:
        log(f"No bounding box for state: {state_upper}", "ERROR")
        return False

    log(f"Converting to GeoJSON with spatial filter: {state_upper}")
    log(f"  BBox: {bbox}")

    # Build ogr2ogr command with spatial filter
    cmd = [
        "ogr2ogr",
        "-f", "GeoJSON",
        "-t_srs", "EPSG:4326",
        "-spat", str(bbox[0]), str(bbox[1]), str(bbox[2]), str(bbox[3]),
        "-spat_srs", "EPSG:4326",
        "-progress",
        str(output_path),
        str(shapefile_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        if result.returncode == 0:
            if output_path.exists() and output_path.stat().st_size > 100:
                size_mb = output_path.stat().st_size / (1024 * 1024)
                log(f"  Created: {output_path} ({size_mb:.1f} MB)")

                # Add metadata to GeoJSON
                add_metadata_to_geojson(output_path, state_upper, shapefile_name)
                return True
            else:
                log(f"  No features found in {state_upper} bbox", "WARNING")
                if output_path.exists():
                    output_path.unlink()
                return False
        else:
            log(f"  ogr2ogr error: {result.stderr}", "ERROR")
            return False

    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return False


def add_metadata_to_geojson(geojson_path, state_abbrev, source_name):
    """Add metadata to GeoJSON file"""
    try:
        with open(geojson_path, 'r') as f:
            data = json.load(f)

        # Count features
        feature_count = len(data.get('features', []))

        # Add metadata
        data['metadata'] = {
            "source": "USDA Forest Service - Motor Vehicle Use Maps",
            "source_file": source_name,
            "state": state_abbrev.upper(),
            "feature_count": feature_count,
            "download_date": datetime.now().isoformat(),
            "projection": "EPSG:4326 (WGS84)",
            "key_fields": {
                "SEASONAL": "Seasonal restrictions/closures",
                "PASSENGERVEHICLE": "Highway legal vehicles allowed",
                "HIGHCLEARANCEVEHICLE": "High clearance vehicles allowed",
                "ATV": "ATVs allowed",
                "MOTORCYCLE": "Motorcycles allowed",
                "OPERATIONALMAINTENANCELEVEL": "Maintenance level 1-5"
            }
        }

        with open(geojson_path, 'w') as f:
            json.dump(data, f)

        log(f"  Added metadata: {feature_count} features")

    except Exception as e:
        log(f"  Warning: Could not add metadata: {e}", "WARNING")


def generate_pmtiles(geojson_path, pmtiles_path, layer_name, data_type="roads"):
    """
    Generate PMTiles from GeoJSON

    Args:
        geojson_path: Input GeoJSON file
        pmtiles_path: Output PMTiles file
        layer_name: Name for the tile layer
        data_type: 'roads' or 'trails' (affects zoom levels)
    """
    log(f"Generating PMTiles: {geojson_path}")

    # Set zoom levels based on data type
    # Roads should be visible at z8+, trails at z10+
    if data_type == "roads":
        min_zoom = "8"
        max_zoom = "14"
    else:  # trails
        min_zoom = "10"
        max_zoom = "14"

    cmd = [
        "tippecanoe",
        f"-z{max_zoom}",
        f"-Z{min_zoom}",
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "--coalesce-densest-as-needed",
        "-l", layer_name,
        "--force",  # Overwrite existing
        "-o", str(pmtiles_path),
        str(geojson_path)
    ]

    try:
        log(f"  Running tippecanoe (z{min_zoom}-z{max_zoom})...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)

        if result.returncode == 0:
            if pmtiles_path.exists():
                size_mb = pmtiles_path.stat().st_size / (1024 * 1024)
                log(f"  Created: {pmtiles_path} ({size_mb:.1f} MB)")
                return True

        log(f"  tippecanoe error: {result.stderr}", "ERROR")
        return False

    except subprocess.TimeoutExpired:
        log("  PMTiles generation timed out after 2 hours", "ERROR")
        return False
    except FileNotFoundError:
        log("  tippecanoe not found. Install from https://github.com/felt/tippecanoe", "ERROR")
        return False
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return False


def upload_to_r2(local_path, r2_key):
    """Upload file to Cloudflare R2"""
    try:
        import boto3
    except ImportError:
        log("  boto3 not installed. Run: pip install boto3", "ERROR")
        return None

    log(f"Uploading to R2: {r2_key}")

    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )

        # Determine content type
        if str(local_path).endswith('.geojson'):
            content_type = 'application/geo+json'
        elif str(local_path).endswith('.pmtiles'):
            content_type = 'application/x-protobuf'
        else:
            content_type = 'application/octet-stream'

        file_size = os.path.getsize(local_path) / (1024 * 1024)
        log(f"  Uploading {file_size:.1f} MB...")

        s3_client.upload_file(
            str(local_path),
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


def cleanup_local(paths):
    """Remove local files"""
    for path in paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
                log(f"  Removed: {path}")
            elif os.path.isdir(path):
                shutil.rmtree(path)
                log(f"  Removed directory: {path}")
        except Exception as e:
            log(f"  Cleanup error for {path}: {e}", "WARNING")


def process_mvum_data(data_type, state_abbrev=None, generate_tiles=False,
                      upload=False, cleanup=False, force=False):
    """
    Full pipeline: download, convert, tile, upload

    Args:
        data_type: 'roads', 'trails', or 'road_core'
        state_abbrev: Optional state filter
        generate_tiles: Generate PMTiles
        upload: Upload to R2
        cleanup: Remove local files after upload
        force: Force re-download

    Returns:
        Dict with result info
    """
    source = MVUM_DATA_SOURCES[data_type]
    state_suffix = f"_{state_abbrev.lower()}" if state_abbrev else "_national"

    result = {
        "data_type": data_type,
        "state": state_abbrev,
        "geojson_path": None,
        "pmtiles_path": None,
        "r2_urls": []
    }

    # Step 1: Download
    shapefile_dir = download_mvum_data(data_type, force=force)
    if not shapefile_dir:
        log(f"Failed to download {data_type}", "ERROR")
        return result

    # Step 2: Convert to GeoJSON
    geojson_filename = f"{source['layer_name']}{state_suffix}.geojson"
    geojson_path = GEOJSON_DIR / geojson_filename

    if not force and geojson_path.exists():
        log(f"Using existing GeoJSON: {geojson_path}")
    else:
        if state_abbrev:
            success = convert_with_spatial_filter(
                shapefile_dir,
                source["shapefile"],
                geojson_path,
                state_abbrev
            )
        else:
            success = convert_to_geojson(
                shapefile_dir,
                source["shapefile"],
                geojson_path
            )

        if not success:
            log(f"Failed to convert {data_type} to GeoJSON", "ERROR")
            return result

    result["geojson_path"] = str(geojson_path)

    # Step 3: Generate PMTiles
    if generate_tiles:
        pmtiles_filename = f"{source['layer_name']}{state_suffix}.pmtiles"
        pmtiles_path = PMTILES_DIR / pmtiles_filename

        if not force and pmtiles_path.exists():
            log(f"Using existing PMTiles: {pmtiles_path}")
        else:
            success = generate_pmtiles(
                geojson_path,
                pmtiles_path,
                source["layer_name"],
                data_type
            )
            if not success:
                log(f"Failed to generate PMTiles for {data_type}", "ERROR")
            else:
                result["pmtiles_path"] = str(pmtiles_path)

        if pmtiles_path.exists():
            result["pmtiles_path"] = str(pmtiles_path)

    # Step 4: Upload to R2
    if upload:
        files_to_cleanup = []

        # Upload GeoJSON
        geojson_r2_key = f"enrichment/usfs/{geojson_filename}"
        url = upload_to_r2(geojson_path, geojson_r2_key)
        if url:
            result["r2_urls"].append(url)
            files_to_cleanup.append(str(geojson_path))

        # Upload PMTiles
        if result["pmtiles_path"]:
            pmtiles_r2_key = f"enrichment/usfs/{pmtiles_filename}"
            url = upload_to_r2(result["pmtiles_path"], pmtiles_r2_key)
            if url:
                result["r2_urls"].append(url)
                files_to_cleanup.append(result["pmtiles_path"])

        # Cleanup local files
        if cleanup and files_to_cleanup:
            log("Cleaning up local files...")
            cleanup_local(files_to_cleanup)

    return result


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download USFS Motor Vehicle Use Map (MVUM) Roads and Trails",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download MVUM roads for Texas
  python3 download_mvum.py --roads --state TX

  # Download MVUM trails for Colorado with tiles
  python3 download_mvum.py --trails --state CO --pmtiles

  # Download both roads and trails for a state, generate tiles, and upload
  python3 download_mvum.py --roads --trails --state MT --pmtiles --upload

  # Download national MVUM roads (large, ~214 MB)
  python3 download_mvum.py --roads

  # Full pipeline with cleanup
  python3 download_mvum.py --roads --trails --state AZ --pmtiles --upload --cleanup

  # Download the complete USFS road network (includes non-motorized)
  python3 download_mvum.py --road-core --state OR

Key Fields in MVUM Data:
  SEASONAL                    - Seasonal access restrictions
  PASSENGERVEHICLE           - Highway-legal vehicles allowed (Y/N)
  HIGHCLEARANCEVEHICLE       - High clearance vehicles allowed (Y/N)
  ATV                        - ATVs allowed (Y/N)
  MOTORCYCLE                 - Motorcycles allowed (Y/N)
  OPERATIONALMAINTENANCELEVEL - Road maintenance level (1-5)
        """
    )

    # Data type flags
    parser.add_argument("--roads", action="store_true",
                        help="Download MVUM Roads (214 MB national)")
    parser.add_argument("--trails", action="store_true",
                        help="Download MVUM Trails (53 MB national)")
    parser.add_argument("--road-core", action="store_true",
                        help="Download full USFS Road Network (337 MB national)")

    # Filtering
    parser.add_argument("--state", "-s", type=str,
                        help="State abbreviation to filter by (e.g., TX, CO, MT)")

    # Processing options
    parser.add_argument("--pmtiles", action="store_true",
                        help="Generate PMTiles (requires tippecanoe)")
    parser.add_argument("--upload", action="store_true",
                        help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true",
                        help="Remove local files after upload")
    parser.add_argument("--force", action="store_true",
                        help="Force re-download and overwrite existing files")

    # Info
    parser.add_argument("--list-states", action="store_true",
                        help="List available states with bounding boxes")
    parser.add_argument("--check-deps", action="store_true",
                        help="Check for required dependencies")

    args = parser.parse_args()

    # Handle info flags
    if args.list_states:
        log("Available states:")
        for abbrev, name in sorted(STATE_NAMES.items()):
            bbox = STATE_BBOXES.get(abbrev, [])
            log(f"  {abbrev}: {name}")
        return

    if args.check_deps:
        check_dependencies()
        return

    # Validate arguments
    if not any([args.roads, args.trails, args.road_core]):
        parser.print_help()
        print("\nError: Must specify at least one data type: --roads, --trails, or --road-core")
        return

    if args.state:
        state_upper = args.state.upper()
        if state_upper not in STATE_BBOXES:
            log(f"Unknown state: {args.state}", "ERROR")
            log("Use --list-states to see available states")
            return

    # Check dependencies
    if not check_dependencies():
        log("Missing required dependencies. Install them and try again.", "ERROR")
        return

    # Ensure directories exist
    ensure_directories()

    # Process requested data types
    results = []

    log("=" * 70)
    log("USFS Motor Vehicle Use Map (MVUM) Downloader")
    log("=" * 70)

    if args.roads:
        log("\n" + "=" * 70)
        log("Processing MVUM Roads")
        log("=" * 70)
        result = process_mvum_data(
            "roads",
            state_abbrev=args.state,
            generate_tiles=args.pmtiles,
            upload=args.upload,
            cleanup=args.cleanup,
            force=args.force
        )
        results.append(result)

    if args.trails:
        log("\n" + "=" * 70)
        log("Processing MVUM Trails")
        log("=" * 70)
        result = process_mvum_data(
            "trails",
            state_abbrev=args.state,
            generate_tiles=args.pmtiles,
            upload=args.upload,
            cleanup=args.cleanup,
            force=args.force
        )
        results.append(result)

    if args.road_core:
        log("\n" + "=" * 70)
        log("Processing USFS Road Core (Full Network)")
        log("=" * 70)
        result = process_mvum_data(
            "road_core",
            state_abbrev=args.state,
            generate_tiles=args.pmtiles,
            upload=args.upload,
            cleanup=args.cleanup,
            force=args.force
        )
        results.append(result)

    # Summary
    log("\n" + "=" * 70)
    log("MVUM Download Summary")
    log("=" * 70)

    for result in results:
        log(f"\n{result['data_type'].upper()}:")
        log(f"  State: {result['state'] or 'National'}")
        if result['geojson_path']:
            log(f"  GeoJSON: {result['geojson_path']}")
        if result['pmtiles_path']:
            log(f"  PMTiles: {result['pmtiles_path']}")
        if result['r2_urls']:
            log(f"  R2 URLs:")
            for url in result['r2_urls']:
                log(f"    - {url}")

    log("\n" + "=" * 70)
    log("MVUM download complete!")
    log("=" * 70)


if __name__ == "__main__":
    main()
