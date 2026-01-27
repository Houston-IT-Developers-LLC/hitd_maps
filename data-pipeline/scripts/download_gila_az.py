#!/usr/bin/env python3
"""Download Gila County, AZ parcels from MapServer"""

import requests
import json
import time
import sys

BASE_URL = "https://gis.gilacountyaz.gov/arcgis/rest/services/Assessor/ParcelsTyler/MapServer/0/query"
OUTPUT_FILE = "/home/exx/Documents/C/hitd_maps/data-pipeline/downloads/az_gila/parcels_raw.geojson"

def download_parcels():
    """Download all parcels with pagination"""
    
    # First, get total count
    count_params = {
        'where': '1=1',
        'returnCountOnly': 'true',
        'f': 'json'
    }
    
    response = requests.get(BASE_URL, params=count_params)
    total_count = response.json()['count']
    print(f"Total parcels: {total_count:,}")
    
    # Download in chunks
    all_features = []
    offset = 0
    chunk_size = 1000
    
    while offset < total_count:
        print(f"Downloading {offset:,} to {min(offset + chunk_size, total_count):,}...")
        
        params = {
            'where': '1=1',
            'outFields': '*',
            'geometryPrecision': 6,
            'outSR': 4326,  # Request WGS84 directly
            'f': 'geojson',
            'resultOffset': offset,
            'resultRecordCount': chunk_size
        }
        
        try:
            response = requests.get(BASE_URL, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if 'features' in data:
                all_features.extend(data['features'])
                print(f"  Got {len(data['features'])} features")
            else:
                print(f"  No features in response: {data}")
                break
                
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(5)
            continue
        
        offset += chunk_size
        time.sleep(0.5)  # Be nice to the server
    
    # Create GeoJSON FeatureCollection
    geojson = {
        'type': 'FeatureCollection',
        'features': all_features
    }
    
    # Write to file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(geojson, f)
    
    print(f"\n✓ Downloaded {len(all_features):,} parcels")
    print(f"✓ Saved to {OUTPUT_FILE}")
    
    return len(all_features)

if __name__ == '__main__':
    try:
        count = download_parcels()
        sys.exit(0 if count > 0 else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
