#!/usr/bin/env python3
"""
Download USDA Cropland Data Layer (CDL) from CropScape

Priority: 3
Source: USDA National Agricultural Statistics Service (NASS)
URL: https://nassgeodata.gmu.edu/CropScape/

CropScape/CDL data is valuable for hunting because:
- Corn (1): Deer, waterfowl, dove food plots
- Soybeans (5): Deer, dove staging areas
- Winter Wheat (24): Dove, deer browse
- Alfalfa (36): Deer feeding areas
- Fallow/Idle (61): Dove, quail habitat
- Grassland/Pasture (176): Quail, deer bedding areas

Update Frequency: Annual (typically February/March for prior year)
Current Version: 2024 (2023 data available)
Date Added: 2026-01-13

Note: CDL is raster data. This script converts hunting-relevant crop
classes to vector polygons for efficient map overlay display.
"""

import os
import sys
import json
import shutil
import subprocess
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List, Dict

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
RASTER_DIR = OUTPUT_DIR / "raster" / "cropscape"
VECTOR_DIR = OUTPUT_DIR / "vector" / "cropscape"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# CropScape CDLService endpoint (working as of 2026)
# This SOAP service returns XML with a returnURL to the actual TIF file
CDL_SERVICE_URL = "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLFile"

# Direct download URL pattern for state-level CDL TIF files
# The returnURL from CDLService points to files like:
# https://nassgeodata.gmu.edu/webservice/nass_data_cache/byfips/CDL_2023_{FIPS}.tif
CDL_CACHE_BASE = "https://nassgeodata.gmu.edu/webservice/nass_data_cache/byfips"

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

# Hunting-relevant CDL crop codes
HUNTING_CROPS = {
    1: {
        "name": "Corn",
        "category": "row_crop",
        "hunting_value": "Deer, waterfowl, dove - primary food source",
        "color": "#FFD400"
    },
    5: {
        "name": "Soybeans",
        "category": "row_crop",
        "hunting_value": "Deer, dove - high protein browse",
        "color": "#267000"
    },
    24: {
        "name": "Winter Wheat",
        "category": "small_grain",
        "hunting_value": "Dove, deer - green browse and waste grain",
        "color": "#A57000"
    },
    36: {
        "name": "Alfalfa",
        "category": "hay",
        "hunting_value": "Deer - preferred feeding, high nutrition",
        "color": "#E2007C"
    },
    61: {
        "name": "Fallow/Idle Cropland",
        "category": "fallow",
        "hunting_value": "Dove, quail - weed seeds and cover",
        "color": "#7C7067"
    },
    176: {
        "name": "Grassland/Pasture",
        "category": "grassland",
        "hunting_value": "Quail, deer bedding - cover and browse",
        "color": "#E8D6AF"
    }
}

# Additional useful crops (optional expansion)
EXTENDED_CROPS = {
    4: {"name": "Sorghum", "hunting_value": "Dove, deer, quail"},
    21: {"name": "Barley", "hunting_value": "Dove"},
    23: {"name": "Spring Wheat", "hunting_value": "Dove, deer"},
    26: {"name": "Dbl Crop WinWht/Soybeans", "hunting_value": "Deer, dove"},
    27: {"name": "Rye", "hunting_value": "Deer browse"},
    28: {"name": "Oats", "hunting_value": "Deer, dove"},
    29: {"name": "Millet", "hunting_value": "Dove, quail"},
    37: {"name": "Other Hay/Non Alfalfa", "hunting_value": "Deer"},
    58: {"name": "Clover/Wildflowers", "hunting_value": "Deer, quail"},
    59: {"name": "Sod/Grass Seed", "hunting_value": "Geese"},
    152: {"name": "Shrubland", "hunting_value": "Deer, quail cover"},
    190: {"name": "Woody Wetlands", "hunting_value": "Waterfowl, deer"},
    195: {"name": "Herbaceous Wetlands", "hunting_value": "Waterfowl"}
}

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

# State names for display
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


def log(message: str, level: str = "INFO") -> None:
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories() -> None:
    """Create necessary directories"""
    for dir_path in [RASTER_DIR, VECTOR_DIR, GEOJSON_DIR, PMTILES_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def check_gdal_installed() -> bool:
    """Check if GDAL tools are installed"""
    try:
        result = subprocess.run(["gdal_polygonize.py", "--version"],
                              capture_output=True, text=True)
        return True
    except FileNotFoundError:
        try:
            # Try alternate location
            result = subprocess.run(["python3", "-c", "from osgeo import gdal; print(gdal.__version__)"],
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False


def check_tippecanoe_installed() -> bool:
    """Check if tippecanoe is installed"""
    try:
        result = subprocess.run(["tippecanoe", "--version"],
                              capture_output=True, text=True)
        return True
    except FileNotFoundError:
        return False


def download_cdl_via_cdlservice(state: str, year: int, output_path: Path) -> Optional[str]:
    """
    Download CDL raster data via CDLService SOAP API (working as of 2026)

    This is the primary and most reliable method for downloading state-level CDL data.
    The API returns XML with a returnURL containing the actual download link.

    Endpoint: https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLFile
    Parameters: year={year}&fips={FIPS_CODE}
    Returns XML with: <returnURL>https://nassgeodata.gmu.edu/webservice/nass_data_cache/byfips/CDL_{year}_{FIPS}.tif</returnURL>
    """
    state_upper = state.upper()
    fips = get_state_fips(state_upper)

    if fips == "00":
        log(f"Unknown state: {state_upper}", "ERROR")
        return None

    log(f"Downloading CDL {year} for {state_upper} (FIPS: {fips}) via CDLService...")

    # Build CDLService request URL
    api_url = f"{CDL_SERVICE_URL}?year={year}&fips={fips}"
    log(f"  API URL: {api_url}")

    try:
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

        with urllib.request.urlopen(req, timeout=60) as response:
            xml_data = response.read().decode('utf-8')
            log(f"  Got XML response ({len(xml_data)} bytes)")

            # Parse XML to extract returnURL
            # Response format: <GetCDLFileResponse><returnURL>...</returnURL></GetCDLFileResponse>
            download_url = None

            # Try XML parsing first
            try:
                root = ET.fromstring(xml_data)
                # Find returnURL element (may be namespaced)
                for elem in root.iter():
                    if 'returnURL' in elem.tag or elem.tag == 'returnURL':
                        download_url = elem.text
                        break
            except ET.ParseError:
                log("  XML parsing failed, trying regex...", "WARNING")

            # Fallback to regex if XML parsing didn't work
            if not download_url:
                match = re.search(r'<returnURL[^>]*>([^<]+)</returnURL>', xml_data)
                if match:
                    download_url = match.group(1).strip()
                else:
                    # Try finding any URL in the response
                    url_match = re.search(r'(https?://[^\s<>"]+\.tif)', xml_data)
                    if url_match:
                        download_url = url_match.group(1)

            if download_url and download_url.startswith('http'):
                log(f"  Found download URL: {download_url}")
                return download_file(download_url, output_path)
            else:
                log(f"  No download URL found in response", "ERROR")
                log(f"  Response snippet: {xml_data[:500]}", "DEBUG")
                return None

    except urllib.error.HTTPError as e:
        log(f"  HTTP Error {e.code}: {e.reason}", "ERROR")
        return None
    except urllib.error.URLError as e:
        log(f"  URL Error: {e.reason}", "ERROR")
        return None
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def download_cdl_direct_url(state: str, year: int, output_path: Path) -> Optional[str]:
    """
    Download CDL directly using known URL pattern (fallback method)

    The CDL files are cached at a predictable URL pattern:
    https://nassgeodata.gmu.edu/webservice/nass_data_cache/byfips/CDL_{year}_{FIPS}.tif
    """
    state_upper = state.upper()
    fips = get_state_fips(state_upper)

    if fips == "00":
        log(f"Unknown state: {state_upper}", "ERROR")
        return None

    log(f"Attempting direct CDL download for {state_upper} (FIPS: {fips})...")

    # Build direct download URL
    download_url = f"{CDL_CACHE_BASE}/CDL_{year}_{fips}.tif"
    log(f"  Direct URL: {download_url}")

    return download_file(download_url, output_path)




def get_state_fips(state: str) -> str:
    """Get FIPS code for state"""
    fips_codes = {
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
    return fips_codes.get(state.upper(), "00")


def download_file(url: str, dest_path: Path) -> Optional[str]:
    """Download a file with progress indication"""
    log(f"  Downloading: {url[:80]}...")

    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

        with urllib.request.urlopen(req, timeout=600) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            block_size = 1024 * 1024

            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        print(f"\r  Progress: {downloaded / (1024*1024):.1f}MB ({pct:.1f}%)", end="")

            print()
            log(f"  Saved: {dest_path}")
            return str(dest_path)

    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None




def filter_hunting_crops(raster_path: str, output_path: str,
                         include_extended: bool = False) -> Optional[str]:
    """
    Filter raster to only include hunting-relevant crop codes

    Uses GDAL to reclassify raster, setting non-hunting crops to NoData.
    """
    log(f"Filtering to hunting-relevant crops...")

    # Get crop codes to keep
    codes_to_keep = list(HUNTING_CROPS.keys())
    if include_extended:
        codes_to_keep.extend(EXTENDED_CROPS.keys())

    codes_str = ",".join(str(c) for c in sorted(set(codes_to_keep)))
    log(f"  Keeping crop codes: {codes_str}")

    # Use gdal_calc.py to filter
    # Set all values not in our list to 0 (NoData)
    calc_expression = " + ".join([f"(A=={c})*{c}" for c in codes_to_keep])

    cmd = [
        "gdal_calc.py",
        "-A", raster_path,
        f"--outfile={output_path}",
        f"--calc={calc_expression}",
        "--NoDataValue=0",
        "--type=Byte",
        "--overwrite"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        if result.returncode == 0:
            log(f"  Filtered raster: {output_path}")
            return output_path
        else:
            log(f"  gdal_calc error: {result.stderr}", "ERROR")
            # Fall back to simpler approach using gdal_translate with value filtering
            return filter_hunting_crops_simple(raster_path, output_path, codes_to_keep)
    except FileNotFoundError:
        log("  gdal_calc.py not found, trying simple filter...", "WARNING")
        return filter_hunting_crops_simple(raster_path, output_path, codes_to_keep)
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def filter_hunting_crops_simple(raster_path: str, output_path: str,
                                 codes_to_keep: List[int]) -> Optional[str]:
    """
    Simple raster filtering using numpy and rasterio

    Fallback when gdal_calc is not available.
    """
    try:
        import rasterio
        import numpy as np
    except ImportError:
        log("  rasterio not installed. Install with: pip install rasterio", "ERROR")
        # Just copy the file as-is and proceed
        shutil.copy(raster_path, output_path)
        return output_path

    log(f"  Using rasterio for filtering...")

    try:
        with rasterio.open(raster_path) as src:
            data = src.read(1)
            profile = src.profile

            # Create mask for hunting crops
            mask = np.isin(data, codes_to_keep)

            # Set non-hunting crops to 0 (NoData)
            filtered = np.where(mask, data, 0)

            # Update profile
            profile.update(dtype=rasterio.uint8, nodata=0)

            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(filtered.astype(rasterio.uint8), 1)

        log(f"  Filtered raster: {output_path}")
        return output_path

    except Exception as e:
        log(f"  Filter error: {e}", "ERROR")
        return None


def raster_to_vector(raster_path: str, vector_path: str,
                     simplify_tolerance: float = 0.0005) -> Optional[str]:
    """
    Convert raster to simplified vector polygons

    Uses gdal_polygonize followed by ogr2ogr for simplification.
    This creates clean polygons suitable for map display.
    """
    log(f"Converting raster to vector polygons...")

    # Intermediate shapefile
    temp_shp = vector_path.replace('.geojson', '_raw.shp')

    # Step 1: Polygonize
    cmd_polygonize = [
        "gdal_polygonize.py",
        raster_path,
        "-f", "ESRI Shapefile",
        temp_shp,
        "cropscape",
        "crop_code"
    ]

    try:
        result = subprocess.run(cmd_polygonize, capture_output=True, text=True, timeout=3600)
        if result.returncode != 0:
            log(f"  Polygonize error: {result.stderr}", "ERROR")
            return None

        log(f"  Polygonized to shapefile")

    except FileNotFoundError:
        log("  gdal_polygonize.py not found. Install GDAL: sudo apt-get install gdal-bin python3-gdal", "ERROR")
        return None
    except subprocess.TimeoutExpired:
        log("  Polygonization timed out", "ERROR")
        return None

    # Step 2: Simplify and convert to GeoJSON
    cmd_simplify = [
        "ogr2ogr",
        "-f", "GeoJSON",
        "-t_srs", "EPSG:4326",
        "-simplify", str(simplify_tolerance),
        "-where", "crop_code > 0",  # Exclude NoData
        vector_path,
        temp_shp
    ]

    try:
        result = subprocess.run(cmd_simplify, capture_output=True, text=True, timeout=1800)
        if result.returncode != 0:
            log(f"  Simplify error: {result.stderr}", "ERROR")
            return None

        log(f"  Simplified to GeoJSON: {vector_path}")

        # Cleanup temp shapefile
        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
            temp_file = temp_shp.replace('.shp', ext)
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return vector_path

    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def add_crop_attributes(geojson_path: str) -> Optional[str]:
    """
    Add human-readable crop attributes to GeoJSON features

    Enhances the output with crop names, categories, and hunting value.
    """
    log(f"Adding crop attributes...")

    try:
        with open(geojson_path, 'r') as f:
            data = json.load(f)

        all_crops = {**HUNTING_CROPS, **EXTENDED_CROPS}
        feature_count = 0

        for feature in data.get('features', []):
            props = feature.get('properties', {})
            crop_code = props.get('crop_code') or props.get('DN')  # Different field names possible

            if crop_code and crop_code in all_crops:
                crop_info = all_crops[crop_code]
                props['crop_name'] = crop_info['name']
                props['crop_category'] = crop_info.get('category', 'unknown')
                props['hunting_value'] = crop_info.get('hunting_value', '')
                props['crop_color'] = crop_info.get('color', '#888888')
                feature_count += 1

            feature['properties'] = props

        # Add metadata
        data['metadata'] = {
            "source": "USDA NASS Cropland Data Layer (CDL)",
            "processed_date": datetime.now().isoformat(),
            "crop_types_included": list(HUNTING_CROPS.keys()),
            "feature_count": feature_count
        }

        with open(geojson_path, 'w') as f:
            json.dump(data, f)

        log(f"  Enhanced {feature_count} features with crop attributes")
        return geojson_path

    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def generate_pmtiles(geojson_path: str, pmtiles_path: str) -> bool:
    """
    Generate PMTiles from GeoJSON using tippecanoe
    """
    log(f"Generating PMTiles: {pmtiles_path}")

    cmd = [
        "tippecanoe",
        "-z14",          # Max zoom
        "-Z6",           # Min zoom (crops visible at regional level)
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "--coalesce-densest-as-needed",
        "-l", "cropscape",
        "--force",       # Overwrite existing
        "-o", pmtiles_path,
        geojson_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if result.returncode == 0:
            size_mb = os.path.getsize(pmtiles_path) / (1024 * 1024)
            log(f"  Generated: {pmtiles_path} ({size_mb:.1f}MB)")
            return True
        else:
            log(f"  tippecanoe error: {result.stderr}", "ERROR")
            return False
    except FileNotFoundError:
        log("  tippecanoe not found. Install from: https://github.com/felt/tippecanoe", "ERROR")
        return False
    except subprocess.TimeoutExpired:
        log("  PMTiles generation timed out", "ERROR")
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
        elif local_path.endswith('.tif') or local_path.endswith('.tiff'):
            content_type = 'image/tiff'
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


def cleanup_local(*paths: str) -> None:
    """Remove local files after successful upload"""
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


def process_state(state: str, year: int,
                  generate_tiles: bool = False,
                  upload: bool = False,
                  cleanup: bool = False,
                  include_extended: bool = False) -> bool:
    """
    Process CDL data for a single state

    Pipeline:
    1. Download CDL raster
    2. Filter to hunting-relevant crops
    3. Convert to vector polygons
    4. Add crop attributes
    5. Generate PMTiles (optional)
    6. Upload to R2 (optional)
    7. Cleanup local files (optional)
    """
    state_upper = state.upper()
    state_name = STATE_NAMES.get(state_upper, state_upper)

    log("=" * 60)
    log(f"Processing: {state_name} ({state_upper}) - CDL {year}")
    log("=" * 60)

    # File paths
    raster_raw = RASTER_DIR / f"cdl_{state_upper.lower()}_{year}_raw.tif"
    raster_filtered = RASTER_DIR / f"cdl_{state_upper.lower()}_{year}_hunting.tif"
    vector_path = GEOJSON_DIR / f"cropscape_{state_upper.lower()}.geojson"
    pmtiles_path = PMTILES_DIR / f"cropscape_{state_upper.lower()}.pmtiles"

    # Step 1: Download CDL raster
    if not raster_raw.exists():
        # Try CDLService SOAP API first (most reliable as of 2026)
        result = download_cdl_via_cdlservice(state_upper, year, raster_raw)

        if not result:
            # Try direct URL pattern as fallback
            result = download_cdl_direct_url(state_upper, year, raster_raw)

        if not result:
            log(f"Failed to download CDL for {state_upper}", "ERROR")
            return False
    else:
        log(f"Using existing raster: {raster_raw}")

    # Step 2: Filter to hunting crops
    if not raster_filtered.exists():
        result = filter_hunting_crops(str(raster_raw), str(raster_filtered), include_extended)
        if not result:
            log(f"Failed to filter crops for {state_upper}", "ERROR")
            return False
    else:
        log(f"Using existing filtered raster: {raster_filtered}")

    # Step 3: Convert to vector
    if not vector_path.exists():
        result = raster_to_vector(str(raster_filtered), str(vector_path))
        if not result:
            log(f"Failed to vectorize for {state_upper}", "ERROR")
            return False

        # Step 4: Add crop attributes
        add_crop_attributes(str(vector_path))
    else:
        log(f"Using existing vector: {vector_path}")

    # Step 5: Generate PMTiles
    if generate_tiles:
        if not pmtiles_path.exists():
            if not generate_pmtiles(str(vector_path), str(pmtiles_path)):
                log(f"Failed to generate PMTiles for {state_upper}", "WARNING")
        else:
            log(f"Using existing PMTiles: {pmtiles_path}")

    # Step 6: Upload to R2
    if upload:
        # Upload PMTiles (primary output)
        if generate_tiles and pmtiles_path.exists():
            r2_key = f"enrichment/cropscape/cropscape_{state_upper.lower()}.pmtiles"
            upload_to_r2(str(pmtiles_path), r2_key)

        # Also upload GeoJSON for reference/debugging
        if vector_path.exists():
            r2_key = f"enrichment/cropscape/cropscape_{state_upper.lower()}.geojson"
            upload_to_r2(str(vector_path), r2_key)

    # Step 7: Cleanup
    if cleanup and upload:
        files_to_clean = [str(raster_raw), str(raster_filtered)]
        if generate_tiles:
            files_to_clean.append(str(vector_path))
            files_to_clean.append(str(pmtiles_path))
        cleanup_local(*files_to_clean)

    log(f"Completed: {state_upper}")
    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Download USDA Cropland Data Layer (CDL) from CropScape",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download and process CDL for a specific state
  python3 download_cropscape.py --state TX --year 2023

  # Process multiple states
  python3 download_cropscape.py --state TX,OK,KS --year 2023

  # Full pipeline: download, generate PMTiles, upload to R2
  python3 download_cropscape.py --state TX --year 2023 --pmtiles --upload

  # Full pipeline with cleanup
  python3 download_cropscape.py --state TX --year 2023 --pmtiles --upload --cleanup

  # Include extended crop types (more hunting habitats)
  python3 download_cropscape.py --state TX --year 2023 --extended

  # List available crop codes
  python3 download_cropscape.py --list-crops

Hunting-Relevant Crops (default):
  1   - Corn: Deer, waterfowl, dove food plots
  5   - Soybeans: Deer, dove staging areas
  24  - Winter Wheat: Dove, deer browse
  36  - Alfalfa: Deer feeding areas
  61  - Fallow/Idle: Dove, quail habitat
  176 - Grassland/Pasture: Quail, deer bedding

Output:
  PMTiles: enrichment/cropscape/cropscape_{state}.pmtiles
  GeoJSON: enrichment/cropscape/cropscape_{state}.geojson
        """
    )

    parser.add_argument("--state", "-s",
                        help="State abbreviation(s), comma-separated (e.g., TX,OK,KS)")
    parser.add_argument("--year", "-y", type=int, default=2023,
                        help="CDL data year (default: 2023)")
    parser.add_argument("--pmtiles", action="store_true",
                        help="Generate PMTiles for map display")
    parser.add_argument("--upload", action="store_true",
                        help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true",
                        help="Remove local files after successful upload")
    parser.add_argument("--extended", action="store_true",
                        help="Include extended crop types (sorghum, wetlands, etc.)")
    parser.add_argument("--list-crops", action="store_true",
                        help="List hunting-relevant crop codes")
    parser.add_argument("--all-states", action="store_true",
                        help="Process all US states")
    parser.add_argument("--force", action="store_true",
                        help="Force re-download even if files exist")

    args = parser.parse_args()

    # Ensure directories exist
    ensure_directories()

    # List crops
    if args.list_crops:
        log("Hunting-Relevant Crop Codes (Primary):")
        log("-" * 50)
        for code, info in sorted(HUNTING_CROPS.items()):
            log(f"  {code:3d}: {info['name']}")
            log(f"       Hunting: {info['hunting_value']}")

        log("")
        log("Extended Crop Codes (Optional):")
        log("-" * 50)
        for code, info in sorted(EXTENDED_CROPS.items()):
            log(f"  {code:3d}: {info['name']}")
            log(f"       Hunting: {info['hunting_value']}")
        return

    # Check dependencies
    if not check_gdal_installed():
        log("WARNING: GDAL not fully installed. Some features may not work.", "WARNING")
        log("  Install with: sudo apt-get install gdal-bin python3-gdal")

    if args.pmtiles and not check_tippecanoe_installed():
        log("ERROR: tippecanoe not installed but --pmtiles requested", "ERROR")
        log("  Install from: https://github.com/felt/tippecanoe")
        return

    # Get states to process
    states = []
    if args.state:
        states = [s.strip().upper() for s in args.state.split(",")]
    elif args.all_states:
        states = list(STATE_BBOX.keys())
    else:
        parser.print_help()
        return

    # Validate states
    invalid_states = [s for s in states if s not in STATE_BBOX]
    if invalid_states:
        log(f"Unknown states: {', '.join(invalid_states)}", "ERROR")
        log(f"Valid states: {', '.join(sorted(STATE_BBOX.keys()))}")
        return

    log(f"Processing {len(states)} state(s): {', '.join(states)}")
    log(f"CDL Year: {args.year}")
    log(f"Generate PMTiles: {args.pmtiles}")
    log(f"Upload to R2: {args.upload}")
    log(f"Extended crops: {args.extended}")

    # Process each state
    success_count = 0
    failed_states = []

    for state in states:
        try:
            if process_state(
                state=state,
                year=args.year,
                generate_tiles=args.pmtiles,
                upload=args.upload,
                cleanup=args.cleanup,
                include_extended=args.extended
            ):
                success_count += 1
            else:
                failed_states.append(state)
        except Exception as e:
            log(f"Error processing {state}: {e}", "ERROR")
            failed_states.append(state)

    # Summary
    log("")
    log("=" * 60)
    log("CropScape Download Summary")
    log("=" * 60)
    log(f"  States processed: {success_count}/{len(states)}")
    if failed_states:
        log(f"  Failed states: {', '.join(failed_states)}")
    if args.upload:
        log(f"  R2 location: {R2_PUBLIC_URL}/enrichment/cropscape/")
    log("=" * 60)


if __name__ == "__main__":
    main()
