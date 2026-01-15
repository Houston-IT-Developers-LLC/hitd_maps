#!/usr/bin/env python3
"""
Download SSURGO Soil Survey Data

Priority: 6
Source: USDA NRCS
URL: https://sdmdataaccess.nrcs.usda.gov/

Soil data for:
- Soil type identification
- Drainage classification (wetland indicators)
- Agricultural capability
- Forest productivity ratings
- Wildlife habitat suitability

Update Frequency: Continuous
Date Added: 2026-01-13

Note: SSURGO is very large (~100GB national). This script
uses the Soil Data Access API for on-demand queries rather
than bulk download. For production, consider caching results.
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
CACHE_DIR = OUTPUT_DIR / "cache" / "ssurgo"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# SSURGO Soil Data Access API
SDA_API_URL = "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest"
SDA_SPATIAL_URL = "https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDMWGS84Geographic.wfs"

# Drainage class definitions
DRAINAGE_CLASSES = {
    "Excessively drained": {"code": "A", "desc": "Water removed very rapidly"},
    "Somewhat excessively drained": {"code": "B", "desc": "Water removed rapidly"},
    "Well drained": {"code": "C", "desc": "Water removed readily"},
    "Moderately well drained": {"code": "D", "desc": "Water removed somewhat slowly"},
    "Somewhat poorly drained": {"code": "E", "desc": "Water removed slowly"},
    "Poorly drained": {"code": "F", "desc": "Soil remains wet long periods"},
    "Very poorly drained": {"code": "G", "desc": "Water at/near surface most of year"}
}

# Hydrologic soil groups
HYDROLOGIC_GROUPS = {
    "A": "Low runoff potential, high infiltration",
    "B": "Moderate infiltration",
    "C": "Slow infiltration",
    "D": "High runoff potential, very slow infiltration",
    "A/D": "Drained/undrained dual class",
    "B/D": "Drained/undrained dual class",
    "C/D": "Drained/undrained dual class"
}


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories"""
    for dir_path in [GEOJSON_DIR, CACHE_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def query_soil_by_point(lat, lon):
    """
    Query soil data for a specific point location

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        Dict with soil properties
    """
    log(f"Querying soil data for point: ({lat}, {lon})")

    # SQL query to get soil properties at a point
    sql_query = f"""
    SELECT
        mu.mukey,
        mu.muname AS soil_name,
        mu.mukind AS map_unit_kind,
        c.drclassdcd AS drainage_class,
        c.hydgrpdcd AS hydrologic_group,
        c.forpehrtdcp AS forest_productivity,
        c.niccdcd AS irrigation_capability,
        c.hydricrating AS hydric_rating
    FROM
        mapunit mu
        INNER JOIN component c ON c.mukey = mu.mukey
    WHERE
        mu.mukey IN (
            SELECT mukey
            FROM SDA_Get_Mukey_from_intersection_with_WktWgs84(
                'POINT({lon} {lat})'
            )
        )
        AND c.cokey = (
            SELECT TOP 1 c2.cokey
            FROM component c2
            WHERE c2.mukey = mu.mukey
            ORDER BY c2.comppct_r DESC
        )
    """

    try:
        # Build request
        request_data = {
            "query": sql_query,
            "format": "JSON"
        }

        data = json.dumps(request_data).encode('utf-8')

        req = urllib.request.Request(
            SDA_API_URL,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'GSpot-Outdoors-DataPipeline/1.0'
            }
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'Table' in result and result['Table']:
                row = result['Table'][0]
                soil_data = {
                    "mukey": row.get("mukey"),
                    "soil_name": row.get("soil_name"),
                    "drainage_class": row.get("drainage_class"),
                    "hydrologic_group": row.get("hydrologic_group"),
                    "forest_productivity": row.get("forest_productivity"),
                    "hydric_rating": row.get("hydric_rating"),
                    "is_hydric": row.get("hydric_rating") == "Yes"
                }

                # Add drainage description
                if soil_data["drainage_class"] in DRAINAGE_CLASSES:
                    soil_data["drainage_description"] = DRAINAGE_CLASSES[soil_data["drainage_class"]]["desc"]

                log(f"  Found: {soil_data['soil_name']} ({soil_data['drainage_class']})")
                return soil_data

            log("  No soil data found for location", "WARNING")
            return None

    except Exception as e:
        log(f"  Query error: {e}", "ERROR")
        return None


def query_soil_by_bbox(bbox):
    """
    Query soil map units within a bounding box (two-step approach)

    Args:
        bbox: (xmin, ymin, xmax, ymax) in WGS84

    Returns:
        List of dicts with mukeys and their properties
    """
    log(f"Querying soil data for bbox: {bbox}")

    xmin, ymin, xmax, ymax = bbox

    # WKT polygon for spatial query
    wkt_polygon = f"POLYGON(({xmin} {ymin}, {xmax} {ymin}, {xmax} {ymax}, {xmin} {ymax}, {xmin} {ymin}))"

    # Step 1: Get mukeys in the bbox
    sql_query = f"""
    SELECT
        mu.mukey,
        mu.muname
    FROM
        mapunit mu
    WHERE
        mu.mukey IN (
            SELECT mukey FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt_polygon}')
        )
    """

    try:
        request_data = {"query": sql_query, "format": "JSON"}
        data = json.dumps(request_data).encode('utf-8')

        req = urllib.request.Request(
            SDA_API_URL,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'GSpot-Outdoors-DataPipeline/1.0'
            }
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'Table' not in result or not result['Table']:
                log(f"  No soil data found in area", "WARNING")
                return None

            # Extract mukeys and names
            mukey_names = {}
            for row in result['Table']:
                if isinstance(row, list) and len(row) >= 2:
                    mukey_names[row[0]] = row[1]

            log(f"  Found {len(mukey_names)} map units in area")

            if not mukey_names:
                return None

            # Step 2: Get properties for these mukeys
            properties = query_soil_properties_bulk(list(mukey_names.keys()))

            # Combine results
            features = []
            for mukey, muname in mukey_names.items():
                feature = {
                    "mukey": mukey,
                    "soil_name": muname
                }
                if mukey in properties:
                    feature.update(properties[mukey])
                features.append(feature)

            log(f"  Retrieved properties for {len(features)} soil map units")
            return features

    except Exception as e:
        log(f"  Query error: {e}", "ERROR")
        return None


def query_soil_properties_bulk(mukeys):
    """
    Query soil properties for multiple map unit keys

    Args:
        mukeys: List of mukey values

    Returns:
        Dict mapping mukey to soil properties
    """
    if not mukeys:
        return {}

    log(f"Querying properties for {len(mukeys)} map units")

    properties = {}

    # Process in batches of 50 to avoid query limits
    batch_size = 50
    for i in range(0, len(mukeys), batch_size):
        batch = mukeys[i:i + batch_size]
        mukey_list = ",".join([f"'{k}'" for k in batch])

        # Query component table directly for dominant component
        sql_query = f"""
        SELECT
            mukey,
            compname,
            comppct_r,
            drainagecl,
            hydricrating
        FROM
            component
        WHERE
            mukey IN ({mukey_list})
        ORDER BY mukey, comppct_r DESC
        """

        try:
            request_data = {"query": sql_query, "format": "JSON"}
            data = json.dumps(request_data).encode('utf-8')

            req = urllib.request.Request(
                SDA_API_URL,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'GSpot-Outdoors-DataPipeline/1.0'
                }
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))

                if 'Table' in result:
                    # Group by mukey and take the dominant component (first one due to ORDER BY)
                    seen_mukeys = set()
                    for row in result['Table']:
                        if isinstance(row, list) and len(row) >= 5:
                            mukey = row[0]
                            if mukey not in seen_mukeys:
                                seen_mukeys.add(mukey)
                                properties[mukey] = {
                                    "component_name": row[1],
                                    "component_pct": row[2],
                                    "drainage_class": row[3],
                                    "hydric_rating": row[4],
                                    "is_hydric": row[4] == "Yes"
                                }

        except Exception as e:
            log(f"  Batch query error: {e}", "WARNING")
            continue

    log(f"  Retrieved properties for {len(properties)} map units")
    return properties


def download_soil_for_area(bbox, output_file=None):
    """
    Download soil data for an area with full properties

    Note: SSURGO spatial API returns tabular data only, not geometry.
    This outputs a JSON file with soil properties that can be used for
    parcel enrichment via spatial join with local SSURGO shapefiles.

    Args:
        bbox: (xmin, ymin, xmax, ymax) in WGS84
        output_file: Output JSON path
    """
    if output_file is None:
        bbox_str = f"{bbox[0]:.2f}_{bbox[1]:.2f}_{bbox[2]:.2f}_{bbox[3]:.2f}"
        output_file = GEOJSON_DIR / f"ssurgo_{bbox_str}.json"

    log(f"Downloading SSURGO for bbox: {bbox}")

    # Get soil map units and properties
    soil_data = query_soil_by_bbox(bbox)
    if not soil_data:
        log("  No soil data retrieved", "ERROR")
        return None

    # Build output structure
    output = {
        "type": "SoilDataCollection",
        "name": f"SSURGO Soil Data",
        "metadata": {
            "source": "USDA NRCS Soil Data Access",
            "download_date": datetime.now().isoformat(),
            "bbox": list(bbox),
            "map_unit_count": len(soil_data),
            "api_url": SDA_API_URL,
            "note": "Tabular data only - use SSURGO shapefiles for geometry"
        },
        "map_units": soil_data,
        "summary": {
            "total_units": len(soil_data),
            "drainage_classes": {},
            "hydric_count": 0
        }
    }

    # Calculate summary stats
    for unit in soil_data:
        dc = unit.get("drainage_class")
        if dc:
            output["summary"]["drainage_classes"][dc] = output["summary"]["drainage_classes"].get(dc, 0) + 1
        if unit.get("is_hydric"):
            output["summary"]["hydric_count"] += 1

    # Save
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    log(f"  Saved {len(soil_data)} map units to {output_file}")
    log(f"  Summary: {output['summary']['hydric_count']} hydric units")
    return str(output_file)


def generate_pmtiles(geojson_path, pmtiles_path):
    """Generate PMTiles from GeoJSON"""
    import subprocess

    log(f"Generating PMTiles: {geojson_path}")

    cmd = [
        "tippecanoe",
        "-z14",
        "-Z10",  # Soil data not useful at low zooms
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "-l", "soils",
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
        description="Query SSURGO Soil Survey Data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query soil at a specific point
  python3 download_ssurgo.py --point 30.2672,-97.7431

  # Download soil data for a bounding box
  python3 download_ssurgo.py --bbox -97.5,30.0,-97.0,30.5

  # Full pipeline
  python3 download_ssurgo.py --bbox -97.5,30.0,-97.0,30.5 --pmtiles --upload

Drainage Classes:
  Excessively drained - Water removed very rapidly
  Well drained - Water removed readily
  Moderately well drained - Water removed somewhat slowly
  Somewhat poorly drained - Water removed slowly
  Poorly drained - Soil remains wet long periods
  Very poorly drained - Water at/near surface most of year

Hydric Soils: Indicate wetland areas (poorly/very poorly drained)

Note: SSURGO is very large nationally. This script uses the
API for on-demand queries. For large areas, consider using
the Web Soil Survey bulk download tool.
        """
    )

    parser.add_argument("--point", help="Query point: lat,lon")
    parser.add_argument("--bbox", help="Bounding box: xmin,ymin,xmax,ymax")
    parser.add_argument("--pmtiles", action="store_true", help="Generate PMTiles")
    parser.add_argument("--upload", action="store_true", help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true", help="Remove local files after upload")
    parser.add_argument("--list-classes", action="store_true", help="List drainage classes")

    args = parser.parse_args()

    ensure_directories()

    if args.list_classes:
        log("Drainage Classes:")
        for name, info in DRAINAGE_CLASSES.items():
            log(f"  {name}: {info['desc']}")
        log("\nHydrologic Soil Groups:")
        for code, desc in HYDROLOGIC_GROUPS.items():
            log(f"  {code}: {desc}")
        return

    if args.point:
        try:
            lat, lon = [float(x.strip()) for x in args.point.split(",")]
        except Exception as e:
            log(f"Invalid point format: {e}", "ERROR")
            return

        result = query_soil_by_point(lat, lon)
        if result:
            log("\nSoil Properties:")
            for key, value in result.items():
                log(f"  {key}: {value}")
        return

    if args.bbox:
        try:
            bbox = tuple(float(x.strip()) for x in args.bbox.split(","))
            if len(bbox) != 4:
                raise ValueError("Need 4 coordinates")
        except Exception as e:
            log(f"Invalid bbox format: {e}", "ERROR")
            return

        result = download_soil_for_area(bbox)

        if result:
            files_to_upload = [result]

            if args.pmtiles:
                from pathlib import Path
                pmtiles_name = Path(result).stem + ".pmtiles"
                pmtiles_path = OUTPUT_DIR / "pmtiles" / pmtiles_name
                pmtiles_path.parent.mkdir(parents=True, exist_ok=True)
                if generate_pmtiles(result, pmtiles_path):
                    files_to_upload.append(str(pmtiles_path))

            if args.upload:
                for file_path in files_to_upload:
                    if os.path.exists(file_path):
                        filename = os.path.basename(file_path)
                        r2_key = f"enrichment/ssurgo/{filename}"
                        upload_to_r2(file_path, r2_key)

            if args.cleanup and args.upload:
                for file_path in files_to_upload:
                    if os.path.exists(file_path):
                        cleanup_local(file_path)

        return

    parser.print_help()


if __name__ == "__main__":
    main()
