#!/usr/bin/env python3
"""
Download HIFLD (Homeland Infrastructure Foundation-Level Data) Critical Infrastructure

Sources:
- HIFLD Open Data: https://hifld-geoplatform.opendata.arcgis.com/
- NCES: https://nces.ed.gov/
- Esri Living Atlas

Datasets included:
1. Hospitals (8,013 records)
2. Fire/EMS Stations (3,589 records)
3. Police Stations (18,258 records)
4. Public Schools (102,334 records)
5. Private Schools (22,510 records)
6. Colleges (6,605 records)

Total: ~163,000 records

Update Frequency: Varies by dataset (typically quarterly to annually)
Date Updated: 2026-01-17
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output" / "enrichment"
RAW_DIR = OUTPUT_DIR / "raw" / "hifld"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PMTILES_DIR = OUTPUT_DIR / "pmtiles"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

# HIFLD Dataset Definitions (Updated 2026-01-17 with working URLs)
HIFLD_DATASETS = {
    "hospitals": {
        "url": "https://services7.arcgis.com/JEwYeAy2cc8qOe3o/arcgis/rest/services/hifld_hospitals/FeatureServer/0",
        "layer_name": "hospitals",
        "description": "Hospitals and medical centers across the United States",
        "state_field": "STATE",
    },
    "fire_ems_stations": {
        "url": "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Structures_Medical_Emergency_Response_v1/FeatureServer/2",
        "layer_name": "fire_ems_stations",
        "description": "Fire stations and EMS stations",
        "state_field": "STATE",
    },
    "police": {
        "url": "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Structures_Law_Enforcement_v1/FeatureServer/0",
        "layer_name": "police",
        "description": "Local law enforcement and police stations",
        "state_field": "STATE",
    },
    "public_schools": {
        "url": "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/HIFLD_Public_Schools_Placekey/FeatureServer/0",
        "layer_name": "public_schools",
        "description": "Public schools (K-12)",
        "state_field": "STATE",
    },
    "private_schools": {
        "url": "https://services1.arcgis.com/Ua5sjt3LWTPigjyD/arcgis/rest/services/Private_School_Locations_Current/FeatureServer/0",
        "layer_name": "private_schools",
        "description": "Private schools (K-12)",
        "state_field": "STATE",
    },
    "colleges": {
        "url": "https://services1.arcgis.com/Ua5sjt3LWTPigjyD/arcgis/rest/services/Postsecondary_School_Locations_Current/FeatureServer/0",
        "layer_name": "colleges",
        "description": "Colleges and universities",
        "state_field": "STATE",
    },
}


def log(message: str, level: str = "INFO"):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories."""
    for dir_path in [RAW_DIR, GEOJSON_DIR, PMTILES_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    log(f"Directories ready: {OUTPUT_DIR}")


def fetch_arcgis_features(
    base_url: str,
    where_clause: str = "1=1",
    max_records: int = 2000,
    out_fields: str = "*",
) -> List[Dict[str, Any]]:
    """
    Fetch all features from an ArcGIS Feature Server with pagination.
    """
    all_features = []
    offset = 0
    
    # Create SSL context that doesn't verify certificates (for some ArcGIS servers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    while True:
        params = {
            "where": where_clause,
            "outFields": out_fields,
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": max_records,
        }
        
        url = f"{base_url}/query?{urllib.parse.urlencode(params)}"
        
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                data = json.loads(response.read().decode())
                
                if "error" in data:
                    log(f"  API Error: {data['error']}", "ERROR")
                    break
                
                features = data.get("features", [])
                if not features:
                    break
                
                all_features.extend(features)
                log(f"    Fetched {len(features)} features (total: {len(all_features)})")
                
                # Check if we got fewer than requested (last page)
                if len(features) < max_records:
                    break
                
                offset += max_records
                
        except urllib.error.HTTPError as e:
            log(f"  HTTP Error {e.code}: {e.reason}", "ERROR")
            break
        except urllib.error.URLError as e:
            log(f"  URL Error: {e.reason}", "ERROR")
            break
        except Exception as e:
            log(f"  Error: {str(e)}", "ERROR")
            break
    
    return all_features


def download_dataset(
    dataset_name: str,
    state: Optional[str] = None,
    force: bool = False,
) -> Optional[Path]:
    """
    Download a specific HIFLD dataset.
    """
    if dataset_name not in HIFLD_DATASETS:
        log(f"Unknown dataset: {dataset_name}", "ERROR")
        log(f"Available datasets: {', '.join(HIFLD_DATASETS.keys())}")
        return None

    dataset_info = HIFLD_DATASETS[dataset_name]

    # Determine output filename
    if state:
        output_file = GEOJSON_DIR / f"hifld_{dataset_name}_{state.lower()}.geojson"
        where_clause = f"{dataset_info['state_field']} = '{state.upper()}'"
    else:
        output_file = GEOJSON_DIR / f"hifld_{dataset_name}.geojson"
        where_clause = "1=1"

    # Check if file exists
    if output_file.exists() and not force:
        log(f"  File exists: {output_file} (use --force to re-download)")
        return output_file

    log("=" * 60)
    log(f"Downloading: {dataset_info['description']}")
    log("=" * 60)
    log(f"  Querying: {dataset_info['url']}")
    log(f"  Filter: {where_clause}")

    # Fetch features
    features = fetch_arcgis_features(dataset_info['url'], where_clause)

    if not features:
        log(f"No features returned for {dataset_name}", "ERROR")
        return None

    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "source": "HIFLD/NCES",
            "dataset": dataset_name,
            "description": dataset_info["description"],
            "download_date": datetime.now().isoformat(),
            "feature_count": len(features),
        }
    }

    # Write to file
    with open(output_file, 'w') as f:
        json.dump(geojson, f)

    log(f"  Saved: {output_file}")
    log(f"  Features: {len(features):,}")
    
    return output_file


def download_all_datasets(
    state: Optional[str] = None,
    force: bool = False,
) -> Dict[str, Optional[Path]]:
    """
    Download all HIFLD datasets.
    """
    results = {}
    
    for dataset_name in HIFLD_DATASETS:
        log("")
        path = download_dataset(dataset_name, state=state, force=force)
        results[dataset_name] = path

    return results


def generate_pmtiles(geojson_path: Path, output_name: Optional[str] = None) -> Optional[Path]:
    """
    Generate PMTiles from a GeoJSON file using tippecanoe.
    """
    if not geojson_path.exists():
        log(f"GeoJSON file not found: {geojson_path}", "ERROR")
        return None

    if output_name is None:
        output_name = geojson_path.stem

    output_path = PMTILES_DIR / f"{output_name}.pmtiles"

    log(f"  Generating PMTiles: {output_path.name}")

    # Tippecanoe command
    cmd = [
        "tippecanoe",
        "-o", str(output_path),
        "-z", "14",  # Max zoom
        "-Z", "4",   # Min zoom
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "--force",
        str(geojson_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            log(f"  tippecanoe error: {result.stderr}", "ERROR")
            return None
        log(f"  Created: {output_path}")
        return output_path
    except subprocess.TimeoutExpired:
        log("  tippecanoe timeout", "ERROR")
        return None
    except FileNotFoundError:
        log("  tippecanoe not found - please install it", "ERROR")
        return None


def upload_to_r2(local_path: Path, r2_key: str) -> bool:
    """
    Upload a file to Cloudflare R2 using AWS CLI.
    """
    if not local_path.exists():
        log(f"File not found: {local_path}", "ERROR")
        return False

    log(f"  Uploading: {local_path.name} -> {r2_key}")

    cmd = [
        "aws", "s3", "cp",
        str(local_path),
        f"s3://{R2_BUCKET}/{r2_key}",
        "--endpoint-url", R2_ENDPOINT,
    ]

    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"] = R2_ACCESS_KEY
    env["AWS_SECRET_ACCESS_KEY"] = R2_SECRET_KEY

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
        if result.returncode != 0:
            log(f"  Upload error: {result.stderr}", "ERROR")
            return False
        log(f"  Uploaded: {R2_PUBLIC_URL}/{r2_key}")
        return True
    except subprocess.TimeoutExpired:
        log("  Upload timeout", "ERROR")
        return False
    except FileNotFoundError:
        log("  AWS CLI not found - please install it", "ERROR")
        return False


def cleanup_local_files(paths: List[Path]):
    """Delete local files after successful upload."""
    for path in paths:
        if path and path.exists():
            path.unlink()
            log(f"  Deleted: {path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download HIFLD Critical Infrastructure datasets"
    )
    parser.add_argument(
        "--dataset",
        choices=list(HIFLD_DATASETS.keys()),
        help="Specific dataset to download",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all datasets",
    )
    parser.add_argument(
        "--state",
        help="Filter by state (e.g., CA, TX)",
    )
    parser.add_argument(
        "--pmtiles",
        action="store_true",
        help="Generate PMTiles after download",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload to R2 after generation",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete local files after upload",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if files exist",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available datasets",
    )
    
    args = parser.parse_args()
    
    # List datasets
    if args.list:
        log("Available HIFLD datasets:")
        for name, info in HIFLD_DATASETS.items():
            log(f"  {name:16} - {info['description']}")
        return

    # Validate arguments
    if not args.all and not args.dataset:
        parser.print_help()
        return

    ensure_directories()

    log("=" * 60)
    log("HIFLD Critical Infrastructure Download")
    log("=" * 60)
    log(f"Datasets: {', '.join(HIFLD_DATASETS.keys())}")
    log(f"Coverage: {'State: ' + args.state.upper() if args.state else 'National'}")
    log("=" * 60)

    # Download
    if args.all:
        results = download_all_datasets(state=args.state, force=args.force)
    else:
        path = download_dataset(args.dataset, state=args.state, force=args.force)
        results = {args.dataset: path}

    # Filter successful downloads
    downloaded_files = {k: v for k, v in results.items() if v is not None}
    
    if not downloaded_files:
        log("No files downloaded", "ERROR")
        return

    # Generate PMTiles
    pmtiles_files = []
    if args.pmtiles:
        log("")
        log("=" * 60)
        log("Generating PMTiles")
        log("=" * 60)
        for name, geojson_path in downloaded_files.items():
            pmtiles_path = generate_pmtiles(geojson_path)
            if pmtiles_path:
                pmtiles_files.append(pmtiles_path)

    # Upload to R2
    uploaded_files = []
    if args.upload:
        log("")
        log("=" * 60)
        log("Uploading to R2")
        log("=" * 60)
        for pmtiles_path in pmtiles_files:
            r2_key = f"enrichment/hifld/{pmtiles_path.name}"
            if upload_to_r2(pmtiles_path, r2_key):
                uploaded_files.append(pmtiles_path)

    # Cleanup
    if args.cleanup and uploaded_files:
        log("")
        log("=" * 60)
        log("Cleaning up local files")
        log("=" * 60)
        # Clean up both GeoJSON and PMTiles
        all_files = list(downloaded_files.values()) + pmtiles_files
        cleanup_local_files(all_files)

    # Summary
    log("")
    log("=" * 60)
    log("HIFLD Download Complete!")
    log("=" * 60)
    log(f"Downloaded: {len(downloaded_files)} GeoJSON files")
    if pmtiles_files:
        log(f"Generated: {len(pmtiles_files)} PMTiles files")
    if uploaded_files:
        log(f"Uploaded: {len(uploaded_files)} files to R2")
        log(f"Base URL: {R2_PUBLIC_URL}/enrichment/hifld/")
    log("=" * 60)


if __name__ == "__main__":
    main()
