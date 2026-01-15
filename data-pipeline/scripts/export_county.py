#!/usr/bin/env python3
"""
Export a single Texas county's parcels from TNRIS ArcGIS Feature Service.
Handles pagination (2000 record limit) automatically.
"""

import sys
import json
import urllib.request
import urllib.parse
import time
import os

TNRIS_SERVICE = "https://feature.tnris.org/arcgis/rest/services/Parcels/stratmap25_land_parcels_48/MapServer/0/query"

# Fields to export
OUT_FIELDS = "objectid,prop_id,geo_id,owner_name,county,situs_addr,situs_city,mkt_value,land_value,imp_value,legal_area,gis_area,lgl_area_unit,tax_year"

def fetch_county(county_name, output_file, max_records=None):
    """Fetch all parcels for a county with pagination."""
    all_features = []
    offset = 0
    batch_size = 2000

    print(f"Exporting {county_name} County...")

    while True:
        params = {
            'where': f"county='{county_name}'",
            'outFields': OUT_FIELDS,
            'returnGeometry': 'true',
            'outSR': '4326',
            'f': 'geojson',
            'resultOffset': offset,
            'resultRecordCount': batch_size
        }

        url = f"{TNRIS_SERVICE}?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                data = json.load(response)
                features = data.get('features', [])

                if not features:
                    break

                all_features.extend(features)
                print(f"  Fetched {len(features)} records (total: {len(all_features)})")

                offset += batch_size

                if max_records and len(all_features) >= max_records:
                    all_features = all_features[:max_records]
                    break

                # Rate limiting
                time.sleep(0.3)

        except Exception as e:
            print(f"  Error at offset {offset}: {e}")
            break

    # Save to file
    output = {
        "type": "FeatureCollection",
        "features": all_features
    }

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(output, f)

    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"  Saved {len(all_features)} features to {output_file} ({size_mb:.1f} MB)")

    return len(all_features)

def main():
    if len(sys.argv) < 3:
        print("Usage: export_county.py <county_name> <output_file> [max_records]")
        print("Example: export_county.py MONTGOMERY ./output/MONTGOMERY.geojson")
        sys.exit(1)

    county = sys.argv[1].upper()
    output_file = sys.argv[2]
    max_records = int(sys.argv[3]) if len(sys.argv) > 3 else None

    fetch_county(county, output_file, max_records)

if __name__ == "__main__":
    main()
