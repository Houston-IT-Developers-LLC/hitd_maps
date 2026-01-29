# Immediate Actions Required - Parcel Coverage Issues

**Date:** 2026-01-27
**Priority:** 🔴 URGENT

---

## 🚨 Critical Findings

### What You Discovered
Parcels are missing across Texas in many locations:
- Bryan, TX
- Kurten, TX
- Lubbock, TX
- The Woodlands, TX
- **"More issues than good ones"**

### Root Cause Identified

**Texas Coverage is Actually 3%, NOT 100%:**
- Have detailed data for only **8 out of 254 counties**
- The statewide file (`parcels_tx_statewide_recent`) is **generalized/incomplete**
- Missing **246 counties** with individual parcel data

**This same issue likely affects other "complete" states too!**

---

## ✅ What Was Fixed Today

### 1. Verification Complete
- ✅ Verified all 234 PMTiles files
- ✅ Confirmed 100% have correct WGS84 coordinates
- ✅ Removed 2 invalid files
- ✅ Cleaned 29 duplicates (saved 3.1 GB)
- ✅ Updated coverage_status.json

### 2. Issue Identified
- ✅ Found 56 files with minzoom=10 (won't load until zoomed in)
- ✅ Identified Texas coverage problem (statewide file is generalized)
- ✅ Updated TX status from "100% complete" to "3% complete"

### 3. Documentation Created
- ✅ [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md) - Full verification results
- ✅ [FIXES_APPLIED.md](FIXES_APPLIED.md) - What was fixed
- ✅ [FINAL_STATUS.md](FINAL_STATUS.md) - System status
- ✅ [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick commands
- ✅ [ZOOM_STANDARDIZATION_PLAN.md](ZOOM_STANDARDIZATION_PLAN.md) - Fix minzoom=10 files
- ✅ [TEXAS_COVERAGE_FIX.md](TEXAS_COVERAGE_FIX.md) - Texas county-by-county plan

---

## 🎯 Next Steps (Priority Order)

### Priority 1: Fix Zoom Levels (Quick Win) - 1-2 days

**Problem:** 56 files have minzoom=10, preventing consistent parcel loading

**Solution:** Regenerate these files with minzoom=5

**Impact:** All USA parcels will load at the same zoom level

**See:** [ZOOM_STANDARDIZATION_PLAN.md](ZOOM_STANDARDIZATION_PLAN.md)

**Quick Start:**
```bash
# For files where you have source GeoJSON
tippecanoe -o output.pmtiles \
  --minimum-zoom=5 \
  --maximum-zoom=16 \
  --drop-densest-as-needed \
  --layer=parcels \
  input.geojson
```

### Priority 2: Fix Texas Missing Counties (Medium) - 1-2 weeks

**Problem:** Texas shows only 8 counties, missing 246

**Solution:** Download individual county data

**Start With These (User Reported Missing):**
1. **Montgomery County** - Replace incomplete 5.2 MB file
   - Source: https://data-moco.opendata.arcgis.com/
   - Find REST API endpoint for MCAD Tax Parcels

2. **Brazos County** (Bryan, Kurten)
   - Find Brazos CAD GIS portal
   - Download parcel data

3. **Lubbock County** (Lubbock)
   - Find Lubbock CAD GIS portal
   - Download parcel data

**See:** [TEXAS_COVERAGE_FIX.md](TEXAS_COVERAGE_FIX.md)

### Priority 3: Check Other "Complete" States (Long-term) - 1 month

**Question:** Are other states also using generalized statewide files?

**Action:** Verify actual quality of statewide files for:
- California
- Florida
- New York
- Other large states

---

## 📊 Current System Status

### ✅ Working Well
- 234 files verified with correct coordinates
- No invalid/corrupt files
- Perfect sync between JSON and R2
- No duplicates
- All files load (but at different zoom levels)

### ⚠️ Needs Improvement
- **56 files** need zoom level regeneration (minzoom 10 → 5)
- **Texas** needs county-by-county downloads (246 counties missing)
- **Possibly other states** with similar statewide generalization issues

---

## 🛠️ Tools & Scripts Available

### Verification
```bash
# Check all files
python3 scripts/verify_all_parcels.py

# Deep coordinate check
python3 scripts/verify_coordinates_deep.py

# Consistency check
python3 scripts/verify_coverage_consistency.py
```

### Download & Process
```bash
# Smart reproject (auto-detect CRS)
python3 scripts/smart_reproject_parcels.py input.geojson

# Convert to PMTiles
tippecanoe -o output.pmtiles --minimum-zoom=5 --maximum-zoom=16 input.geojson

# Upload to R2
aws s3 cp file.pmtiles s3://gspot-tiles/parcels/ --endpoint-url $R2_ENDPOINT
```

---

## 💡 Quick Wins You Can Do Now

### 1. Lower Frontend Parcel Load Threshold (5 minutes)

**File:** `web/app/map/page.tsx`

```typescript
// Change this:
const PARCEL_LOAD_ZOOM = 8

// To this:
const PARCEL_LOAD_ZOOM = 5  // Load parcels earlier
```

**Impact:** Users see parcels sooner (but files with minzoom=10 still won't show until zoom 10)

### 2. Show User Message About Missing Data (10 minutes)

Add a note on the map when viewing areas with incomplete data:

```typescript
// In map component
if (currentState === 'TX' && zoom >= 10) {
  showMessage("Texas: Detailed parcels available for major counties. Working on expanding coverage.")
}
```

### 3. Focus on High-Traffic Areas First

Don't try to download all 246 TX counties at once. Start with:
- Top 20 counties by population (covers 60%+ of Texas residents)
- User-reported missing areas (Brazos, Lubbock, Montgomery)
- Major metro areas

---

## 📈 Expected Timeline

### This Week
- ✅ Verification complete (DONE)
- ⏳ Fix 5-10 highest priority minzoom files
- ⏳ Find data sources for Brazos, Lubbock, Montgomery counties

### Next 2 Weeks
- Download and process 3-5 priority Texas counties
- Regenerate 20-30 more minzoom files
- Test improvements on map

### Next Month
- Complete top 20 Texas counties
- Regenerate all 56 minzoom files
- Audit other large states for similar issues

---

## 🎯 Success Criteria

### Short-term (1 week)
- [ ] 10+ minzoom files regenerated with minzoom=5
- [ ] Montgomery County replaced with complete data
- [ ] Brazos County added
- [ ] Lubbock County added

### Medium-term (1 month)
- [ ] All 56 minzoom files fixed
- [ ] Top 20 Texas counties have detailed data
- [ ] User can see parcels in all major Texas cities

### Long-term (3 months)
- [ ] Consistent zoom levels nationwide
- [ ] All 254 Texas counties covered
- [ ] Other large states audited and fixed

---

## 📞 Questions to Answer

1. **Do you want to regenerate all 56 minzoom files?**
   - Or start with top 10-20 high-traffic states?

2. **For Texas, how many counties should we target?**
   - Option A: Top 20 (covers 60% of population)
   - Option B: Top 50 (covers 80%+ of population)
   - Option C: All 254 (100% coverage, but 3+ months work)

3. **Should we audit other large states?**
   - Check if CA, FL, NY, IL, etc. have similar statewide generalization issues

---

## 📁 Reference Documents

| Document | Purpose |
|----------|---------|
| [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md) | Complete verification findings |
| [TEXAS_COVERAGE_FIX.md](TEXAS_COVERAGE_FIX.md) | Texas county-by-county plan |
| [ZOOM_STANDARDIZATION_PLAN.md](ZOOM_STANDARDIZATION_PLAN.md) | Fix 56 minzoom files |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Commands cheat sheet |
| [FIXES_APPLIED.md](FIXES_APPLIED.md) | What was fixed today |

---

## ✨ Bottom Line

**Good News:**
- ✅ All coordinate data is correct
- ✅ System is verified and optimized
- ✅ We identified the root cause of missing parcels

**Challenge:**
- ⚠️ Texas (and possibly other states) need county-level data downloads
- ⚠️ 56 files need zoom level regeneration

**Solution:**
- Tackle in phases: Quick wins first, then systematic expansion
- Focus on user-reported issues and high-traffic areas
- Document and track progress

---

**Your verification work is complete!** The issues you're seeing are now documented with clear action plans.
