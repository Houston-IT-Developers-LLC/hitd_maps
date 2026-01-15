#!/usr/bin/env python3
"""
Download State Game Management Unit (GMU) Boundaries

Priority: 3
Sources: State Fish & Wildlife Agencies

GMU/Hunt Unit boundaries for:
- Hunting unit designations
- Game management areas
- Hunt planning and regulations

Update Frequency: Annual (varies by state)
Date Added: 2026-01-13

Note: Each state publishes GMU data differently (GeoJSON, Shapefile,
ArcGIS Feature Service, KML). This script handles multiple formats.
"""

import os
import sys
import json
import ssl
import urllib.request
import urllib.parse
import urllib.error
import tempfile
import zipfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Create SSL context that doesn't verify certificates (for problematic state servers)
SSL_CONTEXT_UNVERIFIED = ssl.create_default_context()
SSL_CONTEXT_UNVERIFIED.check_hostname = False
SSL_CONTEXT_UNVERIFIED.verify_mode = ssl.CERT_NONE

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"
TEMP_DIR = DATA_PIPELINE_DIR / "temp" / "gmu"

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

# State GMU Data Sources
# Format options: "geojson", "shapefile", "arcgis_fs", "kml"
#
# NOTE: State wildlife agency GIS endpoints change frequently.
# If a download fails, check the state agency's GIS portal for updated URLs.
# Common patterns:
#   - ArcGIS Hub: https://[state].hub.arcgis.com or https://[agency].maps.arcgis.com
#   - Open Data Portal: https://geodata.[state].gov or https://gis.[agency].gov
#
# To find updated endpoints:
#   1. Visit the state fish & game website GIS/Maps section
#   2. Search ArcGIS Hub for "[state] hunting districts" or "game management units"
#   3. Look for REST Services directory links
#
# STATUS KEY:
#   verified: Recently tested and working
#   unverified: URL may need updating - check state GIS portal if fails
#
STATE_SOURCES: Dict[str, Dict[str, Any]] = {
    # ========================================================================
    # VERIFIED WORKING ENDPOINTS (as of 2026-01)
    # ========================================================================
    "MI": {
        "name": "Michigan DNR",
        "format": "arcgis_fs",
        "url": "https://services3.arcgis.com/Jdnp1TjADvSDxMAX/ArcGIS/rest/services/Deer_Management_Units_for_Deer_Camp_Survey/FeatureServer",
        "layer_id": 0,
        "id_field": "DMU",
        "name_field": "DMU",
        "notes": "Deer Management Units from MI DNR",
        "status": "verified"
    },

    # ========================================================================
    # UNVERIFIED ENDPOINTS - May need URL updates
    # Check state GIS portals if these fail
    # ========================================================================
    "CO": {
        "name": "Colorado Parks & Wildlife",
        "format": "arcgis_fs",
        # Updated 2026-01: CPWAdminData hosted service with GMU layer
        # Source: https://geodata.colorado.gov/datasets/CPW::cpwadmindata/about?layer=6
        "url": "https://services5.arcgis.com/ttNGmDvKQA7oeDQ3/arcgis/rest/services/CPWAdminData/FeatureServer",
        "layer_id": 6,  # Layer 6 = CPW GMU Boundary (Big Game)
        "id_field": "GMUID",
        "name_field": "GMUID",  # GMUID is the primary identifier, no separate name field
        "notes": "Big Game Management Units from CPW - Layer 6 of CPWAdminData service",
        "status": "verified"
    },
    "MT": {
        "name": "Montana Fish Wildlife & Parks",
        "format": "arcgis_fs",
        # Updated 2026-01: Current 2024-2025 hunting districts
        # Source: https://gis-mtfwp.hub.arcgis.com/datasets/d148ae5ae2374132b53b438b6c03264f_0
        "url": "https://services3.arcgis.com/Cdxz8r11hT0MGzg1/arcgis/rest/services/ADMBND_HD_DEERELKLION/FeatureServer",
        "layer_id": 0,
        "id_field": "DISTRICT",
        "name_field": "NAME",
        "notes": "Deer and Elk Hunting Districts (2024-2025 Seasons) from Montana FWP",
        "status": "verified"
    },
    "AZ": {
        "name": "Arizona Game & Fish Department",
        "format": "arcgis_fs",
        # Updated 2026-01: Official AZGFD Hunt Units hosted on ArcGIS Online
        # Source: https://www.arcgis.com/home/item.html?id=7c8d66aa4f3e4e62b243f1216734a581
        "url": "https://services8.arcgis.com/KyZIQDOsXnGaTxj2/arcgis/rest/services/AZ_Game_and_Fish_Hunt_Units/FeatureServer",
        "layer_id": 0,
        "id_field": "UNIT",
        "name_field": "UNIT_NAME",
        "notes": "Game Management Units from AZGFD - 56 hunt units statewide",
        "status": "verified"
    },
    "WY": {
        "name": "Wyoming Game & Fish Department",
        "format": "arcgis_fs",
        # Updated 2026-01: Official WGFD Deer Hunt Areas 2025
        # Source: https://wyoming-wgfd.opendata.arcgis.com
        "url": "https://services6.arcgis.com/cWzdqIyxbijuhPLw/arcgis/rest/services/DeerHuntAreas/FeatureServer",
        "layer_id": 0,
        "id_field": "HUNTAREA",
        "name_field": "HUNTNAME",
        "notes": "Deer Hunt Areas 2025 from WGFD - includes mule deer and white-tailed deer areas",
        "status": "verified"
    },
    "NM": {
        "name": "New Mexico Game & Fish",
        "format": "arcgis_fs",
        # Updated 2026-01: BLM-hosted NMDGF Game Management Units
        # Source: https://gis.blm.gov/nmarcgis/rest/services/Recreation/NMDGF_NM_Game_Management_Units/MapServer
        "url": "https://gis.blm.gov/nmarcgis/rest/services/Recreation/NMDGF_NM_Game_Management_Units/MapServer",
        "layer_id": 0,
        "id_field": "GMU",
        "name_field": "GMU",
        "notes": "Game Management Units from NMDGF hosted by BLM - Big Game Management Units per Title 19 Chapter 30 Part 4",
        "status": "verified"
    },
    "ID": {
        "name": "Idaho Fish & Game",
        "format": "arcgis_fs",
        # Try: https://idfg.idaho.gov/data for updated URL
        "url": "https://services.arcgis.com/FjJI5xHF2dUPVrgK/arcgis/rest/services/GameManagementUnits/FeatureServer",
        "layer_id": 0,
        "id_field": "UNIT_ID",
        "name_field": "UNIT_NAME",
        "notes": "Game Management Units from IDFG",
        "status": "unverified"
    },
    "UT": {
        "name": "Utah Division of Wildlife Resources",
        "format": "arcgis_fs",
        "url": "https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/DWR_Wildlife_SGMA/FeatureServer",
        "layer_id": 0,
        "id_field": "UNIT_ID",
        "name_field": "UNIT_NAME",
        "notes": "Wildlife Management Units from UDWR",
        "status": "unverified"
    },
    "NV": {
        "name": "Nevada Department of Wildlife",
        "format": "arcgis_fs",
        "url": "https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/Hunt_Unit_Boundaries/FeatureServer",
        "layer_id": 0,
        "id_field": "UNIT_NUM",
        "name_field": "UNIT_NAME",
        "notes": "Hunt Unit Boundaries from NDOW",
        "status": "unverified"
    },
    "OR": {
        "name": "Oregon Department of Fish & Wildlife",
        "format": "arcgis_fs",
        # Updated 2026-01: Official ODFW Wildlife Management Units from NRIMP
        # Source: https://nrimp.dfw.state.or.us/arcgis/rest/services/Compass/ODFW_WildlifeManagementUnits/MapServer
        "url": "https://nrimp.dfw.state.or.us/arcgis/rest/services/Compass/ODFW_WildlifeManagementUnits/MapServer",
        "layer_id": 0,
        "id_field": "UNIT_NAME",
        "name_field": "UNIT_NAME",
        "notes": "Wildlife Management Units from ODFW - published in Oregon Big Game Hunting Regulations",
        "status": "verified"
    },
    "WA": {
        "name": "Washington Department of Fish & Wildlife",
        "format": "arcgis_fs",
        # Updated 2026-01: Official WDFW GMU from HOReferenceService
        # Source: https://geodataservices.wdfw.wa.gov/arcgis/rest/services/MapServices/HOReferenceService/MapServer/0
        "url": "https://geodataservices.wdfw.wa.gov/arcgis/rest/services/MapServices/HOReferenceService/MapServer",
        "layer_id": 0,
        "id_field": "GMU_Num",
        "name_field": "GMU_Name",
        "notes": "Game Management Units from WDFW - 140+ GMUs for hunt planning",
        "status": "verified"
    },
    "TX": {
        "name": "Texas Parks & Wildlife Department",
        "format": "arcgis_fs",
        # Updated 2026-01: TPWD White-tailed Deer Management Units (MapServer - no pagination)
        # Source: https://tpwd.texas.gov/arcgis/rest/services/Wildlife/TPWD_WL_WTDMU/MapServer
        "url": "https://tpwd.texas.gov/arcgis/rest/services/Wildlife/TPWD_WL_WTDMU/MapServer",
        "layer_id": 0,
        "id_field": "UnitNumber",
        "name_field": "UnitNumber",  # Only field available is UnitNumber
        "notes": "White-tailed Deer Management Units (44 DMUs) from TPWD - MapServer, no pagination needed",
        "status": "verified"
    },
    "SD": {
        "name": "South Dakota Game Fish & Parks",
        "format": "arcgis_fs",
        "url": "https://services.arcgis.com/QxHl3qxXMO1JjT3o/arcgis/rest/services/Hunt_Units/FeatureServer",
        "layer_id": 0,
        "id_field": "UNIT_NUM",
        "name_field": "UNIT_NAME",
        "notes": "Hunt Units from SDGFP",
        "status": "unverified"
    },
    "ND": {
        "name": "North Dakota Game & Fish",
        "format": "arcgis_fs",
        "url": "https://services.arcgis.com/F7DSX1DSNSiWmOqh/arcgis/rest/services/Hunting_Units/FeatureServer",
        "layer_id": 0,
        "id_field": "UNIT_ID",
        "name_field": "UNIT_NAME",
        "notes": "Hunting Units from NDGF",
        "status": "unverified"
    },
    "NE": {
        "name": "Nebraska Game & Parks",
        "format": "arcgis_fs",
        "url": "https://services.arcgis.com/PwY9ZxGQLzFBnLwT/arcgis/rest/services/Hunt_Management_Units/FeatureServer",
        "layer_id": 0,
        "id_field": "UNIT_ID",
        "name_field": "UNIT_NAME",
        "notes": "Hunt Management Units from NGPC",
        "status": "unverified"
    },
    "KS": {
        "name": "Kansas Department of Wildlife & Parks",
        "format": "arcgis_fs",
        "url": "https://services.arcgis.com/Jz3XkT0jNqFE0z0S/arcgis/rest/services/Management_Units/FeatureServer",
        "layer_id": 0,
        "id_field": "UNIT_ID",
        "name_field": "UNIT_NAME",
        "notes": "Management Units from KDWP",
        "status": "unverified"
    },
    "OK": {
        "name": "Oklahoma Department of Wildlife Conservation",
        "format": "arcgis_fs",
        "url": "https://services.arcgis.com/RuScGTzPrFW9PJLP/arcgis/rest/services/Wildlife_Management_Units/FeatureServer",
        "layer_id": 0,
        "id_field": "WMU_ID",
        "name_field": "WMU_NAME",
        "notes": "Wildlife Management Units from ODWC",
        "status": "unverified"
    },
    "PA": {
        "name": "Pennsylvania Game Commission",
        "format": "arcgis_fs",
        # Try: https://gis.pgc.pa.gov for updated URL
        "url": "https://gis.pgc.pa.gov/arcgis/rest/services/PGC/WMU_Boundaries/MapServer",
        "layer_id": 0,
        "id_field": "WMU",
        "name_field": "WMU_NAME",
        "notes": "Wildlife Management Units from PGC",
        "status": "unverified"
    },
    "WI": {
        "name": "Wisconsin DNR",
        "format": "arcgis_fs",
        # Updated 2026-01: WI DNR Deer Management Units service
        # Source: https://dnrmaps.wi.gov/arcgis/rest/services/WM_CWD/WM_DMU_WTM_Ext/MapServer
        "url": "https://dnrmaps.wi.gov/arcgis/rest/services/WM_CWD/WM_DMU_WTM_Ext/MapServer",
        "layer_id": 2,  # Layer 2 = Deer Management Units
        "id_field": "DEER_MGMT_UNIT_ID",
        "name_field": "DEER_MGMT_UNIT_ID",  # DMU ID is the only identifier field
        "notes": "Deer Management Units from WI DNR - county-based in farmland zones, habitat-based in forest zones",
        "status": "verified"
    },
    "MN": {
        "name": "Minnesota DNR",
        "format": "arcgis_fs",
        "url": "https://services.arcgis.com/vCNsuUqFLSuHC46v/arcgis/rest/services/DeerPermitAreas/FeatureServer",
        "layer_id": 0,
        "id_field": "PERMIT_ID",
        "name_field": "PERMIT_NAME",
        "notes": "Deer Permit Areas from MN DNR"
    },
}


def log(message: str, level: str = "INFO") -> None:
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories() -> None:
    """Create necessary directories"""
    for dir_path in [GEOJSON_DIR, PMTILES_DIR, LOG_DIR, TEMP_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def download_file(url: str, output_path: Path, timeout: int = 300, verify_ssl: bool = True) -> bool:
    """Download a file from URL to local path"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

        # Use unverified SSL context if requested (some state servers have cert issues)
        context = None if verify_ssl else SSL_CONTEXT_UNVERIFIED

        with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
            with open(output_path, 'wb') as f:
                shutil.copyfileobj(response, f)
        return True
    except ssl.SSLError as e:
        if verify_ssl:
            log(f"  SSL error, retrying without verification: {e}", "WARNING")
            return download_file(url, output_path, timeout, verify_ssl=False)
        log(f"  SSL error: {e}", "ERROR")
        return False
    except urllib.error.URLError as e:
        # URLError may wrap SSL errors
        if verify_ssl and 'SSL' in str(e) or 'certificate' in str(e).lower():
            log(f"  SSL error in URLError, retrying without verification: {e}", "WARNING")
            return download_file(url, output_path, timeout, verify_ssl=False)
        log(f"  Download error: {e}", "ERROR")
        return False
    except Exception as e:
        log(f"  Download error: {e}", "ERROR")
        return False


def download_geojson(state: str, config: Dict[str, Any]) -> Optional[str]:
    """
    Download GMU data from direct GeoJSON URL
    """
    state_upper = state.upper()
    output_file = GEOJSON_DIR / f"gmu_{state_upper.lower()}.geojson"

    url = config.get('url')
    id_field = config.get('id_field', 'UNIT_ID')
    name_field = config.get('name_field', 'UNIT_NAME')

    log(f"Downloading GeoJSON for {state_upper}")
    log(f"  URL: {url}")

    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

        with urllib.request.urlopen(req, timeout=300) as response:
            data = json.loads(response.read().decode('utf-8'))

        if 'features' not in data or len(data['features']) == 0:
            log(f"  No features found in response", "WARNING")
            return None

        # Normalize features
        normalized_features = normalize_features(
            data['features'],
            state_upper,
            config['name'],
            id_field,
            name_field
        )

        geojson = create_geojson_output(
            normalized_features,
            state_upper,
            config['name'],
            url
        )

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(normalized_features)} GMUs to {output_file}")
        return str(output_file)

    except urllib.error.HTTPError as e:
        log(f"  HTTP Error {e.code}: {e.reason}", "ERROR")
        return None
    except urllib.error.URLError as e:
        log(f"  URL Error: {e.reason}", "ERROR")
        return None
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def download_arcgis_fs(state: str, config: Dict[str, Any]) -> Optional[str]:
    """
    Download GMU data from ArcGIS Feature Service or MapServer with pagination support.
    Handles both FeatureServer and MapServer endpoints, with fallback for services
    that don't support pagination.
    """
    state_upper = state.upper()
    output_file = GEOJSON_DIR / f"gmu_{state_upper.lower()}.geojson"

    service_url = config.get('url')
    layer_id = config.get('layer_id', 0)
    id_field = config.get('id_field', 'UNIT_ID')
    name_field = config.get('name_field', 'UNIT_NAME')

    log(f"Downloading from ArcGIS service for {state_upper}")
    log(f"  Service: {service_url}")

    base_url = f"{service_url}/{layer_id}/query"

    all_features = []
    offset = 0
    batch_size = 2000
    pagination_supported = True  # Assume pagination is supported initially

    while True:
        # Build query parameters
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "returnGeometry": "true",
            "outSR": "4326",
        }

        # Only add pagination params if pagination is supported
        if pagination_supported and offset > 0:
            params["resultOffset"] = offset
            params["resultRecordCount"] = batch_size
        elif pagination_supported:
            # First request - try with pagination
            params["resultOffset"] = 0
            params["resultRecordCount"] = batch_size

        query_string = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        url = f"{base_url}?{query_string}"

        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

            with urllib.request.urlopen(req, timeout=180) as response:
                data = json.loads(response.read().decode('utf-8'))

                if 'error' in data:
                    error_msg = data['error']
                    # Check if error is due to pagination not being supported
                    if isinstance(error_msg, dict) and 'Pagination' in str(error_msg.get('message', '')):
                        if pagination_supported and offset == 0:
                            log(f"  Pagination not supported, retrying without pagination...", "INFO")
                            pagination_supported = False
                            continue  # Retry without pagination
                    log(f"  API Error: {error_msg}", "ERROR")
                    break

                if 'features' not in data or len(data['features']) == 0:
                    break

                all_features.extend(data['features'])
                log(f"  Fetched {len(data['features'])} features (total: {len(all_features)})")

                # If pagination is not supported or we got fewer features than batch size, we're done
                if not pagination_supported or len(data['features']) < batch_size:
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
        # Normalize features
        normalized_features = normalize_features(
            all_features,
            state_upper,
            config['name'],
            id_field,
            name_field
        )

        geojson = create_geojson_output(
            normalized_features,
            state_upper,
            config['name'],
            service_url
        )

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(normalized_features)} GMUs to {output_file}")
        return str(output_file)

    log(f"  No data retrieved for {state_upper}", "WARNING")
    return None


def download_shapefile(state: str, config: Dict[str, Any]) -> Optional[str]:
    """
    Download and convert Shapefile to GeoJSON
    Requires: ogr2ogr (GDAL) for conversion
    """
    state_upper = state.upper()
    output_file = GEOJSON_DIR / f"gmu_{state_upper.lower()}.geojson"

    url = config.get('url')
    shapefile_name = config.get('shapefile_name')
    id_field = config.get('id_field', 'UNIT_ID')
    name_field = config.get('name_field', 'UNIT_NAME')

    log(f"Downloading Shapefile for {state_upper}")
    log(f"  URL: {url}")

    # Create temp directory for this state
    state_temp = TEMP_DIR / state_upper.lower()
    state_temp.mkdir(parents=True, exist_ok=True)

    zip_path = state_temp / "gmu_data.zip"

    try:
        # Download the zip file
        if not download_file(url, zip_path):
            return None

        log(f"  Downloaded {zip_path.stat().st_size / 1024 / 1024:.1f}MB")

        # Extract zip
        extract_dir = state_temp / "extracted"
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        log(f"  Extracted to {extract_dir}")

        # Find the shapefile
        shp_files = list(extract_dir.rglob("*.shp"))

        if shapefile_name:
            shp_path = None
            for shp in shp_files:
                if shp.name == shapefile_name or shapefile_name in str(shp):
                    shp_path = shp
                    break
            if not shp_path and shp_files:
                shp_path = shp_files[0]
        elif shp_files:
            shp_path = shp_files[0]
        else:
            log(f"  No shapefile found in archive", "ERROR")
            return None

        log(f"  Found shapefile: {shp_path.name}")

        # Convert to GeoJSON using ogr2ogr (reproject to WGS84)
        temp_geojson = state_temp / "temp_output.geojson"

        cmd = [
            "ogr2ogr",
            "-f", "GeoJSON",
            "-t_srs", "EPSG:4326",  # Reproject to WGS84
            str(temp_geojson),
            str(shp_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            log(f"  ogr2ogr error: {result.stderr}", "ERROR")
            # Try without reprojection as fallback
            cmd = [
                "ogr2ogr",
                "-f", "GeoJSON",
                str(temp_geojson),
                str(shp_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                log(f"  ogr2ogr fallback error: {result.stderr}", "ERROR")
                return None

        # Load and normalize
        with open(temp_geojson, 'r') as f:
            data = json.load(f)

        if 'features' not in data or len(data['features']) == 0:
            log(f"  No features in converted GeoJSON", "WARNING")
            return None

        # Normalize features
        normalized_features = normalize_features(
            data['features'],
            state_upper,
            config['name'],
            id_field,
            name_field
        )

        geojson = create_geojson_output(
            normalized_features,
            state_upper,
            config['name'],
            url
        )

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(normalized_features)} GMUs to {output_file}")

        # Cleanup temp files
        shutil.rmtree(state_temp, ignore_errors=True)

        return str(output_file)

    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        # Cleanup on error
        shutil.rmtree(state_temp, ignore_errors=True)
        return None


def download_kml(state: str, config: Dict[str, Any]) -> Optional[str]:
    """
    Download and convert KML to GeoJSON
    Requires: ogr2ogr (GDAL) for conversion
    """
    state_upper = state.upper()
    output_file = GEOJSON_DIR / f"gmu_{state_upper.lower()}.geojson"

    url = config.get('url')
    id_field = config.get('id_field', 'UNIT_ID')
    name_field = config.get('name_field', 'Name')  # KML typically uses 'Name'

    log(f"Downloading KML for {state_upper}")
    log(f"  URL: {url}")

    # Create temp directory
    state_temp = TEMP_DIR / state_upper.lower()
    state_temp.mkdir(parents=True, exist_ok=True)

    kml_path = state_temp / "gmu_data.kml"

    try:
        # Download the KML file
        if not download_file(url, kml_path):
            # Try KMZ
            kmz_path = state_temp / "gmu_data.kmz"
            if not download_file(url, kmz_path):
                return None

            # Extract KMZ (it's a zip)
            with zipfile.ZipFile(kmz_path, 'r') as zip_ref:
                zip_ref.extractall(state_temp)

            kml_files = list(state_temp.glob("*.kml"))
            if kml_files:
                kml_path = kml_files[0]
            else:
                log(f"  No KML found in KMZ", "ERROR")
                return None

        # Convert to GeoJSON using ogr2ogr
        temp_geojson = state_temp / "temp_output.geojson"

        cmd = [
            "ogr2ogr",
            "-f", "GeoJSON",
            "-t_srs", "EPSG:4326",
            str(temp_geojson),
            str(kml_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            log(f"  ogr2ogr error: {result.stderr}", "ERROR")
            return None

        # Load and normalize
        with open(temp_geojson, 'r') as f:
            data = json.load(f)

        if 'features' not in data or len(data['features']) == 0:
            log(f"  No features in converted GeoJSON", "WARNING")
            return None

        # Normalize features
        normalized_features = normalize_features(
            data['features'],
            state_upper,
            config['name'],
            id_field,
            name_field
        )

        geojson = create_geojson_output(
            normalized_features,
            state_upper,
            config['name'],
            url
        )

        with open(output_file, 'w') as f:
            json.dump(geojson, f)

        log(f"  Saved {len(normalized_features)} GMUs to {output_file}")

        # Cleanup
        shutil.rmtree(state_temp, ignore_errors=True)

        return str(output_file)

    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        shutil.rmtree(state_temp, ignore_errors=True)
        return None


def normalize_features(
    features: List[Dict],
    state: str,
    agency_name: str,
    id_field: str,
    name_field: str
) -> List[Dict]:
    """
    Normalize feature properties to standard schema:
    - unit_id: GMU identifier
    - unit_name: GMU name (if available)
    - state: 2-letter state code
    - source_agency: State agency name
    """
    normalized = []

    for feature in features:
        props = feature.get('properties', {})

        # Try to find unit ID from configured field or common alternatives
        unit_id = None
        id_fields = [id_field, 'UNIT_ID', 'GMU', 'GMUID', 'UNIT', 'HD_NUM', 'HUNTAREA',
                     'GMU_NO', 'UnitID', 'UNIT_NUM', 'DMU_ID', 'DMU_CODE', 'WMU', 'WMU_ID',
                     'PERMIT_ID', 'NAME', 'Id', 'ID', 'OBJECTID']

        for field in id_fields:
            if field in props and props[field] is not None:
                unit_id = str(props[field])
                break

        # Try to find unit name from configured field or common alternatives
        unit_name = None
        name_fields = [name_field, 'UNIT_NAME', 'GMU_NAME', 'NAME', 'HD_NAME',
                       'UnitName', 'GMULABEL', 'LABEL', 'DMU_NAME', 'WMU_NAME',
                       'PERMIT_NAME', 'Description', 'name']

        for field in name_fields:
            if field in props and props[field] is not None:
                unit_name = str(props[field])
                break

        # Build normalized properties
        new_props = {
            'unit_id': unit_id or 'UNKNOWN',
            'unit_name': unit_name,
            'gmu_number': unit_id or 'UNKNOWN',  # Alias for convenience
            'state': state,
            'source_agency': agency_name,
            'data_type': 'game_management_unit'
        }

        # Preserve original properties for reference (prefixed)
        for key, value in props.items():
            if key not in new_props:
                new_props[f'orig_{key}'] = value

        feature['properties'] = new_props
        normalized.append(feature)

    return normalized


def create_geojson_output(
    features: List[Dict],
    state: str,
    agency_name: str,
    source_url: str
) -> Dict:
    """Create standardized GeoJSON FeatureCollection output"""
    return {
        "type": "FeatureCollection",
        "name": f"Game Management Units - {state}",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": features,
        "metadata": {
            "source": agency_name,
            "download_date": datetime.now().isoformat(),
            "state": state,
            "feature_count": len(features),
            "api_url": source_url,
            "data_type": "game_management_unit",
            "notes": f"GMU boundaries for {state}"
        }
    }


def download_gmu_for_state(state: str) -> Optional[str]:
    """
    Download GMU data for a specific state using the appropriate method
    """
    state_upper = state.upper()

    if state_upper not in STATE_SOURCES:
        log(f"No GMU source configured for {state_upper}", "WARNING")
        return None

    config = STATE_SOURCES[state_upper]
    format_type = config.get('format', 'arcgis_fs')

    log(f"Processing {state_upper}: {config['name']}")
    log(f"  Format: {format_type}")
    log(f"  Notes: {config.get('notes', 'N/A')}")

    if format_type == 'geojson':
        return download_geojson(state_upper, config)
    elif format_type == 'arcgis_fs':
        return download_arcgis_fs(state_upper, config)
    elif format_type == 'shapefile':
        return download_shapefile(state_upper, config)
    elif format_type == 'kml':
        return download_kml(state_upper, config)
    else:
        log(f"  Unknown format type: {format_type}", "ERROR")
        return None


def generate_pmtiles(geojson_path: str, pmtiles_path: Path) -> bool:
    """Generate PMTiles from GeoJSON using tippecanoe"""
    log(f"Generating PMTiles: {geojson_path}")

    # Remove existing file if present (tippecanoe won't overwrite)
    if pmtiles_path.exists():
        pmtiles_path.unlink()

    cmd = [
        "tippecanoe",
        "-z14",           # Max zoom 14
        "-Z4",            # Min zoom 4
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "-l", "gmu",      # Layer name
        "-o", str(pmtiles_path),
        "--force",        # Overwrite if exists
        str(geojson_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if result.returncode == 0:
            log(f"  Generated: {pmtiles_path}")
            return True
        else:
            log(f"  tippecanoe error: {result.stderr}", "ERROR")
            return False
    except FileNotFoundError:
        log("  tippecanoe not found. Install with: brew install tippecanoe or apt install tippecanoe", "ERROR")
        return False
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return False


def upload_to_r2(local_path: str, r2_key: str) -> Optional[str]:
    """Upload file to Cloudflare R2"""
    try:
        import boto3
    except ImportError:
        log("  boto3 not installed. Install with: pip install boto3", "ERROR")
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
        if local_path.endswith('.geojson'):
            content_type = 'application/geo+json'
        elif local_path.endswith('.pmtiles'):
            content_type = 'application/x-protobuf'
        else:
            content_type = 'application/octet-stream'

        file_size = os.path.getsize(local_path) / (1024 * 1024)
        log(f"  Uploading {file_size:.1f}MB...")

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


def cleanup_local(path: str) -> None:
    """Remove local file after upload"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            log(f"  Removed: {path}")
    except Exception as e:
        log(f"  Cleanup error: {e}", "WARNING")


def list_available_states() -> None:
    """Print list of available state configurations"""
    log("Available State GMU Sources:")
    log("=" * 70)

    for state, config in sorted(STATE_SOURCES.items()):
        log(f"  {state}: {config['name']}")
        log(f"       Format: {config['format']}")
        log(f"       Notes: {config.get('notes', 'N/A')}")
        log("")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Download State Game Management Unit (GMU) Boundaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download GMU data for specific states
  python3 download_gmu.py --state CO,MT,AZ

  # Download all configured states
  python3 download_gmu.py --all

  # Full pipeline with PMTiles and upload
  python3 download_gmu.py --state CO --pmtiles --upload

  # Download, generate PMTiles, upload, then cleanup local files
  python3 download_gmu.py --state CO,MT --pmtiles --upload --cleanup

  # List all available state configurations
  python3 download_gmu.py --list-states

Priority States (cleanest data):
  CO - Colorado (direct GeoJSON)
  MT - Montana (Shapefile)
  AZ - Arizona (ArcGIS Feature Service)
  WY - Wyoming (ArcGIS Feature Service)

Note: Shapefile/KML conversion requires GDAL (ogr2ogr).
      PMTiles generation requires tippecanoe.
        """
    )

    parser.add_argument("--state", "-s",
                        help="State abbreviation(s), comma-separated (e.g., CO,MT,AZ)")
    parser.add_argument("--all", action="store_true",
                        help="Download all configured states")
    parser.add_argument("--pmtiles", action="store_true",
                        help="Generate PMTiles from GeoJSON")
    parser.add_argument("--upload", action="store_true",
                        help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true",
                        help="Remove local files after successful upload")
    parser.add_argument("--list-states", action="store_true",
                        help="List all available state configurations")

    args = parser.parse_args()

    # Handle list states
    if args.list_states:
        list_available_states()
        return

    # Validate arguments
    if not args.state and not args.all:
        parser.print_help()
        return

    ensure_directories()

    # Determine states to process
    if args.all:
        states = list(STATE_SOURCES.keys())
    else:
        states = [s.strip().upper() for s in args.state.split(",")]

    log("=" * 70)
    log("GMU Download Pipeline")
    log("=" * 70)
    log(f"Processing {len(states)} states: {', '.join(states)}")
    log(f"Options: pmtiles={args.pmtiles}, upload={args.upload}, cleanup={args.cleanup}")
    log("=" * 70)

    results = {
        "success": [],
        "failed": [],
        "skipped": []
    }

    for state in states:
        log("")
        log("=" * 60)
        log(f"Processing: {state}")
        log("=" * 60)

        if state not in STATE_SOURCES:
            log(f"  No configuration for {state}", "WARNING")
            results["skipped"].append(state)
            continue

        # Download GeoJSON
        geojson_path = download_gmu_for_state(state)

        if not geojson_path:
            results["failed"].append(state)
            continue

        files_to_upload = [geojson_path]

        # Generate PMTiles
        if args.pmtiles:
            pmtiles_name = f"gmu_{state.lower()}.pmtiles"
            pmtiles_path = PMTILES_DIR / pmtiles_name

            if generate_pmtiles(geojson_path, pmtiles_path):
                files_to_upload.append(str(pmtiles_path))

        # Upload to R2
        if args.upload:
            for file_path in files_to_upload:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    r2_key = f"enrichment/gmu/{filename}"
                    upload_to_r2(file_path, r2_key)

        # Cleanup
        if args.cleanup and args.upload:
            for file_path in files_to_upload:
                if os.path.exists(file_path):
                    cleanup_local(file_path)

        results["success"].append(state)

    # Summary
    log("")
    log("=" * 70)
    log("GMU Download Complete!")
    log("=" * 70)
    log(f"Success: {len(results['success'])} - {', '.join(results['success']) or 'None'}")
    log(f"Failed:  {len(results['failed'])} - {', '.join(results['failed']) or 'None'}")
    log(f"Skipped: {len(results['skipped'])} - {', '.join(results['skipped']) or 'None'}")
    log("")

    if results["success"]:
        log("Output files:")
        for state in results["success"]:
            geojson_file = GEOJSON_DIR / f"gmu_{state.lower()}.geojson"
            if geojson_file.exists():
                log(f"  GeoJSON: {geojson_file}")
            pmtiles_file = PMTILES_DIR / f"gmu_{state.lower()}.pmtiles"
            if pmtiles_file.exists():
                log(f"  PMTiles: {pmtiles_file}")

        if args.upload:
            log("")
            log("R2 URLs:")
            for state in results["success"]:
                log(f"  https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/enrichment/gmu/gmu_{state.lower()}.geojson")
                if args.pmtiles:
                    log(f"  https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/enrichment/gmu/gmu_{state.lower()}.pmtiles")


if __name__ == "__main__":
    main()
