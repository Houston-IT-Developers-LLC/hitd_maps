# St. Tammany Parish, Louisiana - Deployment Report

**Date**: 2026-01-26
**Status**: FAILED - Endpoint Unreachable
**Parish**: St. Tammany Parish, Louisiana
**Population**: ~265,000 (3rd largest in Louisiana)
**Major Cities**: Slidell, Mandeville, Covington

---

## Summary

St. Tammany Parish parcel data deployment **FAILED** due to network connectivity issues with the parish GIS server. The endpoint exists and is documented, but all connection attempts timeout after 15-30 seconds.

---

## Data Source Investigation

### Identified Endpoint
- **Service**: St. Tammany Parish Assessor Office (STPAO) Parcels
- **URL**: `https://atlas.stpgov.org/server/rest/services/STPAO_Parcels/MapServer/1`
- **Type**: ArcGIS MapServer (layer 1)
- **Format**: Supports JSON, GeoJSON, PBF
- **Coordinate System**: NAD_1983_StatePlane_Louisiana_South_FIPS_1702_Feet
- **Last Updated**: 12/31/2024
- **Estimated Records**: 131,134 parcels (as of May 31, 2024)

### Contact Information
- **GIS Contact**: Michael McNeil, IT Services Director, St. Tammany Parish Assessor's Office
- **Email**: mmcneil@stpao.org, gis@stpgov.org
- **Web Portal**: https://atlas.geoportalmaps.com/st_tammany
- **Assessor Site**: https://stpao.org/all-tech/

---

## Connection Attempts

### Test 1: Basic HTTP Request
```bash
curl "https://atlas.stpgov.org/server/rest/services/STPAO_Parcels/MapServer/1?f=json"
```
**Result**: Connection timeout after 15 seconds

### Test 2: Python with Extended Timeout
```python
requests.get(url, timeout=30)
```
**Result**: Connection timeout after 30 seconds

### Test 3: Alternative Endpoints
Tested:
- `https://atlas.stpgov.org/server/rest/services/STPAO_Parcels/MapServer`
- `https://atlas.stpgov.org/server/rest/services`
- `https://gisportal.stpgov.org/arcgis/rest/services`

**Result**: All endpoints timeout (15s)

### Test 4: Custom Headers + Retry Logic
Added User-Agent, Referer headers and retry logic with 30s timeout.

**Result**: Connection hangs indefinitely

---

## Root Cause Analysis

### Likely Issues

1. **Firewall/IP Restriction**: The St. Tammany Parish GIS server appears to have IP-based access controls that block automated requests or requests from outside their network.

2. **Web Portal Integration**: The endpoint is referenced in the data sources registry as "Proprietary web portal - NO public REST API", suggesting it's designed for their web viewer only, not public API access.

3. **Server Configuration**: The server may require:
   - Specific authentication tokens
   - Session cookies from web viewer
   - Whitelisted IP addresses
   - VPN access to parish network

4. **Migration in Progress**: Search results indicate the assessor's office is migrating to geosync.io platform as of February 15, 2026. The current endpoint may be partially offline or restricted during migration.

---

## Alternative Data Access Options

### Option 1: Contact Parish GIS Department
- **Recommendation**: Email mmcneil@stpao.org or gis@stpgov.org to request:
  - Bulk parcel data download (Shapefile or GeoJSON)
  - API access credentials
  - Documentation on public REST API access

### Option 2: Commercial Data Provider
- **Regrid**: https://app.regrid.com/us/la/st-tammany
  - Offers parcel exports (Shapefile, Spreadsheet, KML)
  - Requires Pro account subscription
  - Data may be out of date

### Option 3: Wait for geosync.io Migration
- Platform migration scheduled for February 15, 2026
- New platform may offer better public API access
- Monitor https://stpao.org/all-tech/ for updates

### Option 4: Louisiana Statewide Source
- **Status**: No statewide Louisiana parcel database exists
- Louisiana organizes parcels at parish level only
- Each parish uses different systems (many proprietary)

---

## Data Sources Registry Status

**Current Status**: Listed as "PRIORITY 1 (hunting area)" but marked:
```json
{
  "status": "missing - proprietary portal",
  "format": "Proprietary web portal - NO public REST API",
  "notes": "Atlas/GeoPortal Maps proprietary system. No standard ArcGIS REST access. May require manual contact with assessor."
}
```

This deployment attempt **confirms** the registry assessment that the endpoint is not publicly accessible via standard REST API methods.

---

## Louisiana Parish Coverage Impact

### Current Louisiana Coverage
- **Parishes Deployed**: 7/64 (11%)
  - East Baton Rouge (Baton Rouge)
  - Orleans (New Orleans)
  - Jefferson
  - Caddo (Shreveport)
  - Lafayette
  - Calcasieu (Lake Charles)
  - Terrebonne

### Priority Missing (Population > 100K)
1. **St. Tammany** - 265K - BLOCKED (this report)
2. **Livingston** - 142K - Atlas/GeoPortal proprietary
3. **Tangipahoa** - 133K - Custom portal, no REST
4. **Rapides (Alexandria)** - 130K - Proprietary RAPC GIS
5. **Bossier** - 128K - Atlas/GeoPortal proprietary

### Challenge
Louisiana has **no statewide parcel database**. Each parish:
- Uses different GIS vendors
- Has different access policies
- Many use proprietary web-only viewers
- Few offer standard ArcGIS REST APIs

---

## Recommendations

### Immediate Actions
1. **Email parish GIS contacts** requesting bulk data export or API credentials
2. **Monitor geosync.io migration** - new platform may be more open
3. **Document as BLOCKED** in data sources registry
4. **Focus on other Louisiana parishes** with working endpoints

### Long-term Strategy
1. **Build relationships** with Louisiana parish assessors
2. **Advocate for open data** - cite successful parishes (East Baton Rouge, Jefferson)
3. **Explore state-level coordination** - Louisiana GIS office coordination
4. **Commercial partnerships** - Consider Regrid or other aggregators for Louisiana

---

## Deployment Metrics

| Metric | Value |
|--------|-------|
| **Endpoint Found** | Yes |
| **Endpoint Accessible** | No |
| **Connection Timeout** | 15-30 seconds |
| **Parcels Downloaded** | 0 |
| **PMTiles Created** | No |
| **R2 Upload** | N/A |
| **CDN URL** | N/A |

---

## Next Steps

1. Send email to St. Tammany Parish GIS contacts
2. Mark in registry as "BLOCKED - Firewall/Auth Required"
3. Move to next Louisiana parish (check Livingston, Tangipahoa alternatives)
4. Investigate parishes with confirmed working endpoints
5. Consider FOIA request for bulk data export

---

## Resources

- [St. Tammany Parish Assessor GIS](https://stpao.org/all-tech/)
- [St. Tammany GIS Portal](https://atlas.geoportalmaps.com/st_tammany)
- [MapServer Endpoint](https://atlas.stpgov.org/server/rest/services/STPAO_Parcels/MapServer/1)
- [Louisiana GIS Data Portal](https://www.gis.la.gov/)
- [Regrid - St. Tammany](https://app.regrid.com/us/la/st-tammany)

---

**Report Generated**: 2026-01-26
**Agent**: Claude Code
**Task ID**: St. Tammany Parish Deployment
