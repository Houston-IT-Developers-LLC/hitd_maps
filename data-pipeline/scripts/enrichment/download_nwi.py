#!/usr/bin/env python3
"""
Download National Wetlands Inventory (NWI) Data

Priority: 2
Source: US Fish & Wildlife Service
URL: https://www.fws.gov/program/national-wetlands-inventory

Wetlands data is critical for:
- Waterfowl hunting identification
- Fishing access points
- Seasonal flooding awareness
- Wildlife habitat assessment

Update Frequency: Biannual (May and October)
Current Version: 2024
Date Added: 2026-01-13
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import zipfile
from pathlib import Path
from datetime import datetime

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
RAW_DIR = OUTPUT_DIR / "raw" / "nwi"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# NWI REST API
NWI_FEATURE_SERVICE = "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer"
NWI_LAYER_ID = 0  # Wetlands layer

# NWI Download Portal (for bulk state downloads)
NWI_STATE_DOWNLOAD_BASE = "https://www.fws.gov/wetlands/Data/State-Downloads.html"

# State FIPS codes for NWI downloads
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
    "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56"
}

# State bounding boxes (xmin, ymin, xmax, ymax) in WGS84
# NWI requires spatial queries, not state field queries
STATE_BBOX = {
    "AL": (-88.473, 30.221, -84.889, 35.008),
    "AK": (-179.148, 51.214, -129.980, 71.352),
    "AZ": (-114.814, 31.332, -109.045, 37.004),
    "AR": (-94.618, 33.004, -89.644, 36.500),
    "CA": (-124.409, 32.534, -114.131, 42.009),
    "CO": (-109.060, 36.992, -102.042, 41.003),
    "CT": (-73.728, 40.987, -71.787, 42.050),
    "DE": (-75.789, 38.451, -75.049, 39.839),
    "FL": (-87.635, 24.523, -80.031, 31.001),
    "GA": (-85.605, 30.357, -80.841, 35.001),
    "HI": (-160.074, 18.948, -154.807, 22.235),
    "ID": (-117.243, 41.988, -111.044, 49.001),
    "IL": (-91.513, 36.970, -87.020, 42.508),
    "IN": (-88.097, 37.772, -84.785, 41.761),
    "IA": (-96.639, 40.375, -90.140, 43.501),
    "KS": (-102.052, 36.993, -94.588, 40.003),
    "KY": (-89.571, 36.497, -81.965, 39.147),
    "LA": (-94.043, 28.928, -88.817, 33.020),
    "ME": (-71.084, 43.064, -66.950, 47.460),
    "MD": (-79.487, 37.912, -75.049, 39.723),
    "MA": (-73.508, 41.238, -69.928, 42.887),
    "MI": (-90.418, 41.696, -82.122, 48.189),
    "MN": (-97.239, 43.499, -89.489, 49.384),
    "MS": (-91.655, 30.174, -88.098, 35.001),
    "MO": (-95.774, 35.995, -89.099, 40.613),
    "MT": (-116.050, 44.358, -104.040, 49.001),
    "NE": (-104.053, 40.000, -95.308, 43.001),
    "NV": (-120.006, 35.002, -114.040, 42.002),
    "NH": (-72.557, 42.697, -70.703, 45.305),
    "NJ": (-75.559, 38.928, -73.894, 41.357),
    "NM": (-109.050, 31.332, -103.002, 37.000),
    "NY": (-79.762, 40.496, -71.856, 45.016),
    "NC": (-84.322, 33.845, -75.460, 36.588),
    "ND": (-104.049, 45.935, -96.554, 49.001),
    "OH": (-84.820, 38.403, -80.519, 42.327),
    "OK": (-103.002, 33.616, -94.431, 37.002),
    "OR": (-124.567, 41.992, -116.463, 46.292),
    "PA": (-80.519, 39.720, -74.690, 42.269),
    "RI": (-71.862, 41.146, -71.121, 42.019),
    "SC": (-83.354, 32.035, -78.541, 35.215),
    "SD": (-104.058, 42.480, -96.437, 45.945),
    "TN": (-90.310, 34.983, -81.647, 36.678),
    "TX": (-106.646, 25.837, -93.508, 36.501),
    "UT": (-114.053, 36.998, -109.042, 42.001),
    "VT": (-73.438, 42.727, -71.465, 45.017),
    "VA": (-83.675, 36.541, -75.242, 39.466),
    "WA": (-124.849, 45.544, -116.916, 49.002),
    "WV": (-82.644, 37.202, -77.719, 40.638),
    "WI": (-92.889, 42.492, -86.250, 47.080),
    "WY": (-111.056, 40.995, -104.052, 45.005)
}

# Cowardin classification codes for wetland types
COWARDIN_CODES = {
    "E": "Estuarine",
    "L": "Lacustrine (Lakes)",
    "M": "Marine",
    "P": "Palustrine (Freshwater)",
    "R": "Riverine",
    "E1": "Estuarine Subtidal",
    "E2": "Estuarine Intertidal",
    "L1": "Lacustrine Limnetic (deep water)",
    "L2": "Lacustrine Littoral (shallow)",
    "PAB": "Palustrine Aquatic Bed",
    "PEM": "Palustrine Emergent (marshes)",
    "PFO": "Palustrine Forested",
    "PSS": "Palustrine Scrub-Shrub",
    "PUB": "Palustrine Unconsolidated Bottom (ponds)",
    "R1": "Riverine Upper Perennial",
    "R2": "Riverine Lower Perennial",
    "R3": "Riverine Upper Intermittent",
    "R4": "Riverine Intermittent",
    "R5": "Riverine Unknown"
}


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories"""
    for dir_path in [RAW_DIR, GEOJSON_DIR, PMTILES_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def download_via_api(state_abbrev, bbox=None, max_records=None):
    """
    Download NWI wetlands data via ArcGIS REST API

    Args:
        state_abbrev: 2-letter state code
        bbox: Optional bounding box (xmin, ymin, xmax, ymax) in WGS84
        max_records: Optional limit on number of records (default: 50000 per state for performance)
    """
    import ssl

    # SSL context for certificate issues
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    base_url = f"{NWI_FEATURE_SERVICE}/{NWI_LAYER_ID}/query"

    state_upper = state_abbrev.upper()
    output_file = GEOJSON_DIR / f"nwi_{state_upper.lower()}.geojson"

    # Use state bbox if not provided
    if bbox is None:
        bbox = STATE_BBOX.get(state_upper)
        if bbox is None:
            log(f"  No bounding box available for state: {state_upper}", "ERROR")
            return None

    log(f"Downloading NWI wetlands for: {state_upper}")
    log(f"  Using bbox: {bbox}")

    # Default max records per state to avoid massive downloads
    if max_records is None:
        max_records = 100000  # 100k features max per state

    all_features = []
    batch_size = 100  # NWI API only reliably supports ~100 features per request

    # For large states, we need to subdivide the bbox into smaller cells
    # This uses a grid approach to paginate by geography
    xmin, ymin, xmax, ymax = bbox
    cell_size = 0.5  # 0.5 degree cells

    x = xmin
    total_cells = 0
    max_cells = 200  # Limit total API calls

    while x < xmax and total_cells < max_cells:
        y = ymin
        while y < ymax and total_cells < max_cells:
            cell_bbox = f"{x},{y},{min(x + cell_size, xmax)},{min(y + cell_size, ymax)}"
            total_cells += 1

            params = {
                "where": "1=1",
                "geometry": cell_bbox,
                "geometryType": "esriGeometryEnvelope",
                "spatialRel": "esriSpatialRelIntersects",
                "inSR": "4326",
                "outFields": "*",
                "f": "geojson",
                "returnGeometry": "true",
                "outSR": "4326",
                "resultRecordCount": str(batch_size)
            }

            query_string = urllib.parse.urlencode(params)
            url = f"{base_url}?{query_string}"

            try:
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

                with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                    data = json.loads(response.read().decode('utf-8'))

                    if 'error' in data:
                        # Skip this cell but continue
                        pass
                    else:
                        features = data.get('features', [])
                        if features:
                            all_features.extend(features)

                    # Check max records
                    if len(all_features) >= max_records:
                        log(f"  Reached max records limit: {max_records}")
                        break

            except Exception as e:
                # Skip failed cells
                pass

            y += cell_size

        if len(all_features) >= max_records:
            break
        x += cell_size

    log(f"  Queried {total_cells} grid cells, found {len(all_features)} features")

    if all_features:
        # Add wetland type descriptions
        for feature in all_features:
            props = feature.get('properties', {})
            wetland_type = props.get('WETLAND_TYPE', '')
            if wetland_type:
                # Parse Cowardin code
                system = wetland_type[0] if wetland_type else ''
                props['wetland_system'] = COWARDIN_CODES.get(system, 'Unknown')
                props['wetland_class'] = COWARDIN_CODES.get(wetland_type[:3], wetland_type)

        geojson = {
            "type": "FeatureCollection",
            "name": f"NWI Wetlands - {state_upper}",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": all_features,
            "metadata": {
                "source": "US Fish & Wildlife Service - National Wetlands Inventory",
                "download_date": datetime.now().isoformat(),
                "state": state_upper,
                "feature_count": len(all_features),
                "api_url": NWI_FEATURE_SERVICE
            }
        }

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(all_features)} wetlands to {output_file}")
        return str(output_file)

    log(f"  No wetlands found for {state_upper}", "WARNING")
    return None


def download_state_zip(state_abbrev):
    """
    Download pre-packaged state wetlands data from FWS

    This is faster than API for full state coverage but files are larger.
    """
    state_upper = state_abbrev.upper()
    fips = STATE_FIPS.get(state_upper)

    if not fips:
        log(f"Unknown state: {state_upper}", "ERROR")
        return None

    # FWS state download URL pattern
    # Note: Actual URLs may vary - check FWS website for current links
    download_url = f"https://www.fws.gov/wetlands/downloads/State/{state_upper}_shapefile_wetlands.zip"

    zip_path = RAW_DIR / f"nwi_{state_upper.lower()}.zip"

    log(f"Downloading NWI state package: {state_upper}")

    try:
        req = urllib.request.Request(download_url)
        req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

        with urllib.request.urlopen(req, timeout=600) as response:
            with open(zip_path, 'wb') as f:
                total = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                block_size = 1024 * 1024

                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = (downloaded / total) * 100
                        print(f"\r  Progress: {downloaded / (1024*1024):.1f}MB / {total / (1024*1024):.1f}MB ({pct:.1f}%)", end="")

        print()
        log(f"  Downloaded: {zip_path}")

        # Extract
        with zipfile.ZipFile(zip_path, 'r') as zf:
            extract_dir = RAW_DIR / f"nwi_{state_upper.lower()}"
            zf.extractall(extract_dir)
            log(f"  Extracted to: {extract_dir}")

        return str(extract_dir)

    except urllib.error.HTTPError as e:
        log(f"  State download not available via direct URL. Using API instead.", "WARNING")
        return download_via_api(state_upper)
    except Exception as e:
        log(f"  Download error: {e}. Using API instead.", "WARNING")
        return download_via_api(state_upper)


def convert_shapefile_to_geojson(shp_dir, output_path):
    """Convert shapefile to GeoJSON using ogr2ogr"""
    import subprocess
    import glob

    # Find shapefile
    shp_files = glob.glob(str(shp_dir) + "/**/*.shp", recursive=True)
    if not shp_files:
        log(f"  No shapefile found in {shp_dir}", "ERROR")
        return None

    shp_path = shp_files[0]
    log(f"  Converting: {shp_path}")

    cmd = [
        "ogr2ogr",
        "-f", "GeoJSON",
        "-t_srs", "EPSG:4326",
        str(output_path),
        str(shp_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            log(f"  Converted to: {output_path}")
            return str(output_path)
        else:
            log(f"  Conversion error: {result.stderr}", "ERROR")
            return None
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def generate_pmtiles(geojson_path, pmtiles_path):
    """Generate PMTiles from GeoJSON"""
    import subprocess

    log(f"Generating PMTiles: {geojson_path}")

    cmd = [
        "tippecanoe",
        "-z14",
        "-Z8",  # Min zoom for wetlands (don't need at very low zooms)
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "-l", "wetlands",
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
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return False


def upload_to_r2(local_path, r2_key):
    """Upload file to Cloudflare R2"""
    import boto3

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

        content_type = 'application/geo+json' if local_path.endswith('.geojson') else 'application/x-protobuf'

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
    """Remove local file/directory after upload"""
    import shutil
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        log(f"  Cleaned up: {path}")
    except Exception as e:
        log(f"  Cleanup error: {e}", "WARNING")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Download National Wetlands Inventory (NWI) data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download NWI for a specific state
  python3 download_nwi.py --state TX

  # Download multiple states
  python3 download_nwi.py --state TX,LA,FL

  # Download all states
  python3 download_nwi.py --all-states

  # Full pipeline with upload and cleanup
  python3 download_nwi.py --state TX --pmtiles --upload --cleanup

Wetland Types (Cowardin Classification):
  PEM - Palustrine Emergent (marshes) - great for waterfowl
  PFO - Palustrine Forested (swamps)
  PSS - Palustrine Scrub-Shrub
  PUB - Palustrine Unconsolidated Bottom (ponds)
  L1/L2 - Lakes (deep/shallow)
  R1-R5 - Rivers and streams
        """
    )

    parser.add_argument("--state", "-s", help="State abbreviation(s), comma-separated")
    parser.add_argument("--all-states", action="store_true", help="Download all states")
    parser.add_argument("--method", choices=["api", "zip"], default="api",
                        help="Download method: api (smaller, slower) or zip (larger, faster)")
    parser.add_argument("--pmtiles", action="store_true", help="Generate PMTiles")
    parser.add_argument("--upload", action="store_true", help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true", help="Remove local files after upload")
    parser.add_argument("--max-records", type=int, help="Limit records per state (for testing)")
    parser.add_argument("--list-types", action="store_true", help="List wetland type codes")

    args = parser.parse_args()

    ensure_directories()

    if args.list_types:
        log("Cowardin Wetland Classification Codes:")
        for code, desc in sorted(COWARDIN_CODES.items()):
            log(f"  {code}: {desc}")
        return

    states = []
    if args.state:
        states = [s.strip().upper() for s in args.state.split(",")]
    elif args.all_states:
        states = list(STATE_FIPS.keys())
    else:
        parser.print_help()
        return

    log(f"Processing {len(states)} states: {', '.join(states)}")

    for state in states:
        log("=" * 60)
        log(f"Processing NWI: {state}")
        log("=" * 60)

        # Download
        if args.method == "zip":
            result = download_state_zip(state)
            if result and os.path.isdir(result):
                # Convert shapefile to GeoJSON
                geojson_path = GEOJSON_DIR / f"nwi_{state.lower()}.geojson"
                result = convert_shapefile_to_geojson(result, geojson_path)
        else:
            result = download_via_api(state, max_records=args.max_records)

        if not result:
            log(f"  Failed to download NWI for {state}", "ERROR")
            continue

        geojson_path = result

        # Generate PMTiles
        if args.pmtiles:
            pmtiles_path = PMTILES_DIR / f"nwi_{state.lower()}.pmtiles"
            generate_pmtiles(geojson_path, pmtiles_path)

        # Upload
        if args.upload:
            r2_key = f"enrichment/nwi/nwi_{state.lower()}.geojson"
            upload_to_r2(geojson_path, r2_key)

            if args.pmtiles:
                pmtiles_path = PMTILES_DIR / f"nwi_{state.lower()}.pmtiles"
                if pmtiles_path.exists():
                    r2_key = f"enrichment/nwi/nwi_{state.lower()}.pmtiles"
                    upload_to_r2(str(pmtiles_path), r2_key)

        # Cleanup
        if args.cleanup and args.upload:
            cleanup_local(geojson_path)
            if args.pmtiles:
                pmtiles_path = PMTILES_DIR / f"nwi_{state.lower()}.pmtiles"
                if pmtiles_path.exists():
                    cleanup_local(str(pmtiles_path))

    log("=" * 60)
    log("NWI download complete!")
    log("=" * 60)


if __name__ == "__main__":
    main()
