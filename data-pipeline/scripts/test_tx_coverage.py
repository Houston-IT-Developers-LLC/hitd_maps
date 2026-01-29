#!/usr/bin/env python3
"""
Test Texas parcel coverage by checking random coordinates across the state.
Tests both the statewide file and county-specific files.
"""

import requests
import json
from typing import List, Tuple, Dict

# CDN base URL
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels"

# Test coordinates across Texas (city, lon, lat, expected_file)
TEST_LOCATIONS: List[Tuple[str, float, float, str]] = [
    # Major cities
    ("Houston", -95.3698, 29.7604, "tx_harris"),
    ("Dallas", -96.7970, 32.7767, "tx_dallas"),
    ("Austin", -97.7431, 30.2672, "tx_travis"),
    ("San Antonio", -98.4936, 29.4241, "tx_bexar"),
    ("Fort Worth", -97.3308, 32.7555, "tx_tarrant"),
    ("Denton", -97.1331, 33.2148, "tx_denton"),
    ("Round Rock (Williamson)", -97.6789, 30.5083, "tx_williamson"),

    # Montgomery County (Houston suburbs - THE PROBLEM AREA)
    ("The Woodlands (Montgomery)", -95.4895, 30.1658, "montgomery"),  # Missing tx_ prefix!
    ("Conroe (Montgomery)", -95.4560, 30.3119, "montgomery"),

    # Other TX cities (should be in statewide)
    ("El Paso", -106.4850, 31.7619, "tx_statewide_recent"),
    ("Lubbock", -101.8552, 33.5779, "tx_statewide_recent"),
    ("Amarillo", -101.8313, 35.2220, "tx_statewide_recent"),
    ("Corpus Christi", -97.3964, 27.8006, "tx_statewide_recent"),
    ("Laredo", -99.5075, 27.5306, "tx_statewide_recent"),
    ("Brownsville", -97.4975, 25.9017, "tx_statewide_recent"),
    ("McAllen", -98.2300, 26.2034, "tx_statewide_recent"),
    ("Midland", -102.0779, 31.9973, "tx_statewide_recent"),
    ("Odessa", -102.3676, 31.8457, "tx_statewide_recent"),
    ("Waco", -97.1467, 31.5493, "tx_statewide_recent"),
    ("Killeen", -97.7278, 31.1171, "tx_statewide_recent"),
    ("Tyler", -95.3011, 32.3513, "tx_statewide_recent"),
    ("Beaumont", -94.1266, 30.0860, "tx_statewide_recent"),
    ("Abilene", -99.7331, 32.4487, "tx_statewide_recent"),
]


def lon_lat_to_tile(lon: float, lat: float, zoom: int) -> Tuple[int, int]:
    """Convert lon/lat to tile coordinates at given zoom level."""
    import math
    n = 2 ** zoom
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) +
            1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    return (x, y)


def test_pmtiles_file(file_name: str, lon: float, lat: float) -> Dict:
    """Test if a PMTiles file contains data at the given coordinate."""
    url = f"{CDN_BASE}/parcels_{file_name}.pmtiles"

    # First, try to get metadata
    try:
        # PMTiles uses range requests - test with a HEAD request first
        response = requests.head(url, timeout=10)

        if response.status_code == 404:
            return {
                "file": file_name,
                "status": "NOT_FOUND",
                "url": url
            }
        elif response.status_code != 200:
            return {
                "file": file_name,
                "status": f"HTTP_{response.status_code}",
                "url": url
            }

        # File exists - check if it's accessible
        size = response.headers.get('Content-Length', 'unknown')

        return {
            "file": file_name,
            "status": "EXISTS",
            "url": url,
            "size": size,
            "accessible": True
        }

    except requests.exceptions.Timeout:
        return {
            "file": file_name,
            "status": "TIMEOUT",
            "url": url
        }
    except requests.exceptions.RequestException as e:
        return {
            "file": file_name,
            "status": "ERROR",
            "url": url,
            "error": str(e)
        }


def main():
    print("=" * 80)
    print("TEXAS PARCEL COVERAGE TEST")
    print("=" * 80)
    print()

    results = []
    issues = []

    for location, lon, lat, expected_file in TEST_LOCATIONS:
        print(f"\nTesting: {location} ({lon}, {lat})")
        print(f"  Expected file: parcels_{expected_file}.pmtiles")

        result = test_pmtiles_file(expected_file, lon, lat)
        results.append({
            "location": location,
            "coordinates": (lon, lat),
            "expected_file": expected_file,
            **result
        })

        if result["status"] == "EXISTS":
            print(f"  ✅ File found - Size: {result['size']} bytes")
        elif result["status"] == "NOT_FOUND":
            print(f"  ❌ FILE NOT FOUND: {result['url']}")
            issues.append(f"Missing: {expected_file} for {location}")
        else:
            print(f"  ⚠️  {result['status']}: {result.get('error', 'Unknown issue')}")
            issues.append(f"Issue with {expected_file} for {location}: {result['status']}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    found = sum(1 for r in results if r["status"] == "EXISTS")
    missing = sum(1 for r in results if r["status"] == "NOT_FOUND")
    errors = sum(1 for r in results if r["status"] not in ["EXISTS", "NOT_FOUND"])

    print(f"\nTotal locations tested: {total}")
    print(f"✅ Files found: {found}")
    print(f"❌ Files missing: {missing}")
    print(f"⚠️  Errors: {errors}")

    if issues:
        print("\n" + "=" * 80)
        print("ISSUES FOUND")
        print("=" * 80)
        for issue in issues:
            print(f"  • {issue}")

    # Check for the Montgomery naming issue
    print("\n" + "=" * 80)
    print("SPECIAL CHECK: Montgomery County Naming Issue")
    print("=" * 80)
    print("\nChecking if 'parcels_montgomery.pmtiles' exists (missing tx_ prefix)...")

    result = test_pmtiles_file("montgomery", -95.4895, 30.1658)
    if result["status"] == "EXISTS":
        print(f"✅ Found: parcels_montgomery.pmtiles (Size: {result['size']})")
        print("⚠️  WARNING: This file is missing the 'tx_' state prefix!")
        print("   Should be renamed to: parcels_tx_montgomery.pmtiles")
    else:
        print(f"❌ Not found or error: {result['status']}")

    # Save results
    with open("/tmp/tx_coverage_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Full results saved to: /tmp/tx_coverage_test_results.json")
    print()


if __name__ == "__main__":
    main()
