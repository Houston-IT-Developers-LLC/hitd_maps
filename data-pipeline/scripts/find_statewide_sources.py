#!/usr/bin/env python3
"""
Hunt for statewide parcel datasets for the 14 partial states.
Searches known state GIS portals and data aggregators.
"""

import requests
import json
from typing import List, Dict, Tuple

# 14 partial states needing statewide datasets
PARTIAL_STATES = [
    ("IL", "Illinois", "https://clearinghouse.isgs.illinois.edu/"),
    ("MI", "Michigan", "https://gis-michigan.opendata.arcgis.com/"),
    ("GA", "Georgia", "https://data.georgiagio.org/"),
    ("MO", "Missouri", "https://msdis.missouri.edu/"),
    ("LA", "Louisiana", "https://atlas.ga.lsu.edu/"),
    ("AL", "Alabama", "https://open.alabama.gov/"),
    ("KY", "Kentucky", "https://kyraster.ky.gov/"),
    ("MS", "Mississippi", "https://www.maris.state.ms.us/"),
    ("SC", "South Carolina", "https://www.scdnr.gov/gis/"),
    ("SD", "South Dakota", "https://sdbit.sd.gov/"),
    ("OK", "Oklahoma", "https://data.ok.gov/"),
    ("OR", "Oregon", "https://www.oregon.gov/geo/"),
    ("NE", "Nebraska", "https://nednr.nebraska.gov/"),
    ("KS", "Kansas", "https://www.kansasgis.org/"),
]

# Known statewide parcel aggregators
AGGREGATORS = [
    {
        "name": "ParcelQuest",
        "url": "https://www.parcelquest.com/",
        "note": "Commercial - covers most states"
    },
    {
        "name": "CoreLogic",
        "url": "https://www.corelogic.com/",
        "note": "Commercial - comprehensive coverage"
    },
    {
        "name": "Regrid (formerly Loveland)",
        "url": "https://regrid.com/",
        "note": "Has free nationwide parcel API"
    },
]

# State-specific known sources
STATE_SOURCES = {
    "IL": [
        {
            "name": "Illinois Geospatial Data Clearinghouse",
            "url": "https://clearinghouse.isgs.illinois.edu/",
            "search_url": "https://clearinghouse.isgs.illinois.edu/search?q=parcels",
            "type": "state_portal",
            "likelihood": "HIGH",
            "notes": "Illinois State Geological Survey - check for statewide aggregation"
        },
        {
            "name": "Illinois GIS",
            "url": "https://gis.illinois.gov/",
            "type": "state_gis",
            "likelihood": "HIGH"
        }
    ],
    "MI": [
        {
            "name": "Michigan Geographic Framework",
            "url": "https://gis-michigan.opendata.arcgis.com/",
            "search_url": "https://gis-michigan.opendata.arcgis.com/search?q=parcels",
            "type": "arcgis_hub",
            "likelihood": "HIGH",
            "notes": "Michigan DTMB - likely has statewide aggregation"
        },
        {
            "name": "MGDL - Michigan Geographic Data Library",
            "url": "https://www.mcgi.state.mi.us/mgdl/",
            "type": "state_library",
            "likelihood": "VERY_HIGH"
        }
    ],
    "GA": [
        {
            "name": "Georgia GIO",
            "url": "https://data.georgiagio.org/",
            "search_url": "https://data.georgiagio.org/search?q=parcels",
            "type": "state_portal",
            "likelihood": "HIGH",
            "notes": "Georgia Geographic Information Office"
        },
        {
            "name": "Georgia Spatial Data Infrastructure",
            "url": "https://gis.georgia.gov/",
            "type": "state_gis",
            "likelihood": "MEDIUM"
        }
    ],
    "MO": [
        {
            "name": "MSDIS - Missouri Spatial Data Information Service",
            "url": "https://msdis.missouri.edu/",
            "search_url": "https://msdis.missouri.edu/search?q=parcels",
            "type": "state_library",
            "likelihood": "VERY_HIGH",
            "notes": "University of Missouri - primary state GIS aggregator"
        }
    ],
    "LA": [
        {
            "name": "Louisiana Atlas",
            "url": "https://atlas.ga.lsu.edu/",
            "type": "state_portal",
            "likelihood": "HIGH",
            "notes": "LSU - check for parish aggregations"
        },
        {
            "name": "Louisiana GIS",
            "url": "https://lagis.lsu.edu/",
            "type": "state_gis",
            "likelihood": "MEDIUM"
        }
    ],
    "AL": [
        {
            "name": "Alabama Open Data Portal",
            "url": "https://open.alabama.gov/",
            "search_url": "https://open.alabama.gov/search?q=parcels",
            "type": "state_portal",
            "likelihood": "MEDIUM"
        }
    ],
    "KY": [
        {
            "name": "Kentucky Geography Network",
            "url": "https://kyraster.ky.gov/",
            "type": "state_gis",
            "likelihood": "MEDIUM"
        }
    ],
    "MS": [
        {
            "name": "MARIS - Mississippi Automated Resource Information System",
            "url": "https://www.maris.state.ms.us/",
            "type": "state_portal",
            "likelihood": "HIGH"
        }
    ],
    "SC": [
        {
            "name": "SC Department of Revenue GIS",
            "url": "https://www.scdor.gov/",
            "type": "tax_assessor",
            "likelihood": "MEDIUM",
            "notes": "Revenue dept may have statewide tax parcels"
        }
    ],
    "SD": [
        {
            "name": "South Dakota GIS",
            "url": "https://sdbit.sd.gov/",
            "type": "state_gis",
            "likelihood": "MEDIUM"
        }
    ],
    "OK": [
        {
            "name": "Oklahoma Data Portal",
            "url": "https://data.ok.gov/",
            "search_url": "https://data.ok.gov/search?q=parcels",
            "type": "state_portal",
            "likelihood": "MEDIUM"
        }
    ],
    "OR": [
        {
            "name": "Oregon Spatial Data Library",
            "url": "https://spatialdata.oregonexplorer.info/",
            "type": "state_library",
            "likelihood": "HIGH"
        }
    ],
    "NE": [
        {
            "name": "Nebraska GIS",
            "url": "https://nednr.nebraska.gov/",
            "type": "state_gis",
            "likelihood": "LOW"
        }
    ],
    "KS": [
        {
            "name": "Kansas Data Access & Support Center",
            "url": "https://www.kansasgis.org/",
            "type": "state_portal",
            "likelihood": "LOW"
        }
    ],
}


def main():
    print("=" * 100)
    print("HUNTING FOR STATEWIDE PARCEL DATASETS - 14 PARTIAL STATES")
    print("=" * 100)
    print()

    results = {
        "high_priority": [],
        "medium_priority": [],
        "low_priority": [],
        "manual_search_needed": []
    }

    for state, name, portal in PARTIAL_STATES:
        print(f"\n{'='*100}")
        print(f"{state} - {name}")
        print(f"{'='*100}")

        if state in STATE_SOURCES:
            sources = STATE_SOURCES[state]
            print(f"\nFound {len(sources)} known source(s):\n")

            for i, source in enumerate(sources, 1):
                print(f"{i}. {source['name']}")
                print(f"   URL: {source['url']}")
                print(f"   Type: {source['type']}")
                print(f"   Likelihood: {source['likelihood']}")
                if 'search_url' in source:
                    print(f"   Search: {source['search_url']}")
                if 'notes' in source:
                    print(f"   Notes: {source['notes']}")
                print()

                # Categorize by likelihood
                if source['likelihood'] == 'VERY_HIGH':
                    results['high_priority'].append({
                        'state': state,
                        'name': name,
                        **source
                    })
                elif source['likelihood'] == 'HIGH':
                    results['high_priority'].append({
                        'state': state,
                        'name': name,
                        **source
                    })
                elif source['likelihood'] == 'MEDIUM':
                    results['medium_priority'].append({
                        'state': state,
                        'name': name,
                        **source
                    })
                else:
                    results['low_priority'].append({
                        'state': state,
                        'name': name,
                        **source
                    })
        else:
            print(f"\n⚠️  No known sources cataloged yet - needs manual research")
            results['manual_search_needed'].append({
                'state': state,
                'name': name,
                'portal': portal
            })

    # Print summary
    print("\n" + "=" * 100)
    print("SUMMARY - PRIORITY SEARCH LIST")
    print("=" * 100)

    print("\n🔥 HIGH PRIORITY (Very High/High Likelihood):")
    print("-" * 100)
    for i, source in enumerate(results['high_priority'], 1):
        print(f"{i:2d}. {source['state']} - {source['name']}")
        print(f"    {source['url']}")
        if 'search_url' in source:
            print(f"    Search: {source['search_url']}")
        print()

    print("\n📋 MEDIUM PRIORITY:")
    print("-" * 100)
    for i, source in enumerate(results['medium_priority'], 1):
        print(f"{i:2d}. {source['state']} - {source['name']}")
        print(f"    {source['url']}")
        print()

    print("\n🔍 MANUAL RESEARCH NEEDED:")
    print("-" * 100)
    for i, source in enumerate(results['manual_search_needed'], 1):
        print(f"{i:2d}. {source['state']} - {source['name']}")
        print(f"    Start at: {source['portal']}")
        print()

    # Alternative approaches
    print("\n" + "=" * 100)
    print("ALTERNATIVE DATA SOURCES")
    print("=" * 100)
    print("\n1. Regrid (formerly Loveland) - FREE API")
    print("   URL: https://regrid.com/")
    print("   Coverage: Nationwide including all 14 partial states")
    print("   API: Free tier available")
    print("   Quality: High - updated regularly")
    print()
    print("2. OpenAddresses - FREE")
    print("   URL: https://openaddresses.io/")
    print("   Coverage: Some parcel data mixed with addresses")
    print()
    print("3. County-by-County Scraping")
    print("   Use existing agent/source_finder.py for each state")
    print("   Download top 20 counties by population in each state")
    print()

    # Save results
    with open("/tmp/statewide_source_hunt.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n✅ Full results saved to: /tmp/statewide_source_hunt.json")

    print("\n" + "=" * 100)
    print("RECOMMENDED NEXT STEPS")
    print("=" * 100)
    print()
    print("1. Start with HIGH PRIORITY sources (5-10 states)")
    print("   - Michigan MGDL (VERY HIGH)")
    print("   - Missouri MSDIS (VERY HIGH)")
    print("   - Illinois Clearinghouse (HIGH)")
    print("   - Georgia GIO (HIGH)")
    print("   - Louisiana Atlas (HIGH)")
    print()
    print("2. Check Regrid API for all 14 states")
    print("   - Free tier may have download limits")
    print("   - Worth exploring for quick wins")
    print()
    print("3. Use automated county scraper for remaining states")
    print("   - Focus on top 20 counties by population")
    print("   - Can get to 50-70% coverage quickly")
    print()


if __name__ == "__main__":
    main()
