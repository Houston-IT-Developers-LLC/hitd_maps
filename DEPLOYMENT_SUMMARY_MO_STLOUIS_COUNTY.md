# St. Louis County, Missouri Parcel Deployment

**Date:** 2026-01-25  
**Status:** ✅ Complete

## Summary

Successfully deployed St. Louis County, Missouri parcel data to production.

## Details

- **Source:** St. Louis County GIS Open Data Portal
- **API Endpoint:** `https://maps.stlouisco.com/hosting/rest/services/Maps/AGS_Parcels/MapServer/0`
- **Portal:** data-stlcogis.opendata.arcgis.com
- **Total Parcels:** 401,471
- **County Population:** 989,000
- **File Size:** 11 MB (PMTiles)
- **Original Size:** 839 MB (GeoJSON)

## What Was Done

1. **Source Discovery**
   - Found dataset ID: fd4893ca99244279adb2ffa206e09ec7_7
   - Identified working MapServer endpoint
   - Verified query capabilities (401,471 features confirmed)

2. **Data Download**
   - Created custom download script: `deploy_mo_stlouis_county.py`
   - Used resultOffset pagination (201 chunks × 2000 features)
   - Download time: 8.2 minutes at ~864 features/sec
   - Output: `parcels_mo_stlouis_county.geojson` (839 MB)

3. **Processing**
   - Verified CRS: Already in WGS84 (EPSG:4326) ✓
   - No reprojection needed
   - Converted to PMTiles using tippecanoe
   - Zoom levels: 8-13
   - Final size: 10.3 MB

4. **Deployment**
   - Uploaded to Cloudflare R2: `s3://gspot-tiles/parcels/parcels_mo_stlouis_county.pmtiles`
   - CDN URL: `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_mo_stlouis_county.pmtiles`
   - Verified accessibility: HTTP 200 OK

5. **Registry Updates**
   - Added to `valid_parcels.json` (now 237 files total)
   - Updated `data_sources_registry.json` with:
     - Source metadata
     - API endpoint
     - Record count
     - Last updated date
   - Regenerated `coverage_status.json`

## Coverage Impact

### Missouri Coverage
- **Before:** 8% (9 counties)
- **After:** 8% (10 counties) - St. Louis County added
- **Files:** 10 county-level datasets
- **Status:** Partial (115 total counties)

### Overall Coverage
- **Total Files:** 237 PMTiles
- **Total Coverage:** 70.6% of USA
- **Complete States:** 36/51
- **Partial States:** 15/51
- **Missing States:** 0/51

## Important Notes

- **St. Louis County ≠ St. Louis City:** These are separate jurisdictions
  - St. Louis City: `parcels_mo_stlouis_city` (already deployed)
  - St. Louis County: `parcels_mo_stlouis_county` (newly deployed)
- St. Louis County is the larger metro area surrounding the city
- Population: 989K (county) vs ~300K (city)
- Parcels: 401K (county) vs ~65K (city estimated)

## Files Created/Modified

### New Files
- `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/deploy_mo_stlouis_county.py`
- `/home/exx/Documents/C/hitd_maps/data-pipeline/data/downloads/parcels_mo_stlouis_county.geojson`
- `/home/exx/Documents/C/hitd_maps/data-pipeline/data/downloads/parcels_mo_stlouis_county.pmtiles`

### Updated Files
- `data-pipeline/data/valid_parcels.json`
- `data-pipeline/data/data_sources_registry.json`
- `data-pipeline/data/coverage_status.json`

## Next Steps

To use this data in the frontend:

1. The PMTiles file is already live on CDN
2. Frontend will automatically load it when zoomed to zoom level 8+
3. Layer name: `parcels`
4. Extent: (-90.74, 38.39) to (-90.12, 38.89)

## Technical Details

### Download Script
- Uses ArcGIS REST API resultOffset pagination
- Handles 2000 features per request
- Includes retry logic (3 attempts)
- Rate limiting (0.5s between requests)
- Progress tracking with ETA

### Data Quality
- Geometry type: Polygons
- CRS: WGS84 (EPSG:4326)
- Null geometries: Some features have null geometry (excluded from PMTiles)
- Attributes: 74 fields including:
  - LOCATOR (parcel ID)
  - OWNER_NAME
  - PROP_ADD (property address)
  - TAXYR (tax year)
  - TOTASSMT (total assessment)
  - APPLANDVAL/APPIMPVAL (appraised values)
  - PROPCLASS (property classification)
  - LANDUSE2 (land use)

### Performance
- Download: 8.2 min for 401K features
- Conversion: ~2 min (tippecanoe)
- Upload: <1 min to R2
- Total deployment time: ~12 minutes

---

**Deployment completed successfully by Claude Code on 2026-01-25**
