# Santa Cruz County, Arizona - Parcel Deployment Report

**Deployment Date:** 2026-01-26
**Status:** ✓ Complete

---

## Data Source

| Field | Value |
|-------|-------|
| **County** | Santa Cruz County, Arizona |
| **Population** | ~47,000 |
| **Source** | Santa Cruz County Assessor's Office |
| **Endpoint** | https://mapservices.santacruzcountyaz.gov/wagis01/rest/services/ParcelSearch/Parcels/MapServer/0 |
| **Service Type** | ArcGIS REST MapServer (layer 0) |
| **Update Frequency** | Daily (per source documentation) |
| **Total Features** | 43,184 parcels |

---

## Technical Details

| Field | Value |
|-------|-------|
| **Original CRS** | EPSG:2223 (NAD83 / Arizona Central State Plane, feet) |
| **Output CRS** | EPSG:4326 (WGS84) - converted by API |
| **GeoJSON Size** | 67.2 MB |
| **PMTiles Size** | 46.6 MB |
| **Zoom Levels** | 8-16 |
| **Tile Count** | 8,515 addressed tiles, 7,402 unique |
| **Bounds** | Long: -111.367 to -110.452, Lat: 31.333 to 31.732 |

---

## Deployment

| Field | Value |
|-------|-------|
| **R2 Path** | s3://gspot-tiles/parcels/parcels_az_santa_cruz.pmtiles |
| **CDN URL** | https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_az_santa_cruz.pmtiles |
| **Registry Entry** | parcels_az_santa_cruz |
| **valid_parcels.json** | ✓ Added |
| **data_sources_registry.json** | ✓ Updated |

---

## Arizona Coverage Progress

| Metric | Before | After |
|--------|--------|-------|
| **Counties Covered** | 11/15 (73%) | 12/15 (80%) |
| **Coverage Status** | Partial | Partial |

### Arizona Counties - Current Status

**Have (12/15):**
- Apache
- Cochise
- Coconino
- Gila
- Graham
- Greenlee
- La Paz
- Maricopa
- Pimal
- Pinal
- Santa Cruz ✓ NEW
- Yavapai
- Yuma

**Missing (3/15):**
- Mohave (population ~213K, includes Bullhead City, Lake Havasu City)
- Navajo (population ~108K, includes Show Low, Holbrook)
- Pima (population ~1.04M, Tucson metro - CRITICAL - appears to be missing, may be under different name)

**Note:** Need to verify Pima County status - appears in registry but may need recheck.

---

## Download Process

```python
# Download script: data-pipeline/scripts/download_santa_cruz_az.py
# Method: ArcGIS MapServer Query API
# Batch size: 1,000 features per request
# Total batches: 44
# Download time: ~30 seconds
# Reprojection: Automatic (requested EPSG:4326 via outSR parameter)
```

---

## Validation

| Check | Status |
|-------|--------|
| **Total features match** | ✓ 43,184/43,184 |
| **PMTiles valid** | ✓ Verified with pmtiles show |
| **CDN accessible** | ✓ 200 OK |
| **Content-Type correct** | ✓ application/vnd.pmtiles |
| **Bounds correct** | ✓ Southern Arizona near Mexico border |

---

## Notes

- Santa Cruz County is located on the Arizona-Mexico border
- Includes the city of Nogales (border crossing)
- Source indicates daily updates for parcel splits, combinations, and adjustments
- Data downloaded directly in WGS84 via API parameter (no manual reprojection needed)
- Small county by population (~47K) but strategically important border area

---

## Next Steps for Arizona

To reach 100% coverage, acquire:

1. **Mohave County** (213K pop) - Bullhead City, Lake Havasu City
2. **Navajo County** (108K pop) - Show Low, Holbrook
3. **Verify Pima County** - Should have ~1M pop (Tucson) but needs verification

---

**Deployment completed successfully on 2026-01-26**
