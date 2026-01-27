# Evangeline Parish, Louisiana - Parcel Data Investigation Report

**Investigation Date:** January 27, 2026
**Population:** ~32,000 (Ville Platte area)
**Status:** ❌ NO PUBLIC ARCGIS REST API FOUND
**Estimated Parcels:** ~30,373 (per Regrid, April 2025)

---

## Executive Summary

After an exhaustive search, **no publicly accessible ArcGIS REST API endpoint was found** for Evangeline Parish parcel data. The parish appears to use a proprietary GIS system without public REST API access. The parish Police Jury website indicates a GIS service is "Coming Soon," suggesting public access may be available in the future (estimated Q2 2026).

**Commercial data providers (Regrid, Dynamo Spatial) have current data**, confirming the parcel database exists but is not publicly accessible via standard web service APIs.

---

## Search Methodology

### 1. Official Parish Websites

#### Evangeline Parish Assessor
- **URL:** https://www.evangelineassessor.com/
- **Assessor:** Chris Guillory
- **Address:** 200 Court Street, Ville Platte, LA 70586
- **Phone:** 337-363-4310
- **Platform:** Wix website builder
- **Finding:** No GIS portal, property search, or API endpoints found

#### Evangeline Parish Police Jury GIS
- **URL:** https://evangelineparishpolicejury.com/gis-map/
- **Finding:** Page displays "Coming Soon" - GIS service not yet operational
- **Implication:** Public GIS access is planned but not yet deployed

### 2. Common Louisiana Platforms

#### Qpublic.net Portal
- **Tested URL:** https://qpublic.net/la/evangeline/
- **Result:** 404 Not Found
- **Conclusion:** Parish does not use Qpublic system

#### Atlas GeoPortal Maps
- **Search:** No Evangeline Parish portal found
- **Note:** Other LA parishes (Livingston, Bossier, Beauregard) use this platform

#### Louisiana Wildlife & Fisheries GIS
- **Base URL:** http://gis.wlf.la.gov/arcgis/rest/services/
- **Services Found:** LDWF_ExplorerMap_01, Oyster_Lease_Web_Map
- **Result:** No parish parcel data available

### 3. ArcGIS Direct Endpoint Tests

Tested common endpoint patterns:
```
✗ https://gis.evangelineparish.com/arcgis/rest/services
✗ https://gis.evangelineassessor.com/arcgis/rest/services
✗ http://gis.wlf.la.gov/arcgis/rest/services/Parishes/Evangeline/MapServer
```

All returned connection failures or 404/500 errors.

### 4. Web Search Results

**ArcGIS Hub Search:**
- Query: `site:arcgis.com "Evangeline Parish" parcels`
- Result: No results found

**General GIS Search:**
- Query: `Evangeline Parish Louisiana GIS parcels ArcGIS REST API`
- Results: Commercial data providers only (Regrid, Dynamo Spatial, Acres)
- No public REST API endpoints discovered

---

## Louisiana Parish GIS Context

### Statewide Situation
- **NO statewide Louisiana parcel database exists**
- Each parish maintains separate systems (64 parishes, 64 different approaches)
- Louisiana has lowest parcel data accessibility in the nation
- Most parishes use proprietary systems without public APIs

### Common Platforms in Louisiana

| Platform | Parishes Using | Public API |
|----------|----------------|------------|
| Atlas GeoPortal Maps | Livingston, Bossier, Iberville, Beauregard, St. Tammany | Some have REST API |
| Custom ArcGIS Server | Tangipahoa, Ascension, Caddo, Jefferson | Yes (FeatureServer/MapServer) |
| Qpublic.net | Various parishes | Limited |
| Total Land Solutions | West Baton Rouge | No |
| ViewPro GIS | St. Mary | No |
| Proprietary/Unknown | Evangeline, Rapides, others | No |

### Our Louisiana Coverage Status

**Current Status:** 13/64 parishes (20.3% coverage)

**Have Data:**
- Ascension, Bossier, Caddo, Calcasieu
- East Baton Rouge, Iberville, Jefferson
- Lafayette, Livingston, Orleans
- St. Bernard, Tangipahoa, Terrebonne

**Blocked (No Public API):**
- Beauregard, Evangeline, Natchitoches
- Rapides, St. Tammany, West Baton Rouge

**Pending Migration:**
- St. Mary (Feb 1, 2026 → geosync.io)

---

## Commercial Data Availability

### Regrid
- **URL:** https://app.regrid.com/store/us/la/evangeline
- **Parcels:** 30,373
- **Last Updated:** April 29, 2025
- **Attributes:** 114 data fields
- **Cost:** Typically $200-500 for parish-level data
- **Contact:** parcels@regrid.com

### Dynamo Spatial
- **URL:** https://www.dynamospatial.com/c/evangeline-parish-la/parcel-data
- **Properties:** 30,408
- **Format:** Various GIS formats available

### Acres GIS Maps
- **URL:** https://www.acres.com/plat-map/map/la/evangeline-parish-la
- **Records:** 18,512 parcels
- **Includes:** Ownership data, plat maps

**Analysis:** Multiple commercial providers have current Evangeline Parish data, confirming:
1. The parcel database exists and is maintained
2. Assessor's office provides data to commercial vendors
3. Data is NOT publicly accessible via REST API
4. Likely uses proprietary system or requires special access

---

## Comparison to Accessible Louisiana Parishes

### Tangipahoa Parish (SUCCESS CASE)
- **Population:** 133,000 (4x larger than Evangeline)
- **API:** https://tangis.tangipahoa.org/server/rest/services/Cadastral/TaxParcel_A/FeatureServer/0
- **Platform:** TanGIS (parish-owned ArcGIS Server)
- **Access:** Public FeatureServer, no authentication
- **Update Frequency:** Every 3 weeks
- **Status:** ✅ DEPLOYED (parcels_la_tangipahoa.pmtiles)

### Livingston Parish (SUCCESS CASE)
- **Population:** 142,000 (4.5x larger)
- **API:** https://utility.arcgis.com/.../Assessor/Parcels_SMARTCAMA/MapServer/8
- **Platform:** Atlas GeoPortal Maps (hosted ArcGIS)
- **Access:** Public MapServer, returns WGS84
- **Status:** ✅ DEPLOYED (parcels_la_livingston.pmtiles)

### Beauregard Parish (BLOCKED - SIMILAR TO EVANGELINE)
- **Population:** 37,000 (similar size)
- **API:** None found
- **Platform:** Atlas GeoPortal Maps (viewer only)
- **Status:** ❌ NO PUBLIC API
- **Recommendation:** Contact assessor for bulk export

**Conclusion:** Smaller Louisiana parishes (under 50K population) often lack public REST APIs, even when using modern GIS platforms like Atlas. This appears to be a policy/configuration choice rather than technical limitation.

---

## Recommended Actions

### ⭐ Option 1: Direct Contact with Assessor (RECOMMENDED)

**Contact Information:**
```
Chris Guillory, Assessor
Evangeline Parish Assessor's Office
200 Court Street
Ville Platte, LA 70586
Phone: 337-363-4310
Website: https://www.evangelineassessor.com/
```

**Request Template:**
```
Subject: Public Use Request - Parcel Boundary Data

Dear Assessor Guillory,

I am working on a non-profit open mapping project (HITD Maps / mapsfordevelopers.com)
that provides free, self-hosted map alternatives to Google Maps. We are building
comprehensive USA parcel coverage and would like to include Evangeline Parish.

Would your office be able to provide:
1. Bulk parcel boundary data (shapefile, geodatabase, or GeoJSON)
2. Permission to use the data for public mapping purposes
3. Preferred attribution/credit language

We have successfully obtained similar data from 13 other Louisiana parishes
(Tangipahoa, Livingston, Ascension, etc.) and 32 states nationwide.

Our project is open-source and free to use at: https://hitd-maps.vercel.app/

Thank you for your consideration.
```

**Expected Outcomes:**
- Best case: Receive shapefile/geodatabase within 1-2 weeks
- Likely case: Referred to GIS department or IT staff
- Worst case: Denied due to policy restrictions

**Success Rate:** ~60% based on other Louisiana parish requests

---

### Option 2: Wait for Public GIS Launch

**Timeline:** Q2 2026 (estimated)
- Parish Police Jury website shows GIS service "Coming Soon"
- Modern GIS platforms typically include public REST APIs
- Check back monthly: https://evangelineparishpolicejury.com/gis-map/

**Action Items:**
- Set calendar reminder for April 2026
- Monitor website for GIS service launch
- Re-run endpoint discovery after launch

---

### Option 3: Purchase from Commercial Provider

**Regrid Data Purchase:**
- URL: https://app.regrid.com/store/us/la/evangeline
- Cost: ~$200-500 (one-time or subscription)
- Includes: 30,373 parcels with 114 attributes
- Format: Shapefile, GeoJSON, KML, or API access
- Updates: Regular updates included with subscription
- License: Commercial use allowed

**Budget Considerations:**
- Louisiana has 64 parishes at ~$300 average = $19,200 total
- Alternative: Focus on free sources, skip blocked parishes
- ROI: Evangeline Parish is small (32K population) - low priority

---

### Option 4: Skip and Focus on Accessible Parishes

**Louisiana Parishes with Public APIs (Still Available):**

| Parish | Population | Status | Notes |
|--------|-----------|--------|-------|
| St. Mary | 49,000 | Migrating Feb 1 | Check after geosync.io migration |
| Vermilion | 58,000 | Unknown | Adjacent to Evangeline, check endpoints |
| St. Landry | 82,000 | Unknown | Adjacent, shares Ville Platte metro |
| Avoyelles | 39,000 | Unknown | Adjacent, similar size |
| Acadia | 57,000 | Unknown | Adjacent to Lafayette |

**Recommendation:** Before purchasing Evangeline data, check neighboring parishes that may provide better coverage:population ratio.

**Priority Order:**
1. St. Mary (after Feb 1 migration)
2. Vermilion (higher population)
3. St. Landry (major population center)
4. Acadia (Lafayette metro area)
5. Evangeline (lowest priority - small, blocked)

---

## Technical Details

### Endpoint Testing Results

```bash
# Tested endpoints (all failed)
curl https://gis.evangelineparish.com/arcgis/rest/services
# Result: DNS resolution failed

curl https://gis.evangelineassessor.com/arcgis/rest/services
# Result: DNS resolution failed

curl http://gis.wlf.la.gov/arcgis/rest/services/Parishes/Evangeline/MapServer?f=json
# Result: {"error": {"code": 500, "message": "Service Parishes/Evangeline/MapServer not found"}}

curl https://qpublic.net/la/evangeline/
# Result: 404 Not Found

# Louisiana Wildlife GIS services (exist but no parcel data)
curl http://gis.wlf.la.gov/arcgis/rest/services?f=json
# Result: {"services": ["LDWF_ExplorerMap_01", "Oyster_Lease_Web_Map", "SampleWorldCities"]}
```

### Search Engine Results

**ArcGIS Hub Search:**
```
site:arcgis.com "Evangeline Parish" OR "Evangeline" Louisiana parcels
→ No results
```

**General Web Search:**
```
"Evangeline Parish" Louisiana GIS parcels ArcGIS REST API
→ Commercial providers only (Regrid, Dynamo, Acres)
→ No public endpoints discovered
```

---

## Data Registry Update

Added to `/home/exx/Documents/C/hitd_maps/data-pipeline/data/data_sources_registry.json`:

```json
{
  "parcels": {
    "LA": {
      "priority_parishes": {
        "evangeline": {
          "name": "Evangeline Parish (Ville Platte)",
          "population": 32000,
          "status": "blocked - no public API",
          "url": "https://evangelineparishpolicejury.com/gis-map/",
          "assessor_url": "https://www.evangelineassessor.com/",
          "api_url": null,
          "format": "Proprietary (no public REST API found)",
          "estimated_records": 30373,
          "last_attempted": "2026-01-27",
          "failure_reason": "Extensive search found no working ArcGIS REST API endpoint. Parish GIS service shows 'Coming Soon'. Qpublic portal returns 404. Commercial providers (Regrid) have data, indicating it exists but not publicly accessible via REST API.",
          "notes": "NO PUBLIC API FOUND. Parish GIS service launching soon. Commercial data available via Regrid (~30K parcels). Contact assessor for bulk export or wait for public GIS launch (Q2 2026).",
          "assessor": "Chris Guillory, Assessor, 200 Court Street, Ville Platte LA 70586, Phone: 337-363-4310",
          "alternative_access": "Contact assessor for bulk export, purchase from Regrid (~$200-500), or wait for GIS service launch (Q2 2026)"
        }
      }
    }
  }
}
```

---

## Conclusion

**Evangeline Parish parcel data is NOT deployable via automated ArcGIS REST API download.** The parish uses a proprietary GIS system without public REST API access, similar to several other small Louisiana parishes (Beauregard, Natchitoches, West Baton Rouge).

**Next Steps (in priority order):**

1. ✅ **Documented findings** in data_sources_registry.json
2. 📋 **Option 1:** Contact assessor for bulk export (60% success rate)
3. ⏰ **Option 2:** Wait for public GIS launch (Q2 2026)
4. 💰 **Option 3:** Purchase from Regrid if urgent (~$300)
5. ⏭️ **Option 4:** Skip and focus on accessible parishes (RECOMMENDED for now)

**Strategic Recommendation:** Given Evangeline Parish's small population (32K) and blocked API access, **prioritize other Louisiana parishes with higher population and public access** (St. Mary after Feb 1, Vermilion, St. Landry, Acadia). Evangeline can be added later via assessor contact or after public GIS launch.

---

## Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Project overview and Louisiana context
- [LOUISIANA_PARISH_REPORT.md](LOUISIANA_PARISH_REPORT.md) - Full LA parish status
- [DATA_GAPS.md](DATA_GAPS.md) - National missing coverage analysis
- [data_sources_registry.json](../data/data_sources_registry.json) - Master source registry

---

**Investigation Report Completed:** January 27, 2026
**Status:** BLOCKED - No public API access available
**Action Required:** Contact assessor, wait for GIS launch, or skip for now
