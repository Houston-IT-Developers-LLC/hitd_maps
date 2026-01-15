#!/usr/bin/env python3
"""
Generic ArcGIS Feature Service Parcel Exporter

Exports parcel data from any ArcGIS REST API with pagination support.
Handles services that require county-by-county queries or full statewide export.
"""

import sys
import json
import urllib.request
import urllib.parse
import time
import os
import argparse
from pathlib import Path

# State configurations
STATE_CONFIGS = {
    "FL": {
        "name": "Florida",
        "service_url": "https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0/query",
        "county_field": "CO_NO",  # County number field
        "out_fields": "OBJECTID,CO_NO,PARCEL_ID,DOR_UC,PA_UC,ASMNT_YR,JV,AV_SD,TV_NSD,NO_RES_UNTS,LND_SQFOOT",
        "batch_size": 2000,
        "use_counties": True,
        "estimated_parcels": 10800000
    },
    "MT": {
        "name": "Montana",
        "service_url": "https://gisservicemt.gov/arcgis/rest/services/MSDI_Framework/Parcels/MapServer/0/query",
        "county_field": "CountyName",
        "out_fields": "OBJECTID,PARCELID,COUNTYCD,CountyName,GISAcres,TaxYear,PropertyID,AssessmentCode",
        "batch_size": 2000,
        "use_counties": True,
        "estimated_parcels": 915000
    },
    "NC": {
        "name": "North Carolina",
        "service_url": "https://services.nconemap.gov/secure/rest/services/NC1Map_Parcels/FeatureServer/0/query",
        "county_field": "cntyname",
        "out_fields": "objectid,parno,ownname,improvval,landval,parval,mailadd,mcity,mstate,mzip,cntyname",
        "batch_size": 5000,
        "use_counties": True,
        "estimated_parcels": 5900000
    },
    "OR": {
        "name": "Oregon",
        "service_url": None,  # Download from GEOHub - no statewide API
        "download_url": "https://geohub.oregon.gov/pages/parcel-viewer",
        "batch_size": 0,
        "use_counties": False,
        "estimated_parcels": 1800000
    },
    "WI": {
        "name": "Wisconsin",
        "service_url": "https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels/FeatureServer/0/query",
        "county_field": None,
        "out_fields": "OBJECTID,STATEID,PARCELID,TAXPARCELID,OWNERNME1,SITEADRESS",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 3560000
    },
    "CO": {
        "name": "Colorado",
        "service_url": "https://gis.colorado.gov/public/rest/services/Address_and_Parcel/Colorado_Public_Parcels/FeatureServer/0/query",
        "county_field": "county",
        "out_fields": "*",
        "batch_size": 2000,
        "use_counties": True,
        "estimated_parcels": 2800000,
        "download_url": "https://geodata.colorado.gov/api/download/v1/items/55234e04218f47c9868900e439fcbd5a/geojson?layers=0"
    },
    "MN": {
        "name": "Minnesota",
        "service_url": None,  # Download only
        "download_url": "https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_state_mngeo/plan_parcels_open/gpkg_plan_parcels_open.zip",
        "batch_size": 0,
        "use_counties": False,
        "estimated_parcels": 2500000
    },
    "AR": {
        "name": "Arkansas",
        "service_url": None,  # FTP download
        "download_url": "ftp://ftp.geostor.arkansas.gov/Public_Statewide/CADAS_PARCEL_POLYGON_CAMP.zip",
        "batch_size": 0,
        "use_counties": False,
        "estimated_parcels": 1500000
    },
    "WY": {
        "name": "Wyoming",
        "service_url": None,  # Check geodata hub
        "download_url": "https://data.geospatialhub.org/",
        "batch_size": 0,
        "use_counties": False,
        "estimated_parcels": 400000
    },
    "IN": {
        "name": "Indiana",
        "service_url": "https://gisdata.in.gov/server/rest/services/Hosted/Parcel_Boundaries_of_Indiana_Current/FeatureServer/0/query",
        "county_field": "county_fips",
        "out_fields": "objectid,state_parcel_id,parcel_id,prop_add,prop_city,county_fips",
        "batch_size": 2000,
        "use_counties": True,
        "estimated_parcels": 3100000
    },
    "UT": {
        "name": "Utah",
        "service_url": "https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahStatewideParcels/FeatureServer/0/query",
        "county_field": None,
        "out_fields": "OBJECTID,PARCEL_ID,PARCEL_ADD,PARCEL_CITY,PARCEL_ZIP,OWN_TYPE",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 1200000
    },
    "NM": {
        "name": "New Mexico",
        "service_url": "https://gis.ose.nm.gov/server_s/rest/services/Parcels/County_Parcels_2025/MapServer/0/query",
        "county_field": None,
        "out_fields": "*",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 1100000
    },
    "VA": {
        "name": "Virginia",
        "service_url": "https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VA_Base_Layers/VA_Parcels/FeatureServer/0/query",
        "county_field": "LOCALITY",
        "out_fields": "OBJECTID,VGIN_QPID,FIPS,LOCALITY,PARCELID,PTM_ID",
        "batch_size": 2000,
        "use_counties": True,
        "estimated_parcels": 4000000
    },
    "WA": {
        "name": "Washington",
        "service_url": "https://services.arcgis.com/jsIt88o09Q0r1j8h/arcgis/rest/services/Current_Parcels/FeatureServer/0/query",
        "county_field": "COUNTY_NM",
        "out_fields": "OBJECTID,FIPS_NR,COUNTY_NM,PARCEL_ID_NR,SITUS_ADDRESS,SITUS_CITY_NM,SITUS_ZIP_NR,LANDUSE_CD",
        "batch_size": 2000,
        "use_counties": True,
        "estimated_parcels": 3200000
    },
    "OH": {
        "name": "Ohio",
        "service_url": "https://gis.ohiodnr.gov/arcgis_site2/rest/services/OIT_Services/odnr_landbase_v2/MapServer/4/query",
        "county_field": "COUNTY",
        "out_fields": "OBJECTID,PIN,COUNTY,STATEWIDE_PIN,ASSR_ACRES,OWNER1,OWNER2",
        "batch_size": 1000,
        "use_counties": True,
        "estimated_parcels": 5500000
    },
    "VT": {
        "name": "Vermont",
        "service_url": None,
        "download_url": "https://geodata.vermont.gov/pages/parcels",
        "batch_size": 0,
        "use_counties": False,
        "estimated_parcels": 350000
    },
    "ME": {
        "name": "Maine",
        "service_url": "https://gis.maine.gov/mapservices/rest/services/geolib/MeGIS_Parcels_organized_towns/FeatureServer/0/query",
        "county_field": None,
        "out_fields": "*",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 700000
    },
    "MD": {
        "name": "Maryland",
        "service_url": "https://geodata.md.gov/imap/rest/services/PlanningCadastre/MD_ParcelBoundaries/MapServer/0/query",
        "county_field": "JURSCODE",
        "out_fields": "OBJECTID,JURSCODE,ACCTID,ADDRESS,STRTNUM,STRTNAM,STRTTYP,OOI",
        "batch_size": 1000,
        "use_counties": True,
        "estimated_parcels": 2264000
    },
    "NY": {
        "name": "New York",
        "service_url": "https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/FeatureServer/1/query",
        "county_field": "COUNTY_NAME",
        "out_fields": "OBJECTID,COUNTY_NAME,MUNI_NAME,SWIS,PARCEL_ADDR,PRINT_KEY,SBL,PROP_CLASS,LAND_AV,TOTAL_AV,ACRES",
        "batch_size": 1000,
        "use_counties": True,
        "estimated_parcels": 3713000
    },
    "DC": {
        "name": "District of Columbia",
        "service_url": "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Property_and_Land_WebMercator/MapServer/53/query",
        "county_field": None,
        "out_fields": "OBJECTID,SSL,SQUARE,LOT,ARN,PREMISEADD,OWNERNAME,USECODE,LANDAREA",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 220913
    },
    "NJ": {
        "name": "New Jersey",
        "service_url": "https://services2.arcgis.com/XVOqAjTOJ5P6ngMu/arcgis/rest/services/Hosted_Parcels_Test_WebMer_20201016/FeatureServer/0/query",
        "county_field": "COUNTY",
        "out_fields": "*",
        "batch_size": 2000,
        "use_counties": True,
        "estimated_parcels": 2800000
    },
    # NEW STATEWIDE APIS - VERIFIED WORKING
    "CT": {
        "name": "Connecticut",
        "service_url": "https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/ArcGIS/rest/services/Connecticut_State_Parcel_Layer_2023/FeatureServer/0/query",
        "county_field": None,
        "out_fields": "*",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 1200000
    },
    "DE": {
        "name": "Delaware",
        "service_url": "https://enterprise.firstmap.delaware.gov/arcgis/rest/services/PlanningCadastre/DE_StateParcels/FeatureServer/0/query",
        "county_field": None,
        "out_fields": "*",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 400000
    },
    "HI": {
        "name": "Hawaii",
        "service_url": "https://geodata.hawaii.gov/arcgis/rest/services/ParcelsZoning/MapServer/25/query",
        "county_field": None,
        "out_fields": "*",
        "batch_size": 1000,
        "use_counties": False,
        "estimated_parcels": 450000
    },
    "IA": {
        "name": "Iowa",
        "service_url": "https://services3.arcgis.com/kd9gaiUExYqUbnoq/ArcGIS/rest/services/Iowa_Parcels_2017/FeatureServer/0/query",
        "county_field": None,
        "out_fields": "*",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 1800000
    },
    "MA": {
        "name": "Massachusetts",
        "service_url": "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/L3_TAXPAR_POLY_ASSESS_gdb/FeatureServer/0/query",
        "county_field": None,
        "out_fields": "*",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 2100000
    },
    "NH": {
        "name": "New Hampshire",
        "service_url": "https://granit24a.sr.unh.edu/hosting/rest/services/Hosted/CAD_ParcelMosaic/FeatureServer/1/query",
        "county_field": None,
        "out_fields": "*",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 600000
    },
    "ND": {
        "name": "North Dakota",
        "service_url": "https://services1.arcgis.com/GOcSXpzwBHyk2nog/arcgis/rest/services/NDGISHUB_Parcels/FeatureServer/0/query",
        "county_field": None,
        "out_fields": "*",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 800000
    },
    "WV": {
        "name": "West Virginia",
        "service_url": "https://services.wvgis.wvu.edu/arcgis/rest/services/Planning_Cadastre/WV_Parcels/MapServer/0/query",
        "county_field": None,
        "out_fields": "*",
        "batch_size": 2000,
        "use_counties": False,
        "estimated_parcels": 1000000
    }
}

def get_counties(service_url, county_field):
    """Fetch list of unique counties from the service."""
    params = {
        'where': '1=1',
        'outFields': county_field,
        'returnGeometry': 'false',
        'returnDistinctValues': 'true',
        'f': 'json'
    }
    url = f"{service_url}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            data = json.load(response)
            counties = sorted(set(
                f['attributes'][county_field]
                for f in data.get('features', [])
                if f['attributes'].get(county_field)
            ))
            return counties
    except Exception as e:
        print(f"Error fetching counties: {e}")
        return []

def export_batch(service_url, where_clause, out_fields, offset, batch_size):
    """Export a batch of features."""
    params = {
        'where': where_clause,
        'outFields': out_fields,
        'returnGeometry': 'true',
        'outSR': '4326',
        'f': 'geojson',
        'resultOffset': offset,
        'resultRecordCount': batch_size
    }
    url = f"{service_url}?{urllib.parse.urlencode(params)}"

    with urllib.request.urlopen(url, timeout=120) as response:
        return json.load(response)

def export_state(state_code, output_dir, resume_from=None):
    """Export all parcels for a state."""
    if state_code not in STATE_CONFIGS:
        print(f"Unknown state: {state_code}")
        print(f"Available: {', '.join(STATE_CONFIGS.keys())}")
        return False

    config = STATE_CONFIGS[state_code]
    print(f"\n{'='*60}")
    print(f" Exporting {config['name']} Parcels")
    print(f" Estimated: ~{config['estimated_parcels']:,} parcels")
    print(f"{'='*60}\n")

    if not config.get('service_url'):
        print(f"State {state_code} requires download, not API export")
        if config.get('download_url'):
            print(f"Download URL: {config['download_url']}")
        return False

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    counties_path = output_path / "counties"
    counties_path.mkdir(exist_ok=True)

    if config['use_counties']:
        # Get county list
        print("Fetching county list...")
        counties = get_counties(config['service_url'], config['county_field'])
        if not counties:
            print("ERROR: Could not fetch counties")
            return False

        print(f"Found {len(counties)} counties\n")

        # Check for resume
        start_idx = 0
        if resume_from:
            try:
                start_idx = counties.index(resume_from)
                print(f"Resuming from county: {resume_from} (#{start_idx + 1})")
            except ValueError:
                print(f"County '{resume_from}' not found, starting from beginning")

        total_features = 0

        for i, county in enumerate(counties[start_idx:], start=start_idx + 1):
            county_file = counties_path / f"{state_code}_{str(county).replace(' ', '_').replace('/', '_')}.geojson"

            # Skip if already exists
            if county_file.exists():
                try:
                    with open(county_file) as f:
                        existing = json.load(f)
                        count = len(existing.get('features', []))
                        if count > 0:
                            print(f"[{i}/{len(counties)}] Skipping {county} - already exported ({count:,} features)")
                            total_features += count
                            continue
                except:
                    pass

            print(f"[{i}/{len(counties)}] Processing {county}...")

            where = f"{config['county_field']}='{county}'" if isinstance(county, str) else f"{config['county_field']}={county}"
            all_features = []
            offset = 0

            while True:
                try:
                    data = export_batch(
                        config['service_url'],
                        where,
                        config['out_fields'],
                        offset,
                        config['batch_size']
                    )
                    features = data.get('features', [])
                    if not features:
                        break

                    all_features.extend(features)
                    print(f"    Fetched {len(features):,} (total: {len(all_features):,})")
                    offset += config['batch_size']
                    time.sleep(0.3)  # Rate limiting

                except Exception as e:
                    print(f"    Error at offset {offset}: {e}")
                    break

            # Save county file
            if all_features:
                output = {
                    "type": "FeatureCollection",
                    "features": all_features
                }
                with open(county_file, 'w') as f:
                    json.dump(output, f)

                size_mb = county_file.stat().st_size / (1024 * 1024)
                print(f"    Saved {len(all_features):,} features ({size_mb:.1f} MB)")
                total_features += len(all_features)
            else:
                print(f"    No features found")

        print(f"\n{'='*60}")
        print(f" Export Complete: {config['name']}")
        print(f" Total features: {total_features:,}")
        print(f"{'='*60}\n")

    else:
        # Export all at once with pagination
        print("Exporting all parcels (no county subdivision)...")
        all_features = []
        offset = 0
        output_file = output_path / f"parcels_{state_code.lower()}.geojson"

        while True:
            try:
                data = export_batch(
                    config['service_url'],
                    '1=1',
                    config['out_fields'],
                    offset,
                    config['batch_size']
                )
                features = data.get('features', [])
                if not features:
                    break

                all_features.extend(features)
                print(f"  Fetched {len(features):,} (total: {len(all_features):,})")
                offset += config['batch_size']
                time.sleep(0.3)

            except Exception as e:
                print(f"  Error at offset {offset}: {e}")
                break

        # Save file
        output = {
            "type": "FeatureCollection",
            "features": all_features
        }
        with open(output_file, 'w') as f:
            json.dump(output, f)

        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"\nSaved {len(all_features):,} features to {output_file} ({size_mb:.1f} MB)")

    return True

def main():
    parser = argparse.ArgumentParser(description='Export state parcel data from ArcGIS services')
    parser.add_argument('state', nargs='?', help='State code (FL, MT, NC, OR, WI, CO, IN)')
    parser.add_argument('--output', '-o', default='./output/geojson', help='Output directory')
    parser.add_argument('--resume', '-r', help='Resume from specific county')
    parser.add_argument('--list', '-l', action='store_true', help='List available states')

    args = parser.parse_args()

    if args.list:
        print("\nAvailable states:")
        for code, config in STATE_CONFIGS.items():
            api = "REST API" if config.get('service_url') else "Download"
            print(f"  {code}: {config['name']} ({api}, ~{config['estimated_parcels']:,} parcels)")
        return

    if not args.state:
        parser.print_help()
        return

    export_state(args.state.upper(), args.output, args.resume)

if __name__ == "__main__":
    main()
