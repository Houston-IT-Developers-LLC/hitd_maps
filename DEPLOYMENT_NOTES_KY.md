# Kentucky County Deployment - 2026-01-25

## Completed Deployments

### Daviess County (Owensboro)
- **Status**: DEPLOYED ✓
- **Population**: 102,000
- **Parcels**: 47,923
- **File**: `parcels_ky_daviess.pmtiles` (25 MB)
- **Source**: Owensboro Metropolitan Planning Commission (OMPC)
- **API**: https://gis.owensboro.org/arcgis/rest/services/OMPC/OMPC/MapServer/2
- **CDN**: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_ky_daviess.pmtiles
- **Deployed**: 2026-01-25

## Previously Deployed (Already Have)

1. **Kenton County** - 169K pop (Covington/Cincinnati) ✓
2. **Boone County** - 135K pop (Florence) ✓  
3. **Warren County** - 134K pop (Bowling Green) ✓
4. **Jefferson County** - 782K pop (Louisville) ✓
5. **Fayette County** - 323K pop (Lexington) ✓

## Data Gaps - Requires Manual Investigation

### Hardin County (Elizabethtown)
- **Status**: NOT DEPLOYED ❌
- **Population**: 110,000
- **Priority**: HIGH
- **Issue**: Kentucky state GIS server service appears down/moved
  - Historical URL was: `http://kygisserver.ky.gov/.../Ky_PVA_Hardin_Parcels_WGS84WM/MapServer`
  - Service returns 404 error as of 2026-01-25
  - Not available in KyGovMaps Open Data Portal
- **Next Steps**:
  1. Contact Hardin County GIS directly: https://www.hardincountyky.gov/336/Geographic-Information-Systems-GIS
  2. Check for updated service URL on KyGeoNet
  3. Consider LOJIC regional service (covers Hardin but endpoint not found)
  4. Alternative: Contact Hardin County PVA at (270) 765-2129

## Kentucky Coverage Summary

**Total Counties**: 120  
**Counties Deployed**: 6  
**Coverage**: 5%

**Files**:
- parcels_ky (legacy)
- parcels_ky_boone
- parcels_ky_daviess (NEW)
- parcels_ky_fayette
- parcels_ky_jefferson
- parcels_ky_kenton
- parcels_ky_warren

## Updated Files

- `data-pipeline/data/valid_parcels.json` - Added parcels_ky_daviess
- `data-pipeline/data/coverage_status.json` - Updated KY to 6 counties, 5%, 251 total files
- `data-pipeline/data/data_sources_registry.json` - Added Daviess County source info
