# GSpot Parcel Data Pipeline - Technical Specification

> **Last Updated**: January 13, 2026
> **Status**: Active scraping in progress
> **Total Data**: ~85GB across 46 states

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  ArcGIS APIs    │────▶│  GeoJSON Files  │────▶│    PMTiles      │
│  (Source Data)  │     │  (Local Storage)│     │  (Vector Tiles) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        │                                               ▼
        │                                      ┌─────────────────┐
        │                                      │  Cloudflare R2  │
        │                                      │  (CDN Hosting)  │
        │                                      └─────────────────┘
        │                                               │
        ▼                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│  EPSG:3857      │                            │  MapLibre GL    │
│  → WGS84        │                            │  (Flutter/Web)  │
│  (Reproject)    │                            └─────────────────┘
└─────────────────┘
```

## Quick Start - Run on Server with More RAM

```bash
# Clone and navigate
cd data-pipeline

# Install dependencies
pip install pyproj pmtiles requests
brew install tippecanoe awscli  # or apt-get on Linux

# Run multiple scrapers in parallel
python3 scripts/export_county_parcels.py TX_STATEWIDE -o output/geojson &
python3 scripts/export_county_parcels.py CA_LOS_ANGELES -o output/geojson &
python3 scripts/export_county_parcels.py NY_STATEWIDE_V2 -o output/geojson &

# Monitor progress
ps aux | grep export_county_parcels | grep -v grep
```

## Directory Structure

```
data-pipeline/
├── scripts/
│   ├── export_county_parcels.py   # Main export script (200+ configs)
│   ├── export_state_parcels.py    # Alternative state exporter
│   ├── process_all_states.py      # Batch processor
│   ├── reproject_geojson.py       # EPSG:3857 → EPSG:4326
│   ├── convert_to_pmtiles.py      # tippecanoe + pmtiles
│   ├── bulk_upload_r2.sh          # Bulk Cloudflare R2 upload
│   └── upload_to_r2.sh            # Single file R2 upload
├── output/
│   ├── geojson/                   # Raw GeoJSON by state
│   │   ├── tx/                    # Texas parcels
│   │   ├── ca/                    # California parcels
│   │   └── ...                    # 50 state folders
│   └── tiles/                     # Generated PMTiles
│       ├── parcels_tx.pmtiles
│       ├── parcels_ca.pmtiles
│       └── ...
├── preview/
│   └── index.html                 # Web preview (MapLibre)
└── docs/
    ├── TECHNICAL_SPEC.md          # This file
    ├── DATA_FRESHNESS.md          # Update tracking
    ├── AI_DATA_IMPROVEMENT_GUIDE.md
    └── AI_PROMPT_TEMPLATES.md
```

---

## Cloudflare R2 Configuration

### Bucket Details
| Setting | Value |
|---------|-------|
| **Bucket Name** | `gspot-tiles` |
| **Account ID** | `551bf8d24bb6069fbaa10e863a672fd5` |
| **Public URL** | `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev` |
| **Endpoint** | `https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com` |
| **File Pattern** | `parcels/parcels_{state}.pmtiles` |

### R2 Upload Commands

```bash
# Single file upload
aws s3 cp output/tiles/parcels_tx.pmtiles \
  s3://gspot-tiles/parcels/parcels_tx.pmtiles \
  --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com

# Bulk upload all PMTiles
./scripts/bulk_upload_r2.sh

# Upload GeoJSON for backup
aws s3 cp output/geojson/tx/parcels_tx_harris.geojson \
  s3://gspot-tiles/parcels/parcels_tx_harris.geojson \
  --endpoint-url https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com \
  --no-progress
```

### AWS CLI Configuration for R2

```bash
# Configure credentials (~/.aws/credentials)
[default]
aws_access_key_id = YOUR_R2_ACCESS_KEY
aws_secret_access_key = YOUR_R2_SECRET_KEY

# Or set environment variables
export AWS_ACCESS_KEY_ID=YOUR_R2_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=YOUR_R2_SECRET_KEY
```

### Accessing Files in MapLibre

```javascript
// PMTiles URL pattern
const pmtilesUrl = 'https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/parcels_tx.pmtiles';

// In MapLibre
map.addSource('parcels', {
  type: 'vector',
  url: `pmtiles://${pmtilesUrl}`
});
```

---

## Complete Pipeline Steps

### Step 1: Scrape from ArcGIS APIs

```bash
# List available configs
python3 scripts/export_county_parcels.py --list

# Run single state
python3 scripts/export_county_parcels.py TX_STATEWIDE -o output/geojson

# Run multiple in parallel (for servers with RAM)
for config in TX_STATEWIDE CA_LOS_ANGELES NY_STATEWIDE_V2 FL_STATEWIDE; do
  python3 scripts/export_county_parcels.py $config -o output/geojson &
done
```

### Step 2: Check & Reproject Coordinates

```bash
# Check if reprojection needed (coordinates > 180 = Web Mercator)
head -c 1000 output/geojson/tx/parcels_tx_harris.geojson

# Reproject if needed
python3 scripts/reproject_geojson.py \
  output/geojson/tx/parcels_tx_harris.geojson \
  output/geojson/tx_wgs84/parcels_tx_harris.geojson
```

### Step 3: Generate Vector Tiles

```bash
# Single file
tippecanoe -o output/tiles/parcels_tx.mbtiles \
  -Z10 -z16 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --coalesce-densest-as-needed \
  --detect-shared-borders \
  --simplification=10 \
  -l parcels \
  output/geojson/tx/*.geojson

# Or use the script
python3 scripts/convert_to_pmtiles.py output/geojson/tx output/tiles/parcels_tx.pmtiles
```

### Step 4: Convert to PMTiles

```bash
# Using pmtiles CLI
pmtiles convert output/tiles/parcels_tx.mbtiles output/tiles/parcels_tx.pmtiles

# Or Python script
python3 scripts/mbtiles_to_pmtiles.py output/tiles/parcels_tx.mbtiles output/tiles/parcels_tx.pmtiles
```

### Step 5: Upload to Cloudflare R2

```bash
# Single file
./scripts/upload_to_r2.sh output/tiles/parcels_tx.pmtiles parcels/parcels_tx.pmtiles

# Bulk upload
./scripts/bulk_upload_r2.sh
```

---

## State Scraping Status (January 2026)

### Complete (100%) - 17 States
| State | Size | Parcels | Tax Year |
|-------|------|---------|----------|
| AK | 258MB | ~200K | 2024 |
| CA | 19.4GB | ~14M | 2024-2025 |
| CO | 5.2GB | ~3M | 2024 |
| CT | 2.8GB | ~1.2M | 2024 |
| DE | 391MB | ~400K | 2024 |
| HI | 424MB | ~400K | 2024 |
| IA | 2.2GB | ~1.7M | 2024 |
| MA | 4.4GB | ~2M | 2024 |
| ND | 881MB | ~400K | 2024 |
| NH | 871MB | ~600K | 2024 |
| NV | 2.5GB | ~1.2M | 2024 |
| SC | 2.8GB | ~2.5M | 2024 |
| TN | 3.2GB | ~3M | 2024 |
| UT | 1.3GB | ~1.2M | 2024 |
| WV | 1.9GB | ~1M | 2024 |

### In Progress - Needs More Scraping
| State | Current | Expected | % Complete |
|-------|---------|----------|------------|
| TX | 4.2GB | 22GB | 19% |
| PA | 422MB | 4.5GB | 9% |
| GA | 1.1GB | 3.5GB | 33% |
| MI | 1.8GB | 3.5GB | 51% |
| OH | 2.8GB | 4.5GB | 62% |
| IL | 740MB | 4GB | 18% |
| WI | 1.2GB | 2.4GB | 48% |

### Failed/Needs Attention
| State | Issue | Solution |
|-------|-------|----------|
| AR | API not responding | Find alternative endpoint |
| OK | DNS errors | Check endpoint URL |
| ME | SSL certificate errors | Update certifi or use VPN |
| VT | API errors | Find alternative source |
| RI | No config | Research state GIS portal |
| FL | 403 Forbidden | Add rate limiting, use proxies |

---

## Available Export Configs

### Statewide Configs (Best for coverage)
```
TX_STATEWIDE          # Texas TNRIS - 28M parcels
TX_STATEWIDE_RECENT   # Texas TNRIS most recent
NY_STATEWIDE_V2       # New York ITS - 9M parcels
FL_STATEWIDE          # Florida DEP
PA_STATEWIDE          # Pennsylvania
PA_PASDA_STATEWIDE    # Pennsylvania PASDA
OH_STATEWIDE          # Ohio
VA_STATEWIDE          # Virginia VGIN
CO_STATEWIDE          # Colorado
WI_STATEWIDE          # Wisconsin
NC_STATEWIDE          # North Carolina
IN_STATEWIDE          # Indiana
WA_STATEWIDE          # Washington
```

### Major County Configs
```
# Texas
TX_HARRIS             # Houston - 1.8M parcels
TX_DALLAS             # Dallas - 1M parcels
TX_BEXAR              # San Antonio
TX_TARRANT            # Fort Worth

# California
CA_LOS_ANGELES        # LA County - 2.4M parcels
CA_SAN_DIEGO          # San Diego
CA_ORANGE             # Orange County
CA_RIVERSIDE          # Riverside
CA_ALAMEDA            # Oakland/East Bay

# Florida
FL_MIAMI_DADE         # Miami
FL_BROWARD            # Fort Lauderdale
FL_PALM_BEACH         # Palm Beach
FL_HILLSBOROUGH       # Tampa

# Other Major Metros
IL_COOK               # Chicago
MI_WAYNE              # Detroit
GA_FULTON             # Atlanta
PA_ALLEGHENY          # Pittsburgh
OH_CUYAHOGA           # Cleveland
```

---

## Data Freshness & Update Schedule

### Source Update Frequencies
| Source Type | Update Frequency | Best Time to Scrape |
|-------------|------------------|---------------------|
| State Portals | Annual | January-March (after tax roll) |
| County Assessors | Quarterly | After quarterly updates |
| Major Metros | Monthly | First week of month |

### Check for Updates
```bash
# Check API last edit date
curl -s "{service_url}?f=json" | jq '.editingInfo.lastEditDate'

# Compare parcel counts
curl -s "{service_url}?where=1=1&returnCountOnly=true&f=json" | jq '.count'

# Check tax_year in data
head -c 5000 output/geojson/tx/parcels_tx_harris.geojson | grep -o '"tax_year":"[^"]*"'
```

### Recommended Refresh Schedule
| Priority | States | Frequency |
|----------|--------|-----------|
| High | TX, CA, FL, NY | Quarterly |
| Medium | PA, OH, VA, CO, WI, NC | Bi-annually |
| Low | All others | Annually |

---

## API Query Format

### Standard ArcGIS REST Query
```
GET {service_url}/query?
  where=1=1
  &outFields=*
  &f=geojson
  &resultOffset=0
  &resultRecordCount=2000
  &returnGeometry=true
```

### Query Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| where | `1=1` | Get all records |
| outFields | `*` | All fields |
| f | `geojson` or `json` | Output format |
| resultOffset | `0,2000,4000...` | Pagination |
| resultRecordCount | `1000-2000` | Batch size |
| returnGeometry | `true` | Include polygons |

### Count Query (Check Total Records)
```bash
curl -s "{service_url}/query?where=1=1&returnCountOnly=true&f=json" | jq '.count'
```

---

## Common Field Mappings

Different sources use different field names. Standardize to:

| Standard Field | Common Variants |
|----------------|-----------------|
| owner_name | OWNERNME1, OWNER, OwnerName, OWNER_NAME, owner_name_1 |
| site_address | SITEADRESS, SITEADDRESS, situs_addr, SITE_ADDR |
| parcel_id | PARCELID, parcel_id, PIN, APN, GPIN, HCAD_NUM |
| acreage | ACRES, acreage, Acreage, Shape__Area (÷43560) |
| county | COUNTY, county_name, LOCALITY, site_county |
| land_value | LAND_VALUE, landvalue, assessed_land, land_value |
| improvement_value | IMPR_VALUE, imp_value, BLDGVALUE, bld_value |
| tax_year | tax_year, TAX_YEAR, data_year, TAXYEAR |

---

## Coordinate Systems

### WGS84 (EPSG:4326) - Standard for MapLibre
- Longitude: -180 to 180
- Latitude: -90 to 90
- Example: `-95.3698, 29.7604` (Houston)

### Web Mercator (EPSG:3857) - Needs Conversion
- X: ~-20,000,000 to 20,000,000
- Y: ~-20,000,000 to 20,000,000
- Example: `-10615325, 3473843` (Houston)

### Auto-Detection
```python
def needs_reprojection(coords):
    x, y = coords[0], coords[1]
    return abs(x) > 180 or abs(y) > 90
```

---

## Tippecanoe Configuration

### Recommended Flags for Parcels
```bash
tippecanoe \
  -Z10 \                          # Min zoom 10
  -z16 \                          # Max zoom 16
  --drop-densest-as-needed \      # Handle dense urban areas
  --extend-zooms-if-still-dropping \
  --coalesce-densest-as-needed \  # Merge tiny parcels at low zoom
  --detect-shared-borders \       # Optimize adjacent parcels
  --simplification=10 \           # Reduce vertices
  -l parcels \                    # Layer name
  -o output.mbtiles \
  input.geojson
```

### For Large Files (>10GB)
```bash
tippecanoe \
  --no-feature-limit \
  --no-tile-size-limit \
  -Z10 -z16 \
  --drop-densest-as-needed \
  -l parcels \
  -o output.mbtiles \
  input.geojson
```

---

## Error Handling

### Common Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| Rate Limiting | 429 Too Many Requests | Reduce batch_size to 1000, add 1s delay |
| Timeout | Connection timeout | Increase timeout to 120s |
| SSL Errors | Certificate verify failed | `pip install --upgrade certifi` |
| 403 Forbidden | Access denied | Check if API requires auth/VPN |
| DNS Errors | Host not found | API endpoint may have changed |
| Memory Error | Process killed | Reduce batch_size, process by county |
| Invalid JSON | Parsing error | Check for truncated responses |

### Retry Logic
```python
import time
for attempt in range(3):
    try:
        response = fetch_data()
        break
    except Exception as e:
        time.sleep(2 ** attempt)  # Exponential backoff
```

---

## Performance Benchmarks

| Operation | Speed | Notes |
|-----------|-------|-------|
| API Scraping | ~10K parcels/min | Depends on API speed |
| Reprojection | ~100K parcels/min | CPU-bound |
| Tippecanoe | ~1M parcels/hour | Disk I/O bound |
| PMTiles Convert | ~1GB/min | Quick |
| R2 Upload | ~50MB/min | Network bound |

### RAM Requirements
| Parcel Count | Recommended RAM |
|--------------|-----------------|
| < 1M | 4GB |
| 1-5M | 8GB |
| 5-15M | 16GB |
| 15-30M (TX) | 32GB+ |

---

## Dependencies

### Python
```bash
pip install pyproj pmtiles requests tqdm
```

### System Tools
```bash
# macOS
brew install tippecanoe awscli jq

# Ubuntu/Debian
sudo apt-get install tippecanoe awscli jq

# Verify installations
tippecanoe --version
aws --version
pmtiles --version
```

---

## Testing & Validation

### Validate New API Endpoint
```bash
# 1. Check service info
curl -s "{URL}?f=json" | jq '.name, .type'

# 2. Get field names
curl -s "{URL}?f=json" | jq '.fields[].name'

# 3. Get record count
curl -s "{URL}/query?where=1=1&returnCountOnly=true&f=json" | jq '.count'

# 4. Test pagination support
curl -s "{URL}/query?where=1=1&resultOffset=1000&resultRecordCount=10&f=json"

# 5. Check coordinate system
curl -s "{URL}/query?where=1=1&f=geojson&resultRecordCount=1" | \
  jq '.features[0].geometry.coordinates[0][0]'
```

### Validate Generated Tiles
```bash
# Check PMTiles metadata
pmtiles show output/tiles/parcels_tx.pmtiles

# Serve locally for testing
pmtiles serve output/tiles/ --port 8080

# Open in browser
open http://localhost:8080
```

---

## Adding a New State

1. **Find API Endpoint**
   - Search: `{state} parcel GIS ArcGIS REST`
   - Check state GIS portal
   - Use AI_PROMPT_TEMPLATES.md for search queries

2. **Add Config to export_county_parcels.py**
   ```python
   "XX_STATEWIDE": {
       "name": "State Name Statewide",
       "service_url": "https://gis.state.gov/.../MapServer/0/query",
       "out_fields": "*",
       "batch_size": 2000,
   },
   ```

3. **Test the Config**
   ```bash
   python3 scripts/export_county_parcels.py XX_STATEWIDE -o output/geojson --limit 1000
   ```

4. **Run Full Export**
   ```bash
   python3 scripts/export_county_parcels.py XX_STATEWIDE -o output/geojson
   ```

5. **Generate Tiles & Upload**
   ```bash
   python3 scripts/convert_to_pmtiles.py output/geojson/xx output/tiles/parcels_xx.pmtiles
   ./scripts/upload_to_r2.sh output/tiles/parcels_xx.pmtiles parcels/parcels_xx.pmtiles
   ```

---

## Monitoring Running Scrapers

```bash
# Count active scrapers
ps aux | grep export_county_parcels | grep -v grep | wc -l

# List all running scrapers
ps aux | grep export_county_parcels | grep -v grep | \
  sed 's/.*export_county_parcels.py //' | sed 's/ -o.*//'

# Check memory usage
ps aux | grep export_county_parcels | grep -v grep | \
  awk '{print $12, "| Mem:", int($6/1024)"MB"}'

# Kill all scrapers
pkill -f export_county_parcels
```

---

## Contact & Resources

- **Texas TNRIS**: https://tnris.org
- **Regrid (Commercial Alternative)**: https://regrid.com
- **National Parcel Map**: https://www.arcgis.com/home/item.html?id=a6e0cdb6d2264e7aa4de66acf42d0fa0
