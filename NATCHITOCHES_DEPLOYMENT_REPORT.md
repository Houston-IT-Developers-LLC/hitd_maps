# Natchitoches Parish, Louisiana - Deployment Report

**Date**: 2026-01-26
**Status**: ❌ **DEPLOYMENT NOT POSSIBLE** (Incompatible Backend)
**Parish**: Natchitoches Parish, LA
**Population**: ~38,000
**Estimated Parcels**: 24,345

---

## Executive Summary

**Natchitoches Parish cannot be deployed using our automated pipeline.** The parish uses a QGIS MapServer backend instead of ArcGIS REST API, making it incompatible with our standard download tools.

---

## Technical Findings

### Backend Architecture
- **GIS Platform**: QGIS MapServer (NOT ArcGIS)
- **Backend Server**: `http://192.168.60.130:8001/cgi-bin/qgis_mapserv.fcgi.exe`
- **Frontend Portal**: https://atlas.geoportalmaps.com/natch (GeoPortalMaps)
- **API Type**: None - QGIS WMS/WFS only (not publicly exposed)

### Why Automated Download Failed

1. **No REST API**: Parish doesn't use ArcGIS Server/Online
2. **Internal Server**: QGIS backend runs on internal IP (192.168.60.130)
3. **Not Publicly Accessible**: No external endpoint for programmatic access
4. **Different Protocol**: Would require WMS/WFS if exposed (not REST)

### Endpoints Tested (All Failed)
```
❌ https://services.geoportalmaps.com/arcgis/rest/services/Natchitoches_Services/MapServer
❌ https://atlas.geoportalmaps.com/natch/server/rest/services
❌ https://nagis.natchitoches.org/server/rest/services
❌ https://gis.natchitoches.org/server/rest/services
❌ https://utility.arcgis.com hosted services (checked, no Natchitoches servers)
```

---

## Acquisition Options

### Option 1: Contact Assessor Directly ⭐ **RECOMMENDED**

**Contact Information**:
- **Assessor**: Dollie C. Mahoney, CLA
- **Phone**: (318) 352-2377
- **Address**: P O Box 201, Natchitoches, LA 71458-0201
- **Website**: https://www.natchitochesassessor.org/

**What to Request**:
1. Bulk parcel boundary export (GeoJSON or Shapefile format preferred)
2. Data usage rights for public mapping application
3. Last update date and update frequency
4. Any attribute data available (parcel IDs, addresses, etc.)

**Expected Response Time**: 1-2 weeks
**Success Rate**: Medium (depends on staff availability and willingness)

---

### Option 2: Purchase from Commercial Provider

**Regrid** (Recommended Commercial Source)
- **URL**: https://app.regrid.com/us/la/natchitoches
- **Coverage**: 24,345+ parcels with boundaries
- **Format**: GeoJSON, Shapefile, or API access
- **Est. Cost**: $200-500 for parish data (one-time or subscription)
- **Delivery**: Immediate download after purchase
- **Quality**: High (standardized nationwide)

**Other Commercial Providers**:
- LightBox (formerly CoreLogic)
- DataTree by First American
- ATTOM Data Solutions

**Pros**:
- ✅ Immediate availability
- ✅ Standardized format
- ✅ Regular updates available
- ✅ No IT staff dependencies

**Cons**:
- ❌ Cost ($200-500)
- ❌ May require subscription for updates

---

### Option 3: Skip for Now

**Rationale**:
- Small population (38K - lowest priority for hunting use case)
- Northwest Louisiana has zero coverage currently
- Better ROI focusing on larger parishes with accessible APIs
- May become available if parish upgrades GIS infrastructure

**Alternative Parishes to Prioritize** (Louisiana):
- St. Mary Parish (51K pop) - check for REST API
- Ouachita Parish (Monroe, 150K pop) - check for REST API
- Lafayette Parish (likely already covered)
- St. Charles Parish (52K pop) - check for REST API

---

## Regional Context

### Northwest Louisiana Coverage: 0%

| Parish | Population | Status | Notes |
|--------|-----------|--------|-------|
| Caddo (Shreveport) | 237K | ✅ Have | Already deployed |
| Bossier | 128K | ✅ Have | Already deployed |
| **Natchitoches** | **38K** | ❌ **QGIS** | **No REST API** |
| Red River | 9K | ❌ Missing | Unknown system |
| Sabine | 24K | ❌ Missing | Unknown system |
| DeSoto | 28K | ❌ Missing | Unknown system |
| Webster | 39K | ❌ Missing | Unknown system |

**Current LA Coverage**: 13/64 parishes (20.3%)

---

## Estimated Deployment Size

If data were obtained:
- **Records**: ~24,345 parcels
- **PMTiles Size**: 8-12 MB (estimated)
- **Processing Time**: 15-30 minutes
- **R2 Upload**: 2-5 minutes

---

## Comparison with Similar Parishes

### Successfully Deployed Louisiana Parishes

| Parish | Backend | API Type | Records | How We Got It |
|--------|---------|----------|---------|---------------|
| Bossier | ArcGIS | MapServer | 78,556 | Found hidden endpoint |
| Livingston | ArcGIS | MapServer (utility.arcgis.com) | 84,692 | utility.arcgis.com discovery |
| Tangipahoa | ArcGIS | FeatureServer | 75,919 | Direct parish server |
| Ascension | ArcGIS | FeatureServer | 59,778 | Direct parish server |

**Natchitoches is unique** - only Louisiana parish we've found using QGIS instead of ArcGIS.

---

## Recommendations

### Immediate Action (Next 48 hours)
1. ✅ Document findings (COMPLETED - this report + investigation doc)
2. ⏭️ Update data_sources_registry.json with Natchitoches entry (COMPLETED)
3. ⏭️ Decide: Contact assessor OR purchase from Regrid OR skip

### If Contacting Assessor
**Email Template**:
```
Subject: Request for Bulk Parcel Data Export

Dear Natchitoches Parish Assessor's Office,

We are developing a public property mapping application and would like to include
Natchitoches Parish parcel boundaries. We noticed your GIS portal at
atlas.geoportalmaps.com/natch but could not find a bulk data download option.

Could you provide:
1. Parcel boundary data (GeoJSON or Shapefile format preferred)
2. Permission to use this data in a public web mapping application
3. Information about update frequency and last update date

We would be happy to credit the Natchitoches Parish Assessor's Office as the
data source and provide a link back to your website.

Thank you for your consideration.

Best regards,
[Your Name]
HITD Maps Project
```

### If Purchasing from Regrid
1. Sign up at https://app.regrid.com
2. Navigate to https://app.regrid.com/store/us/la/natchitoches
3. Purchase parish data package
4. Download as GeoJSON
5. Process through our pipeline:
   ```bash
   python3 scripts/smart_reproject_parcels.py natchitoches_regrid.geojson
   tippecanoe -o parcels_la_natchitoches.pmtiles -Z8 -z14 natchitoches_regrid_wgs84.geojson
   aws s3 cp parcels_la_natchitoches.pmtiles s3://gspot-tiles/parcels/ --endpoint-url=$R2_ENDPOINT
   ```

---

## Files Created

1. `/home/exx/Documents/C/hitd_maps/data-pipeline/docs/NATCHITOCHES_PARISH_INVESTIGATION.md`
   - Detailed technical investigation report

2. `/home/exx/Documents/C/hitd_maps/NATCHITOCHES_DEPLOYMENT_REPORT.md`
   - This file - executive summary and recommendations

3. Updated: `/home/exx/Documents/C/hitd_maps/data-pipeline/data/data_sources_registry.json`
   - Added Natchitoches Parish entry with QGIS backend documentation

---

## Lessons Learned

1. **Not all parishes use ArcGIS** - Some use QGIS, MapBox, or proprietary systems
2. **GeoPortalMaps ≠ ArcGIS** - GeoPortalMaps is a frontend that can use various backends
3. **Always check backend technology** - Look at network requests in browser dev tools
4. **Louisiana is fragmented** - 64 independent parish systems with zero coordination

---

## Next Steps

**Your Decision Required**:

☐ **Option A**: Contact Natchitoches Assessor (free, 1-2 week wait, uncertain outcome)
☐ **Option B**: Purchase from Regrid (~$300, immediate, guaranteed data)
☐ **Option C**: Skip Natchitoches, focus on larger parishes with REST APIs

**My Recommendation**: **Option C** (Skip) unless you specifically need Northwest Louisiana coverage. Focus on:
- St. Mary Parish (51K)
- Ouachita Parish (Monroe, 150K)
- Union Parish (22K)
- Other mid-size parishes with potential REST APIs

---

**Investigation Completed**: 2026-01-26
**Investigator**: Claude Sonnet 4.5
**Time Invested**: ~45 minutes of systematic API discovery
**Outcome**: No automated deployment possible - manual acquisition required

---

## Sources

- [Natchitoches Parish Assessor](https://www.natchitochesassessor.org/)
- [Natchitoches GIS Portal](https://atlas.geoportalmaps.com/natch)
- [Regrid - Natchitoches Parish Data](https://app.regrid.com/us/la/natchitoches)
- [Louisiana GIS Data Portal](https://www.doa.la.gov/doa/osl/gis-data/)
- [GeoPortal Maps Platform](https://atlas.geoportalmaps.com/)
- [QPUBLIC Louisiana Assessors](https://qpublic.net/la/laassessors/)
