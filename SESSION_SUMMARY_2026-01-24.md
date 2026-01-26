# HITD Maps - Deployment Session Summary
**Date:** 2026-01-24
**Duration:** Full deployment session
**Strategy:** Free government/open source data only

---

## 🎯 Major Accomplishments

### ✅ Successfully Deployed Today
1. **Washington DC - Owner Polygons**
   - Parcels: 137,380
   - Source: `https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Property_and_Land_WebMercator/FeatureServer/40`
   - Size: 99.9 MB PMTiles
   - **Impact: DC now 100% complete** (was 0%)

2. **Nebraska - Douglas County (Omaha)**
   - Parcels: 216,648
   - Source: `https://dcgis.org/server/rest/services/vector/Parcels_public/FeatureServer/0`
   - Size: 85.0 MB PMTiles
   - **Impact: NE now has Omaha metro coverage** (largest county)

**Total New Parcels**: 354,028
**Total New Storage**: 184.9 MB PMTiles

###📊 Coverage Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Overall Coverage** | 68.6% | 70.6% | +2.0% |
| **Complete States** | 35 | 36 | +1 |
| **Partial States** | 16 | 15 | -1 |
| **Total Files** | 228 | 230 | +2 |
| **Total Storage** | ~730 GB | ~730.2 GB | +0.2 GB |

### 📝 Documentation Created

1. **[MISSING_COUNTIES_NATIONWIDE.md](MISSING_COUNTIES_NATIONWIDE.md)**
   - Comprehensive analysis of all 15 partial states
   - Top 100 missing counties ranked by population
   - Identified 16 "mega counties" (500K+ pop) for priority deployment
   - Strategic deployment phases outlined

2. **Deployment Scripts**
   - `deploy_verified_sources_final.py` - DC + NE deployment
   - `deploy_mega_counties.py` - Template for mega county deployment
   - `deploy_100_percent_coverage.py` - 40+ verified sources

3. **Coverage Reports**
   - Updated `valid_parcels.json` (230 files)
   - Generated fresh `coverage_status.json`
   - Real-time R2 inventory verification

---

## 🔍 Research Findings

### Louisiana Deep Dive (Hunting Priority)
**Status**: 10% coverage (7/64 parishes)
**Parishes Deployed**: Jefferson, Orleans, East Baton Rouge, Caddo, Lafayette, Calcasieu, Terrebonne

**Key Finding**: **NO free statewide parcel data exists**

**Challenge Discovered**:
- Each parish uses proprietary platforms:
  - GeoportalMaps (commercial, no REST API)
  - Azure-hosted custom sites
  - ArcGIS Online (requires authentication)
  - County-specific platforms
- No unified state portal like other states

**Recommended Approach**:
1. **Short-term**: Contact top 5 hunting parishes directly for data exports
   - Plaquemines (coastal waterfowl #1)
   - St. Bernard (coastal waterfowl #2)
   - Tangipahoa (north shore deer/turkey)
   - Livingston (north shore deer/turkey)
   - Vermilion (coastal prairie)

2. **Long-term**: Partnership with commercial provider (Regrid) or state-level data request

### Nationwide County Analysis

**Tier 1: Mega Counties (500K+ population)** - 16 total

Top 5 by Impact:
1. **Fulton, GA** - 1.1M pop (Atlanta) - ~360K parcels
2. **St. Louis County, MO** - 989K pop - ~380K parcels
3. **Gwinnett, GA** - 957K pop (Atlanta metro) - ~245K parcels
4. **Jefferson, KY** - 782K pop (Louisville) - 293K parcels ✅ **Already deployed!**
5. **Multnomah, OR** - 815K pop (Portland) - ~320K parcels

**Discovery**: Jefferson County KY was already deployed in earlier session!

**Verified Working Sources Found**:
- Jefferson County KY: `https://gis.lojic.org/maps/rest/services/LojicSolutions/OpenDataPVA/MapServer/1` ✅
- Fulton County GA: Open Data portal at `https://gisdata.fultoncountyga.gov/` 🔍
- St. Louis County MO: Open Data portal at `https://data-stlcogis.opendata.arcgis.com/` 🔍
- Gwinnett County GA: Services at `gis.gwinnettcounty.com/arcgis/rest/services/` 🔍

**Challenge**: REST endpoints require deeper investigation - many counties use restrictive access or redirects

---

## 🚀 Strategic Insights

### What Works (Free Government Data)
✅ **State-level portals** with ArcGIS REST APIs
✅ **County open data portals** (ArcGIS Hub)
✅ **Direct FeatureServer** endpoints
✅ **Web search + manual verification** approach

### What Doesn't Work
❌ **AI hallucination** of URLs (tried, failed)
❌ **Bulk statewide downloads** (most states don't offer)
❌ **LSU Atlas** for Louisiana (no parcel data)
❌ **MapServers without GeoJSON support**
❌ **Proprietary county platforms** (GeoportalMaps, etc.)

### Time Investment vs. Return
- **High ROI**: Finding statewide sources (1 source = 100% state)
- **Medium ROI**: Mega counties 500K+ (1 county = ~0.3% coverage)
- **Low ROI**: Small counties <50K (1 county = ~0.01% coverage)
- **Very Low ROI**: Individual parish/county contact (weeks for each)

---

## 📋 Remaining Work to 80% Coverage

**Current**: 70.6%
**Target**: 80%
**Gap**: 9.4% (~30M parcels needed)

### Path 1: Mega County Blitz (Recommended)
Deploy top 30 mega counties (250K+ population):
- **Parcels**: ~8-10M
- **Coverage gain**: ~8-9%
- **Challenge**: Finding/verifying REST endpoints
- **Time**: 2-3 full sessions

### Path 2: State Completion Focus
Complete highest-performing partial states:
- **Arizona**: Add Pinal + 2 more → 50% (4 counties)
- **Georgia**: Add Atlanta metros → 25% (6 counties)
- **Missouri**: Add St. Louis County → 30% (1 county!)
- **Combined**: ~5-6% coverage gain

### Path 3: Commercial Data Partnership
Purchase county-level data from Regrid/commercial:
- **Cost**: Varies by state
- **Coverage gain**: Immediate 100% for purchased states
- **Benefit**: Eliminates research time

---

## 🔧 Technical Discoveries

### Working REST Endpoint Patterns
```
# State-level
https://{state}gis.{state}.gov/arcgis/rest/services/Parcels/FeatureServer/0

# County ArcGIS Hub
https://data-{county}gis.opendata.arcgis.com/datasets/{id}

# County Direct Server
https://gis.{county}.gov/arcgis/rest/services/Parcels/FeatureServer/0

# LOJIC (Louisville)
https://gis.lojic.org/maps/rest/services/LojicSolutions/OpenDataPVA/MapServer/1
```

### Download Best Practices
- **Batch size**: 2000 records
- **Workers**: 24 parallel downloads
- **Timeout**: 180s per batch
- **CRS**: Always request EPSG:4326 (WGS84)
- **Format**: GeoJSON for compatibility
- **Processing**: Tippecanoe → PMTiles → R2

### R2 Upload
- **Endpoint**: `https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com`
- **CDN**: `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev`
- **Verification**: Use `pmtiles show {cdn_url}` before cleanup

---

## 📌 Next Session Recommendations

### Option A: Continue Mega County Blitz (Fastest to 80%)
1. Manually find REST endpoints for:
   - Fulton County, GA (Tax Parcels 2025 dataset)
   - St. Louis County, MO (Parcels dataset)
   - Gwinnett County, GA (Land Parcels dataset)
   - Multnomah, OR (Portland parcels)

2. Deploy all 4 counties (+1.2M parcels = +1.2% coverage)

3. Search for next 10 mega counties

### Option B: Focus on High-Impact States
1. **Arizona Pinal County** - 523K pop - Phoenix metro
2. **St. Louis County, MO** - 989K pop - Huge impact for MO
3. **Fulton County, GA** - 1.1M pop - Atlanta proper

Deploying just these 3 would add ~1.3M parcels (+1.3% coverage)

### Option C: Louisiana Completion (Hunting Priority)
1. Contact GIS offices for top 5 hunting parishes
2. Request free Shapefile/GeoJSON exports
3. Process manually over 1-2 weeks
4. Target: 20% LA coverage (12/64 parishes)

---

## 🎓 Lessons Learned

1. **Web search is more reliable than AI** for finding real endpoints
2. **Verify before deploying** - many MapServers don't support GeoJSON
3. **Open Data portals are goldmines** - prioritize ArcGIS Hub portals
4. **State aggregation is rare** - most states manage parcels county-by-county
5. **Mega counties matter** - 30 counties can add 9% coverage
6. **Free data has limits** - some states/counties require commercial partnerships

---

## 📂 Files Created This Session

```
/PRIORITY_EXPANSION_PLAN.md (created earlier, referenced)
/MISSING_COUNTIES_NATIONWIDE.md (new)
/SESSION_SUMMARY_2026-01-24.md (this file)
/data-pipeline/scripts/deploy_verified_sources_final.py (new)
/data-pipeline/scripts/deploy_mega_counties.py (new)
/data-pipeline/scripts/deploy_100_percent_coverage.py (created earlier)
/data-pipeline/data/valid_parcels.json (updated to 230 files)
/data-pipeline/data/coverage_status.json (regenerated)
```

---

## ✅ Recommended Immediate Actions

1. **Update COVERAGE_STATUS.md** with today's gains
2. **Commit all new scripts and docs** to git
3. **Next session**: Start with Option A (Mega County Blitz)
4. **Long-term**: Consider Regrid partnership for Louisiana

---

**Session Status**: ✅ Complete
**Coverage Achievement**: 70.6% (target 80% within reach)
**Files Deployed**: 2 new (DC, NE Douglas)
**Documentation**: Comprehensive
**Next Steps**: Clear and actionable

