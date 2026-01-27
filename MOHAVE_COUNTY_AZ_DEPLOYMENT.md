# Mohave County, Arizona - Deployment Report

**Deployment Date**: 2026-01-26
**Status**: ✅ COMPLETE

---

## Summary

Successfully deployed Mohave County, Arizona parcel data to R2 CDN. This increases Arizona coverage from 73% (11/15 counties) to 80% (12/15 counties).

---

## Data Source

**Provider**: Mohave County GIS
**Endpoint**: https://mcgis.mohave.gov/arcgis/rest/services/Mohave/MapServer/38
**Layer**: ParcelQueryLayer (Layer 38)
**Service Type**: ArcGIS REST MapServer
**Source CRS**: EPSG:3857 (Web Mercator)

---

## Deployment Details

### Parcel Statistics
- **Total Parcels**: 266,330
- **Geographic Coverage**: Mohave County, Arizona
- **Major Cities**: Lake Havasu City, Kingman, Bullhead City
- **County Population**: ~213,000

### File Sizes
| Stage | Format | Size |
|-------|--------|------|
| Download | GeoJSON (EPSG:3857) | 549 MB |
| Reprojected | GeoJSON (EPSG:4326) | 569 MB |
| Final | PMTiles | 357 MB |

### PMTiles Specifications
- **Format**: PMTiles v3 (Vector Protobuf/MVT)
- **Zoom Levels**: 8-16
- **Layer Name**: parcels
- **Compression**: Gzip (internal + tile)
- **Tile Count**: 143,515 entries
- **Bounds**:
  - West: -114.743014°
  - South: 34.209653°
  - East: -112.528728°
  - North: 37.000701°

---

## CDN Access

**R2 Path**: `s3://gspot-tiles/parcels/parcels_az_mohave.pmtiles`
**CDN URL**: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_az_mohave.pmtiles
**File ID**: `parcels_az_mohave`

---

## Processing Pipeline

1. **Download**: Python script to query ArcGIS REST API with pagination (2,000 records/batch)
2. **Reproject**: ogr2ogr to convert from EPSG:3857 to EPSG:4326
3. **Tile Generation**: tippecanoe with density-based dropping for optimal performance
4. **Upload**: AWS CLI to Cloudflare R2
5. **Verification**: pmtiles show to validate metadata

---

## Arizona Coverage Update

### Before This Deployment
- Counties: 11/15 (73%)
- Files: parcels_az, parcels_az_maricopa, parcels_az_pima, parcels_az_pinal, parcels_az_yavapai, parcels_az_yuma, parcels_az_cochise, parcels_az_la_paz, parcels_az_greenlee, parcels_az_graham, parcels_az_gila, parcels_az_apache

### After This Deployment
- Counties: 12/15 (80%)
- **NEW**: parcels_az_mohave

### Remaining Arizona Counties
1. **Navajo County** (population ~110K)
2. **Coconino County** (population ~145K) - includes Flagstaff
3. **Santa Cruz County** (population ~47K)

---

## Registry Updates

✅ Added to `/data-pipeline/data/valid_parcels.json`
✅ Added to `/data-pipeline/data/data_sources_registry.json`
✅ Updated Arizona coverage notes

---

## Search Terms Used

- "Mohave County Arizona parcels"
- "Mohave County GIS"
- "Mohave County ArcGIS REST API"
- "mcgis.mohave.gov"

---

## Sources

- [GIS Maps | Mohave County](https://www.mohave.gov/departments/information-technology/gis-maps/)
- [Mohave MapServer](https://mcgis.mohave.gov/arcgis/rest/services/Mohave/MapServer)
- [PARCELS MapServer](https://mcgis2.mohavecounty.us/arcgis/rest/services/PARCELS/MapServer)
- [Mohave County Open Data](https://az-mohave.opendata.arcgis.com/)

---

## Technical Notes

- Used layer 38 (ParcelQueryLayer) instead of layer 4 (Tax Parcel group layer)
- Layer 38 provided clean access to all 266K parcels with complete attributes
- Server maxRecordCount is 2,000, required 134 API calls to download complete dataset
- Tippecanoe applied density-based feature dropping to optimize tile sizes at lower zoom levels
- No coordinate system issues - source was already in Web Mercator (EPSG:3857)

---

## Next Steps

To complete 100% Arizona coverage:
1. Deploy Navajo County parcels
2. Deploy Coconino County parcels (Flagstaff)
3. Deploy Santa Cruz County parcels

---

**Deployed by**: Claude Code Agent
**Mission**: 100% USA Parcel Coverage
