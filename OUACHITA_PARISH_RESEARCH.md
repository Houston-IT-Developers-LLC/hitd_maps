# Ouachita Parish, Louisiana - Data Source Research Report

**Date:** 2026-01-26
**Status:** NO PUBLIC API AVAILABLE
**Parish:** Ouachita Parish (Monroe area)
**Population:** ~156,000

---

## Summary

After comprehensive research, Ouachita Parish does NOT have a publicly accessible ArcGIS REST API for parcel data. The parish uses actDataScout, a proprietary web portal system that does not provide standard REST endpoints for bulk data access.

---

## Research Conducted

### 1. Web Searches Performed
- Louisiana Atlas (LSU) - No parish-level parcel data
- Louisiana Department of Transportation GIS - No parcel services
- Ouachita Parish Assessor website - Web portal only
- actDataScout.com - Proprietary system, no public API
- City of Monroe GIS department - No public REST services
- ArcGIS Online searches - No Ouachita Parish services found
- AI-powered source finder - Did not find working endpoints

### 2. Systems Checked
- **actDataScout.com** - Primary parcel viewer for Ouachita Parish
  - URL: https://www.actdatascout.com/RealProperty/Louisiana/Ouachita
  - Map: https://www.actdatascout.com/Map/Index
  - Status: Proprietary web portal, no REST API
  - Terms: Explicitly prohibits automated scraping without written permission

- **Ouachita Parish Assessor**
  - Website: http://www.opassessor.com/
  - Address: 301 South Grand Street, Monroe, LA 71201
  - Phone: 318-327-1300
  - Status: Web interface only, no bulk download option

- **City of Monroe GIS**
  - Website: https://monroela.us/departments/engineering/gis-geographic-information-system/
  - Status: No public REST services found

### 3. Louisiana Context
Louisiana is unique among US states:
- **No statewide parcel database**
- Each of 64 parishes uses different systems
- Many parishes use proprietary portals (Atlas/GeoPortal Maps)
- Standard ArcGIS REST APIs are rare

Current HITD Maps Louisiana coverage:
- 7/64 parishes (11%)
- Have: Caddo, Calcasieu, East Baton Rouge, Jefferson, Lafayette, Orleans, Terrebonne
- Missing: 57 parishes including Ouachita

---

## Alternative Data Sources

### Option 1: Commercial Providers (RECOMMENDED)
Purchase bulk parcel data from third-party aggregators:

**Regrid**
- URL: https://app.regrid.com/store/us/la/ouachita
- Coverage: 87,668 parcels
- Format: Shapefile, GeoJSON, CSV
- Cost: ~$500-1000 for county-level data
- Quality: High (standardized schema)

**Dynamo Spatial**
- URL: https://www.dynamospatial.com/c/ouachita-parish-la/parcel-data
- Coverage: 90,695 properties
- Format: ESRI Shapefile
- Cost: Contact for pricing
- Quality: High

**LightBox (formerly CoreLogic)**
- National parcel data provider
- API available
- Cost: Enterprise pricing

### Option 2: Direct Contact (FREE but Manual)
Contact Ouachita Parish Assessor directly:

1. **Call:** 318-327-1300
2. **Visit:** 301 South Grand Street, Monroe, LA 71201
3. **Request:** Bulk GIS data export or shapefile
4. **Format:** Ask for Shapefile or GeoJSON
5. **Update frequency:** Confirm data freshness

Pros:
- Free or low cost
- Official source
- Most current data

Cons:
- Manual process
- May take weeks
- No guarantee of format/quality

### Option 3: Manual Web Portal Export
Some GIS portals allow manual export of selected areas:

1. Visit actDataScout map interface
2. Check for export/download tools
3. May need to export in chunks
4. Combine manually

Pros:
- Free
- Immediate

Cons:
- Very time-consuming
- May violate Terms of Service
- Incomplete coverage likely

---

## Recommendation

### Short-term (Immediate Need)
**Purchase from Regrid** - $500-1000 one-time cost
- Fastest solution (hours)
- Standardized format
- Regular updates available
- API access for future updates

### Long-term (Sustainable)
**Contact Assessor's Office** - Free
- Request annual bulk data agreement
- Establish update schedule
- Build relationship for future needs

### Fallback
**Skip Ouachita for now**
- Focus on parishes with working APIs
- Revisit when more Louisiana sources discovered
- Current 11% LA coverage acceptable for MVP

---

## Next Steps

### If Proceeding with Purchase:
1. Budget approval for $500-1000
2. Purchase from Regrid or Dynamo
3. Download data (Shapefile format)
4. Process: `smart_reproject_parcels.py`
5. Convert: `batch_convert_pmtiles.py`
6. Upload: `upload_to_r2_boto3.py`
7. Deploy as `parcels_la_ouachita.pmtiles`

### If Contacting Assessor:
1. Draft formal data request letter
2. Call 318-327-1300 to confirm recipient
3. Email or mail request
4. Follow up in 1-2 weeks
5. Process received data

### If Skipping:
1. Document in `data_sources_registry.json`
2. Mark as "proprietary_portal" status
3. Add to priority list for future
4. Move to next target parish

---

## Similar Louisiana Parishes

These parishes also use proprietary systems (NO public APIs):
- St. Tammany (265K pop) - atlas.stpgov.org
- Livingston (142K pop) - geoportalmaps.com
- Tangipahoa (133K pop) - custom portal
- Rapides (130K pop) - rapcgis.rapc.info
- Bossier (128K pop) - geoportalmaps.com

**Louisiana Strategy:** May need to budget for commercial data purchases or establish bulk data agreements with each parish assessor office.

---

## Data Sources Registry Update

```json
{
  "LA": {
    "parishes": {
      "ouachita": {
        "name": "Ouachita Parish (Monroe)",
        "population": 156000,
        "status": "proprietary_portal",
        "url": "http://www.opassessor.com/",
        "portal": "https://www.actdatascout.com/RealProperty/Louisiana/Ouachita",
        "api_url": null,
        "format": "Proprietary web portal - NO public REST API",
        "estimated_records": 87668,
        "notes": "actDataScout proprietary system. No standard ArcGIS REST access. Options: (1) Purchase from Regrid/Dynamo ($500-1000), (2) Contact assessor for bulk data (free but manual), (3) Skip for now",
        "commercial_sources": [
          {
            "provider": "Regrid",
            "url": "https://app.regrid.com/store/us/la/ouachita",
            "parcel_count": 87668,
            "cost_estimate": "$500-1000"
          },
          {
            "provider": "Dynamo Spatial",
            "url": "https://www.dynamospatial.com/c/ouachita-parish-la/parcel-data",
            "parcel_count": 90695,
            "cost_estimate": "Contact for pricing"
          }
        ],
        "assessor": {
          "name": "Ouachita Parish Assessor's Office",
          "phone": "318-327-1300",
          "address": "301 South Grand Street, Monroe, LA 71201",
          "contact_method": "Call to request bulk GIS data"
        }
      }
    }
  }
}
```

---

## Sources

Research conducted using:
- [Ouachita Parish Assessor's Office](http://www.opassessor.com/)
- [actDataScout Portal](https://www.actdatascout.com/RealProperty/Louisiana/Ouachita)
- [Louisiana DOA GIS & Data](https://www.doa.la.gov/doa/osl/gis-data/)
- [LSU Atlas](https://atlas.ga.lsu.edu/)
- [City of Monroe GIS](https://monroela.us/departments/engineering/gis-geographic-information-system/)
- [Regrid Data Store](https://app.regrid.com/store/us/la/ouachita)
- [Dynamo Spatial](https://www.dynamospatial.com/c/ouachita-parish-la/parcel-data)
- ArcGIS Online search tools
- AI-powered source discovery tools
