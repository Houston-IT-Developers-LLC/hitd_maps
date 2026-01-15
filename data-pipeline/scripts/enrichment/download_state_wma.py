#!/usr/bin/env python3
"""
Download State Wildlife Management Areas (WMA)

Priority: 4
Sources: Various State Fish & Game Agencies

State WMA data for:
- Public hunting land boundaries
- Wildlife management unit boundaries
- State game lands
- Walk-in hunting access (WIHA/PLOTS)

Update Frequency: Annual (varies by state)
Date Added: 2026-01-13

Note: PAD-US includes much of this data, but state sources
may be more current and include state-specific attributes.
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

# State Wildlife Agency REST Services
# Each state has different endpoints and data structures
STATE_WMA_SERVICES = {
    "TX": {
        "name": "Texas Parks & Wildlife",
        "service_url": "https://services1.arcgis.com/1mtXwieMId59thmg/arcgis/rest/services/WMA_Boundaries_4PublicDistribution/FeatureServer",
        "layer_id": 0,
        "fields": "LoName,County1,County2,BndryType",
        "notes": "Wildlife Management Areas"
    },
    "PA": {
        "name": "Pennsylvania Game Commission",
        "service_url": "https://gis.pgc.pa.gov/arcgis/rest/services/PGC/StateGameLands/MapServer",
        "layer_id": 0,
        "fields": "SGL_NUM,NAME,ACRES,COUNTY",
        "notes": "State Game Lands"
    },
    "MI": {
        "name": "Michigan DNR",
        "service_url": "https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services/State_Managed_Public_Hunting_Lands/FeatureServer",
        "layer_id": 0,
        "fields": "PROPERTYNAME,ACRES,COUNTY",
        "notes": "State Managed Public Hunting Lands"
    },
    "WI": {
        "name": "Wisconsin DNR",
        "service_url": "https://dnrmaps.wi.gov/arcgis/rest/services/LF_DML/LF_AGOL_STAGING_WTM_Ext/MapServer",
        "layer_id": 1,
        "fields": "PROP_NAME,GIS_ACRES,DEED_ACRES,TRANS_TYPE_CODE,FUNCTION_MGT_CODE",
        "notes": "DNR Managed Lands by Parcel"
    },
    "MN": {
        "name": "Minnesota DNR",
        "service_url": "https://services.arcgis.com/vCNsuUqFLSuHC46v/arcgis/rest/services/Wildlife_Management_Areas/FeatureServer",
        "layer_id": 0,
        "fields": "UNITNAME,ACREAGE,COUNTYNAME",
        "notes": "Wildlife Management Areas"
    },
    "CO": {
        "name": "Colorado Parks & Wildlife",
        "service_url": "https://services5.arcgis.com/ttNGmDvKQA7oeDQ3/arcgis/rest/services/CPWAdminData/FeatureServer",
        "layer_id": 5,
        "fields": "PropName,PropType,Acres",
        "notes": "State Wildlife Areas"
    },
    "MT": {
        "name": "Montana FWP",
        "service_url": "https://services3.arcgis.com/Cdxz8r11hT0MGzg1/arcgis/rest/services/FWPLND_WMA/FeatureServer",
        "layer_id": 0,
        "fields": "NAME,ACRES,FWPREG,HUNTING",
        "notes": "FWP Wildlife Management Areas"
    },
    "NC": {
        "name": "NC Wildlife Resources Commission",
        "service_url": "https://services.arcgis.com/vCNsuUqFLSuHC46v/arcgis/rest/services/NC_Game_Lands/FeatureServer",
        "layer_id": 0,
        "fields": "GAMELANDNAME,ACRES,COUNTY",
        "notes": "Game Lands"
    },
    "GA": {
        "name": "Georgia DNR",
        "service_url": "https://services.arcgis.com/vCNsuUqFLSuHC46v/arcgis/rest/services/GA_Wildlife_Management_Areas/FeatureServer",
        "layer_id": 0,
        "fields": "WMA_NAME,ACRES,COUNTY",
        "notes": "Wildlife Management Areas"
    },
    "FL": {
        "name": "Florida FWC",
        "service_url": "https://services.arcgis.com/vCNsuUqFLSuHC46v/arcgis/rest/services/FL_Wildlife_Management_Areas/FeatureServer",
        "layer_id": 0,
        "fields": "WMA_NAME,ACRES,COUNTY",
        "notes": "Wildlife Management Areas"
    },
    "OH": {
        "name": "Ohio DNR",
        "service_url": "https://services.arcgis.com/vCNsuUqFLSuHC46v/arcgis/rest/services/OH_Wildlife_Areas/FeatureServer",
        "layer_id": 0,
        "fields": "AREA_NAME,ACRES,COUNTY",
        "notes": "Wildlife Areas"
    },
    "ID": {
        "name": "Idaho Fish and Game",
        "service_url": "https://services.arcgis.com/FjJI5xHF2dUPVrgK/arcgis/rest/services/WildlifeManagementAreas/FeatureServer",
        "layer_id": 0,
        "fields": "*",
        "notes": "Wildlife Management Areas"
    },
    "WY": {
        "name": "Wyoming Game and Fish",
        "service_url": "https://services6.arcgis.com/cWzdqIyxbijuhPLw/arcgis/rest/services/WildlifeHabitatManagementAreaBoundaries/FeatureServer",
        "layer_id": 0,
        "fields": "WHMA_Name,Acres",
        "notes": "Wildlife Habitat Management Areas (WHMA)"
    },
    "AZ": {
        "name": "Arizona Game and Fish",
        "service_url": "https://services8.arcgis.com/KyZIQDOsXnGaTxj2/arcgis/rest/services/AZ_Game_and_Fish_Hunt_Units/FeatureServer",
        "layer_id": 0,
        "fields": "GMU,GF_REGION,REG_NAME,SQ_MILES,ACRES,HUNT",
        "notes": "Game Management Units (hunt units)"
    },
    "NM": {
        "name": "New Mexico Dept of Game and Fish (via BLM)",
        "service_url": "https://gis.blm.gov/nmarcgis/rest/services/Recreation/NMDGF_NM_Game_Management_Units/MapServer",
        "layer_id": 0,
        "fields": "GMU,BEAR_ZONE,COUGAR_ZON,HUNT_INFO",
        "notes": "Game Management Units"
    },
    "OR": {
        "name": "Oregon Dept of Fish and Wildlife",
        "service_url": "https://nrimp.dfw.state.or.us/arcgis/rest/services/ODFW_Admin/WildlifeManagementUnits/FeatureServer",
        "layer_id": 0,
        "fields": "UNIT_NUM,UNIT_NAME,Acres,REGION",
        "notes": "Wildlife Management Units"
    }
}

# PLOTS/Walk-In Hunting programs (special category)
WALK_IN_PROGRAMS = {
    "KS": {
        "name": "Kansas WIHA (Walk-In Hunting Areas)",
        "service_url": "https://services.arcgis.com/vCNsuUqFLSuHC46v/arcgis/rest/services/KS_WIHA/FeatureServer",
        "layer_id": 0,
        "fields": "NAME,ACRES,COUNTY",
        "notes": "Walk-In Hunting Areas - Private land enrolled for public hunting"
    },
    "NE": {
        "name": "Nebraska Open Fields and Waters",
        "service_url": "https://services.arcgis.com/vCNsuUqFLSuHC46v/arcgis/rest/services/NE_Open_Fields_Waters/FeatureServer",
        "layer_id": 0,
        "fields": "NAME,ACRES,COUNTY",
        "notes": "Open Fields and Waters program"
    },
    "ND": {
        "name": "North Dakota PLOTS",
        "service_url": "https://services.arcgis.com/vCNsuUqFLSuHC46v/arcgis/rest/services/ND_PLOTS/FeatureServer",
        "layer_id": 0,
        "fields": "PLOTSNAME,ACRES,COUNTY",
        "notes": "Private Land Open To Sportsmen"
    },
    "SD": {
        "name": "South Dakota Walk-In Areas",
        "service_url": "https://services.arcgis.com/vCNsuUqFLSuHC46v/arcgis/rest/services/SD_Walk_In/FeatureServer",
        "layer_id": 0,
        "fields": "NAME,ACRES,COUNTY",
        "notes": "Walk-In Area hunting access"
    },
    "MT": {
        "name": "Montana Block Management",
        "service_url": "https://services.arcgis.com/vCNsuUqFLSuHC46v/arcgis/rest/services/MT_Block_Management/FeatureServer",
        "layer_id": 0,
        "fields": "BMA_NAME,ACRES,COUNTY",
        "notes": "Block Management Areas - Private land enrolled for hunting"
    }
}


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories"""
    for dir_path in [GEOJSON_DIR, PMTILES_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def download_state_wma(state_abbrev, service_config):
    """
    Download WMA data from a state's ArcGIS service

    Args:
        state_abbrev: 2-letter state code
        service_config: Dict with service_url, layer_id, fields
    """
    state_upper = state_abbrev.upper()
    output_file = GEOJSON_DIR / f"wma_{state_upper.lower()}.geojson"

    service_url = service_config.get('service_url')
    layer_id = service_config.get('layer_id', 0)
    fields = service_config.get('fields', '*')
    agency_name = service_config.get('name', 'Unknown')

    log(f"Downloading WMA data for {state_upper}")
    log(f"  Agency: {agency_name}")
    log(f"  Service: {service_url}")

    base_url = f"{service_url}/{layer_id}/query"

    all_features = []
    offset = 0
    batch_size = 2000

    while True:
        params = {
            "where": "1=1",
            "outFields": fields,
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

            with urllib.request.urlopen(req, timeout=180) as response:
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
            log(f"  Service may not be available or URL may have changed", "WARNING")
            break
        except urllib.error.URLError as e:
            log(f"  URL Error: {e.reason}", "ERROR")
            break
        except Exception as e:
            log(f"  Error: {e}", "ERROR")
            break

    if all_features:
        # Standardize field names
        for feature in all_features:
            props = feature.get('properties', {})
            props['state'] = state_upper
            props['source_agency'] = agency_name
            props['data_type'] = 'wildlife_management_area'

        geojson = {
            "type": "FeatureCollection",
            "name": f"Wildlife Management Areas - {state_upper}",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": all_features,
            "metadata": {
                "source": agency_name,
                "download_date": datetime.now().isoformat(),
                "state": state_upper,
                "feature_count": len(all_features),
                "api_url": service_url,
                "notes": service_config.get('notes', '')
            }
        }

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(all_features)} WMAs to {output_file}")
        return str(output_file)

    log(f"  No data retrieved for {state_upper}", "WARNING")
    return None


def download_walk_in_areas(state_abbrev, service_config):
    """
    Download Walk-In Hunting Area data (PLOTS, WIHA, etc.)

    These are private lands enrolled in public hunting programs.
    """
    state_upper = state_abbrev.upper()
    output_file = GEOJSON_DIR / f"walk_in_{state_upper.lower()}.geojson"

    service_url = service_config.get('service_url')
    layer_id = service_config.get('layer_id', 0)
    fields = service_config.get('fields', '*')
    program_name = service_config.get('name', 'Walk-In Hunting')

    log(f"Downloading Walk-In Hunting data for {state_upper}")
    log(f"  Program: {program_name}")

    base_url = f"{service_url}/{layer_id}/query"

    all_features = []
    offset = 0
    batch_size = 2000

    while True:
        params = {
            "where": "1=1",
            "outFields": fields,
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

            with urllib.request.urlopen(req, timeout=180) as response:
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

        except Exception as e:
            log(f"  Error: {e}", "ERROR")
            break

    if all_features:
        for feature in all_features:
            props = feature.get('properties', {})
            props['state'] = state_upper
            props['program_name'] = program_name
            props['data_type'] = 'walk_in_hunting'
            props['is_private_land'] = True

        geojson = {
            "type": "FeatureCollection",
            "name": f"Walk-In Hunting - {state_upper}",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": all_features,
            "metadata": {
                "source": program_name,
                "download_date": datetime.now().isoformat(),
                "state": state_upper,
                "feature_count": len(all_features),
                "api_url": service_url,
                "notes": service_config.get('notes', '')
            }
        }

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(all_features)} walk-in areas to {output_file}")
        return str(output_file)

    return None


def generate_pmtiles(geojson_path, pmtiles_path):
    """Generate PMTiles from GeoJSON"""
    import subprocess

    log(f"Generating PMTiles: {geojson_path}")

    cmd = [
        "tippecanoe",
        "-z14",
        "-Z6",
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "-l", "wildlife_areas",
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
        description="Download State Wildlife Management Area Data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download WMA data for specific states
  python3 download_state_wma.py --state TX,CO,MT

  # Download all available states
  python3 download_state_wma.py --all-states

  # Include Walk-In Hunting programs (PLOTS, WIHA, etc.)
  python3 download_state_wma.py --state KS,ND,NE --walk-in

  # Full pipeline
  python3 download_state_wma.py --state TX --pmtiles --upload --cleanup

Available States with WMA Services:
  TX, PA, MI, WI, MN, CO, MT, NC, GA, FL, OH

States with Walk-In Hunting Programs:
  KS (WIHA), NE (Open Fields), ND (PLOTS), SD (Walk-In), MT (Block Mgmt)

Note: Service URLs may change. Check state fish & game websites
for current GIS data access.
        """
    )

    parser.add_argument("--state", "-s", help="State abbreviation(s), comma-separated")
    parser.add_argument("--all-states", action="store_true", help="Download all available states")
    parser.add_argument("--walk-in", action="store_true", help="Include Walk-In Hunting programs")
    parser.add_argument("--pmtiles", action="store_true", help="Generate PMTiles")
    parser.add_argument("--upload", action="store_true", help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true", help="Remove local files after upload")
    parser.add_argument("--list-states", action="store_true", help="List available state services")

    args = parser.parse_args()

    ensure_directories()

    if args.list_states:
        log("Available State WMA Services:")
        for state, config in sorted(STATE_WMA_SERVICES.items()):
            log(f"  {state}: {config['name']} - {config['notes']}")
        log("\nWalk-In Hunting Programs:")
        for state, config in sorted(WALK_IN_PROGRAMS.items()):
            log(f"  {state}: {config['name']} - {config['notes']}")
        return

    states = []
    if args.state:
        states = [s.strip().upper() for s in args.state.split(",")]
    elif args.all_states:
        states = list(STATE_WMA_SERVICES.keys())
    else:
        parser.print_help()
        return

    log(f"Processing {len(states)} states: {', '.join(states)}")

    for state in states:
        log("=" * 60)
        log(f"Processing State WMA: {state}")
        log("=" * 60)

        files_to_upload = []

        # Download WMA data
        if state in STATE_WMA_SERVICES:
            result = download_state_wma(state, STATE_WMA_SERVICES[state])
            if result:
                files_to_upload.append(result)
        else:
            log(f"  No WMA service configured for {state}", "WARNING")

        # Download Walk-In Hunting areas if requested
        if args.walk_in and state in WALK_IN_PROGRAMS:
            result = download_walk_in_areas(state, WALK_IN_PROGRAMS[state])
            if result:
                files_to_upload.append(result)

        # Generate PMTiles
        if args.pmtiles:
            for geojson_file in files_to_upload[:]:
                pmtiles_name = Path(geojson_file).stem + ".pmtiles"
                pmtiles_path = PMTILES_DIR / pmtiles_name
                if generate_pmtiles(geojson_file, pmtiles_path):
                    files_to_upload.append(str(pmtiles_path))

        # Upload
        if args.upload:
            for file_path in files_to_upload:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    r2_key = f"enrichment/state_wma/{filename}"
                    upload_to_r2(file_path, r2_key)

        # Cleanup
        if args.cleanup and args.upload:
            for file_path in files_to_upload:
                if os.path.exists(file_path):
                    cleanup_local(file_path)

    log("=" * 60)
    log("State WMA download complete!")
    log("=" * 60)


if __name__ == "__main__":
    main()
