# Ascension Parish, Louisiana - Deployment Report

**Date:** 2026-01-26
**Parish:** Ascension Parish, LA
**Status:** ✓ DEPLOYED

---

## Summary

Successfully deployed 59,778 property parcels for Ascension Parish, Louisiana (Gonzales area) to Cloudflare R2 CDN.

---

## Data Source

**Authority:** Ascension Parish Data Analytics Department
**Portal:** https://gis.ascensionparishla.gov/
**API Endpoint:** https://gis.ascensionparishla.gov/server/rest/services/AssessorData/Assessor_Parcels/FeatureServer/317

**Technology:** ArcGIS REST FeatureServer 11.4
**Original CRS:** EPSG:3452 / EPSG:102682 (Louisiana State Plane South NAD83, US Feet)
**Total Records:** 59,778 parcels
**Download Size:** 111.4 MB (GeoJSON)

---

## Processing Details

### 1. Download
- **Script:** `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/download_ascension_la.py`
- **Method:** Paginated REST API queries (2,000 records per batch)
- **Total Batches:** 30
- **Output:** `/home/exx/Documents/C/hitd_maps/data-pipeline/downloads/ascension_la_parcels.geojson`

### 2. Reprojection
- **Tool:** ogr2ogr (GDAL)
- **Source CRS:** EPSG:3452 (Louisiana State Plane South NAD83)
- **Target CRS:** EPSG:4326 (WGS84)
- **Output Size:** 115 MB
- **Output:** `/home/exx/Documents/C/hitd_maps/data-pipeline/processed/ascension_la_parcels_wgs84.geojson`

### 3. PMTiles Conversion
- **Tool:** tippecanoe v2.80.0
- **Layer Name:** `parcels_la_ascension`
- **Zoom Levels:** 8-16
- **Options:** `--drop-densest-as-needed --extend-zooms-if-still-dropping`
- **Output Size:** 57 MB
- **Tiles Generated:** 4,113 addressed tiles, 3,971 tile entries
- **Output:** `/home/exx/Documents/C/hitd_maps/data-pipeline/processed/parcels_la_ascension.pmtiles`

### 4. R2 Upload
- **CDN URL:** https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels_la_ascension.pmtiles
- **File Size:** 56.4 MB
- **Content-Type:** application/vnd.pmtiles
- **Status:** ✓ Verified accessible

---

## Coverage Details

**Parish:** Ascension Parish
**Population:** ~126,000
**Major City:** Gonzales
**Bounding Box:**
- West: -91.106660°
- South: 30.062356°
- East: -90.632369°
- North: 30.346887°

**Center:** -90.925598°, 30.285160°

---

## File Updates

### 1. valid_parcels.json
Added `parcels_la_ascension` to the registry (now 268 total files)

### 2. data_sources_registry.json
- Updated Louisiana parish count: 9/64 parishes (14.1%)
- Added Ascension Parish entry to `priority_parishes` section
- Documented API endpoint and metadata

---

## Louisiana Coverage Update

**Previous:** 8/64 parishes (12.5%)
**Current:** 9/64 parishes (14.1%)

**Parishes with Coverage:**
1. Ascension (NEW)
2. Bossier
3. Caddo
4. Calcasieu
5. East Baton Rouge
6. Jefferson
7. Lafayette
8. Orleans
9. Terrebonne

---

## Technical Notes

- **CRS Challenge:** Original data used EPSG:102682, which is an Esri-specific code. Successfully reprojected using EPSG:3452 (equivalent Louisiana State Plane South NAD83).
- **Null Geometries:** Tippecanoe reported some null geometries during processing (not uncommon with assessor data).
- **Data Quality:** Clean parcel boundaries with comprehensive attribute data including Owner_Name, Owner_Address, Assessed_Value, Legal_Description, and property details.

---

## Data Sources

Sources used for discovery:
- [Ascension Parish GIS Division](https://www.ascensionparish.net/geographic-information-system-gis-division/)
- [Ascension Parish Data Analytics Department](https://gis.ascensionparishla.gov/)
- [Ascension Parish Maps Portal](https://maps.apgov.us/)

---

## Next Steps

**Recommended Louisiana parishes to target next:**
1. **St. Tammany** (pop. 265K) - Proprietary portal, may need manual contact
2. **Livingston** (pop. 142K) - Proprietary portal
3. **Tangipahoa** (pop. 133K) - Proprietary portal
4. **Rapides** (pop. 130K) - RAPC GIS system

**Note:** Most Louisiana parishes use proprietary GeoPortal Maps systems without standard ArcGIS REST API access. Ascension Parish is notable for having a proper ArcGIS Server deployment.

---

## Deployment Complete

**File:** `parcels_la_ascension.pmtiles`
**URL:** https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels_la_ascension.pmtiles
**Status:** Live and accessible
**Date:** 2026-01-26
