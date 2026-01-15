# AI Agent Context - hitd_maps

> **This document provides context for AI agents (Open WebUI, Claude, etc.) working with hitd_maps.**

## What is hitd_maps?

hitd_maps is a comprehensive Flutter mapping toolkit for outdoor/hunting applications. It is the **central repository for ALL map-related code and data** for the My G Spot Outdoors platform.

## Repository Locations

| Repo | Path | Purpose |
|------|------|---------|
| **hitd_maps** | `/home/exx/Documents/C/hitd_maps` | Map package (THIS REPO) |
| my-gspot-outdoors | `/home/exx/Documents/C/my-gspot-outdoors-flutter` | Main Flutter app |
| data-pipeline | `my-gspot-outdoors/data-pipeline` | Data scraping scripts |

## Key Files to Know

### Documentation
- `docs/DATA_REGISTRY.md` - **ALL data sources, extraction dates, issues**
- `docs/DATA_PIPELINE.md` - How data flows from source to app
- `docs/TROUBLESHOOTING.md` - Known issues and solutions
- `CHANGELOG.md` - Version history

### Code
- `lib/hitd_maps.dart` - Main package export
- `lib/src/hitd_map.dart` - Map widget
- `lib/src/services/solunar_service.dart` - Moon-based predictions
- `lib/src/services/wind_service.dart` - Wind data (Open-Meteo)

## Data Sources Summary

### Parcel Data (Property Boundaries)
- **Total**: ~150M parcels across US
- **Primary APIs**: TNRIS (TX), NYS ITS (NY), MSDI (MT)
- **Storage**: Cloudflare R2 as PMTiles
- **Update**: Quarterly

### Public Lands (PAD-US)
- **Source**: USGS Gap Analysis Project
- **Coverage**: Nationwide
- **Update**: Annual (October)

### Weather/Wind
- **Source**: Open-Meteo API
- **Cost**: FREE (no API key)
- **Update**: Real-time

## Common Tasks

### Add New Data Layer
1. Add download script to `data-pipeline/scripts/enrichment/`
2. Document in `docs/DATA_REGISTRY.md`
3. Add layer type to `lib/src/layers/map_layer.dart`
4. Update `lib/src/hitd_map_controller.dart`
5. Test and commit to hitd_maps
6. Run `flutter pub get` in main app

### Fix Data Issue
1. Document issue in `docs/DATA_REGISTRY.md` (Known Issues section)
2. Create fix script in `data-pipeline/scripts/`
3. Re-process affected tiles
4. Upload to R2
5. Update CHANGELOG.md

### Update Existing Data
1. Run scraper: `python3 scripts/export_county_parcels.py --state XX`
2. Generate tiles: `tippecanoe ...`
3. Upload: `python3 scripts/upload_pmtiles_to_r2.py`
4. Update `docs/DATA_REGISTRY.md` with new date
5. Update `CHANGELOG.md`

## Credentials (Environment Variables)

```bash
R2_ACCESS_KEY=ecd653afe3300fdc045b9980df0dbb14
R2_SECRET_KEY=c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35
R2_BUCKET=gspot-tiles
R2_ENDPOINT=https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev
```

## Ollama Server

- **Host**: 10.8.0.1:11434
- **Models**: qwen2.5:72b (best for agents), llama3.3:70b, deepseek-r1:671b

## Rules for AI Agents

1. **ALL map changes go in hitd_maps, not the main app**
2. **Update DATA_REGISTRY.md when adding/changing data sources**
3. **Update CHANGELOG.md for significant changes**
4. **Test before pushing to main branch**
5. **Document issues with date and status**

## Quick Commands

```bash
# Check API health
curl -s "https://feature.tnris.org/.../query?where=1=1&returnCountOnly=true&f=json"

# Scrape state
cd /home/exx/Documents/C/my-gspot-outdoors-flutter/data-pipeline
python3 scripts/export_county_parcels.py --state TX

# Upload tiles
python3 scripts/upload_pmtiles_to_r2.py

# Run agent
python3 agent/data_agent.py --once

# Update hitd_maps in main app
cd /home/exx/Documents/C/my-gspot-outdoors-flutter
flutter pub get
```

---

*Last updated: 2026-01-15*
