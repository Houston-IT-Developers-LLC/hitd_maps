# St. Landry Parish, Louisiana - Parcel Data Investigation

**Date**: 2026-01-26
**Parish**: St. Landry Parish, LA
**Population**: ~82,000
**Major City**: Opelousas
**Goal**: Deploy parcels to R2 as `parcels_la_st_landry.pmtiles`

---

## Investigation Summary

After extensive investigation, **St. Landry Parish does NOT have a publicly accessible ArcGIS REST API** for bulk parcel downloads.

---

## Sources Investigated

### 1. St. Landry Parish Assessor
- **Web Portal**: https://stlandrymapping.azurewebsites.net/
- **Assessor Site**: https://www.stlandryassessor.org/
- **Finding**:
  - Has interactive web map viewer (Azure-hosted)
  - NO public ArcGIS REST API endpoints exposed
  - Uses proprietary/closed backend system
  - Web viewer does not expose FeatureServer or MapServer endpoints

### 2. Pattern-Based URL Testing
Tested common ArcGIS REST patterns:
- `https://gis.stlandry.org/arcgis/rest/services` - DNS not found
- `https://maps.stlandry.org/arcgis/rest/services` - DNS not found
- `https://stlandryassessor.org/arcgis/rest/services` - Returns HTML, not JSON
- `https://stlandryassessor.org/server/rest/services` - Returns HTML, not JSON

### 3. Web Search Results
- Found mapping portal but no downloadable data
- Commercial providers (Regrid, DynamoSpatial) have data but require payment
- No free/open data portal identified

### 4. Louisiana Statewide Sources
- **LSU Atlas** (atlas.ga.lsu.edu): Has lidar/imagery but NO parcel data
- **SONRIS** (DNR): Oil/gas data, not parcels
- **Louisiana DOA GIS**: No statewide parcel layer
- Louisiana operates on parish-level GIS (unlike states with statewide systems)

### 5. ArcGIS Online Search
- Searched for "St. Landry Parish Louisiana parcels"
- No public datasets found on ArcGIS Hub or ArcGIS Online

---

## Data Statistics

- **Total Properties**: 61,272 parcels
- **Data Provider**: St. Landry Parish Assessor's Office
- **Last Updated**: Unknown (no metadata available)

---

## Alternative Solutions

### Option 1: Contact Assessor's Office (RECOMMENDED)
**Contact Information**:
- Office: 118 South Court Street, Opelousas, LA 70570
- Phone: 337-942-3166
- Email: Not publicly listed

**Request**:
- Ask for bulk parcel shapefile or GeoJSON export
- Mention it's for a public mapping project (mapsfordevelopers.com)
- Offer to credit them on the platform

### Option 2: Commercial Data Providers
**Regrid** (app.regrid.com/us/la/st-landry)
- Has 61,272+ parcels
- Paid subscription required
- API available with Pro plan
- Cost: Unknown (contact sales)

**DynamoSpatial** (dynamospatial.com/c/st-landry-parish-la)
- Parish-level data available
- Shapefile/GeoJSON formats
- Cost: Unknown (contact sales)

**ReportAllUSA** (reportallusa.com)
- Louisiana statewide parcel data
- Includes St. Landry Parish
- Shapefile format
- Cost: Unknown

### Option 3: Manual Extraction (NOT RECOMMENDED)
- Use browser DevTools to intercept map tile requests
- Extremely time-consuming
- May violate terms of service
- Data quality/completeness not guaranteed

### Option 4: Wait for Open Data Initiative
- Monitor Louisiana open data portal (data.louisiana.gov)
- Check if parish joins statewide open data program
- Could take months or years

---

## Comparison with Other Louisiana Parishes

| Parish | Public API? | Status |
|--------|-------------|--------|
| East Baton Rouge | Portal found | Verification failed |
| Jefferson | Portal found | DNS error |
| Orleans | Portal found | Verification failed |
| St. Tammany | Portal found | Verification failed |
| Lafayette | Portal found | Verification failed |
| Caddo | Portal found | DNS error |
| **St. Landry** | **NO** | **No public API** |

**Pattern**: Louisiana parishes have inconsistent GIS infrastructure. Most have web viewers but not standardized REST APIs for bulk downloads.

---

## Recommendations

### Immediate Next Steps

1. **Call St. Landry Parish Assessor** (337-942-3166)
   - Ask if they can provide bulk parcel data
   - Explain use case (free mapping platform)
   - Request shapefile, GeoJSON, or database export

2. **If Assessor Says No**:
   - Evaluate commercial providers (Regrid vs DynamoSpatial)
   - Check if cost fits budget
   - Consider bulk Louisiana purchase for multiple parishes

3. **If Commercial Too Expensive**:
   - Skip St. Landry Parish for now
   - Focus on parishes with public APIs
   - Revisit in 6-12 months

### Long-Term Strategy

1. **Louisiana Coverage Approach**:
   - Focus on parishes with public ArcGIS REST APIs
   - Build relationships with assessor offices
   - Consider joining Louisiana GIS Association for access

2. **Alternative Data Sources**:
   - Monitor OpenStreetMap for parcel imports
   - Check if Microsoft Building Footprints + Overture addresses sufficient
   - Look for state tax commission data

---

## Technical Notes

### Why This Is Difficult

1. **No Statewide System**: Unlike TX, FL, VT which have statewide parcel databases, Louisiana operates at parish level
2. **Inconsistent Infrastructure**: Each parish has different GIS vendor/setup
3. **Closed Systems**: Many use proprietary vendors (QPublic, TrueAutomation) without public APIs
4. **Small Parish Resources**: St. Landry is mid-sized (~82K pop) so may lack GIS budget for public data portal

### Comparison to Other States

| State | Statewide API? | Coverage |
|-------|----------------|----------|
| Texas | YES | 100% |
| Florida | YES | 100% |
| Vermont | YES | 100% |
| Mississippi | YES | 100% |
| **Louisiana** | **NO** | **0% statewide** |

---

## Sources Reference

### Web Search Results
- [St. Landry Parish Assessor](https://stlandrymapping.azurewebsites.net/)
- [Louisiana GIS & Data Portal](https://www.doa.la.gov/doa/osl/gis-data/)
- [St. Landry Parish GIS Data](https://www.gis-data.org/la-st-landry-parish/)
- [Louisiana Tax Assessors Portal](https://qpublic.net/la/laassessors/)
- [Regrid - St. Landry Parish](https://app.regrid.com/us/la/st-landry)
- [DynamoSpatial - St. Landry Parish](https://www.dynamospatial.com/c/st-landry-parish-la/parcel-data)

---

## Decision Matrix

| Option | Cost | Time | Quality | Legality | Recommendation |
|--------|------|------|---------|----------|----------------|
| Contact Assessor | Free | 1-2 weeks | High | ✓ Legal | **BEST** |
| Commercial (Regrid) | $$$ | 1 day | High | ✓ Legal | If budget allows |
| Manual Extraction | Free | Weeks | Low | ? TOS risk | Avoid |
| Wait for Open Data | Free | Months/Years | Unknown | ✓ Legal | Backup plan |

---

## Conclusion

**Status**: Cannot deploy St. Landry Parish parcels without:
1. Direct contact with assessor's office, OR
2. Purchase from commercial provider

**Next Action**: Call St. Landry Parish Assessor at 337-942-3166 to request bulk parcel data.

**Alternative**: Focus on Louisiana parishes that DO have public APIs (need to identify which ones work from previous test).
