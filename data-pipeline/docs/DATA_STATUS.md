# HITD Maps - Complete Data Status

**Last Updated**: 2026-01-15
**Total R2 Storage**: 517 GB
**Public URL**: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev

---

## Quick Summary

| Metric | Value |
|--------|-------|
| Total States with Parcel Data | **50/50** (100%) |
| States with Statewide Coverage | **31** |
| States with County-Only Coverage | **19** |
| Total Parcel Files | 401 |
| Total Parcel Data Size | 127 GB |
| Total R2 Storage | 517 GB |

---

## R2 Storage Breakdown

| Category | Size | Files | Description |
|----------|------|-------|-------------|
| parcels | 127 GB | 401 | Property boundaries (all 50 states) |
| basemap | 109 GB | 1 | Protomaps self-hosted basemap |
| geojson | 81 GB | 162 | Source GeoJSON backup |
| source-backup | 67 GB | 945 | Original source files |
| pmtiles | 58 GB | 162 | Converted vector tiles |
| roads | 18 GB | 1 | Overture Roads (nationwide) |
| addresses | 7 GB | 1 | Overture Addresses |
| pois | 4 GB | 1 | Points of Interest |
| water | 3 GB | 4 | NHD Water Features |
| enrichment | 3 GB | 108 | Property enrichment data |
| wetlands | 2 GB | 4 | NWI Wetlands |
| terrain | 1 GB | 1 | Terrain tiles |
| trails | 1 GB | 17 | USFS Trails & Roads |
| public-lands | 0.6 GB | 7 | PAD-US, BLM lands |
| wildlife | 0.6 GB | 24 | GMU, WMA, FWS Wildlife |
| fire | 0.1 GB | 2 | Fire perimeters |

---

## Parcel Data Coverage by State

### Complete Statewide Coverage (31 States)

These states have full statewide parcel data:

| State | Files | Size | Source | Status |
|-------|-------|------|--------|--------|
| AR | 1 | 19 KB | Arkansas GIS | Statewide |
| CA | 13 | 12.6 GB | CA State, Counties | Statewide + Counties |
| CO | 5 | 2.2 GB | CO State GIS | Statewide + Counties |
| CT | 2 | 1.1 GB | CT GIS | Statewide |
| DE | 2 | 183 MB | DE State | Statewide |
| FL | 1 | 18 KB | FL DEP | Statewide (metadata only) |
| HI | 4 | 640 MB | HI State | Statewide + Counties |
| IA | 3 | 3.1 GB | IA DNR | Statewide |
| ID | 3 | 370 MB | ID State | Statewide |
| IN | 2 | 8 MB | IN State | Statewide |
| MA | 2 | 1.9 GB | MassGIS | Statewide |
| MD | 1 | 2.2 GB | MD iMap | Statewide |
| ME | 3 | 760 MB | ME GeoLibrary | Statewide |
| MT | 2 | 2.4 GB | MT MSDI | Statewide |
| NC | 6 | 750 MB | NC OneMap | Statewide + Counties |
| ND | 3 | 1.4 GB | ND GIS Hub | Statewide |
| NH | 2 | 910 MB | NH GRANIT | Statewide |
| NJ | 4 | 220 MB | NJ GIS | Statewide |
| NM | 2 | 204 MB | NM RGIS | Statewide |
| NV | 5 | 3.3 GB | NV State | Statewide |
| NY | 3 | 1.7 GB | NYS ITS | Statewide |
| OH | 7 | 74 MB | OH SOS | Statewide |
| PA | 6 | 1.2 GB | PA PASDA | Statewide + Counties |
| TN | 7 | 860 MB | TN TNMAP | Statewide + Counties |
| TX | 11 | 3.6 GB | TNRIS StratMap | Statewide + Counties |
| UT | 2 | 467 MB | UT AGRC | Statewide |
| VA | 9 | 1.9 GB | VA VGIN | Statewide + Counties |
| VT | 2 | 13 KB | VT VCGI | Statewide |
| WA | 4 | 395 MB | WA DNR | Statewide |
| WI | 6 | 1.5 GB | WI DNR | Statewide |
| WV | 2 | 2.7 GB | WV GIS | Statewide |

### Partial County Coverage (19 States)

These states have county-level data only (no statewide source):

| State | Counties | Size | Notes |
|-------|----------|------|-------|
| AK | 6 | 312 MB | Major boroughs covered |
| AL | 4 | 336 MB | Madison, Montgomery covered |
| AZ | 6 | 1.0 GB | Maricopa, Pima partial |
| GA | 9 | 576 MB | Metro Atlanta partial |
| IL | 8 | 1.6 GB | Cook County large file |
| KS | 4 | 294 MB | Major counties |
| KY | 3 | 424 MB | Northern KY covered |
| LA | 6 | 216 MB | Major parishes |
| MI | 10 | 1.0 GB | SE Michigan covered |
| MN | 5 | 198 MB | Twin Cities area |
| MO | 7 | 341 MB | KC/STL metro partial |
| MS | 2 | 310 MB | DeSoto County |
| NE | 2 | 125 MB | Omaha area |
| OK | 2 | 24 KB | **Needs more coverage** |
| OR | 5 | 186 MB | **Needs more coverage** |
| RI | 2 | 28 KB | **Needs more coverage** |
| SC | 6 | 241 MB | Charleston, Greenville |
| SD | 3 | 55 MB | Sioux Falls area |
| WY | 3 | 142 MB | Laramie County |

### Priority States Needing More Data

1. **OK** - Only 2 small county files (24 KB total)
2. **RI** - Only 2 small files (28 KB total)
3. **OR** - 5 counties but missing statewide
4. **FL** - Has statewide API but only metadata exported
5. **SD** - Limited coverage

---

## Enrichment Data Layers

### Public Lands (PAD-US)
- **Source**: USGS Gap Analysis Project
- **Files**: 7 files, 600 MB
- **Coverage**: Nationwide
- **Includes**: BLM, USFS, NPS, FWS, State lands
- **Last Updated**: 2026-01-15

### Wildlife Management
- **GMU Boundaries**: CO, ID, MT, TX, WY, AZ, NM, OR, WA, WI, MI
- **WMA Boundaries**: TX, CO, MT, ID, OR, NM, AZ, WI, WY
- **FWS Wildlife Refuges**: Nationwide
- **Total Files**: 24 files, 600 MB

### Water Features (NHD)
- **Source**: USGS National Hydrography Dataset
- **Files**: 4 files, 3 GB
- **Coverage**: TX, CO, nationwide flowlines

### Wetlands (NWI)
- **Source**: US Fish & Wildlife Service
- **Files**: 4 files, 2 GB
- **Coverage**: TX, MS (more states available)

### USFS Trails & Roads
- **Trail MVUM**: Nationwide, 60 MB
- **Road MVUM**: Nationwide, 355 MB
- **State boundaries**: AK, AZ, CA, CO, ID, MT, NM, NV, OR, TX, WI, WY

### Fire Data
- **Source**: NIFC
- **Wildfire perimeters**: Nationwide, 106 MB
- **Fire perimeters**: 14 MB

---

## Scraping History

### Major Scraping Runs

| Date | States | Records | Notes |
|------|--------|---------|-------|
| 2026-01-13 | TX | 28M | TNRIS StratMap full export |
| 2026-01-13 | Multiple | 45+ | Initial multi-state scrape |
| 2026-01-14 | CA, NY, FL | 25M+ | Large state exports |
| 2026-01-15 | All | - | Enrichment data processing |

### Known Issues & Fixes

| Issue | State/County | Fix | Status |
|-------|--------------|-----|--------|
| Coordinate shift +172.5 | TX Harris | `fix_harris_coords.py` | Fixed |
| Web Mercator not WGS84 | Multiple | Force `-s_srs EPSG:3857` | Fixed |
| SSL certificate errors | Some counties | Use SSL fix script | Fixed |
| Memory exhaustion >5GB | Large files | Use streaming tippecanoe | Fixed |
| Tippecanoe "can't guess maxzoom" | Small files | Use `-z14` instead of `-zg` | Fixed |

---

## API Sources

### Statewide APIs (High Value)

| State | API | Records | URL |
|-------|-----|---------|-----|
| TX | TNRIS StratMap | ~28M | feature.stratmap.tnris.org |
| NY | NYS ITS | ~9M | services6.arcgis.com |
| FL | DEP | ~10M | ca.dep.state.fl.us/arcgis |
| OH | SOS | ~5.5M | gis.ohiosos.gov |
| CA | Multiple | ~15M | Various county APIs |

### Monitored APIs (Agent)

The autonomous agent monitors these APIs every 6 hours:
- `tx_statewide` - Texas TNRIS
- `fl_statewide` - Florida DEP
- `ny_statewide` - New York ITS
- `oh_statewide` - Ohio SOS
- `ca_la_county` - LA County

---

## Cloudflare R2 Credentials

```
R2_ACCESS_KEY = ecd653afe3300fdc045b9980df0dbb14
R2_SECRET_KEY = c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35
R2_BUCKET = gspot-tiles
R2_ENDPOINT = https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com
R2_PUBLIC_URL = https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev
```

---

## Update Schedule

| Data Type | Frequency | Next Update |
|-----------|-----------|-------------|
| Priority states (TX, CA, FL) | Monthly | 2026-02-01 |
| All other states | Quarterly | 2026-04-01 |
| PAD-US public lands | Annual (October) | 2026-10-01 |
| Weather/Wind | Real-time | N/A (API) |
| Fire perimeters | Weekly | Automated |

---

## Running the Pipeline

### Quick Commands

```bash
cd /home/exx/Documents/C/hitd_maps/data-pipeline

# Setup environment
./scripts/setup_environment.sh

# Activate
source venv/bin/activate

# Run autonomous agent (every 6 hours)
python3 agent/data_agent.py --interval 360

# Run single state scrape
python3 scripts/export_county_parcels.py --state TX

# Run full pipeline (reproject → tile → upload → cleanup)
python3 agent/data_agent.py --pipeline

# Cleanup local files already in R2
python3 agent/data_agent.py --cleanup
```

### Systemd Service

```bash
sudo systemctl start data-agent
sudo systemctl status data-agent
journalctl -u data-agent -f
```

---

*This document is auto-generated and updated by the Data Agent*
