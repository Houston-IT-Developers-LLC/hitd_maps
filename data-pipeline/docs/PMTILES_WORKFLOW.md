# PMTiles Generation & R2 Upload Workflow

## Overview

We store **both GeoJSON and PMTiles** on Cloudflare R2:

| Format | Purpose | R2 Path |
|--------|---------|---------|
| **GeoJSON** | Source/backup - regenerate tiles if needed | `geojson/*.geojson` |
| **PMTiles** | Production - Flutter app renders these | `pmtiles/*.pmtiles` |

### Why Keep Both?

- **GeoJSON** is the source of truth
  - Human-readable, easy to debug
  - Can regenerate PMTiles with different settings (zoom levels, simplification)
  - Share raw data if needed
  - Edit/update data when sources change

- **PMTiles** is the optimized delivery format
  - Fast tile serving at any zoom level
  - Compressed for web delivery
  - What the Flutter app actually fetches

Storage is cheap on R2 (no egress fees!) - keeping both is negligible cost.

---

## ⚠️ IMPORTANT: Coordinate System Requirement

**Tippecanoe requires WGS84 coordinates (EPSG:4326)** - standard lat/lng values in the range:
- Longitude: -180 to 180
- Latitude: -90 to 90

Many parcel data sources use **projected coordinate systems** (State Plane, UTM, Web Mercator) with coordinates like `3154733.9, 13922510.6` (feet/meters). These **MUST be reprojected to WGS84** before tippecanoe can generate valid tiles.

### How to Check Coordinate System

```bash
# Check first feature's coordinates
python3 -c "
import json
with open('output/geojson/YOUR_FILE.geojson') as f:
    data = json.load(f)
    coords = data['features'][0]['geometry']['coordinates'][0][0]
    print(f'First coordinate: {coords}')
    if abs(coords[0]) > 180 or abs(coords[1]) > 90:
        print('⚠️  NOT WGS84 - needs reprojection!')
    else:
        print('✓ Appears to be WGS84')
"
```

### Reprojecting to WGS84

Use GDAL's ogr2ogr to reproject:

```bash
# Install GDAL
sudo apt-get install -y gdal-bin

# Reproject single file (auto-detect source CRS from .prj or assume Web Mercator)
ogr2ogr -f GeoJSON -t_srs EPSG:4326 output_wgs84.geojson input.geojson

# If source CRS is known (e.g., Texas State Plane South Central EPSG:2278)
ogr2ogr -f GeoJSON -s_srs EPSG:2278 -t_srs EPSG:4326 output_wgs84.geojson input.geojson

# Batch reproject all files
./scripts/reproject_to_wgs84.sh
```

---

## Complete Data Pipeline

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────┐
│  Raw Data       │────▶│  Reproject to    │────▶│  Generate       │────▶│  Upload to  │
│  (Various CRS)  │     │  WGS84 (GDAL)    │     │  PMTiles        │     │  R2         │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────┘
        │                       │                        │                      │
   output/raw/           output/geojson/          output/pmtiles/        R2 bucket
   (original)            (WGS84)                  (tiles)                (CDN)
```

### Step-by-Step Process

1. **Scrape/Download Raw Data** → `output/raw/` or `output/geojson/`
2. **Check Coordinate System** → Run coordinate check script
3. **Reproject if Needed** → `./scripts/reproject_to_wgs84.sh`
4. **Generate PMTiles** → `./scripts/parallel_pmtiles.sh`
5. **Upload to R2** → `python3 scripts/upload_all_to_r2.py`

---

## Quick Start

### 1. Reproject GeoJSON to WGS84 (if needed)

```bash
cd data-pipeline

# Check if files need reprojection
./scripts/check_coordinates.sh

# Reproject all files that need it
./scripts/reproject_to_wgs84.sh
```

### 2. Generate PMTiles from GeoJSON

```bash
# Generate all PMTiles in parallel (skips existing)
PARALLEL_JOBS=12 ./scripts/parallel_pmtiles.sh

# Or single file
./scripts/generate_pmtiles.sh

# Check output
ls -lh output/pmtiles/
```

### 3. Upload Both to R2

```bash
# Upload everything (GeoJSON + PMTiles)
python3 scripts/upload_all_to_r2.py

# Upload only new files (skip existing in R2)
python3 scripts/upload_all_to_r2.py --skip-existing

# Preview what would be uploaded
python3 scripts/upload_all_to_r2.py --dry-run

# Upload only PMTiles
python3 scripts/upload_all_to_r2.py --pmtiles-only

# Upload only GeoJSON
python3 scripts/upload_all_to_r2.py --geojson-only
```

### 4. List R2 Contents

```bash
python3 scripts/upload_all_to_r2.py --list
```

---

## Directory Structure

### Local

```
data-pipeline/
├── output/
│   ├── raw/               # Original data (may be projected CRS)
│   ├── geojson/           # WGS84 GeoJSON files (source of truth)
│   │   ├── parcels_tx_harris.geojson
│   │   ├── parcels_ca_los_angeles.geojson
│   │   └── ...
│   └── pmtiles/           # Generated PMTiles
│       ├── parcels_tx_harris.pmtiles
│       ├── parcels_ca_los_angeles.pmtiles
│       └── ...
├── scripts/
│   ├── parallel_pmtiles.sh      # Parallel GeoJSON -> PMTiles
│   ├── generate_pmtiles.sh      # Single-threaded version
│   ├── reproject_to_wgs84.sh    # CRS reprojection
│   ├── check_coordinates.sh     # Verify coordinate system
│   ├── upload_all_to_r2.py      # Upload both formats
│   └── retry_failed_pmtiles.sh  # Retry failed conversions
├── logs/
│   └── *.log                    # Per-file conversion logs
└── docs/
    ├── PMTILES_WORKFLOW.md      # This file
    └── SERVER_HANDOFF.md        # Deployment docs
```

### R2 Bucket (`gspot-tiles`)

```
gspot-tiles/
├── geojson/               # Backup/source files (WGS84)
│   ├── parcels_tx_harris.geojson
│   └── ...
├── pmtiles/               # Production tiles
│   ├── parcels_tx_harris.pmtiles
│   └── ...
└── parcels/               # Legacy (old uploads, will deprecate)
```

---

## Public URLs

| Format | Base URL |
|--------|----------|
| GeoJSON | `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/geojson/` |
| PMTiles | `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/pmtiles/` |

Example URLs:
- GeoJSON: `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/geojson/parcels_tx_harris.geojson`
- PMTiles: `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/pmtiles/parcels_tx_harris.pmtiles`

---

## Flutter App Integration

```dart
// Use PMTiles in MapLibre
final pmtilesUrl = 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/pmtiles/parcels_tx_harris.pmtiles';
```

---

## Tippecanoe Options

The `parallel_pmtiles.sh` script uses these tippecanoe settings:

| Option | Purpose |
|--------|---------|
| `-z14` | Fixed max zoom level 14 (reliable, avoids -zg errors) |
| `--drop-densest-as-needed` | Drop features in dense areas at low zoom |
| `--extend-zooms-if-still-dropping` | Extend zoom if still dropping features |

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "Can't guess maxzoom (-zg)" | Features all in same location or projected CRS | Use `-z14` instead of `-zg`, or reproject to WGS84 |
| "0 bytes of vertices" | Coordinates outside WGS84 range | Reproject GeoJSON to EPSG:4326 |
| 32KB output files | Failed conversion (empty tiles) | Check logs, fix CRS, regenerate |

### Customizing Tile Generation

```bash
# Fixed zoom range (z0-z14)
tippecanoe -z14 -o output.pmtiles input.geojson

# Keep all features (no dropping) - WARNING: large files
tippecanoe -z14 --no-feature-limit --no-tile-size-limit -o output.pmtiles input.geojson

# Simplify geometry at low zooms
tippecanoe -z14 --simplification=10 -o output.pmtiles input.geojson

# Include specific properties only
tippecanoe -z14 -y property1 -y property2 -o output.pmtiles input.geojson
```

---

## Workflow Scenarios

### Adding New Data

1. Download/scrape new GeoJSON to `output/raw/` or `output/geojson/`
2. Check coordinate system: `./scripts/check_coordinates.sh`
3. Reproject if needed: `./scripts/reproject_to_wgs84.sh`
4. Generate PMTiles: `./scripts/parallel_pmtiles.sh` (auto-skips existing)
5. Upload: `python3 scripts/upload_all_to_r2.py --skip-existing`

### Updating Existing Data

1. Replace GeoJSON file in `output/geojson/`
2. Delete old PMTiles: `rm output/pmtiles/parcels_xyz.pmtiles`
3. Regenerate: `./scripts/parallel_pmtiles.sh`
4. Upload: `python3 scripts/upload_all_to_r2.py`

### Regenerating Tiles with New Settings

1. Delete the PMTiles file: `rm output/pmtiles/parcels_xyz.pmtiles`
2. Edit script with new tippecanoe options
3. Run `./scripts/parallel_pmtiles.sh`
4. Upload: `python3 scripts/upload_all_to_r2.py --pmtiles-only`

### Recovering from R2

If local files are lost, download from R2:

```bash
# Configure AWS CLI for R2
export AWS_ACCESS_KEY_ID="ecd653afe3300fdc045b9980df0dbb14"
export AWS_SECRET_ACCESS_KEY="c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# Download all GeoJSON
aws s3 sync s3://gspot-tiles/geojson/ output/geojson/ \
  --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com

# Download all PMTiles
aws s3 sync s3://gspot-tiles/pmtiles/ output/pmtiles/ \
  --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com
```

---

## Requirements

- **tippecanoe** v2.x+ (for PMTiles generation)
- **GDAL** (for coordinate reprojection)
- **Python 3** with `boto3` (for R2 uploads)
- **AWS CLI** (optional, for manual operations)

### Install Dependencies

```bash
# tippecanoe (build from source)
sudo apt-get install -y libsqlite3-dev zlib1g-dev
git clone https://github.com/felt/tippecanoe.git /tmp/tippecanoe
cd /tmp/tippecanoe && make -j && sudo make install

# GDAL for reprojection
sudo apt-get install -y gdal-bin

# Python boto3
pip install boto3

# Verify installations
tippecanoe --version
ogr2ogr --version
python3 -c "import boto3; print('boto3 OK')"
```

---

## Troubleshooting

### Check PMTiles file validity

```bash
# Should show metadata and tile counts
pmtiles show output/pmtiles/parcels_tx_harris.pmtiles

# If file is ~32KB and shows minimal data, it's likely a CRS issue
ls -la output/pmtiles/*.pmtiles | awk '$5 < 50000 {print $9 " - POSSIBLY INVALID"}'
```

### Check conversion logs

```bash
# View specific file's conversion log
cat logs/parcels_tx_harris.log

# Find failed conversions
grep -l "Can't guess maxzoom" logs/*.log
```

### Verify GeoJSON coordinates

```bash
# Quick coordinate check for all files
for f in output/geojson/*.geojson; do
  coords=$(python3 -c "import json; d=json.load(open('$f')); print(d['features'][0]['geometry']['coordinates'][0][0])" 2>/dev/null)
  echo "$f: $coords"
done | head -20
```
