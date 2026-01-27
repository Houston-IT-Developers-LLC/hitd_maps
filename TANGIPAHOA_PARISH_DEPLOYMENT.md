# Tangipahoa Parish, Louisiana - Deployment Report

**Date:** 2026-01-26
**Status:** ✅ COMPLETE
**Parish:** Tangipahoa Parish, Louisiana
**Major City:** Hammond

---

## Summary

Successfully deployed 75,919 parcels from Tangipahoa Parish to R2 CDN. This parish was previously marked as "missing - proprietary portal" but we discovered a public ArcGIS REST API through their TanGIS system.

---

## Data Source

| Property | Value |
|----------|-------|
| **Provider** | Tangipahoa Parish GIS (TanGIS) |
| **API Endpoint** | `https://tangis.tangipahoa.org/server/rest/services/Cadastral/TaxParcel_A/FeatureServer/0` |
| **Format** | ArcGIS FeatureServer |
| **Update Frequency** | Every 3 weeks |
| **Original CRS** | EPSG:3452 (Louisiana South State Plane) - but API returns WGS84 GeoJSON |
| **Total Records** | 75,919 parcels |

---

## Coverage Area

- **Bounds:** -90.567467, 30.284020 to -90.242562, 31.000550 (WGS84)
- **Population:** ~133,000
- **Major City:** Hammond
- **Other Areas:** Ponchatoula, Amite, Independence

---

## Deployment Details

### Downloaded Data
- **Method:** Python script with pagination (2,000 records per request)
- **Raw Format:** GeoJSON (WGS84)
- **File Size:** 147.29 MB
- **Download Time:** ~2 minutes (38 API requests)

### PMTiles Conversion
- **Tool:** tippecanoe v2.80.0
- **Zoom Levels:** 8-14
- **Layer Name:** `parcels`
- **Output Size:** 31 MB (30.9 MiB)
- **Tile Count:** 731 tiles
- **Compression:** Gzip

### Upload to R2
- **Bucket:** gspot-tiles
- **Path:** `parcels/parcels_la_tangipahoa.pmtiles`
- **CDN URL:** `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_la_tangipahoa.pmtiles`
- **Content-Type:** `application/vnd.pmtiles`
- **Upload Speed:** ~20-45 MiB/s

---

## Key Discovery

The parish was initially listed as having "NO public REST API" and using a "proprietary web portal." However, investigation revealed:

1. **TanGIS Server:** The parish runs its own ArcGIS Server at `tangis.tangipahoa.org`
2. **Public API:** The REST services directory is publicly accessible
3. **Cadastral Services:** Tax parcels are available via FeatureServer with full query support
4. **GeoJSON Support:** The API supports `f=geojson` parameter, returning data already in WGS84
5. **No Authentication:** No API keys or authentication required

This demonstrates the value of thorough investigation - many "proprietary" systems may have public APIs that aren't well-documented.

---

## Scripts Created

1. **deploy_tangipahoa_la.py**
   - Full deployment pipeline
   - Handles download, reprojection, conversion, and upload
   - Located: `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/`

2. **download_tangipahoa_fixed.py**
   - Improved download script with proper pagination
   - Downloads all 75,919 features in chunks of 2,000
   - Includes progress tracking and error handling

---

## Data Registry Updates

### valid_parcels.json
Added: `parcels_la_tangipahoa`

### data_sources_registry.json
Updated Tangipahoa Parish entry from "missing" to "have":
- Status: `have` (previously: `missing - proprietary portal`)
- API URL: Added FeatureServer endpoint
- Format: `ArcGIS FeatureServer` (previously: `Proprietary web portal`)
- Total Records: 75,919 (previously estimated: 81,479)
- Deployed Date: 2026-01-26
- Notes: Updated with actual deployment details

Updated Louisiana summary:
- Parish Count: **11/64 parishes (17.2%)** (previously: 9/64, 14.1%)

---

## Louisiana Coverage Update

Louisiana now has **11 parishes** covered:

| # | Parish | File |
|---|--------|------|
| 1 | Ascension | parcels_la_ascension |
| 2 | Bossier | parcels_la_bossier |
| 3 | Caddo (Shreveport) | parcels_la_caddo |
| 4 | Calcasieu (Lake Charles) | parcels_la_calcasieu |
| 5 | East Baton Rouge | parcels_la_east_baton_rouge |
| 6 | Jefferson | parcels_la_jefferson_v2 |
| 7 | Lafayette | parcels_la_lafayette |
| 8 | Orleans (New Orleans) | parcels_la_orleans_v2 |
| 9 | St. Bernard | parcels_la_st_bernard |
| 10 | **Tangipahoa (Hammond)** | **parcels_la_tangipahoa** ✨ NEW |
| 11 | Terrebonne | parcels_la_terrebonne |

**Remaining Priority Parishes:**
- St. Tammany (population: 265K) - Atlas/GeoPortal proprietary
- Livingston (population: 142K) - Atlas/GeoPortal proprietary
- Rapides (population: 130K) - RAPC GIS

---

## Validation

### PMTiles Metadata
```
✅ Spec Version: 3
✅ Tile Type: Vector Protobuf (MVT)
✅ Bounds: -90.567467, 30.284020 to -90.242562, 31.000550
✅ Zoom Levels: 8-14
✅ Tile Count: 731 tiles
✅ Compression: Gzip
✅ Layer: parcels
```

### CDN Verification
```
✅ HTTP Status: 200 OK
✅ Content-Type: application/vnd.pmtiles
✅ Content-Length: 32,408,444 bytes (30.9 MB)
✅ CDN: Cloudflare
✅ Accessible: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_la_tangipahoa.pmtiles
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Total Parcels | 75,919 |
| Raw GeoJSON Size | 147.29 MB |
| PMTiles Size | 30.9 MB (79% reduction) |
| Download Time | ~2 minutes |
| Conversion Time | ~15 seconds |
| Upload Time | ~3 seconds |
| **Total Time** | **~3 minutes** |

---

## Next Steps

### Recommended Louisiana Parishes
1. **St. Tammany** (265K pop) - Need to investigate Atlas/GeoPortal Maps backend
2. **Livingston** (142K pop) - Same Atlas system as St. Tammany
3. **Rapides** (130K pop) - RAPC GIS system
4. **Ouachita** (156K pop) - Monroe area
5. **St. Landry** (82K pop) - Opelousas area

### Investigation Tips
- Check for `/server/rest/services` directories on parish domains
- Look for ArcGIS server URLs in web map application network traffic
- Try variations: `gis.parish.gov`, `maps.parish.gov`, `[parish]gis.org`
- Check for hosted services on ArcGIS Online or state platforms

---

## Lessons Learned

1. **Don't Trust Initial Reports:** "Proprietary portal" doesn't mean no public API
2. **Check Network Traffic:** Web applications often call public REST APIs
3. **TanGIS Pattern:** Other parishes may use similar TanGIS or parish-specific servers
4. **GeoJSON is King:** When available, GeoJSON format from ArcGIS eliminates reprojection needs
5. **Pagination Works:** Python pagination is reliable for large datasets (38 requests for 76K features)

---

## Credits

- **Data Source:** Tangipahoa Parish GIS (TanGIS)
- **Data Provider:** Tangipahoa Parish Assessor
- **Deployment:** Claude Code + HITD Maps Team
- **Tools:** Python 3, tippecanoe, AWS CLI, ogr2ogr

---

## Contact

- **TanGIS Website:** https://tangipahoa.org/residents/gis-mapping/tangis/
- **Assessor:** https://tangiassessor.com/
- **Parish Government:** https://tangipahoa.org/

---

**Deployment Completed:** 2026-01-26 23:47:27 UTC
**Verification Completed:** 2026-01-26 23:48:18 UTC
**Status:** ✅ LIVE ON CDN
