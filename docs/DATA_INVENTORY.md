# HITD Maps Data Inventory

**Last Updated:** 2026-01-24

This document provides a complete inventory of all data currently available in HITD Maps.

## Summary

| Metric | Value |
|--------|-------|
| Total PMTiles Files | 197 |
| Parcel Coverage | 60.8% |
| Complete States | 31 |
| Partial States | 19 |
| Missing States | 1 (Rhode Island) |
| R2 Storage Used | ~414 GB |

## Parcel Data by State

### Complete Coverage (31 states + DC)

States with statewide parcel data:

| State | Code | Files | Statewide File | Est. Records |
|-------|------|-------|----------------|--------------|
| Alaska | AK | 2 | parcels_ak_statewide | 410K |
| Arkansas | AR | 2 | parcels_ar_statewide | 2.1M |
| Colorado | CO | 3 | parcels_co_statewide | 2.5M |
| Connecticut | CT | 2 | parcels_ct_statewide | 1.2M |
| Delaware | DE | 2 | parcels_de_statewide | 350K |
| Florida | FL | 2 | parcels_fl_statewide | 10.8M |
| Hawaii | HI | 4 | parcels_hi_statewide | 400K |
| Idaho | ID | 3 | parcels_id_statewide | 381K |
| Indiana | IN | 2 | parcels_in_statewide | 3.2M |
| Iowa | IA | 2 | parcels_ia_statewide | 1.5M |
| Maine | ME | 3 | parcels_me_statewide | 700K |
| Maryland | MD | 1 | parcels_md_statewide | 2.4M |
| Massachusetts | MA | 2 | parcels_ma_statewide | 2.1M |
| Montana | MT | 1 | parcels_mt_statewide | 607K |
| Nevada | NV | 2 | parcels_nv_statewide | 1.4M |
| New Hampshire | NH | 2 | parcels_nh_statewide | 500K |
| New Jersey | NJ | 3 | parcels_nj_statewide_v2 | 2.8M |
| New Mexico | NM | 2 | parcels_nm_statewide_v2 | 1.1M |
| New York | NY | 3 | parcels_ny_statewide_v2 | 9M |
| North Carolina | NC | 12 | parcels_nc_statewide | 4.5M |
| North Dakota | ND | 3 | parcels_nd_statewide | 745K |
| Ohio | OH | 6 | parcels_oh_statewide | 6.3M |
| Pennsylvania | PA | 6 | parcels_pa_statewide | 5.6M |
| Tennessee | TN | 8 | parcels_tn_statewide | 3M |
| Texas | TX | 11 | parcels_tx_statewide_recent | 28M |
| Utah | UT | 2 | parcels_ut_statewide | 1.1M |
| Vermont | VT | 1 | parcels_vt_statewide | 344K |
| Virginia | VA | 6 | parcels_va_statewide_v2 | 4.1M |
| Washington | WA | 5 | parcels_wa_statewide | 3.2M |
| West Virginia | WV | 2 | parcels_wv_statewide | 1M |
| Wisconsin | WI | 7 | parcels_wi_statewide | 3.5M |

### Partial Coverage (19 states)

States with county-level data only:

| State | Code | Files | Coverage % | Major Areas Covered |
|-------|------|-------|------------|---------------------|
| Arizona | AZ | 5 | 26% | Maricopa (Phoenix), Pima (Tucson), Pinal, Yavapai |
| California | CA | 9 | 13% | SF, LA, Sacramento, Orange, Fresno, Sonoma |
| Michigan | MI | 8 | 8% | Wayne (Detroit), Oakland, Kent (GR), Macomb |
| South Dakota | SD | 5 | 7% | Pennington (Rapid City), Beadle, Codington |
| Louisiana | LA | 5 | 6% | Orleans (NO), Jefferson, E Baton Rouge, Lafayette |
| South Carolina | SC | 3 | 6% | Charleston, Greenville, Spartanburg |
| Illinois | IL | 7 | 5% | Cook (Chicago), DuPage, Lake, Will |
| Missouri | MO | 7 | 5% | Kansas City, St. Charles, Christian, Clay, Jackson |
| Oregon | OR | 2 | 5% | Multnomah (Portland), Lane (Eugene) |
| Alabama | AL | 4 | 4% | Mobile, Montgomery, Madison |
| Minnesota | MN | 5 | 4% | Hennepin, Ramsey, Dakota, Anoka |
| Wyoming | WY | 2 | 4% | Campbell |
| Georgia | GA | 7 | 3% | Gwinnett, Cobb, DeKalb, Chatham, Richmond |
| Kentucky | KY | 4 | 2% | Jefferson (Louisville), Boone, Kenton |
| Mississippi | MS | 3 | 2% | Hinds (Jackson), DeSoto |
| Oklahoma | OK | 2 | 2% | Cleveland, Comanche |
| Kansas | KS | 3 | 1% | Sedgwick, Douglas |
| District of Columbia | DC | 1 | 100% | Full coverage |
| Nebraska | NE | 1 | ~5% | Partial |

### No Coverage (1 state)

| State | Code | Status | Known Source |
|-------|------|--------|--------------|
| Rhode Island | RI | **MISSING** | rigis.org (needs discovery) |

## All Parcel Files

Complete list of 197 parcel files:

```
parcels_ak, parcels_ak_statewide
parcels_al, parcels_al_madison_v2, parcels_al_mobile, parcels_al_montgomery
parcels_ar_statewide, parcels_ar_washington
parcels_az, parcels_az_maricopa, parcels_az_pima, parcels_az_pinal, parcels_az_yavapai
parcels_ca, parcels_ca_fresno, parcels_ca_los_angeles_v2, parcels_ca_orange, parcels_ca_orange_v2, parcels_ca_sacramento, parcels_ca_sacramento_v2, parcels_ca_san_francisco, parcels_ca_sonoma
parcels_co, parcels_co_el_paso_v2, parcels_co_statewide
parcels_ct, parcels_ct_statewide
parcels_dc
parcels_de, parcels_de_statewide
parcels_fl_orange, parcels_fl_statewide
parcels_ga, parcels_ga_chatham, parcels_ga_cobb, parcels_ga_dekalb, parcels_ga_gwinnett, parcels_ga_gwinnett_v2, parcels_ga_richmond
parcels_hi, parcels_hi_honolulu, parcels_hi_maui, parcels_hi_statewide
parcels_ia, parcels_ia_statewide
parcels_id, parcels_id_ada_meridian, parcels_id_statewide
parcels_il, parcels_il_cook, parcels_il_cook_county, parcels_il_dupage, parcels_il_dupage_v2, parcels_il_lake, parcels_il_will
parcels_in_marion, parcels_in_statewide
parcels_ks, parcels_ks_douglas, parcels_ks_sedgwick
parcels_ky, parcels_ky_boone, parcels_ky_jefferson, parcels_ky_kenton
parcels_la, parcels_la_east_baton_rouge, parcels_la_jefferson_v2, parcels_la_lafayette, parcels_la_orleans_v2
parcels_ma, parcels_ma_statewide
parcels_md_statewide
parcels_me_bangor, parcels_me_portland, parcels_me_statewide
parcels_mi, parcels_mi_kent, parcels_mi_kent_v2, parcels_mi_macomb, parcels_mi_oakland, parcels_mi_oakland_v2, parcels_mi_ottawa, parcels_mi_wayne
parcels_mn, parcels_mn_anoka, parcels_mn_dakota, parcels_mn_hennepin, parcels_mn_ramsey
parcels_mo, parcels_mo_christian, parcels_mo_clay, parcels_mo_jackson, parcels_mo_kansas_city, parcels_mo_st_charles, parcels_mo_st_charles_v2
parcels_ms, parcels_ms_desoto, parcels_ms_hinds
parcels_mt_statewide
parcels_nc_durham, parcels_nc_durham_wgs84, parcels_nc_forsyth, parcels_nc_forsyth_wgs84, parcels_nc_guilford, parcels_nc_guilford_wgs84, parcels_nc_mecklenburg, parcels_nc_mecklenburg_wgs84, parcels_nc_statewide, parcels_nc_statewide_wgs84, parcels_nc_wake, parcels_nc_wake_wgs84
parcels_nd, parcels_nd_cass, parcels_nd_statewide
parcels_ne
parcels_nh, parcels_nh_statewide
parcels_nj_bergen, parcels_nj_passaic, parcels_nj_statewide_v2
parcels_nm, parcels_nm_statewide_v2
parcels_nv, parcels_nv_statewide
parcels_ny_centroids, parcels_ny_statewide, parcels_ny_statewide_v2
parcels_oh_cuyahoga, parcels_oh_franklin, parcels_oh_hamilton, parcels_oh_montgomery, parcels_oh_statewide, parcels_oh_summit_v2
parcels_ok_cleveland, parcels_ok_comanche
parcels_or_lane, parcels_or_multnomah_v2
parcels_pa_allegheny, parcels_pa_delaware, parcels_pa_lackawanna, parcels_pa_lancaster_v2, parcels_pa_pasda_statewide, parcels_pa_statewide
parcels_sc_charleston, parcels_sc_greenville, parcels_sc_spartanburg
parcels_sd_beadle, parcels_sd_beadle_wgs84, parcels_sd_codington, parcels_sd_codington_wgs84, parcels_sd_pennington
parcels_tn, parcels_tn_davidson, parcels_tn_hamilton, parcels_tn_montgomery, parcels_tn_nashville, parcels_tn_shelby, parcels_tn_statewide, parcels_tn_williamson
parcels_tx, parcels_tx_bexar, parcels_tx_dallas, parcels_tx_denton, parcels_tx_harris, parcels_tx_harris_new, parcels_tx_statewide, parcels_tx_statewide_recent, parcels_tx_tarrant, parcels_tx_travis, parcels_tx_williamson_v2
parcels_ut, parcels_ut_statewide
parcels_va, parcels_va_counties, parcels_va_loudoun_v2, parcels_va_prince_william_v2, parcels_va_statewide, parcels_va_statewide_v2
parcels_vt_statewide
parcels_wa_king, parcels_wa_king_wgs84, parcels_wa_spokane, parcels_wa_spokane_wgs84, parcels_wa_statewide
parcels_wi, parcels_wi_kenosha, parcels_wi_milwaukee, parcels_wi_milwaukee_v2, parcels_wi_racine, parcels_wi_statewide, parcels_wi_waukesha
parcels_wv, parcels_wv_statewide
parcels_wy, parcels_wy_campbell
parcels_montgomery, parcels_counties
```

## Enrichment Data

| Layer | Status | Source | Description |
|-------|--------|--------|-------------|
| PAD-US | Have | USGS GAP | Protected areas, public lands, parks |
| NWI Wetlands | Have | USFWS | National Wetlands Inventory |
| NHD Hydrography | Have | USGS | Rivers, streams, lakes |
| HIFLD Facilities | Have | DHS/CISA | Fire stations, police, hospitals, schools |
| FEMA Flood Zones | Partial | FEMA | Flood hazard areas |
| NLCD Land Cover | Have | USGS | Land use classification |
| SSURGO Soils | Partial | USDA NRCS | Soil survey data |

## Basemap Data

| Layer | Status | Size | Source |
|-------|--------|------|--------|
| Protomaps Planet | Have | 109 GB | Protomaps (OSM-based) |
| Terrain | Have | 1.2 GB | AWS Terrain Tiles |
| Fonts | Have | 33 MB | Glyphs for labels |

## POI Data

| Layer | Status | Source |
|-------|--------|--------|
| OSM Addresses | Have | OpenStreetMap via Geofabrik |
| Overture Places | Have | Overture Maps Foundation |

## R2 Storage Breakdown

| Category | Files | Size | % of Total |
|----------|-------|------|------------|
| Parcels | 365 | 159 GB | 38.5% |
| Basemap | 1 | 109 GB | 26.4% |
| GeoJSON (backup) | 162 | 81 GB | 19.6% |
| PMTiles | 162 | 58 GB | 14.0% |
| POIs | 1 | 3.5 GB | 0.9% |
| Enrichment | 63 | 1.3 GB | 0.3% |
| Terrain | 1 | 1.2 GB | 0.3% |
| Fonts | 256 | 33 MB | 0.0% |
| **Total** | **1,022** | **~414 GB** | **100%** |

## Related Documentation

- [DATA_GAPS.md](DATA_GAPS.md) - What's missing and how to get it
- [DATA_SOURCES.md](../data-pipeline/data/data_sources_registry.json) - All known data sources
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Developer onboarding

## Automated Reports

Run these commands to get current status:

```bash
# Generate coverage report
python3 data-pipeline/scripts/generate_coverage_report.py

# Check for data updates (passive)
python3 data-pipeline/scripts/check_data_freshness.py

# View coverage status
cat data-pipeline/data/coverage_status.json | jq '.summary'
```
