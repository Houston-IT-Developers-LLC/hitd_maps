# Tile Serving Options

Generated MBTiles can be served in several ways depending on infrastructure needs.

## Overview

| Option | Best For | Complexity | Cost |
|--------|----------|------------|------|
| PMTiles on CDN | Production | Low | Low |
| mbtiles-server | Development | Low | Free |
| Tegola | Dynamic data | Medium | Medium |
| PostGIS ST_AsMVT | Real-time | High | Varies |

## Option 1: PMTiles on CDN (Recommended for Production)

Convert MBTiles to PMTiles and serve directly from a CDN. No tile server required.

### What is PMTiles?

PMTiles is a single-file format that supports HTTP range requests, allowing browsers to fetch only the tiles they need directly from cloud storage.

### Setup

```bash
# Install pmtiles CLI
npm install -g pmtiles

# Convert MBTiles to PMTiles
pmtiles convert parcels_tx.mbtiles parcels_tx.pmtiles

# Upload to cloud storage
aws s3 cp parcels_tx.pmtiles s3://your-bucket/tiles/
# or
gsutil cp parcels_tx.pmtiles gs://your-bucket/tiles/
```

### Advantages

- No tile server needed
- Direct CDN serving with range requests
- Single file per tileset
- Supported by MapLibre GL JS, Mapbox GL JS
- Very low cost (just storage + bandwidth)

### CDN Configuration

For AWS CloudFront/S3:
- Enable CORS
- Enable range request support (default)
- Set Content-Type: `application/x-protobuf`

For Cloudflare R2:
- Built-in range request support
- No egress fees

## Option 2: mbtiles-server (Development)

Quick local testing with no configuration.

### Setup

```bash
# Install
npm install -g @maptiler/mbtiles-server

# Run
mbtiles-server --port 8080 ./data-pipeline/output/tiles
```

### Access

Tiles available at: `http://localhost:8080/{tileset}/{z}/{x}/{y}.pbf`

Example: `http://localhost:8080/parcels_tx/12/1024/2048.pbf`

### Advantages

- Zero configuration
- Good for local development
- Supports multiple MBTiles files

### Disadvantages

- Not production-ready
- No caching
- Single-threaded

## Option 3: Tegola (Production - Dynamic)

PostGIS-backed dynamic tile server for frequently updated data.

### Setup

```yaml
# tegola.toml
[webserver]
port = ":8080"

[cache]
type = "file"
basepath = "/tmp/tegola-cache"

[[providers]]
name = "postgis"
type = "postgis"
host = "localhost"
port = 5432
database = "gspot"
user = "postgres"
password = "postgres"
srid = 4326

  [[providers.layers]]
  name = "parcels"
  geometry_fieldname = "geom"
  id_fieldname = "gid"
  sql = """
    SELECT gid, apn, owner_name, county, acres, geom
    FROM parcels
    WHERE geom && !BBOX!
  """

[[maps]]
name = "parcels"
  [[maps.layers]]
  provider_layer = "postgis.parcels"
  min_zoom = 8
  max_zoom = 14
```

### Run

```bash
# Docker
docker run -v $(pwd)/tegola.toml:/opt/tegola.toml \
  gospatial/tegola serve --config /opt/tegola.toml

# Or binary
tegola serve --config tegola.toml
```

### Advantages

- Dynamic tile generation from PostGIS
- Automatic cache invalidation
- Good for frequently updated data

### Disadvantages

- Requires running service
- Higher infrastructure cost
- Slower than pre-generated tiles

## Option 4: PostGIS ST_AsMVT (Real-time)

Generate tiles on-the-fly directly from PostGIS.

### SQL Function

```sql
CREATE OR REPLACE FUNCTION get_parcel_tile(z int, x int, y int)
RETURNS bytea AS $$
  SELECT ST_AsMVT(tile, 'parcels', 4096, 'geom')
  FROM (
    SELECT
      gid,
      apn,
      owner_name,
      county,
      acres,
      ST_AsMVTGeom(
        geom,
        ST_TileEnvelope(z, x, y),
        4096,
        64,
        true
      ) AS geom
    FROM parcels
    WHERE geom && ST_TileEnvelope(z, x, y)
  ) AS tile
  WHERE geom IS NOT NULL;
$$ LANGUAGE SQL STABLE PARALLEL SAFE;
```

### API Endpoint (Next.js)

```typescript
// pages/api/tiles/[z]/[x]/[y].ts
import { Pool } from 'pg';

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

export default async function handler(req, res) {
  const { z, x, y } = req.query;

  const result = await pool.query(
    'SELECT get_parcel_tile($1, $2, $3)',
    [parseInt(z), parseInt(x), parseInt(y)]
  );

  const tile = result.rows[0].get_parcel_tile;

  res.setHeader('Content-Type', 'application/x-protobuf');
  res.setHeader('Cache-Control', 'public, max-age=3600');
  res.send(tile);
}
```

### Advantages

- Always current data
- No pre-generation needed
- Good for small datasets

### Disadvantages

- Database load on every request
- Slower than pre-generated
- Needs caching layer for scale

## Client Integration

### Flutter (mapbox_gl)

```dart
// Add vector tile source
await mapController.addSource(
  'parcels',
  VectorSourceProperties(
    tiles: ['https://cdn.example.com/tiles/parcels/{z}/{x}/{y}.pbf'],
    minzoom: 8,
    maxzoom: 14,
  ),
);

// Add fill layer for parcels
await mapController.addLayer(
  'parcels',
  'parcels-fill',
  FillLayerProperties(
    fillColor: '#4169E1',
    fillOpacity: 0.25,
  ),
  sourceLayer: 'parcels_tx',
);

// Add outline layer
await mapController.addLayer(
  'parcels',
  'parcels-outline',
  LineLayerProperties(
    lineColor: '#2B4799',
    lineWidth: 1,
  ),
  sourceLayer: 'parcels_tx',
);
```

### Flutter (flutter_map with vector_map_tiles)

```dart
import 'package:vector_map_tiles/vector_map_tiles.dart';

VectorTileLayer(
  tileProviders: TileProviders({
    'parcels': MemoryCacheVectorTileProvider(
      delegate: NetworkVectorTileProvider(
        urlTemplate: 'https://cdn.example.com/tiles/parcels/{z}/{x}/{y}.pbf',
        maximumZoom: 14,
      ),
      maxSizeBytes: 1024 * 1024 * 50, // 50MB cache
    ),
  }),
  theme: ProvidedThemes.parcelTheme(), // Custom theme
)
```

### Web (MapLibre GL JS with PMTiles)

```javascript
import maplibregl from 'maplibre-gl';
import { Protocol } from 'pmtiles';

// Register PMTiles protocol
let protocol = new Protocol();
maplibregl.addProtocol('pmtiles', protocol.tile);

const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    sources: {
      parcels: {
        type: 'vector',
        url: 'pmtiles://https://cdn.example.com/tiles/parcels.pmtiles'
      }
    },
    layers: [
      {
        id: 'parcels-fill',
        type: 'fill',
        source: 'parcels',
        'source-layer': 'parcels_tx',
        paint: {
          'fill-color': '#4169E1',
          'fill-opacity': 0.25
        }
      },
      {
        id: 'parcels-outline',
        type: 'line',
        source: 'parcels',
        'source-layer': 'parcels_tx',
        paint: {
          'line-color': '#2B4799',
          'line-width': 1
        }
      }
    ]
  }
});

// Click handler for parcel info
map.on('click', 'parcels-fill', (e) => {
  const properties = e.features[0].properties;
  new maplibregl.Popup()
    .setLngLat(e.lngLat)
    .setHTML(`
      <strong>${properties.owner_name || 'Unknown Owner'}</strong><br>
      APN: ${properties.apn}<br>
      County: ${properties.county}<br>
      Acres: ${properties.acres?.toFixed(2) || 'N/A'}
    `)
    .addTo(map);
});
```

### Web (Google Maps with Deck.gl)

```javascript
import { GoogleMapsOverlay } from '@deck.gl/google-maps';
import { MVTLayer } from '@deck.gl/geo-layers';

const overlay = new GoogleMapsOverlay({
  layers: [
    new MVTLayer({
      id: 'parcels',
      data: 'https://cdn.example.com/tiles/parcels/{z}/{x}/{y}.pbf',
      minZoom: 8,
      maxZoom: 14,
      getFillColor: [65, 105, 225, 64],
      getLineColor: [43, 71, 153],
      getLineWidth: 1,
      pickable: true,
      onClick: ({ object }) => {
        console.log('Clicked parcel:', object.properties);
      }
    })
  ]
});

overlay.setMap(googleMap);
```

## Recommendation for My G Spot Outdoors

### Development
Use `mbtiles-server` for quick local testing.

### Production
Use **PMTiles on CDN** (Cloudflare R2 or AWS CloudFront):

1. Lowest infrastructure complexity
2. Lowest ongoing cost
3. Best performance (edge caching)
4. No servers to maintain

### Workflow

```
PostGIS → GeoJSON → MBTiles → PMTiles → CDN → Client
   ↓         ↓          ↓          ↓        ↓
export   tippecanoe  pmtiles   upload   MapLibre
```

---

*Last updated: 2026-01-10*
