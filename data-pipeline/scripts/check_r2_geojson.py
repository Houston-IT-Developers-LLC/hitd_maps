#!/usr/bin/env python3
"""
Check all GeoJSON files on R2 for coordinate system issues.
Downloads first 5KB of each file and analyzes coordinates.
"""

import subprocess
import json
import re
import sys
import os

R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

def detect_crs(x, y):
    """Detect CRS from coordinate values"""
    # WGS84 (EPSG:4326)
    if -180 <= x <= 180 and -90 <= y <= 90:
        return "WGS84 (EPSG:4326)", True

    # Web Mercator (EPSG:3857)
    if -20037508 <= x <= 20037508 and -20037508 <= y <= 20037508:
        return "Web Mercator (EPSG:3857)", False

    # Texas State Plane South Central (EPSG:2278) - Harris, Travis, Bexar
    if 2000000 < x < 5000000 and 10000000 < y < 20000000:
        return "TX State Plane SC (EPSG:2278)", False

    # Texas State Plane North Central (EPSG:2276) - Dallas, Tarrant
    if 2000000 < x < 4000000 and 6000000 < y < 10000000:
        return "TX State Plane NC (EPSG:2276)", False

    # Michigan Oblique Mercator
    if 10000000 < x < 15000000 and 0 < y < 1500000:
        return "MI Oblique Mercator (EPSG:3078)", False

    # Michigan State Plane
    if 5000000 < x < 10000000 and 0 < y < 3000000:
        return "MI State Plane (EPSG:2253)", False

    # Pennsylvania
    if 1000000 < x < 3500000 and 0 < y < 1000000:
        return "PA State Plane (EPSG:2272)", False

    # New York Long Island
    if 800000 < x < 1500000 and 100000 < y < 500000:
        return "NY State Plane (EPSG:2263)", False

    # Georgia
    if 500000 < x < 1500000 and 0 < y < 2000000:
        return "GA State Plane (EPSG:2240)", False

    # Generic large values - assume needs reprojection
    if abs(x) > 1000 or abs(y) > 1000:
        return f"UNKNOWN (x={x:.0f}, y={y:.0f})", False

    return "UNKNOWN", False

def check_file(filename):
    """Check a single GeoJSON file"""
    # Download first 10KB
    cmd = f'aws s3 cp s3://{R2_BUCKET}/parcels/{filename} - --endpoint-url {R2_ENDPOINT} 2>/dev/null | head -c 10000'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if not result.stdout:
        return filename, "ERROR: Could not download", False

    # Find first coordinate pair
    coords = re.search(r'\[\[([0-9.-]+),\s*([0-9.-]+)\]', result.stdout)
    if not coords:
        coords = re.search(r'"coordinates":\s*\[([0-9.-]+),\s*([0-9.-]+)\]', result.stdout)

    if not coords:
        return filename, "ERROR: No coordinates found", False

    x, y = float(coords.group(1)), float(coords.group(2))
    crs, is_wgs84 = detect_crs(x, y)

    return filename, crs, is_wgs84

def main():
    # Get file list
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        with open('/tmp/r2_geojson_files.txt') as f:
            files = [line.strip() for line in f if line.strip()]

    print(f"Checking {len(files)} GeoJSON files...")
    print("=" * 80)

    issues = []
    ok_count = 0

    for i, filename in enumerate(files):
        fname, crs, is_ok = check_file(filename)
        status = "OK" if is_ok else "NEEDS FIX"
        print(f"[{i+1:3d}/{len(files)}] {fname:50s} {crs:30s} [{status}]")

        if not is_ok:
            issues.append((fname, crs))
        else:
            ok_count += 1

    print("=" * 80)
    print(f"\nSummary: {ok_count} OK, {len(issues)} need fixing")

    if issues:
        print("\nFiles needing reprojection:")
        for fname, crs in issues:
            print(f"  - {fname}: {crs}")

    # Save issues to file
    with open('/tmp/r2_issues.txt', 'w') as f:
        for fname, crs in issues:
            f.write(f"{fname}\t{crs}\n")

if __name__ == "__main__":
    main()
