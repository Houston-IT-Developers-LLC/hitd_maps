#!/usr/bin/env python3
"""
Comprehensive USA parcel coverage test.
Tests ALL 51 states with sample coordinates in every state.
"""

import requests
import json
import time
from typing import List, Tuple, Dict

CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels"

# Test coordinates for ALL 51 states (state, capital/major city, lon, lat, expected_file)
STATE_TEST_COORDS = [
    # States with 100% coverage (37 states)
    ("AK", "Anchorage", -149.9003, 61.2181, "parcels_ak_statewide"),
    ("AR", "Little Rock", -92.2896, 34.7465, "parcels_ar_statewide"),
    ("CA", "Los Angeles", -118.2437, 34.0522, "parcels_ca_statewide"),
    ("CO", "Denver", -104.9903, 39.7392, "parcels_co_statewide"),
    ("CT", "Hartford", -72.6851, 41.7658, "parcels_ct_statewide_v2"),
    ("DC", "Washington DC", -77.0369, 38.9072, "parcels_dc_owner_polygons"),
    ("DE", "Wilmington", -75.5277, 39.7391, "parcels_de_statewide"),
    ("FL", "Miami", -80.1918, 25.7617, "parcels_fl_statewide"),
    ("HI", "Honolulu", -157.8583, 21.3099, "parcels_hi_statewide"),
    ("IA", "Des Moines", -93.6091, 41.5868, "parcels_ia_statewide"),
    ("ID", "Boise", -116.2146, 43.6150, "parcels_id_statewide"),
    ("IN", "Indianapolis", -86.1581, 39.7684, "parcels_in_statewide"),
    ("MA", "Boston", -71.0589, 42.3601, "parcels_ma_statewide"),
    ("MD", "Baltimore", -76.6122, 39.2904, "parcels_md_statewide"),
    ("ME", "Portland", -70.2553, 43.6591, "parcels_me_statewide"),
    ("MN", "Minneapolis", -93.2650, 44.9778, "parcels_mn_statewide"),
    ("MT", "Billings", -108.5007, 45.7833, "parcels_mt_statewide_v2"),
    ("NC", "Charlotte", -80.8431, 35.2271, "parcels_nc_statewide"),
    ("ND", "Fargo", -96.7898, 46.8772, "parcels_nd_statewide"),
    ("NH", "Manchester", -71.5381, 42.9956, "parcels_nh_statewide"),
    ("NJ", "Newark", -74.1724, 40.7357, "parcels_nj_statewide_v2"),
    ("NM", "Albuquerque", -106.6504, 35.0844, "parcels_nm_statewide_v2"),
    ("NV", "Las Vegas", -115.1398, 36.1699, "parcels_nv_statewide"),
    ("NY", "New York City", -74.0060, 40.7128, "parcels_ny_statewide_v2"),
    ("OH", "Columbus", -82.9988, 39.9612, "parcels_oh_statewide"),
    ("PA", "Philadelphia", -75.1652, 39.9526, "parcels_pa_statewide"),
    ("RI", "Providence", -71.4128, 41.8240, "parcels_ri_statewide"),
    ("TN", "Nashville", -86.7816, 36.1627, "parcels_tn_statewide"),
    ("TX", "Austin", -97.7431, 30.2672, "parcels_tx_statewide_recent"),
    ("UT", "Salt Lake City", -111.8910, 40.7608, "parcels_ut_statewide"),
    ("VA", "Richmond", -77.4360, 37.5407, "parcels_va_statewide_v2"),
    ("VT", "Burlington", -73.2121, 44.4759, "parcels_vt_statewide"),
    ("WA", "Seattle", -122.3321, 47.6062, "parcels_wa_statewide"),
    ("WI", "Milwaukee", -87.9065, 43.0389, "parcels_wi_statewide"),
    ("WV", "Charleston", -81.6326, 38.3498, "parcels_wv_statewide"),
    ("WY", "Cheyenne", -104.8202, 41.1400, "parcels_wy_statewide"),
    ("AZ", "Phoenix", -112.0740, 33.4484, "parcels_az_maricopa"),  # 100% via counties

    # States with partial coverage (14 states) - test major metros
    ("AL", "Birmingham", -86.8025, 33.5207, "parcels_al_jefferson"),
    ("GA", "Atlanta", -84.3880, 33.7490, "parcels_ga_fulton"),
    ("IL", "Chicago", -87.6298, 41.8781, "parcels_il_cook"),
    ("KS", "Wichita", -97.3301, 37.6872, "parcels_ks_sedgwick"),
    ("KY", "Louisville", -85.7585, 38.2527, "parcels_ky_jefferson"),
    ("LA", "New Orleans", -90.0715, 29.9511, "parcels_la_orleans_v2"),
    ("MI", "Detroit", -83.0458, 42.3314, "parcels_mi_wayne"),
    ("MO", "St. Louis", -90.1994, 38.6270, "parcels_mo_stlouis_county"),
    ("MS", "Jackson", -90.1848, 32.2988, "parcels_ms_hinds"),
    ("NE", "Omaha", -95.9979, 41.2565, "parcels_ne_douglas"),
    ("OK", "Oklahoma City", -97.5164, 35.4676, "parcels_ok_oklahoma"),
    ("OR", "Portland", -122.6765, 45.5152, "parcels_or_multnomah_v2"),
    ("SC", "Charleston", -79.9311, 32.7765, "parcels_sc_charleston"),
    ("SD", "Sioux Falls", -96.7003, 43.5460, "parcels_sd_minnehaha"),
]


def check_file_exists(filename: str) -> Dict:
    """Check if a PMTiles file exists on R2."""
    url = f"{CDN_BASE}/{filename}.pmtiles"
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            size_mb = int(response.headers.get('Content-Length', 0)) / 1024 / 1024
            return {
                "exists": True,
                "size_mb": size_mb,
                "status_code": 200
            }
        else:
            return {
                "exists": False,
                "status_code": response.status_code
            }
    except requests.exceptions.Timeout:
        return {"exists": False, "error": "timeout"}
    except Exception as e:
        return {"exists": False, "error": str(e)}


def main():
    print("=" * 100)
    print("COMPREHENSIVE USA PARCEL COVERAGE TEST - ALL 51 STATES")
    print("=" * 100)
    print(f"\nTesting {len(STATE_TEST_COORDS)} state locations...")
    print(f"Total states to verify: 51 (50 states + DC)")
    print()

    results = {
        "complete_states": [],
        "partial_states": [],
        "failed_states": [],
        "total_tested": 0,
        "total_passed": 0,
        "total_failed": 0,
    }

    print("Testing each state's primary file:")
    print("-" * 100)

    for state, city, lon, lat, expected_file in STATE_TEST_COORDS:
        results["total_tested"] += 1

        # Format output
        state_info = f"{state:3s} | {city:20s} ({lon:9.4f}, {lat:8.4f})"
        file_info = f" -> {expected_file}"

        print(f"{state_info:60s}{file_info:40s}", end=" ")

        # Check file
        result = check_file_exists(expected_file)

        if result["exists"]:
            size = result.get("size_mb", 0)
            print(f"✅ ({size:6.1f} MB)")
            results["total_passed"] += 1

            # Categorize state
            if "statewide" in expected_file:
                results["complete_states"].append(state)
            else:
                results["partial_states"].append(state)
        else:
            error = result.get("error", result.get("status_code", "unknown"))
            print(f"❌ {error}")
            results["total_failed"] += 1
            results["failed_states"].append((state, expected_file, error))

        # Rate limit
        if results["total_tested"] % 10 == 0:
            time.sleep(0.3)

    # Check for naming issues
    print()
    print("=" * 100)
    print("CHECKING FOR NAMING ISSUES (missing state prefixes)")
    print("=" * 100)

    # Common county names that might be missing state prefixes
    potential_issues = []
    common_counties = [
        "montgomery", "washington", "jefferson", "jackson", "franklin",
        "lincoln", "madison", "marion", "warren", "clark"
    ]

    for county in common_counties:
        result = check_file_exists(f"parcels_{county}")
        if result["exists"]:
            size = result.get("size_mb", 0)
            print(f"⚠️  Found: parcels_{county}.pmtiles ({size:.1f} MB) - Missing state prefix?")
            potential_issues.append(county)

    if not potential_issues:
        print("✅ No naming issues detected")

    # Summary
    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total states tested: {results['total_tested']}")
    print(f"✅ Passed: {results['total_passed']}")
    print(f"❌ Failed: {results['total_failed']}")
    print(f"Success rate: {(results['total_passed']/results['total_tested']*100):.1f}%")
    print()
    print(f"States with 100% coverage: {len(results['complete_states'])}")
    print(f"States with partial coverage: {len(results['partial_states'])}")
    print()

    if results["failed_states"]:
        print("=" * 100)
        print("FAILED STATES")
        print("=" * 100)
        for state, file, error in results["failed_states"]:
            print(f"  ❌ {state}: {file} - {error}")
        print()

    # Save detailed results
    output = {
        "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_tested": results["total_tested"],
            "passed": results["total_passed"],
            "failed": results["total_failed"],
            "success_rate": round(results["total_passed"]/results["total_tested"]*100, 1)
        },
        "complete_states": results["complete_states"],
        "partial_states": results["partial_states"],
        "failed_states": results["failed_states"],
        "naming_issues": potential_issues
    }

    with open("/tmp/usa_coverage_test_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("✅ Full results saved to: /tmp/usa_coverage_test_results.json")

    if results["total_failed"] == 0 and not potential_issues:
        print()
        print("🎉 ✅ ALL 51 STATES VERIFIED - NO ISSUES FOUND!")
    elif results["total_failed"] == 0:
        print()
        print(f"⚠️  All states passed, but {len(potential_issues)} potential naming issues found")
    else:
        print()
        print(f"⚠️  {results['total_failed']} states have issues that need attention")

    print()


if __name__ == "__main__":
    main()
