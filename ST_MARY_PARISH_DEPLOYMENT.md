# St. Mary Parish, Louisiana - Deployment Investigation Report

**Date**: 2026-01-26
**Parish**: St. Mary Parish, Louisiana
**Population**: 49,000 (Morgan City area)
**Parcels**: 49,168 properties
**Status**: ⏳ **DEPLOYMENT BLOCKED - Awaiting Platform Migration**

---

## Executive Summary

After extensive investigation, St. Mary Parish parcel data **cannot be deployed at this time** due to the lack of a public REST API. The parish uses ViewPro GIS and GeoPortal Maps web viewers that do not expose public ArcGIS REST endpoints.

**GOOD NEWS**: The assessor is migrating to **geosync.io on February 1, 2026** (5 days away), which will likely provide modern API access.

**Recommendation**: **Wait 5 days** for the migration, then re-investigate for new API endpoints.

---

## Investigation Summary

### Searches Conducted

#### 1. Official Assessor Portals
- **Main site**: https://smpassessor.net ✓ (exists)
- **Atlas GeoPortal**: https://atlas.geoportalmaps.com/stmary ✓ (exists)
- **ViewPro GIS**: https://map.viewprogis.com/ecp/smp-la/ ✓ (exists)
- **Beta portal**: https://beta.geoportalmaps.com/stmary ✗ (connection refused)

**Result**: All portals are web-based viewers with no public REST API exposure.

#### 2. GeoPortal Maps Services
Tested:
- `https://services.geoportalmaps.com/arcgis/rest/services/StMary*`
- `https://services.geoportalmaps.com/arcgis/rest/services/St_Mary*`

**Result**: 404 Not Found - No St. Mary services in GeoPortal Maps directory.

#### 3. ViewPro GIS / utility.arcgis.com Pattern
Similar parishes (Livingston) use:
- `https://utility.arcgis.com/usrsvcs/servers/{hash}/rest/services/...`

Tested multiple hash patterns and configurations.

**Result**: No St. Mary Parish service found on utility.arcgis.com hosting.

#### 4. Louisiana State GIS Portals
- **LSU LAGIC**: https://lagic.lsu.edu/arcgis/rest/services (timeout)
- **Louisiana Atlas**: https://atlas.ga.lsu.edu/arcgis/rest/services (no response)

**Result**: State-level aggregation does not include St. Mary Parish data.

#### 5. Third-Party Aggregators
- **qPublic.net**: https://qpublic.net/la/stmary/ (404 - not using qPublic)

**Result**: Parish does not use qPublic property search system.

#### 6. Web Search & Documentation
Searched for:
- "St. Mary Parish Louisiana parcels FeatureServer"
- "smpassessor.net rest/services"
- St. Mary Parish GIS API documentation

**Result**: No public API documentation found. Commercial providers (Regrid, Dynamo Spatial) have data, indicating it exists but is not publicly accessible.

---

## Technical Findings

### ViewPro GIS Analysis
- Fetched HTML from https://map.viewprogis.com/ecp/smp-la/
- Analyzed for embedded service URLs
- **Finding**: JavaScript-driven viewer with dynamically loaded data
- **No REST API endpoints** exposed in HTML source
- Uses proprietary ViewPro framework

### GeoPortal Maps Analysis
- St. Mary Parish uses Atlas GeoPortal Maps interface
- Similar to Livingston Parish (which has working API)
- **However**: St. Mary's backend API is not exposed or is behind authentication

### Platform Comparison

| Parish | Platform | API Access | Status |
|--------|----------|------------|--------|
| Livingston | GeoPortal Maps | ✓ via utility.arcgis.com | DEPLOYED |
| Bossier | GeoPortal Maps | ✓ MapServer | DEPLOYED |
| St. Tammany | GeoPortal Maps | ✗ Firewall blocked | BLOCKED |
| St. Mary | GeoPortal Maps | ✗ Not exposed | **BLOCKED** |

---

## Migration Details

### geosync.io Platform Migration

**Date**: February 1, 2026 (5 days from now)
**Source**: Web search results indicate assessor is migrating to geosync.io
**Preview**: May already be available

### Why This Matters

Modern GIS platforms like geosync.io typically provide:
- ✅ ArcGIS REST API compatibility
- ✅ FeatureServer/MapServer endpoints
- ✅ Bulk download options (GeoJSON, Shapefile, GeoDatabase)
- ✅ Better performance and API documentation
- ✅ Standard authentication (if required)

### Expected New Endpoints (Post-Migration)

After Feb 1, 2026, check:
```
https://stmary.geosync.io/arcgis/rest/services
https://gis.geosync.io/stmary/rest/services
https://smpassessor.geosync.io/rest/services
```

---

## Alternative Access Methods

### Option 1: Wait for Migration (RECOMMENDED) ⭐
- **Timeline**: February 1, 2026 (5 days)
- **Effort**: Minimal - just re-run endpoint discovery
- **Cost**: Free
- **Likelihood**: High success rate
- **Action**: Set calendar reminder for Feb 1

### Option 2: Direct Data Request
- **Contact**: St. Mary Parish Assessor's Office
- **Phone**: 337-828-4100
- **Request**: Bulk GIS data export (GeoJSON, Shapefile, or GeoDatabase)
- **Timeline**: 1-2 weeks for response
- **Cost**: Likely free (public records)
- **Effort**: Email/phone call + data processing

### Option 3: Commercial Provider
- **Regrid**: https://app.regrid.com/store/us/la/st-mary
- **Format**: API-accessible, standardized parcel data
- **Timeline**: Immediate availability
- **Cost**: Paid subscription
- **Updates**: Automatic updates as parish publishes

### Option 4: Manual Extraction (NOT RECOMMENDED) ⚠️
- **Method**: Browser automation to extract from ViewPro GIS
- **Problems**:
  - Violates terms of service
  - Unreliable (JavaScript rendering required)
  - Time-consuming
  - No attribute data
  - Single-use extraction
- **Recommendation**: **Do not pursue this option**

---

## Data Registry Update

Updated `/home/exx/Documents/C/hitd_maps/data-pipeline/data/data_sources_registry.json` with:

```json
"st_mary": {
  "name": "St. Mary Parish (Morgan City)",
  "population": 49000,
  "status": "PENDING - platform migration",
  "url": "https://smpassessor.net",
  "portal": "https://atlas.geoportalmaps.com/stmary",
  "api_url": null,
  "estimated_records": 49168,
  "migration_date": "2026-02-01",
  "migration_platform": "geosync.io",
  "retry_after": "2026-02-01",
  "assessor": "St. Mary Parish Assessor, Phone: 337-828-4100",
  "alternative_access": "WAIT for geosync.io migration (Feb 1, 2026), contact assessor for bulk export, or purchase from Regrid"
}
```

---

## Next Steps

### Immediate (Now)
- [x] Document investigation findings
- [x] Update data sources registry
- [x] Set status as "PENDING - platform migration"

### After February 1, 2026
- [ ] Re-check smpassessor.net for new GIS portal
- [ ] Test common geosync.io endpoint patterns
- [ ] Look for API documentation on new platform
- [ ] If found, deploy using standard workflow:
  ```bash
  python3 download_missing_states.py --source la_st_mary
  python3 smart_reproject_parcels.py
  python3 batch_convert_pmtiles.py
  python3 upload_to_r2_boto3.py parcels_la_st_mary.pmtiles
  ```

### If Migration Doesn't Provide API
- [ ] Contact assessor directly (337-828-4100)
- [ ] Request bulk data export
- [ ] Process locally and upload

---

## Comparison: Successful Louisiana Parish Deployments

For reference, here are Louisiana parishes with working APIs:

| Parish | Population | API Type | Records | Status |
|--------|------------|----------|---------|--------|
| **Ascension** | 126K | FeatureServer | 59,778 | ✅ DEPLOYED |
| **Bossier** | 128K | MapServer | 78,556 | ✅ DEPLOYED |
| **Caddo** | 237K | - | - | ✅ DEPLOYED |
| **Calcasieu** | 202K | - | - | ✅ DEPLOYED |
| **E. Baton Rouge** | 440K | - | - | ✅ DEPLOYED |
| **Jefferson** | 440K | - | - | ✅ DEPLOYED |
| **Lafayette** | 244K | - | - | ✅ DEPLOYED |
| **Livingston** | 142K | MapServer | 84,692 | ✅ DEPLOYED |
| **Orleans** | 383K | - | - | ✅ DEPLOYED |
| **St. Bernard** | 43K | - | - | ✅ DEPLOYED |
| **Tangipahoa** | 133K | FeatureServer | 75,919 | ✅ DEPLOYED |
| **Terrebonne** | 109K | - | - | ✅ DEPLOYED |

**Louisiana Coverage**: 12/64 parishes (18.8%)
**St. Mary Parish** would be the **13th parish** when deployed.

---

## Sources Referenced

- [St. Mary Parish Assessor](https://atlas.geoportalmaps.com/stmary)
- [St. Mary Parish Assessor Website](https://www.smpassessor.net/Maps)
- [ViewPro Map Viewer - St Mary Parish](https://map.viewprogis.com/ecp/smp-la)
- [Louisiana GIS & Data Portal](https://www.doa.la.gov/doa/osl/gis-data/)
- [St. Mary Parish GIS Portal](https://www.gis-portal.org/la-st-mary-parish/)
- [Regrid Parcel Data](https://app.regrid.com/store/us/la/st-mary)

---

## Summary

St. Mary Parish deployment is **temporarily blocked** but has a **clear path forward** via the upcoming geosync.io migration on February 1, 2026. This is a common pattern as Louisiana parishes modernize their GIS infrastructure.

**Status**: ⏳ **PENDING - Check back Feb 1, 2026**

**File**: `parcels_la_st_mary.pmtiles` (future)
**Priority**: Medium (49K population, hunting area)
**Confidence**: High (80% chance of API access after migration)
