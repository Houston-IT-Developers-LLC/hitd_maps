# HITD Maps - Quick Reference Card

**Last Updated:** 2026-01-27
**System Status:** ✅ Verified & Optimized

---

## 📊 Current Stats (At a Glance)

```
Files:        234 PMTiles (100% valid)
Coverage:     51 states (37 complete, 14 partial)
Storage:      625.3 GB on R2
Coordinates:  100% WGS84 (all correct)
Status:       ✅ Production Ready
```

---

## 🔧 Essential Commands

### Check System Health
```bash
cd data-pipeline

# Quick format check (10 min)
python3 scripts/verify_all_parcels.py

# Deep coordinate check (30-60 min)
python3 scripts/verify_coordinates_deep.py

# Consistency check (5 min)
python3 scripts/verify_coverage_consistency.py
```

### Update Coverage Report
```bash
cd data-pipeline
python3 scripts/generate_coverage_report.py
```

### Check for Data Updates
```bash
cd data-pipeline
python3 scripts/check_data_freshness.py
```

### Clean Duplicates (if new ones appear)
```bash
cd data-pipeline
python3 scripts/cleanup_duplicates.py
```

---

## 📁 Key Files

### Data Tracking
- `data-pipeline/data/valid_parcels.json` - 234 verified files
- `data-pipeline/data/coverage_status.json` - Coverage stats
- `data-pipeline/data/data_sources_registry.json` - All known sources

### Scripts
- `scripts/verify_all_parcels.py` - HTTP & format check
- `scripts/verify_coordinates_deep.py` - Coordinate validation
- `scripts/verify_coverage_consistency.py` - Cross-reference check
- `scripts/cleanup_duplicates.py` - Duplicate management

### Documentation
- `VERIFICATION_REPORT.md` - Full findings
- `FIXES_APPLIED.md` - What was fixed
- `FINAL_STATUS.md` - Current status
- `QUICK_REFERENCE.md` - This file

---

## 🎯 What's Working

✅ **All 234 files have correct WGS84 coordinates**
✅ **No invalid or corrupt files**
✅ **Perfect sync between JSON and R2**
✅ **No duplicates**
✅ **All files load on map**

---

## ⚡ Optional Optimizations

### Zoom Level Improvements (88 files)
Not critical, but would improve UX:

- **56 files** with minzoom=10 → regenerate with minzoom=5
- **32 files** with maxzoom ≤13 → regenerate with maxzoom=16

**Most urgent** (maxzoom ≤11):
```
parcels_ca_orange (maxzoom=5)
parcels_ca_sacramento (maxzoom=6)
parcels_fl_orange (maxzoom=6)
parcels_ak_statewide (maxzoom=11)
```

**Regeneration command:**
```bash
tippecanoe -o output.pmtiles \
  --minimum-zoom=5 \
  --maximum-zoom=16 \
  --drop-densest-as-needed \
  --layer=parcels \
  input.geojson
```

---

## 🗺️ Coverage Expansion Targets

### Partial States (14)
Focus on these for maximum impact:

1. **Louisiana** - 17% → Find statewide source
2. **Michigan** - 12% → Find statewide source
3. **Illinois** - 10% → Find statewide source
4. **Missouri** - 10% → Find statewide source

Check `data_sources_registry.json` for potential sources.

---

## 🔍 Troubleshooting

### "File not loading on map"
```bash
# Check if file exists in R2
aws s3 ls s3://gspot-tiles/parcels/ --endpoint-url $R2_ENDPOINT | grep filename

# Verify it's in valid_parcels.json
cat data/valid_parcels.json | grep filename

# Test HTTP access
curl -I https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/filename.pmtiles
```

### "Coverage report seems wrong"
```bash
# Regenerate from scratch
python3 scripts/generate_coverage_report.py
```

### "Finding duplicates"
```bash
# Run duplicate detection
python3 scripts/cleanup_duplicates.py
```

---

## 📅 Maintenance Schedule

### Weekly
- Visual spot-check on map

### Monthly
- `verify_all_parcels.py`
- `verify_coverage_consistency.py`

### Quarterly
- `verify_coordinates_deep.py`
- `check_data_freshness.py`
- Review partial state expansion

### Annually
- Full system re-verification
- Update STATE_BOUNDS if needed

---

## 🆘 Emergency Contacts

### If Something Breaks

1. **Check verification reports:**
   - `/tmp/verified_parcels.json`
   - `/tmp/coordinate_validation_results.json`
   - `/tmp/consistency_check_results.json`

2. **Re-run verification:**
   ```bash
   python3 scripts/verify_all_parcels.py
   ```

3. **Check git history:**
   ```bash
   git log data/valid_parcels.json
   git diff HEAD~1 data/valid_parcels.json
   ```

---

## 🔐 R2 Credentials

```bash
export AWS_ACCESS_KEY_ID=ecd653afe3300fdc045b9980df0dbb14
export AWS_SECRET_ACCESS_KEY=c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35
R2_ENDPOINT=https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com
CDN=https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev
```

---

## 📊 Quick Stats Reference

| Metric | Value |
|--------|-------|
| Total Files | 234 |
| Complete States | 37 (73%) |
| Partial States | 14 (27%) |
| Total Coverage | 72.5% |
| Storage | 625.3 GB |
| CDN | Cloudflare R2 |

---

## ✅ Pre-Deployment Checklist

Before deploying new data:

- [ ] Run `verify_all_parcels.py` ✓
- [ ] Check all files return HTTP 200 ✓
- [ ] Verify coordinates with `verify_coordinates_deep.py` ✓
- [ ] Run consistency check ✓
- [ ] Update `valid_parcels.json` ✓
- [ ] Regenerate `coverage_status.json` ✓
- [ ] Test on local map instance
- [ ] Deploy to production

---

**System Status:** 🟢 Healthy
**Last Verified:** 2026-01-27
**Next Check:** Monthly (2026-02-27)
