#!/usr/bin/env python3
"""
Fix coordinate system issues in Harris County GeoJSON.

The source data has coordinates that are:
1. Swapped: [lat, lng] instead of [lng, lat]
2. Longitude shifted by +172.5
3. Latitude offset by approximately -1.66 degrees
"""

import json
import sys
import re

# Offset values determined by comparing known locations
LAT_OFFSET = 1.66  # Add this to latitude
LNG_SHIFT = 172.5  # Subtract this from the shifted longitude value

def fix_coord_pair(coord):
    """Fix a single coordinate pair."""
    if not isinstance(coord, list) or len(coord) < 2:
        return coord

    val1 = coord[0]  # In source data, this is latitude (~26-30)
    val2 = coord[1]  # In source data, this is shifted longitude (~76-78)

    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
        # Check if this looks like our corrupted format [lat, shifted_lng]
        if 25 < val1 < 32 and 74 < val2 < 80:
            lng_fixed = val2 - LNG_SHIFT
            lat_fixed = val1 + LAT_OFFSET
            return [lng_fixed, lat_fixed]
        elif -100 < val1 < -90 and 25 < val2 < 32:
            if val2 < 29:
                return [val1, val2 + LAT_OFFSET]
            return coord
        else:
            return coord
    return coord

def fix_coords(coords):
    """Recursively fix coordinates in nested arrays."""
    if not coords:
        return coords

    if isinstance(coords, list) and len(coords) >= 2:
        if isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float)):
            return fix_coord_pair(coords)
        else:
            return [fix_coords(c) for c in coords]
    elif isinstance(coords, list):
        return [fix_coords(c) for c in coords]
    return coords

def process_file(input_path, output_path):
    """Process a GeoJSON file and fix coordinates."""
    print(f"Reading: {input_path}")
    print(f"Applying: LAT_OFFSET=+{LAT_OFFSET}, LNG_SHIFT=-{LNG_SHIFT}")

    # Read entire file
    with open(input_path, 'r') as f:
        content = f.read()

    # Parse as JSON
    print("Parsing JSON (this may take a moment for large files)...")
    data = json.loads(content)

    features = data.get('features', [])
    total = len(features)
    print(f"Found {total:,} features")

    # Process each feature
    for i, feature in enumerate(features):
        if feature and feature.get('geometry') and feature['geometry'].get('coordinates'):
            feature['geometry']['coordinates'] = fix_coords(feature['geometry']['coordinates'])

        if (i + 1) % 100000 == 0:
            print(f"  Processed {i + 1:,} / {total:,} features...")

    # Write output
    print(f"Writing to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(data, f)

    print(f"\nComplete! Processed {total:,} features")
    return total

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: fix_harris_coords_v2.py input.geojson output.geojson")
        sys.exit(1)

    process_file(sys.argv[1], sys.argv[2])
