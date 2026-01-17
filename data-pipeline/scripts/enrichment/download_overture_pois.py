#!/usr/bin/env python3
"""
Download Overture Maps Places (POI) Dataset

Priority: 1 (Critical - 64M+ business POIs for consumer maps)
Source: Overture Maps Foundation
URL: https://overturemaps.org/

Overture Maps Places contains 64M+ global points of interest including:
- Businesses (restaurants, shops, services)
- Landmarks and attractions
- Public facilities
- And more

Data Sources:
  - Direct: overturemaps Python CLI (pip install overturemaps)
  - DuckDB: Efficient state-by-state queries from Overture S3 bucket

Key Fields Preserved:
  - id: Unique identifier
  - names.primary: Primary name
  - categories.primary: Primary category
  - categories.alternate: Alternate categories
  - addresses: Freeform, locality, region, country
  - phones, emails, websites, socials: Contact info
  - brand: Brand information
  - confidence: Data confidence score
  - geometry: Point location

Update Frequency: Quarterly releases
Current Release: 2025-01-15.0
Date Added: 2026-01-17

Usage:
  # Download for specific states
  python3 download_overture_pois.py --state TX,CA,CO --pmtiles --upload

  # Download all 50 states
  python3 download_overture_pois.py --all-states --pmtiles --upload

  # Download entire USA at once (large, ~5GB)
  python3 download_overture_pois.py --national --pmtiles --upload
"""

import os
import sys
import json
import subprocess
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
RAW_DIR = OUTPUT_DIR / "raw" / "overture_pois"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

# Overture Maps Configuration
# Latest release as of 2026-01-17
OVERTURE_RELEASE = "2025-01-15.0"
OVERTURE_S3_BUCKET = "overturemaps-us-west-2"
OVERTURE_S3_REGION = "us-west-2"
OVERTURE_PLACES_PATH = f"s3://{OVERTURE_S3_BUCKET}/release/{OVERTURE_RELEASE}/theme=places/*/*"

# USA bounding box for national download
USA_BBOX = [-125, 24, -66, 50]  # [west, south, east, north]

# State bounding boxes (west, south, east, north) in WGS84
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
    "WY": [-111.1, 41.0, -104.1, 45.0],
    "DC": [-77.1, 38.8, -76.9, 39.0],
    "PR": [-67.3, 17.9, -65.2, 18.5]
}

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
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia", "PR": "Puerto Rico"
}

# State abbreviation to region name mapping for Overture filtering
STATE_REGION_NAMES = {
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
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia", "PR": "Puerto Rico"
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
    available = {"duckdb": False, "overturemaps": False, "tippecanoe": False}

    # Check DuckDB (preferred method)
    try:
        import duckdb
        available["duckdb"] = True
        log("Found: DuckDB (preferred method)")
    except ImportError:
        missing.append("duckdb - Install: pip install duckdb")

    # Check overturemaps CLI (alternative method)
    try:
        result = subprocess.run(
            ["overturemaps", "--help"],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            available["overturemaps"] = True
            log("Found: overturemaps CLI")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        missing.append("overturemaps - Install: pip install overturemaps")

    # Check tippecanoe for PMTiles generation
    try:
        result = subprocess.run(
            ["tippecanoe", "--version"],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            available["tippecanoe"] = True
            log("Found: tippecanoe")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        missing.append("tippecanoe - Install: see https://github.com/felt/tippecanoe")

    if not available["duckdb"] and not available["overturemaps"]:
        log("ERROR: Need either duckdb or overturemaps CLI", "ERROR")
        log("Install with: pip install duckdb  OR  pip install overturemaps", "ERROR")
        return None

    if missing:
        log("Optional missing dependencies:", "WARNING")
        for dep in missing:
            log(f"  - {dep}", "WARNING")

    return available


def download_via_duckdb(bbox, output_path, state_abbrev=None, region_filter=None):
    """
    Download Overture Places using DuckDB (most efficient method).

    This method directly queries the Overture S3 bucket using DuckDB's
    spatial and httpfs extensions for efficient filtering.

    Args:
        bbox: Bounding box [west, south, east, north]
        output_path: Output GeoJSON file path
        state_abbrev: Optional state abbreviation for logging
        region_filter: Optional region name to filter by (e.g., "Texas")

    Returns:
        Path to output file or None on failure
    """
    try:
        import duckdb
    except ImportError:
        log("DuckDB not installed. Install with: pip install duckdb", "ERROR")
        return None

    location_desc = state_abbrev if state_abbrev else "specified bbox"
    log(f"Downloading Overture Places via DuckDB for {location_desc}")
    log(f"  Bbox: {bbox}")
    log(f"  Release: {OVERTURE_RELEASE}")

    try:
        # Create DuckDB connection
        conn = duckdb.connect()

        # Install and load required extensions
        log("  Loading DuckDB extensions...")
        conn.execute("INSTALL spatial;")
        conn.execute("INSTALL httpfs;")
        conn.execute("LOAD spatial;")
        conn.execute("LOAD httpfs;")

        # Configure S3 access (Overture data is public)
        conn.execute(f"SET s3_region='{OVERTURE_S3_REGION}';")

        # Build the query with all POI fields
        west, south, east, north = bbox

        # Build WHERE clause
        where_conditions = [
            f"bbox.xmin >= {west}",
            f"bbox.xmax <= {east}",
            f"bbox.ymin >= {south}",
            f"bbox.ymax <= {north}"
        ]

        # Add region filter if specified (for state filtering)
        if region_filter:
            where_conditions.append(f"addresses[1].region = '{region_filter}'")

        # Always filter to US
        where_conditions.append("addresses[1].country = 'US'")

        where_clause = " AND ".join(where_conditions)

        query = f"""
        SELECT
            id,
            names.primary AS name,
            categories.primary AS category_primary,
            categories.alternate AS category_alternate,
            addresses[1].freeform AS address_freeform,
            addresses[1].locality AS address_city,
            addresses[1].region AS address_state,
            addresses[1].country AS address_country,
            addresses[1].postcode AS address_postcode,
            phones[1] AS phone,
            websites[1] AS website,
            socials AS socials,
            brand.names.primary AS brand_name,
            confidence AS confidence,
            ST_GeomFromWKB(geometry) AS geometry
        FROM read_parquet('{OVERTURE_PLACES_PATH}', filename=true, hive_partitioning=1)
        WHERE {where_clause}
        """

        log("  Executing query (this may take several minutes)...")
        start_time = datetime.now()

        # Execute query and get results
        result = conn.execute(query)

        # Convert to GeoJSON
        log("  Converting to GeoJSON...")
        features = []
        row_count = 0

        for row in result.fetchall():
            row_count += 1
            if row_count % 100000 == 0:
                log(f"    Processed {row_count:,} features...")

            # Build properties from row
            properties = {
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "categories_alt": row[3] if row[3] else [],
                "address": row[4],
                "city": row[5],
                "state": row[6],
                "country": row[7],
                "postcode": row[8],
                "phone": row[9],
                "website": row[10],
                "socials": row[11] if row[11] else [],
                "brand": row[12],
                "confidence": row[13]
            }

            # Clean up None values
            properties = {k: v for k, v in properties.items() if v is not None}

            # Get geometry (last column)
            geom = row[14]
            if geom:
                # DuckDB returns geometry as WKB, convert to GeoJSON
                geom_json = conn.execute(
                    f"SELECT ST_AsGeoJSON(ST_GeomFromWKB('{geom.hex()}'))"
                ).fetchone()[0]

                feature = {
                    "type": "Feature",
                    "properties": properties,
                    "geometry": json.loads(geom_json)
                }
                features.append(feature)

        elapsed = (datetime.now() - start_time).total_seconds()
        log(f"  Query completed in {elapsed:.1f}s, {len(features):,} features")

        if not features:
            log(f"  No features found for {location_desc}", "WARNING")
            conn.close()
            return None

        # Write GeoJSON
        geojson = {
            "type": "FeatureCollection",
            "name": f"Overture Places" + (f" - {state_abbrev}" if state_abbrev else " - USA"),
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": features,
            "metadata": {
                "source": "Overture Maps Foundation",
                "release": OVERTURE_RELEASE,
                "download_date": datetime.now().isoformat(),
                "state": state_abbrev,
                "feature_count": len(features),
                "bbox": bbox
            }
        }

        log(f"  Writing {len(features):,} features to {output_path}...")
        with open(output_path, 'w') as f:
            json.dump(geojson, f)

        size_mb = output_path.stat().st_size / (1024 * 1024)
        log(f"  Saved: {output_path} ({size_mb:.1f} MB)")

        conn.close()
        return str(output_path)

    except Exception as e:
        log(f"  DuckDB error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return None


def download_via_cli(bbox, output_path, state_abbrev=None):
    """
    Download Overture Places using the overturemaps CLI.

    This is an alternative to DuckDB that uses the official CLI tool.

    Args:
        bbox: Bounding box [west, south, east, north]
        output_path: Output GeoJSON file path
        state_abbrev: Optional state abbreviation for logging

    Returns:
        Path to output file or None on failure
    """
    location_desc = state_abbrev if state_abbrev else "specified bbox"
    log(f"Downloading Overture Places via CLI for {location_desc}")
    log(f"  Bbox: {bbox}")

    west, south, east, north = bbox
    bbox_str = f"{west},{south},{east},{north}"

    cmd = [
        "overturemaps", "download",
        "--bbox", bbox_str,
        "-f", "geojson",
        "--type", "place",
        "-o", str(output_path)
    ]

    try:
        log("  Running overturemaps CLI (this may take several minutes)...")
        start_time = datetime.now()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout for large downloads
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        if result.returncode != 0:
            log(f"  CLI error: {result.stderr}", "ERROR")
            return None

        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            log(f"  Download completed in {elapsed:.1f}s")
            log(f"  Saved: {output_path} ({size_mb:.1f} MB)")

            # Count features
            with open(output_path, 'r') as f:
                data = json.load(f)
                feature_count = len(data.get('features', []))
                log(f"  Features: {feature_count:,}")

            return str(output_path)
        else:
            log(f"  Output file not created", "ERROR")
            return None

    except subprocess.TimeoutExpired:
        log("  Download timed out after 2 hours", "ERROR")
        return None
    except FileNotFoundError:
        log("  overturemaps CLI not found. Install with: pip install overturemaps", "ERROR")
        return None
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def download_overture_pois(state_abbrev=None, use_duckdb=True, force=False):
    """
    Download Overture POIs for a state or national coverage.

    Args:
        state_abbrev: State abbreviation (e.g., "TX") or None for national
        use_duckdb: Use DuckDB (True) or CLI (False)
        force: Force re-download even if file exists

    Returns:
        Path to GeoJSON file or None
    """
    if state_abbrev:
        state_upper = state_abbrev.upper()
        bbox = STATE_BBOXES.get(state_upper)
        if not bbox:
            log(f"Unknown state: {state_abbrev}", "ERROR")
            return None
        region_filter = STATE_REGION_NAMES.get(state_upper)
        output_filename = f"overture_pois_{state_upper.lower()}.geojson"
    else:
        bbox = USA_BBOX
        region_filter = None
        output_filename = "overture_pois_usa.geojson"

    output_path = GEOJSON_DIR / output_filename

    # Check if already exists
    if not force and output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        log(f"File already exists: {output_path} ({size_mb:.1f} MB)")
        log("Use --force to re-download")
        return str(output_path)

    # Try DuckDB first, fall back to CLI
    if use_duckdb:
        result = download_via_duckdb(bbox, output_path, state_abbrev, region_filter)
        if result:
            return result
        log("DuckDB download failed, trying CLI...", "WARNING")

    # Fall back to CLI
    return download_via_cli(bbox, output_path, state_abbrev)


def generate_pmtiles(geojson_path, pmtiles_path, layer_name="places"):
    """
    Generate PMTiles from GeoJSON.

    Args:
        geojson_path: Input GeoJSON file
        pmtiles_path: Output PMTiles file
        layer_name: Name for the tile layer

    Returns:
        True on success, False on failure
    """
    log(f"Generating PMTiles: {geojson_path}")

    # POIs are visible at higher zooms (z10+) for readability
    min_zoom = "5"
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
        start_time = datetime.now()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        if result.returncode == 0:
            if pmtiles_path.exists():
                size_mb = pmtiles_path.stat().st_size / (1024 * 1024)
                log(f"  Generated in {elapsed:.1f}s: {pmtiles_path} ({size_mb:.1f} MB)")
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


def process_state(state_abbrev, generate_tiles=True, upload=False,
                  cleanup=False, force=False, use_duckdb=True):
    """
    Full pipeline for a single state.

    Args:
        state_abbrev: State abbreviation
        generate_tiles: Generate PMTiles
        upload: Upload to R2
        cleanup: Remove local files after upload
        force: Force re-download
        use_duckdb: Use DuckDB (True) or CLI (False)

    Returns:
        Dict with result info
    """
    result = {
        "state": state_abbrev,
        "geojson_path": None,
        "pmtiles_path": None,
        "r2_urls": []
    }

    # Download
    geojson_path = download_overture_pois(
        state_abbrev=state_abbrev,
        use_duckdb=use_duckdb,
        force=force
    )

    if not geojson_path:
        log(f"Failed to download POIs for {state_abbrev}", "ERROR")
        return result

    result["geojson_path"] = geojson_path

    # Generate PMTiles
    if generate_tiles:
        pmtiles_filename = f"overture_pois_{state_abbrev.lower()}.pmtiles"
        pmtiles_path = PMTILES_DIR / pmtiles_filename

        if not force and pmtiles_path.exists():
            log(f"Using existing PMTiles: {pmtiles_path}")
            result["pmtiles_path"] = str(pmtiles_path)
        else:
            success = generate_pmtiles(
                Path(geojson_path),
                pmtiles_path,
                layer_name="places"
            )
            if success:
                result["pmtiles_path"] = str(pmtiles_path)

    # Upload
    if upload and result["pmtiles_path"]:
        files_to_cleanup = []

        # Upload PMTiles (skip GeoJSON to save space - PMTiles is more efficient)
        pmtiles_r2_key = f"pois/overture_pois_{state_abbrev.lower()}.pmtiles"
        url = upload_to_r2(result["pmtiles_path"], pmtiles_r2_key)
        if url:
            result["r2_urls"].append(url)
            files_to_cleanup.append(result["pmtiles_path"])
            files_to_cleanup.append(result["geojson_path"])

        # Cleanup
        if cleanup and files_to_cleanup:
            log("Cleaning up local files...")
            cleanup_local(files_to_cleanup)

    return result


def process_national(generate_tiles=True, upload=False, cleanup=False,
                     force=False, use_duckdb=True):
    """
    Full pipeline for national USA coverage.

    Args:
        generate_tiles: Generate PMTiles
        upload: Upload to R2
        cleanup: Remove local files after upload
        force: Force re-download
        use_duckdb: Use DuckDB (True) or CLI (False)

    Returns:
        Dict with result info
    """
    result = {
        "state": "USA",
        "geojson_path": None,
        "pmtiles_path": None,
        "r2_urls": []
    }

    # Download
    geojson_path = download_overture_pois(
        state_abbrev=None,
        use_duckdb=use_duckdb,
        force=force
    )

    if not geojson_path:
        log("Failed to download national POIs", "ERROR")
        return result

    result["geojson_path"] = geojson_path

    # Generate PMTiles
    if generate_tiles:
        pmtiles_filename = "overture_pois_usa.pmtiles"
        pmtiles_path = PMTILES_DIR / pmtiles_filename

        if not force and pmtiles_path.exists():
            log(f"Using existing PMTiles: {pmtiles_path}")
            result["pmtiles_path"] = str(pmtiles_path)
        else:
            success = generate_pmtiles(
                Path(geojson_path),
                pmtiles_path,
                layer_name="places"
            )
            if success:
                result["pmtiles_path"] = str(pmtiles_path)

    # Upload
    if upload and result["pmtiles_path"]:
        files_to_cleanup = []

        # Upload PMTiles
        pmtiles_r2_key = "pois/overture_pois_usa.pmtiles"
        url = upload_to_r2(result["pmtiles_path"], pmtiles_r2_key)
        if url:
            result["r2_urls"].append(url)
            files_to_cleanup.append(result["pmtiles_path"])
            files_to_cleanup.append(result["geojson_path"])

        # Cleanup
        if cleanup and files_to_cleanup:
            log("Cleaning up local files...")
            cleanup_local(files_to_cleanup)

    return result


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download Overture Maps Places (POI) Dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download POIs for specific states
  python3 download_overture_pois.py --state TX,CA,CO --pmtiles

  # Download all 50 states (parallel processing)
  python3 download_overture_pois.py --all-states --pmtiles --upload

  # Download entire USA at once (large, ~5GB GeoJSON)
  python3 download_overture_pois.py --national --pmtiles --upload

  # Full pipeline with cleanup
  python3 download_overture_pois.py --state TX --pmtiles --upload --cleanup

  # Use CLI instead of DuckDB
  python3 download_overture_pois.py --state TX --use-cli

Data Fields in Output:
  id                - Unique Overture ID
  name              - Primary name
  category          - Primary category
  categories_alt    - Alternative categories
  address           - Full street address
  city              - City/locality
  state             - State/region
  country           - Country code
  postcode          - ZIP/postal code
  phone             - Primary phone number
  website           - Primary website
  socials           - Social media links
  brand             - Brand name
  confidence        - Data confidence score (0-1)

Overture Release: {release}
        """.format(release=OVERTURE_RELEASE)
    )

    # Download scope
    parser.add_argument("--state", "-s", type=str,
                        help="State abbreviation(s), comma-separated (e.g., TX,CA,CO)")
    parser.add_argument("--all-states", action="store_true",
                        help="Download all 50 US states")
    parser.add_argument("--national", action="store_true",
                        help="Download entire USA at once (large download)")

    # Processing options
    parser.add_argument("--pmtiles", action="store_true",
                        help="Generate PMTiles (requires tippecanoe)")
    parser.add_argument("--upload", action="store_true",
                        help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true",
                        help="Remove local files after upload")
    parser.add_argument("--force", action="store_true",
                        help="Force re-download and overwrite existing files")

    # Method selection
    parser.add_argument("--use-cli", action="store_true",
                        help="Use overturemaps CLI instead of DuckDB")

    # Info
    parser.add_argument("--list-states", action="store_true",
                        help="List available states")
    parser.add_argument("--check-deps", action="store_true",
                        help="Check for required dependencies")

    args = parser.parse_args()

    # Handle info flags
    if args.list_states:
        log("Available states:")
        for abbrev, name in sorted(STATE_NAMES.items()):
            log(f"  {abbrev}: {name}")
        return

    if args.check_deps:
        check_dependencies()
        return

    # Check dependencies
    deps = check_dependencies()
    if not deps:
        return

    # Validate we can use requested method
    use_duckdb = not args.use_cli
    if use_duckdb and not deps.get("duckdb"):
        if deps.get("overturemaps"):
            log("DuckDB not available, falling back to CLI", "WARNING")
            use_duckdb = False
        else:
            log("No download method available", "ERROR")
            return

    # Ensure directories exist
    ensure_directories()

    log("=" * 70)
    log("Overture Maps Places (POI) Downloader")
    log(f"Release: {OVERTURE_RELEASE}")
    log("=" * 70)

    results = []

    # Process based on arguments
    if args.national:
        result = process_national(
            generate_tiles=args.pmtiles,
            upload=args.upload,
            cleanup=args.cleanup,
            force=args.force,
            use_duckdb=use_duckdb
        )
        results.append(result)

    elif args.all_states:
        # All 50 US states
        states = list(STATE_BBOXES.keys())
        log(f"Processing {len(states)} states...")

        for state in states:
            log("\n" + "=" * 60)
            log(f"Processing: {state} ({STATE_NAMES.get(state, state)})")
            log("=" * 60)

            result = process_state(
                state_abbrev=state,
                generate_tiles=args.pmtiles,
                upload=args.upload,
                cleanup=args.cleanup,
                force=args.force,
                use_duckdb=use_duckdb
            )
            results.append(result)

    elif args.state:
        # Specific states
        states = [s.strip().upper() for s in args.state.split(",")]
        log(f"Processing {len(states)} states: {', '.join(states)}")

        for state in states:
            if state not in STATE_BBOXES:
                log(f"Unknown state: {state}", "ERROR")
                continue

            log("\n" + "=" * 60)
            log(f"Processing: {state} ({STATE_NAMES.get(state, state)})")
            log("=" * 60)

            result = process_state(
                state_abbrev=state,
                generate_tiles=args.pmtiles,
                upload=args.upload,
                cleanup=args.cleanup,
                force=args.force,
                use_duckdb=use_duckdb
            )
            results.append(result)

    else:
        parser.print_help()
        return

    # Summary
    log("\n" + "=" * 70)
    log("Overture POI Download Summary")
    log("=" * 70)

    successful = sum(1 for r in results if r["geojson_path"])
    failed = len(results) - successful

    log(f"\nProcessed: {len(results)} regions")
    log(f"Successful: {successful}")
    log(f"Failed: {failed}")

    if any(r["r2_urls"] for r in results):
        log("\nUploaded URLs:")
        for r in results:
            for url in r["r2_urls"]:
                log(f"  - {url}")

    log("\n" + "=" * 70)
    log("Overture POI download complete!")
    log("=" * 70)


if __name__ == "__main__":
    main()
