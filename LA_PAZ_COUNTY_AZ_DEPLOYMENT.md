# La Paz County, Arizona - Parcel Deployment Report

**Date**: 2026-01-26
**Status**: ✅ COMPLETE

---

## Summary

Successfully deployed La Paz County, Arizona parcel data to R2 CDN.

---

## Deployment Details

| Attribute | Value |
|-----------|-------|
| **County** | La Paz County, Arizona |
| **Population** | ~20,000 |
| **Parcel Count** | 16,176 |
| **Data Source** | Arizona Department of Water Resources |
| **Endpoint Type** | ArcGIS REST MapServer |
| **Source CRS** | EPSG:26912 (UTM Zone 12N) |
| **Target CRS** | EPSG:4326 (WGS84) |

---

## Data Source

**Endpoint URL**:
`https://azwatermaps.azwater.gov/arcgis/rest/services/General/Parcels_for_TEST/MapServer/4`

**Provider**: Arizona Department of Water Resources
**Format**: ArcGIS REST MapServer (Layer 4)
**Max Records per Request**: 2,000
**Total Requests**: 9 (pagination)

---

## File Details

### Raw GeoJSON (EPSG:26912)
- **Path**: `/home/exx/Documents/C/hitd_maps/data-pipeline/downloads/parcels_az_la_paz.geojson`
- **Size**: 12 MB

### Reprojected GeoJSON (EPSG:4326)
- **Path**: `/home/exx/Documents/C/hitd_maps/data-pipeline/processed/parcels_az_la_paz_wgs84.geojson`
- **Size**: 12.2 MB

### PMTiles
- **Path**: `/home/exx/Documents/C/hitd_maps/data-pipeline/processed/parcels_az_la_paz.pmtiles`
- **Size**: 19.4 MB (20,384,682 bytes)
- **Zoom Levels**: 8-16
- **Layer Name**: `parcels`

---

## CDN Deployment

**R2 Bucket**: `gspot-tiles`
**S3 Path**: `s3://gspot-tiles/parcels/parcels_az_la_paz.pmtiles`

**CDN URL**:
https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_az_la_paz.pmtiles

**Verification**: ✅ Accessible (HTTP 200)
**Content-Type**: `application/vnd.pmtiles`
**ETag**: `50591793afc9c2eff584ad413194c186-3`

---

## Registry Updates

### valid_parcels.json
✅ Added `parcels_az_la_paz` to the valid parcels list (position: alphabetically sorted)

### data_sources_registry.json
✅ Added La Paz County to Arizona counties section:
```json
"la_paz": {
  "name": "La Paz County",
  "url": "https://azwatermaps.azwater.gov/arcgis/rest/services/General/Parcels_for_TEST/MapServer/4",
  "format": "ArcGIS REST MapServer",
  "total_records": 16176,
  "our_status": "have",
  "our_file": "parcels_az_la_paz",
  "deployed_date": "2026-01-26",
  "notes": "Western Arizona county (population ~20K), borders California and Colorado River"
}
```

✅ Updated Arizona coverage note:
- **Previous**: "Have 6/15 counties (40% coverage)"
- **Updated**: "Have 8/15 counties (53% coverage): Maricopa, Pima, Pinal, Yavapai, Yuma, Cochise, La Paz, Greenlee" (Note: Graham also added in parallel)

---

## Arizona Coverage Status

**Total Counties in Arizona**: 15
**Counties Deployed**: 9
**Coverage**: 60%

### Deployed Counties:
1. ✅ Maricopa (Phoenix metro - largest)
2. ✅ Pima (Tucson)
3. ✅ Pinal
4. ✅ Yavapai
5. ✅ Yuma (border county)
6. ✅ Cochise (Sierra Vista)
7. ✅ **La Paz** (NEW - western border county) - 16,176 parcels
8. ✅ Greenlee (deployed in parallel) - 4,706 parcels
9. ✅ Graham (deployed in parallel) - 18,744 parcels

### Missing Counties (6):
- Apache
- Coconino (Flagstaff)
- Gila
- Mohave (Kingman, Lake Havasu City)
- Navajo
- Santa Cruz

---

## Technical Notes

- **MapServer vs FeatureServer**: This endpoint is a MapServer (not FeatureServer), which is read-only but fully functional for data extraction
- **Coordinate System**: Data was in UTM Zone 12N (EPSG:26912), appropriate for western Arizona
- **Reprojection**: Successfully converted to WGS84 (EPSG:4326) using ogr2ogr
- **Tippecanoe**: Used default drop-densest-as-needed strategy for optimal tile generation
- **Pagination**: Required 9 requests to fetch all 16,176 parcels (2,000 record limit per request)

---

## Processing Pipeline

```
1. Download (9 paginated requests) → parcels_az_la_paz.geojson (12 MB)
2. Reproject (ogr2ogr) → parcels_az_la_paz_wgs84.geojson (12.2 MB)
3. Convert (tippecanoe) → parcels_az_la_paz.pmtiles (19.4 MB)
4. Upload (aws s3 cp) → R2 CDN
5. Verify (HTTP HEAD) → ✅ 200 OK
6. Update registries → valid_parcels.json + data_sources_registry.json
```

---

## Deployment Script

**Script**: `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/deploy_az_la_paz.py`
**Execution Time**: ~2 minutes
**Status**: Reusable for future updates

---

## Next Steps - Remaining Arizona Counties

### High Priority (Population > 100K):
- **Coconino County** (Flagstaff) - Pop: 145,000
- **Mohave County** (Kingman, Lake Havasu City) - Pop: 213,000

### Medium Priority:
- Apache County - Pop: 71,000
- Gila County - Pop: 53,000
- Navajo County - Pop: 110,000
- Graham County - Pop: 38,000
- Santa Cruz County - Pop: 47,000
- Greenlee County - Pop: 9,000

---

## Sources

- [La Paz County Data Viewer](https://gis.lapazcountyaz.org/portal/apps/webappviewer/index.html?id=cb17ccc0aed140c88d27002344089041)
- [ArcGIS MapServer Layer](https://azwatermaps.azwater.gov/arcgis/rest/services/General/Parcels_for_TEST/MapServer/4)
- [La Paz County Official Website](https://www.lapaz.gov/346/Community-Development---GIS)

---

**Deployed by**: Claude Code Agent
**Date**: 2026-01-26 23:27 UTC
