#!/usr/bin/env python3
"""
Download Federal Lands Data (BLM, USFS, NPS, FWS)

Priority: 7
Sources:
  - BLM Surface Management Agency: https://www.blm.gov/services/geospatial/GISData
  - USDA Forest Service: https://data.fs.usda.gov/geodata/

Federal lands data for:
- BLM land boundaries
- National Forest boundaries
- Wilderness areas
- Recreation areas

Update Frequency: Quarterly (BLM), Annual (USFS)
Date Added: 2026-01-13

Note: PAD-US (Priority 1) includes most federal lands.
Use this for BLM/USFS-specific attributes not in PAD-US.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from datetime import datetime

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# BLM Surface Management Agency Service
# Layer 1 = Surface Management Agency (all federal lands)
BLM_SMA_SERVICE = "https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer"
BLM_SMA_LAYER = 1

# USFS Administrative Boundaries
USFS_SERVICE = "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_ForestSystemBoundaries_01/MapServer"
USFS_ADMIN_LAYER = 0

# Wilderness Areas (from USFS EDW - updated service URL)
WILDERNESS_SERVICE = "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Wilderness_01/MapServer"
WILDERNESS_LAYER = 0

# State bounding boxes (xmin, ymin, xmax, ymax) in WGS84
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

# Agency codes
AGENCY_CODES = {
    "BLM": "Bureau of Land Management",
    "FS": "Forest Service",
    "FWS": "Fish and Wildlife Service",
    "NPS": "National Park Service",
    "DOD": "Department of Defense",
    "BOR": "Bureau of Reclamation",
    "TVA": "Tennessee Valley Authority",
    "DOE": "Department of Energy",
    "OTHER": "Other Federal"
}

# States with significant federal lands (western focus)
FEDERAL_LAND_STATES = [
    "AK", "AZ", "CA", "CO", "ID", "MT", "NV", "NM", "OR", "UT", "WA", "WY"
]


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories"""
    for dir_path in [GEOJSON_DIR, PMTILES_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def query_arcgis_service(base_url, params, timeout=300, retries=3):
    """
    Query an ArcGIS REST service with proper URL encoding.
    Returns JSON response or None on error.
    """
    # Use urlencode which handles special characters properly
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
        except urllib.error.HTTPError as e:
            if e.code == 500 and attempt < retries - 1:
                log(f"  HTTP 500 - retry {attempt + 1}/{retries}...", "WARNING")
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            log(f"  HTTP Error {e.code}: {e.reason}", "ERROR")
            return None
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                log(f"  URL Error - retry {attempt + 1}/{retries}...", "WARNING")
                import time
                time.sleep(2 ** attempt)
                continue
            log(f"  URL Error: {e.reason}", "ERROR")
            return None
        except Exception as e:
            log(f"  Error: {e}", "ERROR")
            return None
    return None


def download_blm_sma(state_abbrev=None, bbox=None):
    """
    Download BLM Surface Management Agency data

    Returns federal land polygons with agency, unit name, and acreage.
    Uses tiled bbox queries for large states to avoid server timeouts.
    """
    state_upper = state_abbrev.upper() if state_abbrev else None
    output_file = GEOJSON_DIR / f"blm_sma_{state_upper.lower() if state_upper else 'national'}.geojson"

    log(f"Downloading BLM SMA" + (f" for {state_upper}" if state_upper else " (national)"))

    # First check if state has any BLM data
    base_url = f"{BLM_SMA_SERVICE}/{BLM_SMA_LAYER}/query"

    count_params = {
        "where": f"ADMIN_ST='{state_upper}'" if state_upper else "1=1",
        "returnCountOnly": "true",
        "f": "json"
    }
    count_result = query_arcgis_service(base_url, count_params, timeout=60)

    if count_result and count_result.get('count', 0) == 0:
        log(f"  No BLM data for {state_upper} (0 features)")
        return None

    feature_count = count_result.get('count', 0) if count_result else 'unknown'
    log(f"  Found {feature_count} BLM features for {state_upper}")

    all_features = []

    # Get state bbox for tiled queries
    state_bbox = bbox or (STATE_BBOX.get(state_upper) if state_upper else None)

    if state_bbox:
        # Divide state into tiles for large queries to avoid timeouts
        # Large western states need smaller tiles
        xmin, ymin, xmax, ymax = state_bbox
        width = xmax - xmin
        height = ymax - ymin

        # Adaptive tile size based on expected feature density
        # Western states with lots of federal land need smaller tiles
        high_density_states = ["AZ", "NV", "UT", "NM", "WY", "MT", "ID", "CO", "OR", "CA", "AK"]
        if state_upper in high_density_states:
            tile_size = 1.0  # 1 degree tiles for dense states
        else:
            tile_size = 2.0  # Larger tiles for sparse states

        tiles = []
        y = ymin
        while y < ymax:
            x = xmin
            while x < xmax:
                tiles.append((x, y, min(x + tile_size, xmax), min(y + tile_size, ymax)))
                x += tile_size
            y += tile_size

        log(f"  Querying in {len(tiles)} tiles...")

        for tile_idx, tile in enumerate(tiles):
            tile_features = download_blm_tile(base_url, state_upper, tile)
            if tile_features:
                all_features.extend(tile_features)
            if (tile_idx + 1) % 10 == 0 or tile_idx == len(tiles) - 1:
                log(f"  Tile {tile_idx + 1}/{len(tiles)}: {len(all_features)} total features")
    else:
        # Non-tiled query for national or unknown states
        offset = 0
        batch_size = 1000

        while True:
            params = {
                "where": f"ADMIN_ST='{state_upper}'" if state_upper else "1=1",
                "outFields": "ADMIN_AGENCY_CODE,ADMIN_UNIT_NAME,SHAPE_Area,ADMIN_ST",
                "f": "geojson",
                "returnGeometry": "true",
                "outSR": "4326",
                "resultOffset": offset,
                "resultRecordCount": batch_size
            }

            data = query_arcgis_service(base_url, params)

            if data is None or 'error' in data:
                break
            if 'features' not in data or len(data['features']) == 0:
                break

            all_features.extend(data['features'])
            log(f"  Fetched {len(data['features'])} features (total: {len(all_features)})")

            if len(data['features']) < batch_size:
                break
            offset += batch_size

    if all_features:
        # Deduplicate features by geometry (tiles may overlap at edges)
        seen_ids = set()
        unique_features = []
        for feature in all_features:
            # Use a combination of properties as ID since OBJECTID isn't always returned
            props = feature.get('properties', {})
            feature_id = f"{props.get('ADMIN_UNIT_NAME', '')}_{props.get('ADMIN_AGENCY_CODE', '')}_{hash(str(feature.get('geometry', {}).get('coordinates', [])[:2]))}"
            if feature_id not in seen_ids:
                seen_ids.add(feature_id)
                # Add agency name descriptions
                agency_code = props.get('ADMIN_AGENCY_CODE', '')
                props['agency_name'] = AGENCY_CODES.get(agency_code, agency_code)
                unique_features.append(feature)

        all_features = unique_features
        log(f"  After dedup: {len(all_features)} unique features")

        geojson = {
            "type": "FeatureCollection",
            "name": f"BLM SMA" + (f" - {state_upper}" if state_upper else ""),
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": all_features,
            "metadata": {
                "source": "Bureau of Land Management - Surface Management Agency",
                "download_date": datetime.now().isoformat(),
                "state": state_upper,
                "feature_count": len(all_features),
                "api_url": BLM_SMA_SERVICE
            }
        }

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(all_features)} features to {output_file}")
        return str(output_file)

    return None


def download_blm_tile(base_url, state_upper, bbox):
    """Download BLM features for a single tile/bbox"""
    all_features = []
    offset = 0
    batch_size = 500  # Smaller batches for tiled queries

    while True:
        params = {
            "where": f"ADMIN_ST='{state_upper}'" if state_upper else "1=1",
            "outFields": "ADMIN_AGENCY_CODE,ADMIN_UNIT_NAME,SHAPE_Area,ADMIN_ST",
            "f": "geojson",
            "returnGeometry": "true",
            "outSR": "4326",
            "geometry": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "inSR": "4326",
            "resultOffset": offset,
            "resultRecordCount": batch_size
        }

        data = query_arcgis_service(base_url, params, timeout=120)

        if data is None or 'error' in data:
            break
        if 'features' not in data or len(data['features']) == 0:
            break

        all_features.extend(data['features'])

        if len(data['features']) < batch_size:
            break
        offset += batch_size

    return all_features


def download_usfs_boundaries(state_abbrev=None):
    """
    Download USDA Forest Service administrative boundaries

    Returns National Forest and Grassland boundaries.
    """
    state_upper = state_abbrev.upper() if state_abbrev else None
    output_file = GEOJSON_DIR / f"usfs_boundaries_{state_upper.lower() if state_upper else 'national'}.geojson"

    log(f"Downloading USFS boundaries" + (f" for {state_upper}" if state_upper else " (national)"))

    base_url = f"{USFS_SERVICE}/{USFS_ADMIN_LAYER}/query"

    all_features = []
    offset = 0
    batch_size = 1000

    while True:
        # USFS doesn't have a state field, so we download all and filter by bbox
        params = {
            "where": "1=1",
            "outFields": "FORESTNAME,REGION,GIS_ACRES",
            "f": "geojson",
            "returnGeometry": "true",
            "outSR": "4326",
            "resultOffset": offset,
            "resultRecordCount": batch_size
        }

        # If state specified, use bbox to filter
        if state_upper and state_upper in STATE_BBOX:
            bbox = STATE_BBOX[state_upper]
            params["geometry"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"
            params["inSR"] = "4326"

        data = query_arcgis_service(base_url, params)
        
        if data is None:
            break
            
        if 'error' in data:
            log(f"  API Error: {data['error']}", "ERROR")
            break

        if 'features' not in data or len(data['features']) == 0:
            break

        all_features.extend(data['features'])
        log(f"  Fetched {len(data['features'])} features (total: {len(all_features)})")

        if len(data['features']) < batch_size:
            break

        offset += batch_size

    if all_features:
        geojson = {
            "type": "FeatureCollection",
            "name": f"USFS Boundaries" + (f" - {state_upper}" if state_upper else ""),
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": all_features,
            "metadata": {
                "source": "USDA Forest Service - Administrative Boundaries",
                "download_date": datetime.now().isoformat(),
                "state": state_upper,
                "feature_count": len(all_features),
                "api_url": USFS_SERVICE
            }
        }

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(all_features)} features to {output_file}")
        return str(output_file)

    return None


def download_wilderness_areas(state_abbrev=None):
    """
    Download designated Wilderness Areas

    Returns boundaries of federally designated wilderness.
    """
    state_upper = state_abbrev.upper() if state_abbrev else None
    output_file = GEOJSON_DIR / f"wilderness_{state_upper.lower() if state_upper else 'national'}.geojson"

    log(f"Downloading Wilderness Areas" + (f" for {state_upper}" if state_upper else " (national)"))

    base_url = f"{WILDERNESS_SERVICE}/{WILDERNESS_LAYER}/query"

    all_features = []
    offset = 0
    batch_size = 1000

    while True:
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "returnGeometry": "true",
            "outSR": "4326",
            "resultOffset": offset,
            "resultRecordCount": batch_size
        }

        # If state specified, use bbox to filter
        if state_upper and state_upper in STATE_BBOX:
            bbox = STATE_BBOX[state_upper]
            params["geometry"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"
            params["inSR"] = "4326"

        data = query_arcgis_service(base_url, params)
        
        if data is None:
            break
            
        if 'error' in data:
            log(f"  API Error: {data['error']}", "ERROR")
            break

        if 'features' not in data or len(data['features']) == 0:
            break

        all_features.extend(data['features'])
        log(f"  Fetched {len(data['features'])} features (total: {len(all_features)})")

        if len(data['features']) < batch_size:
            break

        offset += batch_size

    if all_features:
        geojson = {
            "type": "FeatureCollection",
            "name": f"Wilderness Areas" + (f" - {state_upper}" if state_upper else ""),
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": all_features,
            "metadata": {
                "source": "USDA Forest Service - Wilderness Areas",
                "download_date": datetime.now().isoformat(),
                "state": state_upper,
                "feature_count": len(all_features),
                "api_url": WILDERNESS_SERVICE
            }
        }

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(all_features)} features to {output_file}")
        return str(output_file)

    return None


def generate_pmtiles(geojson_path, pmtiles_path, layer_name="federal_lands"):
    """Generate PMTiles from GeoJSON"""
    import subprocess

    log(f"Generating PMTiles: {geojson_path}")

    cmd = [
        "tippecanoe",
        "-z14",
        "-Z4",
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "-l", layer_name,
        "-o", str(pmtiles_path),
        "--force",
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
    """Remove local file after upload"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            log(f"  Removed: {path}")
    except Exception as e:
        log(f"  Cleanup error: {e}", "WARNING")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Download Federal Lands Data (BLM, USFS)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download BLM data for western states
  python3 download_federal_lands.py --blm --state NV,UT,AZ

  # Download USFS boundaries
  python3 download_federal_lands.py --usfs --state CO,MT

  # Download wilderness areas
  python3 download_federal_lands.py --wilderness --state WY

  # Download all federal lands data
  python3 download_federal_lands.py --all --state CO --pmtiles --upload

Note: For comprehensive federal lands data, consider using
PAD-US (download_pad_us.py) which includes all federal lands.
        """
    )

    parser.add_argument("--state", "-s", help="State abbreviation(s), comma-separated")
    parser.add_argument("--blm", action="store_true", help="Download BLM SMA data")
    parser.add_argument("--usfs", action="store_true", help="Download USFS boundaries")
    parser.add_argument("--wilderness", action="store_true", help="Download Wilderness Areas")
    parser.add_argument("--all", action="store_true", help="Download all federal lands data")
    parser.add_argument("--pmtiles", action="store_true", help="Generate PMTiles")
    parser.add_argument("--upload", action="store_true", help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true", help="Remove local files after upload")

    args = parser.parse_args()

    ensure_directories()

    if not any([args.blm, args.usfs, args.wilderness, args.all]):
        parser.print_help()
        return

    states = []
    if args.state:
        states = [s.strip().upper() for s in args.state.split(",")]
    else:
        # Default to western states with significant federal lands
        states = FEDERAL_LAND_STATES

    log(f"Processing {len(states)} states: {', '.join(states)}")

    for state in states:
        log("=" * 60)
        log(f"Processing Federal Lands: {state}")
        log("=" * 60)

        files_to_upload = []

        # BLM Surface Management Agency
        if args.blm or args.all:
            result = download_blm_sma(state)
            if result:
                files_to_upload.append(result)

        # USFS Boundaries
        if args.usfs or args.all:
            result = download_usfs_boundaries(state)
            if result:
                files_to_upload.append(result)

        # Wilderness Areas
        if args.wilderness or args.all:
            result = download_wilderness_areas(state)
            if result:
                files_to_upload.append(result)

        # Generate PMTiles
        if args.pmtiles:
            for geojson_file in files_to_upload[:]:
                pmtiles_name = Path(geojson_file).stem + ".pmtiles"
                pmtiles_path = PMTILES_DIR / pmtiles_name
                layer_name = Path(geojson_file).stem.split('_')[0]  # blm, usfs, or wilderness
                if generate_pmtiles(geojson_file, pmtiles_path, layer_name):
                    files_to_upload.append(str(pmtiles_path))

        # Upload
        if args.upload:
            for file_path in files_to_upload:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    # Determine subfolder
                    if "blm" in filename.lower():
                        subfolder = "blm"
                    elif "usfs" in filename.lower():
                        subfolder = "usfs"
                    elif "wilderness" in filename.lower():
                        subfolder = "usfs"
                    else:
                        subfolder = "federal"
                    r2_key = f"enrichment/{subfolder}/{filename}"
                    upload_to_r2(file_path, r2_key)

        # Cleanup
        if args.cleanup and args.upload:
            for file_path in files_to_upload:
                if os.path.exists(file_path):
                    cleanup_local(file_path)

    log("=" * 60)
    log("Federal lands download complete!")
    log("=" * 60)


if __name__ == "__main__":
    main()
