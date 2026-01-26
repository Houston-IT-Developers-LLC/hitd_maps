# HITD Maps - Claude Code Context

## Project Overview

HITD Maps (mapsfordevelopers.com) is a self-hosted Google Maps alternative with comprehensive USA property parcel coverage. All data is hosted on Cloudflare R2 for zero-egress costs and served via CDN globally.

---

## 📊 Coverage Status

**For complete coverage details, see [COVERAGE_STATUS.md](COVERAGE_STATUS.md)**

### Quick Stats (2026-01-24)

| Metric | Value |
|--------|-------|
| **Parcel Coverage** | 63% (32/51 states fully covered) |
| **States at 100%** | 32 (includes DC) |
| **States Partial** | 18 (county-level only, 2-27% each) |
| **States Missing** | 1 (Rhode Island - no statewide DB exists) |
| **Total Parcel Files** | 203 |
| **Total R2 Storage** | 625.3 GB |

### Data Types Available
- Parcels (70.1 GB) - Property boundaries
- Addresses (7.0 GB) - Overture nationwide
- POIs (14.6 GB) - Overture businesses/landmarks
- Roads (18.4 GB) - Overture nationwide
- Basemap (233.4 GB) - Protomaps global
- Terrain (43.8 GB) - Elevation data
- Public Lands (616 MB) - PAD-US
- HIFLD (219 MB) - Hospitals, schools, fire stations

---

## Quick Reference Commands

### Check Coverage
```bash
# Generate fresh coverage report
python3 data-pipeline/scripts/generate_coverage_report.py

# View coverage status
cat data-pipeline/data/coverage_status.json | jq '.states.TX'
```

### Check for Data Updates (PASSIVE - no automatic changes)
```bash
# Check all sources
python3 data-pipeline/scripts/check_data_freshness.py

# Check specific state
python3 data-pipeline/scripts/check_data_freshness.py --state TX

# Quick check (priority sources only)
python3 data-pipeline/scripts/check_data_freshness.py --quick
```

### Download Missing Data (MANUAL trigger)
```bash
# Find sources for missing state
python3 data-pipeline/agent/source_finder.py --state RI

# Download from known source
python3 data-pipeline/scripts/download_missing_states.py --source tx_montgomery --workers 10

# Process and upload
python3 data-pipeline/scripts/parallel_process_upload.py 4
```

### Makefile Shortcuts
```bash
cd data-pipeline
make status      # Pipeline status
make pipeline    # Process pending files
make issues      # Show open issues
make auto-fix    # Run auto-fixes
```

---

## Architecture

```
Frontend (Vercel) ─────► Cloudflare CDN ─────► R2 Storage
     │                                              │
     │ Next.js 15                                   │ PMTiles
     │ MapLibre GL JS                               │ ~414 GB
     │ Supabase Auth                                │
     │ Stripe Payments                              │
     │                                              │
     └──────────────────────────────────────────────┘
                           │
                    Data Pipeline
                           │
              ┌────────────┴────────────┐
              │                         │
         Download              Process & Upload
              │                         │
         ArcGIS REST           ogr2ogr → tippecanoe
         County APIs           → pmtiles → R2
```

### Key Directories
```
hitd_maps/
├── web/                    # Next.js frontend
├── demo/                   # Static map demo
├── data-pipeline/
│   ├── scripts/            # Processing scripts
│   ├── agent/              # AI agent tools (MANUAL)
│   └── data/               # Tracking data
│       ├── valid_parcels.json
│       ├── coverage_status.json
│       ├── data_sources_registry.json
│       └── freshness_report.json
└── docs/
    ├── DATA_INVENTORY.md   # What we have
    ├── DATA_GAPS.md        # What's missing
    └── DEVELOPER_GUIDE.md  # Onboarding guide
```

---

## R2 Configuration

```
Bucket: gspot-tiles
Endpoint: https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com
CDN: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev
AWS_ACCESS_KEY: ecd653afe3300fdc045b9980df0dbb14
AWS_SECRET_KEY: c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35
```

---

## Third-Party Services

| Service | Purpose | Docs |
|---------|---------|------|
| Cloudflare R2 | Tile storage & CDN | r2.dev |
| Vercel | Frontend hosting | vercel.com |
| Supabase | Auth & database | supabase.com |
| Stripe | Payments | stripe.com |
| Ollama | Local AI (10.8.0.1:11434) | ollama.ai |

## Open Source Stack

### Frontend
- Next.js 15, React 19, TypeScript
- MapLibre GL JS 4.5, PMTiles 3.0.6
- Protomaps themes, Tailwind CSS
- Radix UI, Lucide icons

### Data Pipeline
- GDAL/ogr2ogr (reprojection)
- Tippecanoe (tile generation)
- PMTiles CLI (validation)
- boto3 (R2 uploads)
- Python 3.10+

---

## Key Scripts

### Coverage & Monitoring
| Script | Purpose |
|--------|---------|
| `generate_coverage_report.py` | Generate coverage_status.json |
| `check_data_freshness.py` | Passive update checking |

### Data Acquisition
| Script | Purpose |
|--------|---------|
| `download_missing_states.py` | Download from ArcGIS REST |
| `smart_reproject_parcels.py` | Auto-CRS reprojection |
| `batch_convert_pmtiles.py` | GeoJSON to PMTiles |
| `upload_to_r2_boto3.py` | Upload to R2 |

### Agent Tools (MANUAL trigger only)
| Script | Purpose |
|--------|---------|
| `agent/source_finder.py` | Find sources for missing states |
| `agent/data_agent.py` | Main orchestrator |
| `agent/auto_fixer.py` | Fix common issues |

---

## Data Tracking Files

### valid_parcels.json
List of 197 verified working PMTiles files. Add new files here after validation.

### coverage_status.json
Machine-readable coverage by state:
```json
{
  "states": {
    "TX": {
      "status": "partial",
      "completeness_pct": 19,
      "statewide_file": "parcels_tx_statewide",
      "missing_counties": ["Montgomery", "Brazos", ...]
    }
  }
}
```

### data_sources_registry.json
Master registry of ALL known data sources (have and don't have):
- ArcGIS REST API endpoints
- Update frequencies
- Record counts
- Contact info

### freshness_report.json
Results of last `check_data_freshness.py` run:
- Sources with updates available
- Sources current
- Sources with errors

---

## Coordinate Systems

Most parcel data comes in State Plane projections:

| State | EPSG Codes |
|-------|------------|
| TX | 2276-2280, 3857 |
| GA | 2239, 2240 |
| FL | 2236-2238, 3086-3087 |
| CA | 2227-2232, 3310 |
| NY | 2260-2263 |
| PA | 2271, 2272 |
| OH | 3734, 3735 |

**Target:** WGS84 (EPSG:4326)

Use `smart_reproject_parcels.py` for auto-detection.

---

## Common Issues & Fixes

### Parcels Not Loading
1. **Wrong CRS** - Data not reprojected to WGS84
   - Fix: `python3 smart_reproject_parcels.py input.geojson`
2. **NO_TILE_DATA** - PMTiles empty
   - Fix: Rebuild with tippecanoe
3. **Layer mismatch** - Source layer name wrong
   - Check: `pmtiles show file.pmtiles`

### R2 Upload Issues
```bash
# Test credentials
aws s3 ls s3://gspot-tiles --endpoint-url $R2_ENDPOINT
```

---

## Update Schedule

| Data Type | Frequency | When to Check |
|-----------|-----------|---------------|
| State Parcels | Annual (Q1) | Monthly |
| County Parcels | Quarterly-Annual | Monthly |
| PAD-US | Annual (Nov) | Annually |
| Protomaps | Monthly | Monthly |

---

## Documentation

| File | Contents |
|------|----------|
| [DATA_INVENTORY.md](docs/DATA_INVENTORY.md) | Complete list of what we have |
| [DATA_GAPS.md](docs/DATA_GAPS.md) | What's missing, how to get it |
| [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | New developer onboarding |
| [data_sources_registry.json](data-pipeline/data/data_sources_registry.json) | All known sources |

---

## Deployment

- **Frontend**: Vercel at https://hitd-maps.vercel.app/
- **Demo**: Static demo at /demo/index.html
- **Data**: Cloudflare R2 CDN (global)
- **Pipeline**: Local server with parallel workers

---

## ArcGIS Data Sources (Key APIs)

```python
# Florida statewide (10.8M parcels)
'https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer/0'

# Texas statewide (28M parcels)
'https://feature.stratmap.tnris.org/arcgis/rest/services/StratMap/StratMap22_Land_Parcels_BIG/FeatureServer/0'

# Vermont statewide (344K parcels)
'https://services1.arcgis.com/BkFxaEFNwHqX3tAw/arcgis/rest/services/FS_VCGI_OPENDATA_Cadastral_VTPARCELS_poly_standardized_parcels_SP_v1/FeatureServer/0'

# Washington DC (200K parcels)
'https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Property_and_Land_WebMercator/MapServer/53'
```

See `data_sources_registry.json` for complete list.
