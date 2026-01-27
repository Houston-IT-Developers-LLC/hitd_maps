# Natchitoches Parish, Louisiana - Data Acquisition Investigation

**Date**: 2026-01-26
**Parish**: Natchitoches Parish, LA
**Population**: ~38,000
**Status**: ❌ No public ArcGIS REST API available

---

## Summary

Natchitoches Parish does NOT have a publicly accessible ArcGIS REST API for parcel data. The parish uses a QGIS-based backend server that is not accessible via standard REST queries.

---

## Investigation Results

### Official GIS Portal
- **Portal URL**: https://atlas.geoportalmaps.com/natch
- **Alternate URL**: http://www.geoportalmaps.com/atlas/natchitoches/
- **Assessor Website**: https://www.natchitochesassessor.org/
- **Property Search**: https://natchitochesassessor.azurewebsites.net/searchonly

### Backend Technology
The portal uses **QGIS MapServer**, not ArcGIS Server:
```
http://192.168.60.130:8001/cgi-bin/qgis_mapserv.fcgi.exe?MAP=D:/GCTServices/Natchitoches_Services.mxd.qgs
```

This is an internal server (192.168.x.x) that is:
- Not publicly accessible
- Not REST API compatible
- Requires WMS/WFS protocol (if exposed)

### Tested Endpoints (All Failed)
```
❌ https://services.geoportalmaps.com/arcgis/rest/services/Natchitoches_Services/MapServer
❌ https://atlas.geoportalmaps.com/natch/server/rest/services
❌ https://nagis.natchitoches.org/server/rest/services
❌ https://gis.natchitoches.org/server/rest/services
❌ https://atlas.geoportalmaps.com/natchitoches/server/rest/services
❌ Utility.arcgis.com hosted services
```

---

## Alternative Acquisition Methods

### 1. Direct Contact - Assessor's Office ⭐ RECOMMENDED
**Contact**: Natchitoches Parish Assessor
**Phone**: (318) 352-2377
**Address**: P O Box 201, Natchitoches, LA 71458-0201
**Assessor**: Dollie C. Mahoney, CLA

**Request**: Bulk parcel data export (GeoJSON, Shapefile, or GeoPackage format)

### 2. Commercial Data Providers
- **Regrid**: https://app.regrid.com/us/la/natchitoches
  - Reported: 24,345+ parcels with boundaries
  - Pricing: ~$200-500 for parish data

- **LightBox** (formerly CoreLogic)
- **DataTree** by First American
- **ATTOM Data Solutions**

### 3. Louisiana Statewide Sources
Louisiana has **NO statewide parcel database**. Each parish maintains independent systems.

Current HITD coverage for Louisiana: **12/64 parishes (18.8%)**
- Have: Ascension, Bossier, Caddo, Calcasieu, East Baton Rouge, Jefferson, Lafayette, Livingston, Orleans, St. Bernard, Tangipahoa, Terrebonne

### 4. Web Scraping (Last Resort)
The GeoPortalMaps interface could theoretically be scraped via browser automation (Selenium/Playwright), but:
- ⚠️ Violates terms of service
- ⚠️ Very slow (1 parcel at a time)
- ⚠️ Unreliable and requires maintenance
- ⚠️ May get IP blocked

---

## Estimated Parcel Count
- **Regrid reports**: 24,345 parcels
- **Other sources**: 32,627 properties
- **Estimated PMTiles size**: 8-12 MB

---

## Regional Context

Natchitoches is part of **Northwest Louisiana**. Neighboring parishes:

| Parish | Status | Notes |
|--------|--------|-------|
| Natchitoches | ❌ Missing | No REST API (QGIS backend) |
| Red River | ❌ Missing | Unknown system |
| Sabine | ❌ Missing | Unknown system |
| DeSoto | ❌ Missing | Unknown system |
| Winn | ❌ Missing | Unknown system |
| Grant | ❌ Missing | Unknown system |

**Northwest Louisiana region has ZERO coverage** in our system.

---

## Recommendation

**Action**: Contact Natchitoches Parish Assessor's office directly at (318) 352-2377 and request:

1. Bulk export of parcel boundaries (GeoJSON or Shapefile preferred)
2. Data license/usage rights for mapping application
3. Update frequency and last update date

**Alternative**: If assessor cannot provide data:
- Purchase from Regrid ($200-500)
- Skip for now and focus on parishes with REST APIs
- Wait for state to develop centralized system (unlikely)

---

## Similar Louisiana Parishes (Successfully Deployed)

These parishes use **accessible** ArcGIS REST APIs:

| Parish | API Type | Endpoint Pattern |
|--------|----------|------------------|
| Ascension | FeatureServer | gis.ascensionparishla.gov/server/rest |
| Bossier | MapServer | bpagis.bossierparish.org/server/rest |
| Livingston | MapServer (utility.arcgis.com) | utility.arcgis.com/usrsvcs/servers/... |
| Tangipahoa | FeatureServer | tangis.tangipahoa.org/server/rest |

Natchitoches uses a **completely different backend** (QGIS) that doesn't fit this pattern.

---

## Web Search Sources

Research conducted using:
- [Natchitoches Parish Assessor](https://www.natchitochesassessor.org/)
- [GeoPortal Maps Atlas](https://atlas.geoportalmaps.com/natch)
- [Regrid Parcel Data](https://app.regrid.com/us/la/natchitoches)
- [Louisiana GIS Resources](https://www.doa.la.gov/doa/osl/gis-data/)
- [QPUBLIC Louisiana Assessors](https://qpublic.net/la/laassessors/)

---

## Next Steps

1. ✅ Document findings (this file)
2. ⏭️ Contact assessor's office for bulk data
3. ⏭️ If no response in 1 week, evaluate commercial purchase
4. ⏭️ Focus on other Louisiana parishes with REST APIs
5. ⏭️ Update data_sources_registry.json with findings

---

**Investigation completed**: 2026-01-26
**Investigator**: Claude (AI Agent)
**Outcome**: No automated download possible - manual acquisition required
