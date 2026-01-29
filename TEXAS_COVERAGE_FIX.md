# Texas Parcel Coverage - Critical Issues & Fix Plan

**Date:** 2026-01-27
**Status:** 🔴 **URGENT - Widespread Missing Data**

---

## 🚨 Critical Problem

**Texas is marked as "100% complete" but parcels are missing everywhere:**

- Bryan, TX (Brazos County) - ✗ Missing
- Kurten, TX (Brazos County) - ✗ Missing
- Lubbock, TX (Lubbock County) - ✗ Missing
- The Woodlands, TX (Montgomery County) - ✗ Incomplete
- **And 242+ more counties**

---

## 📊 Current State

### What We Have (10 files)

| File | Coverage | Status |
|------|----------|--------|
| parcels_tx_statewide_recent | All of TX | ⚠️ Low quality/generalized |
| parcels_tx_bexar | Bexar County | ✓ Good |
| parcels_tx_dallas | Dallas County | ✓ Good |
| parcels_tx_denton | Denton County | ✓ Good |
| parcels_tx_harris_new | Harris County | ✓ Good |
| parcels_tx_montgomery | Montgomery County | ⚠️ Incomplete (5.2 MB) |
| parcels_tx_tarrant_v2 | Tarrant County | ✓ Good |
| parcels_tx_travis_v2 | Travis County | ✓ Good |
| parcels_tx_williamson_v2 | Williamson County | ✓ Good |
| parcels_tx | Generic overlay | ⚠️ minzoom=10 |

### What We're Missing (244+ counties)

Texas has **254 total counties**. We only have detailed data for **8-9 counties**.

**Critical Missing Counties:**
- Brazos (Bryan, College Station)
- Lubbock (Lubbock)
- Montgomery (incomplete - The Woodlands area gaps)
- El Paso (El Paso)
- Collin (Plano, McKinney)
- Fort Bend (Sugar Land)
- Hidalgo (McAllen)
- Cameron (Brownsville)
- **...and 236+ more**

---

## 🔍 Root Cause Analysis

### Why Parcels Are Missing

**The TX Statewide File is Generalized:**
- `parcels_tx_statewide_recent` exists and has proper zoom settings (minzoom=5, maxzoom=15)
- BUT the data is **simplified/generalized** for file size
- Many individual properties are omitted
- Only major parcels or aggregated boundaries included

**This is common for statewide datasets:**
- Statewide files = overview/generalized
- County files = detailed/complete
- **Texas needs county-by-county downloads for full coverage**

---

## ✅ Solution: Download Individual Counties

### Texas Statewide Source

**Official Texas Parcel Data:**
- **Source:** Texas Strategic Mapping (StratMap)
- **URL:** https://stratmap.org/ and https://tnris.org/
- **ArcGIS REST API:**
  ```
  https://feature.stratmap.tnris.org/arcgis/rest/services/StratMap/StratMap22_Land_Parcels_BIG/FeatureServer/0
  ```
- **Total Records:** ~28 million parcels
- **Coverage:** All 254 Texas counties
- **Issue:** This is the generalized statewide we already have

### Individual County Sources

**Better Approach:** Download from individual County Appraisal Districts (CADs)

**Top Priority Counties (by population):**

1. **Harris County** ✓ Have it (Houston)
2. **Dallas County** ✓ Have it
3. **Tarrant County** ✓ Have it (Fort Worth)
4. **Bexar County** ✓ Have it (San Antonio)
5. **Travis County** ✓ Have it (Austin)
6. **Collin County** ✗ Need (Plano, McKinney, Frisco)
7. **Hidalgo County** ✗ Need (McAllen, Edinburg)
8. **El Paso County** ✗ Need (El Paso)
9. **Denton County** ✓ Have it
10. **Fort Bend County** ✗ Need (Sugar Land, Missouri City)
11. **Montgomery County** ⚠️ Have incomplete (The Woodlands, Conroe)
12. **Williamson County** ✓ Have it (Round Rock, Georgetown)
13. **Brazos County** ✗ **Need - User reported missing (Bryan, College Station)**
14. **Lubbock County** ✗ **Need - User reported missing (Lubbock)**

---

## 📋 Priority Action Plan

### Phase 1: Fix Reported Missing Counties (URGENT)

#### 1. Brazos County (Bryan, Kurten, College Station)
- **CAD:** Brazos Central Appraisal District (BCAD)
- **Website:** https://www.brazoscad.org/
- **GIS Portal:** Search for "Brazos County Texas GIS parcel data"
- **Population:** ~230,000
- **Priority:** 🔴 HIGH (user reported)

#### 2. Lubbock County (Lubbock)
- **CAD:** Lubbock Central Appraisal District (LCAD)
- **Website:** http://www.lcad.org/
- **GIS Portal:** Search for "Lubbock County Texas GIS parcel data"
- **Population:** ~310,000
- **Priority:** 🔴 HIGH (user reported)

#### 3. Montgomery County (The Woodlands, Conroe) - FIX
- **CAD:** Montgomery Central Appraisal District (MCAD)
- **Website:** https://mcad-tx.org/gis-data
- **Open Data:** https://data-moco.opendata.arcgis.com/
- **Current File:** 5.2 MB (clearly incomplete)
- **Population:** ~620,000
- **Priority:** 🔴 URGENT (user reported, we have bad data)

### Phase 2: Top 20 Counties by Population

Download detailed parcel data for the 20 most populous Texas counties:

```
1. Harris ✓
2. Dallas ✓
3. Tarrant ✓
4. Bexar ✓
5. Travis ✓
6. Collin ✗
7. Hidalgo ✗
8. El Paso ✗
9. Denton ✓
10. Fort Bend ✗
11. Montgomery ⚠️
12. Williamson ✓
13. Cameron ✗
14. Nueces ✗
15. Brazoria ✗
16. Bell ✗
17. Galveston ✗
18. Webb ✗
19. Jefferson ✗
20. McLennan ✗
```

**Status:** 6/20 complete, 14 needed

### Phase 3: Remaining 234 Counties

Use automated tools to download from:
1. County Appraisal District websites
2. County GIS portals
3. Texas StratMap (individual county exports)
4. OpenStreetMap-based sources

---

## 🛠️ Finding Data Sources

### Method 1: County Appraisal Districts

Every Texas county has a Central Appraisal District (CAD):

```
Format: [County]CAD.org
Examples:
- Montgomery: mcad-tx.org
- Brazos: brazoscad.org
- Lubbock: lcad.org
- Harris: hcad.org
```

**Steps:**
1. Go to [county]cad.org
2. Look for "GIS Data", "Maps", or "Property Search"
3. Find ArcGIS REST API, shapefile download, or open data portal

### Method 2: Texas GIS Portals

**Statewide Resources:**
- Texas Natural Resources Information System (TNRIS): https://tnris.org/
- StratMap: https://stratmap.org/
- Texas Open Data Portal: https://data.texas.gov/

**Search Pattern:**
```
"[County Name] County Texas parcel data ArcGIS REST"
"[County Name] CAD GIS data"
"[County Name] appraisal district parcels"
```

### Method 3: ArcGIS Hub Search

```
https://hub.arcgis.com/search?q=[County]%20Texas%20parcels
```

---

## 📝 Download Script Template

```bash
#!/bin/bash
# Download Texas counties one by one

COUNTIES_TO_DOWNLOAD=(
    "brazos"
    "lubbock"
    "collin"
    "hidalgo"
    "el_paso"
    "fort_bend"
    # ... add all 244 needed counties
)

for county in "${COUNTIES_TO_DOWNLOAD[@]}"; do
    echo "Downloading $county County..."

    # Find source URL (manual step for now)
    # Then download using download_missing_states.py or manual download

    python3 scripts/download_parcel_data.py \
        --county "$county" \
        --state TX \
        --output "data/downloads/parcels_tx_${county}.geojson"

    # Reproject if needed
    python3 scripts/smart_reproject_parcels.py \
        "data/downloads/parcels_tx_${county}.geojson"

    # Convert to PMTiles
    tippecanoe -o "processed/parcels_tx_${county}.pmtiles" \
        --minimum-zoom=5 \
        --maximum-zoom=16 \
        --drop-densest-as-needed \
        --layer=parcels \
        --force \
        "data/downloads/parcels_tx_${county}.geojson"

    # Upload to R2
    aws s3 cp "processed/parcels_tx_${county}.pmtiles" \
        s3://gspot-tiles/parcels/ \
        --endpoint-url $R2_ENDPOINT

    # Add to valid_parcels.json
    echo "  \"parcels_tx_${county}\"," >> data/valid_parcels.json

    echo "✓ Completed $county County"
done
```

---

## 🎯 Immediate Actions (Today)

### 1. Update Coverage Status

**Fix the misleading "100% complete" status:**

```python
# In coverage_status.json, change TX from:
"TX": {
    "status": "complete",
    "completeness_pct": 100,
    ...
}

# To:
"TX": {
    "status": "partial",
    "completeness_pct": 3,  # 8 counties / 254 = 3%
    "notes": "Statewide file is generalized. Need individual county downloads for accurate coverage.",
    ...
}
```

### 2. Find Sources for Critical Counties

**Montgomery County (The Woodlands):**
- Check https://data-moco.opendata.arcgis.com/ for REST API
- Download full dataset (not the 5.2 MB incomplete file)

**Brazos County (Bryan, Kurten):**
- Find Brazos CAD GIS portal
- Download parcel shapefile or access REST API

**Lubbock County (Lubbock):**
- Find Lubbock CAD GIS portal
- Download parcel shapefile or access REST API

### 3. Document the Issue

Add to CLAUDE.md:
```markdown
## Texas Coverage Note

Texas is marked as having statewide coverage via parcels_tx_statewide_recent,
but this file is generalized and missing many parcels. Individual county
downloads are required for accurate property-level coverage.

Current county coverage: 8/254 (3%)
Target: Top 20 counties by population, then expand.
```

---

## 💡 Alternative: Improve Statewide File

If downloading 254 counties is impractical, we can:

1. **Contact Texas StratMap** and request higher-resolution statewide export
2. **Download the full 28M parcel dataset** from the StratMap REST API (may take days)
3. **Process in chunks** to create detailed statewide PMTiles

**StratMap Full Download:**
```bash
# This will take a LONG time but get all 28M parcels
python3 scripts/download_missing_states.py \
    --source tx_statewide \
    --workers 20 \
    --output data/downloads/parcels_tx_statewide_full.geojson
```

---

## 📊 Success Metrics

### Current State
- ✗ Parcels missing in 246+ counties
- ✗ User complaints about Bryan, Lubbock, Montgomery, etc.
- ✗ Coverage shows "100%" but reality is 3%

### Target State
- ✓ Top 20 counties have detailed data (covering 60% of TX population)
- ✓ No user complaints about missing parcels in major cities
- ✓ Coverage accurately reflects actual availability

---

## ⏱️ Estimated Timeline

### Immediate (1-3 days)
- Fix Montgomery County (replace 5.2 MB file)
- Download Brazos County
- Download Lubbock County
- Update coverage_status.json to show reality

### Short-term (1-2 weeks)
- Download top 20 counties
- Verify quality
- Update map

### Long-term (1-3 months)
- Automated county discovery and download
- Cover all 254 counties
- 100% Texas coverage (for real this time)

---

## 🔗 Resources

### Texas Data Sources
- [Texas StratMap](https://stratmap.org/)
- [TNRIS](https://tnris.org/)
- [Texas Open Data](https://data.texas.gov/)
- [Montgomery County Open Data](https://data-moco.opendata.arcgis.com/)

### County Appraisal Districts
- Find your county: [County]CAD.org
- Example: https://mcad-tx.org/ (Montgomery)

---

**Status:** 🔴 Critical issue identified
**Next Step:** Find and download Brazos, Lubbock, and fix Montgomery County data
**Owner:** Immediate action required
