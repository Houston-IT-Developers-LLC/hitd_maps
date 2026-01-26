#!/usr/bin/env python3
"""
Download parcel data for missing states from ArcGIS REST services.
Uses parallel workers to download quickly while respecting rate limits.
"""

import requests
import json
import os
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Output directory
OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/downloads")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ArcGIS REST service endpoints for missing states
SERVICES = {
    'parcels_fl_statewide': {
        'url': 'https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0',
        'state': 'FL',
        'max_per_request': 2000,
        'notes': 'Florida statewide parcels - 10.8M features'
    },
    'parcels_vt_statewide': {
        'url': 'https://services1.arcgis.com/BkFxaEFNwHqX3tAw/arcgis/rest/services/FS_VCGI_OPENDATA_Cadastral_VTPARCELS_poly_standardized_parcels_SP_v1/FeatureServer/0',
        'state': 'VT',
        'max_per_request': 2000,
        'notes': 'Vermont statewide parcels - 344K features, WKID 32145'
    },
    'parcels_ak_statewide': {
        'url': 'https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/AK_Parcels/FeatureServer/0',
        'state': 'AK',
        'max_per_request': 2000,
        'notes': 'Alaska statewide parcels - 410K features'
    },
    'parcels_id_statewide': {
        'url': 'https://services1.arcgis.com/CNPdEkvnGl65jCX8/arcgis/rest/services/Public_Idaho_Parcels_/FeatureServer/0',
        'state': 'ID',
        'max_per_request': 2000,
        'notes': 'Idaho public parcels - 380K features'
    },
    'parcels_mt_statewide': {
        'url': 'https://services.arcgis.com/iTQUx5ZpNUh47Geb/arcgis/rest/services/Montana_Parcel_Earliest_Build_Year/FeatureServer/0',
        'state': 'MT',
        'max_per_request': 2000,
        'notes': 'Montana parcels - 607K features'
    },
    'parcels_nv_statewide': {
        'url': 'https://arcgis.water.nv.gov/arcgis/rest/services/BaseLayers/County_Parcels_in_Nevada/MapServer/0',
        'state': 'NV',
        'max_per_request': 1000,
        'notes': 'Nevada county parcels - 1.4M features'
    },
    'parcels_al_mobile': {
        'url': 'https://services8.arcgis.com/HND1NcQt6vgOGn1z/arcgis/rest/services/MCRC_Public_Parcels/FeatureServer/0',
        'state': 'AL',
        'max_per_request': 2000,
        'notes': 'Mobile County Alabama - 213K features'
    },
    'parcels_ar_washington': {
        'url': 'https://services1.arcgis.com/G4bYaaas92zuKaUR/arcgis/rest/services/Parcels_Washington_County/FeatureServer/0',
        'state': 'AR',
        'max_per_request': 2000,
        'notes': 'Washington County Arkansas - 112K features'
    },
    'parcels_ok_comanche': {
        'url': 'https://services6.arcgis.com/eNPJk90aMrXNOKF8/arcgis/rest/services/Comanche_Parcels/FeatureServer/0',
        'state': 'OK',
        'max_per_request': 2000,
        'notes': 'Comanche County Oklahoma - 56K features'
    },
    'parcels_ms_hinds': {
        'url': 'https://services6.arcgis.com/rdiy8o2SBpQHoL4Q/arcgis/rest/services/HINDS_PARCELS/FeatureServer/0',
        'state': 'MS',
        'max_per_request': 2000,
        'notes': 'Hinds County Mississippi (Jackson area) - 114K features'
    },
    'parcels_sd_pennington': {
        'url': 'https://services1.arcgis.com/AhXvNWFdL7hH4TjJ/arcgis/rest/services/PenningtonParcels/FeatureServer/0',
        'state': 'SD',
        'max_per_request': 2000,
        'notes': 'Pennington County South Dakota (Rapid City) - 52K features'
    },
    'parcels_or_washington': {
        'url': 'https://gispub.co.washington.or.us/server/rest/services/Washington_County_Taxlots/FeatureServer/0',
        'state': 'OR',
        'max_per_request': 2000,
        'notes': 'Washington County Oregon - 200K features, WKID 2913'
    },
    'parcels_ms_harrison': {
        'url': 'https://gis.dmr.ms.gov/server/rest/services/BaseData/Parcels_Harrison/MapServer/0',
        'state': 'MS',
        'max_per_request': 1000,
        'notes': 'Harrison County Mississippi (Gulfport) - 208K population, MapServer'
    },
    'parcels_ms_madison': {
        'url': 'https://gis.cmpdd.org/arcgis/rest/services/Madison/TAXINFO/MapServer/0',
        'state': 'MS',
        'max_per_request': 2000,
        'notes': 'Madison County Mississippi - 109K population'
    },
}


def get_feature_count(url):
    """Get total feature count from service."""
    params = {
        'where': '1=1',
        'returnCountOnly': 'true',
        'f': 'json'
    }
    try:
        r = requests.get(f'{url}/query', params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            return data.get('count', 0)
    except Exception as e:
        print(f"Error getting count: {e}")
    return 0


def get_service_info(url):
    """Get service info including spatial reference."""
    try:
        r = requests.get(url, params={'f': 'json'}, timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Error getting service info: {e}")
    return {}


def download_batch(url, offset, limit, out_sr=4326):
    """Download a batch of features."""
    params = {
        'where': '1=1',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'geojson',
        'resultOffset': offset,
        'resultRecordCount': limit,
        'outSR': out_sr
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.get(f'{url}/query', params=params, timeout=120)
            if r.status_code == 200:
                data = r.json()
                if 'features' in data:
                    return data['features']
                elif 'error' in data:
                    print(f"  API error at offset {offset}: {data['error']}")
                    return []
        except requests.exceptions.Timeout:
            print(f"  Timeout at offset {offset}, attempt {attempt + 1}/{max_retries}")
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f"  Error at offset {offset}: {e}")
            time.sleep(1)

    return []


def download_service(name, config, max_workers=10):
    """Download all features from a service."""
    url = config['url']
    max_per_request = config.get('max_per_request', 2000)

    print(f"\n{'='*60}")
    print(f"Downloading: {name}")
    print(f"URL: {url}")
    print(f"Notes: {config.get('notes', 'N/A')}")
    print(f"{'='*60}")

    # Get total count
    total = get_feature_count(url)
    if total == 0:
        print("  No features found or service unavailable")
        return None

    print(f"  Total features: {total:,}")

    # Get service info
    info = get_service_info(url)
    extent = info.get('extent', {})
    sr = extent.get('spatialReference', {})
    wkid = sr.get('wkid') or sr.get('latestWkid')
    print(f"  Source WKID: {wkid}")

    # Calculate batches
    num_batches = math.ceil(total / max_per_request)
    print(f"  Batches: {num_batches} ({max_per_request} features per batch)")

    # Download in parallel
    all_features = []
    completed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i in range(num_batches):
            offset = i * max_per_request
            future = executor.submit(download_batch, url, offset, max_per_request)
            futures[future] = offset

        for future in as_completed(futures):
            offset = futures[future]
            try:
                features = future.result()
                all_features.extend(features)
                completed += 1

                # Progress update
                pct = (completed / num_batches) * 100
                elapsed = time.time() - start_time
                rate = len(all_features) / elapsed if elapsed > 0 else 0
                eta = (total - len(all_features)) / rate if rate > 0 else 0

                print(f"\r  Progress: {completed}/{num_batches} batches ({pct:.1f}%) - {len(all_features):,} features - {rate:.0f}/sec - ETA: {eta:.0f}s    ", end='', flush=True)
            except Exception as e:
                print(f"\n  Error processing batch at offset {offset}: {e}")

    print()  # Newline after progress

    elapsed = time.time() - start_time
    print(f"  Downloaded {len(all_features):,} features in {elapsed:.1f}s")

    if len(all_features) == 0:
        return None

    # Create GeoJSON
    geojson = {
        'type': 'FeatureCollection',
        'features': all_features
    }

    # Save to file
    output_path = OUTPUT_DIR / f"{name}.geojson"
    print(f"  Saving to: {output_path}")

    with open(output_path, 'w') as f:
        json.dump(geojson, f)

    file_size = output_path.stat().st_size / (1024 * 1024)
    print(f"  File size: {file_size:.1f} MB")

    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Download parcel data for missing states')
    parser.add_argument('--service', type=str, help='Download specific service only')
    parser.add_argument('--workers', type=int, default=10, help='Max parallel workers')
    parser.add_argument('--list', action='store_true', help='List available services')
    args = parser.parse_args()

    if args.list:
        print("Available services:")
        for name, config in SERVICES.items():
            print(f"  {name}")
            print(f"    State: {config['state']}")
            print(f"    Notes: {config.get('notes', 'N/A')}")
            print()
        return

    services_to_download = SERVICES
    if args.service:
        if args.service in SERVICES:
            services_to_download = {args.service: SERVICES[args.service]}
        else:
            print(f"Unknown service: {args.service}")
            print(f"Available: {list(SERVICES.keys())}")
            return

    print("="*60)
    print("PARCEL DATA DOWNLOADER")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Services to download: {len(services_to_download)}")
    print("="*60)

    results = []
    for name, config in services_to_download.items():
        try:
            path = download_service(name, config, max_workers=args.workers)
            if path:
                results.append((name, config['state'], path))
        except Exception as e:
            print(f"Failed to download {name}: {e}")

    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)
    print(f"Successfully downloaded: {len(results)} services")
    for name, state, path in results:
        print(f"  {name} ({state}): {path}")

    print("\nNext steps:")
    print("1. Reproject if needed: ogr2ogr -f GeoJSON -t_srs EPSG:4326 output.geojson input.geojson")
    print("2. Convert to PMTiles: tippecanoe -o output.pmtiles -l parcels --force input.geojson")
    print("3. Upload to R2: aws s3 cp output.pmtiles s3://gspot-tiles/")


if __name__ == '__main__':
    main()

# Additional county sources discovered
ADDITIONAL_SERVICES = {
    'parcels_sc_greenville': {
        'url': 'https://services.arcgis.com/zTM0LZtJeE1HzO09/arcgis/rest/services/kx_greenville_county_sc_tax_parcel_SHP/FeatureServer/0',
        'state': 'SC',
        'max_per_request': 2000,
        'notes': 'Greenville County SC - 215K features'
    },
    'parcels_sc_charleston': {
        'url': 'https://services1.arcgis.com/G0z1RCvykC1mcsVI/arcgis/rest/services/Parcels/FeatureServer/0',
        'state': 'SC',
        'max_per_request': 2000,
        'notes': 'Charleston area SC - 393K features'
    },
    'parcels_wy_campbell': {
        'url': 'https://services.arcgis.com/8TsfFS9tNkO3ZLZr/arcgis/rest/services/campbell_parcels/FeatureServer/0',
        'state': 'WY',
        'max_per_request': 2000,
        'notes': 'Campbell County WY - 20K features'
    },
}

# Merge additional services
SERVICES.update(ADDITIONAL_SERVICES)
