# Texas Parcel Data Plan

Complete plan for generating and serving property line data for all of Texas.

## Current Status

**What's Working:**
- Live TNRIS ArcGIS API queries work for on-demand parcel data
- Web app displays parcels correctly at zoom 14+
- Parcel details panel shows all property information

**Limitation:**
- TNRIS API has 2,000 record limit per query
- Each map view triggers API call (latency + rate limits)
- Not suitable for production scale

## Goal

Generate pre-built vector tiles for all ~28 million Texas parcels to serve from CDN.

---

## Option A: Use Existing TNRIS Live API (Current)

**Pros:**
- Already working
- Always current data (quarterly updates)
- No storage costs

**Cons:**
- 2,000 parcel limit per query
- API latency on every pan/zoom
- May hit rate limits
- Not suitable for offline use

**Recommendation:** Keep for fallback, but implement tiles for production.

---

## Option B: Pre-Generated Vector Tiles (Recommended)

### Step 1: Download TNRIS Statewide Dataset

**Data Source:** TxGIO StratMap Land Parcels
- URL: https://tnris.org/stratmap/land-parcels
- Format: File Geodatabase (.gdb)
- Size: ~5-8 GB compressed
- Records: ~28 million parcels
- Updates: Quarterly

**Download Process:**
```bash
# Navigate to TNRIS Data Hub
# Find current StratMap Land Parcels download link
# Run download script
cd data-pipeline
./scripts/download_texas.sh ./downloads "https://data.tnris.org/[current-url]/parcels.gdb.zip"
```

### Step 2: Convert to PostGIS

```bash
# Create database
createdb gspot
psql gspot -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Load geodatabase (10-30 min for 28M parcels)
./scripts/load_texas.sh ./downloads/StratMap_Land_Parcels.gdb
```

**Table Schema:**
```sql
CREATE TABLE parcels (
  gid SERIAL PRIMARY KEY,
  prop_id VARCHAR(50),
  geo_id VARCHAR(50),
  owner_name VARCHAR(255),
  situs_addr VARCHAR(255),
  situs_city VARCHAR(100),
  county VARCHAR(100),
  mkt_value NUMERIC,
  land_value NUMERIC,
  imp_value NUMERIC,
  legal_area NUMERIC,
  tax_year INTEGER,
  geom GEOMETRY(MultiPolygon, 4326)
);

CREATE INDEX idx_parcels_geom ON parcels USING GIST (geom);
CREATE INDEX idx_parcels_county ON parcels (county);
```

### Step 3: Export to GeoJSON

```bash
# Export full state (may be 10+ GB)
./scripts/export_geojson.sh TX

# Or export by county for parallel processing
./scripts/export_geojson.sh TX --by-county
```

### Step 4: Generate Vector Tiles

```bash
# Generate MBTiles (30-60 min)
./scripts/generate_tiles.sh ./output/geojson ./output/tiles TX

# Result: parcels_tx.mbtiles (~2-5 GB)
```

**Tippecanoe Settings for 28M Parcels:**
```bash
tippecanoe \
  -o parcels_tx.mbtiles \
  -Z8 -z14 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --coalesce-densest-as-needed \
  --detect-shared-borders \
  --simplification=10 \
  --minimum-zoom=8 \
  --maximum-zoom=14 \
  -l parcels_tx \
  --force \
  parcels_tx.geojson
```

### Step 5: Convert to PMTiles

```bash
# Install pmtiles CLI
npm install -g pmtiles

# Convert MBTiles to PMTiles
pmtiles convert parcels_tx.mbtiles parcels_tx.pmtiles

# Result: parcels_tx.pmtiles (~1-3 GB)
```

### Step 6: Deploy to CDN

**Option A: Cloudflare R2 (Recommended)**
- No egress fees
- Built-in range request support
- Global edge network

```bash
# Using wrangler CLI
wrangler r2 object put tiles/parcels_tx.pmtiles --file=parcels_tx.pmtiles
```

**Option B: AWS S3 + CloudFront**
```bash
aws s3 cp parcels_tx.pmtiles s3://my-gspot-tiles/parcels/
# Configure CloudFront distribution with CORS headers
```

### Step 7: Update Web App

```typescript
// src/components/map/ParcelLayer.tsx
import { Protocol } from 'pmtiles';

// Register PMTiles protocol
const protocol = new Protocol();
maplibregl.addProtocol('pmtiles', protocol.tile);

// Use PMTiles source
new MVTLayer({
  id: 'parcels',
  data: 'pmtiles://https://cdn.mygspot.com/tiles/parcels_tx.pmtiles',
  // ... rest of config
})
```

---

## Resource Requirements

### Storage
| Stage | Size |
|-------|------|
| Raw GDB download | 5-8 GB |
| PostGIS database | 15-20 GB |
| GeoJSON export | 10-15 GB |
| MBTiles | 2-5 GB |
| PMTiles | 1-3 GB |
| **CDN hosting** | **1-3 GB** |

### Processing Time (Apple Silicon M1/M2)
| Step | Duration |
|------|----------|
| Download | 10-30 min |
| Load to PostGIS | 20-40 min |
| Export GeoJSON | 15-30 min |
| Generate tiles | 30-60 min |
| Convert PMTiles | 5-10 min |
| **Total** | **~2-3 hours** |

### Monthly Costs
| Service | Cost |
|---------|------|
| Cloudflare R2 (3GB) | ~$0.05/mo |
| R2 egress | $0 |
| Or: S3 (3GB) | ~$0.07/mo |
| CloudFront egress | ~$10-50/mo |

---

## Hybrid Approach (Recommended)

Use both approaches for best user experience:

1. **CDN Tiles (Primary):** Fast display of parcel boundaries
2. **TNRIS API (On-Click):** Fetch detailed property data when user clicks

```typescript
// Display from tiles
const parcelLayer = new MVTLayer({
  data: 'pmtiles://https://cdn.mygspot.com/tiles/parcels_tx.pmtiles',
  pickable: true,
  onClick: async ({ object, coordinate }) => {
    // Fetch full details from TNRIS API
    const details = await queryParcelAtPoint(coordinate[0], coordinate[1]);
    showParcelDetails(details);
  }
});
```

**Benefits:**
- Fast tile display from CDN
- Fresh property details on click
- Best of both worlds

---

## Update Schedule

TNRIS updates quarterly. Recommended workflow:

1. Subscribe to TNRIS update notifications
2. On new release:
   - Download new dataset
   - Run tile generation pipeline
   - Deploy new PMTiles to CDN
   - Old tiles automatically replaced

**Automation Script:**
```bash
#!/bin/bash
# quarterly_update.sh

# 1. Download latest
./scripts/download_texas.sh ./downloads "$NEW_DOWNLOAD_URL"

# 2. Load to PostGIS
./scripts/load_texas.sh ./downloads/*.gdb

# 3. Export and generate tiles
./scripts/export_geojson.sh TX
./scripts/generate_tiles.sh

# 4. Convert and upload
pmtiles convert ./output/tiles/parcels_tx.mbtiles ./output/tiles/parcels_tx.pmtiles
wrangler r2 object put tiles/parcels_tx.pmtiles --file=./output/tiles/parcels_tx.pmtiles

echo "Texas parcel tiles updated!"
```

---

## Immediate Next Steps

1. **Get TNRIS download URL**
   - Visit https://tnris.org/stratmap/land-parcels
   - Find current statewide download link

2. **Set up processing environment**
   ```bash
   brew install gdal postgis tippecanoe
   npm install -g pmtiles
   createdb gspot
   psql gspot -c "CREATE EXTENSION postgis;"
   ```

3. **Run pipeline**
   ```bash
   cd data-pipeline
   ./scripts/download_texas.sh ./downloads "[URL]"
   ./scripts/load_texas.sh ./downloads/*.gdb
   ./scripts/export_geojson.sh TX
   ./scripts/generate_tiles.sh
   ```

4. **Test locally**
   ```bash
   npm install -g @maptiler/mbtiles-server
   mbtiles-server --port 8080 ./output/tiles
   # Update web app to use localhost:8080
   ```

5. **Deploy to CDN**
   - Convert to PMTiles
   - Upload to Cloudflare R2 or AWS S3

---

*Created: 2026-01-09*
*Phase: Property Lines for Texas*
