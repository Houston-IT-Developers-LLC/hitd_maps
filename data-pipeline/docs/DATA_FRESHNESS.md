# GSpot Parcel Data Freshness Tracker

## Last Updated: January 13, 2026

## Pipeline Overview

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. SCRAPE   │───▶│  2. REPROJECT│───▶│  3. TILE     │───▶│  4. UPLOAD   │───▶│  5. DISPLAY  │
│  ArcGIS APIs │    │  EPSG:3857   │    │  tippecanoe  │    │  Cloudflare  │    │  MapLibre GL │
│  → GeoJSON   │    │  → WGS84     │    │  → PMTiles   │    │  R2 CDN      │    │  Flutter/Web │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

## Data Sources & Update Frequencies

### Statewide Data Sources

| State | Source | API Type | Update Freq | Last Scraped | Tax Year |
|-------|--------|----------|-------------|--------------|----------|
| TX | TNRIS StratMap | ArcGIS REST | Annual | Jan 2026 | 2025 |
| CA | County APIs | ArcGIS REST | Quarterly | Jan 2026 | 2024-2025 |
| NY | NYS ITS | ArcGIS REST | Annual | Jan 2026 | 2024 |
| FL | County APIs | ArcGIS REST | Annual | Jan 2026 | 2024 |
| PA | PASDA | ArcGIS REST | Annual | Jan 2026 | 2024 |
| OH | County APIs | ArcGIS REST | Annual | Jan 2026 | 2024 |
| VA | VGIN | ArcGIS REST | Annual | Jan 2026 | 2024 |
| CO | State GIS | ArcGIS REST | Annual | Jan 2026 | 2024 |
| WI | State Cartographer | ArcGIS REST | Annual | Jan 2026 | 2024 |
| NC | NC OneMap | ArcGIS REST | Annual | Jan 2026 | 2024 |

### County-Level Sources

Most county assessor offices update their GIS data:
- **Annually**: After tax roll certification (typically Jan-Mar)
- **Quarterly**: Major metros (Harris, LA, Cook, etc.)
- **Monthly**: Some progressive counties

## How to Check for Updates

### 1. Check API Metadata
```bash
curl -s "{service_url}?f=json" | jq '.editingInfo.lastEditDate'
```

### 2. Compare Record Counts
```bash
curl -s "{service_url}?where=1=1&returnCountOnly=true&f=json" | jq '.count'
```

### 3. Check Tax Year Field
Most parcel data includes `tax_year` or `data_year` field indicating the assessment year.

## Recommended Update Schedule

| Priority | States | Frequency | Notes |
|----------|--------|-----------|-------|
| High | TX, CA, FL, NY | Quarterly | High user traffic |
| Medium | PA, OH, VA, CO, WI, NC | Bi-annually | Moderate traffic |
| Low | All others | Annually | Low traffic |

## Automation Scripts

### Check All Sources for Updates
```bash
python3 scripts/check_data_updates.py --all
```

### Re-scrape Single State
```bash
python3 scripts/export_county_parcels.py TX_STATEWIDE -o output/geojson
```

### Full Pipeline (Scrape → Tile → Upload)
```bash
./scripts/full_pipeline.sh TX
```

## State-by-State Status

### Complete (Ready for MapLibre)
- AK, CA, CO, CT, DE, HI, IA, MA, ND, NH, NV, SC, TN, UT, WV

### In Progress
- TX (6 agents running - expected ~28M parcels)
- PA (4 agents running)
- CA (6 agents running - expanding coverage)
- WI (1 agent running)
- OH, GA, MI, AZ, NV, IL, MO, OR, WA, NC, LA

### Needs Attention
- AR: API not responding
- OK: DNS errors
- ME: SSL certificate issues
- VT: API errors
- RI: No config available
- FL: County APIs blocking requests (need rate limiting)

## API Health Monitoring

### Common Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| Rate Limiting | 429 errors | Reduce batch_size, add delays |
| Timeout | Connection timeout | Increase timeout, smaller batches |
| SSL Errors | Certificate errors | Update certifi, check VPN |
| 403 Forbidden | Access denied | Check if API requires auth |
| DNS Errors | Host not found | API endpoint changed |

## Future Improvements

1. **Automated Update Detection**: Cron job to check API metadata weekly
2. **Incremental Updates**: Only fetch changed parcels (where available)
3. **Data Validation**: Compare parcel counts before/after updates
4. **Notification System**: Alert when data is stale (>1 year old)

## Contact for Data Issues

- Texas TNRIS: tnris.org
- California Counties: Individual county assessor offices
- National Parcel Data: regrid.com (commercial alternative)
