#!/usr/bin/env python3
"""Download remaining state parcel data (SC, WY)."""

import requests
import json
import os
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

OUTPUT_DIR = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/data/downloads")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SERVICES = {
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


def get_feature_count(url):
    params = {'where': '1=1', 'returnCountOnly': 'true', 'f': 'json'}
    try:
        r = requests.get(f'{url}/query', params=params, timeout=30)
        if r.status_code == 200:
            return r.json().get('count', 0)
    except:
        pass
    return 0


def download_batch(url, offset, limit):
    params = {
        'where': '1=1',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'geojson',
        'resultOffset': offset,
        'resultRecordCount': limit,
        'outSR': 4326
    }
    for attempt in range(3):
        try:
            r = requests.get(f'{url}/query', params=params, timeout=120)
            if r.status_code == 200:
                data = r.json()
                return data.get('features', [])
        except:
            time.sleep(2 ** attempt)
    return []


def download_service(name, config, max_workers=15):
    url = config['url']
    max_per_request = config.get('max_per_request', 2000)
    
    print(f"\n{'='*60}")
    print(f"Downloading: {name}")
    print(f"Notes: {config.get('notes', 'N/A')}")
    print(f"{'='*60}")
    
    total = get_feature_count(url)
    if total == 0:
        print("  No features found")
        return None
    
    print(f"  Total features: {total:,}")
    num_batches = math.ceil(total / max_per_request)
    print(f"  Batches: {num_batches}")
    
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
            features = future.result()
            all_features.extend(features)
            completed += 1
            pct = (completed / num_batches) * 100
            elapsed = time.time() - start_time
            rate = len(all_features) / elapsed if elapsed > 0 else 0
            print(f"\r  Progress: {completed}/{num_batches} ({pct:.1f}%) - {len(all_features):,} features - {rate:.0f}/sec", end='', flush=True)
    
    print()
    
    if not all_features:
        return None
    
    geojson = {'type': 'FeatureCollection', 'features': all_features}
    output_path = OUTPUT_DIR / f"{name}.geojson"
    
    with open(output_path, 'w') as f:
        json.dump(geojson, f)
    
    file_size = output_path.stat().st_size / (1024 * 1024)
    print(f"  Saved: {output_path} ({file_size:.1f} MB)")
    return output_path


def main():
    import sys
    service_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    if service_name:
        if service_name in SERVICES:
            download_service(service_name, SERVICES[service_name])
        else:
            print(f"Unknown service: {service_name}")
    else:
        for name, config in SERVICES.items():
            download_service(name, config)


if __name__ == '__main__':
    main()
