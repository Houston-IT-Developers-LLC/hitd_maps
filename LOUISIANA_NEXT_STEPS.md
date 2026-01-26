# Louisiana Parish Deployment - Next Steps

## Status: Manual Intervention Required

**Date:** 2026-01-25  
**Current Coverage:** 7/64 parishes (11%)  
**Priority Parishes:** 5 identified, NONE deployable via automation

---

## What Was Attempted

1. ✅ Researched 5 priority hunting parishes (St. Tammany, Livingston, Tangipahoa, Rapides, Bossier)
2. ✅ Searched for ArcGIS REST API endpoints
3. ✅ Tested GeoPortal Maps and custom portals
4. ✅ Created discovery script (`scrape_la_priority_parishes.py`)
5. ✅ Updated `data_sources_registry.json` with findings
6. ✅ Generated comprehensive investigation report

## Why No Deployment

**Louisiana is uniquely difficult:**
- NO statewide parcel database (unlike 36 other states)
- Each of 64 parishes maintains independent systems
- Most use **proprietary web portals** without public REST APIs
- Atlas/GeoPortal Maps (commercial platform) - no bulk export
- Even when MapServer endpoints exist, they require authentication

## Current Louisiana Coverage (Verified)

| Parish | Population | File | Source |
|--------|-----------|------|--------|
| Caddo | 237K | `parcels_la_caddo` | Shreveport area |
| Calcasieu | 203K | `parcels_la_calcasieu` | Lake Charles |
| East Baton Rouge | 456K | `parcels_la_east_baton_rouge` | Baton Rouge |
| Jefferson | 440K | `parcels_la_jefferson_v2` | New Orleans metro |
| Lafayette | 244K | `parcels_la_lafayette` | Lafayette |
| Orleans | 383K | `parcels_la_orleans_v2` | New Orleans |
| Terrebonne | 109K | `parcels_la_terrebonne` | Houma |

**Total Coverage:** ~2.1M population, 7 parishes

## Missing Priority Parishes (Hunting Focus)

| Parish | Population | Records | Status | Action Required |
|--------|-----------|---------|--------|----------------|
| **St. Tammany** | 265K | 131K | ❌ Proprietary | Contact assessor |
| **Livingston** | 142K | 80K | ❌ Proprietary | Contact assessor |
| **Tangipahoa** | 133K | 81K | ❌ Proprietary | Contact assessor |
| Rapides | 130K | Unknown | ❌ Proprietary | Contact assessor |
| Bossier | 128K | Unknown | ❌ Proprietary | Contact assessor |

---

## Recommended Actions

### HIGH PRIORITY: Direct Outreach (Free/Low-Cost)

**Email these 3 hunting parishes FIRST:**

#### 1. St. Tammany Parish Assessor
- **Contact:** St. Tammany Parish Assessor's Office
- **Website:** https://stpao.org/all-tech/
- **Phone:** Find on website
- **Request:** Bulk parcel shapefile export
- **Value:** 265K population, 131K parcels, North Shore hunting area

#### 2. Livingston Parish Assessor
- **Address:** 20400 Government Blvd., Livingston, LA 70754
- **Website:** https://www.livingstonassessor.com/mapping
- **Request:** Bulk parcel shapefile export
- **Value:** 142K population, 80K parcels, prime hunting territory

#### 3. Tangipahoa Parish Assessor
- **Website:** https://tangiassessor.com/gis-mapping
- **Request:** Bulk parcel shapefile export
- **Value:** 133K population, 81K parcels, hunting area

### Email Template

```
Subject: Request for Bulk Parcel Data for Public Mapping Platform

Dear [Parish Name] Assessor's Office,

I am writing on behalf of HITD Maps (mapsfordevelopers.com), a public mapping 
platform that provides free property parcel boundaries to landowners, hunters, 
developers, and the general public.

We would like to include [Parish Name] property parcels on our platform to help 
residents and visitors better understand property boundaries, especially for 
hunting land research and outdoor recreation planning.

Would you be able to provide a bulk export of your parcel boundaries in shapefile 
or GeoJSON format? We will:
- Properly attribute all data to your office
- Update the data annually (or at your recommended frequency)
- Provide free public access to help your residents

Our platform currently serves users across 36 states and hosts over 200 parcel 
datasets. We would be honored to include [Parish Name].

Thank you for considering this request.

Best regards,
[Your Name]
HITD Maps Development Team
mapsfordevelopers.com
```

---

## Alternative Options (If Outreach Fails)

### Option 2: Commercial Data Purchase

**Regrid** (https://regrid.com)
- Cost: ~$2,500-5,000 per parish
- Format: Standardized nationwide
- Licensing: Check restrictions
- Estimated total: $12,500-25,000 for 5 parishes

**LightBox / CoreLogic**
- Enterprise pricing
- National coverage
- Request quote

### Option 3: Manual Export (Last Resort)

Some portals allow export of visible map areas. Labor-intensive but possible:
1. Load parish web portal
2. Zoom to area
3. Export visible features (if available)
4. Repeat for entire parish
5. Merge exports

---

## Processing Pipeline (Once Data Acquired)

When you receive parcel data from parishes:

```bash
# 1. Save received file
mv ~/Downloads/parish_parcels.shp data-pipeline/data/downloads/

# 2. Convert to GeoJSON (if shapefile)
ogr2ogr -f GeoJSON -t_srs EPSG:4326 \
  parcels_la_st_tammany.geojson \
  parish_parcels.shp

# 3. Convert to PMTiles
tippecanoe -o parcels_la_st_tammany.pmtiles \
  -z 15 -Z 10 \
  --drop-densest-as-needed \
  --layer parcels \
  parcels_la_st_tammany.geojson

# 4. Upload to R2
aws s3 cp parcels_la_st_tammany.pmtiles \
  s3://gspot-tiles/parcels/ \
  --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com

# 5. Add to valid_parcels.json
# 6. Update coverage_status.json
# 7. Verify on map
```

---

## Timeline

### Week 1 (Jan 26 - Feb 1)
- [ ] Draft personalized emails for 3 priority parishes
- [ ] Send emails to assessor offices
- [ ] Call offices if email bounces

### Week 2-3 (Feb 2 - Feb 15)
- [ ] Follow up if no response
- [ ] Process any received data
- [ ] Deploy to production

### Month 2 (If No Response)
- [ ] Contact Rapides and Bossier parishes
- [ ] Evaluate commercial vendor costs
- [ ] Make purchase decision

---

## Files Created

1. **`/home/exx/Documents/C/hitd_maps/LOUISIANA_PARISH_REPORT.md`**
   - Full investigation report
   - Technical findings
   - All 5 parishes detailed

2. **`/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/scrape_la_priority_parishes.py`**
   - Discovery script (shows what was attempted)
   - Documents why automation failed

3. **`/home/exx/Documents/C/hitd_maps/data-pipeline/data/data_sources_registry.json`**
   - Updated with all 5 priority parishes
   - Includes assessor contacts, portals, estimated records

4. **`/home/exx/Documents/C/hitd_maps/LOUISIANA_NEXT_STEPS.md`**
   - This file - action plan

---

## Success Metrics

**If 3 parishes respond positively:**
- Add ~292K parcels
- Cover 540K population
- Significant boost to hunting land coverage
- Cost: $0 (just time)

**ROI:** High value for hunter demographic, zero cost if assessors cooperate

---

## Questions?

- Check `LOUISIANA_PARISH_REPORT.md` for full technical details
- See `data_sources_registry.json` for all parish contact info
- Use `scrape_la_priority_parishes.py` as template if APIs become available

**Bottom Line:** Louisiana requires manual outreach. Start with the 3 highest-priority hunting parishes, use the email template, and be patient. Success rate for assessor cooperation is typically 50-70%.
