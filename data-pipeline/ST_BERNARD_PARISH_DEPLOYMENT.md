# St. Bernard Parish, Louisiana - Parcel Deployment Report

**Date**: 2026-01-26
**Parish**: St. Bernard Parish, Louisiana
**Status**: ✅ DEPLOYED SUCCESSFULLY

---

## Summary

Successfully deployed 21,761 parcel records from St. Bernard Parish (Chalmette area) to Cloudflare R2 CDN.

### Key Details

| Attribute | Value |
|-----------|-------|
| **Parish Name** | St. Bernard Parish |
| **State** | Louisiana |
| **Major City** | Chalmette |
| **Population** | ~47,000 |
| **Total Parcels** | 21,761 |
| **File Size** | 25.0 MB |
| **Zoom Levels** | 6-16 |
| **Geographic Extent** | -90.010226, 29.628881 to -89.170075, 30.156005 |

---

## Data Source

**Source**: St. Bernard Parish Government
**Portal**: https://gis-stbernard.opendata.arcgis.com/
**ArcGIS Server**: https://lucity.sbpg.net/arcgis/rest/services/ComDev/Parcels3/MapServer/0
**Contact**: gis@sbpg.net

### Source Details
- Service Type: ArcGIS MapServer
- Native CRS: EPSG:3452 (Louisiana State Plane South)
- Output Format: GeoJSON (WGS84)
- Max Record Count: 1,000 per request
- Total Batches: 22

### Key Fields
- ParcelNumber
- Owner_Name
- Owner_Address
- Street_Name
- Assessed_Value
- SalesPrice
- Legal_Description
- Ward
- Subdivision

---

## Deployment Process

### 1. Data Discovery
Found St. Bernard Parish Open Data portal with parcel dataset. The ArcGIS REST API endpoint returns GeoJSON already in WGS84 format, eliminating the need for coordinate reprojection.

### 2. Download
```bash
Source: https://lucity.sbpg.net/arcgis/rest/services/ComDev/Parcels3/MapServer/0
Method: Batched queries (1,000 records per batch)
Total Requests: 22
Download Time: ~2 minutes
Raw File: 28.3 MB GeoJSON
```

### 3. Coordinate System
**Important Discovery**: Unlike the MapServer metadata which reports EPSG:3452, the GeoJSON export is already in WGS84 (EPSG:4326). This is an ArcGIS server behavior where GeoJSON format is automatically reprojected.

```
Sample Coordinate: -90.009566, 29.949855 (already WGS84)
No reprojection needed!
```

### 4. PMTiles Conversion
```bash
Tool: tippecanoe v2.80.0
Min Zoom: 6
Max Zoom: 16
Layer Name: parcels
Options:
  - Drop densest as needed
  - Extend zooms if still dropping
  - Coalesce densest as needed
  - Detect shared borders
  - Simplification: 10

Output: 25.0 MB PMTiles
Tiles Created: 8,724 addressed tiles
```

### 5. Upload to R2
```bash
Bucket: gspot-tiles
File: parcels_la_st_bernard.pmtiles
Size: 25.0 MB
Upload Speed: ~26-33 MiB/s
Status: Success
```

---

## Deployment Assets

### Files Created

| File | Location | Size | Description |
|------|----------|------|-------------|
| Raw GeoJSON | `downloads/parcels_la_st_bernard_raw.geojson` | 28.3 MB | Original download |
| Processed GeoJSON | `processed/parcels_la_st_bernard_4326.geojson` | 28.3 MB | WGS84 (copy of raw) |
| PMTiles | `processed/parcels_la_st_bernard.pmtiles` | 25.0 MB | Final tileset |

### Public Access

**CDN URL**: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels_la_st_bernard.pmtiles

**Registry Entry**: `parcels_la_st_bernard` (added to valid_parcels.json)

---

## Technical Notes

### ArcGIS GeoJSON Export Behavior
When requesting GeoJSON format from ArcGIS REST APIs, the server automatically reprojects to WGS84 regardless of the service's native coordinate system. This is different from querying in JSON or Feature format which returns data in the service's native CRS.

**Lesson**: Always check actual coordinates in downloaded GeoJSON before reprojecting.

### Coordinate Validation
```python
# Check if coordinates are already WGS84
first_coord = geojson['features'][0]['geometry']['coordinates'][0][0]
lon, lat = first_coord[0], first_coord[1]

if -180 <= lon <= 180 and -90 <= lat <= 90:
    # Already WGS84, no reprojection needed
```

---

## Coverage Impact

### Louisiana State Progress

**Before Deployment**:
- Louisiana parishes with data: Variable (check coverage_status.json)

**After Deployment**:
- Added: St. Bernard Parish (21,761 parcels)
- Total Louisiana parcel files: +1

### Deployment Script

Created reusable script: `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/deploy_st_bernard_parish.py`

**Features**:
- Automatic coordinate system detection
- Batched download with progress tracking
- Smart reprojection (only if needed)
- PMTiles conversion with tippecanoe
- R2 upload with AWS CLI
- Registry updates

---

## Validation

### PMTiles Validation
```bash
pmtiles show parcels_la_st_bernard.pmtiles
```

**Results**:
- ✅ Spec version: 3
- ✅ Tile type: Vector Protobuf (MVT)
- ✅ Bounds: Correct Louisiana coordinates
- ✅ Zoom range: 6-16
- ✅ Tiles: 8,724 addressed tiles
- ✅ Attribution: St. Bernard Parish Government

### Public Access Test
```bash
curl -I https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels_la_st_bernard.pmtiles
```

**Results**:
- ✅ HTTP 200 OK
- ✅ Content-Length: 26,210,304 bytes (25 MB)
- ✅ Publicly accessible via CDN

---

## Next Steps

### 1. Map Integration
Add St. Bernard Parish to map viewer:
```javascript
map.addSource('parcels-st-bernard', {
  type: 'vector',
  url: 'pmtiles://https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels_la_st_bernard.pmtiles'
});
```

### 2. Update Documentation
- [x] Add to valid_parcels.json
- [ ] Update coverage_status.json for Louisiana
- [ ] Update DATA_INVENTORY.md
- [ ] Update Louisiana parish coverage report

### 3. Expand Louisiana Coverage
St. Bernard Parish neighbors to prioritize:
- Orleans Parish (New Orleans) - likely has existing data
- Plaquemines Parish (south)
- Jefferson Parish (west)

---

## Search Keywords

For future reference and discoverability:
- St. Bernard Parish Louisiana parcels
- Chalmette property data
- St. Bernard Parish GIS
- Louisiana State Plane South (EPSG:3452)
- New Orleans metro area parcels

---

## Sources

- [St. Bernard Parish Open GIS Data](https://gis-stbernard.opendata.arcgis.com/)
- [Parcels Dataset](https://gis-stbernard.opendata.arcgis.com/datasets/7d8d0f1453d347b480fd45fc92fae636)
- [St. Bernard Parish GIS Portal](https://www.sbpg.net/331/GIS-Maps-Data-Portal)

---

**Deployment completed**: 2026-01-26 23:50 UTC
**Deployed by**: Claude Code Agent
**Total deployment time**: ~5 minutes
