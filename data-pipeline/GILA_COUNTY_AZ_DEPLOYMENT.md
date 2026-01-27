# Gila County, Arizona Parcel Deployment Report

**Date**: 2026-01-26
**Status**: ✅ Successfully Deployed

---

## Summary

Successfully deployed Gila County, Arizona parcels to R2 CDN, increasing Arizona coverage from 9 to 10 counties (67% complete).

## Data Source

- **Endpoint**: `https://gis.gilacountyaz.gov/arcgis/rest/services/Assessor/ParcelsTyler/MapServer/0`
- **Type**: ArcGIS REST MapServer
- **Format**: GeoJSON (with WGS84 reprojection)
- **Total Parcels**: 33,558
- **County Info**: 
  - Population: ~54,000
  - Major cities: Globe, Payson
  - Region: Central Arizona

## Processing Pipeline

1. **Download**: Downloaded all 33,558 parcels via paginated API requests (1,000 per batch)
   - Source: Gila County Assessor ParcelsTyler service
   - Output: `/home/exx/Documents/C/hitd_maps/data-pipeline/downloads/az_gila/parcels_raw.geojson` (35 MB)
   - CRS: EPSG:4326 (WGS84) - requested directly from API, no reprojection needed

2. **Convert to PMTiles**: 
   - Tool: tippecanoe v2.80.0
   - Zoom levels: 8-16
   - Output: `parcels_az_gila.pmtiles` (25 MB)
   - Tiles: 3,894 addressed tiles, 3,864 entries

3. **Upload to R2**:
   - Destination: `s3://gspot-tiles/parcels/parcels_az_gila.pmtiles`
   - Transfer speed: ~30 MiB/s
   - Content-Type: `application/vnd.pmtiles`

## Verification

✅ **CDN URL**: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_az_gila.pmtiles

✅ **PMTiles Metadata**:
```
Bounds: -111.545881, 32.983158, -110.691850, 34.418836
Min zoom: 8
Max zoom: 16
Tile type: Vector Protobuf (MVT)
Layer: parcels
Attribution: Gila County
```

✅ **Added to Registry**:
- `valid_parcels.json`: Added "parcels_az_gila" (alphabetically sorted)
- `data_sources_registry.json`: Added Gila County entry with full metadata

## Arizona Coverage Update

**Before**: 9/15 counties (60%)
**After**: 10/15 counties (67%)

**Covered Counties**:
1. Maricopa (Phoenix metro) - 4.5M population
2. Pima (Tucson) - 1.1M population  
3. Pinal - 470K population
4. Yavapai - 236K population
5. Yuma - 213K population
6. Cochise - 126K population
7. Gila - 54K population ⬅️ **NEW**
8. La Paz - 20K population
9. Graham - 38K population
10. Greenlee - 10K population

**Still Missing** (5 counties):
- Apache County
- Coconino County (Flagstaff)
- Mohave County (Lake Havasu City)
- Navajo County
- Santa Cruz County

## Files Created

- `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/download_gila_az.py`
- `/home/exx/Documents/C/hitd_maps/data-pipeline/downloads/az_gila/parcels_raw.geojson` (35 MB)
- `/home/exx/Documents/C/hitd_maps/data-pipeline/processed/parcels_az_gila.pmtiles` (25 MB)

## Next Steps

To complete Arizona coverage (remaining 5 counties):
1. Apache County - Search for county GIS portal
2. Coconino County (Flagstaff) - Major county, should have data
3. Mohave County - Check assessor website
4. Navajo County - May be available via state portal
5. Santa Cruz County - Border county, check accessibility

---

**Deployment Time**: ~3 minutes
**Data Quality**: Excellent - clean geometries, complete attributes
**Status**: Production Ready ✅
