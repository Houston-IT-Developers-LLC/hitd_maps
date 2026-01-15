# My G Spot Outdoors - Complete Knowledge Base

## OVERVIEW

**My G Spot Outdoors** is a real-time hunting group coordination platform that enables hunters and hunting clubs to:
- Track each other in real-time within hunting boundaries
- Auto check-in/out via geofencing
- Access comprehensive public land data for all 50 US states
- Coordinate via messaging and map markers
- Receive smart safety notifications

## TECHNOLOGY STACK

### Mobile App (Flutter)
- **Framework**: Flutter with GetX state management
- **Architecture**: MVC with modular feature organization
- **Maps**: hitd_maps package (custom wrapper around MapLibre GL)
- **Auth**: Firebase Auth (Google, Facebook, Apple, Email)
- **Real-time**: Socket.IO for live location/chat
- **Push**: Firebase Cloud Messaging (FCM)
- **Storage**: GetStorage (local), SQLite (offline location cache)

### Data Pipeline (Python)
- **Scraping**: ArcGIS REST API queries (200+ county configs)
- **Processing**: GeoJSON → GDAL Reproject → Tippecanoe → PMTiles
- **Storage**: Cloudflare R2 CDN
- **Language**: Python 3 with aiohttp, boto3, requests

### Web App (Planned)
- **Framework**: Next.js 14+ with React
- **Maps**: Google Maps JS API or Mapbox GL JS

---

## KEY DIRECTORIES

```
/home/exx/Documents/C/hitd_maps/
├── lib/                           # Flutter app source
│   ├── modules/                   # Feature modules (auth, club, chat, home, etc.)
│   ├── services/                  # API, socket, notification services
│   ├── utils/                     # Helpers, constants, colors
│   └── bindings/                  # GetX dependency injection
├── data-pipeline/                 # Data scraping & processing
│   ├── scripts/                   # Python scrapers and processors
│   │   ├── export_county_parcels.py   # Main scraper (200+ county configs)
│   │   ├── enrichment/            # PAD-US, NWI, NHD, etc. downloaders
│   │   └── upload_*.py            # R2 upload scripts
│   ├── output/                    # Scraped data (GeoJSON, PMTiles)
│   ├── docs/                      # Technical documentation
│   ├── config/                    # JSON configs for sources
│   └── agent/                     # Autonomous agent scripts
├── .planning/                     # Project planning docs
│   ├── PROJECT.md                 # Vision and goals
│   ├── ROADMAP.md                 # 26 phases with details
│   └── phases/                    # Per-phase plans and summaries
└── pubspec.yaml                   # Flutter dependencies
```

---

## CRITICAL CREDENTIALS & SECRETS

### Cloudflare R2 (Object Storage)
```
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"
```

### Google Maps API
```
Web Key: AIzaSyBV_7SXEuB-eaVC_Oi4GEp9sye4297L5ac
```

### Firebase
```
Project ID: my-g-spot-outdoors
GCM Sender ID: 237526722
Storage Bucket: my-g-spot-outdoors.firebasestorage.app
```

### Backend API
```
Production: https://api.mygspotoutdoors.com
Development: http://localhost:3017
```

---

## DATA PIPELINE DETAILS

### Main Scraper: export_county_parcels.py
- **Location**: `/data-pipeline/scripts/export_county_parcels.py`
- **Purpose**: Export parcel data from ArcGIS REST APIs
- **Counties**: 200+ configurations across all 50 states
- **Output**: GeoJSON files in `/output/geojson/{state}/`

### Key State APIs (Statewide)
| State | API | Records |
|-------|-----|---------|
| TX | TNRIS StratMap | ~28M parcels |
| NY | NYS ITS | ~9M parcels |
| MT | MSDI Framework | All counties |
| FL | DEP ArcGIS | ~10M parcels |
| OH | SOS ArcGIS | ~5.5M parcels |

### Processing Pipeline
```
1. SCRAPE: python3 export_county_parcels.py --state TX
   → Output: output/geojson/counties/parcels_tx_*.geojson

2. CHECK COORDINATES: ./scripts/check_coordinates.sh
   → Detects if file needs reprojection (|X| > 180 or |Y| > 90)

3. REPROJECT (if needed): ./scripts/reproject_to_wgs84.sh
   → ogr2ogr -f GeoJSON -s_srs EPSG:3857 -t_srs EPSG:4326 out.geojson in.geojson
   → Converts Web Mercator to WGS84 (required for Tippecanoe)

4. TILE: ./scripts/generate_pmtiles.sh
   → tippecanoe -zg --drop-densest-as-needed --no-tile-compression -o out.pmtiles in.geojson
   → Generates PMTiles at multiple zoom levels

5. UPLOAD: python3 scripts/upload_to_r2_boto3.py --delete
   → Uploads to Cloudflare R2 CDN
   → Deletes local files after successful upload

6. VERIFY: curl -I https://pub-xxx.r2.dev/parcels/filename.pmtiles
   → Check file is accessible
```

### Automated Full Pipeline (Single Command)
```bash
# Runs: CHECK → REPROJECT → TILE → UPLOAD → CLEANUP
python3 scripts/parallel_process_upload.py 4  # 4 workers
```

### Coordinate System Reference
| CRS | EPSG | X Range | Y Range | Needs Reprojection |
|-----|------|---------|---------|-------------------|
| WGS84 | 4326 | -180 to 180 | -90 to 90 | No (ready) |
| Web Mercator | 3857 | -20M to 20M | -20M to 20M | Yes |
| State Plane | Varies | Large values | Large values | Yes |

### Known Coordinate Issues
| County | Issue | Fix |
|--------|-------|-----|
| Harris TX | Coords shifted by +172.5 | `python3 scripts/fix_harris_coords.py` |
| Various | State Plane CRS | `ogr2ogr -s_srs EPSG:XXXX -t_srs EPSG:4326` |

### Enrichment Data Sources
| Source | Purpose | Size | Priority |
|--------|---------|------|----------|
| PAD-US | Public lands (BLM, USFS, etc.) | 2.5GB | 1 |
| NWI | Wetlands (waterfowl habitat) | 15GB | 2 |
| NHD | Hydrography (streams, lakes) | 25GB | 3 |
| NLCD | Land cover classification | 50GB | 5 |
| SSURGO | Soil data | 100GB | 6 |

---

## hitd_maps PACKAGE

Custom Flutter package for map functionality.

### Usage
```dart
import 'package:hitd_maps/hitd_maps.dart';

HitdMap(
  initialPosition: LatLng(29.7604, -95.3698),
  initialZoom: 14.0,
  layers: [
    HitdMapLayer.parcels(),    // Property boundaries
    HitdMapLayer.publicLands(), // Public land overlay
  ],
  onFeatureTap: (latLng, properties) {
    // Handle parcel tap
  },
)
```

### Key Classes
- `HitdMap` - Main map widget
- `HitdMapController` - Map control (move, zoom, layers)
- `HitdMapLayer` - Layer configuration
- `ParcelInfo` - Parcel data model
- `LatLng` - Coordinate class

---

## PROJECT PHASES (ROADMAP)

### Completed (Phases 1-9)
- ✅ Phase 1: Production Readiness (security, memory leaks)
- ✅ Phase 2: Test Foundation
- ✅ Phase 3: Mobile App Polish
- ✅ Phase 4: Geofencing Core (auto check-in/out)
- ✅ Phase 5: Smart Notifications
- ✅ Phase 6: Map Data Pipeline (Texas)
- ✅ Phase 7: Web App Foundation
- ✅ Phase 9: Map Data Expansion (all 50 states)

### In Progress (Phases 10-14)
- 🚧 Phase 10: Launch Preparation
- 📋 Phase 11: Texas Parcel Full Export
- 📋 Phase 12: Map Performance Optimization
- 📋 Phase 13: Multi-State Parcel Data
- 📋 Phase 14: Automated Data Updates

### Future Features (Phases 15-26)
**Quick Wins:**
- Phase 15: Solunar Calculator (hunting time predictions)
- Phase 16: Wind Overlay (Open-Meteo API)
- Phase 17: Public Lands Layer (PAD-US)

**Medium Effort:**
- Phase 18: Crop History (USDA CropScape)
- Phase 19: Wildfire History (NIFC)
- Phase 20: WMA Boundaries

**High Impact:**
- Phase 21: Deer Movement Score (algorithm)
- Phase 22: Terrain Analysis (USGS 3DEP)
- Phase 23: Drive Coordinator (KILLER FEATURE)

**Group Features:**
- Phase 24: Shared Stand Picker
- Phase 25: Group Harvest Log
- Phase 26: Member Down Alert + Trail Cams

---

## COMMON COMMANDS

### Run Scraper
```bash
cd /home/exx/Documents/C/hitd_maps/data-pipeline

# Single state
python3 scripts/export_county_parcels.py --state TX

# Specific county
python3 scripts/export_county_parcels.py --county TX_HARRIS

# List available counties
python3 scripts/export_county_parcels.py --list
```

### Upload to R2
```bash
# Upload PMTiles
python3 scripts/upload_pmtiles_to_r2.py

# Upload all GeoJSON
python3 scripts/upload_all_to_r2.py

# List R2 contents
python3 scripts/upload_to_r2_boto3.py --list
```

### Generate Tiles
```bash
# Convert GeoJSON to PMTiles
tippecanoe -zg -o parcels_tx.pmtiles --drop-densest-as-needed output/geojson/tx/*.geojson
```

### Check API Health
```bash
# Texas API
curl -s "https://feature.tnris.org/arcgis/rest/services/Parcels/stratmap25_land_parcels_48/MapServer/0/query?where=1=1&returnCountOnly=true&f=json"

# Florida API
curl -s "https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/PARCELS/MapServer/0/query?where=1=1&returnCountOnly=true&f=json"
```

### Flutter App
```bash
cd /home/exx/Documents/C/hitd_maps

# Run on device
flutter run

# Build APK
flutter build apk

# Build iOS
flutter build ios
```

---

## AUTONOMOUS AGENT

### Data Agent Location
`/data-pipeline/agent/data_agent.py`

### Start Agent
```bash
cd /home/exx/Documents/C/hitd_maps/data-pipeline
source venv/bin/activate

# Single monitoring cycle
python3 agent/data_agent.py --once

# Continuous operation (every 6 hours)
python3 agent/data_agent.py --interval 360

# Check specific API
python3 agent/data_agent.py --check-api tx_statewide

# Run full pipeline only (reproject → tile → upload → cleanup)
python3 agent/data_agent.py --pipeline

# Cleanup local files already in R2
python3 agent/data_agent.py --cleanup

# Scrape a specific state
python3 agent/data_agent.py --scrape TX

# Scrape a specific county
python3 agent/data_agent.py --scrape TX --county harris
```

### Full Continuous Operation Flow
```
┌─────────────────────────────────────────────────────────────┐
│                    EVERY 6 HOURS                            │
│                                                             │
│  1. CHECK APIs ──► Compare record counts                    │
│        │                                                    │
│        ▼                                                    │
│  2. ANALYZE ──► Ask Ollama LLM if scrape needed            │
│        │                                                    │
│        ▼                                                    │
│  3. SCRAPE ──► Run export_county_parcels.py                │
│        │                                                    │
│        ▼                                                    │
│  4. REPROJECT ──► ogr2ogr EPSG:3857 → EPSG:4326            │
│        │                                                    │
│        ▼                                                    │
│  5. TILE ──► tippecanoe → PMTiles                          │
│        │                                                    │
│        ▼                                                    │
│  6. UPLOAD ──► boto3 → Cloudflare R2                       │
│        │                                                    │
│        ▼                                                    │
│  7. CLEANUP ──► Delete local files after upload            │
│        │                                                    │
│        ▼                                                    │
│  8. UPDATE DOCS ──► DATA_FRESHNESS.md                      │
│                                                             │
│  REPEAT...                                                  │
└─────────────────────────────────────────────────────────────┘
```

### What It Does
1. **Monitors APIs** - Checks record counts every 6 hours
2. **Detects Changes** - Compares to previous counts
3. **Uses LLM** - Asks Ollama (qwen2.5:72b) if re-scraping needed
4. **Scrapes Data** - Runs export_county_parcels.py for changed sources
5. **Full Pipeline** - Reproject → Tile → Upload → Cleanup
6. **Updates Docs** - Writes status to DATA_FRESHNESS.md
7. **Cleanup** - Deletes local files after successful R2 upload

### Run as Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/data-agent.service
```

Service file content:
```ini
[Unit]
Description=MyGSpot Data Agent
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

# View logs
journalctl -u data-agent -f
```

---

## FREE DATA SOURCES

| Source | URL | Data |
|--------|-----|------|
| PAD-US | protectedlands.net | Public lands nationwide |
| Open-Meteo | api.open-meteo.com | Weather/wind (NO API KEY) |
| USDA CropScape | nassgeodata.gmu.edu/CropScape | Crop history 2008-2024 |
| NIFC | data-nifc.opendata.arcgis.com | Fire perimeters 2000+ |
| USGS 3DEP | apps.nationalmap.gov/downloader | DEMs 1m-30m |
| USGS NHD | usgs.gov/national-hydrography | Water features |

---

## OLLAMA SERVER

**Host**: 10.8.0.1:11434

### Available Models
- `qwen2.5:72b` - Best for function calling/agents
- `llama3.3:70b` - General chat
- `deepseek-r1:671b` - Deep reasoning
- `qwen2.5-coder:7b` - Code completion
- `nomic-embed-text` - Embeddings

### Test Connection
```bash
curl http://10.8.0.1:11434/api/tags
```

---

## hitd_maps PACKAGE (Separate Repository)

**Location**: `/home/exx/Documents/C/hitd_maps`
**GitHub**: https://github.com/RORHITD/hitd_maps.git

### Purpose
A comprehensive Flutter mapping toolkit for outdoor/hunting applications. **ALL map-related functionality should go in hitd_maps, NOT in the main app.**

### Package Structure
```
/home/exx/Documents/C/hitd_maps/
├── lib/
│   ├── hitd_maps.dart              # Main export file
│   └── src/
│       ├── hitd_map.dart           # Main map widget
│       ├── hitd_map_controller.dart # Map controller
│       ├── hitd_map_config.dart    # Configuration
│       ├── layers/                 # Layer management
│       ├── services/
│       │   ├── solunar_service.dart  # Moon-based predictions
│       │   └── wind_service.dart     # Wind data (Open-Meteo)
│       ├── models/
│       │   ├── parcel_info.dart      # Parcel data model
│       │   └── public_land_info.dart # Public land model
│       ├── widgets/
│       │   ├── wind_overlay.dart     # Wind display widget
│       │   └── solunar_widget.dart   # Solunar display
│       ├── offline/                  # Offline tile caching
│       └── proprietary/              # Premium features (hunting pressure, leases)
```

### Key Features in hitd_maps
1. **HitdMap Widget** - MapLibre GL with PMTiles support
2. **SolunarService** - Moon-based hunting predictions
3. **WindService** - Real-time wind from Open-Meteo
4. **Layer System** - Parcels, public lands, wetlands, WMA
5. **Offline Support** - Download regions for offline use
6. **Proprietary Layers** - Hunting pressure, landowner contacts, leases

### When to Update hitd_maps (NOT main app)
- ANY map-related functionality changes
- New layer types (wetlands, WMA, terrain, crops)
- Solunar or wind service updates
- New map widgets or overlays
- PMTiles/tile configuration changes
- Offline caching improvements

### Development Workflow
```bash
# Work on hitd_maps
cd /home/exx/Documents/C/hitd_maps
# Make changes, commit, push

# Main app pulls from git
cd /home/exx/Documents/C/hitd_maps
flutter pub get  # Pulls latest hitd_maps
```

### Critical Documentation in hitd_maps
- **docs/DATA_REGISTRY.md** - SINGLE SOURCE OF TRUTH for all data sources
- **docs/DATA_PIPELINE.md** - Processing workflow documentation
- **docs/TROUBLESHOOTING.md** - Known issues and fixes
- **docs/INTEGRATION_GUIDE.md** - How to use the package
- **CHANGELOG.md** - Version history and data update log

### Data Sources (See DATA_REGISTRY.md for full details)
| Source | Type | Status |
|--------|------|--------|
| TX TNRIS | Parcels (28M) | ✅ Production |
| NY NYS ITS | Parcels (9M) | ✅ Production |
| PAD-US 4.0 | Public Lands | ✅ Production |
| Open-Meteo | Wind/Weather | ✅ Production |
| 200+ County APIs | Parcels | 🟡 Partial |

---

## CONTACT/SUPPORT

This is a hunting app built for hunters and hunting clubs. The goal is to make it the best group hunting coordination platform with comprehensive land data.

Key differentiators:
1. **Auto geofencing** - Check in/out when entering/leaving areas
2. **Real-time tracking** - See group members on map
3. **Public land data** - All 50 states, free
4. **Drive Coordinator** - Unique feature for group deer drives
5. **Smart notifications** - Safety alerts for hunters

---

*Knowledge base created: 2026-01-15*
*For use with Open WebUI autonomous agents*
