# Property Data Enrichment Guide

## Overview

This document describes the enrichment data sources used to add context to parcel/property data for the GSpot Outdoors app. Enrichment data enhances basic parcel information with outdoor recreation-relevant attributes like proximity to public lands, water features, wetlands, and land cover.

**Date Created:** 2026-01-13
**Last Updated:** 2026-01-13

---

## Quick Start

```bash
cd data-pipeline/scripts/enrichment

# Download enrichment data for a state (top 3 sources)
python3 run_enrichment_pipeline.py --state TX

# Download with PMTiles generation and R2 upload
python3 run_enrichment_pipeline.py --state TX --pmtiles --upload --cleanup

# Download specific sources
python3 run_enrichment_pipeline.py --state TX --sources pad_us,nwi,nhd

# Download all sources for multiple states
python3 run_enrichment_pipeline.py --state TX,CO,MT --all-sources --pmtiles --upload
```

---

## Data Sources by Priority

### Priority 1: PAD-US (Protected Areas Database) ⭐⭐⭐

**The most valuable enrichment for outdoor recreation.**

| Attribute | Value |
|-----------|-------|
| **Provider** | USGS Gap Analysis Project |
| **URL** | https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-download |
| **Format** | GeoDatabase, Shapefile, GeoPackage, GeoJSON |
| **Update Frequency** | Annual (October) |
| **Current Version** | 4.0 |
| **Script** | `scripts/enrichment/download_pad_us.py` |

**What it includes:**
- National Forests (USFS)
- BLM lands
- National Parks (NPS)
- National Wildlife Refuges (FWS)
- State Parks & Forests
- Local/Regional Parks
- Conservation Easements
- Wilderness Areas

**Key Fields:**
- `Mang_Name` - Managing agency name
- `Des_Tp` - Designation type (NF, NP, NWR, SP, WA, etc.)
- `Pub_Access` - Public access level (OA=Open, RA=Restricted, XA=Closed)
- `GAP_Sts` - GAP Status (1-4, protection level)
- `GIS_Acres` - Area in acres

**Enrichment Fields to Add:**
```sql
nearest_public_land_name VARCHAR(255)
nearest_public_land_type VARCHAR(50)
distance_to_public_land_m INTEGER
public_access_level VARCHAR(20)
adjacent_to_public_land BOOLEAN
```

**Usage:**
```bash
# Download PAD-US for Texas
python3 download_pad_us.py --state TX --pmtiles --upload --cleanup

# Download for multiple states
python3 download_pad_us.py --state TX,CO,MT,WY --pmtiles --upload
```

---

### Priority 2: NWI (National Wetlands Inventory) ⭐⭐⭐

**Critical for waterfowl hunting and fishing.**

| Attribute | Value |
|-----------|-------|
| **Provider** | US Fish & Wildlife Service |
| **URL** | https://www.fws.gov/program/national-wetlands-inventory |
| **API** | https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest |
| **Update Frequency** | Biannual (May, October) |
| **Script** | `scripts/enrichment/download_nwi.py` |

**Cowardin Classification Codes:**
| Code | Name | Hunting Relevance |
|------|------|-------------------|
| PEM | Palustrine Emergent (marshes) | **Excellent** waterfowl habitat |
| PFO | Palustrine Forested (swamps) | Good wood duck habitat |
| PSS | Palustrine Scrub-Shrub | Moderate waterfowl |
| PUB | Palustrine Unconsolidated Bottom (ponds) | Fishing, waterfowl |
| L1/L2 | Lacustrine (lakes) | Fishing |
| R1-R5 | Riverine (streams/rivers) | Fishing |

**Enrichment Fields:**
```sql
has_wetlands BOOLEAN
wetland_acres DECIMAL(10,2)
wetland_types TEXT[]
waterfowl_habitat BOOLEAN
```

**Usage:**
```bash
python3 download_nwi.py --state TX --pmtiles --upload --cleanup
```

---

### Priority 3: NHD (National Hydrography Dataset) ⭐⭐⭐

**Water features for fishing and water proximity.**

| Attribute | Value |
|-----------|-------|
| **Provider** | USGS |
| **URL** | https://www.usgs.gov/national-hydrography |
| **API** | https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer |
| **Update Frequency** | Continuous |
| **Script** | `scripts/enrichment/download_nhd.py` |

**Note:** NHD was retired Oct 2023, replaced by 3DHP. Existing data remains valid.

**Feature Types:**
| FType | Name | Description |
|-------|------|-------------|
| 460 | Stream/River | Linear water features |
| 390 | Lake/Pond | Standing water bodies |
| 336 | Canal/Ditch | Artificial waterways |
| 431 | Dam/Weir | Water control structures |

**Enrichment Fields:**
```sql
distance_to_water_m INTEGER
nearest_water_name VARCHAR(255)
nearest_water_type VARCHAR(50)
has_stream_frontage BOOLEAN
has_lake_frontage BOOLEAN
watershed_huc8 VARCHAR(8)
```

**Usage:**
```bash
# Download flowlines and waterbodies (default)
python3 download_nhd.py --state TX --merge --pmtiles --upload

# Download specific layers
python3 download_nhd.py --state TX --layers 2,5 --merge
```

---

### Priority 4: State Wildlife Management Areas ⭐⭐

**State-specific public hunting lands.**

| Attribute | Value |
|-----------|-------|
| **Provider** | Various State Agencies |
| **Update Frequency** | Annual (varies) |
| **Script** | `scripts/enrichment/download_state_wma.py` |

**Available States:**
- TX (TPWD), PA (Game Commission), MI (DNR), WI (DNR)
- MN (DNR), CO (CPW), MT (FWP), NC (WRC), GA (DNR)
- FL (FWC), OH (DNR)

**Walk-In Hunting Programs:**
- KS: WIHA (Walk-In Hunting Areas)
- NE: Open Fields and Waters
- ND: PLOTS (Private Land Open To Sportsmen)
- SD: Walk-In Areas
- MT: Block Management

**Enrichment Fields:**
```sql
nearest_wma_name VARCHAR(255)
distance_to_wma_m INTEGER
adjacent_to_wma BOOLEAN
```

**Usage:**
```bash
python3 download_state_wma.py --state TX,PA,MI --pmtiles --upload

# Include walk-in hunting programs
python3 download_state_wma.py --state KS,ND,NE --walk-in --pmtiles --upload
```

---

### Priority 5: NLCD (National Land Cover Database) ⭐⭐

**Land cover classification for habitat assessment.**

| Attribute | Value |
|-----------|-------|
| **Provider** | USGS EROS / MRLC Consortium |
| **URL** | https://www.mrlc.gov/ |
| **Format** | GeoTIFF (30m raster) |
| **Update Frequency** | Annual |
| **Script** | `scripts/enrichment/download_nlcd.py` |

**Land Cover Classes:**
| Code | Name | Outdoor Relevance |
|------|------|-------------------|
| 41 | Deciduous Forest | Good deer habitat |
| 42 | Evergreen Forest | Good deer/turkey habitat |
| 43 | Mixed Forest | Good wildlife habitat |
| 81 | Pasture/Hay | Dove, quail habitat |
| 82 | Cultivated Crops | Dove, waterfowl staging |
| 90 | Woody Wetlands | Waterfowl, deer |
| 95 | Emergent Wetlands | Waterfowl habitat |

**Note:** NLCD is raster data. Use zonal statistics to summarize per parcel.

**Enrichment Fields:**
```sql
land_cover_class INTEGER
land_cover_name VARCHAR(50)
tree_canopy_pct INTEGER
is_forested BOOLEAN
is_agricultural BOOLEAN
```

**Usage:**
```bash
# Extract for small area via WMS
python3 download_nlcd.py --bbox -97.5,30.0,-97.0,30.5 --year 2021

# Generate zonal statistics helper script
python3 download_nlcd.py --generate-zonal-script
```

---

### Priority 6: SSURGO (Soil Survey) ⭐

**Soil data for habitat and agricultural assessment.**

| Attribute | Value |
|-----------|-------|
| **Provider** | USDA NRCS |
| **URL** | https://sdmdataaccess.nrcs.usda.gov/ |
| **API** | REST API for on-demand queries |
| **Update Frequency** | Continuous |
| **Script** | `scripts/enrichment/download_ssurgo.py` |

**Drainage Classes:**
| Class | Description | Wetland Indicator |
|-------|-------------|-------------------|
| Excessively drained | Water removed very rapidly | No |
| Well drained | Water removed readily | No |
| Moderately well drained | Water removed somewhat slowly | Possible |
| Somewhat poorly drained | Water removed slowly | Possible |
| Poorly drained | Soil remains wet | **Yes** |
| Very poorly drained | Water at surface most of year | **Yes** |

**Enrichment Fields:**
```sql
soil_type VARCHAR(100)
drainage_class VARCHAR(50)
hydric_soil BOOLEAN
forest_productivity VARCHAR(20)
```

**Usage:**
```bash
# Query point
python3 download_ssurgo.py --point 30.2672,-97.7431

# Download for area
python3 download_ssurgo.py --bbox -97.5,30.0,-97.0,30.5 --pmtiles --upload
```

---

### Priority 7: Federal Lands (BLM/USFS) ⭐

**Detailed federal land attributes beyond PAD-US.**

| Attribute | Value |
|-----------|-------|
| **BLM Service** | https://gis.blm.gov/arcgis/rest/services |
| **USFS Service** | https://apps.fs.usda.gov/arcx/rest/services |
| **Update Frequency** | Quarterly (BLM), Annual (USFS) |
| **Script** | `scripts/enrichment/download_federal_lands.py` |

**Note:** Most federal lands are in PAD-US. Use this for BLM/USFS-specific attributes.

**Usage:**
```bash
python3 download_federal_lands.py --blm --usfs --wilderness --state NV,UT,AZ --pmtiles --upload
```

---

### Priority 8: FEMA Flood Zones ⭐

**Flood risk for camping and access assessment.**

| Attribute | Value |
|-----------|-------|
| **Provider** | FEMA |
| **URL** | https://hazards.fema.gov/gis/nfhl/rest/services |
| **Update Frequency** | Continuous |
| **Script** | `scripts/enrichment/download_fema_flood.py` |

**Flood Zone Codes:**
| Zone | Risk | Description |
|------|------|-------------|
| A, AE, AH, AO | High | 100-year floodplain |
| V, VE | High | Coastal flood with wave action |
| X500 | Moderate | 500-year floodplain |
| X | Minimal | Outside 500-year |
| D | Unknown | Undetermined |

**Enrichment Fields:**
```sql
flood_zone VARCHAR(10)
in_100yr_floodplain BOOLEAN
in_500yr_floodplain BOOLEAN
```

**Usage:**
```bash
python3 download_fema_flood.py --bbox -97.5,30.0,-97.0,30.5 --pmtiles --upload
```

---

## Data Update Schedule

| Source | Frequency | Typical Release | Next Check |
|--------|-----------|-----------------|------------|
| PAD-US | Annual | October | 2026-10-01 |
| NWI | Biannual | May, October | 2026-05-01 |
| NHD | Continuous | - | 2026-06-01 |
| State WMA | Annual | Varies | 2026-06-01 |
| NLCD | Annual | - | 2027-01-01 |
| SSURGO | Continuous | - | 2026-06-01 |
| BLM/USFS | Quarterly/Annual | - | 2026-04-01 |
| FEMA | Continuous | - | 2026-04-01 |

**Check dates are stored in:** `config/enrichment_sources.json`

---

## Directory Structure

```
data-pipeline/
├── config/
│   └── enrichment_sources.json    # Source registry & update schedule
├── output/
│   └── enrichment/
│       ├── raw/                   # Original downloads
│       │   ├── pad_us/
│       │   ├── nwi/
│       │   └── ...
│       ├── geojson/               # Processed WGS84 GeoJSON
│       │   ├── pad_us_tx.geojson
│       │   ├── nwi_tx.geojson
│       │   └── ...
│       ├── pmtiles/               # Vector tiles for visualization
│       │   ├── pad_us_tx.pmtiles
│       │   └── ...
│       ├── raster/                # Raster data (NLCD)
│       │   └── nlcd/
│       └── cache/                 # API query cache
│           └── ssurgo/
├── scripts/
│   └── enrichment/
│       ├── run_enrichment_pipeline.py  # Master orchestrator
│       ├── download_pad_us.py
│       ├── download_nwi.py
│       ├── download_nhd.py
│       ├── download_state_wma.py
│       ├── download_nlcd.py
│       ├── download_ssurgo.py
│       ├── download_federal_lands.py
│       └── download_fema_flood.py
└── docs/
    └── ENRICHMENT_DATA.md         # This file
```

---

## Cloudflare R2 Structure

```
gspot-tiles/
├── enrichment/
│   ├── pad_us/
│   │   ├── pad_us_tx.geojson
│   │   ├── pad_us_tx.pmtiles
│   │   └── ...
│   ├── nwi/
│   │   ├── nwi_tx.geojson
│   │   ├── nwi_tx.pmtiles
│   │   └── ...
│   ├── nhd/
│   ├── state_wma/
│   ├── nlcd/
│   ├── ssurgo/
│   ├── blm/
│   ├── usfs/
│   ├── fema/
│   └── epa/
├── geojson/                       # Parcel data
└── pmtiles/                       # Parcel tiles
```

**Public URL Base:** `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev`

**Example URLs:**
- `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/enrichment/pad_us/pad_us_tx.pmtiles`
- `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/enrichment/nwi/nwi_tx.geojson`

---

## Processing Pipeline

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Download from  │────▶│  Validate CRS    │────▶│  Convert to     │
│  API/Portal     │     │  (EPSG:4326)     │     │  GeoJSON        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                                               │
        │                                               ▼
┌───────┴───────┐                              ┌─────────────────┐
│  output/      │                              │  Generate       │
│  enrichment/  │                              │  PMTiles        │
│  raw/         │                              │  (tippecanoe)   │
└───────────────┘                              └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Remove local   │◀────│  Upload to       │◀────│  output/        │
│  files          │     │  Cloudflare R2   │     │  enrichment/    │
│  (optional)     │     │  (boto3)         │     │  pmtiles/       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Tippecanoe Settings for Enrichment Layers

| Layer | Min Zoom | Max Zoom | Special Settings |
|-------|----------|----------|------------------|
| PAD-US | 4 | 14 | `--drop-densest-as-needed` |
| NWI | 8 | 14 | `--drop-densest-as-needed` |
| NHD | 6 | 14 | `--coalesce-smallest-as-needed` |
| State WMA | 6 | 14 | `--drop-densest-as-needed` |
| Federal Lands | 4 | 14 | `--drop-densest-as-needed` |
| FEMA Flood | 8 | 14 | `--drop-densest-as-needed` |
| Soils | 10 | 14 | `--drop-densest-as-needed` |

---

## Flutter App Integration

```dart
// Load enrichment PMTiles
final publicLandsUrl = 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/enrichment/pad_us/pad_us_tx.pmtiles';
final wetlandsUrl = 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/enrichment/nwi/nwi_tx.pmtiles';

// Add layers to MapLibre
map.addSource('public-lands', {
  'type': 'vector',
  'url': 'pmtiles://$publicLandsUrl'
});

map.addLayer({
  'id': 'public-lands-fill',
  'type': 'fill',
  'source': 'public-lands',
  'source-layer': 'public_lands',
  'paint': {
    'fill-color': '#228B22',
    'fill-opacity': 0.3
  }
});
```

---

## Parcel Enrichment Query Examples

### SQL: Find parcels adjacent to public land
```sql
SELECT p.*,
       ST_Distance(p.geom, pad.geom) AS distance_to_public_m,
       pad.Unit_Nm AS nearest_public_land
FROM parcels p
LEFT JOIN LATERAL (
    SELECT geom, Unit_Nm
    FROM pad_us
    WHERE ST_DWithin(p.geom, pad_us.geom, 1609)  -- within 1 mile
    ORDER BY ST_Distance(p.geom, pad_us.geom)
    LIMIT 1
) pad ON true;
```

### SQL: Find parcels with wetlands
```sql
SELECT p.*,
       COALESCE(SUM(ST_Area(ST_Intersection(p.geom, w.geom))), 0) AS wetland_area_sqm
FROM parcels p
LEFT JOIN nwi w ON ST_Intersects(p.geom, w.geom)
GROUP BY p.id;
```

---

## Troubleshooting

### API Rate Limits
- PAD-US: No known limits, but paginate at 2000 records
- NWI: Paginate at 2000 records
- NHD: Paginate at 2000 records
- SSURGO: SQL query timeout ~60 seconds

### Large State Downloads
For very large states (TX, CA), consider:
1. Download by county or region
2. Use parallel processing
3. Stream directly to R2 without local storage

### Coordinate System Issues
All enrichment data should be in WGS84 (EPSG:4326). If you encounter projected coordinates:
```bash
ogr2ogr -f GeoJSON -t_srs EPSG:4326 output.geojson input.geojson
```

### Missing State Data
Some state WMA services may be unavailable or URLs may change. Check state fish & game websites for current GIS data access.

---

## Cost Summary

| Source | Cost | Notes |
|--------|------|-------|
| PAD-US | Free | Public domain |
| NWI | Free | Public domain |
| NHD | Free | Public domain |
| State WMA | Free | Public (varies) |
| NLCD | Free | Public domain |
| SSURGO | Free | Public domain |
| BLM/USFS | Free | Public domain |
| FEMA | Free | Public domain |

**Total enrichment data cost: $0**

---

## References

- [PAD-US Documentation](https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-overview)
- [NWI Web Services](https://www.fws.gov/program/national-wetlands-inventory/web-mapping-services)
- [NHD Access Guide](https://www.usgs.gov/national-hydrography/access-national-hydrography-products)
- [MRLC/NLCD](https://www.mrlc.gov/)
- [Soil Data Access Help](https://sdmdataaccess.nrcs.usda.gov/WebServiceHelp.aspx)
- [BLM GIS Hub](https://gbp-blm-egis.hub.arcgis.com/)
- [USFS Geodata](https://data.fs.usda.gov/geodata/)
