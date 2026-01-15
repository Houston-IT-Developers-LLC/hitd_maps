#!/usr/bin/env python3
"""
Download National Hydrography Dataset (NHD)

Priority: 3
Source: USGS
URL: https://www.usgs.gov/national-hydrography

Water feature data for:
- Distance to water calculations
- Stream/lake frontage identification
- Fishing access points
- Watershed boundaries

Update Frequency: Continuous
Current Version: NHDPlus HR
Date Added: 2026-01-13

Note: NHD was officially retired Oct 2023, replaced by 3DHP.
However, NHD data remains available and valid.
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
RAW_DIR = OUTPUT_DIR / "raw" / "nhd"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# NHD ArcGIS REST Service
NHD_SERVICE = "https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer"

# Key NHD Layers (updated layer IDs from service)
NHD_LAYERS = {
    0: {"name": "NHDPoint", "description": "Point features (springs, wells)"},
    6: {"name": "NHDFlowline", "description": "Linear water features - Large Scale (streams, rivers, canals)"},
    9: {"name": "NHDArea", "description": "Area features - Large Scale (swamps, dams)"},
    12: {"name": "NHDWaterbody", "description": "Water bodies - Large Scale (lakes, ponds, reservoirs)"},
}

# Feature Type Codes (FType)
FTYPE_CODES = {
    # Flowlines
    334: "Connector",
    336: "Canal/Ditch",
    397: "Intermittent Stream",
    420: "Underground Conduit",
    428: "Pipeline",
    460: "Stream/River",
    558: "Artificial Path",
    566: "Coastline",

    # Waterbodies
    361: "Playa",
    378: "Ice Mass",
    390: "Lake/Pond",
    436: "Reservoir",
    466: "Swamp/Marsh",
    493: "Estuary",

    # Areas
    307: "Area of Complex Channels",
    343: "Dam/Weir",
    362: "Playa",
    403: "Inundation Area",
    455: "Spillway",
    484: "Wash",
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


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories"""
    for dir_path in [RAW_DIR, GEOJSON_DIR, PMTILES_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def get_state_bbox(state_abbrev):
    """Get bounding box for state"""
    state_upper = state_abbrev.upper()
    if state_upper in STATE_BBOX:
        return STATE_BBOX[state_upper]

    # Default to CONUS if state not found
    log(f"  No bbox for {state_upper}, using API state filter", "WARNING")
    return None


def download_nhd_layer(layer_id, state_abbrev=None, bbox=None, output_file=None):
    """
    Download NHD layer data via ArcGIS REST API

    Args:
        layer_id: NHD layer ID
        state_abbrev: Optional state filter
        bbox: Optional bounding box (xmin, ymin, xmax, ymax)
        output_file: Output file path
    """
    import ssl

    # SSL context for certificate issues
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    layer_info = NHD_LAYERS.get(layer_id, {})
    layer_name = layer_info.get("name", f"Layer{layer_id}")

    log(f"Downloading NHD {layer_name}")
    if state_abbrev:
        log(f"  State: {state_abbrev}")
    if bbox:
        log(f"  Bbox: {bbox}")

    base_url = f"{NHD_SERVICE}/{layer_id}/query"

    all_features = []
    offset = 0
    batch_size = 2000
    max_features = 100000  # Limit per layer

    while len(all_features) < max_features:
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "returnGeometry": "true",
            "outSR": "4326",
            "resultOffset": str(offset),
            "resultRecordCount": str(batch_size)
        }

        if bbox:
            params["geometry"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"
            params["inSR"] = "4326"

        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"

        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'GSpot-Outdoors-DataPipeline/1.0')

            with urllib.request.urlopen(req, timeout=180, context=ctx) as response:
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

                # Safety limit
                if len(all_features) > 500000:
                    log("  Reached 500k feature limit", "WARNING")
                    break

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
        # Add feature type descriptions
        for feature in all_features:
            props = feature.get('properties', {})
            ftype = props.get('FType')
            if ftype and ftype in FTYPE_CODES:
                props['feature_type_name'] = FTYPE_CODES[ftype]

        geojson = {
            "type": "FeatureCollection",
            "name": f"NHD {layer_name}" + (f" - {state_abbrev}" if state_abbrev else ""),
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": all_features,
            "metadata": {
                "source": "USGS National Hydrography Dataset",
                "download_date": datetime.now().isoformat(),
                "layer": layer_name,
                "layer_id": layer_id,
                "feature_count": len(all_features),
                "api_url": NHD_SERVICE,
                "state": state_abbrev,
                "bbox": bbox
            }
        }

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(geojson, f)
            log(f"  Saved {len(all_features)} features to {output_file}")

        return geojson

    return None


def download_state_nhd(state_abbrev, layers=None):
    """
    Download all NHD layers for a state

    Args:
        state_abbrev: 2-letter state code
        layers: List of layer IDs to download (default: flowlines and waterbodies)
    """
    state_upper = state_abbrev.upper()

    if layers is None:
        # Default to most useful layers for outdoor recreation
        layers = [6, 12]  # Flowlines - Large Scale (streams/rivers) and Waterbodies - Large Scale (lakes/ponds)

    bbox = get_state_bbox(state_upper)

    results = {}
    for layer_id in layers:
        layer_info = NHD_LAYERS.get(layer_id, {})
        layer_name = layer_info.get("name", f"layer{layer_id}").lower()

        output_file = GEOJSON_DIR / f"nhd_{layer_name}_{state_upper.lower()}.geojson"

        result = download_nhd_layer(
            layer_id=layer_id,
            state_abbrev=state_upper,
            bbox=bbox,
            output_file=output_file
        )

        if result:
            results[layer_name] = str(output_file)

    return results


def merge_nhd_layers(state_abbrev, layer_files, output_file):
    """Merge multiple NHD layer files into one GeoJSON"""
    log(f"Merging NHD layers for {state_abbrev}")

    all_features = []
    for layer_name, file_path in layer_files.items():
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                features = data.get('features', [])
                # Add layer source to each feature
                for feat in features:
                    feat['properties']['nhd_layer'] = layer_name
                all_features.extend(features)
                log(f"  Added {len(features)} from {layer_name}")

    if all_features:
        merged = {
            "type": "FeatureCollection",
            "name": f"NHD Hydrography - {state_abbrev}",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": all_features,
            "metadata": {
                "source": "USGS National Hydrography Dataset",
                "download_date": datetime.now().isoformat(),
                "state": state_abbrev,
                "feature_count": len(all_features),
                "layers_merged": list(layer_files.keys())
            }
        }

        with open(output_file, 'w') as f:
            json.dump(merged, f)

        log(f"  Merged {len(all_features)} features to {output_file}")
        return str(output_file)

    return None


def generate_pmtiles(geojson_path, pmtiles_path):
    """Generate PMTiles from GeoJSON"""
    import subprocess

    log(f"Generating PMTiles: {geojson_path}")

    cmd = [
        "tippecanoe",
        "-z14",
        "-Z6",  # Min zoom for water features
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "--coalesce-smallest-as-needed",
        "-l", "hydrography",
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


def cleanup_local(paths):
    """Remove local files after upload"""
    for path in paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
                log(f"  Removed: {path}")
        except Exception as e:
            log(f"  Cleanup error for {path}: {e}", "WARNING")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Download National Hydrography Dataset (NHD)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download NHD for a specific state
  python3 download_nhd.py --state TX

  # Download specific layers only
  python3 download_nhd.py --state TX --layers 2,5

  # Full pipeline
  python3 download_nhd.py --state TX --merge --pmtiles --upload --cleanup

NHD Layers:
  1 - NHDPoint (springs, wells)
  2 - NHDFlowline (streams, rivers, canals) [recommended]
  3 - NHDLine (other linear features)
  4 - NHDArea (swamps, dams)
  5 - NHDWaterbody (lakes, ponds, reservoirs) [recommended]
        """
    )

    parser.add_argument("--state", "-s", help="State abbreviation(s), comma-separated")
    parser.add_argument("--layers", help="Layer IDs to download (default: 6,12)", default="6,12")
    parser.add_argument("--merge", action="store_true", help="Merge layers into single file")
    parser.add_argument("--pmtiles", action="store_true", help="Generate PMTiles")
    parser.add_argument("--upload", action="store_true", help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true", help="Remove local files after upload")
    parser.add_argument("--list-layers", action="store_true", help="List available NHD layers")
    parser.add_argument("--list-types", action="store_true", help="List feature type codes")

    args = parser.parse_args()

    ensure_directories()

    if args.list_layers:
        log("NHD Layers:")
        for layer_id, info in NHD_LAYERS.items():
            log(f"  {layer_id}: {info['name']} - {info['description']}")
        return

    if args.list_types:
        log("NHD Feature Type Codes (FType):")
        for code, name in sorted(FTYPE_CODES.items()):
            log(f"  {code}: {name}")
        return

    if not args.state:
        parser.print_help()
        return

    states = [s.strip().upper() for s in args.state.split(",")]
    layers = [int(l.strip()) for l in args.layers.split(",")]

    log(f"Processing {len(states)} states: {', '.join(states)}")
    log(f"Layers: {layers}")

    for state in states:
        log("=" * 60)
        log(f"Processing NHD: {state}")
        log("=" * 60)

        # Download layers
        layer_files = download_state_nhd(state, layers)

        if not layer_files:
            log(f"  No data downloaded for {state}", "ERROR")
            continue

        files_to_upload = list(layer_files.values())
        merged_file = None

        # Merge layers if requested
        if args.merge and len(layer_files) > 1:
            merged_file = GEOJSON_DIR / f"nhd_{state.lower()}.geojson"
            merge_result = merge_nhd_layers(state, layer_files, merged_file)
            if merge_result:
                files_to_upload = [merge_result]

        # Generate PMTiles
        if args.pmtiles:
            for geojson_file in files_to_upload:
                pmtiles_name = Path(geojson_file).stem + ".pmtiles"
                pmtiles_path = PMTILES_DIR / pmtiles_name
                generate_pmtiles(geojson_file, pmtiles_path)
                files_to_upload.append(str(pmtiles_path))

        # Upload
        if args.upload:
            for file_path in files_to_upload:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    r2_key = f"enrichment/nhd/{filename}"
                    upload_to_r2(file_path, r2_key)

        # Cleanup
        if args.cleanup and args.upload:
            # Cleanup individual layer files
            cleanup_local(layer_files.values())
            # Cleanup merged file
            if merged_file and os.path.exists(merged_file):
                cleanup_local([str(merged_file)])
            # Cleanup PMTiles
            if args.pmtiles:
                pmtiles_files = list(PMTILES_DIR.glob(f"nhd_*{state.lower()}*.pmtiles"))
                cleanup_local([str(f) for f in pmtiles_files])

    log("=" * 60)
    log("NHD download complete!")
    log("=" * 60)


if __name__ == "__main__":
    main()
