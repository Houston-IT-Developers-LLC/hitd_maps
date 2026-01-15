#!/usr/bin/env python3
"""
Download PAD-US (Protected Areas Database of the United States)

Priority: 1 (Most Important)
Source: USGS Gap Analysis Project
URL: https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-download

This is the most valuable enrichment data for outdoor recreation apps.
Includes all public lands: National Forests, BLM, National Parks, Wildlife Refuges,
State Parks, Conservation Easements, and more.

Update Frequency: Annual (typically October)
Current Version: 4.0
Date Added: 2026-01-13
"""

import os
import sys
import json
import urllib.request
import urllib.error
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
CONFIG_FILE = DATA_PIPELINE_DIR / "config" / "enrichment_sources.json"
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
RAW_DIR = OUTPUT_DIR / "raw" / "pad_us"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# PAD-US Download URLs (ScienceBase)
# Version 4.0 - Released October 2023
# ScienceBase Item ID: 652ef930d34edd15305a9b03
PAD_US_DOWNLOADS = {
    "national_gdb": {
        # Direct file download - ScienceBase API format
        # This downloads PADUS4_0Geodatabase.zip (1.59 GB)
        "url": "https://www.sciencebase.gov/catalog/file/get/652ef930d34edd15305a9b03?f=__disk__16%2F80%2F64%2F168064e3e9f18d91f1c2cd68c5c00f0f53e94eba",
        "filename": "PADUS4_0Geodatabase.zip",
        "description": "National Geodatabase (PAD-US 4.0 Full Inventory)",
        "size_mb": 1590
    },
    # Alternative: direct item page API (returns first/primary file)
    "national_direct": {
        "url": "https://www.sciencebase.gov/catalog/file/get/652ef930d34edd15305a9b03",
        "filename": "PADUS4_0Geodatabase.zip",
        "description": "National Geodatabase (direct API)",
        "size_mb": 1590
    }
}

# State-level downloads are available for smaller downloads
PAD_US_STATE_BASE = "https://www.sciencebase.gov/catalog/item/652ef930d34edd15305a9b03"

# State FIPS codes for ScienceBase downloads
STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
    "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
    "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
    "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
    "DC": "11", "PR": "72", "VI": "78", "GU": "66", "AS": "60", "MP": "69"
}

# State names for queries
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

# Working PAD-US API endpoints (tested and verified)
PAD_US_API_ENDPOINTS = [
    # USFS EDW PADUS - Managed Surface Ownership (most comprehensive, has STATE_NM field)
    {
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_PADUS_01/MapServer/3",
        "state_field": "STATE_NM",
        "name": "USFS PADUS Managed Ownership"
    },
    # USFS EDW PADUS - National Designated Areas
    {
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_PADUS_01/MapServer/1",
        "state_field": "STATE_NM",
        "name": "USFS PADUS Designated Areas"
    },
    # USFS EDW PADUS - Conservation Easements
    {
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_PADUS_01/MapServer/2",
        "state_field": "STATE_NM",
        "name": "USFS PADUS Easements"
    },
]

# Key layers in PAD-US
PAD_US_LAYERS = {
    0: "PAD-US Fee",           # Fee-simple protected areas
    1: "PAD-US Easements",     # Conservation easements
    2: "PAD-US Designations",  # Designation overlays
    3: "PAD-US Proclamation",  # Proclamation boundaries
    4: "PAD-US Marine"         # Marine protected areas
}


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories"""
    for dir_path in [RAW_DIR, GEOJSON_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
        log(f"Directory ready: {dir_path}")


def download_file(url, dest_path, description=""):
    """Download a file with progress indication"""
    log(f"Downloading: {description or url}")
    log(f"  Destination: {dest_path}")

    try:
        # Create request with headers
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

        with urllib.request.urlopen(req, timeout=300) as response:
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
                        print(f"\r  Progress: {downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB ({pct:.1f}%)", end="")

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


def download_via_arcgis_api(state_abbrev, output_file=None):
    """
    Download PAD-US data via ArcGIS REST API with fallback endpoints.

    This method downloads from multiple PAD-US layers and combines them
    into a single comprehensive dataset for the state.
    """
    import urllib.parse
    import ssl

    state_upper = state_abbrev.upper()

    # SSL context to handle certificate issues
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    all_features = []

    # Download from each endpoint/layer
    for endpoint in PAD_US_API_ENDPOINTS:
        base_url = endpoint["url"]
        state_field = endpoint["state_field"]
        layer_name = endpoint["name"]

        log(f"  Querying: {layer_name}")

        # Build query for this state
        where_clause = f"{state_field} = '{state_upper}'"

        offset = 0
        max_iterations = 100  # Safety limit
        layer_features = []

        while offset < max_iterations * 2000:
            params = {
                "where": where_clause,
                "outFields": "*",
                "f": "geojson",
                "returnGeometry": "true",
                "outSR": "4326",
                "resultOffset": str(offset),
                "resultRecordCount": "2000"
            }

            query_string = urllib.parse.urlencode(params)
            url = f"{base_url}/query?{query_string}"

            try:
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

                with urllib.request.urlopen(req, timeout=120, context=ctx) as response:
                    data = json.loads(response.read().decode('utf-8'))

                    # Check for errors
                    if 'error' in data:
                        log(f"    API Error: {data['error'].get('message', 'Unknown')}", "WARNING")
                        break

                    features = data.get('features', [])
                    if not features:
                        break

                    # Add source layer info to each feature
                    for f in features:
                        if 'properties' not in f:
                            f['properties'] = {}
                        f['properties']['_source_layer'] = layer_name

                    layer_features.extend(features)
                    log(f"    Fetched {len(features)} features (layer total: {len(layer_features)})")

                    if len(features) < 2000:
                        break

                    offset += 2000

            except urllib.error.HTTPError as e:
                log(f"    HTTP Error {e.code}: {e.reason}", "WARNING")
                break
            except Exception as e:
                log(f"    Error: {e}", "WARNING")
                break

        all_features.extend(layer_features)
        log(f"    Layer complete: {len(layer_features)} features")

    if all_features:
        geojson = {
            "type": "FeatureCollection",
            "features": all_features,
            "metadata": {
                "source": "PAD-US (USFS EDW)",
                "state": state_upper,
                "feature_count": len(all_features),
                "download_date": datetime.now().isoformat(),
                "layers_included": [e["name"] for e in PAD_US_API_ENDPOINTS]
            }
        }

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(geojson, f)
            log(f"  Saved {len(all_features)} total features to {output_file}")

        return geojson

    log(f"  No features found for {state_abbrev}", "WARNING")
    return None


def download_state_pad_us(state_abbrev):
    """Download PAD-US data for a specific state"""
    state_upper = state_abbrev.upper()
    output_file = GEOJSON_DIR / f"pad_us_{state_upper.lower()}.geojson"

    # Check if already exists
    if output_file.exists():
        log(f"File already exists: {output_file}")
        log("Use --force to re-download")
        return str(output_file)

    log(f"Downloading PAD-US for state: {state_upper} ({STATE_NAMES.get(state_upper, state_upper)})")

    # Download via API with fallback endpoints
    geojson = download_via_arcgis_api(
        state_abbrev=state_upper,
        output_file=output_file
    )

    if geojson:
        log(f"  Success: {output_file}")
        return str(output_file)
    else:
        log(f"  Failed to download PAD-US for {state_upper}", "ERROR")
        return None


def download_national_pad_us(force=False):
    """
    Download the full national PAD-US dataset

    This is a large download (~1.6GB) but provides complete coverage.
    For state-by-state approach, use download_state_pad_us() instead.
    """
    log("=" * 60)
    log("PAD-US National Download")
    log("=" * 60)
    log("Downloading PAD-US 4.0 National Geodatabase (~1.6GB)")
    log("=" * 60)

    # Try the direct API first, then fall back to explicit file URL
    download_options = ["national_direct", "national_gdb"]

    for option in download_options:
        download_info = PAD_US_DOWNLOADS[option]
        zip_path = RAW_DIR / download_info["filename"]

        # Check if already downloaded
        if zip_path.exists() and not force:
            log(f"File already exists: {zip_path}")
            log("Use --force to re-download")
            return str(zip_path)

        if zip_path.exists() and force:
            log(f"Removing existing file for re-download: {zip_path}")
            os.remove(zip_path)

        log(f"Trying download option: {option}")
        success = download_file(
            url=download_info["url"],
            dest_path=zip_path,
            description=download_info["description"]
        )

        if success and zip_path.exists() and zip_path.stat().st_size > 100000000:  # >100MB = valid
            # Extract
            log("Extracting geodatabase...")
            extract_zip(zip_path, RAW_DIR)
            return str(zip_path)
        elif success:
            log(f"Download seems incomplete or wrong file, trying next option", "WARNING")
            if zip_path.exists():
                os.remove(zip_path)

    log("All download options failed", "ERROR")
    return None


# Categories of public lands relevant for hunting/recreation
HUNTABLE_LAND_CATEGORIES = {
    # Manager Name patterns (d_Mang_Nam field)
    "manager_names": [
        "USFS",  # US Forest Service
        "BLM",   # Bureau of Land Management
        "FWS",   # US Fish and Wildlife Service
        "NPS",   # National Park Service (limited hunting)
        "USACE", # Army Corps of Engineers
        "BOR",   # Bureau of Reclamation
        "TVA",   # Tennessee Valley Authority
    ],
    # Owner Type patterns (d_Own_Type field)
    "owner_types": [
        "FED",   # Federal
        "STAT",  # State
        "LOC",   # Local
    ],
    # Designation Type patterns (d_Des_Tp field)
    "designation_types": [
        "NF",    # National Forest
        "NG",    # National Grassland
        "NWR",   # National Wildlife Refuge
        "WA",    # Wildlife Area
        "WMA",   # Wildlife Management Area
        "SP",    # State Park
        "SF",    # State Forest
        "NCA",   # National Conservation Area
        "WSA",   # Wilderness Study Area
        "WILD",  # Wilderness
        "RNA",   # Research Natural Area
        "REC",   # Recreation Area
    ],
    # Unit Name patterns to include
    "unit_patterns": [
        "National Forest",
        "National Grassland",
        "Wildlife Refuge",
        "Wildlife Area",
        "Wildlife Management",
        "State Forest",
        "State Park",
        "BLM",
        "Public Land",
        "Conservation Area",
    ]
}


def filter_fee_layer_for_hunting(input_gdb_path, output_geojson):
    """
    Extract and filter the PAD-US Fee layer for hunting-relevant public lands.

    The Fee layer contains parcels where public agencies own the land outright
    (as opposed to easements or designations). This is the most important layer
    for determining where hunting is allowed.
    """
    import subprocess

    log("=" * 60)
    log("Filtering PAD-US Fee Layer for Huntable Public Lands")
    log("=" * 60)

    # Find the geodatabase
    gdb_path = None
    if os.path.isdir(input_gdb_path):
        gdb_path = input_gdb_path
    else:
        # Look for extracted .gdb folder
        for item in RAW_DIR.iterdir():
            if item.suffix == '.gdb' and item.is_dir():
                gdb_path = item
                break

    if not gdb_path:
        log("Could not find geodatabase. Looking for extracted files...", "ERROR")
        # List what we have
        for item in RAW_DIR.iterdir():
            log(f"  Found: {item}")
        return None

    log(f"Using geodatabase: {gdb_path}")

    # List layers in geodatabase
    log("Listing available layers...")
    list_cmd = ["ogrinfo", "-so", str(gdb_path)]
    try:
        result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=60)
        log(f"Layers found:\n{result.stdout}")
    except Exception as e:
        log(f"Error listing layers: {e}", "WARNING")

    # The Fee layer is typically named "PADUS4_0Fee" or similar
    fee_layer_names = ["PADUS4_0Fee", "PADUS4_0_Fee", "PAD_US_Fee", "Fee"]
    fee_layer = None

    for layer_name in fee_layer_names:
        check_cmd = ["ogrinfo", "-so", str(gdb_path), layer_name]
        try:
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and "Layer name:" in result.stdout:
                fee_layer = layer_name
                log(f"Found Fee layer: {fee_layer}")
                break
        except:
            continue

    if not fee_layer:
        log("Could not find Fee layer. Will extract all features.", "WARNING")
        fee_layer = None  # Will use first layer or all

    # Build SQL filter for hunting-relevant lands
    # Focus on: National Forests, BLM, NWR, State Parks, State Forests, WMAs
    sql_filter = """
        d_Own_Type IN ('FED', 'STAT', 'LOC')
        OR d_Mang_Typ IN ('FED', 'STAT', 'LOC')
        OR Mang_Name LIKE '%Forest Service%'
        OR Mang_Name LIKE '%BLM%'
        OR Mang_Name LIKE '%Bureau of Land%'
        OR Mang_Name LIKE '%Fish and Wildlife%'
        OR Mang_Name LIKE '%Wildlife%'
        OR Mang_Name LIKE '%State Park%'
        OR Mang_Name LIKE '%State Forest%'
        OR Mang_Name LIKE '%Game%'
        OR d_Des_Tp IN ('NF', 'NG', 'NWR', 'WA', 'WMA', 'SP', 'SF', 'NCA', 'WSA', 'WILD', 'REC')
        OR Unit_Nm LIKE '%National Forest%'
        OR Unit_Nm LIKE '%National Grassland%'
        OR Unit_Nm LIKE '%Wildlife%'
        OR Unit_Nm LIKE '%State Forest%'
        OR Unit_Nm LIKE '%State Park%'
        OR Unit_Nm LIKE '%BLM%'
        OR Unit_Nm LIKE '%Conservation%'
    """

    # Convert to GeoJSON with filter
    log("Converting Fee layer to GeoJSON with hunting filter...")

    # First try with filter
    output_path = Path(output_geojson)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if fee_layer:
        cmd = [
            "ogr2ogr",
            "-f", "GeoJSON",
            "-t_srs", "EPSG:4326",
            "-sql", f"SELECT * FROM {fee_layer} WHERE {sql_filter}",
            str(output_path),
            str(gdb_path)
        ]
    else:
        # No specific layer found, try without SQL
        cmd = [
            "ogr2ogr",
            "-f", "GeoJSON",
            "-t_srs", "EPSG:4326",
            str(output_path),
            str(gdb_path)
        ]

    try:
        log(f"Running: {' '.join(cmd[:6])}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)

        if result.returncode != 0:
            log(f"Filter failed: {result.stderr}", "WARNING")

            # Try without filter - get all Fee layer data
            log("Trying to extract full Fee layer without filter...")
            cmd_simple = [
                "ogr2ogr",
                "-f", "GeoJSON",
                "-t_srs", "EPSG:4326",
                str(output_path),
                str(gdb_path),
                fee_layer if fee_layer else ""
            ]
            cmd_simple = [c for c in cmd_simple if c]  # Remove empty strings

            result = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=7200)

            if result.returncode != 0:
                log(f"Full extraction also failed: {result.stderr}", "ERROR")
                return None

        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            log(f"Created: {output_path} ({size_mb:.1f} MB)")
            return str(output_path)
        else:
            log("Output file not created", "ERROR")
            return None

    except subprocess.TimeoutExpired:
        log("Conversion timed out (2 hours)", "ERROR")
        return None
    except FileNotFoundError:
        log("ogr2ogr not found. Install GDAL: sudo apt-get install gdal-bin", "ERROR")
        return None
    except Exception as e:
        log(f"Error: {e}", "ERROR")
        return None


def convert_to_geojson(input_path, output_path):
    """Convert GeoPackage/Shapefile to GeoJSON using ogr2ogr"""
    import subprocess

    log(f"Converting to GeoJSON: {input_path}")

    cmd = [
        "ogr2ogr",
        "-f", "GeoJSON",
        "-t_srs", "EPSG:4326",
        str(output_path),
        str(input_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            log(f"  Converted: {output_path}")
            return True
        else:
            log(f"  Conversion error: {result.stderr}", "ERROR")
            return False
    except subprocess.TimeoutExpired:
        log("  Conversion timed out", "ERROR")
        return False
    except FileNotFoundError:
        log("  ogr2ogr not found. Install GDAL: sudo apt-get install gdal-bin", "ERROR")
        return False


def generate_pmtiles(geojson_path, pmtiles_path):
    """Generate PMTiles from GeoJSON"""
    import subprocess

    log(f"Generating PMTiles: {geojson_path}")

    cmd = [
        "tippecanoe",
        "-z14",
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "-l", "public_lands",
        "-o", str(pmtiles_path),
        str(geojson_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if result.returncode == 0:
            log(f"  Generated: {pmtiles_path}")
            return True
        else:
            log(f"  PMTiles error: {result.stderr}", "ERROR")
            return False
    except subprocess.TimeoutExpired:
        log("  PMTiles generation timed out", "ERROR")
        return False
    except FileNotFoundError:
        log("  tippecanoe not found. See docs for installation.", "ERROR")
        return False


def upload_to_r2(local_path, r2_key):
    """Upload file to Cloudflare R2"""
    import boto3

    # R2 Configuration (from main upload script)
    R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
    R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
    R2_BUCKET = "gspot-tiles"
    R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
    R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

    log(f"Uploading to R2: {r2_key}")

    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )

        # Determine content type
        if local_path.endswith('.geojson'):
            content_type = 'application/geo+json'
        elif local_path.endswith('.pmtiles'):
            content_type = 'application/x-protobuf'
        else:
            content_type = 'application/octet-stream'

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


def cleanup_local(path):
    """Remove local file after successful upload"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            log(f"  Removed local file: {path}")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            log(f"  Removed local directory: {path}")
    except Exception as e:
        log(f"  Cleanup error: {e}", "WARNING")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download PAD-US (Protected Areas Database)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download PAD-US for a specific state (recommended)
  python3 download_pad_us.py --state TX

  # Download multiple states
  python3 download_pad_us.py --state TX,CA,CO

  # Download all states (one by one via API)
  python3 download_pad_us.py --all-states

  # Download national dataset and process Fee layer (~1.6GB download)
  python3 download_pad_us.py --national

  # Full national pipeline: download, filter, generate tiles, upload
  python3 download_pad_us.py --national --filter-fee --pmtiles --upload

  # Full pipeline: download, convert, generate tiles, upload, cleanup
  python3 download_pad_us.py --state TX --pmtiles --upload --cleanup
        """
    )

    parser.add_argument("--state", "-s", help="State abbreviation(s), comma-separated (e.g., TX,CA,CO)")
    parser.add_argument("--all-states", action="store_true", help="Download all states via API")
    parser.add_argument("--national", action="store_true", help="Download national dataset (~1.6GB)")
    parser.add_argument("--filter-fee", action="store_true", help="Filter to Fee layer hunting-relevant lands")
    parser.add_argument("--pmtiles", action="store_true", help="Generate PMTiles after download")
    parser.add_argument("--upload", action="store_true", help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true", help="Remove local files after upload")
    parser.add_argument("--force", action="store_true", help="Force re-download even if files exist")
    parser.add_argument("--list-layers", action="store_true", help="List available PAD-US layers")

    args = parser.parse_args()

    # Ensure directories exist
    ensure_directories()

    if args.list_layers:
        log("PAD-US Layers:")
        for layer_id, name in PAD_US_LAYERS.items():
            log(f"  {layer_id}: {name}")
        return

    if args.national:
        # Download national dataset
        zip_path = download_national_pad_us(force=args.force)

        if not zip_path:
            log("National download failed", "ERROR")
            return

        # Filter to Fee layer if requested
        geojson_path = None
        if args.filter_fee:
            output_geojson = GEOJSON_DIR / "pad_us_national_fee.geojson"
            geojson_path = filter_fee_layer_for_hunting(str(RAW_DIR), str(output_geojson))

            if not geojson_path:
                log("Fee layer filtering failed", "ERROR")
                return

        # Generate PMTiles
        pmtiles_path = None
        if args.pmtiles and geojson_path:
            pmtiles_dir = OUTPUT_DIR / "pmtiles"
            pmtiles_dir.mkdir(parents=True, exist_ok=True)
            pmtiles_path = pmtiles_dir / "pad_us_national.pmtiles"

            log("Generating PMTiles for national coverage...")
            generate_pmtiles(geojson_path, pmtiles_path)

        # Upload to R2
        if args.upload:
            if geojson_path and Path(geojson_path).exists():
                r2_key = "enrichment/pad_us/pad_us_national_fee.geojson"
                upload_to_r2(geojson_path, r2_key)

            if pmtiles_path and pmtiles_path.exists():
                r2_key = "enrichment/pad_us/pad_us_national.pmtiles"
                upload_to_r2(str(pmtiles_path), r2_key)

        # Cleanup local files
        if args.cleanup and args.upload:
            if geojson_path:
                cleanup_local(geojson_path)
            if pmtiles_path:
                cleanup_local(str(pmtiles_path))
            # Keep raw geodatabase for reference

        log("=" * 60)
        log("National PAD-US processing complete!")
        log("=" * 60)
        return

    # Default to state-by-state download
    states = []
    if args.state:
        states = [s.strip().upper() for s in args.state.split(",")]
    elif args.all_states:
        # All US states
        states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ]
    else:
        parser.print_help()
        return

    log(f"Processing {len(states)} states: {', '.join(states)}")

    pmtiles_dir = OUTPUT_DIR / "pmtiles"
    pmtiles_dir.mkdir(parents=True, exist_ok=True)

    for state in states:
        log("=" * 60)
        log(f"Processing: {state}")
        log("=" * 60)

        # Download
        geojson_path = download_state_pad_us(state)
        if not geojson_path:
            continue

        # Generate PMTiles
        if args.pmtiles:
            pmtiles_path = pmtiles_dir / f"pad_us_{state.lower()}.pmtiles"
            generate_pmtiles(geojson_path, pmtiles_path)

        # Upload to R2
        if args.upload:
            # Upload GeoJSON
            r2_key = f"enrichment/pad_us/pad_us_{state.lower()}.geojson"
            upload_to_r2(geojson_path, r2_key)

            # Upload PMTiles if generated
            if args.pmtiles:
                pmtiles_path = pmtiles_dir / f"pad_us_{state.lower()}.pmtiles"
                if pmtiles_path.exists():
                    r2_key = f"enrichment/pad_us/pad_us_{state.lower()}.pmtiles"
                    upload_to_r2(str(pmtiles_path), r2_key)

        # Cleanup local files
        if args.cleanup and args.upload:
            cleanup_local(geojson_path)
            if args.pmtiles:
                pmtiles_path = pmtiles_dir / f"pad_us_{state.lower()}.pmtiles"
                cleanup_local(str(pmtiles_path))

    log("=" * 60)
    log("PAD-US download complete!")
    log("=" * 60)


if __name__ == "__main__":
    main()
