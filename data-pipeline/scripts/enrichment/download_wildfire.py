#!/usr/bin/env python3
"""
Download NIFC Wildfire Perimeter Data

Priority: 5
Sources:
  - Historical fires: https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/InterAgencyFirePerimeterHistory_All_Years_View/FeatureServer/0
  - Current fires: https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_Current/FeatureServer/0

Wildfire perimeter data for:
- Recent burn areas (1-5 years old) with rapid regrowth = food sources for deer
- Current active fire locations for safety awareness
- Historical fire patterns for habitat analysis

Update Frequency: Daily (current), Annual (historical)
Date Added: 2026-01-13

Why this matters for hunters:
- Recent burn areas (1-5 years old) have rapid vegetation regrowth
- New vegetation = food sources that attract deer, elk, and other game
- Burn edges create excellent hunting transition zones
- Avoid active fire areas for safety
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

# NIFC ArcGIS Services
NIFC_HISTORICAL_SERVICE = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/InterAgencyFirePerimeterHistory_All_Years_View/FeatureServer/0"
NIFC_CURRENT_SERVICE = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_Current/FeatureServer/0"

# State bounding boxes for spatial filtering (approximate, in WGS84)
# Format: (xmin, ymin, xmax, ymax)
STATE_BBOXES = {
    "AL": (-88.5, 30.2, -84.9, 35.0),
    "AK": (-180.0, 51.2, -129.0, 71.5),
    "AZ": (-114.8, 31.3, -109.0, 37.0),
    "AR": (-94.6, 33.0, -89.6, 36.5),
    "CA": (-124.4, 32.5, -114.1, 42.0),
    "CO": (-109.1, 36.9, -102.0, 41.0),
    "CT": (-73.7, 40.9, -71.8, 42.1),
    "DE": (-75.8, 38.4, -75.0, 39.8),
    "FL": (-87.6, 24.5, -80.0, 31.0),
    "GA": (-85.6, 30.4, -80.8, 35.0),
    "HI": (-160.3, 18.9, -154.8, 22.2),
    "ID": (-117.2, 42.0, -111.0, 49.0),
    "IL": (-91.5, 36.9, -87.5, 42.5),
    "IN": (-88.1, 37.8, -84.8, 41.8),
    "IA": (-96.6, 40.4, -90.1, 43.5),
    "KS": (-102.1, 36.9, -94.6, 40.0),
    "KY": (-89.6, 36.5, -82.0, 39.1),
    "LA": (-94.0, 28.9, -88.8, 33.0),
    "ME": (-71.1, 43.0, -66.9, 47.5),
    "MD": (-79.5, 37.9, -75.0, 39.7),
    "MA": (-73.5, 41.2, -69.9, 42.9),
    "MI": (-90.4, 41.7, -82.4, 48.2),
    "MN": (-97.2, 43.5, -89.5, 49.4),
    "MS": (-91.7, 30.2, -88.1, 35.0),
    "MO": (-95.8, 36.0, -89.1, 40.6),
    "MT": (-116.1, 44.4, -104.0, 49.0),
    "NE": (-104.1, 40.0, -95.3, 43.0),
    "NV": (-120.0, 35.0, -114.0, 42.0),
    "NH": (-72.6, 42.7, -70.6, 45.3),
    "NJ": (-75.6, 38.9, -73.9, 41.4),
    "NM": (-109.1, 31.3, -103.0, 37.0),
    "NY": (-79.8, 40.5, -71.9, 45.0),
    "NC": (-84.3, 33.8, -75.5, 36.6),
    "ND": (-104.1, 45.9, -96.6, 49.0),
    "OH": (-84.8, 38.4, -80.5, 42.0),
    "OK": (-103.0, 33.6, -94.4, 37.0),
    "OR": (-124.6, 41.9, -116.5, 46.3),
    "PA": (-80.5, 39.7, -74.7, 42.3),
    "RI": (-71.9, 41.1, -71.1, 42.0),
    "SC": (-83.4, 32.0, -78.5, 35.2),
    "SD": (-104.1, 42.5, -96.4, 45.9),
    "TN": (-90.3, 35.0, -81.6, 36.7),
    "TX": (-106.6, 25.8, -93.5, 36.5),
    "UT": (-114.1, 37.0, -109.0, 42.0),
    "VT": (-73.4, 42.7, -71.5, 45.0),
    "VA": (-83.7, 36.5, -75.2, 39.5),
    "WA": (-124.8, 45.5, -116.9, 49.0),
    "WV": (-82.6, 37.2, -77.7, 40.6),
    "WI": (-92.9, 42.5, -86.8, 47.1),
    "WY": (-111.1, 40.9, -104.1, 45.0),
}

# State name to abbreviation mapping
STATE_ABBREV = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY"
}

# Reverse mapping: abbreviation to full state name
ABBREV_TO_STATE = {v: k for k, v in STATE_ABBREV.items()}

# Fire age categories for hunting relevance
FIRE_AGE_CATEGORIES = {
    0: {"category": "active", "hunting_value": "avoid", "desc": "Currently burning - avoid area"},
    1: {"category": "recent", "hunting_value": "low", "desc": "1 year old - early succession"},
    2: {"category": "prime", "hunting_value": "high", "desc": "2 years old - excellent browse"},
    3: {"category": "prime", "hunting_value": "high", "desc": "3 years old - peak regrowth"},
    4: {"category": "prime", "hunting_value": "medium", "desc": "4 years old - good browse"},
    5: {"category": "maturing", "hunting_value": "medium", "desc": "5 years old - transitional"},
}


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories"""
    for dir_path in [GEOJSON_DIR, PMTILES_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def download_historical_fires(state_abbrev=None, start_year=None, end_year=None):
    """
    Download historical wildfire perimeter data from NIFC.

    Args:
        state_abbrev: 2-letter state code (e.g., 'TX', 'CA')
        start_year: Start year for filtering (default: 5 years ago)
        end_year: End year for filtering (default: current year)

    Returns:
        Path to the output GeoJSON file, or None on failure

    Note: Historical data uses these fields:
        - FIRE_YEAR_INT: Fire year as integer
        - INCIDENT: Fire name
        - GIS_ACRES: Calculated acreage
        - AGENCY: Managing agency
        - DATE_CUR: Date current
    """
    current_year = datetime.now().year

    if start_year is None:
        start_year = current_year - 5
    if end_year is None:
        end_year = current_year

    state_upper = state_abbrev.upper() if state_abbrev else None

    output_suffix = state_upper.lower() if state_upper else "national"
    output_file = GEOJSON_DIR / f"wildfire_historical_{output_suffix}_{start_year}_{end_year}.geojson"

    log(f"Downloading Historical Wildfire Perimeters")
    log(f"  Years: {start_year} - {end_year}")
    if state_upper:
        log(f"  State: {state_upper}")

    base_url = f"{NIFC_HISTORICAL_SERVICE}/query"

    all_features = []
    offset = 0
    batch_size = 2000

    # Build WHERE clause using correct field name FIRE_YEAR_INT
    where_clause = f"FIRE_YEAR_INT >= {start_year} AND FIRE_YEAR_INT <= {end_year}"

    # Get state bounding box for spatial filtering
    bbox = STATE_BBOXES.get(state_upper) if state_upper else None

    while True:
        params = {
            "where": where_clause,
            "outFields": "FIRE_YEAR_INT,INCIDENT,GIS_ACRES,DATE_CUR,AGENCY,FEATURE_CA,MAP_METHOD",
            "f": "geojson",
            "returnGeometry": "true",
            "outSR": "4326",
            "resultOffset": offset,
            "resultRecordCount": batch_size
        }

        # Add spatial filter if state specified
        if bbox:
            params["geometry"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"
            params["inSR"] = "4326"

        query_string = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        url = f"{base_url}?{query_string}"

        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

            with urllib.request.urlopen(req, timeout=300) as response:
                data = json.loads(response.read().decode('utf-8'))

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

        except urllib.error.HTTPError as e:
            log(f"  HTTP Error {e.code}: {e.reason}", "ERROR")
            break
        except urllib.error.URLError as e:
            log(f"  URL Error: {e.reason}", "ERROR")
            break
        except Exception as e:
            log(f"  Error: {e}", "ERROR")
            break

    if all_features:
        # Enhance features with hunting-relevant metadata
        for feature in all_features:
            props = feature.get('properties', {})

            # Normalize field names for consistency
            fire_year = props.get('FIRE_YEAR_INT')
            if fire_year:
                props['FireYear'] = fire_year
                years_since_fire = current_year - fire_year
                age_info = FIRE_AGE_CATEGORIES.get(
                    min(years_since_fire, 5),
                    {"category": "old", "hunting_value": "low", "desc": "6+ years old - mature vegetation"}
                )
                props['years_since_fire'] = years_since_fire
                props['fire_age_category'] = age_info['category']
                props['hunting_value'] = age_info['hunting_value']
                props['fire_age_description'] = age_info['desc']

            # Normalize incident name
            props['IncidentName'] = props.get('INCIDENT', 'Unknown')

            # Format acres
            gis_acres = props.get('GIS_ACRES')
            if gis_acres:
                props['GISAcres'] = gis_acres
                props['acres_formatted'] = f"{gis_acres:,.0f}"

            # Add state (we filtered spatially, so we know it's in this state)
            if state_upper:
                props['StateName'] = ABBREV_TO_STATE.get(state_upper, state_upper)
                props['state_abbrev'] = state_upper

        geojson = {
            "type": "FeatureCollection",
            "name": f"NIFC Historical Wildfire Perimeters" + (f" - {state_upper}" if state_upper else ""),
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": all_features,
            "metadata": {
                "source": "National Interagency Fire Center (NIFC)",
                "download_date": datetime.now().isoformat(),
                "state": state_upper,
                "start_year": start_year,
                "end_year": end_year,
                "feature_count": len(all_features),
                "api_url": NIFC_HISTORICAL_SERVICE,
                "hunting_note": "Recent burns (2-5 years) create browse areas that attract deer"
            }
        }

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(all_features)} features to {output_file}")
        return str(output_file)

    log("  No features found matching criteria", "WARNING")
    return None


def download_current_fires(state_abbrev=None):
    """
    Download current active wildfire perimeter data from NIFC.

    Args:
        state_abbrev: 2-letter state code (e.g., 'TX', 'CA')

    Returns:
        Path to the output GeoJSON file, or None on failure

    Note: Current fires use these fields:
        - attr_POOState: State (format "US-TX")
        - poly_IncidentName: Fire name
        - poly_GISAcres: Calculated acreage
        - attr_IncidentSize: Incident size
        - attr_PercentContained: Containment percentage
    """
    state_upper = state_abbrev.upper() if state_abbrev else None

    output_suffix = state_upper.lower() if state_upper else "national"
    output_file = GEOJSON_DIR / f"wildfire_current_{output_suffix}.geojson"

    log(f"Downloading Current Active Wildfire Perimeters")
    if state_upper:
        log(f"  State: {state_upper}")

    base_url = f"{NIFC_CURRENT_SERVICE}/query"

    all_features = []
    offset = 0
    batch_size = 2000

    # Build WHERE clause - current fires use attr_POOState with format "US-TX"
    where_clause = "1=1"
    if state_upper:
        where_clause = f"attr_POOState = 'US-{state_upper}'"

    while True:
        params = {
            "where": where_clause,
            "outFields": "poly_IncidentName,poly_GISAcres,attr_POOState,attr_POOCounty,attr_IncidentSize,attr_PercentContained,attr_FireDiscoveryDateTime,attr_GACC,poly_DateCurrent",
            "f": "geojson",
            "returnGeometry": "true",
            "outSR": "4326",
            "resultOffset": offset,
            "resultRecordCount": batch_size
        }

        query_string = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        url = f"{base_url}?{query_string}"

        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

            with urllib.request.urlopen(req, timeout=300) as response:
                data = json.loads(response.read().decode('utf-8'))

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

        except urllib.error.HTTPError as e:
            log(f"  HTTP Error {e.code}: {e.reason}", "ERROR")
            break
        except urllib.error.URLError as e:
            log(f"  URL Error: {e.reason}", "ERROR")
            break
        except Exception as e:
            log(f"  Error: {e}", "ERROR")
            break

    if all_features:
        # Enhance features with safety metadata and normalize field names
        for feature in all_features:
            props = feature.get('properties', {})

            # Normalize field names for consistency
            props['IncidentName'] = props.get('poly_IncidentName', 'Unknown')
            props['GISAcres'] = props.get('poly_GISAcres') or props.get('attr_IncidentSize', 0)

            # Extract state from "US-TX" format
            poo_state = props.get('attr_POOState', '')
            if poo_state and poo_state.startswith('US-'):
                state_code = poo_state.replace('US-', '')
                props['state_abbrev'] = state_code
                props['StateName'] = ABBREV_TO_STATE.get(state_code, state_code)

            # Add current year as fire year
            props['FireYear'] = datetime.now().year

            # Safety and hunting metadata
            props['fire_status'] = 'active'
            props['hunting_value'] = 'avoid'
            props['fire_age_category'] = 'active'
            props['safety_warning'] = 'ACTIVE FIRE - Do not enter area'

            # Format acres
            gis_acres = props.get('GISAcres')
            if gis_acres:
                props['acres_formatted'] = f"{gis_acres:,.0f}"

        geojson = {
            "type": "FeatureCollection",
            "name": f"NIFC Current Wildfire Perimeters" + (f" - {state_upper}" if state_upper else ""),
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": all_features,
            "metadata": {
                "source": "National Interagency Fire Center (NIFC) - WFIGS",
                "download_date": datetime.now().isoformat(),
                "state": state_upper,
                "feature_count": len(all_features),
                "api_url": NIFC_CURRENT_SERVICE,
                "warning": "ACTIVE FIRES - Avoid these areas for safety"
            }
        }

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(all_features)} features to {output_file}")
        return str(output_file)

    log("  No current fires found" + (f" in {state_upper}" if state_upper else ""), "INFO")
    return None


def merge_geojson_files(files, output_path):
    """Merge multiple GeoJSON files into one"""
    all_features = []

    for file_path in files:
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                if 'features' in data:
                    all_features.extend(data['features'])

    if all_features:
        merged = {
            "type": "FeatureCollection",
            "name": "NIFC Wildfire Perimeters (Merged)",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": all_features,
            "metadata": {
                "source": "National Interagency Fire Center (NIFC)",
                "download_date": datetime.now().isoformat(),
                "feature_count": len(all_features),
                "merged_from": [os.path.basename(f) for f in files if f]
            }
        }

        with open(output_path, 'w') as f:
            json.dump(merged, f)

        log(f"  Merged {len(all_features)} features to {output_path}")
        return str(output_path)

    return None


def generate_pmtiles(geojson_path, pmtiles_path, layer_name="wildfire"):
    """Generate PMTiles from GeoJSON using tippecanoe"""
    import subprocess

    log(f"Generating PMTiles: {os.path.basename(geojson_path)}")

    # Remove existing file if present (tippecanoe won't overwrite)
    if os.path.exists(pmtiles_path):
        os.remove(pmtiles_path)

    cmd = [
        "tippecanoe",
        "-z14",           # Max zoom 14
        "-Z4",            # Min zoom 4
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "--coalesce-densest-as-needed",
        "-l", layer_name,
        "-o", str(pmtiles_path),
        "--force",        # Overwrite output
        str(geojson_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if result.returncode == 0:
            file_size = os.path.getsize(pmtiles_path) / (1024 * 1024)
            log(f"  Generated: {pmtiles_path} ({file_size:.1f} MB)")
            return True
        else:
            log(f"  PMTiles error: {result.stderr}", "ERROR")
            return False
    except FileNotFoundError:
        log("  tippecanoe not found. Install with: brew install tippecanoe (macOS) or from source", "ERROR")
        return False
    except subprocess.TimeoutExpired:
        log("  PMTiles generation timed out (>2 hours)", "ERROR")
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

        file_size = os.path.getsize(local_path) / (1024 * 1024)

        s3_client.upload_file(
            local_path,
            R2_BUCKET,
            r2_key,
            ExtraArgs={'ContentType': content_type}
        )

        public_url = f"{R2_PUBLIC_URL}/{r2_key}"
        log(f"  Uploaded: {public_url} ({file_size:.1f} MB)")
        return public_url

    except Exception as e:
        log(f"  Upload error: {e}", "ERROR")
        return None


def cleanup_local(path):
    """Remove local file after upload"""
    try:
        if path and os.path.isfile(path):
            os.remove(path)
            log(f"  Removed: {path}")
    except Exception as e:
        log(f"  Cleanup error: {e}", "WARNING")


def main():
    import argparse

    current_year = datetime.now().year
    default_start_year = current_year - 5

    parser = argparse.ArgumentParser(
        description="Download NIFC Wildfire Perimeter Data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Download last 5 years of fires for Texas
  python3 download_wildfire.py --state TX

  # Download fires from 2020-2025 for California
  python3 download_wildfire.py --state CA --start-year 2020

  # Download historical + current fires, generate PMTiles, upload
  python3 download_wildfire.py --state OR --current --pmtiles --upload

  # National download (large!) with full pipeline
  python3 download_wildfire.py --pmtiles --upload --cleanup

Hunting Relevance:
  Recent burn areas (1-5 years old) have rapid vegetation regrowth.
  This creates browse areas that attract deer, elk, and other game.

  Fire Age Categories:
    0 years (active)  - AVOID - active fire danger
    1 year            - Low value - early succession
    2-3 years         - HIGH value - excellent browse
    4-5 years         - Medium value - good browse
    6+ years          - Lower value - mature vegetation

Data Sources:
  Historical: {NIFC_HISTORICAL_SERVICE}
  Current: {NIFC_CURRENT_SERVICE}
        """
    )

    parser.add_argument("--state", "-s",
                        help="State abbreviation (e.g., TX, CA, OR)")
    parser.add_argument("--start-year", type=int, default=default_start_year,
                        help=f"Start year for historical fires (default: {default_start_year})")
    parser.add_argument("--end-year", type=int, default=current_year,
                        help=f"End year for historical fires (default: {current_year})")
    parser.add_argument("--current", action="store_true",
                        help="Include current active fires")
    parser.add_argument("--historical-only", action="store_true",
                        help="Only download historical fires (skip current)")
    parser.add_argument("--current-only", action="store_true",
                        help="Only download current active fires")
    parser.add_argument("--pmtiles", action="store_true",
                        help="Generate PMTiles using tippecanoe")
    parser.add_argument("--upload", action="store_true",
                        help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true",
                        help="Remove local files after upload")
    parser.add_argument("--list-states", action="store_true",
                        help="List valid state abbreviations")

    args = parser.parse_args()

    # List states and exit
    if args.list_states:
        log("Valid state abbreviations:")
        for abbrev, name in sorted(ABBREV_TO_STATE.items()):
            log(f"  {abbrev}: {name}")
        return

    ensure_directories()

    log("=" * 70)
    log("NIFC Wildfire Perimeter Download")
    log("=" * 70)

    state_upper = args.state.upper() if args.state else None

    if state_upper and state_upper not in ABBREV_TO_STATE:
        log(f"Unknown state: {state_upper}. Use --list-states to see valid options.", "ERROR")
        return

    downloaded_files = []
    pmtiles_files = []

    # Download historical fires
    if not args.current_only:
        historical_file = download_historical_fires(
            state_abbrev=state_upper,
            start_year=args.start_year,
            end_year=args.end_year
        )
        if historical_file:
            downloaded_files.append(historical_file)

    # Download current fires
    if args.current or args.current_only:
        current_file = download_current_fires(state_abbrev=state_upper)
        if current_file:
            downloaded_files.append(current_file)

    if not downloaded_files:
        log("No data downloaded", "WARNING")
        return

    # Merge files if we have both historical and current
    final_geojson = None
    if len(downloaded_files) > 1:
        suffix = state_upper.lower() if state_upper else "national"
        merged_path = GEOJSON_DIR / f"wildfire_{suffix}.geojson"
        final_geojson = merge_geojson_files(downloaded_files, merged_path)
    elif len(downloaded_files) == 1:
        final_geojson = downloaded_files[0]

    # Generate PMTiles
    if args.pmtiles and final_geojson:
        suffix = state_upper.lower() if state_upper else "national"
        pmtiles_name = f"wildfire_{suffix}.pmtiles"
        pmtiles_path = PMTILES_DIR / pmtiles_name

        if generate_pmtiles(final_geojson, pmtiles_path, layer_name="wildfire"):
            pmtiles_files.append(str(pmtiles_path))

    # Upload to R2
    if args.upload:
        # Upload PMTiles (primary deliverable)
        for pmtiles_file in pmtiles_files:
            if os.path.exists(pmtiles_file):
                filename = os.path.basename(pmtiles_file)
                r2_key = f"enrichment/wildfire/{filename}"
                upload_to_r2(pmtiles_file, r2_key)

        # Optionally upload GeoJSON too
        if final_geojson and os.path.exists(final_geojson):
            filename = os.path.basename(final_geojson)
            r2_key = f"enrichment/wildfire/{filename}"
            upload_to_r2(final_geojson, r2_key)

    # Cleanup
    if args.cleanup and args.upload:
        # Clean up all downloaded files
        for file_path in downloaded_files:
            cleanup_local(file_path)

        # Clean up merged file if different from downloaded
        if final_geojson and final_geojson not in downloaded_files:
            cleanup_local(final_geojson)

        # Clean up PMTiles
        for pmtiles_file in pmtiles_files:
            cleanup_local(pmtiles_file)

    log("=" * 70)
    log("Wildfire perimeter download complete!")
    log("=" * 70)

    # Summary
    log("\nSummary:")
    for f in downloaded_files:
        if f and os.path.exists(f):
            size_mb = os.path.getsize(f) / (1024 * 1024)
            log(f"  GeoJSON: {os.path.basename(f)} ({size_mb:.1f} MB)")
    for f in pmtiles_files:
        if f and os.path.exists(f):
            size_mb = os.path.getsize(f) / (1024 * 1024)
            log(f"  PMTiles: {os.path.basename(f)} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
