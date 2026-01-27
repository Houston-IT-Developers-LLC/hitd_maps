# Bossier Parish, Louisiana - Deployment Report

**Date**: 2026-01-26
**Status**: DEPLOYED ✓

---

## Summary

Successfully deployed Bossier Parish, Louisiana parcels to Cloudflare R2 CDN. This adds coverage for the Bossier City area (population 128,000) to our Louisiana parcel dataset.

---

## Data Source

**Discovery**: Found working ArcGIS MapServer endpoint behind the GeoPortal Maps interface that was previously thought to be proprietary-only.

- **API URL**: `https://bpagis.bossierparish.org/server/rest/services/Parcels/BossierParcels_Public_Es2/MapServer/0`
- **Format**: ArcGIS REST MapServer (supports Query and Data capabilities)
- **CRS**: Web Mercator (EPSG:3857)
- **Max Records**: 1,000 per request
- **Portal**: https://atlas.geoportalmaps.com/bossier_public/
- **Official Website**: https://www.bossierparishla.gov/police-jury/divisions/geographic-information-system-(gis)/maps

---

## Statistics

| Metric | Value |
|--------|-------|
| **Total Parcels** | 78,556 |
| **GeoJSON Size** | 119.6 MB |
| **PMTiles Size** | 54.0 MB |
| **Compression Ratio** | 2.2:1 |
| **Zoom Levels** | 8-15 |
| **Tile Count** | 3,211 |

---

## Coverage Area

**Bounding Box**:
- West: -93.841418
- South: 32.235766
- East: -93.382649
- North: 33.019512

**Major Cities Covered**:
- Bossier City
- Haughton
- Benton
- Plain Dealing

---

## Processing Details

### Download
- Method: Paginated ArcGIS REST API queries
- Batches: 79 batches × 1,000 records
- Duration: ~2 minutes
- Output: GeoJSON (119.6 MB)

### Conversion
- Tool: Tippecanoe v2.80.0
- Strategy: `--drop-densest-as-needed --extend-zooms-if-still-dropping`
- Simplification: `-r1` (minimal)
- Layer name: `parcels`
- Output: PMTiles (54.0 MB)

### Upload
- Destination: Cloudflare R2 bucket `gspot-tiles`
- Content-Type: `application/vnd.pmtiles`
- Upload time: ~2 seconds

---

## Public URLs

**PMTiles File**:
```
https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels_la_bossier.pmtiles
```

**MapLibre GL JS Usage**:
```javascript
map.addSource('bossier-parcels', {
  type: 'vector',
  url: 'pmtiles://https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels_la_bossier.pmtiles'
});

map.addLayer({
  id: 'bossier-parcels-fill',
  type: 'fill',
  source: 'bossier-parcels',
  'source-layer': 'parcels',
  minzoom: 8,
  maxzoom: 22,
  paint: {
    'fill-color': '#088',
    'fill-opacity': 0.3
  }
});
```

---

## Registry Updates

### valid_parcels.json
Added `parcels_la_bossier` to the list (now 267 total files).

### data_sources_registry.json
Updated Louisiana section:
- Changed Bossier Parish from "missing - proprietary portal" to "have"
- Added API endpoint, format, and deployment details
- Updated parish count: 8/64 parishes (12.5%)
- Total Louisiana files: 9

---

## Louisiana Coverage Progress

| Parish | Population | Status | File |
|--------|-----------|--------|------|
| **Orleans** | 383,997 | ✓ Have | parcels_la_orleans_v2 |
| **Jefferson** | 440,781 | ✓ Have | parcels_la_jefferson_v2 |
| **East Baton Rouge** | 456,781 | ✓ Have | parcels_la_east_baton_rouge |
| **Caddo (Shreveport)** | 237,848 | ✓ Have | parcels_la_caddo |
| **Lafayette** | 241,753 | ✓ Have | parcels_la_lafayette |
| **Calcasieu (Lake Charles)** | 216,785 | ✓ Have | parcels_la_calcasieu |
| **Terrebonne** | 109,580 | ✓ Have | parcels_la_terrebonne |
| **Bossier** | 128,000 | ✓ **NEW** | parcels_la_bossier |
| St. Tammany | 265,000 | Missing | - |
| Livingston | 142,000 | Missing | - |
| Tangipahoa | 133,000 | Missing | - |
| Rapides | 130,000 | Missing | - |

**Total Coverage**: 8/64 parishes (12.5%)
**Population Coverage**: ~2.2M / 4.6M (48%)

---

## Key Insights

### GeoPortal Maps Discovery
This deployment proves that GeoPortal Maps/Atlas systems (used by multiple Louisiana parishes) often have working ArcGIS REST MapServer endpoints behind their proprietary interfaces. The pattern to discover these endpoints:

1. Open browser dev tools on the web portal
2. Filter network requests for `/MapServer/` or `/FeatureServer/`
3. Look for REST service URLs in the network requests
4. Test the base MapServer URL with `?f=json`
5. Check layer 0 capabilities with `/0?f=json`

**Other Louisiana parishes using GeoPortal Maps**:
- St. Tammany (PRIORITY 1) - https://atlas.geoportalmaps.com/st_tammany
- Livingston (PRIORITY 2) - https://atlas.geoportalmaps.com/livingston

These likely have similar discoverable endpoints.

---

## Data Quality

### Parcel Attributes
- AssessmentNumber
- AssessmentName (owner)
- Roll
- Ward
- LocationCode
- PhysicalAddress
- And more...

### Geometry Quality
- Polygon geometries
- Clean topology
- Properly closed rings
- No major gaps or overlaps observed

---

## Next Steps

### Immediate Priorities
1. **St. Tammany Parish** (265K pop) - Use same discovery technique
2. **Livingston Parish** (142K pop) - Use same discovery technique
3. **Tangipahoa Parish** (133K pop) - Custom GIS portal
4. **Rapides Parish** (130K pop) - RAPC GIS system

### Long-term Strategy
- Louisiana has NO statewide parcel database
- Must acquire parish-by-parish (64 total)
- Many parishes use proprietary portals (GeoPortal Maps, Beacon, etc.)
- Systematic discovery of hidden REST endpoints could unlock 10+ more parishes

---

## Files Created

- **Script**: `/home/exx/Documents/C/hitd_maps/data-pipeline/scripts/deploy_la_bossier.py`
- **GeoJSON**: `/home/exx/Documents/C/hitd_maps/data-pipeline/downloads/parcels_la_bossier.geojson` (119.6 MB)
- **PMTiles**: `/home/exx/Documents/C/hitd_maps/data-pipeline/processed/parcels_la_bossier.pmtiles` (54.0 MB)
- **R2 Upload**: `s3://gspot-tiles/parcels_la_bossier.pmtiles`

---

## Lessons Learned

1. **Don't trust "proprietary portal" labels** - Many have public REST APIs underneath
2. **Browser dev tools are essential** - Network tab reveals hidden endpoints
3. **MapServers can be queried** - Even without FeatureServer, MapServer layer 0 often supports Query operations
4. **Web Mercator is common** - Most parish GIS systems use EPSG:3857
5. **Pagination works reliably** - 1,000 records per batch is stable

---

## Technical Notes

### CRS Handling
Data was already in Web Mercator (EPSG:3857), which is ideal for web maps. Tippecanoe automatically converts to WGS84 (EPSG:4326) for PMTiles storage.

### Tippecanoe Strategy
Used aggressive zoom extension strategy to ensure good visibility at all zoom levels:
- Start at zoom 8 (regional view)
- Max zoom 15 (street-level detail)
- Drop densest features as needed to stay under tile size limits
- Extend zooms if still dropping to preserve data

### R2 Upload
Standard boto3/AWS CLI upload with:
- Correct content-type header (`application/vnd.pmtiles`)
- Public bucket with CDN distribution
- Immediate availability after upload

---

## Conclusion

Bossier Parish deployment successfully adds 78,556 parcels to our Louisiana coverage. The discovery of a working MapServer endpoint behind the GeoPortal Maps interface opens the door to potentially 2-3 more high-priority parishes using the same system.

**Impact**: This brings Louisiana from 7 to 8 parishes (11% → 12.5%) and demonstrates a scalable approach for proprietary portal systems.

---

**Deployment Script**: `deploy_la_bossier.py`
**Deployed By**: Claude Code Agent
**Deployment Time**: ~3 minutes (download + convert + upload)
