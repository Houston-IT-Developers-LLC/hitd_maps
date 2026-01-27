# Beauregard Parish, Louisiana - Deployment Research

**Date**: 2026-01-26
**Status**: ❌ NO PUBLIC API FOUND
**Population**: 37,000 (DeRidder area)
**Target File**: `parcels_la_beauregard.pmtiles`

---

## Summary

After extensive research, **Beauregard Parish does NOT have a publicly accessible ArcGIS REST API endpoint** for parcel data. Deployment cannot proceed without direct contact with the parish assessor or purchase from a commercial provider.

---

## Research Conducted

### 1. Web Search Results
- Found references to Beauregard Parish GIS on commercial platforms:
  - [Regrid](https://app.regrid.com/us/la/beauregard) - ~26,778 properties
  - Mapping Solutions GIS - Commercial parcel data
  - Dynamo Spatial - Commercial parcel data
- These indicate the data **exists** but is not publicly accessible

### 2. GIS Portal Discovery Attempts

#### Atlas/GeoPortal Maps System
- Portal URL: https://atlas.geoportalmaps.com/beauregard
- Portal **exists** but backend REST API **not accessible**
- Tried common Louisiana parish patterns:
  - `https://atlas.geoportalmaps.com/beauregard/rest/services` → 404
  - `https://beauregard.atlas.geoportalmaps.com/server/rest/services` → Failed
  - `https://gis.beauregardparish.org/server/rest/services` → Failed

#### Assessor Website
- URL: http://www.bpassessor.com
- Status: Accessible, but **no public GIS portal link**
- References to maps/GIS found, but no REST API endpoints

#### Other Attempted Patterns
Based on successful Louisiana parish deployments:
- Ascension: `gis.ascensionparishla.gov/server/rest/services`
- Bossier: `bpagis.bossierparish.org/server/rest/services`
- Tangipahoa: `tangis.tangipahoa.org/server/rest/services`
- Calcasieu (neighbor): `cpgis.calcasieuparish.gov/arcgis/rest/services`

**None of these patterns worked for Beauregard Parish.**

### 3. Neighboring Parish Analysis

Beauregard is bordered by:
- **Calcasieu Parish** (pop: 216K) - Has REST API, but MapServer only (not FeatureServer)
- Allen Parish (pop: 22K) - Status unknown
- Vernon Parish (pop: 48K) - Status unknown
- Jefferson Davis Parish (pop: 32K) - Status unknown

Calcasieu API endpoint was tested but appears to be down or restricted.

---

## Why No API Was Found

### Likely Explanations:

1. **Proprietary System**: Parish may use Qpublic.net or similar proprietary vendor
   - These systems typically don't offer standard REST APIs
   - Search results mentioned Qpublic.net reference: https://qpublic.net/la/beauregard/

2. **Authentication Required**: API may exist but require login/token

3. **Internal Network Only**: GIS server may be accessible only within parish network

4. **No Digital System**: Parish may maintain data in offline formats only (unlikely given commercial providers have it)

---

## Current Louisiana Coverage

**Deployed Parishes: 12/64 (18.8%)**

Currently have:
- Ascension
- Bossier
- Caddo
- Calcasieu
- East Baton Rouge
- Jefferson
- Lafayette
- Livingston
- Orleans (New Orleans)
- St. Bernard
- Tangipahoa
- Terrebonne

**Priority parishes still missing:**
- **St. Tammany** (265K pop) - BLOCKED by firewall
- **Rapides** (130K pop) - Proprietary portal, no REST API
- **Beauregard** (37K pop) - No public API found

---

## Next Steps

### Option 1: Direct Contact (Recommended)
Contact **Beauregard Parish Assessor's Office**:
- Address: 214 West 2nd Street, DeRidder, LA 70634
- Phone: **337-463-8945**
- Request:
  - Public REST API endpoint (if available)
  - Or bulk parcel shapefile/geodatabase export
  - Format preference: Shapefile, GeoJSON, or File Geodatabase

### Option 2: Commercial Purchase
- Regrid: https://app.regrid.com/store/us/la/beauregard
- Estimated cost: $50-200 for parish-level data
- Includes ~26,778 parcel records

### Option 3: Wait & Monitor
- Check back quarterly for new public portals
- Monitor for migration to newer GIS systems (like geosync.io)
- Watch for Louisiana statewide data initiatives

### Option 4: Skip For Now
- Focus on other Louisiana parishes with confirmed APIs
- Beauregard is relatively small (37K pop, ~27K parcels)
- Priority should be St. Tammany (265K pop) once firewall resolved

---

## Data Source Registry Update

Added Beauregard Parish to `/data-pipeline/data/data_sources_registry.json`:

```json
"beauregard": {
  "name": "Beauregard Parish (DeRidder)",
  "population": 37000,
  "status": "missing - no public API",
  "url": "http://www.bpassessor.com",
  "portal": "https://atlas.geoportalmaps.com/beauregard",
  "api_url": null,
  "estimated_records": 26778,
  "last_attempted": "2026-01-26",
  "notes": "NO PUBLIC API FOUND. Contact assessor for bulk data request.",
  "assessor": "Beauregard Parish Assessor, 214 West 2nd Street, DeRidder LA 70634, Phone: 337-463-8945"
}
```

---

## Lessons Learned

### Louisiana Parish Data Landscape

Louisiana is **challenging** for automated parcel data collection:
- **No statewide parcel database** exists
- Each of 64 parishes maintains their own systems
- Mix of vendors: ArcGIS Server, Atlas/GeoPortal Maps, Qpublic, proprietary systems
- Some parishes require authentication or restrict public access
- Smaller parishes (<50K pop) often lack public REST APIs

### Success Patterns
Parishes with good public access typically have:
- Population > 100K
- Dedicated GIS department
- Modern ArcGIS infrastructure
- Recent system upgrades

### Blocked Patterns
Parishes without public APIs often:
- Use Qpublic.net or similar proprietary vendors
- Have Atlas/GeoPortal Maps without backend REST access
- Require authentication for bulk access
- Are smaller/rural parishes with limited IT resources

---

## Sources

- [Beauregard Parish GIS Resources](https://www.dynamospatial.com/c/beauregard-parish-la/parcel-data)
- [Regrid: Beauregard Parish Data](https://app.regrid.com/us/la/beauregard)
- [Beauregard Parish Assessor](http://www.bpassessor.com/)
- [County Office: Beauregard GIS Maps](https://www.countyoffice.org/la-beauregard-parish-gis-maps/)
- [Louisiana Assessors Portal](https://qpublic.net/la/laassessors/body-b.html)

---

**Conclusion**: Beauregard Parish deployment is **blocked** until direct contact with assessor or commercial data purchase. Updated data sources registry to reflect this status.
