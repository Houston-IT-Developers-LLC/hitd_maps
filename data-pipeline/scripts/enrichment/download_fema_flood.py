#!/usr/bin/env python3
"""
Download FEMA Flood Zone Data (NFHL)

Priority: 8
Source: FEMA National Flood Hazard Layer
URL: https://www.fema.gov/flood-maps

Flood zone data for:
- Identifying flood-prone areas
- Seasonal flooding awareness for hunters/campers
- Property risk assessment

Update Frequency: Continuous
Current Version: 2024
Date Added: 2026-01-13

API Notes:
- Uses DFIRM_ID prefix filtering (state FIPS code) instead of bbox geometry
- maxAllowableOffset used for geometry simplification to avoid timeouts
- Pagination supported with 2000 records max per request
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import time
from pathlib import Path
from datetime import datetime

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# FEMA NFHL Service - CORRECT URL
# Note: https://hazards.fema.gov/gis/nfhl/... is INVALID (returns 404)
# The correct endpoint is /arcgis/rest/services/public/NFHL/MapServer
FEMA_NFHL_SERVICE = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer"
FLOOD_HAZARD_LAYER = 28  # Flood Hazard Zones (S_FLD_HAZ_AR)

# State FIPS codes for DFIRM_ID filtering
# DFIRM_ID format: SSCCC[C] where SS = state FIPS, CCC[C] = county FIPS
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
}

# State bounding boxes (approximate) - for reference/metadata only
STATE_BBOXES = {
    "TX": (-106.65, 25.84, -93.51, 36.50),
    "CO": (-109.06, 36.99, -102.04, 41.00),
    "CA": (-124.41, 32.53, -114.13, 42.01),
    "FL": (-87.63, 24.52, -80.03, 31.00),
    "AZ": (-114.82, 31.33, -109.04, 37.00),
    "NM": (-109.05, 31.33, -103.00, 37.00),
    "OK": (-103.00, 33.62, -94.43, 37.00),
    "KS": (-102.05, 36.99, -94.59, 40.00),
    "NE": (-104.05, 40.00, -95.31, 43.00),
    "SD": (-104.06, 42.48, -96.44, 45.94),
    "ND": (-104.05, 45.93, -96.55, 49.00),
    "MT": (-116.05, 44.36, -104.04, 49.00),
    "WY": (-111.06, 40.99, -104.05, 45.01),
    "UT": (-114.05, 37.00, -109.04, 42.00),
    "NV": (-120.00, 35.00, -114.04, 42.00),
    "ID": (-117.24, 41.99, -111.04, 49.00),
    "WA": (-124.76, 45.54, -116.92, 49.00),
    "OR": (-124.57, 41.99, -116.46, 46.29),
    "LA": (-94.04, 28.93, -88.82, 33.02),
    "AR": (-94.62, 33.00, -89.64, 36.50),
    "MO": (-95.77, 35.99, -89.10, 40.61),
    "IA": (-96.64, 40.38, -90.14, 43.50),
    "MN": (-97.24, 43.50, -89.49, 49.38),
    "WI": (-92.89, 42.49, -86.25, 47.08),
    "IL": (-91.51, 36.97, -87.02, 42.51),
    "MI": (-90.42, 41.70, -82.12, 48.19),
    "IN": (-88.10, 37.77, -84.78, 41.76),
    "OH": (-84.82, 38.40, -80.52, 42.33),
    "KY": (-89.57, 36.50, -81.96, 39.15),
    "TN": (-90.31, 34.98, -81.65, 36.68),
    "MS": (-91.66, 30.17, -88.10, 35.00),
    "AL": (-88.47, 30.22, -84.89, 35.01),
    "GA": (-85.61, 30.36, -80.84, 35.00),
    "SC": (-83.35, 32.03, -78.54, 35.22),
    "NC": (-84.32, 33.84, -75.46, 36.59),
    "VA": (-83.68, 36.54, -75.24, 39.47),
    "WV": (-82.64, 37.20, -77.72, 40.64),
    "PA": (-80.52, 39.72, -74.69, 42.27),
    "NY": (-79.76, 40.50, -71.86, 45.02),
    "VT": (-73.44, 42.73, -71.46, 45.02),
    "NH": (-72.56, 42.70, -70.70, 45.31),
    "ME": (-71.08, 43.06, -66.95, 47.46),
    "MA": (-73.51, 41.24, -69.93, 42.89),
    "RI": (-71.86, 41.15, -71.12, 42.02),
    "CT": (-73.73, 40.98, -71.79, 42.05),
    "NJ": (-75.56, 38.93, -73.89, 41.36),
    "DE": (-75.79, 38.45, -75.05, 39.84),
    "MD": (-79.49, 37.91, -75.05, 39.72),
}

# Flood Zone Definitions
FLOOD_ZONES = {
    "A": {"risk": "high", "desc": "100-year flood zone, no BFE determined"},
    "AE": {"risk": "high", "desc": "100-year flood zone with Base Flood Elevation"},
    "AH": {"risk": "high", "desc": "100-year flood zone, shallow flooding (ponding)"},
    "AO": {"risk": "high", "desc": "100-year flood zone, shallow flooding (sheet flow)"},
    "A99": {"risk": "high", "desc": "100-year flood zone, protected by levee under construction"},
    "AR": {"risk": "high", "desc": "100-year flood zone, temporarily increased risk"},
    "V": {"risk": "high", "desc": "100-year coastal flood zone with velocity hazard"},
    "VE": {"risk": "high", "desc": "100-year coastal flood zone with BFE and velocity"},
    "X": {"risk": "minimal", "desc": "Minimal flood risk (outside 500-year floodplain)"},
    "X500": {"risk": "moderate", "desc": "500-year flood zone (0.2% annual chance)"},
    "AREA NOT INCLUDED": {"risk": "unknown", "desc": "Area not mapped"},
    "D": {"risk": "undetermined", "desc": "Undetermined but possible flood hazard"},
    "OPEN WATER": {"risk": "n/a", "desc": "Open water body"}
}


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories"""
    for dir_path in [GEOJSON_DIR, PMTILES_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def download_by_state_fips(state_fips, max_features=500000, batch_size=2000, retries=3, simplify=0.0001):
    """
    Download flood zone features for a state using DFIRM_ID prefix filtering.

    This approach is much faster and more reliable than bbox geometry queries
    because DFIRM_ID is indexed and doesn't require spatial operations.

    Args:
        state_fips: 2-digit state FIPS code (e.g., "48" for Texas)
        max_features: Maximum features to download (default 500k)
        batch_size: Records per request (max 2000 per API limit)
        retries: Number of retry attempts per batch
        simplify: Geometry simplification tolerance (maxAllowableOffset)

    Returns:
        List of GeoJSON features or None on failure
    """
    base_url = f"{FEMA_NFHL_SERVICE}/{FLOOD_HAZARD_LAYER}/query"

    all_features = []
    offset = 0
    consecutive_failures = 0
    max_consecutive_failures = 5

    # Use DFIRM_ID LIKE 'SS%' to get all records for a state
    # DFIRM_ID format: SSCCC[C] where SS=state FIPS, CCC[C]=county
    where_clause = f"DFIRM_ID LIKE '{state_fips}%'"

    while True:
        success = False

        for attempt in range(retries):
            try:
                params = {
                    "where": where_clause,
                    "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE,DFIRM_ID",
                    "f": "geojson",
                    "returnGeometry": "true",
                    "outSR": "4326",
                    "resultOffset": offset,
                    "resultRecordCount": batch_size,
                }

                # Add geometry simplification for large datasets
                if simplify > 0:
                    params["maxAllowableOffset"] = simplify

                query_string = urllib.parse.urlencode(params)
                url = f"{base_url}?{query_string}"

                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

                with urllib.request.urlopen(req, timeout=180) as response:
                    data = json.loads(response.read().decode('utf-8'))

                    if 'error' in data:
                        raise Exception(f"API Error: {data['error']}")

                    features = data.get('features', [])

                    if not features:
                        # No more features
                        return all_features

                    all_features.extend(features)
                    success = True
                    consecutive_failures = 0

                    log(f"    Batch {offset//batch_size + 1}: got {len(features)} features (total: {len(all_features)})")

                    if len(features) < batch_size:
                        # Last batch
                        return all_features

                    if len(all_features) >= max_features:
                        log(f"    Reached max features limit ({max_features})")
                        return all_features

                    break  # Success, exit retry loop

            except (urllib.error.HTTPError, urllib.error.URLError, Exception) as e:
                if attempt < retries - 1:
                    wait_time = (attempt + 1) * 10
                    log(f"    Retry {attempt + 1}/{retries} after {wait_time}s: {e}", "WARNING")
                    time.sleep(wait_time)
                else:
                    log(f"    Failed batch at offset {offset}: {e}", "ERROR")
                    consecutive_failures += 1

        if not success:
            if consecutive_failures >= max_consecutive_failures:
                log(f"    Too many consecutive failures, stopping", "ERROR")
                break
            # Skip this batch and continue
            log(f"    Skipping batch at offset {offset}", "WARNING")

        offset += batch_size

        # Rate limiting - be nice to the API
        time.sleep(0.5)

    return all_features if all_features else None


def download_flood_zones(state_abbrev=None, bbox=None, simplify=0.0001, high_risk_only=False):
    """
    Download FEMA flood zone data for a state.

    Uses DFIRM_ID-based filtering which is faster and more reliable than
    bbox geometry queries that often timeout on the FEMA server.

    Args:
        state_abbrev: 2-letter state code (or comma-separated list)
        bbox: Not used (kept for backward compatibility)
        simplify: Geometry simplification tolerance (default 0.0001 degrees ~11m)
        high_risk_only: Only download high-risk zones (A, AE, V, VE, etc.)

    Returns:
        Path to output GeoJSON file, or list of paths for multiple states
    """
    # Handle multiple states
    if state_abbrev and ',' in state_abbrev:
        states = [s.strip().upper() for s in state_abbrev.split(',')]
        results = []
        for state in states:
            result = download_flood_zones(state_abbrev=state, simplify=simplify, high_risk_only=high_risk_only)
            if result:
                results.append(result)
        return results

    state_upper = state_abbrev.upper() if state_abbrev else None

    if not state_upper:
        log("Please provide a state abbreviation with --state", "ERROR")
        return None

    if state_upper not in STATE_FIPS:
        log(f"Unknown state: {state_upper}. Valid states: {', '.join(sorted(STATE_FIPS.keys()))}", "ERROR")
        return None

    state_fips = STATE_FIPS[state_upper]
    output_file = GEOJSON_DIR / f"fema_flood_{state_upper.lower()}.geojson"

    log(f"Downloading FEMA Flood Zones for {state_upper} (FIPS: {state_fips})")
    log(f"  Using DFIRM_ID filtering (faster than bbox queries)")
    log(f"  Geometry simplification: {simplify} degrees (~{simplify * 111000:.0f}m)")

    # Download features
    all_features = download_by_state_fips(state_fips, simplify=simplify)

    if not all_features:
        log("  No features downloaded", "WARNING")
        return None

    log(f"  Downloaded {len(all_features)} total features")

    # Deduplicate features by GFID or geometry hash
    seen = set()
    unique_features = []
    for feature in all_features:
        props = feature.get('properties', {})
        # Try to use a unique identifier first
        gfid = props.get('GFID') or props.get('FLD_AR_ID')
        if gfid:
            if gfid not in seen:
                seen.add(gfid)
                unique_features.append(feature)
        else:
            # Fall back to geometry hash
            geom = feature.get('geometry')
            if geom:
                geom_str = json.dumps(geom, sort_keys=True)
                geom_hash = hash(geom_str)
                if geom_hash not in seen:
                    seen.add(geom_hash)
                    unique_features.append(feature)

    if len(unique_features) < len(all_features):
        log(f"  Deduplicated: {len(all_features)} -> {len(unique_features)} features")
    all_features = unique_features

    # Filter high-risk only if requested
    if high_risk_only:
        high_risk_zones = {'A', 'AE', 'AH', 'AO', 'A99', 'AR', 'V', 'VE'}
        filtered = [f for f in all_features if f.get('properties', {}).get('FLD_ZONE', '') in high_risk_zones]
        log(f"  Filtered to high-risk only: {len(all_features)} -> {len(filtered)} features")
        all_features = filtered

    # Add flood zone descriptions and risk levels
    for feature in all_features:
        props = feature.get('properties', {})
        fld_zone = props.get('FLD_ZONE', '')
        zone_info = FLOOD_ZONES.get(fld_zone, {"risk": "unknown", "desc": fld_zone})
        props['flood_risk'] = zone_info['risk']
        props['flood_description'] = zone_info['desc']
        props['in_100yr_floodplain'] = zone_info['risk'] == 'high'
        props['in_500yr_floodplain'] = zone_info['risk'] in ['high', 'moderate']

    # Build GeoJSON output
    bbox = STATE_BBOXES.get(state_upper)
    geojson = {
        "type": "FeatureCollection",
        "name": f"FEMA Flood Zones - {state_upper}",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": all_features,
        "metadata": {
            "source": "FEMA National Flood Hazard Layer",
            "layer": f"Layer {FLOOD_HAZARD_LAYER} (S_FLD_HAZ_AR)",
            "download_date": datetime.now().isoformat(),
            "state": state_upper,
            "state_fips": state_fips,
            "bbox": list(bbox) if bbox else None,
            "feature_count": len(all_features),
            "geometry_simplification": simplify,
            "api_url": FEMA_NFHL_SERVICE
        }
    }

    with open(output_file, 'w') as f:
        json.dump(geojson, f)

    file_size = os.path.getsize(output_file)
    log(f"  Saved {len(all_features)} features to {output_file}")
    log(f"  File size: {file_size / (1024*1024):.2f} MB")
    return str(output_file)


def generate_pmtiles(geojson_path, pmtiles_path):
    """Generate PMTiles from GeoJSON"""
    import subprocess

    log(f"Generating PMTiles: {geojson_path}")

    cmd = [
        "tippecanoe",
        "-z14",
        "-Z8",
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "-l", "flood_zones",
        "-o", str(pmtiles_path),
        "--force",
        str(geojson_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if result.returncode == 0:
            pmtiles_size = os.path.getsize(pmtiles_path)
            log(f"  Generated: {pmtiles_path} ({pmtiles_size / (1024*1024):.2f} MB)")
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
        description="Download FEMA Flood Zone Data (NFHL)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download flood zones by state (uses DFIRM_ID filtering - fast!)
  python3 download_fema_flood.py --state TX

  # Download multiple states
  python3 download_fema_flood.py --state TX,CO,MT,ID,WI

  # Full pipeline with PMTiles and R2 upload
  python3 download_fema_flood.py --state TX --pmtiles --upload --cleanup

  # Download only high-risk flood zones (faster, smaller files)
  python3 download_fema_flood.py --state TX --high-risk-only --pmtiles

  # Use less geometry simplification for more detail
  python3 download_fema_flood.py --state CO --simplify 0.00001 --pmtiles

Flood Zone Codes:
  A, AE, AH, AO - 100-year flood zone (high risk)
  V, VE - Coastal flood zone with wave action (high risk)
  X500 - 500-year flood zone (moderate risk)
  X - Minimal flood risk
  D - Undetermined risk

Notes:
  - Uses DFIRM_ID prefix filtering (much faster than bbox queries)
  - DFIRM_ID starts with 2-digit state FIPS code
  - Default geometry simplification ~11m for reasonable file sizes
  - Large states (TX, CA) may have 100k+ features
        """
    )

    parser.add_argument("--state", "-s", help="State abbreviation(s), comma-separated (e.g., TX,CO,MT)")
    parser.add_argument("--simplify", type=float, default=0.0001,
                        help="Geometry simplification in degrees (default: 0.0001 ~11m)")
    parser.add_argument("--high-risk-only", action="store_true",
                        help="Only download high-risk zones (A, AE, V, VE, etc.)")
    parser.add_argument("--pmtiles", action="store_true", help="Generate PMTiles")
    parser.add_argument("--upload", action="store_true", help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true", help="Remove local files after upload")
    parser.add_argument("--list-zones", action="store_true", help="List flood zone codes")
    parser.add_argument("--list-states", action="store_true", help="List supported states with FIPS codes")

    args = parser.parse_args()

    ensure_directories()

    if args.list_zones:
        log("FEMA Flood Zone Codes:")
        for zone, info in sorted(FLOOD_ZONES.items()):
            log(f"  {zone}: [{info['risk']}] {info['desc']}")
        return

    if args.list_states:
        log("Supported states with FIPS codes:")
        for state in sorted(STATE_FIPS.keys()):
            log(f"  {state} (FIPS: {STATE_FIPS[state]})")
        return

    if not args.state:
        log("Please provide --state", "ERROR")
        parser.print_help()
        return

    log("=" * 60)
    log("FEMA Flood Zone Download")
    log("=" * 60)
    log(f"API: {FEMA_NFHL_SERVICE}")
    log(f"Layer: {FLOOD_HAZARD_LAYER} (S_FLD_HAZ_AR)")
    log("=" * 60)

    # Download
    result = download_flood_zones(
        state_abbrev=args.state,
        simplify=args.simplify,
        high_risk_only=args.high_risk_only
    )

    if not result:
        log("Download failed", "ERROR")
        return

    # Handle multiple results (list) or single result (string)
    if isinstance(result, list):
        files_to_process = result
    else:
        files_to_process = [result]

    all_files = []

    for geojson_file in files_to_process:
        all_files.append(geojson_file)

        # Generate PMTiles
        if args.pmtiles:
            pmtiles_name = Path(geojson_file).stem + ".pmtiles"
            pmtiles_path = PMTILES_DIR / pmtiles_name
            if generate_pmtiles(geojson_file, pmtiles_path):
                all_files.append(str(pmtiles_path))

    # Upload
    if args.upload:
        for file_path in all_files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                r2_key = f"enrichment/fema/{filename}"
                upload_to_r2(file_path, r2_key)

    # Cleanup
    if args.cleanup and args.upload:
        for file_path in all_files:
            if os.path.exists(file_path):
                cleanup_local(file_path)

    log("=" * 60)
    log("FEMA flood zones download complete!")
    log("=" * 60)


if __name__ == "__main__":
    main()
