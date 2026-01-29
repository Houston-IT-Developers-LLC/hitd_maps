#!/usr/bin/env python3
"""
Final verification of Texas parcel coverage after fixes.
"""

import requests

CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels"


def check_file(name: str) -> tuple:
    """Check if a file exists and get its size."""
    url = f"{CDN_BASE}/{name}.pmtiles"
    try:
        r = requests.head(url, timeout=10)
        if r.status_code == 200:
            size_mb = int(r.headers.get('Content-Length', 0)) / 1024 / 1024
            return True, size_mb
        return False, 0
    except:
        return False, 0


print("=" * 80)
print("TEXAS PARCEL FILES - FINAL VERIFICATION")
print("=" * 80)
print()

# All expected Texas files
tx_files = [
    ("parcels_tx_statewide_recent", "Statewide (Primary)", True),
    ("parcels_tx_statewide", "Statewide (Legacy)", True),
    ("parcels_tx_harris_v2", "Harris County (Houston) v2", True),
    ("parcels_tx_harris", "Harris County (Houston)", True),
    ("parcels_tx_dallas", "Dallas County", True),
    ("parcels_tx_tarrant_v2", "Tarrant County (Fort Worth) v2", True),
    ("parcels_tx_travis_v2", "Travis County (Austin) v2", True),
    ("parcels_tx_williamson_v2", "Williamson County v2", True),
    ("parcels_tx_williamson", "Williamson County", True),
    ("parcels_tx_montgomery", "Montgomery County (The Woodlands)", True),
    ("parcels_tx_bexar", "Bexar County (San Antonio)", True),
    ("parcels_tx_denton", "Denton County", True),
    ("parcels_tx_tarrant", "Tarrant County (Legacy)", False),
    ("parcels_tx_travis", "Travis County (Legacy)", False),
]

found = 0
missing = 0
total = len(tx_files)

for filename, description, required in tx_files:
    exists, size_mb = check_file(filename)

    if exists:
        status = "✅"
        found += 1
        print(f"{status} {filename:40} {description:35} ({size_mb:6.1f} MB)")
    else:
        if required:
            status = "❌"
            missing += 1
            print(f"{status} {filename:40} {description:35} MISSING!")
        else:
            status = "⚠️ "
            print(f"{status} {filename:40} {description:35} (optional)")

print()
print("=" * 80)
print(f"REQUIRED FILES: {found}/{total}")
print(f"✅ Found: {found}")
print(f"❌ Missing: {missing}")
print("=" * 80)

# Check for old misnamed file
print()
print("CLEANUP CHECK:")
print("-" * 80)
exists, size_mb = check_file("parcels_montgomery")
if exists:
    print(f"⚠️  Old file still exists: parcels_montgomery.pmtiles ({size_mb:.1f} MB)")
    print("   This file should be deleted (we now have parcels_tx_montgomery.pmtiles)")
else:
    print("✅ Old parcels_montgomery.pmtiles has been cleaned up")

print()
