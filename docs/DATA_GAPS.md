# HITD Maps Data Gaps & Acquisition Guide

**Last Updated:** 2026-01-24

This document tracks what data is missing and provides instructions for acquiring it.

## Quick Status

| Priority | Category | Items |
|----------|----------|-------|
| P1 | Missing States | 1 (Rhode Island) |
| P2 | High-Value Counties | 5+ (TX Montgomery, Brazos, etc.) |
| P3 | Statewide Gaps | 19 states with county-only coverage |

## Priority 1: Missing States

### Rhode Island (RI)

**Status:** No coverage

| Field | Value |
|-------|-------|
| Estimated Records | 400,000 |
| Known Source | rigis.org |
| Population | 1.1 million |
| Priority | HIGH |

**To Acquire:**

```bash
# 1. Find the API endpoint
python3 data-pipeline/agent/source_finder.py --state RI

# 2. Once found, add to sources and download
python3 data-pipeline/scripts/download_missing_states.py --source ri_statewide --workers 10

# 3. Process and upload
python3 data-pipeline/scripts/parallel_process_upload.py 4
```

**Manual Research:**
- Check https://www.rigis.org/
- Search for "Rhode Island parcel data ArcGIS"
- Contact RI Division of Planning

---

## Priority 2: High-Value Missing Counties

These counties have significant population but no parcel data.

### Texas - Montgomery County (The Woodlands)

| Field | Value |
|-------|-------|
| Population | 620,000 |
| Major Cities | The Woodlands, Conroe |
| Status | **MISSING** |
| Known Sources | mcad-tx.org, TNRIS extract |

**Why Important:** The Woodlands is a major planned community with significant commercial development.

**To Acquire:**
```bash
# Option 1: Extract from TNRIS statewide
python3 data-pipeline/scripts/download_missing_states.py \
  --source tx_statewide \
  --bbox "-96.0,29.8,-95.0,30.6" \
  --output parcels_tx_montgomery

# Option 2: Find Montgomery CAD API
# Check: https://www.mcad-tx.org/
```

### Texas - Brazos County (Bryan/College Station)

| Field | Value |
|-------|-------|
| Population | 233,000 |
| Major Cities | Bryan, College Station |
| Status | **MISSING** |
| Known Sources | brazoscad.org |

**Why Important:** Texas A&M University area with significant student housing and commercial development.

### Texas - Liberty County (Cleveland)

| Field | Value |
|-------|-------|
| Population | 91,000 |
| Major Cities | Cleveland, Liberty |
| Status | **MISSING** |

### Texas - Galveston County

| Field | Value |
|-------|-------|
| Population | 350,000 |
| Major Cities | Galveston, League City, Texas City |
| Status | **MISSING** |

### Texas - Collin County (Plano, Frisco)

| Field | Value |
|-------|-------|
| Population | 1,100,000 |
| Major Cities | Plano, Frisco, McKinney, Allen |
| Status | **MISSING** |

**Why Important:** One of the fastest-growing counties in the US, major DFW suburb.

---

## Priority 3: States Needing Statewide Coverage

These states have county-level data but would benefit from statewide coverage.

### California (13% coverage)

**Current:** SF, LA, Sacramento, Orange, Fresno, Sonoma
**Missing:** San Diego, Riverside, San Bernardino, Alameda, Santa Clara, and 50+ other counties

**Potential Sources:**
- CA State Geoportal: https://gis.data.ca.gov/
- Individual county assessors
- CAL FIRE parcel data

### Michigan (8% coverage)

**Current:** Wayne, Oakland, Kent, Macomb, Ottawa
**Missing:** Western and northern Michigan

### Georgia (3% coverage)

**Current:** Gwinnett, Cobb, DeKalb, Chatham, Richmond
**Missing:** Fulton (downtown Atlanta!), Clayton, and 150+ counties

**Priority:** Fulton County (Atlanta) is critical

### Illinois (5% coverage)

**Current:** Cook, DuPage, Lake, Will
**Missing:** Kane, McHenry, and 95+ counties

### Arizona (26% coverage)

**Current:** Maricopa, Pima, Pinal, Yavapai
**Missing:** Remaining counties

### All Partial States

| State | Coverage | Missing | Priority |
|-------|----------|---------|----------|
| CA | 13% | 50+ counties | High |
| GA | 3% | Fulton + 150 | High |
| MI | 8% | 75+ counties | Medium |
| IL | 5% | 95+ counties | Medium |
| AZ | 26% | 10+ counties | Medium |
| MO | 5% | 100+ counties | Low |
| MN | 4% | 80+ counties | Low |
| LA | 6% | 60+ parishes | Low |
| SC | 6% | 43 counties | Low |
| OR | 5% | 34 counties | Low |
| AL | 4% | 64 counties | Low |
| WY | 4% | 22 counties | Low |
| KY | 2% | 117 counties | Low |
| MS | 2% | 80 counties | Low |
| OK | 2% | 75 counties | Low |
| KS | 1% | 103 counties | Low |
| SD | 7% | 63 counties | Low |

---

## Enrichment Data Gaps

### FEMA Flood Zones

**Status:** Partial coverage
**Gap:** Not all counties have FIRM maps digitized
**Source:** https://msc.fema.gov/

### SSURGO Soils

**Status:** Partial coverage
**Gap:** Some areas still use older STATSGO data
**Source:** https://websoilsurvey.nrcs.usda.gov/

---

## Data Acquisition Commands

### Check for Updates
```bash
# Passive check - doesn't change anything
python3 data-pipeline/scripts/check_data_freshness.py
```

### Find Missing Sources
```bash
# Uses local AI to search for data sources
python3 data-pipeline/agent/source_finder.py --state RI
python3 data-pipeline/agent/source_finder.py --state CA
```

### Download Specific Source
```bash
# Download from known API
python3 data-pipeline/scripts/download_missing_states.py --source <source_id> --workers 10
```

### Process and Upload
```bash
# Full pipeline: reproject → tile → upload
python3 data-pipeline/scripts/parallel_process_upload.py 4
```

### Verify Results
```bash
# Check if file is valid
pmtiles show output/parcels_<state>_<county>.pmtiles

# Update valid parcels list
python3 data-pipeline/scripts/generate_coverage_report.py
```

---

## Known Data Sources by State

For complete source registry, see:
```
data-pipeline/data/data_sources_registry.json
```

### Common Source Patterns

| Source Type | URL Pattern | Example |
|-------------|-------------|---------|
| State GIS | gis.{state}.gov | gis.ny.gov |
| ArcGIS Hub | {state}.maps.arcgis.com | texas.maps.arcgis.com |
| County Assessor | {county}assessor.{state}.gov | Various |
| ESRI Open Data | hub.arcgis.com/search | Search by state |

---

## Update Schedule

| Data Type | Typical Update | When to Check |
|-----------|----------------|---------------|
| State Parcels | Annual (Q1) | Monthly |
| County Parcels | Quarterly-Annual | Monthly |
| PAD-US | Annual (Nov) | Annually |
| Protomaps Planet | Monthly | Monthly |
| HIFLD | Quarterly | Quarterly |

---

## Related Documentation

- [DATA_INVENTORY.md](DATA_INVENTORY.md) - What we currently have
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - How to work with the pipeline
- [data_sources_registry.json](../data-pipeline/data/data_sources_registry.json) - All known sources
