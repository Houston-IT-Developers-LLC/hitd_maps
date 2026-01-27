# St. Charles Parish, Louisiana - Deployment Report

**Date**: 2026-01-26  
**Parish**: St. Charles Parish, Louisiana  
**Population**: ~53,000 (Hahnville, Luling, Boutte areas)  
**Target File**: `parcels_la_st_charles.pmtiles`  
**Status**: ❌ **FAILED - NO PUBLIC API**

---

## Deployment Attempt Summary

**Goal**: Download St. Charles Parish parcels from ArcGIS REST API, convert to PMTiles, and deploy to R2.

**Result**: No publicly accessible ArcGIS REST API endpoint found.

---

## Investigation Findings

### 1. Current GIS Infrastructure

St. Charles Parish uses **QGIS Server** on an internal network instead of ArcGIS Server:

- **Current System**: GeoPortal Maps (atlas.geoportalmaps.com/stcharles)
- **Backend**: QGIS MapServer at `http://192.168.60.130:8001/cgi-bin/qgis_mapserv.fcgi.exe`
- **Access**: Internal network only (not publicly accessible)
- **Migration**: Moving to geosync.io platform (January 2026)

### 2. Geosync.io Platform Check

The parish has migrated to geosync.io:
- ✓ Site live at: https://stcharles.geosync.io/
- ✗ No public REST API endpoints
- Platform is a React SPA (Single Page Application)
- Data served through proprietary backend (not standard ArcGIS REST)

### 3. Alternative Sources Investigated

| Source | Status | Notes |
|--------|--------|-------|
| St. Charles Parish GIS Office | Public records request required | Official source |
| Port of South Louisiana GIS | No public REST API found | Covers St. Charles but no direct access |
| Louisiana State GIS Services | Not responsive | State-level servers unreachable |
| geoportalmaps.com | QGIS Server (internal) | 192.168.x.x network |
| geosync.io | No REST API | New platform, proprietary |

### 4. Web Search Results

From multiple searches:
- **Over 45,505 properties** in St. Charles Parish
- **Official Contact**: St. Charles Parish GIS Office
  - Website: https://www.stcharlesparish.gov/departments/geographic-information-systems-gis
  - Data requests: Submit public records request
- **Commercial Providers Available**:
  - Regrid (app.regrid.com)
  - Dynamo Spatial (dynamospatial.com)

---

## Data Access Options

### Option 1: Public Records Request (FREE)
**Contact**: St. Charles Parish GIS Office  
**Method**: Submit public records request via parish website  
**Timeline**: Unknown (government response times vary)  
**Format**: Likely Shapefile or GeoPackage  
**Pros**: Official, free, complete data  
**Cons**: Manual process, unknown timeline

### Option 2: Commercial Provider (PAID)
**Providers**: Regrid, Dynamo Spatial, CoreLogic  
**Timeline**: Immediate  
**Format**: Various (Shapefile, GeoJSON, etc.)  
**Cost**: ~$50-500 depending on provider  
**Pros**: Immediate access, standardized format  
**Cons**: Costs money, may have usage restrictions

### Option 3: Wait for API (UNCERTAIN)
**Platform**: geosync.io  
**Status**: Recently launched (Jan 2026)  
**Possibility**: May add public REST API in future  
**Timeline**: Unknown  
**Pros**: Free if/when available  
**Cons**: No guarantee they'll offer public API

---

## Recommendation

**For HITD Maps Coverage**:

1. **Short-term**: Skip St. Charles Parish for now
   - Focus on parishes with public APIs (we have 12/64 Louisiana parishes already)
   - Louisiana coverage: 18.8% (no statewide source exists)

2. **Medium-term**: Submit public records request
   - Free but manual process
   - Add to backlog for future processing

3. **Long-term**: Monitor geosync.io platform
   - Check periodically if they expose public REST APIs
   - Contact parish GIS office to request public API access

---

## Louisiana Parish Coverage Update

**Current Status**: 12/64 parishes (18.8%)

**Parishes We Have**:
- Ascension ✓
- Bossier ✓
- Caddo ✓
- Calcasieu ✓
- East Baton Rouge ✓
- Jefferson ✓
- Lafayette ✓
- Livingston ✓
- Orleans ✓
- St. Bernard ✓
- Tangipahoa ✓
- Terrebonne ✓

**Priority Missing** (with public APIs):
- Still searching for more parishes with accessible REST APIs
- Louisiana is unique: NO statewide parcel database
- Each parish uses different systems (ArcGIS, QGIS, proprietary)

**St. Charles Parish**:
- Population: 53,000
- Priority: Medium (moderate population)
- API Status: ❌ Not publicly accessible
- Action: Defer until public API available or submit records request

---

## Technical Details

### URLs Tested

| URL Pattern | Result |
|-------------|--------|
| `https://gis.stcharlesparish.la.gov/arcgis/rest/services` | DNS not found |
| `https://scpagis.stcharlesparish.la.gov/server/rest/services` | DNS not found |
| `https://stcharles.geosync.io/arcgis/rest/services` | Returns HTML (no REST API) |
| `https://gisportsl.com/arcgis/rest/services` | 404 Not Found |
| Port of South Louisiana servers | 404/500 errors |
| Louisiana state GIS servers | Connection timeout |

### GeoPortal Maps Backend Discovery

From `https://atlas.geoportalmaps.com/stcharles`:
```
Data Sources:
- Street mapping: http://192.168.60.130:8001/cgi-bin/qgis_mapserv.fcgi.exe?MAP=D:/GCTServices/StCharlesStreetmap.mxd.qgs
- Feature/parcel data: http://192.168.60.130:8001/cgi-bin/qgis_mapserv.fcgi.exe?MAP=D:/GCTServices/StCharles_Services.mxd.qgs
```

**Conclusion**: Internal QGIS Server, not publicly routable.

---

## Sources Referenced

- [St. Charles Parish GIS Office](https://www.stcharlesparish.gov/departments/geographic-information-systems-gis)
- [St. Charles Parish Assessor Property Search](https://stcharlesassessor.com/property-search-maps/)
- [GeoPortal Maps - St. Charles Atlas](https://atlas.geoportalmaps.com/stcharles)
- [Port of South Louisiana GIS](https://portsl.com/gis/)
- [Dynamo Spatial - St. Charles Parish](https://www.dynamospatial.com/c/st-charles-parish-la/parcel-data)
- [Regrid - St. Charles Parish](https://app.regrid.com/us/la/st-charles)

---

**Deployment Status**: ❌ **BLOCKED**  
**Reason**: No public ArcGIS REST API available  
**Next Steps**: Monitor for API access or submit public records request

---

*Generated: 2026-01-26*
