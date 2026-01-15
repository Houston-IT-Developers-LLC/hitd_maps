#!/usr/bin/env python3
"""
Generate Tile Index from R2 Bucket

Scans the R2 bucket and generates a live index of available tiles,
including file sizes, URLs, and metadata.

This index is uploaded to R2 and can be fetched by web/mobile apps
to know what data is available.

Usage:
    python3 generate_tile_index.py
    python3 generate_tile_index.py --upload
    python3 generate_tile_index.py --pretty
"""

import os
import sys
import json
import boto3
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent
CONFIG_DIR = DATA_PIPELINE_DIR / "config"

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

# Layer categories
LAYER_CATEGORIES = {
    "pmtiles/": "parcels",
    "geojson/": "parcels",
    "enrichment/pad_us/": "public_lands",
    "enrichment/nwi/": "wetlands",
    "enrichment/nhd/": "hydrography",
    "enrichment/state_wma/": "wildlife_areas",
    "enrichment/fema/": "flood_zones",
    "enrichment/blm/": "federal_lands",
    "enrichment/usfs/": "federal_lands",
    "enrichment/ssurgo/": "soils",
    "enrichment/nlcd/": "land_cover"
}


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def get_s3_client():
    """Create S3 client for R2"""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
    )


def format_size(size_bytes):
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def extract_state_from_key(key):
    """Extract state code from file key"""
    filename = key.split('/')[-1]
    # Pattern: *_XX.pmtiles or *_XX.geojson
    parts = filename.replace('.pmtiles', '').replace('.geojson', '').split('_')
    for part in reversed(parts):
        if len(part) == 2 and part.isalpha():
            return part.upper()
    return None


def get_layer_category(key):
    """Get layer category from file key"""
    for prefix, category in LAYER_CATEGORIES.items():
        if key.startswith(prefix):
            return category
    return "other"


def scan_r2_bucket():
    """Scan R2 bucket and collect file information"""
    s3_client = get_s3_client()

    log("Scanning R2 bucket...")

    files = []
    prefixes = ["pmtiles/", "geojson/", "enrichment/", "parcels/"]

    for prefix in prefixes:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    size = obj['Size']
                    last_modified = obj['LastModified']

                    # Skip directories
                    if key.endswith('/'):
                        continue

                    # Only include pmtiles and geojson
                    if not (key.endswith('.pmtiles') or key.endswith('.geojson')):
                        continue

                    file_info = {
                        "key": key,
                        "size": size,
                        "size_formatted": format_size(size),
                        "last_modified": last_modified.isoformat(),
                        "url": f"{R2_PUBLIC_URL}/{key}",
                        "format": "pmtiles" if key.endswith('.pmtiles') else "geojson",
                        "state": extract_state_from_key(key),
                        "category": get_layer_category(key)
                    }

                    files.append(file_info)

    log(f"Found {len(files)} files")
    return files


def generate_index(files):
    """Generate structured tile index from file list"""

    # Group by category and state
    by_category = defaultdict(lambda: defaultdict(dict))
    by_state = defaultdict(lambda: defaultdict(list))

    total_size = 0

    for f in files:
        category = f['category']
        state = f['state']
        fmt = f['format']

        total_size += f['size']

        if state:
            by_category[category][state][fmt] = {
                "url": f['url'],
                "size": f['size'],
                "size_formatted": f['size_formatted'],
                "last_modified": f['last_modified']
            }

            by_state[state][category].append({
                "format": fmt,
                "url": f['url'],
                "size": f['size']
            })

    # Build index structure
    index = {
        "name": "GSpot Outdoors Tile Index",
        "version": "1.0.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "cdn_base": R2_PUBLIC_URL,
        "protocol": "pmtiles://",
        "statistics": {
            "total_files": len(files),
            "total_size": total_size,
            "total_size_formatted": format_size(total_size),
            "states_covered": len(by_state),
            "categories": list(by_category.keys())
        },
        "layers": {},
        "states": {}
    }

    # Build layers section
    layer_meta = {
        "parcels": {
            "name": "Property Parcels",
            "source_layer": "parcels",
            "min_zoom": 10,
            "max_zoom": 16
        },
        "public_lands": {
            "name": "Public Lands (PAD-US)",
            "source_layer": "public_lands",
            "min_zoom": 4,
            "max_zoom": 14
        },
        "wetlands": {
            "name": "Wetlands (NWI)",
            "source_layer": "wetlands",
            "min_zoom": 8,
            "max_zoom": 14
        },
        "hydrography": {
            "name": "Water Features (NHD)",
            "source_layer": "hydrography",
            "min_zoom": 6,
            "max_zoom": 14
        },
        "wildlife_areas": {
            "name": "Wildlife Management Areas",
            "source_layer": "wildlife_areas",
            "min_zoom": 6,
            "max_zoom": 14
        },
        "flood_zones": {
            "name": "Flood Zones (FEMA)",
            "source_layer": "flood_zones",
            "min_zoom": 8,
            "max_zoom": 14
        },
        "federal_lands": {
            "name": "Federal Lands (BLM/USFS)",
            "source_layer": "federal_lands",
            "min_zoom": 4,
            "max_zoom": 14
        },
        "soils": {
            "name": "Soil Data (SSURGO)",
            "source_layer": "soils",
            "min_zoom": 10,
            "max_zoom": 14
        }
    }

    for category, states_data in by_category.items():
        meta = layer_meta.get(category, {"name": category.title(), "source_layer": category})

        index["layers"][category] = {
            **meta,
            "states_available": sorted(states_data.keys()),
            "state_count": len(states_data),
            "files": states_data
        }

    # Build states section
    state_names = {
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

    for state, layers in by_state.items():
        index["states"][state] = {
            "name": state_names.get(state, state),
            "layers_available": list(layers.keys()),
            "layer_count": len(layers),
            "data": dict(layers)
        }

    return index


def upload_index(index, pretty=False):
    """Upload index to R2"""
    s3_client = get_s3_client()

    # Generate JSON
    if pretty:
        content = json.dumps(index, indent=2, default=str)
    else:
        content = json.dumps(index, default=str)

    # Upload
    key = "index.json"
    log(f"Uploading index to R2: {key}")

    s3_client.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=content.encode('utf-8'),
        ContentType='application/json',
        CacheControl='public, max-age=3600'  # 1 hour cache
    )

    url = f"{R2_PUBLIC_URL}/{key}"
    log(f"Index uploaded: {url}")

    return url


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate tile index from R2 bucket")
    parser.add_argument("--upload", action="store_true", help="Upload index to R2")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON output")
    parser.add_argument("--output", "-o", help="Output file path")

    args = parser.parse_args()

    # Scan bucket
    files = scan_r2_bucket()

    if not files:
        log("No files found in bucket", "WARNING")
        return

    # Generate index
    index = generate_index(files)

    # Output
    if args.pretty:
        output = json.dumps(index, indent=2, default=str)
    else:
        output = json.dumps(index, default=str)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        log(f"Index saved to: {args.output}")
    else:
        print(output)

    # Upload if requested
    if args.upload:
        url = upload_index(index, args.pretty)
        log(f"\nPublic URL: {url}")

    # Summary
    log("\n" + "=" * 50)
    log("TILE INDEX SUMMARY")
    log("=" * 50)
    log(f"Total files: {index['statistics']['total_files']}")
    log(f"Total size: {index['statistics']['total_size_formatted']}")
    log(f"States: {index['statistics']['states_covered']}")
    log(f"Categories: {', '.join(index['statistics']['categories'])}")


if __name__ == "__main__":
    main()
