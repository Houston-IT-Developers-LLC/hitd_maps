#!/usr/bin/env python3
"""
County-by-County Parcel Exporter

For states without statewide APIs, this script exports parcels from individual county APIs.
"""

import sys
import json
import urllib.request
import urllib.parse
import time
import os
from pathlib import Path

# County configurations organized by state
COUNTY_CONFIGS = {
    # ============================================================
    # PRIORITY HUNTING STATES - STATEWIDE APIs
    # ============================================================

    # TEXAS STATEWIDE (TNRIS StratMap - 28M parcels)
    "TX_STATEWIDE": {
        "name": "Texas Statewide (TNRIS StratMap 2025)",
        "service_url": "https://feature.tnris.org/arcgis/rest/services/Parcels/stratmap25_land_parcels_48/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "TX_STATEWIDE_RECENT": {
        "name": "Texas Statewide (TNRIS Most Recent)",
        "service_url": "https://feature.tnris.org/arcgis/rest/services/Parcels/stratmap_land_parcels_48_most_recent/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEW YORK STATEWIDE (NYS ITS - 9M parcels)
    "NY_STATEWIDE_V2": {
        "name": "New York Statewide Tax Parcels (FeatureServer)",
        "service_url": "https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/FeatureServer/1/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # MONTANA STATEWIDE (MSDI Framework - All counties)
    "MT_STATEWIDE_V2": {
        "name": "Montana Statewide (MSDI Framework)",
        "service_url": "https://gisservicemt.gov/arcgis/rest/services/MSDI_Framework/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ============================================================
    # MICHIGAN COUNTIES (ALL VERIFIED WORKING)
    "MI_OAKLAND": {
        "name": "Oakland County, MI",
        "service_url": "https://services.arcgis.com/f4rR7WnIfGBdVYFd/arcgis/rest/services/Tax_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MI_WAYNE": {
        "name": "Wayne County (Detroit), MI",
        "service_url": "https://services2.arcgis.com/HsXtOCMp1Nis1Ogr/arcgis/rest/services/DetParcels2021_wOwnerInfo_20230801/FeatureServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MI_KENT": {
        "name": "Kent County, MI",
        "service_url": "https://gis.kentcountymi.gov/agisprod/rest/services/ParcelsWithCondos/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MI_MACOMB": {
        "name": "Macomb County, MI",
        "service_url": "https://gis.macombgov.org/arcgis1/rest/services/Equalization/Equalization_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MI_OTTAWA": {
        "name": "Ottawa County, MI",
        "service_url": "https://gis.miottawa.org/arcgis/rest/services/HostedServices/Parcels/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MI_MARQUETTE": {
        "name": "Marquette County, MI",
        "service_url": "https://services9.arcgis.com/6EuFgO4fLTqfNOhu/ArcGIS/rest/services/MarquetteParcelData/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MI_WASHTENAW": {
        "name": "Washtenaw County (Ann Arbor), MI",
        "service_url": "https://gisservices.ewashtenaw.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ILLINOIS COUNTIES (VERIFIED WORKING)
    "IL_DUPAGE": {
        "name": "DuPage County, IL",
        "service_url": "https://gis.dupageco.org/arcgis/rest/services/ParcelSearch/DuPageAssessmentParcelViewer/MapServer/4/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "IL_LAKE": {
        "name": "Lake County, IL",
        "service_url": "https://maps.lakecountyil.gov/arcgis/rest/services/GISMapping/WABParcels/MapServer/12/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "IL_WILL": {
        "name": "Will County, IL",
        "service_url": "https://gis.willcountyillinois.com/hosting/rest/services/Basemap/Parcels_LY_DV/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MISSOURI COUNTIES (VERIFIED WORKING)
    "MO_ST_CHARLES": {
        "name": "St. Charles County, MO",
        "service_url": "https://maps.sccmo.org/scc_gis/rest/services/open_data/Tax_Information/FeatureServer/3/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MO_CLAY": {
        "name": "Clay County, MO",
        "service_url": "https://services7.arcgis.com/3c8lLdmDNevrTlaV/ArcGIS/rest/services/ClayCountyParcelService/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MO_KANSAS_CITY": {
        "name": "Kansas City, MO",
        "service_url": "https://mapd.kcmo.org/kcgis/rest/services/DataLayers/FeatureServer/14/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MO_CHRISTIAN": {
        "name": "Christian County, MO",
        "service_url": "https://gis.christiancountymo.gov/arcgis/rest/services/Christian_Ozark/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # TEXAS COUNTIES (ALL VERIFIED WORKING)
    "TX_HARRIS": {
        "name": "Harris County, TX (Houston)",
        "service_url": "https://www.gis.hctx.net/arcgis/rest/services/HCAD/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,  # API max is 1000
    },
    "TX_TARRANT": {
        "name": "Tarrant County, TX (Fort Worth)",
        "service_url": "https://mapit.tarrantcounty.com/arcgis/rest/services/Dynamic/TADParcelsApp/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "TX_BEXAR": {
        "name": "Bexar County, TX (San Antonio)",
        "service_url": "https://maps.bexar.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "TX_TRAVIS": {
        "name": "Travis County, TX (Austin)",
        "service_url": "https://gis.traviscountytx.gov/server1/rest/services/Boundaries_and_Jurisdictions/TCAD_public/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "TX_DENTON": {
        "name": "Denton County, TX",
        "service_url": "https://gis.dentoncounty.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # PENNSYLVANIA COUNTIES
    "PA_PHILADELPHIA": {
        "name": "Philadelphia County, PA",
        "service_url": "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/Philadelphia_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "PA_ALLEGHENY": {
        "name": "Allegheny County, PA",
        "service_url": "https://gisdata.alleghenycounty.us/arcgis/rest/services/OPENDATA/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "PA_MONTGOMERY": {
        "name": "Montgomery County, PA",
        "service_url": "https://gis.montcopa.org/arcgis/rest/services/OpenData/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "PA_BUCKS": {
        "name": "Bucks County, PA",
        "service_url": "https://services3.arcgis.com/SP47Tddf7RK32lBU/arcgis/rest/services/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "PA_LANCASTER": {
        "name": "Lancaster County, PA",
        "service_url": "https://arcgis.lancastercountypa.gov/arcgis/rest/services/Properties/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "PA_BERKS": {
        "name": "Berks County, PA",
        "service_url": "https://gis.co.berks.pa.us/arcgis/rest/services/Assess/ParcelBase4/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "PA_YORK": {
        "name": "York County, PA",
        "service_url": "https://www.yorkcountygis.com/arcgis/rest/services/OpenData/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "PA_LEHIGH": {
        "name": "Lehigh County, PA",
        "service_url": "https://gis.lehighcounty.org/arcgis/rest/services/OpenData/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # GEORGIA COUNTIES
    "GA_FULTON": {
        "name": "Fulton County, GA",
        "service_url": "https://gis.fultoncountyga.gov/arcgis/rest/services/MapServices/ParcelsRoads/MapServer/52/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_GWINNETT": {
        "name": "Gwinnett County, GA",
        "service_url": "https://gis3.gwinnettcounty.com/mapvis/rest/services/GISDataBrowser/GC_Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_COBB": {
        "name": "Cobb County, GA",
        "service_url": "https://gis.cobbcounty.org/arcgis/rest/services/OpenData/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_DEKALB": {
        "name": "DeKalb County, GA",
        "service_url": "https://gis.dekalbcountyga.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_CHEROKEE": {
        "name": "Cherokee County, GA",
        "service_url": "https://services6.arcgis.com/dpaY3zboICQILFY5/arcgis/rest/services/Cherokee_County_Parcels_/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "GA_GLYNN": {
        "name": "Glynn County, GA",
        "service_url": "https://webadaptor.glynncounty-ga.gov/webadaptor/rest/services/Parcels/Parcels_Rectified/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_CHATHAM": {
        "name": "Chatham County, GA (Savannah)",
        "service_url": "https://pub.sagis.org/arcgis/rest/services/Pictometry/ParcelDigest/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_LIBERTY": {
        "name": "Liberty County, GA",
        "service_url": "https://gis.libertycountyga.com/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # TENNESSEE (STATEWIDE + COUNTIES)
    "TN_STATEWIDE": {
        "name": "Tennessee Statewide Parcels (TDEC)",
        "service_url": "https://tdeconline.tn.gov/arcgis/rest/services/Parcels_OG/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "TN_SHELBY": {
        "name": "Shelby County, TN (Memphis)",
        "service_url": "https://gis.shelbycountytn.gov/arcgis/rest/services/Parcel/CERT_Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "TN_DAVIDSON": {
        "name": "Davidson County, TN (Nashville)",
        "service_url": "https://maps.nashville.gov/arcgis/rest/services/Cadastral/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "TN_KNOX": {
        "name": "Knox County, TN (Knoxville)",
        "service_url": "https://www.kgis.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "TN_HAMILTON": {
        "name": "Hamilton County, TN (Chattanooga)",
        "service_url": "https://mapsdev.hamiltontn.gov/hcwa03/rest/services/OpenGov/OpenGov_HamiltonTN/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "TN_RUTHERFORD": {
        "name": "Rutherford County, TN",
        "service_url": "https://maps.rutherfordcountytn.gov/ags02/rest/services/ParcelCAMA/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "TN_MONTGOMERY": {
        "name": "Montgomery County, TN",
        "service_url": "https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/ArcGIS/rest/services/Montgomery_County_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "TN_WILSON": {
        "name": "Wilson County, TN",
        "service_url": "https://services.arcgis.com/wilsoncounty/arcgis/rest/services/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # KENTUCKY COUNTIES
    "KY_JEFFERSON": {
        "name": "Jefferson County, KY (Louisville)",
        "service_url": "https://gis.lojic.org/maps/rest/services/LojicSolutions/OpenDataPVA/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "KY_FAYETTE": {
        "name": "Fayette County, KY (Lexington)",
        "service_url": "https://services.arcgis.com/lfucg/arcgis/rest/services/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KY_KENTON": {
        "name": "Kenton County, KY",
        "service_url": "https://maps.linkgis.org/server/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "KY_BOONE": {
        "name": "Boone County, KY",
        "service_url": "https://secure.boonecountygis.com/server/rest/services/ParcelLayers/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "KY_HARDIN": {
        "name": "Hardin County, KY",
        "service_url": "http://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_PVA_Hardin_Parcels_WGS84WM/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # VIRGINIA COUNTIES (additional to statewide)
    "VA_ALBEMARLE": {
        "name": "Albemarle County, VA",
        "service_url": "https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/Albemarle_County_Parcels_Map/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # SOUTH CAROLINA COUNTIES
    "SC_CHARLESTON": {
        "name": "Charleston County, SC",
        "service_url": "https://gis.charlestoncounty.org/arcgis/rest/services/Parcel/ParcelData/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "SC_GREENVILLE": {
        "name": "Greenville County, SC",
        "service_url": "https://www.gcgis.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "SC_RICHLAND": {
        "name": "Richland County, SC",
        "service_url": "https://gis.richlandcountysc.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ALABAMA COUNTIES
    "AL_JEFFERSON": {
        "name": "Jefferson County, AL (Birmingham)",
        "service_url": "https://jeffcomaps.jccal.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AL_MOBILE": {
        "name": "Mobile County, AL",
        "service_url": "https://gisportal.mobilecountyal.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AL_MADISON": {
        "name": "Madison County, AL (Huntsville)",
        "service_url": "https://maps.madisoncountyal.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # LOUISIANA PARISHES
    "LA_ORLEANS": {
        "name": "Orleans Parish, LA (New Orleans)",
        "service_url": "https://gis.nola.gov/arcgis/rest/services/Cadastral/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "LA_EASTBATONROUGE": {
        "name": "East Baton Rouge Parish, LA",
        "service_url": "https://gis.brla.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "LA_JEFFERSON": {
        "name": "Jefferson Parish, LA",
        "service_url": "https://gis.jpso.com/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MISSISSIPPI COUNTIES
    "MS_HINDS": {
        "name": "Hinds County, MS (Jackson)",
        "service_url": "https://gis.co.hinds.ms.us/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MS_HARRISON": {
        "name": "Harrison County, MS",
        "service_url": "https://gis.co.harrison.ms.us/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # OKLAHOMA COUNTIES
    "OK_OKLAHOMA": {
        "name": "Oklahoma County, OK (OKC)",
        "service_url": "https://gisdata.oklahomacounty.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OK_TULSA": {
        "name": "Tulsa County, OK",
        "service_url": "https://gis.tulsacounty.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ARIZONA COUNTIES (VERIFIED WORKING)
    "AZ_MARICOPA": {
        "name": "Maricopa County, AZ (Phoenix)",
        "service_url": "https://gis.mcassessor.maricopa.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "AZ_PIMA": {
        "name": "Pima County, AZ (Tucson)",
        "service_url": "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AZ_PINAL": {
        "name": "Pinal County, AZ",
        "service_url": "https://rogue.casagrandeaz.gov/arcgis/rest/services/Pinal_County/Pinal_County_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEVADA COUNTIES (VERIFIED WORKING)
    "NV_CLARK": {
        "name": "Clark County, NV (Las Vegas)",
        "service_url": "https://maps.clarkcountynv.gov/arcgis/rest/services/Assessor/Layers/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NV_WASHOE": {
        "name": "Washoe County, NV (Reno)",
        "service_url": "https://wcgisweb.washoecounty.us/arcgis/rest/services/OpenData/OpenData/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # IDAHO COUNTIES (PARTIAL COVERAGE)
    "ID_ADA_MERIDIAN": {
        "name": "City of Meridian, Ada County, ID (Boise area)",
        "service_url": "https://gis.meridiancity.org/server/rest/services/CD/AGOL_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # CALIFORNIA COUNTIES (VERIFIED WORKING)
    "CA_LOS_ANGELES": {
        "name": "Los Angeles County, CA",
        "service_url": "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "CA_SAN_DIEGO": {
        "name": "San Diego County, CA",
        "service_url": "https://geo.sandag.org/server/rest/services/Hosted/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CA_ORANGE": {
        "name": "Orange County, CA",
        "service_url": "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "CA_RIVERSIDE": {
        "name": "Riverside County, CA",
        "service_url": "https://content.rcflood.org/arcgis/rest/services/FloodControlJS/DynamicLayer/FeatureServer/3/query",
        "out_fields": "*",
        "batch_size": 3000,
    },
    "CA_SACRAMENTO": {
        "name": "Sacramento County, CA",
        "service_url": "https://mapservices.gis.saccounty.net/arcgis/rest/services/PARCELS/MapServer/8/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CA_FRESNO": {
        "name": "Fresno County, CA",
        "service_url": "https://gisprod10.co.fresno.ca.us/server/rest/services/Hosted/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # KANSAS COUNTIES
    "KS_SEDGWICK": {
        "name": "Sedgwick County, KS (Wichita)",
        "service_url": "https://services7.arcgis.com/McLat6HlPl45bNBv/arcgis/rest/services/SC_WebServices_view/FeatureServer/3/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # SOUTH DAKOTA
    "SD_SIOUX_FALLS": {
        "name": "Sioux Falls, SD",
        "service_url": "https://gis.siouxfalls.gov/arcgis/rest/services/Data/Property/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # WYOMING COUNTIES
    "WY_LARAMIE": {
        "name": "Laramie County, WY (Cheyenne)",
        "service_url": "https://maps.laramiecounty.com/arcgis/rest/services/Planning/Standard_Information/MapServer/12/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # LOUISIANA PARISHES (UPDATED/VERIFIED)
    "LA_ORLEANS_V2": {
        "name": "Orleans Parish, LA (New Orleans)",
        "service_url": "https://gis.nola.gov/arcgis/rest/services/LandBase/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "LA_JEFFERSON_V2": {
        "name": "Jefferson Parish, LA",
        "service_url": "https://eweb.jeffparish.net/arcgis/rest/services/Cadastre/Cadastre/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "LA_EAST_BATON_ROUGE": {
        "name": "East Baton Rouge Parish, LA",
        "service_url": "https://maps.brla.gov/gis/rest/services/Cadastral/Tax_Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MISSISSIPPI COUNTIES (VERIFIED)
    "MS_DESOTO": {
        "name": "DeSoto County, MS",
        "service_url": "https://gis.desotocountyms.gov/arcgis/rest/services/CountyWebMap/Tax_Assessors_County_Web_Map/MapServer/29/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MS_HINDS_V2": {
        "name": "Hinds County, MS (Jackson)",
        "service_url": "https://gis.cmpdd.org/arcgis/rest/services/Hosted/Hinds_County_Map/FeatureServer/24/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ALABAMA COUNTIES (VERIFIED)
    "AL_MADISON_V2": {
        "name": "Madison County, AL (Huntsville)",
        "service_url": "https://maps.huntsvilleal.gov/server/rest/services/Boundaries/MadisonCountyParcels/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # SOUTH CAROLINA COUNTIES (VERIFIED)
    "SC_CHARLESTON_V2": {
        "name": "Charleston County, SC",
        "service_url": "https://gisccapps.charlestoncounty.org/arcgis/rest/services/GIS_VIEWER/Parcel_Search/MapServer/4/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SC_GREENVILLE_V2": {
        "name": "Greenville County, SC",
        "service_url": "https://www.gcgis.org/arcgis/rest/services/StormWater/StormWater/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # OREGON COUNTIES (VERIFIED WORKING)
    "OR_DOUGLAS": {
        "name": "Douglas County, OR",
        "service_url": "https://gis.co.douglas.or.us/server/rest/services/Parcel/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OR_LANE": {
        "name": "Lane County, OR (Eugene)",
        "service_url": "https://lcmaps.lanecounty.org/arcgis/rest/services/AT/AddressParcelSales/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OR_DESCHUTES": {
        "name": "Deschutes County, OR (Bend)",
        "service_url": "https://maps.deschutes.org/arcgis/rest/services/OpenData/LandFD/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OR_BENTON": {
        "name": "Benton County, OR (Corvallis)",
        "service_url": "https://gis.co.benton.or.us/arcgis/rest/services/Public/Appraisal/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OR_STATEWIDE": {
        "name": "Oregon Statewide (Forestry Tax Lots)",
        "service_url": "https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # PENNSYLVANIA (STATEWIDE + COUNTIES)
    "PA_STATEWIDE": {
        "name": "Pennsylvania Statewide",
        "service_url": "https://gis.dep.pa.gov/depgisprd/rest/services/Parcels/PA_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "PA_PASDA_STATEWIDE": {
        "name": "Pennsylvania PASDA Statewide",
        "service_url": "https://apps.pasda.psu.edu/arcgis/rest/services/PA_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "PA_LACKAWANNA": {
        "name": "Lackawanna County, PA",
        "service_url": "https://gis.lackawannacounty.org/arcgis/rest/services/GISViewer/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "PA_LANCASTER_V2": {
        "name": "Lancaster County, PA",
        "service_url": "https://arcgis.lancastercountypa.gov/arcgis/rest/services/parcel_poly/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "PA_DELAWARE": {
        "name": "Delaware County, PA",
        "service_url": "https://gis.delcopa.gov/arcgis/rest/services/Parcels/Parcels_Public_Access/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # ALASKA BOROUGHS (via DNR)
    "AK_FAIRBANKS": {
        "name": "Fairbanks North Star Borough, AK",
        "service_url": "https://arcgis.dnr.alaska.gov/arcgis/rest/services/OpenData/Administrative_BoroughParcels/FeatureServer/9/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_JUNEAU": {
        "name": "City & Borough of Juneau, AK",
        "service_url": "https://arcgis.dnr.alaska.gov/arcgis/rest/services/OpenData/Administrative_BoroughParcels/FeatureServer/3/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # OHIO (STATEWIDE + COUNTIES)
    "OH_STATEWIDE": {
        "name": "Ohio Statewide Parcels (DNR)",
        "service_url": "https://gis.ohiodnr.gov/arcgis_site2/rest/services/OIT_Services/odnr_landbase_v2/MapServer/4/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OH_FRANKLIN": {
        "name": "Franklin County, OH (Columbus)",
        "service_url": "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 3000,
    },
    "OH_MONTGOMERY": {
        "name": "Montgomery County, OH (Dayton)",
        "service_url": "https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/ArcGIS/rest/services/Montgomery_County_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OH_SUMMIT": {
        "name": "Summit County, OH (Akron)",
        "service_url": "https://maps.summitcounty.org/arcgis/rest/services/Maps/OnlineMap/MapServer/4/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # ILLINOIS COUNTIES (MORE)
    "IL_COOK": {
        "name": "Cook County, IL (Chicago)",
        "service_url": "https://gis.cookcountyil.gov/traditional/rest/services/CookViewer3Dynamic/MapServer/2024/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # WISCONSIN COUNTIES
    "WI_MILWAUKEE": {
        "name": "Milwaukee County, WI",
        "service_url": "https://lio.milwaukeecountywi.gov/arcgis/rest/services/PropertyInfo/Parcels_EagleView/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "WI_WAUKESHA": {
        "name": "Waukesha County, WI",
        "service_url": "https://gis.waukeshacounty.gov/host/rest/services/Parcel_Basemap/MapServer/10/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "WI_KENOSHA": {
        "name": "Kenosha County, WI",
        "service_url": "https://mapping.kenoshacountywi.gov/server/rest/services/SpecialAppData/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "WI_RACINE": {
        "name": "Racine County, WI",
        "service_url": "https://arcgis.racinecounty.com/arcgis/rest/services/Mapbook/Mapbook/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MINNESOTA COUNTIES
    "MN_HENNEPIN": {
        "name": "Hennepin County, MN (Minneapolis)",
        "service_url": "https://gis.hennepin.us/arcgis/rest/services/HennepinData/LAND_PROPERTY/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "MN_RAMSEY": {
        "name": "Ramsey County, MN (St. Paul)",
        "service_url": "https://maps.co.ramsey.mn.us/arcgis/rest/services/OpenData/OpenData/FeatureServer/12/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # NEBRASKA COUNTIES
    "NE_LANCASTER": {
        "name": "Lancaster County, NE (Lincoln)",
        "service_url": "https://gis.lincoln.ne.gov/public/rest/services/Assessor/ParcelLinesAerial/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # MICHIGAN COUNTIES (MORE)
    "MI_KENT_V2": {
        "name": "Kent County, MI (Grand Rapids)",
        "service_url": "https://gis.kentcountymi.gov/agisprod/rest/services/ParcelsWithCondos/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "MI_GRAND_TRAVERSE": {
        "name": "Grand Traverse County, MI",
        "service_url": "https://gis.grandtraverse.org/arcgis/rest/services/Treasurer/Parcel20/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # NEW JERSEY (STATEWIDE)
    "NJ_STATEWIDE": {
        "name": "New Jersey Statewide",
        "service_url": "https://services.arcgis.com/njFNhDsUCentVYJW/ArcGIS/rest/services/Parcels_in_New_Jersey/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEW YORK (STATEWIDE + COUNTIES)
    "NY_STATEWIDE": {
        "name": "New York Statewide Tax Parcels Public",
        "service_url": "https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NY_CENTROIDS": {
        "name": "New York Statewide Tax Parcel Centroids",
        "service_url": "https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcel_Centroid_Points/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NY_WESTCHESTER": {
        "name": "Westchester County, NY",
        "service_url": "https://gis2.westchestergov.com/arcgis/rest/services/OpenData/TaxParcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NY_ERIE": {
        "name": "Erie County (Buffalo), NY",
        "service_url": "https://gis.erie.gov/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NY_SUFFOLK": {
        "name": "Suffolk County, NY",
        "service_url": "https://gis.suffolkcountyny.gov/gis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # VIRGINIA COUNTIES
    "VA_FAIRFAX": {
        "name": "Fairfax County, VA",
        "service_url": "https://www.fairfaxcounty.gov/gisint1/rest/services/PLUS/DefaultMap/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "VA_ARLINGTON": {
        "name": "Arlington County, VA",
        "service_url": "https://gis.arlingtonva.us/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "VA_LOUDOUN": {
        "name": "Loudoun County, VA",
        "service_url": "https://logis.loudoun.gov/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "VA_PRINCE_WILLIAM": {
        "name": "Prince William County, VA",
        "service_url": "https://gismap.pwcgov.org/arcgis/rest/services/Parcels/Parcel_OD/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # TEXAS COUNTIES (NEW)
    "TX_WILLIAMSON": {
        "name": "Williamson County, TX",
        "service_url": "https://gis.wilco.org/arcgis/rest/services/Land/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "TX_DALLAS": {
        "name": "Dallas County, TX",
        "service_url": "https://egis.dallascityhall.com/arcgis/rest/services/Basemap/DallasTaxParcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "TX_EL_PASO": {
        "name": "El Paso County, TX",
        "service_url": "https://gis.elpasoco.com/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # FLORIDA COUNTIES (NEW)
    "FL_MIAMI_DADE": {
        "name": "Miami-Dade County, FL",
        "service_url": "https://gis.miamidade.gov/arcgis/rest/services/PropertySearch/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_PALM_BEACH": {
        "name": "Palm Beach County, FL",
        "service_url": "https://maps.co.palm-beach.fl.us/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # GEORGIA COUNTIES (NEW)
    "GA_FORSYTH": {
        "name": "Forsyth County, GA",
        "service_url": "https://gis.forsythco.com/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NORTH CAROLINA COUNTIES (NEW)
    "NC_MECKLENBURG": {
        "name": "Mecklenburg County (Charlotte), NC",
        "service_url": "https://gis.charlottenc.gov/arcgis/rest/services/CountyData/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NC_DURHAM": {
        "name": "Durham County, NC",
        "service_url": "https://webgis.dconc.gov/server/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ARIZONA COUNTIES (NEW)
    "AZ_YAVAPAI": {
        "name": "Yavapai County, AZ",
        "service_url": "https://gis.yavapai.us/arcgis/rest/services/Assessor/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AZ_MOHAVE": {
        "name": "Mohave County, AZ",
        "service_url": "https://gis.mohave.gov/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MARYLAND (STATEWIDE)
    "MD_STATEWIDE": {
        "name": "Maryland Statewide",
        "service_url": "https://geodata.md.gov/imap/rest/services/PlanningCadastre/MD_ParcelBoundaries/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # VERMONT (STATEWIDE)
    "VT_STATEWIDE": {
        "name": "Vermont Statewide",
        "service_url": "https://services1.arcgis.com/BkFxaEFNwHqX3tAw/arcgis/rest/services/FS_VCGI_VTPARCELS_WM_NOCACHE_v2/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ARKANSAS (STATEWIDE)
    "AR_STATEWIDE": {
        "name": "Arkansas Statewide",
        "service_url": "https://gis.arkansas.gov/arcgis/rest/services/FEATURESERVICES/Planning_Cadastre/FeatureServer/6/query",
        "out_fields": "*",
        "batch_size": 200,
    },

    # TENNESSEE COUNTIES
    "TN_NASHVILLE": {
        "name": "Nashville-Davidson, TN",
        "service_url": "https://maps.nashville.gov/arcgis/rest/services/Cadastral/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "TN_SHELBY": {
        "name": "Shelby County (Memphis), TN",
        "service_url": "https://gis.shelbycountytn.gov/arcgis/rest/services/Parcel/CERT_Parcel/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MAINE (UNORGANIZED TERRITORY)
    "ME_UNORGANIZED": {
        "name": "Maine Unorganized Territory",
        "service_url": "https://gis.maine.gov/arcgis/rest/services/mrs/Maine_Parcels_Unorganized_Territory/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "ME_BANGOR": {
        "name": "Bangor, ME",
        "service_url": "https://mapping.bangormaine.gov/server/rest/services/ParcelViewer/Parcel/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MONTANA (STATEWIDE)
    "MT_STATEWIDE": {
        "name": "Montana Statewide",
        "service_url": "https://services.arcgis.com/qnjIrwR8z5Izc0ij/ArcGIS/rest/services/DEV%20Montana%20Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # WYOMING (STATEWIDE)
    "WY_STATEWIDE": {
        "name": "Wyoming Statewide Private Parcels",
        "service_url": "https://gis.deq.wyo.gov/arcgis/rest/services/WY_PRIVATE_PARCELS/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "WY_LARAMIE": {
        "name": "Laramie County, WY",
        "service_url": "https://maps.laramiecounty.com/arcgis/rest/services/Planning/Standard_Information/MapServer/12/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # UTAH (STATEWIDE)
    "UT_STATEWIDE": {
        "name": "Utah Statewide",
        "service_url": "https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/Parcels_Utah/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # IDAHO (STATEWIDE)
    "ID_STATEWIDE": {
        "name": "Idaho Statewide",
        "service_url": "https://gis.idwr.idaho.gov/hosting/rest/services/Reference/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEVADA (STATEWIDE)
    "NV_STATEWIDE": {
        "name": "Nevada Statewide",
        "service_url": "https://arcgis.water.nv.gov/arcgis/rest/services/BaseLayers/County_Parcels_in_Nevada/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "NV_CLARK_V2": {
        "name": "Clark County (Las Vegas), NV",
        "service_url": "https://maps.clarkcountynv.gov/arcgis/rest/services/GISMO/AssessorMap/FeatureServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # COLORADO COUNTIES
    "CO_BOULDER": {
        "name": "Boulder County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/3/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_EL_PASO": {
        "name": "El Paso County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/11/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_JEFFERSON": {
        "name": "Jefferson County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/16/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # GEORGIA COUNTIES
    "GA_FULTON": {
        "name": "Fulton County (Atlanta), GA",
        "service_url": "https://gis.fultoncountyga.gov/arcgis/rest/services/MapServices/ParcelsRoads/MapServer/5/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_DEKALB": {
        "name": "DeKalb County, GA",
        "service_url": "https://gis.dekalbcountyga.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # OHIO COUNTIES
    "OH_LUCAS": {
        "name": "Lucas County (Toledo), OH",
        "service_url": "http://lcapps.co.lucas.oh.us/arcgis/rest/services/SanitaryEngineer/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # INDIANA COUNTIES
    "IN_ALLEN": {
        "name": "Allen County, IN",
        "service_url": "https://gis.acimap.us/services/rest/services/BaseMaps/GeneralPurposeBaseMap/MapServer/24/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # WISCONSIN (STATEWIDE)
    "WI_STATEWIDE": {
        "name": "Wisconsin Statewide",
        "service_url": "https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MISSISSIPPI (STATEWIDE)
    "MS_STATEWIDE": {
        "name": "Mississippi Statewide",
        "service_url": "https://gis.mississippi.edu/server/rest/services/Cadastral/MS_Parcels_Aprl2024/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MS_EAST_STATEWIDE": {
        "name": "Mississippi East Statewide Parcels (2024)",
        "service_url": "https://gis.mississippi.edu/server/rest/services/Cadastral/MS_East_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "MS_WEST_STATEWIDE": {
        "name": "Mississippi West Statewide Parcels (2024)",
        "service_url": "https://gis.mississippi.edu/server/rest/services/Cadastral/MS_West_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # VIRGINIA (STATEWIDE - NEW 2024)
    "VA_STATEWIDE_V2": {
        "name": "Virginia Statewide Parcels (VGIN 2024)",
        "service_url": "https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VA_Base_Layers/VA_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # FLORIDA (STATEWIDE - NEW)
    "FL_STATEWIDE": {
        "name": "Florida Statewide Cadastral (10.8M parcels)",
        "service_url": "https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NORTH CAROLINA (STATEWIDE - NEW)
    "NC_STATEWIDE": {
        "name": "North Carolina Statewide Parcels (5.9M parcels)",
        "service_url": "https://services.nconemap.gov/secure/rest/services/NC1Map_Parcels/FeatureServer/1/query",
        "out_fields": "*",
        "batch_size": 5000,
    },

    # NEW YORK STATE (STATEWIDE - NEW)
    "NY_STATEWIDE": {
        "name": "New York State Tax Parcels Public (3.7M parcels)",
        "service_url": "https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # GEORGIA COUNTIES (NEW)
    "GA_FULTON_V2": {
        "name": "Fulton County (Atlanta), GA",
        "service_url": "https://gismaps.fultoncountyga.gov/arcgispub/rest/services/OpenData/Tax_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_FORSYTH_V2": {
        "name": "Forsyth County, GA",
        "service_url": "https://geo.forsythco.com/gis/rest/services/Public/Tax_Parcel/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # OKLAHOMA COUNTY (NEW)
    "OK_COUNTY_V2": {
        "name": "Oklahoma County Tax Parcels",
        "service_url": "https://services.arcgis.com/f4rR7WnIfGBdVYFd/arcgis/rest/services/Tax_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # PENNSYLVANIA (STATEWIDE - NEW)
    "PA_STATEWIDE": {
        "name": "Pennsylvania Statewide Parcels (PASDA)",
        "service_url": "https://apps.pasda.psu.edu/arcgis/rest/services/PA_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # WASHINGTON STATE (STATEWIDE - NEW)
    "WA_STATEWIDE_V2": {
        "name": "Washington State Current Parcels (3.3M)",
        "service_url": "https://services.arcgis.com/jsIt88o09Q0r1j8h/arcgis/rest/services/Current_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "WA_KING_COUNTY": {
        "name": "King County (Seattle), WA",
        "service_url": "https://gismaps.kingcounty.gov/arcgis/rest/services/Property/KingCo_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # MICHIGAN (NEW)
    "MI_WAYNE_COUNTY": {
        "name": "Wayne County (Detroit Metro), MI",
        "service_url": "https://www.waynecounty.com/gisserver/rest/services/ParcelViewer/prcls_fullAdd_parsed_FINAL/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MI_DETROIT": {
        "name": "City of Detroit Parcels",
        "service_url": "https://services2.arcgis.com/qvkbeam7Wirps6zC/ArcGIS/rest/services/parcel_file_current/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # OHIO (NEW)
    "OH_STATEWIDE": {
        "name": "Ohio Statewide Parcels (DNR 6.3M)",
        "service_url": "https://gis.ohiodnr.gov/arcgis_site2/rest/services/OIT_Services/odnr_landbase_v2/MapServer/4/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OH_FRANKLIN": {
        "name": "Franklin County (Columbus), OH",
        "service_url": "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 3000,
    },

    # ILLINOIS (NEW)
    "IL_COOK_COUNTY": {
        "name": "Cook County (Chicago), IL",
        "service_url": "https://gis.cookcountyil.gov/traditional/rest/services/parcel_current_beta/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEW JERSEY (STATEWIDE - NEW)
    "NJ_STATEWIDE": {
        "name": "New Jersey Statewide Parcels (3.5M)",
        "service_url": "https://maps.nj.gov/arcgis/rest/services/Framework/Cadastral/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # MINNESOTA (NEW)
    "MN_HENNEPIN": {
        "name": "Hennepin County (Minneapolis), MN",
        "service_url": "https://gis.hennepin.us/arcgis/rest/services/HennepinData/LAND_PROPERTY/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MASSACHUSETTS (STATEWIDE - NEW)
    "MA_STATEWIDE": {
        "name": "Massachusetts Statewide Parcels (MassGIS 2.5M)",
        "service_url": "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/L3_TAXPAR_POLY_ASSESS_gdb/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # CONNECTICUT (STATEWIDE - NEW)
    "CT_STATEWIDE": {
        "name": "Connecticut Statewide Parcels (1.3M)",
        "service_url": "https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/ArcGIS/rest/services/Connecticut_CAMA_and_Parcel_Layer/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ARIZONA (NEW)
    "AZ_MARICOPA": {
        "name": "Maricopa County (Phoenix), AZ",
        "service_url": "https://gis.mcassessor.maricopa.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # COLORADO (NEW)
    "CO_ARAPAHOE": {
        "name": "Arapahoe County, CO",
        "service_url": "https://gis.arapahoegov.com/arcgis/rest/services/CountyFeatureService/FeatureServer/14/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # LOUISIANA PARISHES (MORE)
    "LA_LAFAYETTE": {
        "name": "Lafayette Parish, LA",
        "service_url": "https://maps.lafayettela.gov/arcgis/rest/services/BaseLayers/LCG_Parcels_withCAMA_Data/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ALABAMA COUNTIES (MORE)
    "AL_MONTGOMERY": {
        "name": "Montgomery County, AL",
        "service_url": "https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/ArcGIS/rest/services/Montgomery_County_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # OKLAHOMA COUNTIES
    "OK_OKLAHOMA_COUNTY": {
        "name": "Oklahoma County (OKC), OK",
        "service_url": "https://oklahomacounty.geocortex.com/arcgis/rest/services/Staging/OklahomaCountyAllParcelsData/MapServer/12/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # WASHINGTON STATE (STATEWIDE + COUNTIES)
    "WA_STATEWIDE": {
        "name": "Washington Statewide Parcels (DAHP)",
        "service_url": "https://wisaard.dahp.wa.gov/server/rest/services/County_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "WA_KING": {
        "name": "King County (Seattle), WA",
        "service_url": "https://gisdata.kingcounty.gov/arcgis/rest/services/OpenDataPortal/property__parcel_area/MapServer/439/query",
        "out_fields": "*",
        "batch_size": 4000,
    },
    "WA_SPOKANE": {
        "name": "Spokane County, WA",
        "service_url": "https://gismo.spokanecounty.org/arcgis/rest/services/Assessor/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # OREGON COUNTIES (MORE)
    "OR_MULTNOMAH": {
        "name": "Multnomah County (Portland), OR",
        "service_url": "https://www.portlandmaps.com/arcgis/rest/services/Public/Parcel_Dimensions/MapServer/231/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OR_CLACKAMAS": {
        "name": "Clackamas County, OR",
        "service_url": "https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # FLORIDA COUNTIES (MORE)
    "FL_HILLSBOROUGH": {
        "name": "Hillsborough County (Tampa), FL",
        "service_url": "https://maps.hillsboroughcounty.org/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_ORANGE": {
        "name": "Orange County (Orlando), FL",
        "service_url": "https://maps.ocpafl.org/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_DUVAL": {
        "name": "Duval County (Jacksonville), FL",
        "service_url": "https://maps.coj.net/arcgis/rest/services/Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_BROWARD": {
        "name": "Broward County, FL",
        "service_url": "https://gis.broward.org/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_PINELLAS": {
        "name": "Pinellas County, FL",
        "service_url": "https://egis.pinellascounty.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # DELAWARE (STATEWIDE)
    "DE_STATEWIDE": {
        "name": "Delaware Statewide Parcels (FirstMap 2024)",
        "service_url": "https://enterprise.firstmap.delaware.gov/arcgis/rest/services/PlanningCadastre/DE_StateParcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "DE_NEW_CASTLE": {
        "name": "New Castle County, DE",
        "service_url": "http://firstmap.gis.delaware.gov/arcgis/rest/services/PlanningCadastre/DE_Parcels/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "DE_KENT": {
        "name": "Kent County, DE",
        "service_url": "http://firstmap.gis.delaware.gov/arcgis/rest/services/PlanningCadastre/DE_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "DE_SUSSEX": {
        "name": "Sussex County, DE",
        "service_url": "http://firstmap.gis.delaware.gov/arcgis/rest/services/PlanningCadastre/DE_Parcels/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # PENNSYLVANIA (MORE)
    "PA_ALLEGHENY": {
        "name": "Allegheny County (Pittsburgh), PA",
        "service_url": "https://gisdata.alleghenycounty.us/arcgis/rest/services/EGIS/Web_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "PA_MONTGOMERY": {
        "name": "Montgomery County, PA",
        "service_url": "https://gis.montcopa.org/arcgis/rest/services/Parcels/Montgomery_County_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # HAWAII (STATEWIDE + COUNTIES)
    "HI_STATEWIDE": {
        "name": "Hawaii Statewide TMK Parcels",
        "service_url": "https://geodata.hawaii.gov/arcgis/rest/services/ParcelsZoning/MapServer/25/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "HI_HONOLULU": {
        "name": "Honolulu County (Oahu), HI",
        "service_url": "https://geodata.hawaii.gov/arcgis/rest/services/ParcelsZoning/MapServer/11/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "HI_MAUI": {
        "name": "Maui County, HI",
        "service_url": "https://geodata.hawaii.gov/arcgis/rest/services/ParcelsZoning/MapServer/30/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "HI_HAWAII": {
        "name": "Hawaii County (Big Island), HI",
        "service_url": "https://gis.hawaiicounty.gov/arcgis/rest/services/COHGIS_Public/COHGIS_Public/MapServer/23/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # NEW MEXICO (STATEWIDE + COUNTIES)
    "NM_STATEWIDE": {
        "name": "New Mexico Statewide Parcels 2021",
        "service_url": "https://gis.ose.state.nm.us/arcgis/rest/services/Parcels/County_Parcels_2021/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NM_STATEWIDE_V2": {
        "name": "New Mexico Statewide Parcels 2025",
        "service_url": "https://gis.ose.nm.gov/server_s/rest/services/Parcels/County_Parcels_2025/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NM_DONA_ANA": {
        "name": "Dona Ana County (Las Cruces), NM",
        "service_url": "https://gis.donaanacounty.org/server/rest/services/Parcel/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ARIZONA COUNTIES (MORE)
    "AZ_COCONINO": {
        "name": "Coconino County (Flagstaff), AZ",
        "service_url": "https://webmaps.coconino.az.gov/arcgis/rest/services/ParcelOwnerInfo/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # SOUTH DAKOTA COUNTIES
    "SD_MINNEHAHA": {
        "name": "Minnehaha County (Sioux Falls), SD",
        "service_url": "https://gis.minnehahacounty.org/minnemap/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NORTH DAKOTA (STATEWIDE)
    "ND_STATEWIDE": {
        "name": "North Dakota Statewide Parcels (NDGISHUB)",
        "service_url": "https://services1.arcgis.com/GOcSXpzwBHyk2nog/arcgis/rest/services/NDGISHUB_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "ND_CASS": {
        "name": "Cass County (Fargo), ND",
        "service_url": "https://gis.cityoffargo.com/arcgis/rest/services/Basemap/CassCountyParcelsWGS84/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # RHODE ISLAND (MUNICIPAL)
    "RI_CRANSTON": {
        "name": "Cranston, RI",
        "service_url": "https://gis.cranstonri.org/arcgis/rest/services/RIGISParcels_Cranston/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "RI_EAST_PROVIDENCE": {
        "name": "East Providence, RI",
        "service_url": "https://gis3.cdmsmithgis.com/arcgis/rest/services/EastProvidence/EastProvidence_Operational_2023/MapServer/44/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "RI_PROVIDENCE": {
        "name": "Providence, RI",
        "service_url": "https://webgis.providenceri.gov/server/rest/services/Planning/PVD_Radius_BaseMap/MapServer/22/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "RI_SOUTH_KINGSTOWN": {
        "name": "South Kingstown, RI",
        "service_url": "https://gishost.cdmsmithgis.com/cdmsmithgis/rest/services/SouthKingstown_OperationalMap_Tax_Pub/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # GEORGIA (NEW ENDPOINTS)
    "GA_FULTON_V3": {
        "name": "Fulton County (Atlanta), GA",
        "service_url": "https://gis.fultoncountyga.gov/arcgis/rest/services/MapServices/ParcelsRoads/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_DEKALB_V2": {
        "name": "DeKalb County, GA",
        "service_url": "https://gis.dekalbcountyga.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_CHEROKEE_V2": {
        "name": "Cherokee County, GA",
        "service_url": "https://services6.arcgis.com/dpaY3zboICQILFY5/arcgis/rest/services/Cherokee_County_Parcels_/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_GLYNN_V2": {
        "name": "Glynn County, GA",
        "service_url": "https://webadaptor.glynncounty-ga.gov/webadaptor/rest/services/Parcels/Parcels_Rectified/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # FLORIDA (NEW ENDPOINTS)
    "FL_MIAMI_DADE_V2": {
        "name": "Miami-Dade County, FL",
        "service_url": "https://gis.miamidade.gov/arcgis/rest/services/PropertySearch/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_BROWARD_V2": {
        "name": "Broward County, FL",
        "service_url": "https://gis.broward.org/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_PALM_BEACH_V2": {
        "name": "Palm Beach County, FL",
        "service_url": "https://maps.co.palm-beach.fl.us/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_ORANGE_V2": {
        "name": "Orange County (Orlando), FL",
        "service_url": "https://maps.ocpafl.org/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_HILLSBOROUGH_V2": {
        "name": "Hillsborough County (Tampa), FL",
        "service_url": "https://maps.hillsboroughcounty.org/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_DUVAL_V2": {
        "name": "Duval County (Jacksonville), FL",
        "service_url": "https://maps.coj.net/arcgis/rest/services/Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_PINELLAS_V2": {
        "name": "Pinellas County, FL",
        "service_url": "https://egis.pinellascounty.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # COLORADO (COUNTY-SPECIFIC FROM STATE PORTAL)
    "CO_DENVER_V2": {
        "name": "Denver County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/7/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_BOULDER_V2": {
        "name": "Boulder County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/3/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_ADAMS_V3": {
        "name": "Adams County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_ARAPAHOE_V3": {
        "name": "Arapahoe County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_DOUGLAS_V2": {
        "name": "Douglas County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/8/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_EL_PASO_V3": {
        "name": "El Paso County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/11/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_JEFFERSON_V2": {
        "name": "Jefferson County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/16/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_LARIMER_V2": {
        "name": "Larimer County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/18/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MISSISSIPPI (STATEWIDE 2024)
    "MS_STATEWIDE_2024": {
        "name": "Mississippi Statewide Parcels (April 2024)",
        "service_url": "https://gis.mississippi.edu/server/rest/services/Cadastral/MS_Parcels_Aprl2024/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MS_HARRISON_V2": {
        "name": "Harrison County (Gulfport), MS",
        "service_url": "https://geo.co.harrison.ms.us/server/rest/services/AssetMap/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # OKLAHOMA (NEW ENDPOINTS)
    "OK_OKLAHOMA_V2": {
        "name": "Oklahoma County (OKC), OK",
        "service_url": "https://gisdata.oklahomacounty.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OK_TULSA_V2": {
        "name": "Tulsa County, OK",
        "service_url": "https://gis.tulsacounty.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OK_CLEVELAND": {
        "name": "Cleveland County (Norman), OK",
        "service_url": "https://gis.clevelandcounty.com/arcgis/rest/services/Tax/Tax/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # SOUTH DAKOTA (NEW ENDPOINTS)
    "SD_SIOUX_FALLS_V2": {
        "name": "Sioux Falls City, SD",
        "service_url": "https://gis.siouxfalls.gov/arcgis/rest/services/Data/Property/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ALASKA (NEW ENDPOINTS)
    "AK_MATSU": {
        "name": "Matanuska-Susitna Borough, AK",
        "service_url": "https://services1.arcgis.com/eTj8tUjPZjmU3JEE/arcgis/rest/services/Cadastral_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_KENAI": {
        "name": "Kenai Peninsula Borough, AK",
        "service_url": "http://forestrymaps.alaska.gov/arcgis/rest/services/Alaska_Boroughs/FeatureServer/6/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_NORTH_SLOPE": {
        "name": "North Slope Borough, AK",
        "service_url": "https://arcgis.dnr.alaska.gov/arcgis/rest/services/OpenData/Administrative_BoroughParcels/FeatureServer/8/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_SITKA": {
        "name": "City & Borough of Sitka, AK",
        "service_url": "https://arcgis.dnr.alaska.gov/arcgis/rest/services/OpenData/Administrative_BoroughParcels/FeatureServer/10/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_DENALI": {
        "name": "Denali Borough, AK",
        "service_url": "https://arcgis.dnr.alaska.gov/arcgis/rest/services/OpenData/Administrative_BoroughParcels/FeatureServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # VERMONT (STATEWIDE V2)
    "VT_STATEWIDE_V2": {
        "name": "Vermont Statewide Parcels (VCGI)",
        "service_url": "https://services1.arcgis.com/BkFxaEFNwHqX3tAw/arcgis/rest/services/FS_VCGI_VTPARCELS_WM_NOCACHE_v2/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # WYOMING (STATEWIDE + COUNTIES)
    "WY_STATEWIDE_V2": {
        "name": "Wyoming Private Parcels (Statewide)",
        "service_url": "https://gis.deq.wyo.gov/arcgis/rest/services/WY_PRIVATE_PARCELS/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "WY_LARAMIE_V2": {
        "name": "Laramie County (Cheyenne), WY",
        "service_url": "https://maps.laramiecounty.com/arcgis/rest/services/features/CountyBaseMapFeatures/FeatureServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "WY_LINCOLN": {
        "name": "Lincoln County, WY",
        "service_url": "http://maps.lcwy.org/arcgis/rest/services/PUBLIC/ParcelMap/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # IOWA COUNTIES
    "IA_LINN": {
        "name": "Linn County (Cedar Rapids), IA",
        "service_url": "https://gis.linncountyiowa.gov/ags/rest/services/RealEstate/mapLandRecords/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # KANSAS COUNTIES
    "KS_SHAWNEE": {
        "name": "Shawnee County (Topeka), KS",
        "service_url": "https://gis.sncoapps.us/arcgis2/rest/services/Appraiser/AppraisalDataPro/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NORTH CAROLINA (STATEWIDE + COUNTIES)
    "NC_STATEWIDE": {
        "name": "North Carolina Statewide Parcels (NC OneMap)",
        "service_url": "https://services.nconemap.gov/secure/rest/services/NC1Map_Parcels/FeatureServer/1/query",
        "out_fields": "*",
        "batch_size": 5000,
    },
    "NC_WAKE": {
        "name": "Wake County (Raleigh), NC",
        "service_url": "https://maps.wakegov.com/arcgis/rest/services/Property/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NC_GUILFORD": {
        "name": "Guilford County (Greensboro), NC",
        "service_url": "https://gcgis.guilfordcountync.gov/arcgis/rest/services/GISDV/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NC_FORSYTH": {
        "name": "Forsyth County (Winston-Salem), NC",
        "service_url": "https://maps.co.forsyth.nc.us/arcgis/rest/services/WSFCS/WSFCS_ForsythCounty_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NC_CUMBERLAND": {
        "name": "Cumberland County (Fayetteville), NC",
        "service_url": "https://gis.co.cumberland.nc.us/server/rest/services/Tax/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # INDIANA (STATEWIDE + COUNTIES)
    "IN_STATEWIDE": {
        "name": "Indiana Statewide Parcels Current",
        "service_url": "https://gisdata.in.gov/server/rest/services/Hosted/Parcel_Boundaries_of_Indiana_Current/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "IN_MARION": {
        "name": "Marion County (Indianapolis), IN",
        "service_url": "https://xmaps.indy.gov/arcgis/rest/services/Basemaps/IndyBase_Topographic/MapServer/54/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "IN_HAMILTON": {
        "name": "Hamilton County, IN",
        "service_url": "https://gis1.hamiltoncounty.in.gov/arcgis/rest/services/Parcels_Cached/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MINNESOTA COUNTIES (MORE)
    "MN_DAKOTA": {
        "name": "Dakota County, MN",
        "service_url": "https://gis2.co.dakota.mn.us/arcgis/rest/services/DCGIS_OL_PropertyInformation/MapServer/71/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MN_ANOKA": {
        "name": "Anoka County, MN",
        "service_url": "https://gis.anokacountymn.gov/anoka_gis/rest/services/OpenData_Property/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # COLORADO COUNTIES (MORE - from statewide service)
    "CO_ARAPAHOE": {
        "name": "Arapahoe County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_LARIMER": {
        "name": "Larimer County (Fort Collins), CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/18/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_DENVER": {
        "name": "Denver County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/7/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_ADAMS": {
        "name": "Adams County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_DOUGLAS": {
        "name": "Douglas County, CO",
        "service_url": "https://gis.colorado.gov/public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer/8/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ARIZONA COUNTIES (MORE - from ADWR service)
    "AZ_APACHE": {
        "name": "Apache County, AZ",
        "service_url": "https://azwatermaps.azwater.gov/arcgis/rest/services/General/Parcels_for_TEST/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AZ_NAVAJO": {
        "name": "Navajo County, AZ",
        "service_url": "https://azwatermaps.azwater.gov/arcgis/rest/services/General/Parcels_for_TEST/FeatureServer/5/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # CALIFORNIA COUNTIES (MORE)
    "CA_ALAMEDA": {
        "name": "Alameda County (Oakland), CA",
        "service_url": "http://gis.acgov.org/arcgis/rest/services/AlamedaCounty_Dynamic/ParcelsAPNs/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CA_SONOMA": {
        "name": "Sonoma County, CA",
        "service_url": "https://socogis.sonomacounty.ca.gov/map/rest/services/OWTSPublic/Permit_Sonoma_GIS_Parcel_Base/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "CA_ZONING_STATEWIDE": {
        "name": "California Statewide Zoning (with Parcel Geometries)",
        "service_url": "https://services8.arcgis.com/Xr1lDrwMv89PhjD9/arcgis/rest/services/California_Statewide_Zoning_North/FeatureServer/1/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # WEST VIRGINIA (STATEWIDE)
    "WV_STATEWIDE": {
        "name": "West Virginia Statewide",
        "service_url": "https://services.wvgis.wvu.edu/arcgis/rest/services/Planning_Cadastre/WV_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # CONNECTICUT (STATEWIDE)
    "CT_STATEWIDE": {
        "name": "Connecticut Statewide",
        "service_url": "https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/Connecticut_State_Parcel_Layer_2023/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # VIRGINIA (STATEWIDE + COUNTIES)
    "VA_STATEWIDE": {
        "name": "Virginia Statewide Parcels (VDEM)",
        "service_url": "https://gismaps.vdem.virginia.gov/arcgis/rest/services/VA_Base_Layers/VA_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "VA_VIRGINIA_BEACH": {
        "name": "Virginia Beach, VA",
        "service_url": "https://geo.vbgov.com/mapservices/rest/services/Basemaps/Property_Information/MapServer/12/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "VA_HENRICO": {
        "name": "Henrico County, VA",
        "service_url": "https://portal.henrico.gov/mapping/rest/services/layers/Tax_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "VA_LOUDOUN_V2": {
        "name": "Loudoun County, VA (Alt)",
        "service_url": "https://logis.loudoun.gov/gis/rest/services/COL/LandRecords/MapServer/5/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "VA_PRINCE_WILLIAM_V2": {
        "name": "Prince William County, VA (Alt)",
        "service_url": "https://gisweb.pwcva.gov/arcgis/rest/services/CountyMapper/LandRecords/MapServer/4/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEBRASKA COUNTIES
    "NE_LANCASTER": {
        "name": "Lancaster County (Lincoln), NE",
        "service_url": "https://gisext.lincoln.ne.gov/arcgis/rest/services/Assessor/Pub_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NE_SARPY": {
        "name": "Sarpy County, NE",
        "service_url": "https://geodata.sarpy.gov/arcgis/rest/services/Cadastral/LandRecordsSearch/MapServer/5/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NE_STATEWIDE": {
        "name": "Nebraska Statewide Parcels 2023",
        "service_url": "https://giscat.ne.gov/enterprise/rest/services/TaxParcels2023/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # OKLAHOMA COUNTIES (MORE)
    "OK_TULSA": {
        "name": "Tulsa County, OK",
        "service_url": "https://maps.cityoftulsa.org/hosting/rest/services/DatabaseViews/LandBaseView/FeatureServer/10/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OK_CLEVELAND": {
        "name": "Cleveland County (Norman), OK",
        "service_url": "https://gis.clevelandcounty.com/arcgis/rest/services/Tax/Tax/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # TENNESSEE COUNTIES (MORE)
    "TN_SHELBY": {
        "name": "Shelby County (Memphis), TN",
        "service_url": "https://gis.shelbycountytn.gov/arcgis/rest/services/Parcel/CERT_Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "TN_HAMILTON": {
        "name": "Hamilton County (Chattanooga), TN",
        "service_url": "https://mapsdev.hamiltontn.gov/hcwa03/rest/services/Live_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # KENTUCKY COUNTIES
    "KY_JEFFERSON": {
        "name": "Jefferson County (Louisville), KY",
        "service_url": "https://gis.lojic.org/maps/rest/services/PvaGis/PvaParcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KY_KENTON": {
        "name": "Kenton County, KY",
        "service_url": "https://maps.linkgis.org/server/rest/services/Parcel_QueryOnly/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KY_BOONE": {
        "name": "Boone County, KY",
        "service_url": "https://secure.boonecountygis.com/server/rest/services/ParcelLayers/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MISSOURI COUNTIES (MORE)
    "MO_JACKSON": {
        "name": "Jackson County (Kansas City), MO",
        "service_url": "https://jcgis.jacksongov.org/arcgis/rest/services/Cadastral/LotsAndDimensions/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MO_ST_CHARLES_V2": {
        "name": "St. Charles County, MO (Tax)",
        "service_url": "https://maps.sccmo.org/scc_gis/rest/services/open_data/Tax_Information/FeatureServer/3/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MO_GREENE": {
        "name": "Greene County (Springfield), MO",
        "service_url": "https://greenecountyassessor.org/arcgis/rest/services/ParcelPublicAccess1JAN212025/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # KANSAS COUNTIES (MORE)
    "KS_DOUGLAS": {
        "name": "Douglas County (Lawrence), KS",
        "service_url": "https://gis2.lawrenceks.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KS_WYANDOTTE": {
        "name": "Wyandotte County (Kansas City), KS",
        "service_url": "https://gisweb.wycokck.org/arcgis/rest/services/GISPUB/UGMAPS_4_V02/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEW JERSEY (STATEWIDE - VERIFIED)
    "NJ_STATEWIDE_V2": {
        "name": "New Jersey Statewide (Composite)",
        "service_url": "https://services2.arcgis.com/XVOqAjTOJ5P6ngMu/arcgis/rest/services/Parcels_Composite_NJ_WM/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NJ_BERGEN": {
        "name": "Bergen County, NJ",
        "service_url": "https://bchapeweb.co.bergen.nj.us/arcgis/rest/services/Parcel_idtLookup/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NJ_PASSAIC": {
        "name": "Passaic County, NJ",
        "service_url": "https://gis.passaiccountynj.org/arcgis/rest/services/Hosted/Passaic_County_2020_Parcel/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MAINE (STATEWIDE)
    "ME_STATEWIDE": {
        "name": "Maine Statewide",
        "service_url": "https://gis.mcht.org/arcgis/rest/services/Cadastral_Planning/MCHT_Combined_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEW HAMPSHIRE (STATEWIDE)
    "NH_STATEWIDE": {
        "name": "New Hampshire Statewide",
        "service_url": "https://nhgeodata.unh.edu/nhgeodata/rest/services/CAD/ParcelMosaic/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MASSACHUSETTS (STATEWIDE)
    "MA_STATEWIDE": {
        "name": "Massachusetts Statewide",
        "service_url": "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/L3_TAXPAR_POLY_ASSESS_gdb/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # FLORIDA STATEWIDE CADASTRAL
    "FL_STATEWIDE": {
        "name": "Florida Statewide Cadastral",
        "service_url": "https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # TEXAS COUNTIES (MORE)
    "TX_BEXAR": {
        "name": "Bexar County (San Antonio), TX",
        "service_url": "https://maps.bexar.org/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "TX_DENTON": {
        "name": "Denton County, TX",
        "service_url": "https://gis.dentoncounty.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "TX_TRAVIS": {
        "name": "Travis County (Austin), TX",
        "service_url": "https://taxmaps.traviscountytx.gov/arcgis/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "TX_TARRANT": {
        "name": "Tarrant County (Fort Worth), TX",
        "service_url": "https://mapit.tarrantcounty.com/arcgis/rest/services/Dynamic/TADParcelsApp/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "TX_WILLIAMSON_V2": {
        "name": "Williamson County, TX (WCAD)",
        "service_url": "https://gis.wilco.org/arcgis/rest/services/public/county_wcad_parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # SOUTH CAROLINA COUNTIES
    "SC_CHARLESTON": {
        "name": "Charleston County, SC",
        "service_url": "https://gisccapps.charlestoncounty.org/arcgis/rest/services/GIS_VIEWER/Public_Search/MapServer/4/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "SC_GREENVILLE": {
        "name": "Greenville County, SC",
        "service_url": "https://www.gcgis.org/arcgis/rest/services/StormWater/StormWater/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "SC_HORRY": {
        "name": "Horry County (Myrtle Beach), SC",
        "service_url": "https://www.horrycounty.org/parcelapp/rest/services/HorryCountyGISApp/MapServer/24/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "SC_SPARTANBURG": {
        "name": "Spartanburg County, SC",
        "service_url": "https://maps.spartanburgcounty.org/server/rest/services/GIS/CAMA_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # GEORGIA COUNTIES (MORE)
    "GA_CHATHAM": {
        "name": "Chatham County (Savannah), GA",
        "service_url": "https://pub.sagis.org/arcgis/rest/services/OpenData/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_RICHMOND": {
        "name": "Richmond County (Augusta), GA",
        "service_url": "https://services1.arcgis.com/UKYQy2KtG5YhYPTp/arcgis/rest/services/OpenData_Parcels/FeatureServer/4/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_COBB": {
        "name": "Cobb County, GA",
        "service_url": "https://gis.cobbcounty.gov/gisserver/rest/services/cobbpublic/Parcels/MapServer/3/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_GWINNETT_V2": {
        "name": "Gwinnett County, GA (Property)",
        "service_url": "https://services3.arcgis.com/RfpmnkSAQleRbndX/arcgis/rest/services/Property_and_Tax/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # LOUISIANA PARISHES
    "LA_ORLEANS": {
        "name": "Orleans Parish (New Orleans), LA",
        "service_url": "https://gis.nola.gov/arcgis/rest/services/LandBase/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "LA_EAST_BATON_ROUGE": {
        "name": "East Baton Rouge Parish, LA",
        "service_url": "https://maps.brla.gov/gis/rest/services/Cadastral/Tax_Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ALABAMA COUNTIES (MORE)
    "AL_MADISON": {
        "name": "Madison County (Huntsville), AL",
        "service_url": "https://maps.huntsvilleal.gov/server/rest/services/Boundaries/MadisonCountyParcels/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # COLORADO (STATEWIDE)
    "CO_STATEWIDE": {
        "name": "Colorado Statewide",
        "service_url": "https://gis.colorado.gov/public/rest/services/Address_and_Parcel/Colorado_Public_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_EL_PASO_V2": {
        "name": "El Paso County (Colorado Springs), CO",
        "service_url": "https://gispw.coloradosprings.gov/arcgis/rest/services/OMS_Base_Maps/GoGOV_Basemap/MapServer/12/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_ARAPAHOE_V2": {
        "name": "Arapahoe County, CO (Direct)",
        "service_url": "https://gis.arapahoegov.com/arcgis/rest/services/CountyFeatureService/MapServer/14/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_ADAMS_V2": {
        "name": "Adams County, CO (Direct)",
        "service_url": "https://gisapp.adcogov.org/arcgis/rest/services/AdvancedExt/MapServer/70/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # IOWA (STATEWIDE + MORE)
    "IA_STATEWIDE": {
        "name": "Iowa Statewide",
        "service_url": "https://services3.arcgis.com/kd9gaiUExYqUbnoq/ArcGIS/rest/services/Iowa_Parcels_2017/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "IA_POLK": {
        "name": "Polk County (Des Moines), IA",
        "service_url": "https://gisp1.polkcountyiowa.gov/server/rest/services/Public/Polk_County_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "IA_JOHNSON": {
        "name": "Johnson County (Iowa City), IA",
        "service_url": "https://gis.johnsoncountyiowa.gov/arcgis/rest/services/PDS/MapServer/51/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # OHIO COUNTIES (MORE)
    "OH_CUYAHOGA": {
        "name": "Cuyahoga County (Cleveland), OH",
        "service_url": "https://gis.cuyahogacounty.us/server/rest/services/MyPLACE/Parcels_WMA_GJOIN_WGS84/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OH_HAMILTON": {
        "name": "Hamilton County (Cincinnati), OH",
        "service_url": "https://gis.hamilton-oh.gov/arcgis/rest/services/Viewer/WebLayers_HamiltonProperties/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OH_SUMMIT_V2": {
        "name": "Summit County (Akron), OH (Direct)",
        "service_url": "https://scgis.summitoh.net/hosted/rest/services/parcels_web_GEODATA_Tax_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # CALIFORNIA (MORE)
    "CA_LOS_ANGELES_V2": {
        "name": "Los Angeles County, CA (Parcel Cache)",
        "service_url": "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "CA_ORANGE_V2": {
        "name": "Orange County, CA (OCGIS)",
        "service_url": "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CA_SAN_FRANCISCO": {
        "name": "San Francisco County, CA",
        "service_url": "https://sfplanninggis.org/arcgiswa/rest/services/PlanningData/MapServer/23/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "CA_SACRAMENTO_V2": {
        "name": "Sacramento County, CA (All Parcels)",
        "service_url": "https://mapservices.gis.saccounty.net/arcgis/rest/services/PARCELS/MapServer/22/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ILLINOIS (MORE)
    "IL_COOK_V2": {
        "name": "Cook County, IL (Chicago - Viewer)",
        "service_url": "https://gis.cookcountyil.gov/traditional/rest/services/cookVwrDynmc/MapServer/44/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "IL_DUPAGE_V2": {
        "name": "DuPage County, IL (RealEstate)",
        "service_url": "https://gis.dupageco.org/arcgis/rest/services/DuPage_County_IL/ParcelsWithRealEstateCC/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # MICHIGAN (MORE)
    "MI_OAKLAND_V2": {
        "name": "Oakland County, MI (Enterprise)",
        "service_url": "https://gisservices.oakgov.com/arcgis/rest/services/Enterprise/EnterpriseOpenParcelDataMapService/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2500,
    },
    "MI_MACOMB_V2": {
        "name": "Macomb County, MI (Additional)",
        "service_url": "https://gis.macombgov.org/arcgis1/rest/services/Additional_Parcels_2/MapServer/16/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # KENTUCKY (NEW ENDPOINTS)
    "KY_JEFFERSON": {
        "name": "Jefferson County (Louisville), KY",
        "service_url": "https://gis.lojic.org/maps/rest/services/LojicSolutions/OpenDataPVA/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KY_FAYETTE": {
        "name": "Fayette County (Lexington), KY",
        "service_url": "https://services.arcgis.com/lfucg/arcgis/rest/services/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KY_KENTON": {
        "name": "Kenton County, KY",
        "service_url": "https://www.pdskentucky.org/arcgis/rest/services/openData/PropertyParcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KY_BOONE": {
        "name": "Boone County, KY",
        "service_url": "https://www.pdskentucky.org/arcgis/rest/services/openData/PropertyParcels_Boone/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # LOUISIANA (NEW ENDPOINTS)
    "LA_ORLEANS": {
        "name": "Orleans Parish (New Orleans), LA",
        "service_url": "https://gis.nola.gov/arcgis/rest/services/LandBase/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "LA_ST_TAMMANY": {
        "name": "St. Tammany Parish, LA",
        "service_url": "https://atlas.stpgov.org/server/rest/services/STPAO_Parcels/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "LA_EAST_BATON_ROUGE": {
        "name": "East Baton Rouge Parish, LA",
        "service_url": "https://services2.arcgis.com/ux6FH2N0x0Jngtk7/arcgis/rest/services/Tax_Parcel/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # OREGON (NEW ENDPOINTS)
    "OR_MULTNOMAH": {
        "name": "Multnomah County (Portland), OR",
        "service_url": "https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/25/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OR_WASHINGTON": {
        "name": "Washington County, OR",
        "service_url": "https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/33/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OR_CLACKAMAS": {
        "name": "Clackamas County, OR",
        "service_url": "https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OR_LANE": {
        "name": "Lane County (Eugene), OR",
        "service_url": "https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/19/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OR_MARION": {
        "name": "Marion County (Salem), OR",
        "service_url": "https://gis.odf.oregon.gov/ags1/rest/services/WebMercator/TaxlotsDisplay/MapServer/23/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # KANSAS (NEW ENDPOINTS)
    "KS_SEDGWICK": {
        "name": "Sedgwick County (Wichita), KS",
        "service_url": "https://gisportal.sedgwick.gov/arcgis/rest/services/Appraisers/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KS_WYANDOTTE": {
        "name": "Wyandotte County (Kansas City), KS",
        "service_url": "https://maps.wycokck.org/arcgis/rest/services/Maps/Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KS_DOUGLAS": {
        "name": "Douglas County (Lawrence), KS",
        "service_url": "https://services2.arcgis.com/Pg5HZ7bvBNT16Tn4/arcgis/rest/services/Parcels_Export/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # SOUTH DAKOTA - First District Association Counties
    "SD_SIOUX_FALLS_V3": {
        "name": "Sioux Falls / Lincoln County, SD",
        "service_url": "https://gis.siouxfalls.gov/arcgis/rest/services/Data/Property/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "SD_PENNINGTON": {
        "name": "Pennington County (Rapid City), SD",
        "service_url": "https://gis.rcgov.org/server/rest/services/OpenData/TaxParcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "SD_CODINGTON": {
        "name": "Codington County (Watertown), SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Codington/codingtonparcels/MapServer/10/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SD_BEADLE": {
        "name": "Beadle County (Huron), SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Beadle/beadlemapnet/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SD_ROBERTS": {
        "name": "Roberts County, SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Roberts/robertsmapnet/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SD_EDMUNDS": {
        "name": "Edmunds County, SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Edmunds/edmundsmapnet/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SD_HAND": {
        "name": "Hand County, SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Hand/handmapnet/MapServer/7/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SD_KINGSBURY": {
        "name": "Kingsbury County, SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Kingsbury/kingsburymapnet/MapServer/6/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SD_GRANT": {
        "name": "Grant County, SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Grant/grantmapnet/MapServer/17/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SD_HAMLIN": {
        "name": "Hamlin County, SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Hamlin/hamlinmapnet/MapServer/10/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SD_CLARK": {
        "name": "Clark County, SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Clark/clarkmapnet/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SD_DEUEL": {
        "name": "Deuel County, SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Deuel/deuelmapnet/MapServer/4/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SD_MOODY": {
        "name": "Moody County, SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Moody/moodymapnet/MapServer/7/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "SD_MINER": {
        "name": "Miner County, SD",
        "service_url": "https://www.1stdistrict.org/arcgis/rest/services/Miner/minermapnet/MapServer/3/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # ALASKA - DNR Borough Parcels
    "AK_JUNEAU": {
        "name": "City & Borough of Juneau, AK",
        "service_url": "https://arcgis.dnr.alaska.gov/arcgis/rest/services/OpenData/Administrative_BoroughParcels/FeatureServer/3/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_FAIRBANKS": {
        "name": "Fairbanks North Star Borough, AK",
        "service_url": "https://arcgis.dnr.alaska.gov/arcgis/rest/services/OpenData/Administrative_BoroughParcels/FeatureServer/9/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_SKAGWAY": {
        "name": "Municipality of Skagway, AK",
        "service_url": "https://arcgis.dnr.alaska.gov/arcgis/rest/services/OpenData/Administrative_BoroughParcels/FeatureServer/11/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_MATSU": {
        "name": "Matanuska-Susitna Borough, AK",
        "service_url": "https://maps.matsugov.us/map/rest/services/OpenData/Cadastral_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 5000,
    },
    "AK_FNSB_DIRECT": {
        "name": "Fairbanks NSB Direct Parcels, AK",
        "service_url": "https://gisportal.fnsb.gov/referenced/rest/services/_/Parcels/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_DNR_DISPOSALS": {
        "name": "Alaska DNR Land Disposals",
        "service_url": "https://arcgis.dnr.alaska.gov/arcgis/rest/services/OpenData/Ownership_LandDisposal_All/FeatureServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_BLM_NATIVE": {
        "name": "BLM Alaska Native Allotment",
        "service_url": "https://gis.blm.gov/akarcgis/rest/services/Land_Status/BLM_AK_Land_Status_Conveyed_Lands/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_BLM_ANCSA": {
        "name": "BLM Alaska ANCSA Conveyed Land",
        "service_url": "https://gis.blm.gov/akarcgis/rest/services/Land_Status/BLM_AK_Land_Status_Conveyed_Lands/FeatureServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_BLM_STATE": {
        "name": "BLM Alaska State Conveyed Land",
        "service_url": "https://gis.blm.gov/akarcgis/rest/services/Land_Status/BLM_AK_Land_Status_Conveyed_Lands/FeatureServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AK_BLM_PRIVATE": {
        "name": "BLM Alaska Private Conveyed Land",
        "service_url": "https://gis.blm.gov/akarcgis/rest/services/Land_Status/BLM_AK_Land_Status_Conveyed_Lands/FeatureServer/4/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEBRASKA - Statewide
    "NE_STATEWIDE": {
        "name": "Nebraska Statewide Parcels",
        "service_url": "https://giscat.ne.gov/enterprise/rest/services/StatewideParcelsExternal/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NE_LANCASTER": {
        "name": "Lancaster County (Lincoln), NE",
        "service_url": "https://gis.lincoln.ne.gov/public/rest/services/Assessor/TaxParcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NE_HALL": {
        "name": "Hall County (Grand Island), NE",
        "service_url": "https://gis.grand-island.com/arcgis/rest/services/County/ParcelOwners/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # WYOMING - Additional Counties
    "WY_CAMPBELL": {
        "name": "Campbell County (Gillette), WY",
        "service_url": "https://gisportal.gillettewy.gov/arcgisserver/rest/services/BOCountyTaxParcelMS/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "WY_TETON": {
        "name": "Teton County (Jackson Hole), WY",
        "service_url": "https://gis.tetoncountywy.gov/server/rest/services/Public_Services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 5000,
    },
    "WY_PARK": {
        "name": "Park County (Cody), WY",
        "service_url": "https://maps.parkco.us/arcgis/rest/services/Parcels/ParkParcelPublic/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "WY_SHERIDAN": {
        "name": "Sheridan County, WY",
        "service_url": "https://gismaps.sheridanwy.net/arcgis/rest/services/UtilityViewer/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "WY_FREMONT": {
        "name": "Fremont County (Lander/Riverton), WY",
        "service_url": "https://fremontgis.com/server/rest/services/AUT_LAND_RECORDS/MapServer/1069/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # OKLAHOMA - INCOG Regional Counties
    "OK_TULSA": {
        "name": "Tulsa County, OK (INCOG)",
        "service_url": "https://map11.incog.org/arcgis11wa/rest/services/Parcels_TulsaCo/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OK_CREEK": {
        "name": "Creek County, OK (INCOG)",
        "service_url": "https://map11.incog.org/arcgis11wa/rest/services/Parcels_CreekCo/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OK_OSAGE": {
        "name": "Osage County, OK (INCOG)",
        "service_url": "https://map11.incog.org/arcgis11wa/rest/services/Parcels_OsageCo/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OK_ROGERS": {
        "name": "Rogers County, OK (INCOG)",
        "service_url": "https://map11.incog.org/arcgis11wa/rest/services/Parcels_RogersCo/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OK_WAGONER": {
        "name": "Wagoner County, OK (INCOG)",
        "service_url": "https://map11.incog.org/arcgis11wa/rest/services/Parcels_WagonerCo/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OK_NORMAN": {
        "name": "Norman (Cleveland County), OK",
        "service_url": "https://maps.normanok.gov/arcgis/rest/services/GeneralBaseMap2020/MapServer/28/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OK_EDMOND": {
        "name": "Edmond (Oklahoma County), OK",
        "service_url": "https://gis.edmondok.gov/arcgis/rest/services/EdmondOKPLL/EdmondOKPLL/MapServer/22/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OK_BROKEN_ARROW": {
        "name": "Broken Arrow (Tulsa County), OK",
        "service_url": "https://gis.brokenarrowok.gov/server/rest/services/Tyler/EnerGov/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEW HAMPSHIRE - Statewide GRANIT
    "NH_STATEWIDE": {
        "name": "NH GRANIT Statewide Parcel Mosaic",
        "service_url": "https://nhgeodata.unh.edu/nhgeodata/rest/services/CAD/ParcelMosaic/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NH_MANCHESTER": {
        "name": "Manchester, NH Parcels",
        "service_url": "https://ags.manchesternh.gov/agsgis7/rest/services/Community/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NH_NASHUA": {
        "name": "Nashua, NH Parcels",
        "service_url": "https://newgis.nashuanh.gov/arcgisapp3/rest/services/HTML_Viewer/NashuaNH_OperationalLayers_2022/MapServer/7/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NH_KEENE": {
        "name": "Keene, NH Tax Parcels",
        "service_url": "https://cartegraph.ci.keene.nh.us/gis/rest/services/TAX_PARCELS_INFO/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MAINE - Statewide
    "ME_STATEWIDE": {
        "name": "Maine Statewide Parcels Merged",
        "service_url": "https://services1.arcgis.com/RbMX0mRVOFNTdLzd/arcgis/rest/services/Maine_Parcels_Merged/FeatureServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "ME_MCHT_COMBINED": {
        "name": "MCHT Combined Parcels, ME",
        "service_url": "https://gis.mcht.org/arcgis/rest/services/Cadastral_Planning/MCHT_Combined_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "ME_PORTLAND": {
        "name": "Portland, ME Parcels",
        "service_url": "https://gis.portlandmaine.gov/maps/rest/services/ParcelsWGS84/FeatureServer/8/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "ME_LEWISTON": {
        "name": "Lewiston, ME Parcels",
        "service_url": "https://maps2.lewistonmaine.gov/arcgis/rest/services/Public/LewParcels_public_recs/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # WEST VIRGINIA - Statewide
    "WV_STATEWIDE_V2": {
        "name": "WV Statewide Parcels (WVGIS Tech Center)",
        "service_url": "https://services.wvgis.wvu.edu/arcgis/rest/services/Planning_Cadastre/WV_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "WV_KANAWHA": {
        "name": "Kanawha County (Charleston), WV",
        "service_url": "https://kanawhacountyassessorgis.com/server/rest/services/Parcel_Lines/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # IDAHO - Statewide
    "ID_STATEWIDE": {
        "name": "Idaho IDWR Statewide Parcels",
        "service_url": "https://gis.idwr.idaho.gov/hosting/rest/services/Reference/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "ID_WHITESTAR": {
        "name": "Idaho IDL WhiteStar Statewide Parcels",
        "service_url": "https://gis1.idl.idaho.gov/arcgis/rest/services/Portal/WhiteStar_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "ID_CANYON": {
        "name": "Canyon County, ID",
        "service_url": "https://maps.canyonco.org/arcgisserver/rest/services/Assessor/CCPublicTaxparcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # MONTANA - Statewide
    "MT_STATEWIDE": {
        "name": "Montana MSDI Framework Parcels",
        "service_url": "https://gisservicemt.gov/arcgis/rest/services/MSDI_Framework/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MT_YELLOWSTONE": {
        "name": "Yellowstone County (Billings), MT",
        "service_url": "https://gis.yellowstonecountymt.gov/arcgis/rest/services/Yellowstone/MapServer/29/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MT_GALLATIN": {
        "name": "Gallatin County (Bozeman), MT",
        "service_url": "https://gis.gallatin.mt.gov/arcgis/rest/services/MapServices/Planning/MapServer/7/query",
        "out_fields": "*",
        "batch_size": 5000,
    },
    "MT_FLATHEAD": {
        "name": "Flathead County (Kalispell), MT",
        "service_url": "https://maps.flatheadcounty.gov/server/rest/services/IMA/Property/MapServer/54/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEVADA - Statewide
    "NV_STATEWIDE": {
        "name": "Nevada Statewide Parcels (Water Resources)",
        "service_url": "https://arcgis.water.nv.gov/arcgis/rest/services/BaseLayers/County_Parcels_in_Nevada/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NV_CLARK": {
        "name": "Clark County (Las Vegas), NV",
        "service_url": "https://maps.clarkcountynv.gov/arcgis/rest/services/GISMO/AssessorMap/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NV_WASHOE": {
        "name": "Washoe County (Reno), NV",
        "service_url": "https://wcgisweb.washoecounty.us/arcgis/rest/services/OpenData/OpenData/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # HAWAII - Statewide
    "HI_STATEWIDE": {
        "name": "Hawaii Statewide TMK Parcels",
        "service_url": "https://geodata.hawaii.gov/arcgis/rest/services/ParcelsZoning/MapServer/25/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "HI_HAWAII_COUNTY": {
        "name": "Hawaii County (Big Island) Parcels",
        "service_url": "https://geodata.hawaii.gov/arcgis/rest/services/ParcelsZoning/MapServer/5/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "HI_HONOLULU": {
        "name": "Honolulu County (Oahu) Parcels",
        "service_url": "https://geodata.hawaii.gov/arcgis/rest/services/ParcelsZoning/MapServer/11/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "HI_MAUI": {
        "name": "Maui County Parcels",
        "service_url": "https://geodata.hawaii.gov/arcgis/rest/services/ParcelsZoning/MapServer/30/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "HI_KAUAI": {
        "name": "Kauai County Parcels",
        "service_url": "https://geodata.hawaii.gov/arcgis/rest/services/ParcelsZoning/MapServer/9/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # IOWA - Statewide
    "IA_STATEWIDE": {
        "name": "Iowa Statewide Parcels 2017",
        "service_url": "https://services3.arcgis.com/kd9gaiUExYqUbnoq/ArcGIS/rest/services/Iowa_Parcels_2017/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "IA_POLK": {
        "name": "Polk County (Des Moines), IA",
        "service_url": "https://maps.dsm.city/p2/rest/services/External/EXTDynamicShowMeMyHouse/MapServer/18/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "IA_SCOTT": {
        "name": "Scott County (Davenport), IA",
        "service_url": "https://services.arcgis.com/ovln19YRWV44nBqV/ArcGIS/rest/services/Cadastral/FeatureServer/3/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "IA_JOHNSON": {
        "name": "Johnson County (Iowa City), IA",
        "service_url": "https://gis.johnsoncountyiowa.gov/arcgis/rest/services/Parcels_WFS/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "IA_STORY": {
        "name": "Story County (Ames), IA",
        "service_url": "https://apps.storycounty.com/arcgis/rest/services/parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEW MEXICO - Counties
    "NM_BERNALILLO": {
        "name": "Bernalillo County (Albuquerque), NM",
        "service_url": "https://assessormap.bernco.gov/server/rest/services/GIS/ASROnline_Public_Map/MapServer/22/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NM_SANTA_FE": {
        "name": "Santa Fe County, NM",
        "service_url": "https://sfcomaps.santafecountynm.gov/restsvc/rest/services/TaxParcelsDB/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NM_DONA_ANA": {
        "name": "Dona Ana County (Las Cruces), NM",
        "service_url": "https://gis.donaana.gov/server/rest/services/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NM_SANDOVAL": {
        "name": "Sandoval County, NM",
        "service_url": "https://services2.arcgis.com/KQGAxSQd2SGmmuxN/arcgis/rest/services/City_of_Rio_Rancho_Parcels/FeatureServer/18/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NM_VALENCIA": {
        "name": "Valencia County, NM",
        "service_url": "https://arcgisce2.co.valencia.nm.us/arcgis/rest/services/GIS_OnlineMap/MapServer/14/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # COLORADO - Statewide + Counties
    "CO_STATEWIDE": {
        "name": "Colorado Public Parcels Statewide",
        "service_url": "https://gis.colorado.gov/public/rest/services/Address_and_Parcel/Colorado_Public_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_ARAPAHOE": {
        "name": "Arapahoe County, CO",
        "service_url": "https://gis.arapahoegov.com/arcgis/rest/services/OpenDataService/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "CO_BOULDER": {
        "name": "Boulder County, CO",
        "service_url": "https://maps.bouldercounty.org/arcgis/rest/services/PARCELS/PARCELS_OWNER/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 5000,
    },
    "CO_DOUGLAS": {
        "name": "Douglas County, CO",
        "service_url": "https://apps.douglas.co.us/gisod/rest/services/Parcels/FeatureServer/4/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CO_EL_PASO": {
        "name": "El Paso County (Colorado Springs), CO",
        "service_url": "https://gis.coloradosprings.gov/arcgis/rest/services/GeneralUse/LandRecords/MapServer/4/query",
        "out_fields": "*",
        "batch_size": 500,
    },
    "CO_LARIMER": {
        "name": "Larimer County, CO",
        "service_url": "https://maps1.larimer.org/arcgis/rest/services/MapServices/Parcels/MapServer/3/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # ALABAMA - Counties
    "AL_JEFFERSON": {
        "name": "Jefferson County (Birmingham), AL",
        "service_url": "https://gis.jccal.org/arcgis/rest/services/Basemap/JeffersonCountyParcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "AL_BALDWIN": {
        "name": "Baldwin County, AL",
        "service_url": "https://al05baldrevenue.kcsgis.com/kcsgis/rest/services/Baldwin/Public/MapServer/54/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AL_MADISON": {
        "name": "Madison County (Huntsville), AL",
        "service_url": "https://web3.kcsgis.com/kcsgis/rest/services/Madison/AL47_GAMAWeb/MapServer/141/query",
        "out_fields": "*",
        "batch_size": 50000,
    },
    "AL_MONTGOMERY": {
        "name": "Montgomery County, AL",
        "service_url": "https://web3.kcsgis.com/kcsgis/rest/services/Montgomery/AL03_GAMAWeb/MapServer/29/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # MISSISSIPPI - Counties
    "MS_HARRISON": {
        "name": "Harrison County (Gulfport), MS",
        "service_url": "https://geo.co.harrison.ms.us/server/rest/services/AssetMap/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MS_DESOTO": {
        "name": "DeSoto County, MS",
        "service_url": "https://services6.arcgis.com/4Zxj9BGpFPVGgwpo/arcgis/rest/services/Parcels_2025/FeatureServer/11/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MS_HINDS": {
        "name": "Hinds County (Jackson), MS",
        "service_url": "https://gis.cmpdd.org/server/rest/services/Hosted/Hinds_County_Map/FeatureServer/24/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MS_RANKIN": {
        "name": "Rankin County, MS",
        "service_url": "https://gis.cmpdd.org/server/rest/services/Hosted/Rankin_County_Feature_Layer/FeatureServer/8/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MS_MADISON": {
        "name": "Madison County, MS",
        "service_url": "https://gis.cmpdd.org/server/rest/services/Hosted/Madison_County_Map/FeatureServer/36/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # LOUISIANA - Parishes
    "LA_ORLEANS_V2": {
        "name": "Orleans Parish (New Orleans), LA",
        "service_url": "https://gis.nola.gov/arcgis/rest/services/LandBase/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "LA_JEFFERSON_V3": {
        "name": "Jefferson Parish, LA",
        "service_url": "https://eweb.jeffparish.net/arcgis/rest/services/SCP/MPN/MapServer/3/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "LA_EBR": {
        "name": "East Baton Rouge Parish, LA",
        "service_url": "https://maps.brla.gov/gis/rest/services/Cadastral/Tax_Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "LA_CALCASIEU": {
        "name": "Calcasieu Parish (Lake Charles), LA",
        "service_url": "https://lak-dc-arcgis.cppj.net/arcgis/rest/services/TA/Tax_Assessment_Editor/MapServer/17/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # WISCONSIN - Statewide + Counties
    "WI_STATEWIDE_V2": {
        "name": "Wisconsin Statewide Parcels",
        "service_url": "https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "WI_MILWAUKEE_V2": {
        "name": "Milwaukee County, WI",
        "service_url": "https://lio.milwaukeecountywi.gov/arcgis/rest/services/PropertyInfo/Parcels_EagleView/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "WI_DANE": {
        "name": "Dane County (Madison), WI",
        "service_url": "https://maps.cityofmadison.com/arcgis/rest/services/Planning/GFLU_current/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "WI_WAUKESHA_V2": {
        "name": "Waukesha County, WI",
        "service_url": "https://gis.waukeshacounty.gov/host/rest/services/Parcel_Basemap/MapServer/10/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "WI_BROWN": {
        "name": "Brown County (Green Bay), WI",
        "service_url": "https://gis.browncountywi.gov/arcgis/rest/services/ParcelPolygons/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 8000,
    },
    "WI_RACINE_V2": {
        "name": "Racine County, WI",
        "service_url": "https://arcgis.racinecounty.com/arcgis/rest/services/Mapbook/Mapbook/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "WI_KENOSHA": {
        "name": "Kenosha County, WI",
        "service_url": "https://mapping.kenoshacountywi.gov/server/rest/services/SpecialAppData/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # TENNESSEE - Counties
    "TN_SHELBY": {
        "name": "Shelby County (Memphis), TN",
        "service_url": "https://gis.shelbycountytn.gov/arcgis/rest/services/Parcel/CERT_Parcel/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "TN_HAMILTON": {
        "name": "Hamilton County (Chattanooga), TN",
        "service_url": "https://mapsdev.hamiltontn.gov/hcwa03/rest/services/Live_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "TN_WILLIAMSON": {
        "name": "Williamson County, TN",
        "service_url": "http://arcgis2.williamson-tn.org/arcgis/rest/services/IDT/DataPull/MapServer/4/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # MISSOURI - Counties
    "MO_STL_CITY": {
        "name": "St. Louis City, MO",
        "service_url": "https://maps6.stlouis-mo.gov/arcgis/rest/services/St_Louis_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MO_STL_COUNTY": {
        "name": "St. Louis County, MO",
        "service_url": "https://services2.arcgis.com/w657bnjzrjguNyOy/ArcGIS/rest/services/Pardata_JurisFeb2024/FeatureServer/5/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MO_JACKSON": {
        "name": "Jackson County (Kansas City), MO",
        "service_url": "https://jcgis.jacksongov.org/arcgis/rest/services/ParcelViewer/ParcelsAscendRelate/FeatureServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "MO_ST_CHARLES": {
        "name": "St. Charles County, MO",
        "service_url": "https://gis.sccmo.org/scc_gis/rest/services/open_data/Tax_Information/FeatureServer/3/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "MO_GREENE": {
        "name": "Greene County (Springfield), MO",
        "service_url": "https://greenecountyassessor.org/arcgis/rest/services/AllParcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # KENTUCKY - Counties
    "KY_FAYETTE_V2": {
        "name": "Fayette County (Lexington), KY",
        "service_url": "https://services1.arcgis.com/Mg7DLdfYcSWIaDnu/ArcGIS/rest/services/Parcel/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KY_WARREN": {
        "name": "Warren County (Bowling Green), KY",
        "service_url": "https://webgis.bgky.org/server/rest/services/CCPC/CCPC_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KY_BOONE_V2": {
        "name": "Boone County, KY",
        "service_url": "https://secure.boonecountygis.com/server/rest/services/ParcelLayers/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "KY_CAMPBELL": {
        "name": "Campbell County, KY",
        "service_url": "https://maps.linkgis.org/server/rest/services/Parcel_QueryOnly/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # PENNSYLVANIA - Counties
    "PA_PHILADELPHIA": {
        "name": "Philadelphia County, PA",
        "service_url": "https://services.arcgis.com/fLeGjb7u4uXqeF9q/ArcGIS/rest/services/DOR_Parcel/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "PA_ALLEGHENY": {
        "name": "Allegheny County (Pittsburgh), PA",
        "service_url": "https://services1.arcgis.com/vdNDkVykv9vEWFX4/arcgis/rest/services/AlCoParcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "PA_MONTGOMERY": {
        "name": "Montgomery County, PA",
        "service_url": "https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/ArcGIS/rest/services/Montgomery_County_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "PA_BUCKS": {
        "name": "Bucks County, PA",
        "service_url": "https://services3.arcgis.com/SP47Tddf7RK32lBU/arcgis/rest/services/Bucks_County_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "PA_CHESTER": {
        "name": "Chester County, PA",
        "service_url": "https://services.arcgis.com/G4S1dGvn7PIgYd6Y/arcgis/rest/services/Parcels_owners/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "PA_LANCASTER": {
        "name": "Lancaster County, PA",
        "service_url": "https://arcgis.lancastercountypa.gov/arcgis/rest/services/parcel_poly/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # CONNECTICUT - Statewide
    "CT_STATEWIDE_V2": {
        "name": "Connecticut CAMA Statewide Parcels",
        "service_url": "https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/Connecticut_CAMA_and_Parcel_Layer/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "CT_BRIDGEPORT": {
        "name": "Bridgeport, CT",
        "service_url": "https://maps.ctmetro.org/server/rest/services/Bridgeport/Bridgeport_Parcels_NAD83/MapServer/7/query",
        "out_fields": "*",
        "batch_size": 5000,
    },
    "CT_HARTFORD": {
        "name": "Hartford, CT",
        "service_url": "https://gis.hartford.gov/arcgis/rest/services/AccelaMobile/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # UTAH - Counties
    "UT_SALT_LAKE": {
        "name": "Salt Lake County, UT",
        "service_url": "https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/Parcels_SaltLake/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "UT_UTAH": {
        "name": "Utah County (Provo), UT",
        "service_url": "https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/Parcels_Utah/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "UT_DAVIS": {
        "name": "Davis County, UT",
        "service_url": "https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/Parcels_Davis/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "UT_WEBER": {
        "name": "Weber County (Ogden), UT",
        "service_url": "https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/Parcels_Weber/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "UT_WASHINGTON": {
        "name": "Washington County (St. George), UT",
        "service_url": "https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/Parcels_Washington/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "UT_CACHE": {
        "name": "Cache County, UT",
        "service_url": "https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/Parcels_Cache/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # ARIZONA - Counties (ADWR)
    "AZ_MARICOPA": {
        "name": "Maricopa County (Phoenix), AZ",
        "service_url": "https://azwatermaps.azwater.gov/arcgis/rest/services/General/Parcels/MapServer/7/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AZ_PINAL_V2": {
        "name": "Pinal County, AZ",
        "service_url": "https://azwatermaps.azwater.gov/arcgis/rest/services/General/Parcels/MapServer/11/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AZ_YAVAPAI": {
        "name": "Yavapai County, AZ",
        "service_url": "https://gis.yavapaiaz.gov/arcgis/rest/services/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AZ_MOHAVE": {
        "name": "Mohave County, AZ",
        "service_url": "https://mcgis.mohave.gov/arcgis/rest/services/Mohave/MapServer/38/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "AZ_YUMA": {
        "name": "Yuma County, AZ",
        "service_url": "https://arcgis.yumacountyaz.gov/webgis/rest/services/YC_Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # OREGON - Counties (ODF)
    "OR_MULTNOMAH_V2": {
        "name": "Multnomah County (Portland), OR",
        "service_url": "https://www3.multco.us/gisagspublic/rest/services/DART/Taxlots_WebMerc/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OR_LANE_V2": {
        "name": "Lane County (Eugene), OR",
        "service_url": "https://lcmaps.lanecounty.org/arcgis/rest/services/AT/AddressParcelSales/MapServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "OR_MARION_V2": {
        "name": "Marion County (Salem), OR",
        "service_url": "https://gis.co.marion.or.us/arcgis/rest/services/Public/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OR_DESCHUTES": {
        "name": "Deschutes County (Bend), OR",
        "service_url": "https://maps.deschutes.org/arcgis/rest/services/Dial2_Taxlots/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # NORTH CAROLINA - Counties
    "NC_MECKLENBURG": {
        "name": "Mecklenburg County (Charlotte), NC",
        "service_url": "https://gis.charlottenc.gov/arcgis/rest/services/CountyData/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 3000,
    },
    "NC_DURHAM": {
        "name": "Durham County, NC",
        "service_url": "https://webgis2.durhamnc.gov/server/rest/services/ProjectServices/Parcel_Reference_ID_Lookup/FeatureServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NC_BUNCOMBE": {
        "name": "Buncombe County (Asheville), NC",
        "service_url": "https://gis.ashevillenc.gov/server/rest/services/Property/BuncombeCountyProperty/FeatureServer/31/query",
        "out_fields": "*",
        "batch_size": 150000,
    },
    "NC_NEW_HANOVER": {
        "name": "New Hanover County (Wilmington), NC",
        "service_url": "https://gis.nhcgov.com/server/rest/services/Layers/Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 10000,
    },
    "NC_PITT": {
        "name": "Pitt County (Greenville), NC",
        "service_url": "https://gis.pittcountync.gov/gis/rest/services/OPIS/OperationalLayers/MapServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # GEORGIA - Counties
    "GA_GWINNETT": {
        "name": "Gwinnett County, GA",
        "service_url": "https://services3.arcgis.com/RfpmnkSAQleRbndX/arcgis/rest/services/Property_and_Tax/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_DEKALB": {
        "name": "DeKalb County, GA",
        "service_url": "https://dcgis.dekalbcountyga.gov/hosted/rest/services/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_CHATHAM": {
        "name": "Chatham County (Savannah), GA",
        "service_url": "https://pub.sagis.org/arcgis/rest/services/OpenData/Parcels/MapServer/25/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_RICHMOND": {
        "name": "Richmond County (Augusta), GA",
        "service_url": "https://gismap.augustaga.gov/arcgis/rest/services/Map_LayersTS/MapServer/316/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "GA_MUSCOGEE": {
        "name": "Muscogee County (Columbus), GA",
        "service_url": "https://gis.columbus.gov/arcgis/rest/services/Applications/CSIR_Public/MapServer/3/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # FLORIDA - Counties (FL Health)
    "FL_MIAMI_DADE": {
        "name": "Miami-Dade County, FL",
        "service_url": "https://gis.floridahealth.gov/server/rest/services/EHWATER/Parcels/FeatureServer/42/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_BROWARD": {
        "name": "Broward County, FL",
        "service_url": "https://gis.floridahealth.gov/server/rest/services/EHWATER/Parcels/FeatureServer/5/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_PALM_BEACH": {
        "name": "Palm Beach County, FL",
        "service_url": "https://maps.co.palm-beach.fl.us/arcgis/rest/services/Parcels/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "FL_HILLSBOROUGH": {
        "name": "Hillsborough County (Tampa), FL",
        "service_url": "https://arcgis.tampagov.net/arcgis/rest/services/Parcels/TaxParcel/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 6000,
    },
    "FL_ORANGE": {
        "name": "Orange County (Orlando), FL",
        "service_url": "https://ocgis4.ocfl.net/arcgis/rest/services/Public_Dynamic/MapServer/216/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "FL_DUVAL": {
        "name": "Duval County (Jacksonville), FL",
        "service_url": "https://maps.coj.net/coj/rest/services/CityBiz/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "FL_PINELLAS": {
        "name": "Pinellas County, FL",
        "service_url": "https://egis.pinellas.gov/pcpagis/rest/services/PcpaBaseMap/BaseMapParcelAerialsLastYear/MapServer/135/query",
        "out_fields": "*",
        "batch_size": 15000,
    },

    # OHIO - Counties
    "OH_STARK": {
        "name": "Stark County (Canton), OH",
        "service_url": "https://scgisa.starkcountyohio.gov/arcgis/rest/services/Auditor/StarkCountyParcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 4000,
    },
    "OH_MONTGOMERY": {
        "name": "Montgomery County (Dayton), OH",
        "service_url": "https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/ArcGIS/rest/services/Montgomery_County_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OH_SUMMIT": {
        "name": "Summit County (Akron), OH",
        "service_url": "https://maps.summitcounty.org/arcgis/rest/services/Maps/OnlineMap/MapServer/4/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OH_CUYAHOGA": {
        "name": "Cuyahoga County (Cleveland), OH",
        "service_url": "https://gis.cuyahogacounty.us/server/rest/services/CUYAHOGA_BASE_TILED/Real_Property_Features_WGS84/MapServer/25/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OH_LUCAS": {
        "name": "Lucas County (Toledo), OH",
        "service_url": "https://lcaudgis.co.lucas.oh.us/gisaudserver/rest/services/Tyler/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "OH_HAMILTON": {
        "name": "Hamilton County (Cincinnati), OH",
        "service_url": "https://cagisonline.hamilton-co.org/arcgis/rest/services/COUNTYWIDE/Cadastral/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },

    # MICHIGAN - Counties
    "MI_KENT": {
        "name": "Kent County (Grand Rapids), MI",
        "service_url": "https://gis.kentcountymi.gov/agisprod/rest/services/ParcelsWithCondos/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "MI_DETROIT": {
        "name": "Detroit City (Wayne County), MI",
        "service_url": "https://services2.arcgis.com/HsXtOCMp1Nis1Ogr/ArcGIS/rest/services/DetParcels2021_wOwnerInfo_20230801/FeatureServer/2/query",
        "out_fields": "*",
        "batch_size": 2000,
    },

    # NEW YORK - Counties
    "NY_NASSAU": {
        "name": "Nassau County, NY",
        "service_url": "https://services6.arcgis.com/dptt3Slw4IV02m0l/ArcGIS/rest/services/Nassau_County_Parcels_v2/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NY_WESTCHESTER": {
        "name": "Westchester County, NY",
        "service_url": "https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/arcgis/rest/services/Westchester_County_Parcels/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NY_ERIE": {
        "name": "Erie County (Buffalo), NY",
        "service_url": "https://gis.erie.gov/server/rest/services/OGIS/Parcels/MapServer/0/query",
        "out_fields": "*",
        "batch_size": 1000,
    },
    "NY_MONROE": {
        "name": "Monroe County (Rochester), NY",
        "service_url": "https://maps.monroecounty.gov/server/rest/services/Hosted/Parcels_Public/FeatureServer/0/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
    "NY_STATEWIDE": {
        "name": "New York State Tax Parcels",
        "service_url": "https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/ArcGIS/rest/services/NYS_Tax_Parcels_Public/FeatureServer/1/query",
        "out_fields": "*",
        "batch_size": 2000,
    },
}


def fetch_parcels(config):
    """Fetch all parcels from a county API."""
    service_url = config['service_url']
    out_fields = config.get('out_fields', '*')
    batch_size = config.get('batch_size', 2000)

    all_features = []
    offset = 0

    print(f"Fetching parcels from {config['name']}...")

    while True:
        params = {
            'where': '1=1',
            'outFields': out_fields,
            'returnGeometry': 'true',
            'resultOffset': str(offset),
            'resultRecordCount': str(batch_size),
            'f': 'json'
        }

        url = f"{service_url}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')

            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.load(resp)

            features = data.get('features', [])
            if not features:
                break

            all_features.extend(features)
            print(f"  Fetched {len(features)} (total: {len(all_features)})")

            if len(features) < batch_size:
                break

            offset += batch_size
            time.sleep(0.2)  # Be nice to servers

        except Exception as e:
            print(f"  Error at offset {offset}: {e}")
            if offset == 0:
                return None
            break

    return all_features


def convert_to_geojson(features):
    """Convert ArcGIS features to GeoJSON."""
    geojson = {
        'type': 'FeatureCollection',
        'features': []
    }

    for f in features:
        geom = f.get('geometry', {})
        props = f.get('attributes', {})

        if 'rings' in geom:
            geojson['features'].append({
                'type': 'Feature',
                'properties': props,
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': geom['rings']
                }
            })
        elif 'x' in geom and 'y' in geom:
            geojson['features'].append({
                'type': 'Feature',
                'properties': props,
                'geometry': {
                    'type': 'Point',
                    'coordinates': [geom['x'], geom['y']]
                }
            })

    return geojson


def export_county(county_key, output_dir):
    """Export a single county's parcel data."""
    if county_key not in COUNTY_CONFIGS:
        print(f"Unknown county: {county_key}")
        print(f"Available counties: {list(COUNTY_CONFIGS.keys())}")
        return False

    config = COUNTY_CONFIGS[county_key]

    # Create output directory
    state = county_key.split('_')[0].lower()
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Fetch parcels
    features = fetch_parcels(config)

    if not features:
        print(f"No features retrieved for {config['name']}")
        return False

    # Convert to GeoJSON
    geojson = convert_to_geojson(features)

    # Save
    output_file = os.path.join(output_dir, f"parcels_{county_key.lower()}.geojson")
    with open(output_file, 'w') as f:
        json.dump(geojson, f)

    file_size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\nSaved {len(geojson['features'])} features to {output_file} ({file_size:.1f} MB)")
    return True


def list_counties():
    """List all available counties by state."""
    states = {}
    for key, config in COUNTY_CONFIGS.items():
        state = key.split('_')[0]
        if state not in states:
            states[state] = []
        states[state].append((key, config['name']))

    for state, counties in sorted(states.items()):
        print(f"\n{state}:")
        for key, name in counties:
            print(f"  {key}: {name}")


def export_state_counties(state_prefix, output_dir):
    """Export all counties for a given state."""
    counties = [k for k in COUNTY_CONFIGS.keys() if k.startswith(state_prefix + '_')]

    if not counties:
        print(f"No counties configured for state: {state_prefix}")
        return

    print(f"Exporting {len(counties)} counties for {state_prefix}...")

    for i, county_key in enumerate(counties, 1):
        print(f"\n[{i}/{len(counties)}] {county_key}")
        export_county(county_key, output_dir)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Export county parcel data')
    parser.add_argument('county', nargs='?', help='County key (e.g., PA_PHILADELPHIA) or state prefix (e.g., PA)')
    parser.add_argument('-o', '--output', default='./output/geojson/counties', help='Output directory')
    parser.add_argument('-l', '--list', action='store_true', help='List available counties')
    parser.add_argument('-a', '--all', action='store_true', help='Export all counties for a state prefix')

    args = parser.parse_args()

    if args.list:
        list_counties()
    elif args.county:
        if args.all or len(args.county) == 2:
            # Export all counties for a state
            export_state_counties(args.county.upper(), args.output)
        else:
            # Export single county
            export_county(args.county.upper(), args.output)
    else:
        parser.print_help()
