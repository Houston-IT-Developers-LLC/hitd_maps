# Iberia Parish, Louisiana - Parcel Data Research

**Date**: 2026-01-26
**Parish**: Iberia Parish, Louisiana
**Population**: ~69,000
**Major City**: New Iberia
**Target File**: `parcels_la_iberia.pmtiles`

---

## Summary

**NO FREE PUBLIC REST API AVAILABLE** for Iberia Parish parcels. The parish uses a proprietary GeoPortal Maps system with an internal QGIS MapServer that is not publicly accessible via standard REST endpoints.

---

## Data Sources Investigated

### 1. Iberia Parish Government GIS Hub
- **URL**: https://gis-ipg.hub.arcgis.com/
- **Status**: Interactive maps only, no downloadable datasets
- **Findings**:
  - Hosts interactive Experience Builder apps (Zoning, Districts, etc.)
  - No public REST API endpoints
  - No downloadable data layers
- **Contact**: iberiagis@iberiagov.net

### 2. Atlas GeoPortal Maps
- **URL**: https://atlas.geoportalmaps.com/iberia
- **Status**: Proprietary web viewer with internal QGIS backend
- **Findings**:
  - Uses internal QGIS MapServer at `http://192.168.60.130:8001` (not publicly accessible)
  - Spatial reference: EPSG:3452 (Louisiana State Plane South)
  - MapServer endpoint at `https://services.geoportalmaps.com/arcgis/rest/services/Iberia_Parcels/MapServer` returns 404
  - Moving to geosync.io platform as of January 1, 2026

### 3. Louisiana State GIS (LAGIC/LSU)
- **URL**: http://lagic.lsu.edu/
- **Status**: No statewide parcel dataset
- **Findings**:
  - Louisiana has NO statewide parcel database
  - Each parish manages data independently via proprietary systems
  - 7/64 parishes currently in our coverage (11%)

### 4. ArcGIS Open Data Portal
- **Search**: Checked ArcGIS.com and opendata.arcgis.com
- **Status**: No Iberia Parish parcel datasets found
- **Findings**: No public feature services discovered

---

## Commercial Data Options

### Regrid (Recommended)
- **URL**: https://app.regrid.com/store/us/la/iberia
- **Coverage**: Full Iberia Parish (~46,920 properties)
- **Formats**: Shapefile, CSV, KML, GeoJSON
- **Pricing**:
  - Per-county purchase (one-time)
  - Regrid Pro subscription (multi-county access)
  - API licenses available (nationwide access)

**Free Option**: Regrid offers a free nationwide parcel boundary tile layer via ArcGIS Living Atlas:
- **MapServer**: https://tiles.arcgis.com/tiles/KzeiCaQsMoeCfoCq/arcgis/rest/services/Regrid_Nationwide_Parcel_Boundaries_v1/MapServer
- **Limitation**: TilesOnly (MapServer) - cannot query/download features, only view tiles
- **Attributes**: Limited (address, size, parcel ID visible on click)
- **Full data**: Requires purchase from Regrid Data Store

### Dynamo Spatial
- **URL**: https://www.dynamospatial.com/c/iberia-parish-la/parcel-data
- **Coverage**: 46,920+ properties
- **Format**: ESRI Shapefile
- **Pricing**: Commercial (pricing not listed)

---

## Recommendations

### Option 1: Contact Iberia Parish GIS Directly (FREE)
**Contact**: iberiagis@iberiagov.net
**Phone**: 337-369-4438 (Planning & Zoning)

**Request**: Bulk parcel data export in Shapefile/GeoJSON format

**Pros**:
- Free (if they provide it)
- Official/authoritative source
- Most up-to-date

**Cons**:
- May take time to respond
- May not provide bulk downloads
- No guarantee of success

**Recommended Email Template**:
```
Subject: Request for Bulk Parcel Data Export

Dear Iberia Parish GIS Team,

I am working on a public mapping project (mapsfordevelopers.com) to provide
comprehensive parcel coverage across the United States. We currently have
coverage for 7 Louisiana parishes and would like to add Iberia Parish.

Would it be possible to obtain a bulk export of parcel boundaries in
Shapefile, GeoJSON, or similar GIS format? We would properly attribute the
data source and use it for non-commercial mapping purposes.

Thank you for your consideration.
```

### Option 2: Purchase from Regrid (PAID - RECOMMENDED)
**Cost**: Estimated $200-500 for single-county purchase
**Turnaround**: Immediate download
**Quality**: High - standardized, cleaned data with 143+ attributes

**Pros**:
- Immediate access
- Standardized schema (easier to process)
- 100% coverage guarantee
- Additional attributes (zoning, building footprints, etc.)
- Regular updates available

**Cons**:
- Cost (one-time purchase)
- Commercial data (requires license compliance)

**URL**: https://app.regrid.com/store/us/la/iberia

### Option 3: Manual Digitization from Public Maps (FREE but LABOR-INTENSIVE)
**Not recommended** - Would require scraping/digitizing from the web viewer, violating terms of service.

---

## Louisiana Parish Context

Louisiana is one of the most challenging states for parcel data acquisition:
- **No statewide database** (unlike TX, FL, CA, etc.)
- **64 parishes** each with independent systems
- **Many use proprietary portals** (Atlas/GeoPortal Maps, Schneider, etc.)
- **Current HITD coverage**: 7/64 parishes (11%)

**Other LA parishes with similar issues**:
- St. Tammany (Priority 1 - hunting area) - Atlas/GeoPortal Maps
- Livingston (Priority 2) - Atlas/GeoPortal Maps
- Tangipahoa (Priority 3) - Custom GIS portal
- Rapides (Priority 4) - RAPC GIS
- Bossier (Priority 5) - Atlas/GeoPortal Maps

**Strategy**: Focus on parishes with public REST APIs first, then consider bulk Regrid purchase for remaining parishes.

---

## Next Steps

1. **Send email** to iberiagis@iberiagov.net requesting bulk parcel data
2. **Wait 1-2 weeks** for response
3. **If no response or declined**: Purchase from Regrid
4. **Update data_sources_registry.json** with Iberia Parish details
5. **Consider batch Regrid purchase** for all missing Louisiana parishes

---

## Technical Notes

- **Target CRS**: EPSG:4326 (WGS84) for PMTiles
- **Source CRS**: EPSG:3452 (Louisiana State Plane South NAD83 Feet)
- **Reprojection**: Required via ogr2ogr
- **Estimated file size**: ~5-8 MB PMTiles (based on similar parishes)

---

## Sources

- [Iberia Parish Government GIS Hub](https://gis-ipg.hub.arcgis.com/)
- [Atlas GeoPortal Maps - Iberia Parish](https://atlas.geoportalmaps.com/iberia)
- [Regrid - Iberia Parish Data Store](https://app.regrid.com/store/us/la/iberia)
- [Louisiana GIS & Data](https://www.doa.la.gov/doa/osl/gis-data/)
- [LAGIC - Louisiana Geographic Information Center](http://lagic.lsu.edu/)
- [Regrid USA Nationwide Parcel Boundaries (ArcGIS Living Atlas)](https://www.arcgis.com/home/item.html?id=a2050b09baff493aa4ad7848ba2fac00)
