#!/usr/bin/env python3
"""
Find parcel data sources for missing states from official open data portals.
This script lists known ArcGIS REST services and download links for each state.
"""

# Known parcel data sources for missing states
STATE_SOURCES = {
    'FL': {
        'name': 'Florida',
        'sources': [
            {
                'name': 'Florida GIO Parcels',
                'url': 'https://services1.arcgis.com/O1JpcwDW8sjYuddV/arcgis/rest/services/FDOR_Parcels/FeatureServer/0',
                'type': 'arcgis',
                'notes': 'Statewide parcels from Florida Geographic Information Office'
            },
            {
                'name': 'Florida DOT Open Data',
                'url': 'https://gis.fdot.gov/arcgis/rest/services',
                'type': 'portal',
                'notes': 'Check for parcel layers'
            }
        ]
    },
    'AL': {
        'name': 'Alabama',
        'sources': [
            {
                'name': 'Alabama GIS Portal',
                'url': 'https://open.alabama.gov/',
                'type': 'portal',
                'notes': 'Check for parcel/property data'
            }
        ]
    },
    'AR': {
        'name': 'Arkansas',
        'sources': [
            {
                'name': 'Arkansas GIS Office',
                'url': 'https://gis.arkansas.gov/',
                'type': 'portal',
                'notes': 'State GIS portal'
            }
        ]
    },
    'SC': {
        'name': 'South Carolina',
        'sources': [
            {
                'name': 'SC Revenue and Fiscal Affairs',
                'url': 'https://rfa.sc.gov/',
                'type': 'portal',
                'notes': 'May have parcel data'
            }
        ]
    },
    'MS': {
        'name': 'Mississippi', 
        'sources': [
            {
                'name': 'Mississippi Geospatial Clearinghouse',
                'url': 'https://www.maris.state.ms.us/',
                'type': 'portal',
                'notes': 'State geospatial data'
            }
        ]
    },
    'OK': {
        'name': 'Oklahoma',
        'sources': [
            {
                'name': 'Oklahoma GIS Council',
                'url': 'https://okmaps.org/',
                'type': 'portal',
                'notes': 'State GIS data'
            }
        ]
    },
    'MT': {
        'name': 'Montana',
        'sources': [
            {
                'name': 'Montana State Library',
                'url': 'https://msl.mt.gov/geoinfo/',
                'type': 'portal',
                'notes': 'Geographic Information'
            }
        ]
    },
    'WY': {
        'name': 'Wyoming',
        'sources': [
            {
                'name': 'Wyoming SGID',
                'url': 'https://geospatialhub.org/',
                'type': 'portal',
                'notes': 'State Geographic Info Database'
            }
        ]
    },
    'SD': {
        'name': 'South Dakota',
        'sources': [
            {
                'name': 'SD GIS',
                'url': 'https://opendata2017-09-18t192802468z-sdgs.hub.arcgis.com/',
                'type': 'arcgis_hub',
                'notes': 'ArcGIS Hub'
            }
        ]
    },
    'ND': {
        'name': 'North Dakota',
        'sources': [
            {
                'name': 'ND GIS Hub',
                'url': 'https://ndgishub.nd.gov/',
                'type': 'portal',
                'notes': 'State GIS data portal'
            }
        ]
    },
    'NV': {
        'name': 'Nevada',
        'sources': [
            {
                'name': 'Nevada GIS',
                'url': 'https://clearinghouse.nv.gov/',
                'type': 'portal', 
                'notes': 'State clearinghouse'
            },
            {
                'name': 'Clark County (Las Vegas)',
                'url': 'https://gisgate.co.clark.nv.us/gismo/datalist.html',
                'type': 'download',
                'notes': 'Clark County GIS data'
            }
        ]
    },
    'ID': {
        'name': 'Idaho',
        'sources': [
            {
                'name': 'Idaho Geospatial Office',
                'url': 'https://gis.idaho.gov/',
                'type': 'portal',
                'notes': 'State GIS portal'
            }
        ]
    },
    'AK': {
        'name': 'Alaska',
        'sources': [
            {
                'name': 'Alaska SDMI',
                'url': 'https://gis.data.alaska.gov/',
                'type': 'arcgis_hub',
                'notes': 'Statewide Digital Mapping Initiative'
            }
        ]
    },
    'VT': {
        'name': 'Vermont',
        'sources': [
            {
                'name': 'Vermont Open Geodata Portal',
                'url': 'https://geodata.vermont.gov/',
                'type': 'arcgis_hub',
                'notes': 'State open data portal'
            }
        ]
    },
    'RI': {
        'name': 'Rhode Island',
        'sources': [
            {
                'name': 'RIGIS',
                'url': 'https://www.rigis.org/',
                'type': 'portal',
                'notes': 'Rhode Island Geographic Information System'
            },
            {
                'name': 'RIGIS Data',
                'url': 'https://www.arcgis.com/home/group.html?id=ae7c0e00f6b84cb4a2d7c45f60e8e8b4',
                'type': 'arcgis_hub',
                'notes': 'RIGIS ArcGIS group'
            }
        ]
    }
}

def main():
    missing = ['AK', 'AL', 'AR', 'FL', 'ID', 'MS', 'MT', 'NV', 'OK', 'RI', 'SC', 'SD', 'VT', 'WY']
    
    print("=" * 70)
    print("PARCEL DATA SOURCES FOR MISSING STATES")
    print("=" * 70)
    print()
    
    for state in missing:
        info = STATE_SOURCES.get(state, {})
        name = info.get('name', state)
        sources = info.get('sources', [])
        
        print(f"\n{state} - {name}")
        print("-" * 40)
        
        if sources:
            for src in sources:
                print(f"  Source: {src['name']}")
                print(f"  URL: {src['url']}")
                print(f"  Type: {src['type']}")
                print(f"  Notes: {src['notes']}")
                print()
        else:
            print("  No known sources - needs research")
            print()
    
    print("\n" + "=" * 70)
    print("RECOMMENDED APPROACH:")
    print("=" * 70)
    print("""
1. Start with states that have ArcGIS REST services (FL, etc.)
2. Use export_county_parcels.py pattern to download GeoJSON
3. Apply appropriate PROJ string if needed
4. Convert to PMTiles with tippecanoe
5. Upload to R2

Priority order (by population/importance):
1. FL (Florida) - 22M population
2. SC (South Carolina) - 5M population  
3. AL (Alabama) - 5M population
4. OK (Oklahoma) - 4M population
5. NV (Nevada) - 3M population (Clark County/Las Vegas)
6. AR (Arkansas) - 3M population
7. MS (Mississippi) - 3M population
8. RI (Rhode Island) - 1M population (small, easy to complete)
9. MT (Montana) - 1M population
10. ID (Idaho) - 2M population
11. SD (South Dakota) - 900K population
12. VT (Vermont) - 650K population
13. WY (Wyoming) - 580K population
14. AK (Alaska) - 730K population (sparse, complex)
""")

if __name__ == '__main__':
    main()
