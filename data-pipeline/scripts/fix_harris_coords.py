#!/usr/bin/env python3
"""
Fix coordinate system issues in Harris County GeoJSON.

The source data has coordinates in format [lat, lng+172.5]:
- First value is latitude (around 26-30 for Houston area)
- Second value is longitude shifted by +172.5 (around 76-78 instead of -96 to -94)

This script fixes coordinates to proper GeoJSON [lng, lat] format.
"""

import json
import sys
from pathlib import Path

def fix_coord_pair(coord):
    """Fix a single coordinate pair [lat, lng_shifted] -> [lng, lat]."""
    if not isinstance(coord, list) or len(coord) < 2:
        return coord

    val1 = coord[0]
    val2 = coord[1]

    # Check if this looks like [lat, shifted_lng]
    # Latitude should be 26-31 for Houston area
    # Shifted longitude should be 76-78 (actual -96 to -94 + 172.5)
    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
        # val1 appears to be latitude (26-31)
        # val2 appears to be shifted longitude (76-78)
        if 25 < val1 < 32 and 74 < val2 < 80:
            # Fix: [lng_fixed, lat]
            lng_fixed = val2 - 172.5
            lat = val1
            return [lng_fixed, lat]
        elif -100 < val1 < -90 and 25 < val2 < 32:
            # Already fixed format [lng, lat] - return as is
            return coord
        else:
            # Unknown format - return as is
            return coord
    return coord

def fix_coords(coords):
    """Recursively fix coordinates in nested arrays."""
    if not coords:
        return coords

    # Check if this is a coordinate pair [x, y]
    if isinstance(coords, list) and len(coords) >= 2:
        if isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float)):
            # This is a coordinate pair
            return fix_coord_pair(coords)
        else:
            # This is a nested array (ring, polygon, etc.)
            return [fix_coords(c) for c in coords]
    elif isinstance(coords, list):
        return [fix_coords(c) for c in coords]
    return coords

def process_file(input_path, output_path):
    """Process a GeoJSON file and fix coordinates."""
    print(f"Reading: {input_path}")

    features_processed = 0
    features_with_geom = 0
    fixed_coords = 0
    already_correct = 0

    with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
        # Write header
        outfile.write('{\n"type": "FeatureCollection",\n"features": [\n')

        first_feature = True
        in_features = False

        for line in infile:
            line = line.strip()

            # Skip header lines
            if '"type": "FeatureCollection"' in line or '"features": [' in line:
                if '"features": [' in line:
                    in_features = True
                continue

            # Skip closing brackets
            if line in [']', ']}', ']}\n', '']:
                continue

            # Process features
            if in_features and line.startswith('{'):
                # Remove trailing comma if present
                if line.endswith(','):
                    line = line[:-1]

                try:
                    feature = json.loads(line)

                    if feature.get('geometry') and feature['geometry'].get('coordinates'):
                        old_coords = feature['geometry']['coordinates']
                        feature['geometry']['coordinates'] = fix_coords(old_coords)
                        features_with_geom += 1

                    features_processed += 1

                    # Write feature
                    if not first_feature:
                        outfile.write(',\n')
                    first_feature = False
                    outfile.write(json.dumps(feature))

                    if features_processed % 100000 == 0:
                        print(f"  Processed {features_processed:,} features...")

                except json.JSONDecodeError as e:
                    print(f"  Warning: Could not parse feature, skipping: {str(e)[:50]}")
                    continue

        # Close the file
        outfile.write('\n]\n}\n')

    print(f"\nComplete! Processed {features_processed:,} features ({features_with_geom:,} with geometry)")
    return features_processed

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: fix_harris_coords.py input.geojson output.geojson")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    process_file(input_file, output_file)
