# Webster Parish, Louisiana - Parcel Data Investigation Report

**Date**: 2026-01-27
**Parish**: Webster Parish (Minden area)
**Population**: ~39,000
**Status**: ❌ **NO PUBLIC API AVAILABLE**

---

## Executive Summary

Webster Parish, Louisiana does **NOT** have a publicly accessible ArcGIS REST API for parcel data. After extensive investigation, the parish uses an internal QGIS MapServer accessible only on their private network, making automated data extraction impossible through standard methods.

**Recommendation**: Contact the Webster Parish Assessor directly for bulk data export, or purchase from commercial providers.

---

## Investigation Details

### Official Sources

| Resource | URL | Status |
|----------|-----|--------|
| **Assessor Website** | https://www.websterassessor.org/ | Active (contact info available) |
| **Public GIS Portal** | https://atlas.geoportalmaps.com/webster_public | Active (web viewer only) |
| **Contact Page** | https://www.websterassessor.org/contact-us | Available |

### Technical Infrastructure

**Platform**: GeoPortal Maps (GCT/Geosync)
**Backend**: QGIS MapServer
**Network**: Internal only (192.168.60.130:8001)

**Portal Analysis**:
- Uses QGIS WMS services on private network:
  - `http://192.168.60.130:8001/cgi-bin/qgis_mapserv.fcgi.exe?MAP=D:/GCTServices/Webster_Parcels.mxd.qgs`
  - `http://192.168.60.130:8001/cgi-bin/qgis_mapserv.fcgi.exe?MAP=D:/GCTServices/WebsterMap.mxd.qgs`
- Imagery proxy: `http://localhost:8084/ImageryProxy/api/Proxy/Geosync/Webster/`
- **No public ArcGIS REST endpoints found**

### Endpoints Tested

All tested endpoints **FAILED**:

```
❌ https://webstergis.websterparish.org/server/rest/services/Parcels/MapServer/0
❌ https://webstergis.websterparish.org/server/rest/services/Parcels/WebsterParcels_Public/MapServer/0
❌ https://services6.arcgis.com/*/arcgis/rest/services/Webster_Parish_Parcels/FeatureServer/0
❌ https://utility.arcgis.com/usrsvcs/servers/*/rest/services/Webster*/FeatureServer/0
```

**Failure Pattern**: Matches other Louisiana parishes using GeoPortal Maps platform:
- Beauregard Parish - No public API
- St. Tammany Parish - Firewall/auth blocked
- St. Mary Parish - Proprietary ViewPro GIS (migrating to geosync.io Feb 2026)

---

## Commercial Data Availability

**Estimated Parcel Count**: ~61,084 parcels

### Commercial Providers

1. **Regrid**
   - URL: https://app.regrid.com/store/us/la/webster
   - Format: Shapefile, KML, Spreadsheet
   - Cost: ~$500 (estimate for parish-level data)
   - Coverage: Complete Webster Parish

2. **Dynamo Spatial**
   - URL: https://www.dynamospatial.com/c/webster-parish-la/parcel-data
   - Format: ESRI Shapefile (can convert to other formats)
   - Coverage: 61,084+ properties
   - Note: Industry-standard formats available

**Evidence**: Multiple commercial providers have Webster Parish data, confirming the parcel database exists and is available through official channels (just not publicly via REST API).

---

## Data Access Options

### Option 1: Contact Webster Parish Assessor (FREE - Official)

**Best for**: Official/authoritative data, no cost

**Contact**:
- Website: https://www.websterassessor.org/contact-us
- Office: Webster Parish Assessor's Office
- Request: Bulk export of parcel shapefile or GeoJSON

**Approach**:
```
Subject: Parcel Data Request for Open Source Mapping Project

Dear Webster Parish Assessor,

I am working on an open-source mapping project (mapsfordevelopers.com)
providing free parcel data for developers and researchers. We currently
serve 32 states and 200+ datasets nationwide.

Would you be able to provide a bulk export of Webster Parish parcels
in Shapefile or GeoJSON format? We would:
- Publicly host the data for free access
- Credit Webster Parish Assessor as the source
- Update data annually as it becomes available
- Ensure data integrity and accuracy

This would benefit property researchers, developers, and the public
while maintaining attribution to your office.

Thank you for your consideration.
```

**Data Usage Restrictions**:
- Data is copyrighted by Webster Parish Assessor
- Cannot sell, trade, or create derivatives without written permission
- Request explicit permission for public hosting and redistribution

---

### Option 2: Purchase from Commercial Provider (PAID - Immediate)

**Best for**: Immediate access, guaranteed availability

**Regrid** (Recommended):
- Pricing: ~$500 for parish-level data (Pro account)
- Formats: Shapefile, KML, Spreadsheet
- License: Check if allows redistribution for open-source projects
- Support: Professional data support

**Dynamo Spatial**:
- Pricing: Contact for quote
- Formats: Shapefile + conversions
- Coverage: 61K+ properties confirmed

**Important**: Verify licensing terms allow public redistribution before purchasing.

---

### Option 3: Wait for Platform Migration (UNCERTAIN)

**Best for**: Patience, potential future free access

Similar Louisiana parishes are migrating to modern platforms:
- **St. Mary Parish**: Migrating to geosync.io (Feb 1, 2026)
- Modern platforms often provide REST API access

**Action**: Check back in 6-12 months to see if Webster Parish upgrades to a platform with public API access.

---

## Comparison with Working Louisiana Parishes

### Louisiana Parishes with PUBLIC APIs (13/64 = 20.3%)

| Parish | Population | Parcels | API Type | Status |
|--------|------------|---------|----------|--------|
| **Ascension** | 126K | 59,778 | ArcGIS FeatureServer | ✅ Deployed |
| **Bossier** | 128K | 78,556 | ArcGIS MapServer | ✅ Deployed |
| **Caddo** | 237K | Unknown | ArcGIS | ✅ Deployed |
| **Calcasieu** | 203K | Unknown | ArcGIS | ✅ Deployed |
| **East Baton Rouge** | 456K | Unknown | ArcGIS | ✅ Deployed |
| **Iberville** | 31K | 17,471 | ArcGIS FeatureServer | ✅ Deployed |
| **Jefferson** | 432K | Unknown | ArcGIS | ✅ Deployed |
| **Lafayette** | 241K | Unknown | ArcGIS | ✅ Deployed |
| **Livingston** | 142K | 84,692 | ArcGIS MapServer | ✅ Deployed |
| **Orleans** | 383K | Unknown | ArcGIS | ✅ Deployed |
| **St. Bernard** | 47K | Unknown | ArcGIS | ✅ Deployed |
| **Tangipahoa** | 133K | 75,919 | ArcGIS FeatureServer | ✅ Deployed |
| **Terrebonne** | 109K | Unknown | ArcGIS | ✅ Deployed |

### Louisiana Parishes WITHOUT Public APIs

| Parish | Population | Platform | Issue |
|--------|------------|----------|-------|
| **Webster** | 39K | GeoPortal/QGIS | Internal network only |
| **Beauregard** | 37K | GeoPortal Maps | No public API |
| **St. Tammany** | 265K | GeoPortal Maps | Firewall blocked |
| **St. Mary** | 49K | ViewPro GIS | Migrating Feb 2026 |
| **West Baton Rouge** | 27K | Total Land Solutions | Proprietary |
| **Rapides** | 130K | RAPC Portal | No REST API |

**Pattern**: Louisiana has **NO statewide parcel database**. Each parish uses independent systems, with ~80% having no public API access.

---

## Technical Notes

### Why This Parish is Challenging

1. **No Statewide Database**: Louisiana is one of the few states with zero centralized parcel data
2. **Proprietary Platforms**: Many parishes use commercial platforms (GeoPortal Maps, ViewPro, Total Land Solutions) that prioritize web viewers over API access
3. **Internal Networks**: Some parishes (like Webster) host GIS services on internal-only networks
4. **Budget Constraints**: Smaller parishes (~39K population) often lack resources for modern GIS infrastructure

### Data Conversion Pipeline (If Obtained)

If you obtain Webster Parish parcels via assessor or commercial provider:

```bash
# 1. Reproject to WGS84 (EPSG:4326)
ogr2ogr -f GeoJSON \
  -t_srs EPSG:4326 \
  webster_wgs84.geojson \
  webster_raw.shp

# 2. Convert to PMTiles
tippecanoe -o parcels_la_webster.pmtiles \
  -Z8 -z15 \
  -l parcels \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  webster_wgs84.geojson

# 3. Upload to R2
aws s3 cp parcels_la_webster.pmtiles \
  s3://gspot-tiles/parcels/parcels_la_webster.pmtiles \
  --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com

# 4. Validate
pmtiles show parcels_la_webster.pmtiles
```

**Expected Output**:
- File size: ~20-30 MB (based on ~61K parcels)
- Zoom levels: 8-15
- CRS: WGS84 (EPSG:4326)

---

## Recommendation

### Immediate Action

**Contact Webster Parish Assessor** for bulk data export (FREE option first):
1. Visit https://www.websterassessor.org/contact-us
2. Request Shapefile or GeoJSON export
3. Explain open-source mapping project use case
4. Request permission for public hosting/redistribution

### If Assessor Declines

**Purchase from Regrid** (~$500):
- Immediate access
- Professional support
- Verified data quality
- Check redistribution license terms

### Long-term Strategy

**Monitor for platform migrations**:
- Check Webster Parish every 6-12 months
- If they migrate to modern platform (like St. Mary → geosync.io), may gain API access
- Watch for Louisiana statewide parcel initiative (unlikely but possible)

---

## Updated Registry Entry

Webster Parish has been added to `/home/exx/Documents/C/hitd_maps/data-pipeline/data/data_sources_registry.json`:

```json
{
  "webster": {
    "name": "Webster Parish (Minden)",
    "population": 39000,
    "status": "missing - no public API",
    "url": "https://www.websterassessor.org/",
    "portal": "https://atlas.geoportalmaps.com/webster_public",
    "api_url": null,
    "format": "QGIS MapServer (internal network only)",
    "estimated_records": 61084,
    "last_attempted": "2026-01-27",
    "failure_reason": "Portal uses internal QGIS MapServer on private network",
    "notes": "NO PUBLIC API - Contact assessor or purchase from Regrid/Dynamo Spatial",
    "assessor": "Webster Parish Assessor, websterassessor.org/contact-us",
    "alternative_access": "Contact assessor or purchase from commercial provider",
    "checked_date": "2026-01-27"
  }
}
```

---

## Sources

- [Webster Parish Assessor Maps](https://www.websterassessor.org/maps)
- [Webster Parish GIS Portal](https://atlas.geoportalmaps.com/webster_public)
- [Regrid - Webster Parish Data](https://app.regrid.com/store/us/la/webster)
- [Dynamo Spatial - Webster Parish](https://www.dynamospatial.com/c/webster-parish-la/parcel-data)
- [Louisiana GIS & Data Portal](https://www.doa.la.gov/doa/osl/gis-data/)

---

## Appendix: Louisiana Parish Coverage Summary

**Current Coverage**: 13/64 parishes (20.3%)

**Total Files**: 13 parishes
**Total Parcels**: ~1.2M+ (estimated, many counts unknown)
**R2 Storage**: ~450 MB (Louisiana parcels)

**Next Priorities**:
1. **St. Mary Parish** - Wait for geosync.io migration (Feb 1, 2026)
2. **Rapides Parish** (130K pop) - Contact assessor
3. **Webster Parish** (39K pop) - Contact assessor or purchase
4. **Beauregard Parish** (37K pop) - Contact assessor or purchase

**Goal**: Achieve 30% Louisiana coverage (19/64 parishes) by end of Q1 2026.

---

*Report generated by HITD Maps data pipeline - 2026-01-27*
