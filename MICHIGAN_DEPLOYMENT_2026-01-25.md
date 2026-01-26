# Michigan County Parcel Deployment Summary
**Date:** 2026-01-25
**Session:** Top Priority Michigan Counties Deployment

---

## Mission

Deploy parcel data for top missing Michigan counties by population priority:
1. ~~Ingham (284K pop) - Lansing~~ - Endpoint not discovered
2. ~~Saginaw (190K pop)~~ - Endpoint not discovered
3. ~~Berrien (154K pop)~~ - Endpoint not discovered
4. ~~Jackson (160K pop)~~ - Endpoint found (MapServer), not deployed
5. ~~Bay (103K pop)~~ - Endpoint not discovered
6. ~~Muskegon (175K pop)~~ - **ALREADY DEPLOYED** (existing file)
7. **Monroe (154K pop)** - **✓ DEPLOYED**

---

## Deployed Counties

### Monroe County ✓
- **Population:** 154,000
- **Parcels:** 7,731
- **File Size:** 3.5 MB (PMTiles)
- **Source:** https://gis.monroemi.gov/server/rest/services/Hosted/Parcels_V2/FeatureServer/0
- **Format:** ArcGIS FeatureServer
- **CDN URL:** https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels_mi_monroe.pmtiles
- **Status:** Live on R2, added to valid_parcels.json

---

## Endpoints Discovered (Not Yet Deployed)

### Jackson County
- **Population:** 160,000
- **Source:** https://gis.mijackson.org/countygis/rest/services/RealEstate/RealEstateParcels/MapServer/0
- **Type:** MapServer (not FeatureServer)
- **Issue:** MapServer has different query capabilities - query with returnCountOnly failed
- **Next Step:** Implement MapServer-specific download approach

---

## Endpoints Still Needed

### 1. Ingham County (Lansing) - 284K pop
- **Viewer:** https://ingham-equalization.rsgis.msu.edu/
- **Host:** MSU Remote Sensing & GIS (RS&GIS)
- **Server:** https://enterprise.rsgis.msu.edu/server/rest/services
- **Status:**
  - Ingham folder exists on MSU server but contains no services
  - 414 total services on MSU server, none explicitly named for Ingham parcels
  - Viewer page doesn't expose REST endpoint in HTML source
- **Options:**
  - Contact MSU RS&GIS or Ingham County Equalization
  - Use browser dev tools to intercept XHR requests from viewer
  - Search MSU server's 414 services more systematically

### 2. Saginaw County - 190K pop
- **Portal:** https://www.sagagis.org/ (Saginaw Area GIS Authority)
- **Viewer:** https://app.fetchgis.com/?currentMap=saginaw (FetchGIS)
- **Status:**
  - Uses FetchGIS viewer (proprietary interface)
  - Backend likely ArcGIS Server but endpoint not exposed
- **Options:**
  - Check FetchGIS network requests
  - Contact SAGA GIS directly
  - Look for alternative county data portals

### 3. Berrien County - 154K pop
- **Viewer:** https://beacon.schneidercorp.com/Application.aspx?AppID=346
- **System:** Beacon by Schneider Corporation
- **Status:**
  - Proprietary Beacon system (not standard ArcGIS)
  - May have REST API but not publicly documented
- **Options:**
  - Contact Berrien County GIS
  - Research Beacon API documentation
  - Alternative: download from third-party aggregators (Regrid, etc.)

### 4. Bay County - 103K pop
- **Portal:** https://data-baycountygis.opendata.arcgis.com/
- **Server:** https://services.arcgis.com/rQ8M8TYeQeYBDHpI/arcgis/rest/services
- **Status:**
  - ArcGIS Open Data portal exists
  - Org ID rQ8M8TYeQeYBDHpI found but server returned no parcel-named services
  - Dataset catalog search returned no parcel datasets
- **Options:**
  - Browse Open Data portal manually for parcel datasets
  - Check different ArcGIS service folders
  - Contact Bay County GIS department

---

## Michigan Coverage Update

**Before:** 12% (10 counties)
**After:** 13% (11 counties)

### Current Michigan Files
1. parcels_mi (legacy)
2. parcels_mi_arenac
3. parcels_mi_kent
4. parcels_mi_kent_v2
5. parcels_mi_macomb
6. parcels_mi_midland
7. **parcels_mi_monroe** ← NEW
8. parcels_mi_muskegon (already existed)
9. parcels_mi_oakland
10. parcels_mi_oakland_v2
11. parcels_mi_ottawa
12. parcels_mi_wayne

### Total Michigan Counties: 83
### Covered: 11 counties (13%)
### Major Metro Covered: Detroit, Grand Rapids
### Major Metro Missing: Lansing (Ingham)

---

## Technical Notes

### Tools Created
- `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/download_michigan_counties.py`
  - Custom download script for Michigan counties
  - Supports both FeatureServer and MapServer (partial)
  - Parallel download with 10 workers
  - Auto-chunking for large datasets

### Challenges Encountered
1. **MapServer vs FeatureServer:** Jackson County uses MapServer which doesn't support the same query operations as FeatureServer
2. **Hidden Endpoints:** Many counties use viewers that don't expose their backend REST APIs in obvious ways
3. **Proprietary Systems:** Beacon (Berrien) and FetchGIS (Saginaw) may not use standard ArcGIS REST APIs
4. **Empty Folders:** MSU RS&GIS has an "Ingham" folder but it contains no services

### Search Resources Used
- [Michigan GIS Open Data](https://gis-michigan.opendata.arcgis.com/)
- [Ingham County Tax Viewer](https://ingham-equalization.rsgis.msu.edu/)
- [Jackson County GIS](https://gis.mijackson.org/)
- [Monroe County GIS Portal](https://gis.monroemi.gov/portal)
- [Bay County Open Data](https://data-baycountygis.opendata.arcgis.com/)
- [Saginaw Area GIS Authority](https://www.sagagis.org/)
- [Berrien County Beacon](https://beacon.schneidercorp.com/)

---

## Next Steps

### Immediate (High Priority)
1. **Jackson County:** Implement MapServer download support
   - Test export capability: `/MapServer/0/query?where=1=1&outFields=*&f=json&resultRecordCount=1`
   - May need to use exportImage or different query method

2. **Ingham County:** Network analysis
   - Open viewer in browser dev tools
   - Monitor Network tab for XHR requests
   - Capture actual service endpoint being called
   - Alternative: Email ingham-equalization@rsgis.msu.edu

### Short Term
3. **Bay County:** Manual portal exploration
   - Visit https://data-baycountygis.opendata.arcgis.com/
   - Search for "parcel" or "tax" datasets manually
   - Check dataset API resources if found

4. **Saginaw County:** FetchGIS network capture
   - Load https://app.fetchgis.com/?currentMap=saginaw
   - Monitor network requests to find backend server
   - May be standard ArcGIS once discovered

5. **Berrien County:** Contact county directly
   - Beacon system may require special access
   - Alternative: Use third-party parcel providers

### Future Enhancements
- Add MapServer support to download script
- Create viewer-to-endpoint discovery tool
- Document all Michigan county GIS systems for future reference

---

## Files Modified
- `/home/exx/Documents/C/hitd_maps/data-pipeline/data/valid_parcels.json` - Added parcels_mi_monroe
- `/home/exx/Documents/C/hitd_maps/data-pipeline/data/data_sources_registry.json` - Added Monroe County details + priority counties section
- `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/download_michigan_counties.py` - Created (new)

---

## Impact

### Coverage Improvement
- **+1 Michigan county** (Monroe)
- **+7,731 parcels** (Monroe)
- **+3.5 MB** deployed data
- Michigan now at **13% coverage** (was 12%)

### Strategic Value
- Validated FeatureServer discovery and deployment workflow
- Identified technical blockers for remaining counties
- Created reusable Michigan download script
- Documented all priority county GIS systems and their challenges

### User Value
- Monroe County (154K population) users can now access parcel data
- Southeast Michigan coverage improved (Monroe borders Ohio and Detroit metro)

---

## Conclusion

**Success:** 1 of 7 target counties deployed (Monroe County)

**Blockers:**
- 4 counties need endpoint discovery (Ingham, Saginaw, Berrien, Bay)
- 1 county needs MapServer support (Jackson)
- 1 county already existed (Muskegon)

**Key Learning:** Most Michigan counties use proprietary viewers or non-standard systems, making REST API discovery more challenging than typical ArcGIS Online deployments.

**Recommendation:** For the remaining counties, direct county contact or browser-based endpoint discovery will likely be faster than automated searches.
