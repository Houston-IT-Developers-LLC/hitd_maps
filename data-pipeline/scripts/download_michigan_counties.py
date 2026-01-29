#!/usr/bin/env python3
"""
Download parcel data for priority Michigan counties from ArcGIS REST services.
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

# Michigan County ArcGIS REST service endpoints
SERVICES = {
    'parcels_mi_monroe': {
        'url': 'https://gis.monroemi.gov/server/rest/services/Hosted/Parcels_V2/FeatureServer/0',
        'state': 'MI',
        'county': 'Monroe',
        'max_per_request': 2000,
        'notes': 'Monroe County Michigan (154K pop) - FeatureServer VERIFIED'
    },
    'parcels_mi_jackson': {
        'url': 'https://gis.mijackson.org/countygis/rest/services/RealEstate/RealEstateParcels/MapServer/0',
        'state': 'MI',
        'county': 'Jackson',
        'max_per_request': 1000,
        'notes': 'Jackson County Michigan (160K pop, Jackson) - MapServer (different API)'
    },
    # Add more counties as endpoints are discovered
    'parcels_mi_ingham': {
        'url': 'TBD',  # MSU RS&GIS hosted - need to discover endpoint
        'state': 'MI',
        'county': 'Ingham',
        'max_per_request': 2000,
        'notes': 'Ingham County Michigan (284K pop, Lansing) - MSU RS&GIS'
    },
    'parcels_mi_saginaw': {
        'url': 'TBD',  # SAGA GIS/FetchGIS - need to discover endpoint
        'state': 'MI',
        'county': 'Saginaw',
        'max_per_request': 2000,
        'notes': 'Saginaw County Michigan (190K pop) - SAGA GIS'
    },
    'parcels_mi_berrien': {
        'url': 'TBD',  # Beacon/Schneider system - may need different approach
        'state': 'MI',
        'county': 'Berrien',
        'max_per_request': 2000,
        'notes': 'Berrien County Michigan (154K pop) - Beacon system'
    },
    'parcels_mi_bay': {
        'url': 'TBD',  # Open Data portal - need to find FeatureServer
        'state': 'MI',
        'county': 'Bay',
        'max_per_request': 2000,
        'notes': 'Bay County Michigan (103K pop) - Open Data portal'
    },
    'parcels_mi_genesee': {
        'url': 'https://gis.gcrc.org/arcgis/rest/services/GCRC/GCRC_Properties_real/FeatureServer/0',
        'state': 'MI',
        'county': 'Genesee',
        'max_per_request': 2000,
        'notes': 'Genesee County Michigan (402K pop, Flint) - GCRC GIS'
    },
    'parcels_mi_washtenaw': {
        'url': 'https://services.arcgis.com/f4rR7WnIfGBdVYFd/arcgis/rest/services/Parcels/FeatureServer/0',
        'state': 'MI',
        'county': 'Washtenaw',
        'max_per_request': 1000,
        'notes': 'Washtenaw County Michigan (367K pop, Ann Arbor) - Open Data Portal'
    },
    'parcels_mi_kalamazoo': {
        'url': 'https://gis.kalcounty.com/server/rest/services/Hosted/Parcels__2025_/FeatureServer/0',
        'state': 'MI',
        'county': 'Kalamazoo',
        'max_per_request': 2000,
        'notes': 'Kalamazoo County Michigan (262K pop) - 2025 parcel data'
    },
    'parcels_mi_grand_traverse': {
        'url': 'https://gis.grandtraverse.org/arcgis/rest/services/Treasurer/Parcel20/FeatureServer/0',
        'state': 'MI',
        'county': 'Grand Traverse',
        'max_per_request': 2000,
        'notes': 'Grand Traverse County Michigan (95K pop, Traverse City) - VERIFIED'
    },
    'parcels_mi_marquette': {
        'url': 'https://services9.arcgis.com/6EuFgO4fLTqfNOhu/ArcGIS/rest/services/MarquetteParcelData/FeatureServer/0',
        'state': 'MI',
        'county': 'Marquette',
        'max_per_request': 2000,
        'notes': 'Marquette County Michigan (66K pop) - VERIFIED'
    },
    'parcels_mi_arenac': {
        'url': 'https://services8.arcgis.com/SWvtgOskziun2bFF/arcgis/rest/services/Arenac_Parcel_2026/FeatureServer/0',
        'state': 'MI',
        'county': 'Arenac',
        'max_per_request': 2000,
        'notes': 'Arenac County Michigan (15K pop) - 2026 parcel data'
    },
    'parcels_mi_livingston': {
        'url': 'https://gis.livgov.com/arcgis/rest/services/BaseData/Parcels/FeatureServer/0',
        'state': 'MI',
        'county': 'Livingston',
        'max_per_request': 2000,
        'notes': 'Livingston County Michigan (193K pop) - County GIS'
    },
    'parcels_mi_st_clair': {
        'url': 'https://gis.stclaircounty.org/arcgis/rest/services/Parcels/FeatureServer/0',
        'state': 'MI',
        'county': 'St. Clair',
        'max_per_request': 2000,
        'notes': 'St. Clair County Michigan (160K pop) - County GIS'
    },
    'parcels_mi_lenawee': {
        'url': 'https://services1.arcgis.com/m7djDD6l7d4cGuWe/arcgis/rest/services/Lenawee_Parcels/FeatureServer/0',
        'state': 'MI',
        'county': 'Lenawee',
        'max_per_request': 2000,
        'notes': 'Lenawee County Michigan (99K pop) - ArcGIS Online'
    },
    'parcels_mi_calhoun': {
        'url': 'https://gis.calhouncountymi.gov/arcgis/rest/services/Parcels/MapServer/0',
        'state': 'MI',
        'county': 'Calhoun',
        'max_per_request': 2000,
        'notes': 'Calhoun County Michigan (134K pop, Battle Creek) - MapServer'
    },
    'parcels_mi_clinton': {
        'url': 'https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services/Parcels/FeatureServer/0',
        'state': 'MI',
        'county': 'Clinton',
        'max_per_request': 2000,
        'notes': 'Clinton County Michigan (79K pop) - ArcGIS Online'
    },
    'parcels_mi_eaton': {
        'url': 'https://services8.arcgis.com/kSWeZLv5KXVYeave/arcgis/rest/services/Parcels/FeatureServer/0',
        'state': 'MI',
        'county': 'Eaton',
        'max_per_request': 2000,
        'notes': 'Eaton County Michigan (109K pop, Lansing area) - ArcGIS Online'
    },
    'parcels_mi_allegan': {
        'url': 'https://services6.arcgis.com/FU0UxR6xC00IS3t1/arcgis/rest/services/Parcels/FeatureServer/0',
        'state': 'MI',
        'county': 'Allegan',
        'max_per_request': 2000,
        'notes': 'Allegan County Michigan (120K pop) - ArcGIS Online'
    },
}


def get_feature_count(service_url):
    """Get total feature count from service"""
    try:
        params = {
            'where': '1=1',
            'returnCountOnly': 'true',
            'f': 'json'
        }
        response = requests.get(f"{service_url}/query", params=params, timeout=30)
        data = response.json()
        return data.get('count', 0)
    except Exception as e:
        print(f"Error getting count: {e}")
        return None


def download_chunk(service_url, offset, max_records, chunk_id, output_file):
    """Download a single chunk of features"""
    params = {
        'where': '1=1',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'geojson',
        'resultOffset': offset,
        'resultRecordCount': max_records
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{service_url}/query", params=params, timeout=120)
            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])

                if features:
                    # Save chunk to temp file
                    chunk_file = output_file.parent / f"{output_file.stem}_chunk_{chunk_id}.geojson"
                    with open(chunk_file, 'w') as f:
                        json.dump(data, f)

                    return len(features), chunk_file
                return 0, None
            else:
                print(f"HTTP {response.status_code} for chunk {chunk_id}, attempt {attempt+1}")
                time.sleep(2 ** attempt)
        except Exception as e:
            print(f"Error downloading chunk {chunk_id}, attempt {attempt+1}: {e}")
            time.sleep(2 ** attempt)

    return 0, None


def merge_chunks(chunk_files, output_file):
    """Merge all chunk files into single GeoJSON"""
    all_features = []

    for chunk_file in sorted(chunk_files):
        if chunk_file.exists():
            with open(chunk_file, 'r') as f:
                data = json.load(f)
                all_features.extend(data.get('features', []))
            chunk_file.unlink()  # Delete chunk after merging

    # Create final GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }

    with open(output_file, 'w') as f:
        json.dump(geojson, f)

    return len(all_features)


def download_service(service_name, service_config, workers=4):
    """Download all features from a service"""
    service_url = service_config['url']

    if service_url == 'TBD':
        print(f"\nSkipping {service_name}: Endpoint not yet discovered")
        return

    print(f"\n{'='*80}")
    print(f"Downloading {service_name}")
    print(f"County: {service_config['county']}, State: {service_config['state']}")
    print(f"Notes: {service_config['notes']}")
    print(f"{'='*80}\n")

    # Get total count
    total_features = get_feature_count(service_url)
    if not total_features:
        print(f"ERROR: Could not get feature count for {service_name}")
        return

    print(f"Total features: {total_features:,}")

    max_per_request = service_config['max_per_request']
    total_chunks = math.ceil(total_features / max_per_request)
    print(f"Will download in {total_chunks} chunks using {workers} workers\n")

    # Output file
    output_file = OUTPUT_DIR / f"{service_name}.geojson"

    # Download chunks in parallel
    chunk_files = []
    downloaded = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for i in range(total_chunks):
            offset = i * max_per_request
            future = executor.submit(
                download_chunk,
                service_url,
                offset,
                max_per_request,
                i,
                output_file
            )
            futures[future] = i

        for future in as_completed(futures):
            chunk_id = futures[future]
            try:
                feature_count, chunk_file = future.result()
                downloaded += feature_count
                if chunk_file:
                    chunk_files.append(chunk_file)

                progress = (downloaded / total_features) * 100
                print(f"Progress: {downloaded:,}/{total_features:,} features ({progress:.1f}%)")
            except Exception as e:
                print(f"Error in chunk {chunk_id}: {e}")

    # Merge all chunks
    print(f"\nMerging {len(chunk_files)} chunks...")
    final_count = merge_chunks(chunk_files, output_file)

    print(f"\n✓ Download complete!")
    print(f"  Output: {output_file}")
    print(f"  Features: {final_count:,}")
    print(f"  File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Download Michigan county parcel data')
    parser.add_argument('--service', help='Specific service to download (default: all with valid URLs)')
    parser.add_argument('--workers', type=int, default=10, help='Number of parallel workers (default: 10)')
    parser.add_argument('--list', action='store_true', help='List available services')

    args = parser.parse_args()

    if args.list:
        print("\nAvailable services:")
        for name, config in SERVICES.items():
            print(f"\n  {name}")
            print(f"    County: {config['county']}")
            print(f"    State: {config['state']}")
            print(f"    URL: {config['url']}")
            print(f"    Notes: {config['notes']}")
        print()
        return

    if args.service:
        if args.service not in SERVICES:
            print(f"ERROR: Unknown service '{args.service}'")
            print("Use --list to see available services")
            return

        download_service(args.service, SERVICES[args.service], args.workers)
    else:
        # Download all services with valid URLs
        for service_name, service_config in SERVICES.items():
            if service_config['url'] != 'TBD':
                download_service(service_name, service_config, args.workers)
            else:
                print(f"Skipping {service_name}: URL not yet discovered")


if __name__ == '__main__':
    main()
