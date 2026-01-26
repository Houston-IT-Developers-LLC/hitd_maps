# HITD Maps Developer Guide

**Last Updated:** 2026-01-24

This guide provides everything a new developer needs to understand and work with the HITD Maps system.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Third-Party Services](#third-party-services)
4. [Open Source Libraries](#open-source-libraries)
5. [Getting Started](#getting-started)
6. [Data Pipeline](#data-pipeline)
7. [Frontend Development](#frontend-development)
8. [Common Tasks](#common-tasks)
9. [Data Sources](#data-sources)
10. [Troubleshooting](#troubleshooting)

---

## System Overview

HITD Maps (mapsfordevelopers.com) is a self-hosted Google Maps alternative providing:

- **Vector basemap** - OpenStreetMap data via Protomaps Planet
- **Property parcels** - 197 files covering 47 states + DC
- **POI/Address data** - Points of interest and geocoding
- **Enrichment layers** - Wetlands, public lands, facilities

All data is stored on Cloudflare R2 for zero-egress costs and served via global CDN.

### Key Stats
| Metric | Value |
|--------|-------|
| Total Files | 197 parcel files |
| Coverage | 47 states + DC (60.8%) |
| Storage | ~414 GB in R2 |
| Tile Format | PMTiles (cloud-optimized) |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         User Browser                              │
│                    (MapLibre GL JS + PMTiles)                    │
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTPS
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Cloudflare CDN                               │
│                 (Global edge caching)                            │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Cloudflare R2                                │
│              (Object storage - gspot-tiles bucket)               │
│                                                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │ protomaps-  │ │ parcels_*.  │ │ enrichment/ │ │  terrain/  │ │
│  │ planet.pmtiles│ │  pmtiles    │ │   layers   │ │   tiles    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└───────────────────────────▲──────────────────────────────────────┘
                            │ Upload
                            │
┌──────────────────────────────────────────────────────────────────┐
│                    Data Pipeline Server                           │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Download Scripts                          │  │
│  │  • download_missing_states.py (ArcGIS REST)               │  │
│  │  • Source-specific scrapers                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Processing Pipeline                       │  │
│  │  • ogr2ogr (reproject to WGS84)                           │  │
│  │  • tippecanoe (GeoJSON → PMTiles)                         │  │
│  │  • pmtiles show (validation)                              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Upload to R2                             │  │
│  │  • boto3 S3-compatible client                             │  │
│  │  • upload_to_r2_boto3.py                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      Frontend (Vercel)                            │
│                                                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │   Next.js   │ │  Supabase   │ │   Stripe    │ │  MapLibre  │ │
│  │  App Router │ │    Auth     │ │  Payments   │ │  GL JS     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Third-Party Services

### Cloudflare R2
**Purpose:** Object storage and CDN for all map tiles

| Config | Value |
|--------|-------|
| Bucket | `gspot-tiles` |
| Endpoint | `https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com` |
| CDN URL | `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev` |

**Why R2?** Zero egress fees. Map tiles generate massive bandwidth; R2 makes this economically viable.

**Docs:** https://developers.cloudflare.com/r2/

### Vercel
**Purpose:** Frontend hosting with edge functions

- Automatic deployments from Git
- Edge-optimized Next.js
- Preview deployments for PRs

**Docs:** https://vercel.com/docs

### Supabase
**Purpose:** Authentication and database

- Email/password and OAuth authentication
- PostgreSQL database for user profiles, API keys
- Row-level security for data isolation

**Docs:** https://supabase.com/docs

### Stripe
**Purpose:** Payment processing

- Subscription management (Free, Pro, Enterprise tiers)
- Checkout sessions
- Customer portal for billing

**Docs:** https://stripe.com/docs

### Ollama (Local AI)
**Purpose:** Local AI for data pipeline agents

- Runs locally at `10.8.0.1:11434`
- Used for source discovery and data validation
- NOT automatic - manually triggered only

**Docs:** https://ollama.ai/

---

## Open Source Libraries

### Frontend (Next.js)

| Library | Version | Purpose |
|---------|---------|---------|
| `next` | 15.1.0 | React framework with App Router |
| `react` | 19.0.0 | UI library |
| `maplibre-gl` | 4.5.0 | Map rendering engine |
| `pmtiles` | 3.0.6 | Cloud-optimized tile protocol |
| `protomaps-themes-base` | 4.5.0 | Map styling themes |
| `@supabase/supabase-js` | 2.47.0 | Supabase client |
| `@supabase/ssr` | 0.5.0 | Server-side auth |
| `stripe` | 17.0.0 | Payment integration |
| `@stripe/stripe-js` | 4.0.0 | Stripe client |
| `tailwindcss` | 3.4.0 | CSS framework |
| `@radix-ui/react-*` | various | UI primitives |
| `lucide-react` | 0.468.0 | Icons |
| `class-variance-authority` | 0.7.0 | Component variants |
| `clsx` | 2.1.1 | Class name utility |
| `tailwind-merge` | 2.5.0 | Tailwind class merging |

### Data Pipeline (Python)

| Library | Purpose |
|---------|---------|
| `gdal` / `ogr2ogr` | Geospatial data transformation |
| `boto3` | S3-compatible uploads to R2 |
| `pyproj` | Coordinate system transformations |
| `aiohttp` | Async HTTP requests |
| `requests` | HTTP requests |
| `shapely` | Geometry operations |

### CLI Tools

| Tool | Purpose |
|------|---------|
| `tippecanoe` | GeoJSON to PMTiles/MBTiles conversion |
| `pmtiles` | PMTiles CLI (show, extract, serve) |
| `ogr2ogr` | Coordinate reprojection |
| `aws` / `rclone` | R2 uploads |

---

## Getting Started

### Prerequisites

**System Requirements:**
- Node.js 18+
- Python 3.10+
- GDAL with ogr2ogr
- Tippecanoe
- PMTiles CLI

**Install on Ubuntu/Debian:**
```bash
# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Python
sudo apt install -y python3 python3-pip python3-venv

# GDAL
sudo apt install -y gdal-bin libgdal-dev

# Tippecanoe
git clone https://github.com/felt/tippecanoe.git
cd tippecanoe && make -j && sudo make install

# PMTiles CLI
npm install -g pmtiles
```

### Frontend Setup

```bash
cd web
npm install
cp .env.example .env.local

# Edit .env.local with your keys:
# - NEXT_PUBLIC_SUPABASE_URL
# - NEXT_PUBLIC_SUPABASE_ANON_KEY
# - STRIPE_SECRET_KEY
# - NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

npm run dev
# Open http://localhost:3000
```

### Data Pipeline Setup

```bash
cd data-pipeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install boto3 requests aiohttp pyproj shapely

# Configure R2 credentials
export R2_ENDPOINT="https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
export R2_ACCESS_KEY="ecd653afe3300fdc045b9980df0dbb14"
export R2_SECRET_KEY="c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# Check status
make status
```

---

## Data Pipeline

### Directory Structure

```
data-pipeline/
├── agent/                  # AI agent scripts (manual trigger)
│   ├── data_agent.py       # Main agent orchestrator
│   ├── source_finder.py    # Find data sources for states
│   └── auto_fixer.py       # Auto-fix common issues
├── scripts/                # Processing scripts
│   ├── download_missing_states.py  # ArcGIS downloader
│   ├── smart_reproject_parcels.py  # Auto-CRS reprojection
│   ├── batch_convert_pmtiles.py    # Batch conversion
│   ├── upload_to_r2_boto3.py       # R2 upload
│   ├── generate_coverage_report.py # Coverage tracking
│   └── check_data_freshness.py     # Passive update checker
├── data/                   # Tracking data
│   ├── valid_parcels.json          # List of valid files
│   ├── coverage_status.json        # Coverage by state
│   ├── data_sources_registry.json  # All known sources
│   └── freshness_report.json       # Last freshness check
├── config/                 # Configuration
│   └── sources.json        # Data source definitions
├── output/                 # Processed files (before upload)
├── input/                  # Downloaded raw data
└── Makefile               # Common operations
```

### Pipeline Flow

```
1. DOWNLOAD: Fetch data from ArcGIS REST API or other source
   └─▶ python3 scripts/download_missing_states.py --source tx_statewide

2. REPROJECT: Convert coordinates to WGS84 (EPSG:4326)
   └─▶ ogr2ogr -t_srs EPSG:4326 output.geojson input.geojson

3. CONVERT: GeoJSON to PMTiles
   └─▶ tippecanoe -o output.pmtiles -zg input.geojson

4. VALIDATE: Check the output
   └─▶ pmtiles show output.pmtiles

5. UPLOAD: Send to R2
   └─▶ python3 scripts/upload_to_r2_boto3.py output.pmtiles

6. UPDATE: Add to valid_parcels.json
```

### Makefile Commands

```bash
# Show help
make help

# Check pipeline status
make status

# Run full update (download + process + upload)
make update

# Process existing files only
make pipeline

# Check R2 inventory
make r2-inventory

# Show issues
make issues

# Run auto-fix
make auto-fix
```

---

## Frontend Development

### Directory Structure

```
web/
├── app/                    # Next.js App Router
│   ├── (dashboard)/        # Authenticated routes
│   │   └── dashboard/
│   │       ├── page.tsx    # Main dashboard
│   │       ├── billing/    # Subscription management
│   │       └── api-keys/   # API key management
│   ├── (marketing)/        # Public routes
│   ├── api/                # API routes
│   │   └── billing/        # Stripe webhooks
│   └── layout.tsx          # Root layout
├── components/
│   └── ui/                 # Shadcn UI components
├── lib/
│   ├── supabase/           # Supabase client
│   └── utils.ts            # Utility functions
└── public/                 # Static assets
```

### Map Integration

The map uses MapLibre GL JS with PMTiles protocol:

```typescript
import maplibregl from 'maplibre-gl';
import { Protocol } from 'pmtiles';

// Register PMTiles protocol
const protocol = new Protocol();
maplibregl.addProtocol('pmtiles', protocol.tile);

// Create map
const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    sources: {
      parcels: {
        type: 'vector',
        url: 'pmtiles://https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels_tx_statewide.pmtiles'
      }
    },
    layers: [
      {
        id: 'parcels-fill',
        type: 'fill',
        source: 'parcels',
        'source-layer': 'parcels',
        paint: {
          'fill-color': '#627BC1',
          'fill-opacity': 0.5
        }
      }
    ]
  }
});
```

---

## Common Tasks

### Add New Parcel Data

```bash
# 1. Find the source (ArcGIS REST preferred)
python3 scripts/check_data_freshness.py  # See known sources

# 2. Download
python3 scripts/download_missing_states.py --source tx_montgomery --workers 10

# 3. Process (if not auto-converted)
python3 scripts/smart_reproject_parcels.py input/tx_montgomery.geojson

# 4. Validate
pmtiles show output/parcels_tx_montgomery.pmtiles

# 5. Upload
python3 scripts/upload_to_r2_boto3.py output/parcels_tx_montgomery.pmtiles

# 6. Update tracking
# Add "parcels_tx_montgomery" to data/valid_parcels.json
```

### Check Coverage Status

```bash
# Generate fresh report
python3 scripts/generate_coverage_report.py

# View specific state
cat data/coverage_status.json | jq '.states.TX'

# View summary
cat data/coverage_status.json | jq '{complete: .complete_states, partial: .partial_states, missing: .missing_states}'
```

### Check for Data Updates

```bash
# Passive check - doesn't change anything
python3 scripts/check_data_freshness.py

# Check specific state
python3 scripts/check_data_freshness.py --state TX

# Quick check (priority sources only)
python3 scripts/check_data_freshness.py --quick
```

### Find Missing Data Sources

```bash
# Use AI agent to search for sources (manual trigger)
python3 agent/source_finder.py --state RI
```

---

## Data Sources

All parcel data comes from public open data portals:

| Source Type | URL Pattern | Example |
|-------------|-------------|---------|
| State GIS | `gis.{state}.gov` | gis.ny.gov |
| ArcGIS Hub | `{state}.maps.arcgis.com` | texas.maps.arcgis.com |
| County Assessor | `{county}assessor.{state}.gov` | Various |
| ESRI Open Data | `hub.arcgis.com/search` | Search by state |

### ArcGIS REST API Pattern

Most parcel data is available via ArcGIS REST services:

```
Base URL: https://services{N}.arcgis.com/{ID}/arcgis/rest/services/{NAME}/FeatureServer/0

Query endpoint: {Base URL}/query
  ?where=1=1
  &outFields=*
  &outSR=4326
  &f=geojson
  &resultOffset=0
  &resultRecordCount=1000
```

### Known Good Sources

See `data-pipeline/data/data_sources_registry.json` for the complete list.

Key sources:
- **Florida**: `services9.arcgis.com/Gh9awoU677aKree0` - 10.8M parcels
- **Texas**: `feature.stratmap.tnris.org` - 28M parcels
- **New York**: NY GIS Clearinghouse
- **Ohio**: Ohio Geographically Referenced Information Program

---

## Troubleshooting

### Parcels Not Loading

**Symptom:** Map loads but no parcels visible

**Causes:**
1. Wrong coordinates (not reprojected to WGS84)
2. Layer name mismatch
3. Zoom level restrictions

**Fix:**
```bash
# Check the file
pmtiles show parcels_xx_county.pmtiles

# Look for:
# - bounds (should be in -180 to 180 lon, -90 to 90 lat)
# - layer names
# - tile count (should be > 0)
```

### NO_TILE_DATA Error

**Symptom:** PMTiles header valid but no tiles

**Cause:** Tippecanoe didn't generate tiles (empty input or wrong settings)

**Fix:**
```bash
# Rebuild with verbose output
tippecanoe -o output.pmtiles -zg --force input.geojson
```

### Coordinate Issues

**Symptom:** Parcels appear in wrong location (often near Africa)

**Cause:** Source data in State Plane or other projection, not reprojected

**Fix:**
```bash
# Use smart reprojection
python3 scripts/smart_reproject_parcels.py input.geojson

# Or manual with known EPSG
ogr2ogr -s_srs EPSG:2276 -t_srs EPSG:4326 output.geojson input.geojson
```

### R2 Upload Failures

**Symptom:** Upload hangs or fails

**Causes:**
1. Wrong credentials
2. File too large for single upload
3. Network issues

**Fix:**
```bash
# Test credentials
aws s3 ls s3://gspot-tiles --endpoint-url $R2_ENDPOINT

# For large files, use multipart
python3 scripts/upload_to_r2_boto3.py --multipart large_file.pmtiles
```

---

## Related Documentation

- [DATA_INVENTORY.md](DATA_INVENTORY.md) - Complete list of what we have
- [DATA_GAPS.md](DATA_GAPS.md) - What's missing and how to get it
- [CLAUDE.md](../CLAUDE.md) - AI assistant context
- [data_sources_registry.json](../data-pipeline/data/data_sources_registry.json) - All known sources

---

## Getting Help

- **Issues:** https://github.com/your-org/hitd-maps/issues
- **Internal:** Check `docs/` folder for detailed guides
- **AI Assistance:** See `CLAUDE.md` for context to provide to Claude
