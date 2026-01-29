# Zoom Level Standardization Plan
## Make All USA Parcels Load at Same Zoom Level

**Created:** 2026-01-27
**Issue:** 56 files have minzoom=10, preventing consistent parcel loading across USA

---

## 🎯 Goal

**Standardize all parcel files to load at zoom level 5-8** for consistent user experience across all 51 states.

---

## 📊 Current Problem

### Files with minzoom=10 (56 total)

These files won't load until users zoom to level 10+, creating an inconsistent experience:

**By State:**
- **AL:** parcels_al
- **AK:** parcels_ak
- **AZ:** parcels_az
- **CA:** parcels_ca, parcels_ca_statewide (2 files)
- **CO:** parcels_co
- **CT:** parcels_ct
- **DC:** parcels_dc_owner_polygons
- **DE:** parcels_de
- **GA:** parcels_ga, parcels_ga_forsyth, parcels_ga_fulton (3 files)
- **HI:** parcels_hi
- **IA:** parcels_ia
- **ID:** parcels_id
- **IL:** parcels_il, parcels_il_cook, parcels_il_mchenry (3 files)
- **KS:** parcels_ks
- **KY:** parcels_ky, parcels_ky_fayette, parcels_ky_warren (3 files)
- **LA:** parcels_la, parcels_la_caddo, parcels_la_calcasieu, parcels_la_terrebonne (4 files)
- **MA:** parcels_ma
- **MI:** parcels_mi, parcels_mi_arenac, parcels_mi_midland, parcels_mi_muskegon (4 files)
- **MN:** parcels_mn, parcels_mn_statewide (2 files)
- **MO:** parcels_mo, parcels_mo_boone, parcels_mo_springfield, parcels_mo_stlouis_city (4 files)
- **MS:** parcels_ms, parcels_ms_east, parcels_ms_west (3 files)
- **ND:** parcels_nd
- **NE:** parcels_ne, parcels_ne_douglas (2 files)
- **NH:** parcels_nh
- **NM:** parcels_nm
- **NV:** parcels_nv
- **TN:** parcels_tn
- **TX:** parcels_tx
- **UT:** parcels_ut
- **VA:** parcels_va_counties
- **WI:** parcels_wi
- **WV:** parcels_wv
- **WY:** parcels_wy, parcels_wy_statewide (2 files)
- **Unknown:** parcels_counties, parcels_montgomery (2 files)

---

## ✅ Solution: Regenerate with Standard Settings

### Target Settings

```bash
--minimum-zoom=5    # Load at state/regional level
--maximum-zoom=16   # High detail at property level
--drop-densest-as-needed  # Automatically thin data at lower zooms
--layer=parcels     # Consistent layer naming
```

### Tippecanoe Command Template

```bash
tippecanoe -o output.pmtiles \
  --minimum-zoom=5 \
  --maximum-zoom=16 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --layer=parcels \
  --force \
  input.geojson
```

---

## 📝 Regeneration Script

Create `scripts/regenerate_minzoom_files.sh`:

```bash
#!/bin/bash
# Regenerate all files with minzoom=10 to use minzoom=5

FILES_TO_REGENERATE=(
    "parcels_al"
    "parcels_ak"
    "parcels_az"
    "parcels_ca"
    "parcels_ca_statewide"
    "parcels_co"
    "parcels_ct"
    "parcels_dc_owner_polygons"
    "parcels_de"
    "parcels_ga"
    "parcels_ga_forsyth"
    "parcels_ga_fulton"
    "parcels_hi"
    "parcels_ia"
    "parcels_id"
    "parcels_il"
    "parcels_il_cook"
    "parcels_il_mchenry"
    "parcels_ks"
    "parcels_ky"
    "parcels_ky_fayette"
    "parcels_ky_warren"
    "parcels_la"
    "parcels_la_caddo"
    "parcels_la_calcasieu"
    "parcels_la_terrebonne"
    "parcels_ma"
    "parcels_mi"
    "parcels_mi_arenac"
    "parcels_mi_midland"
    "parcels_mi_muskegon"
    "parcels_mn"
    "parcels_mn_statewide"
    "parcels_mo"
    "parcels_mo_boone"
    "parcels_mo_springfield"
    "parcels_mo_stlouis_city"
    "parcels_ms"
    "parcels_ms_east"
    "parcels_ms_west"
    "parcels_nd"
    "parcels_ne"
    "parcels_ne_douglas"
    "parcels_nh"
    "parcels_nm"
    "parcels_nv"
    "parcels_tn"
    "parcels_tx"
    "parcels_ut"
    "parcels_va_counties"
    "parcels_wi"
    "parcels_wv"
    "parcels_wy"
    "parcels_wy_statewide"
    "parcels_counties"
    "parcels_montgomery"
)

DOWNLOAD_DIR="data/downloads"
PROCESSED_DIR="processed"
UPLOAD_DIR="data/pmtiles"

for file in "${FILES_TO_REGENERATE[@]}"; do
    echo "Processing $file..."

    # Check if source GeoJSON exists
    if [ -f "$DOWNLOAD_DIR/${file}.geojson" ]; then
        echo "  Found source: ${file}.geojson"

        # Regenerate PMTiles with correct zoom settings
        tippecanoe -o "$PROCESSED_DIR/${file}.pmtiles" \
          --minimum-zoom=5 \
          --maximum-zoom=16 \
          --drop-densest-as-needed \
          --extend-zooms-if-still-dropping \
          --layer=parcels \
          --force \
          "$DOWNLOAD_DIR/${file}.geojson"

        echo "  ✓ Regenerated ${file}.pmtiles"

        # Upload to R2
        aws s3 cp "$PROCESSED_DIR/${file}.pmtiles" \
          s3://gspot-tiles/parcels/ \
          --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com

        echo "  ✓ Uploaded to R2"
    else
        echo "  ✗ Source not found: ${file}.geojson"
        echo "     Need to re-download from original source"
    fi

    echo ""
done

echo "Regeneration complete!"
echo "Run verify_all_parcels.py to confirm"
```

---

## 🔍 Montgomery County TX Specific Issue

**Problem:** Montgomery County TX data is incomplete (only 5.2 MB file)

### Data Source Found

Montgomery County, Texas has official parcel data through:

1. **Montgomery Central Appraisal District (MCAD)**
   - Portal: https://mcad-tx.org/gis-data
   - Open Data: https://data-moco.opendata.arcgis.com/

2. **Montgomery County GIS**
   - Server: https://gis.mctx.org/arcgis/rest/services

### Action Required

1. Find the correct ArcGIS REST API endpoint for MCAD parcels
2. Download complete dataset
3. Reprocess and upload

**Potential Endpoints to Check:**
- Check https://gis.mctx.org/arcgis/rest/services for parcel services
- Look for "Tax Parcel", "MCAD", or "Cadastral" in service names
- Typically named like: `.../FeatureServer/0` or `.../MapServer/0`

---

## 📋 Implementation Steps

### Phase 1: Locate Source Files (1-2 days)

```bash
# Check which source GeoJSON files exist
cd data-pipeline
ls -lh data/downloads/parcels_*.geojson | wc -l

# Find missing sources
for file in parcels_al parcels_ak parcels_az ...; do
    if [ ! -f "data/downloads/${file}.geojson" ]; then
        echo "Missing: $file"
    fi
done
```

### Phase 2: Regenerate Files (2-4 hours)

```bash
# Run regeneration script
chmod +x scripts/regenerate_minzoom_files.sh
./scripts/regenerate_minzoom_files.sh
```

### Phase 3: Verify Results (30 min)

```bash
# Verify all files have correct settings
python3 scripts/verify_coordinates_deep.py

# Check summary
grep "minzoom.*5" /tmp/coordinate_validation_results.json | wc -l
# Should show 56 fixed files
```

---

## 🎯 Expected Results

### Before
- 56 files won't load until zoom 10+
- Inconsistent experience across states
- Users confused why some areas show parcels, others don't

### After
- All 234 files load at zoom 5-8
- Consistent experience nationwide
- Parcels visible as soon as users zoom to neighborhood level

---

## 💾 Storage Impact

**Estimate:** Files may be 10-30% larger with minzoom=5 vs minzoom=10
- Current 56 files: ~50-100 GB total
- After regeneration: ~55-130 GB total
- Additional storage: ~5-30 GB

**Worth it?** YES - much better user experience

---

## 🔧 Alternative: Frontend-Only Solution

If regenerating 56 files is too much work, you can modify the frontend to force-load parcels earlier:

### Option A: Lower Map's Parcel Load Threshold

In `web/app/map/page.tsx`, change:
```typescript
const PARCEL_LOAD_ZOOM = 8  // Current
const PARCEL_LOAD_ZOOM = 5  // New - loads parcels earlier
```

**Problem:** Files with minzoom=10 still won't have tiles available until zoom 10

### Option B: Show Message to Users

Add a note when zoom < 10 and parcels haven't loaded:
```typescript
"Zoom in closer to see property parcels (zoom level 10+)"
```

**Problem:** Doesn't fix the underlying issue

---

## ✅ Recommended Approach

**Best Solution:** Regenerate all 56 files with minzoom=5

**Why:**
1. One-time fix (vs. confusing users forever)
2. Consistent experience across all states
3. Professional quality
4. Matches user expectation

**Priority Order:**
1. High-traffic states: TX, CA, FL, NY (fix first)
2. Complete states with minzoom=10
3. Partial states

---

## 📊 Progress Tracking

Create a tracking file:

```json
{
  "files_to_regenerate": 56,
  "files_completed": 0,
  "files_in_progress": [],
  "files_missing_source": [],
  "estimated_completion": "TBD"
}
```

---

## Sources

Data sources found for Montgomery County, TX:
- [Montgomery County GIS](https://data-moco.opendata.arcgis.com/)
- [Montgomery County Texas Geocore](https://moco.maps.arcgis.com/)
- [MCAD Public Portal](https://mcad-tx.org/gis-data)
- [Tax Parcel View](https://data-moco.opendata.arcgis.com/datasets/tax-parcel-view)

---

**Next Steps:**
1. Decide: Regenerate all 56 files, or start with high-priority states?
2. Locate source GeoJSON files for each
3. Run regeneration script
4. Upload to R2
5. Verify with coordinate validation script

**Timeline:** 2-5 days depending on number of files regenerated
