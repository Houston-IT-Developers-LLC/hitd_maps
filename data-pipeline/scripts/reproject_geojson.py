#!/usr/bin/env python3
"""Reproject GeoJSON from Web Mercator (EPSG:3857) to WGS84 (EPSG:4326)."""

import json
import sys
from pyproj import Transformer

def transform_coordinates(coords, transformer):
    """Recursively transform coordinates."""
    if isinstance(coords[0], (int, float)):
        # This is a point [x, y] or [x, y, z]
        lng, lat = transformer.transform(coords[0], coords[1])
        if len(coords) > 2:
            return [lng, lat, coords[2]]
        return [lng, lat]
    else:
        # This is a list of coordinates
        return [transform_coordinates(c, transformer) for c in coords]

def reproject_geojson(input_path, output_path):
    """Reproject GeoJSON file from EPSG:3857 to EPSG:4326."""
    # Create transformer: 3857 (Web Mercator) -> 4326 (WGS84)
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    print(f"Loading {input_path}...")
    with open(input_path, 'r') as f:
        data = json.load(f)

    print(f"Reprojecting {len(data.get('features', []))} features...")

    for i, feature in enumerate(data.get('features', [])):
        if i % 50000 == 0:
            print(f"  Progress: {i}/{len(data['features'])}")

        geom = feature.get('geometry')
        if geom and geom.get('coordinates'):
            geom['coordinates'] = transform_coordinates(geom['coordinates'], transformer)

    # Update CRS if present
    if 'crs' in data:
        data['crs'] = {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}
        }

    print(f"Writing {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(data, f)

    print("Done!")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 reproject_geojson.py <input.geojson> <output.geojson>")
        sys.exit(1)

    reproject_geojson(sys.argv[1], sys.argv[2])
