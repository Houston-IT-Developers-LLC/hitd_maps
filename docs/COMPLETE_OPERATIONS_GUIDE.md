# HITD Maps - Complete Operations Guide

**Purpose**: This document contains EVERYTHING needed to autonomously scrape, process, upload, and manage parcel data for HITD Maps.

**Package**: hitd_maps (Houston IT Developers LLC)
**Last Updated**: 2026-01-15
**Server**: Exxact 512GB RAM / 48 CPU cores

---

## Quick Start

```bash
# One-command setup
cd /home/exx/Documents/C/hitd_maps/data-pipeline
./scripts/setup_environment.sh

# Check status
make status

# Run full update
make update

# Or start autonomous agent
make agent
```

---

## Table of Contents

1. [System Dependencies](#1-system-dependencies)
2. [Environment Setup](#2-environment-setup)
3. [Credentials & Configuration](#3-credentials--configuration)
4. [Complete Pipeline Workflow](#4-complete-pipeline-workflow)
5. [Step-by-Step Operations](#5-step-by-step-operations)
6. [Coordinate System Handling](#6-coordinate-system-handling)
7. [Known Issues & Fixes](#7-known-issues--fixes)
8. [Continuous Operation Mode](#8-continuous-operation-mode)
9. [R2 Upload & Cleanup](#9-r2-upload--cleanup)
10. [Verification & Testing](#10-verification--testing)
11. [Makefile Reference](#11-makefile-reference)

---

## 1. System Dependencies

### Required System Packages

```bash
# Install all dependencies
sudo apt-get update
sudo apt-get install -y \
    gdal-bin \
    python3 \
    python3-pip \
    python3-venv \
    jq \
    curl \
    git

# Install Tippecanoe (vector tile generator)
git clone https://github.com/felt/tippecanoe.git
cd tippecanoe
make -j$(nproc)
sudo make install
cd ..
rm -rf tippecanoe

# Verify installations
ogr2ogr --version      # GDAL 3.x+
tippecanoe --version   # Tippecanoe 2.x+
python3 --version      # Python 3.8+
```

### Python Dependencies

```bash
cd /home/exx/Documents/C/hitd_maps/data-pipeline

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install boto3 aiohttp requests

# For the autonomous agent
pip install sqlite3  # Usually built-in
```

### Version Requirements

| Tool | Minimum Version | Purpose |
|------|-----------------|---------|
| GDAL | 3.0+ | Coordinate reprojection (ogr2ogr) |
| Tippecanoe | 2.0+ | GeoJSON to PMTiles conversion |
| Python | 3.8+ | Scraping scripts |
| boto3 | 1.20+ | R2/S3 uploads |
| aiohttp | 3.8+ | Async HTTP for agent |

---

## 2. Environment Setup

### Directory Structure

```
/home/exx/Documents/C/hitd_maps/data-pipeline/
├── scripts/                    # All processing scripts
│   ├── export_county_parcels.py    # Main scraper (200+ county configs)
│   ├── reproject_to_wgs84.sh       # Coordinate reprojection
│   ├── generate_pmtiles.sh         # Tile generation
│   ├── check_coordinates.sh        # Coordinate validation
│   ├── fix_harris_coords.py        # Harris County fix
│   ├── upload_to_r2_boto3.py       # R2 upload
│   └── parallel_process_upload.py  # Full pipeline (reproject+tile+upload+cleanup)
├── output/
│   ├── geojson/                # Raw scraped data
│   │   ├── counties/           # Per-county files
│   │   └── reprojected/        # After coordinate fix
│   └── pmtiles/                # Generated tiles
├── logs/                       # Processing logs
├── agent/                      # Autonomous agent
│   ├── data_agent.py           # Main agent script
│   ├── agent_state.db          # SQLite state tracking
│   └── KNOWLEDGE_BASE.md       # AI context document
├── docs/                       # Documentation
└── config/                     # JSON configurations
```

### Environment Variables

Create `/home/exx/Documents/C/hitd_maps/data-pipeline/.env`:

```bash
# Cloudflare R2 Credentials
R2_ACCESS_KEY=ecd653afe3300fdc045b9980df0dbb14
R2_SECRET_KEY=c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35
R2_BUCKET=gspot-tiles
R2_ENDPOINT=https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev

# Ollama (for AI agent)
OLLAMA_BASE=http://10.8.0.1:11434
OLLAMA_MODEL=qwen2.5:72b

# Processing settings
PARALLEL_JOBS=8
MAX_WORKERS=4
```

Load environment:

```bash
source /home/exx/Documents/C/hitd_maps/data-pipeline/.env
export R2_ACCESS_KEY R2_SECRET_KEY R2_BUCKET R2_ENDPOINT R2_PUBLIC_URL
```

---

## 3. Credentials & Configuration

### Cloudflare R2 (PRODUCTION)

```python
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
```

### R2 Directory Structure

```
gspot-tiles/
├── parcels/                    # Parcel PMTiles
│   ├── parcels_tx_harris.pmtiles
│   ├── parcels_tx_dallas.pmtiles
│   └── ...
├── enrichment/                 # Additional layers
│   ├── pad_us/                 # Public lands
│   ├── wma/                    # Wildlife Management Areas
│   └── nwi/                    # Wetlands
├── basemap/
│   └── basemap.pmtiles
└── fonts/                      # Map fonts
```

### Ollama Server

```bash
OLLAMA_HOST=10.8.0.1:11434

# Available models
qwen2.5:72b      # Best for function calling/agents
llama3.3:70b     # General chat
deepseek-r1:671b # Deep reasoning

# Test connection
curl http://10.8.0.1:11434/api/tags
```

---

## 4. Complete Pipeline Workflow

### Visual Pipeline Flow

```
                        SCRAPE
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ArcGIS REST API  ─────►  export_county_parcels.py                   │
│  (County GIS)              │                                         │
│                            ▼                                         │
│                    output/geojson/counties/*.geojson                 │
└──────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
                   CHECK COORDINATES
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│  check_coordinates.sh  ────►  Python coordinate check                │
│                               │                                      │
│  If |X| > 180 or |Y| > 90:   Need reprojection (projected CRS)      │
│  If |X| <= 180 and |Y| <= 90: Already WGS84 (ready)                 │
└──────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
               REPROJECT (if needed)
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│  reproject_to_wgs84.sh  ────►  ogr2ogr                               │
│                                │                                     │
│  ogr2ogr -f GeoJSON \                                                │
│    -s_srs EPSG:3857 \          # Source: Web Mercator               │
│    -t_srs EPSG:4326 \          # Target: WGS84                      │
│    output_wgs84.geojson \                                           │
│    input.geojson                                                     │
└──────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
               GENERATE PMTILES
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│  generate_pmtiles.sh  ────►  tippecanoe                              │
│                              │                                       │
│  tippecanoe \                                                        │
│    -zg \                       # Auto-select max zoom               │
│    --drop-densest-as-needed \  # Simplify at low zooms              │
│    --extend-zooms-if-still-dropping \                               │
│    --no-tile-compression \     # Required for PMTiles               │
│    -o output.pmtiles \                                              │
│    input.geojson                                                     │
└──────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
               UPLOAD TO R2
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│  upload_to_r2_boto3.py  ────►  boto3 S3 client                       │
│                                │                                     │
│  s3_client.upload_file(                                              │
│      pmtiles_path,                                                   │
│      'gspot-tiles',                                                  │
│      f'parcels/{filename}.pmtiles'                                   │
│  )                                                                   │
└──────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
               CLEANUP LOCAL FILES
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Delete after successful upload:                                     │
│  - Original GeoJSON (output/geojson/counties/*.geojson)             │
│  - Reprojected GeoJSON (output/geojson/reprojected/*.geojson)       │
│  - PMTiles (output/pmtiles/*.pmtiles)                                │
│                                                                      │
│  Keep: R2 upload is the permanent storage                            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. Step-by-Step Operations

### Operation 1: Scrape a Single County

```bash
cd /home/exx/Documents/C/hitd_maps/data-pipeline

# List available counties
python3 scripts/export_county_parcels.py --list

# Scrape specific county
python3 scripts/export_county_parcels.py --county TX_HARRIS

# Output: output/geojson/counties/parcels_tx_harris.geojson
```

### Operation 2: Scrape an Entire State

```bash
# Scrape all counties for a state
python3 scripts/export_county_parcels.py --state TX

# Output: Multiple files in output/geojson/counties/
```

### Operation 3: Check Coordinate System

```bash
# Check if files need reprojection
./scripts/check_coordinates.sh

# Output:
# ✓ WGS84 (ready): 45
# ⚠️  Needs reprojection: 12
# ❌ Errors/empty: 2
```

### Operation 4: Reproject to WGS84

```bash
# Reproject all files that need it
./scripts/reproject_to_wgs84.sh

# What it does:
# 1. Backs up original to output/geojson_projected/
# 2. Runs: ogr2ogr -f GeoJSON -s_srs EPSG:3857 -t_srs EPSG:4326 output.geojson input.geojson
# 3. Validates output coordinates are in WGS84 range
```

### Operation 5: Generate PMTiles

```bash
# Generate tiles for all GeoJSON files
./scripts/generate_pmtiles.sh

# Or single file:
tippecanoe \
  -zg \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --no-tile-compression \
  -o output/pmtiles/parcels_tx_harris.pmtiles \
  output/geojson/counties/parcels_tx_harris.geojson
```

### Operation 6: Upload to R2

```bash
# Upload all PMTiles
python3 scripts/upload_pmtiles_to_r2.py

# Upload with deletion after success
python3 scripts/upload_to_r2_boto3.py --delete

# List R2 contents
python3 scripts/upload_to_r2_boto3.py --list
```

### Operation 7: Full Pipeline (Automated)

```bash
# Run the complete pipeline for all pending files:
# Reproject → Tile → Upload → Cleanup
python3 scripts/parallel_process_upload.py 4  # 4 workers

# This script:
# 1. Finds all GeoJSON files
# 2. Checks if reprojection needed
# 3. Reprojects with ogr2ogr
# 4. Converts to PMTiles with tippecanoe
# 5. Uploads to R2
# 6. Deletes local files after successful upload
# 7. Updates PARCEL_DATA_MANIFEST.json
```

---

## 6. Coordinate System Handling

### Understanding Coordinate Systems

| CRS | EPSG | X Range | Y Range | Common Sources |
|-----|------|---------|---------|----------------|
| WGS84 | 4326 | -180 to 180 | -90 to 90 | GPS, Web maps |
| Web Mercator | 3857 | -20M to 20M | -20M to 20M | ArcGIS exports |
| State Plane | Varies | Large values | Large values | County GIS |

### Detection Logic

```python
def needs_reprojection(geojson_path):
    """Check first coordinate to detect CRS."""
    with open(geojson_path) as f:
        data = json.load(f)
        coord = data['features'][0]['geometry']['coordinates'][0][0]

        # WGS84 check
        if abs(coord[0]) <= 180 and abs(coord[1]) <= 90:
            return False  # Already WGS84
        else:
            return True   # Needs reprojection
```

### Reprojection Command

```bash
# Web Mercator (EPSG:3857) to WGS84 (EPSG:4326)
ogr2ogr -f GeoJSON \
    -s_srs EPSG:3857 \
    -t_srs EPSG:4326 \
    output_wgs84.geojson \
    input.geojson

# Auto-detect source CRS (if embedded in file)
ogr2ogr -f GeoJSON \
    -t_srs EPSG:4326 \
    output_wgs84.geojson \
    input.geojson
```

---

## 7. Known Issues & Fixes

### Issue 1: Harris County Coordinate Shift

**Problem**: Harris County TX data has coordinates in format `[lat, lng+172.5]` instead of `[lng, lat]`.

**Detection**:
```
Coordinates look like: [29.7604, 77.1302]
Should be: [-95.3698, 29.7604]
```

**Fix**:
```bash
python3 scripts/fix_harris_coords.py \
    input.geojson \
    output_fixed.geojson
```

**Fix Logic**:
```python
def fix_coord_pair(coord):
    val1, val2 = coord[0], coord[1]
    # If val1 is latitude (25-32) and val2 is shifted longitude (74-80)
    if 25 < val1 < 32 and 74 < val2 < 80:
        lng_fixed = val2 - 172.5  # Unshift longitude
        lat = val1
        return [lng_fixed, lat]  # Return as [lng, lat]
    return coord
```

### Issue 2: Tippecanoe "Can't Guess Maxzoom"

**Problem**: Small datasets fail with "can't guess maxzoom" error.

**Fix**: Use explicit zoom level instead of `-zg`:
```bash
tippecanoe \
    -z14 \                          # Fixed max zoom
    --minimum-zoom=10 \             # Fixed min zoom
    --drop-densest-as-needed \
    -o output.pmtiles \
    input.geojson
```

### Issue 3: SSL Certificate Errors

**Problem**: Some county APIs have SSL certificate issues.

**Fix**: Use the SSL-fixed scraper:
```bash
python3 scripts/export_county_parcels_ssl_fix.py --county PROBLEMATIC_COUNTY
```

Or disable SSL verification (not recommended for production):
```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

### Issue 4: Memory Exhaustion on Large Files

**Problem**: Files >5GB cause memory issues during PMTiles generation.

**Fix**: Use tippecanoe's streaming mode:
```bash
tippecanoe \
    -z14 \
    --no-feature-limit \
    --no-tile-size-limit \
    --drop-densest-as-needed \
    -o output.pmtiles \
    input.geojson
```

Or split large files first:
```bash
# Split by feature count
ogr2ogr -f GeoJSON -limit 1000000 output_part1.geojson input.geojson
```

### Issue 5: Empty or Corrupt GeoJSON

**Problem**: Some scrapes produce empty or invalid GeoJSON.

**Detection**:
```bash
./scripts/check_coordinates.sh
# Shows: ❌ filename.geojson - EMPTY or NO_GEOM
```

**Fix**: Delete and re-scrape:
```bash
rm output/geojson/counties/parcels_COUNTY.geojson
python3 scripts/export_county_parcels.py --county STATE_COUNTY
```

---

## 8. Continuous Operation Mode

### Start Autonomous Agent

```bash
cd /home/exx/Documents/C/hitd_maps/data-pipeline

# Activate virtual environment
source venv/bin/activate

# Run once (for testing)
python3 agent/data_agent.py --once

# Run continuously (every 6 hours)
python3 agent/data_agent.py --interval 360

# Check specific API
python3 agent/data_agent.py --check-api tx_statewide
```

### What the Agent Does

1. **Every 6 hours**: Checks all monitored APIs for record count changes
2. **If data changed >0.1%**: Asks Ollama LLM if re-scrape is needed
3. **If LLM says yes**: Queues scrape job with priority
4. **Runs scrape**: Executes export_county_parcels.py
5. **Processes output**: Reproject → PMTiles → Upload → Cleanup
6. **Updates docs**: Writes to DATA_FRESHNESS.md

### Run as Systemd Service

Create `/etc/systemd/system/data-agent.service`:

```ini
[Unit]
Description=HITD Maps Data Agent
After=network.target

[Service]
Type=simple
User=exx
WorkingDirectory=/home/exx/Documents/C/hitd_maps/data-pipeline
ExecStart=/home/exx/Documents/C/hitd_maps/data-pipeline/venv/bin/python3 agent/data_agent.py --interval 360
Restart=always
RestartSec=60
Environment="OLLAMA_BASE=http://10.8.0.1:11434"

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable data-agent
sudo systemctl start data-agent
sudo systemctl status data-agent
```

### Monitored APIs

| Source ID | State | Expected Records | API URL |
|-----------|-------|------------------|---------|
| tx_statewide | TX | 28,000,000 | feature.stratmap.tnris.org |
| fl_statewide | FL | 10,000,000 | ca.dep.state.fl.us/arcgis |
| ny_statewide | NY | 9,000,000 | services6.arcgis.com |
| oh_statewide | OH | 5,500,000 | gis.ohiosos.gov |
| ca_la_county | CA | 2,500,000 | public.gis.lacounty.gov |

---

## 9. R2 Upload & Cleanup

### Upload with Automatic Cleanup

```python
#!/usr/bin/env python3
"""Upload PMTiles to R2 and delete local files after success."""

import boto3
import os
from pathlib import Path

R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

def upload_and_cleanup(local_path, r2_key, delete_local=True):
    """Upload file to R2 and delete local copy on success."""
    client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
    )

    # Upload
    client.upload_file(str(local_path), R2_BUCKET, r2_key)
    print(f"Uploaded: {r2_key}")

    # Verify upload
    response = client.head_object(Bucket=R2_BUCKET, Key=r2_key)
    remote_size = response['ContentLength']
    local_size = os.path.getsize(local_path)

    if remote_size == local_size:
        if delete_local:
            os.remove(local_path)
            print(f"Deleted local: {local_path}")
        return True
    else:
        print(f"Size mismatch! Local: {local_size}, Remote: {remote_size}")
        return False
```

### Cleanup Strategy

**After successful R2 upload, delete**:
1. Original GeoJSON (`output/geojson/counties/*.geojson`)
2. Reprojected GeoJSON (`output/geojson/reprojected/*.geojson`)
3. PMTiles (`output/pmtiles/*.pmtiles`)
4. Backup projected files (`output/geojson_projected/*.geojson`)

**Keep permanently**:
- Processing logs (`logs/*.log`)
- Manifest file (`docs/PARCEL_DATA_MANIFEST.json`)
- Agent state database (`agent/agent_state.db`)

### Verify R2 Contents

```bash
# List all parcels in R2
python3 -c "
import boto3
client = boto3.client('s3',
    endpoint_url='https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com',
    aws_access_key_id='ecd653afe3300fdc045b9980df0dbb14',
    aws_secret_access_key='c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35',
)
response = client.list_objects_v2(Bucket='gspot-tiles', Prefix='parcels/')
for obj in response.get('Contents', []):
    print(f\"{obj['Key']} - {obj['Size']/1024/1024:.1f}MB\")
"
```

---

## 10. Verification & Testing

### Test 1: Check GDAL Installation

```bash
ogr2ogr --version
# Expected: GDAL 3.x.x, released YYYY/MM/DD
```

### Test 2: Check Tippecanoe Installation

```bash
tippecanoe --version
# Expected: tippecanoe v2.x.x
```

### Test 3: Test R2 Connection

```bash
python3 -c "
import boto3
client = boto3.client('s3',
    endpoint_url='https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com',
    aws_access_key_id='ecd653afe3300fdc045b9980df0dbb14',
    aws_secret_access_key='c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35',
)
response = client.list_objects_v2(Bucket='gspot-tiles', MaxKeys=1)
print('R2 connection: SUCCESS')
"
```

### Test 4: Test Ollama Connection

```bash
curl -s http://10.8.0.1:11434/api/tags | jq '.models[].name'
```

### Test 5: Run Mini Pipeline Test

```bash
cd /home/exx/Documents/C/hitd_maps/data-pipeline

# Scrape a small county
python3 scripts/export_county_parcels.py --county TX_LOVING  # Tiny county

# Check coordinates
./scripts/check_coordinates.sh

# Process
python3 scripts/parallel_process_upload.py 1
```

### Test 6: Verify Uploaded Tiles

```bash
# Test tile accessibility
curl -I "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_tx_harris.pmtiles"
# Expected: HTTP/2 200
```

---

## Quick Reference Commands

```bash
# ==== SCRAPING ====
python3 scripts/export_county_parcels.py --state TX
python3 scripts/export_county_parcels.py --county TX_HARRIS
python3 scripts/export_county_parcels.py --list

# ==== COORDINATE CHECK ====
./scripts/check_coordinates.sh

# ==== REPROJECT ====
./scripts/reproject_to_wgs84.sh

# ==== GENERATE TILES ====
./scripts/generate_pmtiles.sh

# ==== UPLOAD ====
python3 scripts/upload_to_r2_boto3.py --delete

# ==== FULL PIPELINE ====
python3 scripts/parallel_process_upload.py 4

# ==== AGENT ====
python3 agent/data_agent.py --once
python3 agent/data_agent.py --interval 360

# ==== R2 LIST ====
python3 scripts/upload_to_r2_boto3.py --list
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ogr2ogr: command not found` | GDAL not installed | `sudo apt install gdal-bin` |
| `tippecanoe: command not found` | Tippecanoe not installed | See Section 1 |
| `can't guess maxzoom` | Small dataset | Use `-z14` instead of `-zg` |
| Coordinates way off | Wrong CRS | Run `./scripts/reproject_to_wgs84.sh` |
| Harris County wrong location | Coordinate shift issue | Run `fix_harris_coords.py` |
| R2 upload fails | Credentials wrong | Check .env file |
| Agent not connecting to Ollama | Network issue | Check `curl http://10.8.0.1:11434/api/tags` |

---

## 11. Makefile Reference

The data-pipeline includes a Makefile for common operations:

```bash
cd /home/exx/Documents/C/hitd_maps/data-pipeline

# Setup
make setup          # Full server setup
make setup-dev      # Development setup (lighter)

# Operations
make status         # Show pipeline status
make update         # Run full update (scrape + pipeline)
make pipeline       # Process existing files only
make cleanup        # Remove uploaded local files
make docs           # Update documentation

# Agent
make agent          # Start autonomous agent (6hr interval)
make agent-once     # Run one monitoring cycle

# Scraping
make scrape STATE=TX             # Scrape Texas
make scrape STATE=CA COUNTY=LA   # Scrape LA County, CA

# Testing
make test           # Run all tests
make check-api      # Check all monitored APIs

# Service
make install-service  # Install systemd service
make logs             # View agent logs

# R2
make r2-inventory     # List R2 bucket contents
```

### Environment Variables

Set these before running make commands:

```bash
export WORKERS=4      # Number of parallel workers
export INTERVAL=360   # Agent check interval (minutes)
```

---

*This document is the SINGLE SOURCE OF TRUTH for all HITD Maps data pipeline operations.*
*Package: hitd_maps by Houston IT Developers LLC*
*Updated: 2026-01-15*
