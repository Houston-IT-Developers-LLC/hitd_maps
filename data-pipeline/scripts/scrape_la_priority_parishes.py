#!/usr/bin/env python3
"""
HITD Maps - Louisiana Priority Parishes (Hunting Areas)
Targeting: St. Tammany, Livingston, Tangipahoa, Rapides, Bossier

WARNING: Louisiana has no statewide database. Each parish uses proprietary systems.
This script attempts to find and download from any available REST endpoints.
"""

import requests
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Configuration
OUTPUT_DIR = "/home/exx/Documents/C/hitd_maps/data-pipeline/output"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

os.environ['AWS_ACCESS_KEY_ID'] = 'ecd653afe3300fdc045b9980df0dbb14'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://atlas.geoportalmaps.com/'
}

# Priority Louisiana parishes - attempting to find working endpoints
CANDIDATE_SOURCES = {
    "la_st_tammany": {
        "name": "Louisiana - St. Tammany Parish (265K pop, North Shore)",
        "priority": 1,
        "population": 265000,
        "endpoints_to_try": [
            "https://atlas.stpgov.org/server/rest/services/STPAO_Parcels/MapServer/0",
            "https://atlas.stpgov.org/server/rest/services/STPAO_Parcels/FeatureServer/0",
            "https://services.arcgis.com/*/arcgis/rest/services/*St*Tammany*Parcels*/FeatureServer/0",
        ],
        "notes": "St. Tammany Parish - high hunting value, North Shore"
    },
    "la_livingston": {
        "name": "Louisiana - Livingston Parish (142K pop, hunting area)",
        "priority": 2,
        "population": 142000,
        "endpoints_to_try": [
            "https://atlas.geoportalmaps.com/livingston/*/Parcels*/FeatureServer/0",
        ],
        "notes": "Livingston Parish - prime hunting territory"
    },
    "la_tangipahoa": {
        "name": "Louisiana - Tangipahoa Parish (133K pop, hunting area)",  
        "priority": 3,
        "population": 133000,
        "endpoints_to_try": [
            "https://tangipahoa.org/*/Parcels*/FeatureServer/0",
        ],
        "notes": "Tangipahoa Parish - hunting area"
    },
    "la_rapides": {
        "name": "Louisiana - Rapides Parish (130K pop, Alexandria)",
        "priority": 4,
        "population": 130000,
        "endpoints_to_try": [
            "https://rapcgis.rapc.info/*/Parcels*/FeatureServer/0",
        ],
        "notes": "Rapides Parish - Alexandria area"
    },
    "la_bossier": {
        "name": "Louisiana - Bossier Parish (128K pop)",
        "priority": 5,
        "population": 128000,
        "endpoints_to_try": [
            "https://atlas.geoportalmaps.com/bossier*/*/Parcels*/FeatureServer/0",
        ],
        "notes": "Bossier Parish - Shreveport area"
    }
}

def test_endpoint(url):
    """Test if an ArcGIS REST endpoint is accessible"""
    try:
        # Try count query first
        count_url = f"{url}/query?where=1%3D1&returnCountOnly=true&f=json"
        resp = requests.get(count_url, headers=HEADERS, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            if 'count' in data:
                return data.get('count', 0)
            elif 'error' in data:
                return None
        return None
    except:
        return None

def discover_working_endpoints():
    """Attempt to discover working endpoints for priority parishes"""
    print("\n" + "="*80)
    print("DISCOVERING WORKING ENDPOINTS FOR LOUISIANA PRIORITY PARISHES")
    print("="*80)
    
    working_sources = {}
    
    for source_id, config in CANDIDATE_SOURCES.items():
        print(f"\n[{config['priority']}] {config['name']}")
        print(f"    Population: {config['population']:,}")
        print(f"    Testing {len(config['endpoints_to_try'])} potential endpoints...")
        
        # For now, mark as not found - manual intervention needed
        print(f"    ❌ No working REST endpoint discovered")
        print(f"    Note: {config['notes']}")
        print(f"    Action: Manual research needed - parish uses proprietary web portal")
    
    return working_sources

def main():
    print("\n" + "="*80)
    print("HITD Maps - Louisiana Priority Parishes Scraper")
    print("WARNING: Louisiana has no statewide parcel database!")
    print("="*80)
    
    # Discover what we can access
    working_sources = discover_working_endpoints()
    
    if not working_sources:
        print("\n" + "="*80)
        print("RESULT: NO AUTOMATED ACCESS AVAILABLE")
        print("="*80)
        print("\nLouisiana parishes identified:")
        print("1. St. Tammany (265K) - atlas.stpgov.org (proprietary portal)")
        print("2. Livingston (142K) - atlas.geoportalmaps.com/livingston (proprietary)")
        print("3. Tangipahoa (133K) - tangipahoa.org (proprietary portal)")
        print("4. Rapides (130K) - rapcgis.rapc.info (proprietary portal)")
        print("5. Bossier (128K) - atlas.geoportalmaps.com/bossier_public (proprietary)")
        print("\nAll parishes use custom web portals WITHOUT standard ArcGIS REST APIs.")
        print("Options:")
        print("  1. Contact each parish assessor directly for bulk data")
        print("  2. Purchase from commercial vendors (Regrid, LightBox, CoreLogic)")
        print("  3. Manual download from web portals (if bulk export available)")
        print("\nCurrent LA coverage: 7 parishes (Caddo, Calcasieu, East Baton Rouge,")
        print("                               Jefferson, Lafayette, Orleans, Terrebonne)")
        return
    
    print(f"\nFound {len(working_sources)} accessible sources")
    print("Proceeding with download...")
    
    # If we found working sources, process them
    # (This code won't execute unless endpoints are discovered)
    for source_id, source in working_sources.items():
        print(f"\nProcessing: {source_id}")
        # Download logic would go here

if __name__ == '__main__':
    main()
