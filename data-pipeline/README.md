# HITD Maps - Data Pipeline

Autonomous data pipeline for processing and serving parcel data, enrichment layers, and map tiles.

## Quick Start

```bash
# One-command setup
./scripts/setup_environment.sh

# Check status
make status

# Run full update
make update

# Start autonomous agent (every 6 hours)
make agent
```

## Overview

This pipeline:
1. **Scrapes** parcel data from 200+ county ArcGIS APIs
2. **Reprojects** coordinates to WGS84 (EPSG:4326)
3. **Generates** PMTiles vector tiles using Tippecanoe
4. **Uploads** to Cloudflare R2 CDN
5. **Cleans up** local files after successful upload
6. **Updates** documentation automatically

## Directory Structure

```
data-pipeline/
├── agent/                  # Autonomous monitoring agent
│   ├── data_agent.py       # Main agent script
│   └── agent_state.db      # SQLite state tracking
├── scripts/                # Processing scripts
│   ├── export_county_parcels.py
│   ├── reproject_to_wgs84.sh
│   ├── parallel_process_upload.py
│   └── ...
├── config/                 # Configuration files
│   ├── sources.json        # Data source registry
│   ├── enrichment_sources.json
│   └── hitd-data-agent.service
├── output/                 # Processing output
│   ├── geojson/
│   └── pmtiles/
├── docs/                   # Pipeline documentation
├── Makefile                # Common operations
└── .env                    # Credentials (created by setup)
```

## Make Commands

| Command | Description |
|---------|-------------|
| `make setup` | Install all dependencies |
| `make status` | Show pipeline status |
| `make update` | Run full scrape + pipeline |
| `make pipeline` | Process existing files |
| `make agent` | Start autonomous agent |
| `make scrape STATE=TX` | Scrape specific state |
| `make docs` | Update documentation |
| `make cleanup` | Remove uploaded local files |

## Agent Operation

The autonomous agent monitors key APIs and automatically:
- Detects data changes (record count changes >0.1%)
- Uses Ollama LLM to decide if re-scraping is needed
- Queues and executes scrape jobs
- Processes through full pipeline
- Updates documentation

```bash
# Run once
python3 agent/data_agent.py --once

# Run continuously
python3 agent/data_agent.py --interval 360

# Check specific API
python3 agent/data_agent.py --check-api tx_statewide

# Run pipeline only
python3 agent/data_agent.py --pipeline

# Update docs only
python3 agent/data_agent.py --update-docs
```

## Install as Service

```bash
make install-service
sudo systemctl start hitd-data-agent
sudo systemctl status hitd-data-agent
```

## Documentation

- [COMPLETE_OPERATIONS_GUIDE.md](docs/COMPLETE_OPERATIONS_GUIDE.md) - Full operations manual
- [DATA_PIPELINE.md](../docs/DATA_PIPELINE.md) - Pipeline workflow
- [DATA_REGISTRY.md](../docs/DATA_REGISTRY.md) - Data source registry
- [TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md) - Common issues

## Part of HITD Maps

This data pipeline is part of the [hitd_maps](https://github.com/RORHITD/hitd_maps) Flutter package by Houston IT Developers LLC.

## Repository

- **GitHub**: https://github.com/RORHITD/hitd_maps
- **Issues**: https://github.com/RORHITD/hitd_maps/issues
