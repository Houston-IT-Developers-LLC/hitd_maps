# Self-Hosted Map Infrastructure

## Current Status

We are building a **100% self-hosted map solution** on Cloudflare R2 - no external dependencies.

### Already Self-Hosted on R2

| Asset | URL | Size | Status |
|-------|-----|------|--------|
| **Basemap** | `r2.dev/basemap/planet.pmtiles` | 110 GB | Done |
| **Harris County Parcels** | `r2.dev/parcels/parcels_tx_harris.pmtiles` | 266 MB | Done |
| **MapLibre GL JS** | `r2.dev/js/maplibre-gl.js` | 757 KB | Done |
| **MapLibre CSS** | `r2.dev/js/maplibre-gl.css` | 64 KB | Done |
| **PMTiles JS** | `r2.dev/js/pmtiles.js` | 47 KB | Done |
| **Font Glyphs** | `r2.dev/fonts/Noto Sans Regular/*.pbf` | 34 MB | Done |

**R2 Bucket URL:** `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/`

### Pending Self-Hosting

| Asset | Source | Size (USA) | Priority |
|-------|--------|------------|----------|
| **Terrain Tiles** | USGS 3DEP / SRTM | 50-100 GB | High |
| **Satellite Imagery** | NASA NAIP | 30+ TB | Medium |
| **POIs** | Overture Maps | 75-100 GB | High |
| **Buildings** | Overture Maps | ~50 GB | Medium |
| **Addresses** | Overture Maps | ~20 GB | Low |

---

## Data Sources Research

### 1. Terrain/Elevation Data

**Best Option: USGS 3DEP + SRTM**

Download methods:
```bash
# Install elevation tool
pip install elevation

# Download SRTM 30m for USA (uses bbox)
eio clip -o usa_dem.tif --bounds -125 24.8 -65.8 49.2

# Convert to terrain-rgb format
rio rgbify -b -10000 -i 0.1 usa_dem.tif usa_terrain_rgb.tif

# Create PMTiles
gdal2tiles.py usa_terrain_rgb.tif ./tiles/
pmtiles convert tiles/ usa_terrain.pmtiles
```

**Storage:** ~50-100 GB for USA at zoom levels 0-14

### 2. Satellite Imagery

**Best Option: NASA NAIP** (0.6m resolution)

Sources:
- USGS EarthExplorer: https://earthexplorer.usgs.gov/
- USDA NAIP Hub: https://naip-usdaonline.hub.arcgis.com/

**Storage:** 30+ TB for complete USA coverage (can subset by state)

### 3. Points of Interest (POIs)

**Best Option: Overture Maps**

```bash
# Install Overture CLI
pip install overturemaps

# Download USA POIs
overturemaps download \
  --bbox=-125,24.8,-65.8,49.2 \
  -f geojson \
  --type=place \
  -o usa_pois.geojson

# Convert to PMTiles
tippecanoe -fo usa_pois.pmtiles \
  -Z10 -z14 \
  -l pois \
  usa_pois.geojson
```

**Categories available:** 64M+ POIs with 2,000+ categories
- Restaurants, cafes, bars
- Gas stations, car dealers
- Hospitals, pharmacies
- Schools, universities
- Banks, ATMs
- Shopping malls, stores
- Hotels, campgrounds

### 4. Buildings Footprints

From Overture Maps:
```bash
overturemaps download \
  --bbox=-125,24.8,-65.8,49.2 \
  -f geojson \
  --type=building \
  -o usa_buildings.geojson
```

### 5. Transportation/Roads

Already included in Protomaps basemap, but Overture provides additional detail:
```bash
overturemaps download \
  --bbox=-125,24.8,-65.8,49.2 \
  -f geojson \
  --type=segment \
  -o usa_roads.geojson
```

---

## R2 Bucket Structure

```
pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/
├── basemap/
│   └── planet.pmtiles          # 110 GB - World basemap
├── parcels/
│   └── parcels_tx_harris.pmtiles  # 266 MB - Harris County
├── js/
│   ├── maplibre-gl.js          # 757 KB
│   ├── maplibre-gl.css         # 64 KB
│   └── pmtiles.js              # 47 KB
├── fonts/
│   └── Noto Sans Regular/      # 34 MB - 256 PBF files
│       ├── 0-255.pbf
│       ├── 256-511.pbf
│       └── ... (all Unicode ranges)
├── terrain/                     # TODO
│   └── usa_terrain.pmtiles
├── satellite/                   # TODO
│   └── naip_*.pmtiles
└── pois/                        # TODO
    └── usa_pois.pmtiles
```

---

## Monthly Costs (Estimated)

| Resource | Cost |
|----------|------|
| R2 Storage (200 GB) | $3.00 |
| R2 Class A Operations | $4.50/million |
| R2 Class B Operations | $0.36/million |
| **Total (typical usage)** | **~$10-20/month** |

**Note:** R2 has zero egress fees, unlike S3!

---

## MapLibre Configuration

Current self-hosted setup in `complete_map.html`:

```javascript
// All resources from our R2 bucket
const R2_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev";

const mapStyle = {
    version: 8,
    glyphs: `${R2_BASE}/fonts/{fontstack}/{range}.pbf`,
    sources: {
        "basemap": {
            type: "vector",
            url: `pmtiles://${R2_BASE}/basemap/planet.pmtiles`
        },
        "parcels": {
            type: "vector",
            url: `pmtiles://${R2_BASE}/parcels/parcels_tx_harris.pmtiles`
        }
        // TODO: Add terrain, satellite, POIs
    }
};
```

---

## Scripts for Data Processing

### Upload to R2
```python
# Use boto3 with R2 credentials
# See: data-pipeline/scripts/upload_to_r2_boto3.py
```

### Coordinate Transformation
```bash
# Texas State Plane to WGS84
ogr2ogr -f GeoJSON \
    -s_srs EPSG:2278 \
    -t_srs EPSG:4326 \
    output.geojson input.geojson
```

### Create PMTiles
```bash
tippecanoe -z14 -Z10 \
    --drop-densest-as-needed \
    -o output.pmtiles \
    -l layer_name \
    input.geojson
```

---

## Next Steps

1. **Download SRTM terrain data** (~50 GB)
   - Convert to terrain-rgb PMTiles
   - Upload to R2

2. **Download Overture Maps POIs** (~75-100 GB)
   - Filter to USA bbox
   - Convert to PMTiles
   - Upload to R2

3. **Download NAIP satellite imagery** (prioritize hunting areas)
   - Start with Texas
   - Convert to raster PMTiles
   - Upload to R2

4. **Add more Texas county parcels**
   - Use existing scraping scripts
   - Transform coordinates (EPSG:2278 → 4326)
   - Generate PMTiles
   - Upload to R2

---

## External Dependencies: NONE

After completing the above, our map will have:
- Zero CDN dependencies
- Zero API key requirements
- Zero third-party tile services
- Complete data ownership
- Predictable costs (R2 storage only)
