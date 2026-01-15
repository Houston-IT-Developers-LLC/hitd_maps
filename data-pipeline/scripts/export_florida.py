#!/usr/bin/env python3
"""Export Florida parcels by county number (1-67)"""
import json
import urllib.request
import urllib.parse
import time
import os
from pathlib import Path

SERVICE_URL = "https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0/query"
OUT_FIELDS = "OBJECTID,CO_NO,PARCEL_ID,DOR_UC,ASMNT_YR"
BATCH_SIZE = 2000

def export_county(county_no, output_dir):
    """Export a single county by number."""
    all_features = []
    offset = 0
    
    print(f"[{county_no}/67] Exporting county {county_no}...")
    
    while True:
        params = {
            'where': f"CO_NO={county_no}",
            'outFields': OUT_FIELDS,
            'returnGeometry': 'true',
            'outSR': '4326',
            'f': 'geojson',
            'resultOffset': offset,
            'resultRecordCount': BATCH_SIZE
        }
        url = f"{SERVICE_URL}?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                data = json.load(response)
                features = data.get('features', [])
                if not features:
                    break
                all_features.extend(features)
                print(f"    Fetched {len(features):,} (total: {len(all_features):,})")
                offset += BATCH_SIZE
                time.sleep(0.3)
        except Exception as e:
            print(f"    Error: {e}")
            break
    
    if all_features:
        output_file = Path(output_dir) / f"FL_{county_no:02d}.geojson"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump({"type": "FeatureCollection", "features": all_features}, f)
        size_mb = output_file.stat().st_size / (1024*1024)
        print(f"    Saved {len(all_features):,} features ({size_mb:.1f} MB)")
    return len(all_features)

if __name__ == "__main__":
    output_dir = "./output/geojson/fl/counties"
    total = 0
    for county in range(1, 68):
        count = export_county(county, output_dir)
        total += count
    print(f"\nTotal: {total:,} features")
