#!/usr/bin/env python3
"""
Download USGS 3DEP Digital Elevation Model (DEM) Data

Priority: 9
Source: USGS 3D Elevation Program (3DEP)
URL: https://www.usgs.gov/3d-elevation-program
API: https://tnmaccess.nationalmap.gov/api/v1/products

Downloads elevation data for terrain analysis including:
- 1/3 arc-second (~10m) resolution DEMs
- 1 arc-second (~30m) resolution DEMs
- Seamless DEM products for any area

Use this script to download DEM data before running terrain_analysis.py

Update Frequency: Continuous updates as new LiDAR collected
Date Added: 2026-01-13
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import argparse
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
DEM_DIR = OUTPUT_DIR / "dem"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# USGS TNM API
TNM_API_BASE = "https://tnmaccess.nationalmap.gov/api/v1/products"

# State bounding boxes (approximate)
STATE_BBOXES = {
    "AL": (-88.5, 30.2, -84.9, 35.0),
    "AK": (-179.2, 51.2, -129.98, 71.4),
    "AZ": (-114.8, 31.3, -109.0, 37.0),
    "AR": (-94.6, 33.0, -89.6, 36.5),
    "CA": (-124.4, 32.5, -114.1, 42.0),
    "CO": (-109.1, 36.99, -102.0, 41.0),
    "CT": (-73.7, 40.95, -71.8, 42.1),
    "DE": (-75.8, 38.45, -75.0, 39.85),
    "FL": (-87.6, 24.5, -80.0, 31.0),
    "GA": (-85.6, 30.4, -80.8, 35.0),
    "HI": (-160.3, 18.9, -154.8, 22.2),
    "ID": (-117.2, 42.0, -111.0, 49.0),
    "IL": (-91.5, 37.0, -87.5, 42.5),
    "IN": (-88.1, 37.8, -84.8, 41.8),
    "IA": (-96.6, 40.4, -90.1, 43.5),
    "KS": (-102.1, 37.0, -94.6, 40.0),
    "KY": (-89.6, 36.5, -81.95, 39.15),
    "LA": (-94.0, 29.0, -89.0, 33.0),
    "ME": (-71.1, 43.0, -66.95, 47.5),
    "MD": (-79.5, 37.9, -75.0, 39.7),
    "MA": (-73.5, 41.2, -69.9, 42.9),
    "MI": (-90.4, 41.7, -82.4, 48.2),
    "MN": (-97.2, 43.5, -89.5, 49.4),
    "MS": (-91.7, 30.2, -88.1, 35.0),
    "MO": (-95.8, 36.0, -89.1, 40.6),
    "MT": (-116.1, 44.4, -104.0, 49.0),
    "NE": (-104.1, 40.0, -95.3, 43.0),
    "NV": (-120.0, 35.0, -114.0, 42.0),
    "NH": (-72.6, 42.7, -70.7, 45.3),
    "NJ": (-75.6, 38.9, -73.9, 41.4),
    "NM": (-109.1, 31.3, -103.0, 37.0),
    "NY": (-79.8, 40.5, -71.9, 45.0),
    "NC": (-84.3, 33.85, -75.5, 36.6),
    "ND": (-104.1, 45.9, -96.6, 49.0),
    "OH": (-84.8, 38.4, -80.5, 42.0),
    "OK": (-103.0, 33.6, -94.4, 37.0),
    "OR": (-124.6, 41.99, -116.5, 46.3),
    "PA": (-80.5, 39.7, -74.7, 42.3),
    "RI": (-71.9, 41.1, -71.1, 42.0),
    "SC": (-83.4, 32.0, -78.5, 35.2),
    "SD": (-104.1, 42.5, -96.4, 45.95),
    "TN": (-90.3, 35.0, -81.65, 36.7),
    "TX": (-106.65, 25.8, -93.5, 36.5),
    "UT": (-114.1, 37.0, -109.0, 42.0),
    "VT": (-73.4, 42.7, -71.5, 45.0),
    "VA": (-83.7, 36.5, -75.2, 39.5),
    "WA": (-124.8, 45.5, -116.9, 49.0),
    "WV": (-82.7, 37.2, -77.7, 40.6),
    "WI": (-92.9, 42.5, -86.8, 47.1),
    "WY": (-111.1, 41.0, -104.1, 45.0)
}

# 3DEP Product Types
DEM_PRODUCTS = {
    "1/3 arc-second": {
        "datasets": "National Elevation Dataset (NED) 1/3 arc-second",
        "resolution": "~10m",
        "description": "High resolution DEM from NED",
        "format": "GeoTIFF"
    },
    "1 arc-second": {
        "datasets": "National Elevation Dataset (NED) 1 arc-second",
        "resolution": "~30m",
        "description": "Standard resolution DEM from NED",
        "format": "GeoTIFF"
    },
    "3DEP 1/3 arc-second": {
        "datasets": "Digital Elevation Model (DEM) 1 meter",
        "resolution": "~10m",
        "description": "3DEP elevation products",
        "format": "GeoTIFF"
    }
}


def log(message: str, level: str = "INFO") -> None:
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories() -> None:
    """Create necessary directories"""
    for dir_path in [DEM_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def query_tnm_api(
    bbox: Tuple[float, float, float, float],
    datasets: str = "National Elevation Dataset (NED) 1/3 arc-second",
    max_results: int = 100
) -> List[Dict]:
    """
    Query USGS TNM API for elevation products

    Args:
        bbox: (minx, miny, maxx, maxy) bounding box in WGS84
        datasets: Dataset type to search
        max_results: Maximum number of results

    Returns:
        List of product dictionaries
    """
    log(f"Querying TNM API for: {datasets}")
    log(f"  Bounding box: {bbox}")

    params = {
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
        "datasets": datasets,
        "max": max_results,
        "outputFormat": "JSON"
    }

    url = f"{TNM_API_BASE}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode())

        items = data.get("items", [])
        log(f"  Found {len(items)} products")

        return items

    except urllib.error.HTTPError as e:
        log(f"  HTTP Error: {e.code} - {e.reason}", "ERROR")
        return []
    except urllib.error.URLError as e:
        log(f"  URL Error: {e.reason}", "ERROR")
        return []
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return []


def search_elevation_products(
    bbox: Tuple[float, float, float, float] = None,
    state: str = None,
    resolution: str = "1/3 arc-second"
) -> List[Dict]:
    """
    Search for available elevation products

    Args:
        bbox: Bounding box (minx, miny, maxx, maxy)
        state: State abbreviation (uses state bbox if no bbox provided)
        resolution: "1/3 arc-second" (~10m) or "1 arc-second" (~30m)

    Returns:
        List of available products
    """
    if bbox is None and state:
        bbox = STATE_BBOXES.get(state.upper())
        if bbox is None:
            log(f"Unknown state: {state}", "ERROR")
            return []

    if bbox is None:
        log("Please provide --bbox or --state", "ERROR")
        return []

    # Map resolution to dataset name
    if "1/3" in resolution:
        datasets = "National Elevation Dataset (NED) 1/3 arc-second"
    else:
        datasets = "National Elevation Dataset (NED) 1 arc-second"

    products = query_tnm_api(bbox, datasets)

    return products


def download_dem(
    url: str,
    output_path: str,
    extract: bool = True
) -> Optional[str]:
    """
    Download DEM file from USGS

    Args:
        url: Download URL
        output_path: Output file path
        extract: Extract ZIP files

    Returns:
        Path to downloaded/extracted file
    """
    log(f"Downloading: {os.path.basename(url)}")
    log(f"  From: {url}")

    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

        # Download to temp file first
        temp_path = output_path + ".download"

        with urllib.request.urlopen(req, timeout=300) as response:
            file_size = response.headers.get('Content-Length')
            if file_size:
                file_size = int(file_size) / (1024 * 1024)
                log(f"  Size: {file_size:.1f} MB")

            with open(temp_path, 'wb') as f:
                block_size = 8192
                downloaded = 0
                while True:
                    block = response.read(block_size)
                    if not block:
                        break
                    f.write(block)
                    downloaded += len(block)

        # Rename to final path
        os.rename(temp_path, output_path)
        log(f"  Saved: {output_path}")

        # Extract if ZIP
        if extract and output_path.endswith('.zip'):
            extract_dir = os.path.dirname(output_path)
            log(f"  Extracting to: {extract_dir}")

            with zipfile.ZipFile(output_path, 'r') as zf:
                # Find the GeoTIFF file
                tif_files = [n for n in zf.namelist() if n.endswith('.tif') or n.endswith('.tiff')]
                if tif_files:
                    for tif_name in tif_files:
                        zf.extract(tif_name, extract_dir)
                        extracted_path = os.path.join(extract_dir, tif_name)
                        log(f"  Extracted: {extracted_path}")
                        return extracted_path
                else:
                    # Extract all
                    zf.extractall(extract_dir)
                    log(f"  Extracted all files")

            return output_path

        return output_path

    except urllib.error.HTTPError as e:
        log(f"  HTTP Error: {e.code} - {e.reason}", "ERROR")
        return None
    except urllib.error.URLError as e:
        log(f"  URL Error: {e.reason}", "ERROR")
        return None
    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def download_dem_for_bbox(
    bbox: Tuple[float, float, float, float],
    output_dir: Path = None,
    resolution: str = "1/3 arc-second",
    state: str = None
) -> List[str]:
    """
    Download all DEM tiles covering a bounding box

    Args:
        bbox: (minx, miny, maxx, maxy) in WGS84
        output_dir: Output directory
        resolution: DEM resolution
        state: State abbreviation for naming

    Returns:
        List of downloaded file paths
    """
    if output_dir is None:
        output_dir = DEM_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    # Search for products
    products = search_elevation_products(bbox=bbox, resolution=resolution)

    if not products:
        log("No DEM products found for the specified area", "WARNING")
        return []

    downloaded = []

    for product in products:
        title = product.get("title", "unknown")
        download_url = product.get("downloadURL")

        if not download_url:
            log(f"  No download URL for: {title}", "WARNING")
            continue

        # Generate output filename
        safe_title = "".join(c if c.isalnum() or c in '-_.' else '_' for c in title)
        if state:
            filename = f"dem_{state}_{safe_title}.zip"
        else:
            filename = f"dem_{safe_title}.zip"

        # Truncate if too long
        if len(filename) > 200:
            filename = filename[:200] + ".zip"

        output_path = str(output_dir / filename)

        # Skip if already downloaded
        if os.path.exists(output_path):
            log(f"  Already exists: {output_path}")
            # Find extracted TIF
            for f in output_dir.glob("*.tif"):
                if safe_title[:50] in f.name:
                    downloaded.append(str(f))
                    break
            continue

        result = download_dem(download_url, output_path)
        if result:
            downloaded.append(result)

    return downloaded


def download_seamless_dem(
    bbox: Tuple[float, float, float, float],
    output_path: str = None,
    resolution: str = "1/3 arc-second"
) -> Optional[str]:
    """
    Download seamless DEM from USGS National Map viewer service

    This creates a merged DEM for the entire bbox rather than tiles.

    Args:
        bbox: (minx, miny, maxx, maxy)
        output_path: Output file path
        resolution: Resolution string

    Returns:
        Path to downloaded DEM
    """
    log("Downloading seamless DEM...")
    log(f"  Bbox: {bbox}")
    log(f"  Resolution: {resolution}")

    # Calculate dimensions
    # 1/3 arc-second = ~10m, 1 arc-second = ~30m
    if "1/3" in resolution:
        arc_seconds = 1/3
        meters_per_pixel = 10
    else:
        arc_seconds = 1
        meters_per_pixel = 30

    # Calculate size in pixels (limit to reasonable size)
    width_deg = bbox[2] - bbox[0]
    height_deg = bbox[3] - bbox[1]

    # Approximate pixels
    width_px = int(width_deg * 3600 / arc_seconds)
    height_px = int(height_deg * 3600 / arc_seconds)

    # Limit to 10000 x 10000 pixels
    max_dim = 10000
    if width_px > max_dim or height_px > max_dim:
        scale = max(width_px, height_px) / max_dim
        width_px = int(width_px / scale)
        height_px = int(height_px / scale)
        log(f"  Scaled to {width_px} x {height_px} pixels", "WARNING")

    log(f"  Size: {width_px} x {height_px} pixels")

    # Use TNM Web Map Service for seamless DEMs
    # Note: This may have limitations on area size
    wms_url = "https://elevation.nationalmap.gov/arcgis/services/3DEPElevation/ImageServer/WMSServer"

    params = {
        "service": "WMS",
        "version": "1.1.1",
        "request": "GetMap",
        "layers": "3DEPElevation:None",
        "styles": "",
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
        "width": width_px,
        "height": height_px,
        "srs": "EPSG:4326",
        "format": "image/tiff"
    }

    url = f"{wms_url}?{urllib.parse.urlencode(params)}"

    if output_path is None:
        output_path = str(DEM_DIR / f"dem_seamless_{bbox[0]:.2f}_{bbox[1]:.2f}_{bbox[2]:.2f}_{bbox[3]:.2f}.tif")

    try:
        log(f"  Requesting from WMS...")
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

        with urllib.request.urlopen(req, timeout=600) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())

        log(f"  Saved: {output_path}")
        return output_path

    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        log("  Try downloading tiles instead with: --tiles", "INFO")
        return None


def merge_dem_tiles(tile_paths: List[str], output_path: str) -> Optional[str]:
    """
    Merge multiple DEM tiles into a single file using GDAL

    Args:
        tile_paths: List of input GeoTIFF paths
        output_path: Output merged GeoTIFF path

    Returns:
        Output path if successful
    """
    log(f"Merging {len(tile_paths)} DEM tiles...")

    try:
        from osgeo import gdal

        # Use GDAL VRT for efficient merging
        vrt_path = output_path.replace('.tif', '.vrt')

        # Build VRT
        vrt_options = gdal.BuildVRTOptions(resampleAlg='bilinear')
        vrt = gdal.BuildVRT(vrt_path, tile_paths, options=vrt_options)
        vrt = None  # Close VRT

        # Translate VRT to GeoTIFF
        translate_options = gdal.TranslateOptions(
            format='GTiff',
            creationOptions=['COMPRESS=LZW', 'TILED=YES', 'BIGTIFF=IF_NEEDED']
        )
        gdal.Translate(output_path, vrt_path, options=translate_options)

        log(f"  Merged: {output_path}")

        # Cleanup VRT
        try:
            os.remove(vrt_path)
        except:
            pass

        return output_path

    except ImportError:
        log("GDAL not available - cannot merge tiles", "ERROR")
        return None
    except Exception as e:
        log(f"  Merge error: {e}", "ERROR")
        return None


def download_opentopography(
    bbox: Tuple[float, float, float, float],
    output_path: str = None,
    api_key: str = None
) -> Optional[str]:
    """
    Download DEM from OpenTopography (alternative source)

    Requires free API key from: https://opentopography.org/

    Args:
        bbox: (minx, miny, maxx, maxy)
        output_path: Output file path
        api_key: OpenTopography API key

    Returns:
        Path to downloaded DEM
    """
    if api_key is None:
        api_key = os.environ.get('OPENTOPO_API_KEY')
        if not api_key:
            log("OpenTopography API key required", "ERROR")
            log("Get free key at: https://opentopography.org/")
            log("Set OPENTOPO_API_KEY environment variable")
            return None

    log("Downloading from OpenTopography...")

    # SRTM GL1 (30m global) or 3DEP (10m US)
    base_url = "https://portal.opentopography.org/API/globaldem"

    params = {
        "demtype": "SRTMGL1",  # or "AW3D30" for ALOS World 3D
        "south": bbox[1],
        "north": bbox[3],
        "west": bbox[0],
        "east": bbox[2],
        "outputFormat": "GTiff",
        "API_Key": api_key
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    if output_path is None:
        output_path = str(DEM_DIR / f"dem_opentopo_{bbox[0]:.2f}_{bbox[1]:.2f}.tif")

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=300) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())

        log(f"  Saved: {output_path}")
        return output_path

    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def list_available_products(state: str = None, bbox: Tuple[float, float, float, float] = None):
    """List available DEM products for an area"""
    if bbox is None and state:
        bbox = STATE_BBOXES.get(state.upper())
        if bbox is None:
            log(f"Unknown state: {state}", "ERROR")
            return

    if bbox is None:
        log("Please provide --state or --bbox", "ERROR")
        return

    log("Available DEM Products:")
    log("=" * 70)

    for res_name, res_info in DEM_PRODUCTS.items():
        log(f"\n{res_name} ({res_info['resolution']}):")

        if "1/3" in res_name:
            datasets = "National Elevation Dataset (NED) 1/3 arc-second"
        elif "1 arc" in res_name:
            datasets = "National Elevation Dataset (NED) 1 arc-second"
        else:
            datasets = res_info.get('datasets', '')

        products = query_tnm_api(bbox, datasets, max_results=20)

        if products:
            for i, prod in enumerate(products[:10]):
                title = prod.get('title', 'Unknown')[:60]
                size = prod.get('sizeInBytes', 0) / (1024 * 1024)
                log(f"  {i+1}. {title} ({size:.1f} MB)")

            if len(products) > 10:
                log(f"  ... and {len(products) - 10} more")
        else:
            log("  No products found")


def main():
    parser = argparse.ArgumentParser(
        description="Download USGS 3DEP Digital Elevation Model Data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available products for Texas
  python3 download_dem.py --state TX --list

  # Download DEM tiles for a county-sized area
  python3 download_dem.py --bbox -97.5,30.0,-97.0,30.5

  # Download and merge tiles for a state
  python3 download_dem.py --state TX --tiles --merge

  # Download seamless DEM for small area
  python3 download_dem.py --bbox -97.5,30.0,-97.0,30.5 --seamless

  # Specify resolution
  python3 download_dem.py --state CO --resolution "1 arc-second"

Data Sources:
  USGS TNM: Primary source for NED/3DEP data
  OpenTopography: Alternative source (requires free API key)

Resolution Options:
  1/3 arc-second: ~10m resolution (best for terrain analysis)
  1 arc-second: ~30m resolution (faster downloads)

After Download:
  Use terrain_analysis.py to extract hunting features:
  python3 terrain_analysis.py --input dem.tif --state TX --pmtiles
        """
    )

    parser.add_argument("--state", "-s",
                        help="State abbreviation (e.g., TX, CO)")
    parser.add_argument("--bbox",
                        help="Bounding box: minx,miny,maxx,maxy")
    parser.add_argument("--resolution", "-r",
                        default="1/3 arc-second",
                        help="DEM resolution: '1/3 arc-second' or '1 arc-second'")
    parser.add_argument("--output", "-o",
                        help="Output directory or file path")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List available products only")
    parser.add_argument("--tiles", action="store_true",
                        help="Download individual tiles")
    parser.add_argument("--seamless", action="store_true",
                        help="Download seamless merged DEM (small areas only)")
    parser.add_argument("--merge", action="store_true",
                        help="Merge downloaded tiles into single file")
    parser.add_argument("--opentopo", action="store_true",
                        help="Use OpenTopography as source (requires API key)")
    parser.add_argument("--api-key",
                        help="OpenTopography API key")
    parser.add_argument("--max-tiles", type=int, default=50,
                        help="Maximum number of tiles to download")

    args = parser.parse_args()

    ensure_directories()

    # Parse bounding box
    bbox = None
    if args.bbox:
        try:
            bbox = tuple(float(x.strip()) for x in args.bbox.split(","))
            if len(bbox) != 4:
                raise ValueError("Need 4 coordinates")
        except Exception as e:
            log(f"Invalid bbox format: {e}", "ERROR")
            sys.exit(1)
    elif args.state:
        bbox = STATE_BBOXES.get(args.state.upper())
        if bbox is None:
            log(f"Unknown state: {args.state}", "ERROR")
            log(f"Available states: {', '.join(sorted(STATE_BBOXES.keys()))}")
            sys.exit(1)
    else:
        log("Please provide --state or --bbox", "ERROR")
        parser.print_help()
        sys.exit(1)

    # Output directory
    output_dir = Path(args.output) if args.output else DEM_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # List products
    if args.list:
        list_available_products(state=args.state, bbox=bbox)
        return

    log("=" * 70)
    log("DEM DOWNLOAD")
    log("=" * 70)
    log(f"Bounding box: {bbox}")
    log(f"Resolution: {args.resolution}")
    log(f"Output: {output_dir}")
    log("=" * 70)

    downloaded_files = []

    # Download method
    if args.opentopo:
        result = download_opentopography(
            bbox=bbox,
            output_path=str(output_dir / f"dem_{args.state or 'custom'}.tif"),
            api_key=args.api_key
        )
        if result:
            downloaded_files.append(result)

    elif args.seamless:
        result = download_seamless_dem(
            bbox=bbox,
            output_path=str(output_dir / f"dem_{args.state or 'custom'}_seamless.tif"),
            resolution=args.resolution
        )
        if result:
            downloaded_files.append(result)

    else:
        # Download tiles (default)
        downloaded_files = download_dem_for_bbox(
            bbox=bbox,
            output_dir=output_dir,
            resolution=args.resolution,
            state=args.state
        )

        # Limit number of tiles
        if len(downloaded_files) > args.max_tiles:
            log(f"Limiting to {args.max_tiles} tiles (found {len(downloaded_files)})", "WARNING")
            downloaded_files = downloaded_files[:args.max_tiles]

    # Merge tiles if requested
    if args.merge and len(downloaded_files) > 1:
        merged_path = str(output_dir / f"dem_{args.state or 'custom'}_merged.tif")
        result = merge_dem_tiles(downloaded_files, merged_path)
        if result:
            log(f"\nMerged DEM: {result}")
            downloaded_files = [result]

    # Summary
    log("")
    log("=" * 70)
    log("DOWNLOAD COMPLETE")
    log("=" * 70)
    log(f"Downloaded {len(downloaded_files)} file(s)")
    for f in downloaded_files:
        log(f"  {f}")

    if downloaded_files:
        log(f"\nNext step - Run terrain analysis:")
        log(f"  python3 terrain_analysis.py --input {downloaded_files[0]} --state {args.state or 'XX'} --pmtiles --upload")


if __name__ == "__main__":
    main()
