# Scraping Run - January 13, 2026

## Server Details
- **Server**: 512GB RAM Server
- **Started**: 2026-01-13 06:54 UTC
- **CPU Cores**: 48
- **Max Concurrent Scrapers**: 100+

## Data Source Update Frequencies

| State | Source | Update Frequency | Last Known Update |
|-------|--------|------------------|-------------------|
| TX | TNRIS StratMap | Annually (Jan) | 2025 |
| NY | NYS ITS | Quarterly | 2025-Q4 |
| FL | DEP Cadastral | Monthly | 2026-01 |
| CA | County APIs | Varies | 2025-2026 |
| OH | DNR | Annually | 2025 |
| PA | PASDA | Annually | 2025 |
| WI | DNR Statewide | Annually | 2025 |
| NC | NC OneMap | Quarterly | 2025-Q4 |
| CO | State GIS | Annually | 2025 |
| UT | AGRC | Annually | 2025 |
| MA | MassGIS | Annually | 2025 |
| CT | CT DEEP | Annually | 2025 |
| IA | Iowa DNR | Annually | 2025 |
| MT | MSDI | Annually | 2025 |
| NV | State GIS | Annually | 2025 |
| NH | GRANIT | Annually | 2025 |
| VT | VCGI | Annually | 2025 |
| WV | State GIS | Annually | 2025 |

## Property Fields Collected

Common fields across most sources:
- **Parcel ID / APN**: Unique identifier
- **Owner Name**: Property owner(s)
- **Mailing Address**: Owner mailing address
- **Site Address**: Property location
- **Legal Description**: Legal land description
- **Acreage / Square Feet**: Property size
- **Land Use / Zoning**: Property classification
- **Assessed Value**: Tax assessment value
- **Tax District**: Taxation jurisdiction
- **Geometry**: Polygon boundary (WGS84)

## Scraping Progress

### Started at: 06:54 UTC
| Time | Scrapers | Data Size | Files |
|------|----------|-----------|-------|
| 06:55 | 37 | 459MB | 17 |
| 06:56 | 50 | 2.4GB | 39 |
| 06:58 | 69 | 3.9GB | 48 |
| 07:00 | 72 | 5.9GB | 68 |
| 07:02 | 84 | 8.3GB | 81 |
| 07:03 | 67 | 12GB | 92 |
| 07:10 | 57 | 20GB | 114 |
| 07:30 | 34 | 34GB | 132 |
| 08:00 | 21 | 51GB | 143 |
| 09:00 | 9 | 67GB | 148 |
| 10:30 | 5 | 77GB | 152 |
| 12:15 | 3 | 80GB | 154 |

### Upload to R2 Complete: 12:20 UTC
- **154 files uploaded successfully**
- **0 failures**
- Total data in R2: ~80GB

## Cloudflare R2 Upload Info

- **Bucket**: gspot-tiles
- **Public URL**: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev
- **File Pattern**: parcels/parcels_{state}.pmtiles
- **Upload Script**: scripts/bulk_upload_r2.sh

## MapLibre Integration

PMTiles can be loaded directly in MapLibre GL JS/Flutter:

```javascript
// Web
const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

map.addSource('parcels', {
  type: 'vector',
  url: 'pmtiles://https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_tx.pmtiles'
});
```

```dart
// Flutter
final pmtilesUrl = 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_tx.pmtiles';
```

## Recommended Re-scrape Schedule

- **Monthly**: FL (frequent updates)
- **Quarterly**: NY, NC (quarterly data releases)
- **Annually**: TX, CA, OH, PA, WI, and most other states (annual data releases, typically Jan-Feb)

## Notes

- All geometries are in WGS84 (EPSG:4326)
- PMTiles include simplified geometries at low zoom levels
- Full property details available at zoom 14+
