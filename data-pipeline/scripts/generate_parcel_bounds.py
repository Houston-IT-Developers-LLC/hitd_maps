#!/usr/bin/env python3
"""
Generate spatial index with bounding boxes for all parcel PMTiles files.
This enables efficient viewport-based loading on the frontend.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Read valid parcels list
VALID_PARCELS_FILE = Path(__file__).parent.parent / "data" / "valid_parcels.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "parcel_bounds.json"
DOWNLOADS_DIR = Path(__file__).parent.parent / "data" / "downloads"


def get_pmtiles_bounds(pmtiles_path: str) -> Tuple[float, float, float, float] | None:
    """Extract bounding box from PMTiles metadata."""
    try:
        result = subprocess.run(
            ["pmtiles", "show", pmtiles_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return None

        # Parse bounds from output
        # Format: "bounds: (long: -87.621842, lat: 25.802557) (long: -80.074339, lat: 30.998610)"
        for line in result.stdout.split('\n'):
            if line.startswith('bounds:'):
                # Extract coordinates
                parts = line.split('(long:')[1:]
                if len(parts) >= 2:
                    # First point (min)
                    min_parts = parts[0].split(',')
                    min_lon = float(min_parts[0].strip())
                    min_lat = float(min_parts[1].split('lat:')[1].strip().rstrip(')'))

                    # Second point (max)
                    max_parts = parts[1].split(',')
                    max_lon = float(max_parts[0].strip())
                    max_lat = float(max_parts[1].split('lat:')[1].strip().rstrip(')'))

                    return (min_lon, min_lat, max_lon, max_lat)

        return None
    except Exception as e:
        print(f"Error getting bounds for {pmtiles_path}: {e}", file=sys.stderr)
        return None


def main():
    # Load valid parcels list
    with open(VALID_PARCELS_FILE) as f:
        parcels = json.load(f)

    print(f"Processing {len(parcels)} parcel files...")

    bounds_index: Dict[str, Dict] = {}
    processed = 0
    failed = 0

    for parcel_name in parcels:
        # Try to find the PMTiles file
        pmtiles_path = DOWNLOADS_DIR / f"{parcel_name}.pmtiles"

        if not pmtiles_path.exists():
            print(f"⚠ File not found: {parcel_name}.pmtiles", file=sys.stderr)
            failed += 1
            continue

        bounds = get_pmtiles_bounds(str(pmtiles_path))

        if bounds:
            min_lon, min_lat, max_lon, max_lat = bounds

            # Determine type (statewide vs county)
            is_statewide = 'statewide' in parcel_name or parcel_name.endswith('_wgs84')

            # Extract state code
            state = parcel_name.split('_')[1].upper() if '_' in parcel_name else 'UNKNOWN'

            bounds_index[parcel_name] = {
                "bounds": [min_lon, min_lat, max_lon, max_lat],
                "state": state,
                "type": "statewide" if is_statewide else "county",
                "center": [
                    (min_lon + max_lon) / 2,
                    (min_lat + max_lat) / 2
                ],
                "area": (max_lon - min_lon) * (max_lat - min_lat)
            }

            processed += 1
            if processed % 10 == 0:
                print(f"Processed {processed}/{len(parcels)}...")
        else:
            print(f"✗ Failed to get bounds: {parcel_name}", file=sys.stderr)
            failed += 1

    # Write output
    output_data = {
        "generated_at": "2026-01-27",
        "total_files": len(parcels),
        "processed": processed,
        "failed": failed,
        "parcels": bounds_index
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✓ Generated spatial index: {OUTPUT_FILE}")
    print(f"  Processed: {processed}")
    print(f"  Failed: {failed}")
    print(f"\nStates covered:")
    states = {}
    for parcel_data in bounds_index.values():
        state = parcel_data['state']
        states[state] = states.get(state, 0) + 1

    for state, count in sorted(states.items()):
        print(f"  {state}: {count} files")


if __name__ == '__main__':
    main()
