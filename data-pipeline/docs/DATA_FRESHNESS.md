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


<!-- AGENT_STATUS_START -->
## Automated API Health Check

Last updated by Data Agent: 2026-01-17 19:57:47

| Source | Status | Records | Last Check |
|--------|--------|---------|------------|
| tx_statewide | ✅ | 14,347,648 | 2026-01-17 19:57 |
| tx_statewide_recent | ✅ | 14,347,648 | 2026-01-17 19:57 |
| ny_statewide_v2 | ✅ | 3,713,082 | 2026-01-17 19:57 |
| mt_statewide_v2 | ✅ | 915,189 | 2026-01-17 19:57 |
| tn_statewide | ❌ | Error | 2026-01-17 19:57 |
| or_statewide | ✅ | 0 | 2026-01-17 19:57 |
| pa_statewide | ✅ | 4,280,310 | 2026-01-17 19:57 |
| pa_pasda_statewide | ✅ | 4,280,310 | 2026-01-17 19:57 |
| oh_statewide | ✅ | 6,318,338 | 2026-01-17 19:57 |
| nj_statewide | ✅ | 3,475,671 | 2026-01-17 19:57 |
| ny_statewide | ✅ | 3,713,082 | 2026-01-17 19:57 |
| md_statewide | ✅ | 2,264,064 | 2026-01-17 19:57 |
| vt_statewide | ✅ | 44,308 | 2026-01-17 19:57 |
| ar_statewide | ✅ | 2,111,591 | 2026-01-17 19:57 |
| mt_statewide | ✅ | 915,189 | 2026-01-17 19:57 |
| wy_statewide | ✅ | 0 | 2026-01-17 19:57 |
| ut_statewide | ✅ | 280,809 | 2026-01-17 19:57 |
| id_statewide | ✅ | 1,151,432 | 2026-01-17 19:57 |
| nv_statewide | ✅ | 1,394,190 | 2026-01-17 19:57 |
| wi_statewide | ✅ | 3,562,907 | 2026-01-17 19:57 |
| ms_statewide | ✅ | 85 | 2026-01-17 19:57 |
| ms_east_statewide | ✅ | 1,120,249 | 2026-01-17 19:57 |
| ms_west_statewide | ✅ | 874,590 | 2026-01-17 19:57 |
| va_statewide_v2 | ✅ | 4,176,975 | 2026-01-17 19:57 |
| fl_statewide | ✅ | 10,834,415 | 2026-01-17 19:57 |
| nc_statewide | ✅ | 5,913,369 | 2026-01-17 19:57 |
| wa_statewide_v2 | ✅ | 3,322,257 | 2026-01-17 19:57 |
| ma_statewide | ✅ | 2,556,486 | 2026-01-17 19:57 |
| ct_statewide | ✅ | 1,247,506 | 2026-01-17 19:57 |
| wa_statewide | ✅ | 0 | 2026-01-17 19:57 |
| de_statewide | ✅ | 449,787 | 2026-01-17 19:57 |
| hi_statewide | ✅ | 384,262 | 2026-01-17 19:57 |
| nm_statewide | ❌ | Error | 2026-01-17 19:57 |
| nm_statewide_v2 | ✅ | 255,181 | 2026-01-17 19:57 |
| nd_statewide | ✅ | 729,993 | 2026-01-17 19:57 |
| ms_statewide_2024 | ✅ | 85 | 2026-01-17 19:57 |
| vt_statewide_v2 | ✅ | 44,308 | 2026-01-17 19:57 |
| wy_statewide_v2 | ✅ | 0 | 2026-01-17 19:57 |
| in_statewide | ✅ | 0 | 2026-01-17 19:57 |
| ca_zoning_statewide | ✅ | 264,417 | 2026-01-17 19:57 |
| wv_statewide | ✅ | 1,389,855 | 2026-01-17 19:57 |
| va_statewide | ❌ | Error | 2026-01-17 19:57 |
| ne_statewide | ❌ | Error | 2026-01-17 19:57 |
| nj_statewide_v2 | ✅ | 3,475,671 | 2026-01-17 19:57 |
| me_statewide | ✅ | 716,975 | 2026-01-17 19:57 |
| nh_statewide | ✅ | 616,179 | 2026-01-17 19:57 |
| co_statewide | ✅ | 2,532,052 | 2026-01-17 19:57 |
| ia_statewide | ✅ | 2,450,589 | 2026-01-17 19:57 |
| wv_statewide_v2 | ✅ | 1,389,855 | 2026-01-17 19:57 |
| wi_statewide_v2 | ✅ | 3,562,907 | 2026-01-17 19:57 |
| ct_statewide_v2 | ✅ | 1,282,833 | 2026-01-17 19:57 |
| mn_statewide | ✅ | 0 | 2026-01-17 19:57 |
| ri_statewide | ✅ | 0 | 2026-01-17 19:57 |
| enrichment_nwi | ✅ | 0 | 2026-01-17 19:57 |
| enrichment_nhd | ✅ | 0 | 2026-01-17 19:57 |
| enrichment_nlcd | ❌ | Error | 2026-01-17 19:57 |
| enrichment_ssurgo | ❌ | Error | 2026-01-17 19:57 |
| enrichment_blm_sma | ✅ | 0 | 2026-01-17 19:57 |
| enrichment_usfs | ✅ | 0 | 2026-01-17 19:57 |
| enrichment_fema_flood | ❌ | Error | 2026-01-17 19:57 |
| enrichment_epa_brownfields | ❌ | Error | 2026-01-17 19:57 |
| enrichment_tiger_roads | ❌ | Error | 2026-01-17 19:57 |

<!-- AGENT_STATUS_END -->