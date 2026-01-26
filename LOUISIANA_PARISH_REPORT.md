# Louisiana Priority Parishes Investigation
**Date:** 2026-01-25  
**Status:** No automated deployment possible  
**Coverage:** 7/64 parishes (11%)

## Executive Summary

Investigation into 5 high-priority Louisiana parishes for hunting land mapping reveals **NO parishes have publicly accessible ArcGIS REST APIs**. All use proprietary web mapping portals that do not expose standard REST endpoints for bulk data extraction.

## Current Louisiana Coverage (7 parishes)

| Parish | File | Status |
|--------|------|--------|
| Caddo (Shreveport) | `parcels_la_caddo` | Deployed |
| Calcasieu | `parcels_la_calcasieu` | Deployed |
| East Baton Rouge | `parcels_la_east_baton_rouge` | Deployed |
| Jefferson | `parcels_la_jefferson_v2` | Deployed |
| Lafayette | `parcels_la_lafayette` | Deployed |
| Orleans (New Orleans) | `parcels_la_orleans_v2` | Deployed |
| Terrebonne (Houma) | `parcels_la_terrebonne` | Deployed |

## Priority Parishes Investigated

### 1. St. Tammany Parish (265K population)
- **Hunting Value:** HIGH - North Shore hunting area
- **Portal:** https://atlas.geoportalmaps.com/st_tammany
- **Assessor:** https://stpao.org/all-tech/
- **Records:** ~131,134 parcels
- **System:** Atlas/GeoPortal Maps proprietary platform
- **API Access:** MapServer endpoint exists but requires authentication/special access
- **Endpoint:** `https://atlas.stpgov.org/server/rest/services/STPAO_Parcels/MapServer/1`
- **Status:** ❌ No public REST API access

### 2. Livingston Parish (142K population)
- **Hunting Value:** HIGH - Prime hunting territory
- **Portal:** https://atlas.geoportalmaps.com/livingston
- **Assessor:** Livingston Parish Assessor, 20400 Government Blvd., Livingston, LA 70754
- **Records:** ~79,559 properties
- **System:** Atlas/GeoPortal Maps proprietary platform
- **API Access:** None discovered
- **Status:** ❌ No public REST API access

### 3. Tangipahoa Parish (133K population)
- **Hunting Value:** HIGH - Hunting area
- **Portal:** https://tangipahoa.org/residents/gis-mapping/tangis/
- **Assessor:** https://tangiassessor.com/gis-mapping
- **Records:** ~81,479 properties
- **System:** Custom TanGIS department portal
- **API Access:** None discovered
- **Status:** ❌ No public REST API access

### 4. Rapides Parish (130K population - Alexandria)
- **Hunting Value:** Medium
- **Portal:** https://rapcgis.rapc.info/portal/apps/webappviewer/index.html
- **Assessor:** http://www.rapidesassessor.org/
- **Records:** Unknown
- **System:** Rapides Area Planning Commission (RAPC) GIS
- **API Access:** None discovered
- **Status:** ❌ No public REST API access

### 5. Bossier Parish (128K population)
- **Hunting Value:** Medium
- **Portal:** https://atlas.geoportalmaps.com/bossier_public/
- **Assessor:** Bossier Parish Assessor
- **Records:** Unknown
- **System:** Atlas/GeoPortal Maps proprietary platform
- **API Access:** None discovered
- **Status:** ❌ No public REST API access

## Technical Findings

### Why Louisiana Is Difficult

1. **No Statewide Database:** Unlike most states, Louisiana has NO centralized parcel database
2. **Parish Autonomy:** Each of 64 parishes maintains independent GIS systems
3. **Proprietary Platforms:** Most use Atlas/GeoPortal Maps or custom web portals
4. **No REST APIs:** Standard ArcGIS REST endpoints are not publicly exposed
5. **Authentication Required:** Even when MapServer endpoints exist, they require special access

### Platform Analysis

**Atlas/GeoPortal Maps** (Used by St. Tammany, Livingston, Bossier):
- Commercial platform by GeoPortal Maps LLC
- Web viewer only - no bulk export
- REST services exist but are protected
- Would need to contact vendor for API access

**Custom Portals** (Tangipahoa, Rapides):
- Each parish built custom GIS viewer
- No standardized data access
- Would need parish-specific arrangements

## Deployment Options

Since automated scraping is not possible, these are the viable paths:

### Option 1: Direct Parish Contact (Recommended for Priority Parishes)
**Best for:** St. Tammany, Livingston, Tangipahoa (hunting priority)

**Process:**
1. Contact parish assessor's office directly
2. Request bulk parcel shapefile/GeoJSON export
3. Explain use case (public mapping platform)
4. May be provided free for public use or small fee

**Sample Request Email:**
```
Subject: Request for Bulk Parcel Data Export

Dear [Parish] Assessor's Office,

We are building a public mapping platform (mapsfordevelopers.com) and would like to 
include [Parish] property parcels to help landowners, hunters, and developers locate 
properties.

Would you be able to provide a bulk export of your parcel boundaries (shapefile or 
GeoJSON format)? We will properly attribute the data to your office and keep it updated.

Thank you,
[Your name]
HITD Maps Team
```

### Option 2: Commercial Data Vendors
**Providers:**
- **Regrid:** https://regrid.com - Per-parish pricing
- **LightBox:** Enterprise parcel data
- **CoreLogic:** National parcel database

**Pros:** Immediate access, standardized format  
**Cons:** Expensive ($$ per parish), licensing restrictions

### Option 3: Manual Portal Export
Some portals may allow manual export of visible areas. Labor-intensive but possible for small parishes.

### Option 4: Wait for State Initiative
Louisiana may eventually create a statewide parcel database (like Texas TNRIS). Monitor https://www.gis.la.gov/

## Recommendations

### Immediate Action (Next 48 Hours)
1. ✅ **Document findings** - Complete ✓
2. ✅ **Update data_sources_registry.json** - Complete ✓
3. **Email 3 highest-priority parishes:**
   - St. Tammany Parish Assessor
   - Livingston Parish Assessor (20400 Government Blvd., Livingston, LA 70754)
   - Tangipahoa Parish Assessor

### Short Term (This Month)
1. If parish responses are positive, process and deploy
2. If no response, evaluate commercial vendor costs
3. Check if existing 7 parishes cover main user demand

### Long Term
1. Monitor for Louisiana statewide parcel initiative
2. Add Louisiana parishes incrementally as budget/access allows
3. Consider crowdsourcing: Allow users to upload parish data

## Cost-Benefit Analysis

**Estimated Value of 5 Priority Parishes:**
- Combined population: ~798K
- Estimated parcels: ~292K+ parcels
- Hunting land market: High value for hunters/landowners

**Acquisition Costs:**
- Free (parish cooperation): $0
- Commercial (Regrid): ~$2,500-5,000 per parish = $12,500-25,000
- Time investment: 2-4 hours per parish for outreach

**Recommendation:** Start with direct parish outreach (free/low-cost) before considering commercial purchase.

## Next Steps

1. **Draft and send parish outreach emails** (template above)
2. **Track responses** in agent issues database
3. **If successful:** Process received data through standard pipeline
4. **If unsuccessful:** Evaluate commercial vendor options
5. **Update COVERAGE_STATUS.md** once new parishes are acquired

## References

- [St. Tammany Parish GIS](https://atlas.geoportalmaps.com/st_tammany)
- [Livingston Parish Assessor](https://www.livingstonassessor.com/mapping)
- [Tangipahoa Parish GIS](https://tangipahoa.org/residents/gis-mapping/)
- [Rapides Parish Assessor](http://www.rapidesassessor.org/)
- [Bossier Parish GIS](https://www.bossierparishla.gov/police-jury/divisions/geographic-information-system-(gis)/)
- [Louisiana GIS Portal](https://www.gis.la.gov/)

---
**Script Generated:** `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/scrape_la_priority_parishes.py`  
**Status:** Discovery complete - no automated deployment possible
