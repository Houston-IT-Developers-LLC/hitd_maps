#!/usr/bin/env python3
"""
Download National Land Cover Database (NLCD)

Priority: 5
Source: USGS EROS / MRLC Consortium
URL: https://www.mrlc.gov/

Land cover data for:
- Identifying forested parcels (hunting habitat)
- Agricultural vs timber land classification
- Tree canopy percentage
- Land cover change detection

Update Frequency: Annual
Current Version: NLCD 2021 (Annual NLCD 1985-2024)
Date Added: 2026-01-13

Note: NLCD is raster data (GeoTIFF). This script downloads
Cloud Optimized GeoTIFFs (COG) for efficient access.
For parcel enrichment, use zonal statistics to summarize
land cover per parcel rather than converting to vector.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
RASTER_DIR = OUTPUT_DIR / "raster" / "nlcd"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# NLCD Data Access
# Option 1: AWS Cloud (recommended for programmatic access)
NLCD_AWS_BASE = "s3://mrlc-data/"
NLCD_AWS_HTTPS = "https://mrlc-data.s3.amazonaws.com/"

# Option 2: ScienceBase downloads
NLCD_SCIENCEBASE = "https://www.sciencebase.gov/catalog/item/60d4b067d34e0de9e9ba5156"

# Option 3: MRLC Web Services (for on-demand queries)
NLCD_WMS = "https://www.mrlc.gov/geoserver/mrlc_display/wms"

# NLCD Land Cover Classes
NLCD_CLASSES = {
    11: {"name": "Open Water", "category": "water", "color": "#466b9f"},
    12: {"name": "Perennial Ice/Snow", "category": "water", "color": "#d1def8"},
    21: {"name": "Developed, Open Space", "category": "developed", "color": "#dec5c5"},
    22: {"name": "Developed, Low Intensity", "category": "developed", "color": "#d99282"},
    23: {"name": "Developed, Medium Intensity", "category": "developed", "color": "#eb0000"},
    24: {"name": "Developed, High Intensity", "category": "developed", "color": "#ab0000"},
    31: {"name": "Barren Land", "category": "barren", "color": "#b3ac9f"},
    41: {"name": "Deciduous Forest", "category": "forest", "color": "#68ab5f"},
    42: {"name": "Evergreen Forest", "category": "forest", "color": "#1c5f2c"},
    43: {"name": "Mixed Forest", "category": "forest", "color": "#b5c58f"},
    52: {"name": "Shrub/Scrub", "category": "shrubland", "color": "#ccb879"},
    71: {"name": "Grassland/Herbaceous", "category": "herbaceous", "color": "#dfdfc2"},
    81: {"name": "Pasture/Hay", "category": "agricultural", "color": "#dcd939"},
    82: {"name": "Cultivated Crops", "category": "agricultural", "color": "#ab6c28"},
    90: {"name": "Woody Wetlands", "category": "wetland", "color": "#b8d9eb"},
    95: {"name": "Emergent Herbaceous Wetlands", "category": "wetland", "color": "#6c9fb8"}
}

# NLCD Products
NLCD_PRODUCTS = {
    "landcover": {
        "name": "Land Cover",
        "description": "16-class land cover classification",
        "filename_pattern": "nlcd_{year}_land_cover_l48_20210604.tif",
        "years": [2001, 2004, 2006, 2008, 2011, 2013, 2016, 2019, 2021]
    },
    "tree_canopy": {
        "name": "Tree Canopy Cover",
        "description": "Percent tree canopy cover (0-100)",
        "filename_pattern": "nlcd_{year}_tree_canopy_cover_analytical_l48_20210604.tif",
        "years": [2011, 2016, 2019, 2021]
    },
    "impervious": {
        "name": "Impervious Surface",
        "description": "Percent impervious surface (0-100)",
        "filename_pattern": "nlcd_{year}_impervious_l48_20210604.tif",
        "years": [2001, 2004, 2006, 2008, 2011, 2013, 2016, 2019, 2021]
    }
}


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories"""
    for dir_path in [RASTER_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def download_nlcd_conus(product="landcover", year=2021):
    """
    Download NLCD raster data for CONUS (Continental US)

    Args:
        product: One of 'landcover', 'tree_canopy', 'impervious'
        year: Data year

    Note: Full CONUS files are very large (5-20GB each).
    Consider using AWS S3 CLI or the WMS service for smaller areas.
    """
    product_info = NLCD_PRODUCTS.get(product)
    if not product_info:
        log(f"Unknown product: {product}", "ERROR")
        return None

    if year not in product_info['years']:
        log(f"Year {year} not available for {product}", "ERROR")
        log(f"  Available years: {product_info['years']}")
        return None

    log(f"NLCD {product_info['name']} - {year}")
    log("=" * 60)
    log("WARNING: Full CONUS NLCD files are very large (5-20GB)")
    log("Consider using:")
    log("  1. AWS S3 CLI: aws s3 cp s3://mrlc-data/... local/")
    log("  2. MRLC Web Viewer for small area downloads")
    log("  3. WMS service for on-demand queries")
    log("=" * 60)

    # For now, just return info about how to download
    download_info = {
        "product": product,
        "year": year,
        "aws_path": f"{NLCD_AWS_HTTPS}{product_info['filename_pattern'].format(year=year)}",
        "sciencebase": NLCD_SCIENCEBASE,
        "wms": NLCD_WMS,
        "local_path": RASTER_DIR / f"nlcd_{product}_{year}.tif"
    }

    log(f"\nDownload URLs:")
    log(f"  AWS: {download_info['aws_path']}")
    log(f"  ScienceBase: {download_info['sciencebase']}")

    return download_info


def extract_nlcd_for_bbox(bbox, product="landcover", year=2021, output_file=None):
    """
    Extract NLCD data for a specific bounding box using WMS

    Args:
        bbox: (xmin, ymin, xmax, ymax) in WGS84
        product: NLCD product type
        year: Data year
        output_file: Output file path

    Note: For large areas, this may fail or be very slow.
    Better to download full raster and clip locally.
    """
    if output_file is None:
        output_file = RASTER_DIR / f"nlcd_{product}_{year}_clip.tif"

    log(f"Extracting NLCD {product} {year} for bbox: {bbox}")

    # WMS GetMap request parameters
    width = int((bbox[2] - bbox[0]) / 0.0003)  # ~30m resolution
    height = int((bbox[3] - bbox[1]) / 0.0003)

    # Limit size
    max_dim = 4096
    if width > max_dim or height > max_dim:
        scale = max(width, height) / max_dim
        width = int(width / scale)
        height = int(height / scale)
        log(f"  Scaled to {width}x{height} pixels", "WARNING")

    params = {
        "service": "WMS",
        "version": "1.1.1",
        "request": "GetMap",
        "layers": f"mrlc_display:NLCD_{year}_Land_Cover_L48",
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
        "width": width,
        "height": height,
        "srs": "EPSG:4326",
        "format": "image/geotiff"
    }

    query_string = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
    url = f"{NLCD_WMS}?{query_string}"

    log(f"  Requesting {width}x{height} pixel image...")

    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

        with urllib.request.urlopen(req, timeout=300) as response:
            with open(output_file, 'wb') as f:
                f.write(response.read())

        log(f"  Saved to: {output_file}")
        return str(output_file)

    except Exception as e:
        log(f"  Error: {e}", "ERROR")
        return None


def generate_zonal_stats_script():
    """
    Generate a Python script for computing zonal statistics
    (land cover per parcel)
    """
    script_content = '''#!/usr/bin/env python3
"""
Compute NLCD zonal statistics per parcel

This script requires:
  - rasterio
  - rasterstats
  - geopandas

Usage:
    python3 nlcd_zonal_stats.py parcels.geojson nlcd_landcover.tif output.geojson
"""

import sys
import json
import geopandas as gpd
from rasterstats import zonal_stats

NLCD_CLASSES = {
    11: "Open Water", 12: "Perennial Ice/Snow",
    21: "Developed, Open Space", 22: "Developed, Low Intensity",
    23: "Developed, Medium Intensity", 24: "Developed, High Intensity",
    31: "Barren Land",
    41: "Deciduous Forest", 42: "Evergreen Forest", 43: "Mixed Forest",
    52: "Shrub/Scrub", 71: "Grassland/Herbaceous",
    81: "Pasture/Hay", 82: "Cultivated Crops",
    90: "Woody Wetlands", 95: "Emergent Herbaceous Wetlands"
}

def main():
    if len(sys.argv) != 4:
        print("Usage: nlcd_zonal_stats.py parcels.geojson nlcd.tif output.geojson")
        sys.exit(1)

    parcels_file = sys.argv[1]
    nlcd_file = sys.argv[2]
    output_file = sys.argv[3]

    print(f"Loading parcels: {parcels_file}")
    gdf = gpd.read_file(parcels_file)

    print(f"Computing zonal statistics from: {nlcd_file}")
    # Get majority class for each parcel
    stats = zonal_stats(gdf, nlcd_file, categorical=True, all_touched=True)

    # Add results to geodataframe
    for i, stat in enumerate(stats):
        if stat:
            # Find majority class
            majority_class = max(stat.items(), key=lambda x: x[1])[0] if stat else None
            gdf.loc[i, 'nlcd_class'] = majority_class
            gdf.loc[i, 'nlcd_name'] = NLCD_CLASSES.get(majority_class, 'Unknown')

            # Calculate forest percentage
            forest_classes = [41, 42, 43, 90]
            total_pixels = sum(stat.values())
            forest_pixels = sum(stat.get(c, 0) for c in forest_classes)
            gdf.loc[i, 'forest_pct'] = (forest_pixels / total_pixels * 100) if total_pixels > 0 else 0

            # Is primarily forested?
            gdf.loc[i, 'is_forested'] = gdf.loc[i, 'forest_pct'] > 50

    print(f"Saving results: {output_file}")
    gdf.to_file(output_file, driver='GeoJSON')
    print("Done!")

if __name__ == "__main__":
    main()
'''

    script_path = SCRIPT_DIR / "nlcd_zonal_stats.py"
    with open(script_path, 'w') as f:
        f.write(script_content)

    log(f"Generated zonal stats script: {script_path}")
    return str(script_path)


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

        s3_client.upload_file(
            local_path,
            R2_BUCKET,
            r2_key,
            ExtraArgs={'ContentType': 'image/tiff'}
        )

        public_url = f"{R2_PUBLIC_URL}/{r2_key}"
        log(f"  Uploaded: {public_url}")
        return public_url

    except Exception as e:
        log(f"  Upload error: {e}", "ERROR")
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Download National Land Cover Database (NLCD)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show available products and years
  python3 download_nlcd.py --list

  # Extract NLCD for a small area via WMS
  python3 download_nlcd.py --bbox -97.5,30.0,-97.0,30.5 --year 2021

  # Generate zonal statistics helper script
  python3 download_nlcd.py --generate-zonal-script

  # Show download info for full CONUS raster
  python3 download_nlcd.py --product landcover --year 2021 --info

NLCD Land Cover Classes:
  Forest: 41 (Deciduous), 42 (Evergreen), 43 (Mixed)
  Agricultural: 81 (Pasture/Hay), 82 (Cultivated Crops)
  Wetlands: 90 (Woody), 95 (Emergent Herbaceous)
  Developed: 21-24 (Open Space to High Intensity)
  Water: 11 (Open Water), 12 (Ice/Snow)

Note: NLCD is raster data. For parcel enrichment, use zonal
statistics to summarize land cover per parcel polygon.
        """
    )

    parser.add_argument("--product", choices=["landcover", "tree_canopy", "impervious"],
                        default="landcover", help="NLCD product type")
    parser.add_argument("--year", type=int, default=2021, help="Data year")
    parser.add_argument("--bbox", help="Bounding box: xmin,ymin,xmax,ymax")
    parser.add_argument("--info", action="store_true", help="Show download info only")
    parser.add_argument("--upload", action="store_true", help="Upload to Cloudflare R2")
    parser.add_argument("--generate-zonal-script", action="store_true",
                        help="Generate helper script for zonal statistics")
    parser.add_argument("--list", action="store_true", help="List available products and classes")

    args = parser.parse_args()

    ensure_directories()

    if args.list:
        log("NLCD Products:")
        for prod_key, prod_info in NLCD_PRODUCTS.items():
            log(f"  {prod_key}: {prod_info['name']}")
            log(f"    {prod_info['description']}")
            log(f"    Years: {prod_info['years']}")
        log("\nNLCD Land Cover Classes:")
        for code, info in sorted(NLCD_CLASSES.items()):
            log(f"  {code}: {info['name']} ({info['category']})")
        return

    if args.generate_zonal_script:
        generate_zonal_stats_script()
        return

    if args.info:
        download_nlcd_conus(args.product, args.year)
        return

    if args.bbox:
        try:
            bbox = tuple(float(x.strip()) for x in args.bbox.split(","))
            if len(bbox) != 4:
                raise ValueError("Need 4 coordinates")
        except Exception as e:
            log(f"Invalid bbox format: {e}", "ERROR")
            return

        result = extract_nlcd_for_bbox(bbox, args.product, args.year)

        if result and args.upload:
            r2_key = f"enrichment/nlcd/{os.path.basename(result)}"
            upload_to_r2(result, r2_key)

        return

    # Default: show download info
    download_nlcd_conus(args.product, args.year)


if __name__ == "__main__":
    main()
