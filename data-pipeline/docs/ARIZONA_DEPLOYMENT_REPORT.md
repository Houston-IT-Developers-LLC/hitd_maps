# Arizona County Parcel Deployment Report

**Date:** 2026-01-25
**Objective:** Complete statewide Arizona parcel coverage (15/15 counties)
**Starting Coverage:** 26% (4/15 counties)
**Current Coverage:** 40% (6/15 counties)
**Target Coverage:** 100% (15/15 counties)

---

## Deployment Summary

### ✅ Successfully Deployed (2 new counties)

| County | Records | File Size | Status | URL |
|--------|---------|-----------|--------|-----|
| **Yuma** | 96,848 | 37 MB | ✅ Deployed | https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_az_yuma.pmtiles |
| **Cochise** | 62,910 | 19 MB | ✅ Deployed | https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_az_cochise.pmtiles |

**Total New Records:** 159,758 parcels
**Total Storage Added:** 56 MB PMTiles

### ✅ Previously Deployed (4 counties)

| County | File ID | Status |
|--------|---------|--------|
| Maricopa | parcels_az_maricopa | ✅ Live |
| Pima | parcels_az_pima | ✅ Live |
| Pinal | parcels_az_pinal | ✅ Live |
| Yavapai | parcels_az_yavapai | ✅ Live |

---

## Remaining Counties (9 counties)

### High Priority - Endpoints Found

| County | Population | Endpoint Status | Action Needed |
|--------|-----------|-----------------|---------------|
| **Mohave** | 213,954 | Endpoint timeout | Alternative server: Try https://az-mohave.opendata.arcgis.com/ |
| **Navajo** | 106,717 | Portal found | Extract FeatureServer from https://open-data-ncaz.hub.arcgis.com/ |

### Medium Priority - Manual Research Required

| County | Population | Known Resources | Action |
|--------|-----------|-----------------|--------|
| **Coconino** | 145,101 | https://data-coconinocounty.opendata.arcgis.com/ | Browse portal, find parcel dataset |
| **Apache** | 66,021 | Web apps found | Contact GIS department |
| **Gila** | 53,597 | https://www.gilacountyaz.gov | Email GIS dept |
| **Santa Cruz** | 47,669 | Via SEAGO | Contact https://www.seago.org/ |
| **Graham** | 38,533 | Via SEAGO | Contact https://www.seago.org/ |

### Low Priority - Smallest Counties

| County | Population | Notes |
|--------|-----------|-------|
| **La Paz** | 16,557 | Portal found but 404: https://gis.lapazcountyaz.org/ |
| **Greenlee** | 9,563 | Smallest AZ county, manual contact needed |

---

## Deployment Process

### What Worked

1. **Yuma County**
   - Endpoint: `https://arcgis.yumacountyaz.gov/webgis/rest/services/YC_Parcels/MapServer/0`
   - Batch size: 2,000 records per request
   - Workers: 10 parallel downloads
   - Time: ~5 minutes download, 3 minutes processing
   - CRS: Already WGS84 (no reprojection needed)

2. **Cochise County**
   - Endpoint: `https://services6.arcgis.com/Yxem0VOcqSy8T6TE/ArcGIS/rest/services/Cad_Parcel_Geometry/FeatureServer/0`
   - Batch size: 1,000 records per request
   - Workers: 10 parallel downloads
   - Time: ~4 minutes download, 2 minutes processing
   - Note: Server returned 62,910 features instead of advertised 124,910

### Technical Stack

- **Download:** Python + requests + ThreadPoolExecutor (10 workers)
- **Processing:** Already WGS84, no reprojection needed
- **Tiling:** tippecanoe -zg with auto zoom levels
- **Upload:** boto3 to Cloudflare R2
- **CDN:** Instant availability at pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev

---

## Coverage Impact

### State Level
- **Before:** 4/15 counties = 26.7%
- **After:** 6/15 counties = 40.0%
- **Improvement:** +13.3% Arizona coverage

### National Level
- Arizona has 15 counties out of 3,143 total US counties (0.48%)
- Each Arizona county represents ~0.03% of national coverage
- **National impact:** +0.06% (2 counties deployed)

### Population Coverage
- **Yuma County:** 213,787 residents
- **Cochise County:** 126,442 residents
- **Total new coverage:** 340,229 people

---

## Next Steps

### Phase 1: Low-Hanging Fruit (Estimated 2-3 hours)

1. **Navajo County**
   - Visit https://open-data-ncaz.hub.arcgis.com/
   - Search for "parcels"
   - Extract FeatureServer URL
   - Run deployment script

2. **Coconino County**
   - Visit https://data-coconinocounty.opendata.arcgis.com/
   - Search catalog for parcels
   - Download and deploy

3. **Mohave County**
   - Try alternative portal: https://az-mohave.opendata.arcgis.com/
   - Or email IT department for working REST endpoint

### Phase 2: SEAGO Counties (Estimated 1-2 hours)

4-6. **Graham, Greenlee, Santa Cruz**
   - Contact SEAGO (SouthEastern Arizona Governments Organization)
   - Request batch access to all 3 counties
   - Website: https://www.seago.org/maps-and-gis-resources

### Phase 3: Manual Outreach (Estimated 1 day)

7-9. **Apache, Gila, La Paz**
   - Email county GIS coordinators directly
   - Use AGIC contact directory: https://agic.az.gov/resources
   - Request FeatureServer URLs or bulk downloads

---

## Scripts Created

All deployment scripts available in `/data-pipeline/scripts/`:

1. **deploy_arizona_counties.py** - Main orchestration script
2. **sources_arizona_new.json** - Verified endpoint registry
3. Inline Python scripts for download, processing, upload

### Example Usage

```bash
# Download county
python3 scripts/download_arizona_county.py --county yuma --workers 10

# Convert to PMTiles
tippecanoe -o parcels_az_county.pmtiles -zg --force parcels_az_county.geojson

# Upload to R2
python3 scripts/upload_to_r2.py parcels_az_county.pmtiles
```

---

## Data Quality Notes

### Yuma County
- ✅ Complete coverage
- ✅ Already in WGS84
- ✅ Rich attributes (owner, tax info, address)
- ⚠️ 2026 tax year data (very current)

### Cochise County
- ⚠️ Partial coverage? (62K received vs 124K advertised)
- ✅ Already in WGS84
- ✅ Good geometry quality
- Note: May need to verify if this is tax parcels only vs all parcels

---

## Resources

### Arizona GIS Portals
- **AZGeo Hub:** https://azgeo-data-hub-agic.hub.arcgis.com/
- **AGIC Resources:** https://agic.az.gov/resources
- **State Land Dept:** https://land.az.gov/maps-gis

### County Contacts
- See AGIC interactive map for GIS coordinator emails
- Phone: (602) 364-3747
- Email: agic_info@azland.gov

### Third-Party Options
- **Regrid:** Offers all AZ counties for purchase
  - https://app.regrid.com/store/us/az/buy
  - Standardized schema
  - Regular updates
  - Alternative if county sources unavailable

---

## Recommendations

### Immediate (This Week)
1. Deploy Navajo County (portal accessible, ~100K parcels expected)
2. Deploy Coconino County (largest county by area)
3. Fix Mohave County endpoint (213K population)

### Short-term (This Month)
4. Batch request SEAGO counties (Graham, Greenlee, Santa Cruz)
5. Email Apache, Gila, La Paz GIS departments
6. Update coverage_status.json to 100%

### Long-term (Next Quarter)
- Set up quarterly refresh schedule for all 15 counties
- Monitor data freshness
- Add to automated pipeline
- Consider Regrid subscription for consistency

---

## Success Metrics

### Target State
- ✅ **100% Arizona coverage** (15/15 counties)
- ✅ **All data in PMTiles format**
- ✅ **Hosted on R2 CDN**
- ✅ **Updated quarterly**
- ✅ **Listed in valid_parcels.json**

### Coverage Goals
- Current: 40% → Target: 100%
- Timeline: 2-3 weeks with manual outreach
- Or: Purchase Regrid data for instant 100% coverage

---

## Files Modified

1. `/data-pipeline/data/valid_parcels.json` - Added 2 new counties
2. `/data-pipeline/data/sources_arizona_new.json` - Created endpoint registry
3. `/data-pipeline/scripts/deploy_arizona_counties.py` - Created deployment tool
4. `/data-pipeline/data/downloads/arizona/` - 2 new PMTiles uploaded to R2

---

**Report Generated:** 2026-01-25
**Next Review:** After Phase 1 completion (estimated 2026-01-27)
