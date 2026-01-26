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

Last updated by Data Agent: 2026-01-26 18:55:27

| Source | Status | Records | Last Check |
|--------|--------|---------|------------|
| tx_statewide | ✅ | 14,347,648 | 2026-01-26 18:55 |
| tx_statewide_recent | ✅ | 14,347,648 | 2026-01-26 18:55 |
| ny_statewide_v2 | ✅ | 3,713,082 | 2026-01-26 18:55 |
| mt_statewide_v2 | ✅ | 915,580 | 2026-01-26 18:55 |
| mi_oakland | ✅ | 63,584 | 2026-01-26 18:55 |
| mi_wayne | ✅ | 381,119 | 2026-01-26 18:55 |
| mi_kent | ✅ | 231,560 | 2026-01-26 18:55 |
| mi_macomb | ✅ | 332,878 | 2026-01-26 18:55 |
| mi_ottawa | ✅ | 117,687 | 2026-01-26 18:55 |
| mi_marquette | ✅ | 0 | 2026-01-26 18:55 |
| mi_washtenaw | ❌ | Error | 2026-01-26 18:55 |
| il_dupage | ✅ | 337,074 | 2026-01-26 18:55 |
| il_lake | ✅ | 278,809 | 2026-01-26 18:55 |
| il_will | ✅ | 282,265 | 2026-01-26 18:55 |
| mo_st_charles | ✅ | 171,400 | 2026-01-26 18:55 |
| mo_clay | ✅ | 98,112 | 2026-01-26 18:55 |
| mo_kansas_city | ✅ | 203,689 | 2026-01-26 18:55 |
| mo_christian | ✅ | 8,421 | 2026-01-26 18:55 |
| tx_harris | ✅ | 1,538,771 | 2026-01-26 18:55 |
| tx_tarrant | ✅ | 693,363 | 2026-01-26 18:55 |
| tx_bexar | ✅ | 710,772 | 2026-01-26 18:55 |
| tx_travis | ✅ | 373,683 | 2026-01-26 18:55 |
| tx_denton | ✅ | 304,723 | 2026-01-26 18:55 |
| pa_philadelphia | ✅ | 607,491 | 2026-01-26 18:55 |
| pa_allegheny | ✅ | 1,574 | 2026-01-26 18:55 |
| pa_montgomery | ✅ | 25,296 | 2026-01-26 18:55 |
| pa_bucks | ✅ | 237,404 | 2026-01-26 18:55 |
| pa_lancaster | ✅ | 188,463 | 2026-01-26 18:55 |
| pa_berks | ❌ | Error | 2026-01-26 18:55 |
| pa_york | ❌ | Error | 2026-01-26 18:55 |
| pa_lehigh | ❌ | Error | 2026-01-26 18:55 |
| ga_fulton | ❌ | Error | 2026-01-26 18:55 |
| ga_gwinnett | ✅ | 306,162 | 2026-01-26 18:55 |
| ga_cobb | ✅ | 282,345 | 2026-01-26 18:55 |
| ga_dekalb | ✅ | 245,772 | 2026-01-26 18:55 |
| ga_cherokee | ✅ | 0 | 2026-01-26 18:55 |
| ga_glynn | ❌ | Error | 2026-01-26 18:55 |
| ga_chatham | ✅ | 120,988 | 2026-01-26 18:55 |
| ga_liberty | ❌ | Error | 2026-01-26 18:55 |
| tn_statewide | ❌ | Error | 2026-01-26 18:55 |
| tn_shelby | ✅ | 352,614 | 2026-01-26 18:55 |
| tn_davidson | ✅ | 285,521 | 2026-01-26 18:55 |
| tn_knox | ❌ | Error | 2026-01-26 18:55 |
| tn_hamilton | ✅ | 167,714 | 2026-01-26 18:55 |
| tn_rutherford | ❌ | Error | 2026-01-26 18:55 |
| tn_montgomery | ✅ | 25,296 | 2026-01-26 18:55 |
| tn_wilson | ✅ | 0 | 2026-01-26 18:55 |
| ky_jefferson | ✅ | 293,067 | 2026-01-26 18:55 |
| ky_fayette | ✅ | 0 | 2026-01-26 18:55 |
| ky_kenton | ❌ | Error | 2026-01-26 18:55 |
| ky_boone | ❌ | Error | 2026-01-26 18:55 |
| ky_hardin | ✅ | 0 | 2026-01-26 18:55 |
| va_albemarle | ✅ | 49,616 | 2026-01-26 18:55 |
| sc_charleston | ✅ | 196,988 | 2026-01-26 18:55 |
| sc_greenville | ✅ | 241,638 | 2026-01-26 18:55 |
| sc_richland | ❌ | Error | 2026-01-26 18:55 |
| al_jefferson | ❌ | Error | 2026-01-26 18:55 |
| al_mobile | ❌ | Error | 2026-01-26 18:55 |
| al_madison | ✅ | 196,213 | 2026-01-26 18:55 |
| la_orleans | ❌ | Error | 2026-01-26 18:55 |
| la_eastbatonrouge | ❌ | Error | 2026-01-26 18:55 |
| la_jefferson | ❌ | Error | 2026-01-26 18:55 |
| ms_hinds | ✅ | 128,056 | 2026-01-26 18:55 |
| ms_harrison | ✅ | 96,571 | 2026-01-26 18:55 |
| ok_oklahoma | ❌ | Error | 2026-01-26 18:55 |
| ok_tulsa | ✅ | 283,629 | 2026-01-26 18:55 |
| az_maricopa | ✅ | 1,744,991 | 2026-01-26 18:55 |
| az_pima | ✅ | 445,971 | 2026-01-26 18:55 |
| az_pinal | ✅ | 60,160 | 2026-01-26 18:55 |
| nv_clark | ✅ | 943,432 | 2026-01-26 18:55 |
| nv_washoe | ✅ | 192,991 | 2026-01-26 18:55 |
| id_ada_meridian | ✅ | 58,120 | 2026-01-26 18:55 |
| ca_los_angeles | ✅ | 2,430,849 | 2026-01-26 18:55 |
| ca_san_diego | ✅ | 1,089,699 | 2026-01-26 18:55 |
| ca_orange | ✅ | 702,999 | 2026-01-26 18:55 |
| ca_riverside | ❌ | Error | 2026-01-26 18:55 |
| ca_sacramento | ✅ | 506,912 | 2026-01-26 18:55 |
| ca_fresno | ✅ | 302,760 | 2026-01-26 18:55 |
| ks_sedgwick | ❌ | Error | 2026-01-26 18:55 |
| sd_sioux_falls | ✅ | 66,527 | 2026-01-26 18:55 |
| wy_laramie | ✅ | 45,841 | 2026-01-26 18:55 |
| la_orleans_v2 | ❌ | Error | 2026-01-26 18:55 |
| la_jefferson_v2 | ❌ | Error | 2026-01-26 18:55 |
| la_east_baton_rouge | ✅ | 0 | 2026-01-26 18:55 |
| ms_desoto | ✅ | 84,398 | 2026-01-26 18:55 |
| ms_hinds_v2 | ✅ | 128,056 | 2026-01-26 18:55 |
| al_madison_v2 | ✅ | 194,167 | 2026-01-26 18:55 |
| sc_charleston_v2 | ✅ | 196,988 | 2026-01-26 18:55 |
| sc_greenville_v2 | ✅ | 241,638 | 2026-01-26 18:55 |
| or_douglas | ✅ | 70,554 | 2026-01-26 18:55 |
| or_lane | ✅ | 0 | 2026-01-26 18:55 |
| or_deschutes | ❌ | Error | 2026-01-26 18:55 |
| or_benton | ✅ | 4 | 2026-01-26 18:55 |
| or_statewide | ✅ | 0 | 2026-01-26 18:55 |
| pa_statewide | ❌ | Error | 2026-01-26 18:55 |
| pa_pasda_statewide | ❌ | Error | 2026-01-26 18:55 |
| pa_lackawanna | ✅ | 103,149 | 2026-01-26 18:55 |
| pa_lancaster_v2 | ✅ | 188,463 | 2026-01-26 18:55 |
| pa_delaware | ✅ | 208,235 | 2026-01-26 18:55 |
| ak_fairbanks | ✅ | 57,685 | 2026-01-26 18:55 |
| ak_juneau | ✅ | 13,119 | 2026-01-26 18:55 |
| oh_statewide | ✅ | 6,318,338 | 2026-01-26 18:55 |
| oh_franklin | ✅ | 492,206 | 2026-01-26 18:55 |
| oh_montgomery | ✅ | 25,296 | 2026-01-26 18:55 |
| oh_summit | ✅ | 37,992 | 2026-01-26 18:55 |
| il_cook | ❌ | Error | 2026-01-26 18:55 |
| wi_milwaukee | ✅ | 280,679 | 2026-01-26 18:55 |
| wi_waukesha | ✅ | 162,684 | 2026-01-26 18:55 |
| wi_kenosha | ✅ | 68,729 | 2026-01-26 18:55 |
| wi_racine | ✅ | 84,570 | 2026-01-26 18:55 |
| mn_hennepin | ✅ | 0 | 2026-01-26 18:55 |
| mn_ramsey | ❌ | Error | 2026-01-26 18:55 |
| ne_lancaster | ✅ | 121,851 | 2026-01-26 18:55 |
| mi_kent_v2 | ✅ | 231,560 | 2026-01-26 18:55 |
| mi_grand_traverse | ❌ | Error | 2026-01-26 18:55 |
| nj_statewide | ✅ | 3,475,671 | 2026-01-26 18:55 |
| ny_statewide | ✅ | 3,713,082 | 2026-01-26 18:55 |
| ny_centroids | ✅ | 5,499,211 | 2026-01-26 18:55 |
| ny_westchester | ✅ | 257,530 | 2026-01-26 18:55 |
| ny_erie | ✅ | 360,170 | 2026-01-26 18:55 |
| ny_suffolk | ❌ | Error | 2026-01-26 18:55 |
| va_fairfax | ✅ | 382,999 | 2026-01-26 18:55 |
| va_arlington | ❌ | Error | 2026-01-26 18:55 |
| va_loudoun | ❌ | Error | 2026-01-26 18:55 |
| va_prince_william | ❌ | Error | 2026-01-26 18:55 |
| tx_williamson | ✅ | 0 | 2026-01-26 18:55 |
| tx_dallas | ✅ | 496,810 | 2026-01-26 18:55 |
| tx_el_paso | ❌ | Error | 2026-01-26 18:55 |
| fl_miami_dade | ✅ | 558,438 | 2026-01-26 18:55 |
| fl_palm_beach | ❌ | Error | 2026-01-26 18:55 |
| ga_forsyth | ✅ | 0 | 2026-01-26 18:55 |
| nc_mecklenburg | ✅ | 392,269 | 2026-01-26 18:55 |
| nc_durham | ✅ | 132,213 | 2026-01-26 18:55 |
| az_yavapai | ✅ | 187,001 | 2026-01-26 18:55 |
| az_mohave | ✅ | 0 | 2026-01-26 18:55 |
| md_statewide | ❌ | Error | 2026-01-26 18:55 |
| vt_statewide | ✅ | 44,310 | 2026-01-26 18:55 |
| ar_statewide | ✅ | 2,111,591 | 2026-01-26 18:55 |
| tn_nashville | ✅ | 285,521 | 2026-01-26 18:55 |
| me_unorganized | ✅ | 0 | 2026-01-26 18:55 |
| me_bangor | ✅ | 11,244 | 2026-01-26 18:55 |
| mt_statewide | ✅ | 915,580 | 2026-01-26 18:55 |
| wy_statewide | ✅ | 0 | 2026-01-26 18:55 |
| ut_statewide | ✅ | 280,809 | 2026-01-26 18:55 |
| id_statewide | ✅ | 1,151,432 | 2026-01-26 18:55 |
| nv_statewide | ✅ | 1,394,190 | 2026-01-26 18:55 |
| nv_clark_v2 | ✅ | 943,432 | 2026-01-26 18:55 |
| co_boulder | ✅ | 140,151 | 2026-01-26 18:55 |
| co_el_paso | ✅ | 237,530 | 2026-01-26 18:55 |
| co_jefferson | ✅ | 0 | 2026-01-26 18:55 |
| oh_lucas | ❌ | Error | 2026-01-26 18:55 |
| in_allen | ✅ | 0 | 2026-01-26 18:55 |
| wi_statewide | ✅ | 3,562,907 | 2026-01-26 18:55 |
| ms_statewide | ✅ | 85 | 2026-01-26 18:55 |
| ms_east_statewide | ✅ | 1,120,249 | 2026-01-26 18:55 |
| ms_west_statewide | ✅ | 874,590 | 2026-01-26 18:55 |
| va_statewide_v2 | ❌ | Error | 2026-01-26 18:55 |
| fl_statewide | ✅ | 10,834,415 | 2026-01-26 18:55 |
| nc_statewide | ✅ | 5,913,947 | 2026-01-26 18:55 |
| ga_fulton_v2 | ✅ | 370,743 | 2026-01-26 18:55 |
| ga_forsyth_v2 | ✅ | 103,827 | 2026-01-26 18:55 |
| ok_county_v2 | ✅ | 63,584 | 2026-01-26 18:55 |
| wa_statewide_v2 | ✅ | 3,322,257 | 2026-01-26 18:55 |
| wa_king_county | ✅ | 637,767 | 2026-01-26 18:55 |
| mi_wayne_county | ✅ | 785,527 | 2026-01-26 18:55 |
| mi_detroit | ✅ | 381,119 | 2026-01-26 18:55 |
| il_cook_county | ✅ | 0 | 2026-01-26 18:55 |
| ma_statewide | ✅ | 2,556,486 | 2026-01-26 18:55 |
| ct_statewide | ✅ | 1,247,506 | 2026-01-26 18:55 |
| co_arapahoe | ✅ | 231,089 | 2026-01-26 18:55 |
| la_lafayette | ❌ | Error | 2026-01-26 18:55 |
| al_montgomery | ✅ | 105,289 | 2026-01-26 18:55 |
| ok_oklahoma_county | ❌ | Error | 2026-01-26 18:55 |
| wa_statewide | ✅ | 0 | 2026-01-26 18:55 |
| wa_king | ✅ | 637,767 | 2026-01-26 18:55 |
| wa_spokane | ✅ | 213,663 | 2026-01-26 18:55 |
| or_multnomah | ✅ | 0 | 2026-01-26 18:55 |
| or_clackamas | ✅ | 0 | 2026-01-26 18:55 |
| fl_hillsborough | ✅ | 529,628 | 2026-01-26 18:55 |
| fl_orange | ✅ | 494,288 | 2026-01-26 18:55 |
| fl_duval | ✅ | 406,088 | 2026-01-26 18:55 |
| fl_broward | ✅ | 527,722 | 2026-01-26 18:55 |
| fl_pinellas | ✅ | 311,941 | 2026-01-26 18:55 |
| de_statewide | ✅ | 450,043 | 2026-01-26 18:55 |
| de_new_castle | ❌ | Error | 2026-01-26 18:55 |
| de_kent | ❌ | Error | 2026-01-26 18:55 |
| de_sussex | ❌ | Error | 2026-01-26 18:55 |
| hi_statewide | ✅ | 384,262 | 2026-01-26 18:55 |
| hi_honolulu | ✅ | 171,905 | 2026-01-26 18:55 |
| hi_maui | ✅ | 51,765 | 2026-01-26 18:55 |
| hi_hawaii | ✅ | 0 | 2026-01-26 18:55 |
| nm_statewide | ❌ | Error | 2026-01-26 18:55 |
| nm_statewide_v2 | ✅ | 255,181 | 2026-01-26 18:55 |
| nm_dona_ana | ✅ | 95,209 | 2026-01-26 18:55 |
| az_coconino | ❌ | Error | 2026-01-26 18:55 |
| sd_minnehaha | ✅ | 0 | 2026-01-26 18:55 |
| nd_statewide | ✅ | 740,872 | 2026-01-26 18:55 |
| nd_cass | ✅ | 75,035 | 2026-01-26 18:55 |
| ri_cranston | ❌ | Error | 2026-01-26 18:55 |
| ri_east_providence | ✅ | 15,658 | 2026-01-26 18:55 |
| ri_providence | ❌ | Error | 2026-01-26 18:55 |
| ri_south_kingstown | ✅ | 8,191 | 2026-01-26 18:55 |
| ga_fulton_v3 | ❌ | Error | 2026-01-26 18:55 |
| ga_dekalb_v2 | ❌ | Error | 2026-01-26 18:55 |
| ga_cherokee_v2 | ✅ | 0 | 2026-01-26 18:55 |
| ga_glynn_v2 | ❌ | Error | 2026-01-26 18:55 |
| fl_miami_dade_v2 | ✅ | 0 | 2026-01-26 18:55 |
| fl_broward_v2 | ❌ | Error | 2026-01-26 18:55 |
| fl_palm_beach_v2 | ❌ | Error | 2026-01-26 18:55 |
| fl_orange_v2 | ❌ | Error | 2026-01-26 18:55 |
| fl_hillsborough_v2 | ✅ | 0 | 2026-01-26 18:55 |
| fl_duval_v2 | ❌ | Error | 2026-01-26 18:55 |
| fl_pinellas_v2 | ❌ | Error | 2026-01-26 18:55 |
| co_denver_v2 | ✅ | 0 | 2026-01-26 18:55 |
| co_boulder_v2 | ✅ | 0 | 2026-01-26 18:55 |
| co_adams_v3 | ✅ | 0 | 2026-01-26 18:55 |
| co_arapahoe_v3 | ✅ | 0 | 2026-01-26 18:55 |
| co_douglas_v2 | ✅ | 0 | 2026-01-26 18:55 |
| co_el_paso_v3 | ✅ | 0 | 2026-01-26 18:55 |
| co_jefferson_v2 | ✅ | 0 | 2026-01-26 18:55 |
| co_larimer_v2 | ✅ | 0 | 2026-01-26 18:55 |
| ms_statewide_2024 | ✅ | 85 | 2026-01-26 18:55 |
| ms_harrison_v2 | ✅ | 96,571 | 2026-01-26 18:55 |
| ok_oklahoma_v2 | ❌ | Error | 2026-01-26 18:55 |
| ok_tulsa_v2 | ❌ | Error | 2026-01-26 18:55 |
| ok_cleveland | ✅ | 0 | 2026-01-26 18:55 |
| sd_sioux_falls_v2 | ✅ | 66,527 | 2026-01-26 18:55 |
| ak_matsu | ❌ | Error | 2026-01-26 18:55 |
| ak_kenai | ❌ | Error | 2026-01-26 18:55 |
| ak_north_slope | ✅ | 7,056 | 2026-01-26 18:55 |
| ak_sitka | ✅ | 3,679 | 2026-01-26 18:55 |
| ak_denali | ✅ | 3,127 | 2026-01-26 18:55 |
| vt_statewide_v2 | ✅ | 44,310 | 2026-01-26 18:55 |
| wy_statewide_v2 | ✅ | 0 | 2026-01-26 18:55 |
| wy_laramie_v2 | ✅ | 45,840 | 2026-01-26 18:55 |
| wy_lincoln | ✅ | 0 | 2026-01-26 18:55 |
| ia_linn | ✅ | 0 | 2026-01-26 18:55 |
| ks_shawnee | ❌ | Error | 2026-01-26 18:55 |
| nc_wake | ✅ | 432,904 | 2026-01-26 18:55 |
| nc_guilford | ✅ | 221,914 | 2026-01-26 18:55 |
| nc_forsyth | ✅ | 112 | 2026-01-26 18:55 |
| nc_cumberland | ✅ | 140,409 | 2026-01-26 18:55 |
| in_statewide | ✅ | 3,677,250 | 2026-01-26 18:55 |
| in_marion | ❌ | Error | 2026-01-26 18:55 |
| in_hamilton | ✅ | 0 | 2026-01-26 18:55 |
| mn_dakota | ❌ | Error | 2026-01-26 18:55 |
| mn_anoka | ✅ | 139,980 | 2026-01-26 18:55 |
| co_larimer | ✅ | 180,998 | 2026-01-26 18:55 |
| co_denver | ✅ | 0 | 2026-01-26 18:55 |
| co_adams | ✅ | 0 | 2026-01-26 18:55 |
| co_douglas | ✅ | 157,760 | 2026-01-26 18:55 |
| az_apache | ✅ | 58,031 | 2026-01-26 18:55 |
| az_navajo | ✅ | 86,289 | 2026-01-26 18:55 |
| ca_alameda | ❌ | Error | 2026-01-26 18:55 |
| ca_sonoma | ✅ | 70,065 | 2026-01-26 18:55 |
| ca_zoning_statewide | ✅ | 264,417 | 2026-01-26 18:55 |
| wv_statewide | ✅ | 1,389,855 | 2026-01-26 18:55 |
| va_statewide | ❌ | Error | 2026-01-26 18:55 |
| va_virginia_beach | ✅ | 135,406 | 2026-01-26 18:55 |
| va_henrico | ✅ | 115,374 | 2026-01-26 18:55 |
| va_loudoun_v2 | ✅ | 132,104 | 2026-01-26 18:55 |
| va_prince_william_v2 | ✅ | 156,326 | 2026-01-26 18:55 |
| ne_sarpy | ✅ | 76,853 | 2026-01-26 18:55 |
| ne_statewide | ✅ | 1,152,845 | 2026-01-26 18:55 |
| mo_jackson | ❌ | Error | 2026-01-26 18:55 |
| mo_st_charles_v2 | ✅ | 171,400 | 2026-01-26 18:55 |
| mo_greene | ✅ | 0 | 2026-01-26 18:55 |
| ks_douglas | ✅ | 0 | 2026-01-26 18:55 |
| ks_wyandotte | ✅ | 0 | 2026-01-26 18:55 |
| nj_statewide_v2 | ✅ | 3,475,671 | 2026-01-26 18:55 |
| nj_bergen | ✅ | 300,083 | 2026-01-26 18:55 |
| nj_passaic | ✅ | 132,592 | 2026-01-26 18:55 |
| me_statewide | ✅ | 716,975 | 2026-01-26 18:55 |
| nh_statewide | ✅ | 616,179 | 2026-01-26 18:55 |
| tx_williamson_v2 | ✅ | 286,816 | 2026-01-26 18:55 |
| sc_horry | ✅ | 297,807 | 2026-01-26 18:55 |
| sc_spartanburg | ✅ | 0 | 2026-01-26 18:55 |
| ga_richmond | ✅ | 0 | 2026-01-26 18:55 |
| ga_gwinnett_v2 | ✅ | 306,162 | 2026-01-26 18:55 |
| co_statewide | ✅ | 2,532,052 | 2026-01-26 18:55 |
| co_el_paso_v2 | ✅ | 238,042 | 2026-01-26 18:55 |
| co_arapahoe_v2 | ✅ | 231,089 | 2026-01-26 18:55 |
| co_adams_v2 | ✅ | 187,419 | 2026-01-26 18:55 |
| ia_statewide | ✅ | 2,450,589 | 2026-01-26 18:55 |
| ia_polk | ✅ | 318,353 | 2026-01-26 18:55 |
| ia_johnson | ✅ | 74,384 | 2026-01-26 18:55 |
| oh_cuyahoga | ✅ | 484,435 | 2026-01-26 18:55 |
| oh_hamilton | ✅ | 420,228 | 2026-01-26 18:55 |
| oh_summit_v2 | ✅ | 260,948 | 2026-01-26 18:55 |
| ca_los_angeles_v2 | ✅ | 2,430,849 | 2026-01-26 18:55 |
| ca_orange_v2 | ❌ | Error | 2026-01-26 18:55 |
| ca_san_francisco | ✅ | 226,786 | 2026-01-26 18:55 |
| ca_sacramento_v2 | ✅ | 598,211 | 2026-01-26 18:55 |
| il_cook_v2 | ✅ | 1,419,180 | 2026-01-26 18:55 |
| il_dupage_v2 | ✅ | 337,074 | 2026-01-26 18:55 |
| mi_oakland_v2 | ✅ | 490,495 | 2026-01-26 18:55 |
| mi_macomb_v2 | ✅ | 3 | 2026-01-26 18:55 |
| la_st_tammany | ❌ | Error | 2026-01-26 18:55 |
| or_washington | ✅ | 0 | 2026-01-26 18:55 |
| or_marion | ✅ | 0 | 2026-01-26 18:55 |
| sd_sioux_falls_v3 | ✅ | 66,527 | 2026-01-26 18:55 |
| sd_pennington | ✅ | 0 | 2026-01-26 18:55 |
| sd_codington | ✅ | 18,463 | 2026-01-26 18:55 |
| sd_beadle | ✅ | 16,878 | 2026-01-26 18:55 |
| sd_roberts | ✅ | 14,551 | 2026-01-26 18:55 |
| sd_edmunds | ✅ | 9,589 | 2026-01-26 18:55 |
| sd_hand | ✅ | 9,553 | 2026-01-26 18:55 |
| sd_kingsbury | ✅ | 9,078 | 2026-01-26 18:55 |
| sd_grant | ✅ | 8,903 | 2026-01-26 18:55 |
| sd_hamlin | ✅ | 8,106 | 2026-01-26 18:55 |
| sd_clark | ✅ | 7,615 | 2026-01-26 18:55 |
| sd_deuel | ✅ | 6,977 | 2026-01-26 18:55 |
| sd_moody | ✅ | 6,319 | 2026-01-26 18:55 |
| sd_miner | ✅ | 5,305 | 2026-01-26 18:55 |
| ak_skagway | ✅ | 1,775 | 2026-01-26 18:55 |
| ak_fnsb_direct | ✅ | 63,584 | 2026-01-26 18:55 |
| ak_dnr_disposals | ✅ | 33,757 | 2026-01-26 18:55 |
| ak_blm_native | ✅ | 13,487 | 2026-01-26 18:55 |
| ak_blm_ancsa | ✅ | 305,325 | 2026-01-26 18:55 |
| ak_blm_state | ✅ | 230,178 | 2026-01-26 18:55 |
| ak_blm_private | ✅ | 37,591 | 2026-01-26 18:55 |
| ne_hall | ✅ | 28,877 | 2026-01-26 18:55 |
| wy_campbell | ✅ | 26,540 | 2026-01-26 18:55 |
| wy_teton | ✅ | 16,461 | 2026-01-26 18:55 |
| wy_park | ❌ | Error | 2026-01-26 18:55 |
| wy_sheridan | ✅ | 18,970 | 2026-01-26 18:55 |
| wy_fremont | ✅ | 28,718 | 2026-01-26 18:55 |
| ok_creek | ✅ | 46,138 | 2026-01-26 18:55 |
| ok_osage | ✅ | 42,042 | 2026-01-26 18:55 |
| ok_rogers | ✅ | 51,777 | 2026-01-26 18:55 |
| ok_wagoner | ✅ | 52,839 | 2026-01-26 18:55 |
| ok_norman | ✅ | 46,015 | 2026-01-26 18:55 |
| ok_edmond | ✅ | 42,693 | 2026-01-26 18:55 |
| ok_broken_arrow | ✅ | 73,339 | 2026-01-26 18:55 |
| nh_manchester | ✅ | 33,973 | 2026-01-26 18:55 |
| nh_nashua | ✅ | 20,682 | 2026-01-26 18:55 |
| nh_keene | ✅ | 11,378 | 2026-01-26 18:55 |
| me_mcht_combined | ✅ | 721,871 | 2026-01-26 18:55 |
| me_portland | ❌ | Error | 2026-01-26 18:55 |
| me_lewiston | ✅ | 12,342 | 2026-01-26 18:55 |
| wv_statewide_v2 | ✅ | 1,389,855 | 2026-01-26 18:55 |
| wv_kanawha | ✅ | 117,780 | 2026-01-26 18:55 |
| id_whitestar | ✅ | 1,142,341 | 2026-01-26 18:55 |
| id_canyon | ✅ | 109,197 | 2026-01-26 18:55 |
| mt_yellowstone | ✅ | 83,387 | 2026-01-26 18:55 |
| mt_gallatin | ✅ | 71,653 | 2026-01-26 18:55 |
| mt_flathead | ✅ | 108,833 | 2026-01-26 18:55 |
| hi_hawaii_county | ✅ | 135,471 | 2026-01-26 18:55 |
| hi_kauai | ✅ | 25,121 | 2026-01-26 18:55 |
| ia_scott | ✅ | 75,511 | 2026-01-26 18:55 |
| ia_story | ✅ | 42,203 | 2026-01-26 18:55 |
| nm_bernalillo | ✅ | 256,974 | 2026-01-26 18:55 |
| nm_santa_fe | ✅ | 90,211 | 2026-01-26 18:55 |
| nm_sandoval | ✅ | 599 | 2026-01-26 18:55 |
| nm_valencia | ✅ | 197,821 | 2026-01-26 18:55 |
| al_baldwin | ✅ | 0 | 2026-01-26 18:55 |
| ms_rankin | ✅ | 83,393 | 2026-01-26 18:55 |
| ms_madison | ✅ | 60,658 | 2026-01-26 18:55 |
| la_jefferson_v3 | ❌ | Error | 2026-01-26 18:55 |
| la_ebr | ✅ | 204,855 | 2026-01-26 18:55 |
| la_calcasieu | ✅ | 0 | 2026-01-26 18:55 |
| wi_statewide_v2 | ✅ | 3,562,907 | 2026-01-26 18:55 |
| wi_milwaukee_v2 | ✅ | 280,679 | 2026-01-26 18:55 |
| wi_dane | ✅ | 340,671 | 2026-01-26 18:55 |
| wi_waukesha_v2 | ✅ | 162,684 | 2026-01-26 18:55 |
| wi_brown | ✅ | 105,682 | 2026-01-26 18:55 |
| wi_racine_v2 | ✅ | 84,570 | 2026-01-26 18:55 |
| tn_williamson | ❌ | Error | 2026-01-26 18:55 |
| mo_stl_city | ✅ | 134,932 | 2026-01-26 18:55 |
| mo_stl_county | ✅ | 73,646 | 2026-01-26 18:55 |
| ky_fayette_v2 | ✅ | 114,196 | 2026-01-26 18:55 |
| ky_warren | ✅ | 0 | 2026-01-26 18:55 |
| ky_boone_v2 | ✅ | 54,873 | 2026-01-26 18:55 |
| ky_campbell | ✅ | 37,868 | 2026-01-26 18:55 |
| pa_chester | ✅ | 193,922 | 2026-01-26 18:55 |
| ct_statewide_v2 | ✅ | 1,282,833 | 2026-01-26 18:55 |
| ct_bridgeport | ✅ | 35,992 | 2026-01-26 18:55 |
| ct_hartford | ❌ | Error | 2026-01-26 18:55 |
| ut_salt_lake | ✅ | 395,674 | 2026-01-26 18:55 |
| ut_utah | ✅ | 280,809 | 2026-01-26 18:55 |
| ut_davis | ✅ | 127,186 | 2026-01-26 18:55 |
| ut_weber | ✅ | 114,167 | 2026-01-26 18:55 |
| ut_washington | ✅ | 128,170 | 2026-01-26 18:55 |
| ut_cache | ✅ | 59,422 | 2026-01-26 18:55 |
| az_pinal_v2 | ✅ | 280,172 | 2026-01-26 18:55 |
| az_yuma | ✅ | 96,848 | 2026-01-26 18:55 |
| or_multnomah_v2 | ✅ | 283,878 | 2026-01-26 18:55 |
| or_lane_v2 | ✅ | 158,979 | 2026-01-26 18:55 |
| or_marion_v2 | ✅ | 115,494 | 2026-01-26 18:55 |
| nc_buncombe | ✅ | 134,351 | 2026-01-26 18:55 |
| nc_new_hanover | ✅ | 103,110 | 2026-01-26 18:55 |
| nc_pitt | ✅ | 80,727 | 2026-01-26 18:55 |
| ga_muscogee | ❌ | Error | 2026-01-26 18:55 |
| oh_stark | ✅ | 201,907 | 2026-01-26 18:55 |
| ny_nassau | ✅ | 420,594 | 2026-01-26 18:55 |
| ny_monroe | ✅ | 267,717 | 2026-01-26 18:55 |
| ga_bibb | ❌ | Error | 2026-01-26 18:55 |
| ga_henry | ✅ | 0 | 2026-01-26 18:55 |
| ga_houston | ❌ | Error | 2026-01-26 18:55 |
| ga_hall | ✅ | 0 | 2026-01-26 18:55 |
| ga_douglas | ✅ | 0 | 2026-01-26 18:55 |
| ga_paulding | ✅ | 0 | 2026-01-26 18:55 |
| ga_bartow | ✅ | 0 | 2026-01-26 18:55 |
| ky_daviess | ✅ | 0 | 2026-01-26 18:55 |
| ky_madison | ✅ | 0 | 2026-01-26 18:55 |
| ky_christian | ✅ | 0 | 2026-01-26 18:55 |
| ky_pike | ✅ | 0 | 2026-01-26 18:55 |
| ky_pulaski | ✅ | 0 | 2026-01-26 18:55 |
| mo_montgomery | ✅ | 25,296 | 2026-01-26 18:55 |
| mo_st_louis_city | ❌ | Error | 2026-01-26 18:55 |
| mo_st_louis_county | ✅ | 0 | 2026-01-26 18:55 |
| mo_boone | ✅ | 0 | 2026-01-26 18:55 |
| mo_jefferson | ✅ | 0 | 2026-01-26 18:55 |
| ks_johnson | ✅ | 0 | 2026-01-26 18:55 |
| il_kane | ❌ | Error | 2026-01-26 18:55 |
| il_mchenry | ❌ | Error | 2026-01-26 18:55 |
| il_winnebago | ❌ | Error | 2026-01-26 18:55 |
| il_peoria | ❌ | Error | 2026-01-26 18:55 |
| il_champaign | ✅ | 0 | 2026-01-26 18:55 |
| il_sangamon | ❌ | Error | 2026-01-26 18:55 |
| mi_genesee | ✅ | 0 | 2026-01-26 18:55 |
| mi_ingham | ❌ | Error | 2026-01-26 18:55 |
| mi_kalamazoo | ✅ | 0 | 2026-01-26 18:55 |
| mi_saginaw | ❌ | Error | 2026-01-26 18:55 |
| mi_muskegon | ✅ | 0 | 2026-01-26 18:55 |
| mn_statewide | ✅ | 0 | 2026-01-26 18:55 |
| la_caddo | ❌ | Error | 2026-01-26 18:55 |
| la_ouachita | ✅ | 0 | 2026-01-26 18:55 |
| ok_canadian | ✅ | 0 | 2026-01-26 18:55 |
| ok_comanche | ✅ | 0 | 2026-01-26 18:55 |
| sc_dorchester | ❌ | Error | 2026-01-26 18:55 |
| sc_lexington | ❌ | Error | 2026-01-26 18:55 |
| sc_york | ❌ | Error | 2026-01-26 18:55 |
| ri_statewide | ✅ | 0 | 2026-01-26 18:55 |
| sd_lincoln | ✅ | 0 | 2026-01-26 18:55 |
| al_shelby | ✅ | 0 | 2026-01-26 18:55 |
| al_tuscaloosa | ✅ | 0 | 2026-01-26 18:55 |
| ak_anchorage | ❌ | Error | 2026-01-26 18:55 |
| az_cochise | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_nwi | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_nhd | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_nlcd | ❌ | Error | 2026-01-26 18:55 |
| enrichment_ssurgo | ❌ | Error | 2026-01-26 18:55 |
| enrichment_blm_sma | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_usfs | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_fema_flood | ❌ | Error | 2026-01-26 18:55 |
| enrichment_epa_brownfields | ❌ | Error | 2026-01-26 18:55 |
| enrichment_tiger_roads | ❌ | Error | 2026-01-26 18:55 |
| enrichment_hifld_hospitals | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_hifld_fire_stations | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_hifld_ems_stations | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_hifld_police | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_hifld_public_schools | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_hifld_private_schools | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_hifld_colleges | ✅ | 0 | 2026-01-26 18:55 |
| enrichment_overture_pois | ❌ | Error | 2026-01-26 18:55 |

<!-- AGENT_STATUS_END -->