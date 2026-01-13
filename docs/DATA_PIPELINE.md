# Data Pipeline Documentation

This document explains how map data flows from source to the user's device, and how to maintain and update the data.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Sources](#data-sources)
3. [Processing Pipeline](#processing-pipeline)
4. [Tile Generation](#tile-generation)
5. [Hosting & CDN](#hosting--cdn)
6. [Update Schedule](#update-schedule)
7. [Step-by-Step Procedures](#step-by-step-procedures)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA PIPELINE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   DATA SOURCES                    PROCESSING                    DELIVERY    │
│   ───────────                    ──────────                    ────────    │
│                                                                              │
│   ┌─────────────┐               ┌─────────────┐              ┌──────────┐  │
│   │ County GIS  │──┐            │   ogr2ogr   │              │          │  │
│   │  (Parcels)  │  │            │ (Reproject) │              │ Cloudflare│  │
│   └─────────────┘  │            └──────┬──────┘              │    R2    │  │
│                    │                   │                      │   CDN    │  │
│   ┌─────────────┐  │  ┌─────────┐     │     ┌───────────┐   │          │  │
│   │   PAD-US    │──┼─>│ GeoJSON │─────┼────>│Tippecanoe │──>│ PMTiles  │  │
│   │(Public Land)│  │  │  Files  │     │     │(Tile Gen) │   │  Files   │  │
│   └─────────────┘  │  └─────────┘     │     └───────────┘   │          │  │
│                    │                   │                      └────┬─────┘  │
│   ┌─────────────┐  │            ┌──────┴──────┐                   │        │
│   │ Open-Meteo  │──┘            │   Merge &   │                   │        │
│   │  (Weather)  │               │  Simplify   │                   ▼        │
│   └─────────────┘               └─────────────┘              ┌──────────┐  │
│                                                              │  Mobile  │  │
│   ┌─────────────┐                                            │   App    │  │
│   │ State WMA   │─────────────────────────────────────────>  │(MapLibre)│  │
│   │   Data      │                                            └──────────┘  │
│   └─────────────┘                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Sources

### 1. Parcel Data (Property Boundaries)

| Attribute | Details |
|-----------|---------|
| **Source** | County GIS departments, state GIS portals |
| **Format** | Shapefile, GeoJSON, GDB |
| **Update Frequency** | Varies by county (monthly to annually) |
| **Coverage** | Currently 12+ states, expanding to 50 |
| **Size** | ~80GB raw data (all states) |

**Key Fields:**
- `owner_name` - Property owner
- `situs_addr` - Property address
- `acreage` / `acres` - Lot size
- `total_market_val` - Assessed value
- `county` - County name

### 2. Public Lands (PAD-US)

| Attribute | Details |
|-----------|---------|
| **Source** | USGS Gap Analysis Project |
| **URL** | https://www.usgs.gov/programs/gap-analysis-project |
| **API** | USFS EDW ArcGIS REST API |
| **Update Frequency** | Annual (October) |
| **Coverage** | Nationwide |
| **License** | Public domain |

**Key Fields:**
- `Unit_Nm` - Protected area name
- `Des_Tp` - Designation type (National Forest, BLM, etc.)
- `Mang_Name` - Managing agency
- `GAP_Sts` - Protection level (1-4)
- `Pub_Access` - Public access level

### 3. Weather Data (Open-Meteo)

| Attribute | Details |
|-----------|---------|
| **Source** | Open-Meteo API |
| **URL** | https://api.open-meteo.com |
| **Cost** | FREE (no API key required) |
| **Update Frequency** | Real-time (hourly forecasts) |
| **Data** | Wind speed, direction, gusts |

### 4. State Wildlife Management Areas

| Attribute | Details |
|-----------|---------|
| **Source** | State fish & game departments |
| **Format** | Varies by state (KML, Shapefile, GeoJSON) |
| **Update Frequency** | Annual |
| **Coverage** | State-by-state |

---

## Processing Pipeline

### Step 1: Data Acquisition

```bash
# Parcel data - run scraper for each state
cd data-pipeline
python3 scripts/scrape_parcels.py --state TX

# PAD-US public lands
python3 scripts/enrichment/download_pad_us.py --state TX

# State WMA data
python3 scripts/enrichment/download_state_wma.py --state TX
```

### Step 2: Coordinate Reprojection

All data must be converted to WGS84 (EPSG:4326) for web mapping:

```bash
# Single file
ogr2ogr -f GeoJSON -t_srs EPSG:4326 output.geojson input.shp

# Batch process all files
./scripts/reproject_to_wgs84.sh
```

### Step 3: Data Validation

```bash
# Check coordinates are valid WGS84
./scripts/check_coordinates.sh output/geojson/

# Verify field names
ogrinfo -al -so output.geojson | head -50
```

### Step 4: Merge & Simplify (Optional)

For large datasets, simplify geometry to reduce file size:

```bash
# Simplify with tolerance (in degrees, ~100m at equator)
ogr2ogr -f GeoJSON -simplify 0.0001 simplified.geojson input.geojson
```

---

## Tile Generation

We use **Tippecanoe** to convert GeoJSON to PMTiles format.

### Installation

```bash
# Ubuntu/Debian
sudo apt-get install tippecanoe

# macOS
brew install tippecanoe

# From source
git clone https://github.com/felt/tippecanoe.git
cd tippecanoe && make -j && sudo make install
```

### Basic Tile Generation

```bash
tippecanoe \
  -z14 \                              # Max zoom level
  --drop-densest-as-needed \          # Auto-simplify at low zooms
  --extend-zooms-if-still-dropping \  # Extend zoom if needed
  -l parcels \                        # Layer name
  -o parcels_tx.pmtiles \             # Output file
  parcels_tx.geojson                  # Input file
```

### Recommended Settings by Layer Type

**Parcels (high detail):**
```bash
tippecanoe \
  -z16 \
  --minimum-zoom=10 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --detect-shared-borders \
  -l parcels \
  -o parcels_tx.pmtiles \
  parcels_tx.geojson
```

**Public Lands (medium detail):**
```bash
tippecanoe \
  -z14 \
  --minimum-zoom=6 \
  --drop-densest-as-needed \
  --coalesce-densest-as-needed \
  -l public_lands \
  -o public_lands.pmtiles \
  pad_us_*.geojson
```

**WMA Boundaries (low detail):**
```bash
tippecanoe \
  -z14 \
  --minimum-zoom=8 \
  --simplification=10 \
  -l wma \
  -o wma_tx.pmtiles \
  wma_tx.geojson
```

### Parallel Processing

For multiple states:

```bash
./scripts/parallel_pmtiles.sh
```

---

## Hosting & CDN

### Cloudflare R2 Setup

We use Cloudflare R2 for tile hosting (S3-compatible, no egress fees).

**Bucket Configuration:**
- Bucket Name: `gspot-tiles`
- Public URL: `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev`
- Region: Auto (Cloudflare edge)

**Directory Structure:**
```
gspot-tiles/
├── parcels/
│   ├── parcels_tx.pmtiles
│   ├── parcels_ca.pmtiles
│   └── ...
├── enrichment/
│   ├── pad_us/
│   │   ├── pad_us_tx.pmtiles
│   │   └── ...
│   ├── wma/
│   │   └── ...
│   └── nwi/
│       └── ...
└── basemap/
    └── basemap.pmtiles
```

### Upload Process

```bash
# Using boto3 Python script
python3 scripts/upload_to_r2_boto3.py \
  --file output/pmtiles/parcels_tx.pmtiles \
  --key parcels/parcels_tx.pmtiles

# Bulk upload all PMTiles
python3 scripts/upload_all_to_r2.py
```

### R2 Credentials

Store in environment variables (never commit to git):

```bash
export R2_ACCESS_KEY="your-access-key"
export R2_SECRET_KEY="your-secret-key"
export R2_BUCKET="gspot-tiles"
export R2_ENDPOINT="https://your-account-id.r2.cloudflarestorage.com"
```

---

## Update Schedule

### Parcel Data

| Frequency | Action | Automation |
|-----------|--------|------------|
| **Quarterly** | Re-scrape all states | Scheduled job |
| **Monthly** | Priority states (TX, CA, FL) | Manual trigger |
| **On-demand** | New state additions | Manual |

### Public Lands (PAD-US)

| Frequency | Action |
|-----------|--------|
| **Annual** (October) | Download new PAD-US release |
| **As needed** | Re-process after major federal land changes |

### Weather Data

| Frequency | Action |
|-----------|--------|
| **Real-time** | Fetched on-demand from Open-Meteo API |
| **No tile updates needed** | API handles freshness |

### Recommended Update Calendar

```
January:   Q1 parcel refresh (all states)
April:     Q2 parcel refresh + WMA boundaries update
July:      Q3 parcel refresh
October:   Q4 parcel refresh + PAD-US annual update
Monthly:   TX, CA, FL parcel refresh
```

---

## Step-by-Step Procedures

### Procedure 1: Add a New State

1. **Find data source:**
   ```bash
   # Check state GIS portal
   # Common URLs: gis.[state].gov, [state]geo.org
   ```

2. **Download parcel data:**
   ```bash
   python3 scripts/scrape_parcels.py --state [STATE_CODE]
   ```

3. **Reproject to WGS84:**
   ```bash
   ./scripts/reproject_to_wgs84.sh output/raw/[state]/
   ```

4. **Generate PMTiles:**
   ```bash
   tippecanoe -z16 --minimum-zoom=10 \
     --drop-densest-as-needed \
     -l parcels \
     -o output/pmtiles/parcels_[state].pmtiles \
     output/geojson/parcels_[state].geojson
   ```

5. **Upload to R2:**
   ```bash
   python3 scripts/upload_to_r2_boto3.py \
     --file output/pmtiles/parcels_[state].pmtiles \
     --key parcels/parcels_[state].pmtiles
   ```

6. **Update app configuration:**
   - Add state to `HitdMapController.availableStates`
   - Add state center coordinates to `_stateConfigs`

7. **Test in app:**
   ```dart
   await controller.switchState('[state]');
   ```

### Procedure 2: Update Existing State Data

1. **Backup existing tiles:**
   ```bash
   # R2 versioning handles this automatically
   ```

2. **Re-download source data:**
   ```bash
   python3 scripts/scrape_parcels.py --state TX --force
   ```

3. **Process and upload:**
   ```bash
   ./scripts/reproject_to_wgs84.sh output/raw/tx/
   tippecanoe ... -o parcels_tx.pmtiles ...
   python3 scripts/upload_to_r2_boto3.py --file parcels_tx.pmtiles ...
   ```

4. **Verify in app:**
   - Clear app cache
   - Load state and verify data appears

### Procedure 3: Update PAD-US (Annual)

1. **Check for new release:**
   - Visit: https://www.usgs.gov/programs/gap-analysis-project
   - Look for new PAD-US version (usually October)

2. **Download new data:**
   ```bash
   python3 scripts/enrichment/download_pad_us.py --all-states --force
   ```

3. **Generate tiles:**
   ```bash
   tippecanoe -z14 --minimum-zoom=6 \
     --drop-densest-as-needed \
     --coalesce-densest-as-needed \
     -l public_lands \
     -o public_lands.pmtiles \
     output/enrichment/geojson/pad_us_*.geojson
   ```

4. **Upload and verify:**
   ```bash
   python3 scripts/upload_to_r2_boto3.py \
     --file public_lands.pmtiles \
     --key enrichment/pad_us/public_lands.pmtiles
   ```

### Procedure 4: Emergency Data Fix

If bad data is uploaded:

1. **Identify the problem:**
   ```bash
   # Check tile metadata
   pmtiles show parcels_tx.pmtiles
   ```

2. **Rollback (if R2 versioning enabled):**
   ```bash
   # List versions
   aws s3api list-object-versions \
     --bucket gspot-tiles \
     --prefix parcels/parcels_tx.pmtiles

   # Restore previous version
   aws s3api copy-object \
     --bucket gspot-tiles \
     --copy-source "gspot-tiles/parcels/parcels_tx.pmtiles?versionId=PREVIOUS_VERSION_ID" \
     --key parcels/parcels_tx.pmtiles
   ```

3. **Or re-upload fixed version:**
   ```bash
   python3 scripts/upload_to_r2_boto3.py --file fixed_parcels_tx.pmtiles ...
   ```

4. **Clear CDN cache:**
   - Cloudflare Dashboard > Caching > Purge Cache
   - Or purge specific URL

---

## Monitoring & Alerts

### Data Freshness Tracking

Create a manifest file to track update dates:

```json
// tile_manifest.json
{
  "parcels": {
    "tx": {"updated": "2026-01-10", "records": 28000000},
    "ca": {"updated": "2026-01-08", "records": 15000000}
  },
  "public_lands": {
    "version": "PAD-US 4.0",
    "updated": "2025-10-15"
  }
}
```

### Health Checks

```bash
# Check if tiles are accessible
curl -I https://pub-xxx.r2.dev/parcels/parcels_tx.pmtiles

# Check tile metadata
pmtiles show https://pub-xxx.r2.dev/parcels/parcels_tx.pmtiles
```

---

## Cost Estimates

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| Cloudflare R2 Storage | ~$15/TB | ~100GB tiles = ~$1.50/mo |
| Cloudflare R2 Egress | $0 | Free egress! |
| Open-Meteo API | $0 | Free tier |
| Processing Server | $20-50 | For large tile generation |

**Total estimated monthly cost: $20-50**

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.
