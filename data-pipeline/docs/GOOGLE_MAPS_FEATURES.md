# Building a Google Maps Alternative with Self-Hosted Data

## Current Status ✅

We have:
- **Basemap**: Protomaps planet.pmtiles (110GB) - roads, water, parks, buildings, place labels
- **Parcels**: Harris County property boundaries with owner/value data
  - Fixed: State Plane (EPSG:2278) → WGS84 (EPSG:4326) transformation
  - See [COORDINATE_ISSUES.md](./COORDINATE_ISSUES.md) for details
- **Hosting**: Cloudflare R2 (zero egress fees)
- **Rendering**: MapLibre GL JS
- **Interactive Features**:
  - POI labels (hospitals, schools, restaurants, shops, gas stations)
  - 3D building extrusions (toggle on/off)
  - Terrain hillshade overlay (toggle on/off)
  - Parcel click popups with property details

## What Google Maps Has (and how we can replicate)

### 1. Points of Interest (POIs) 🏪
**What it is**: Restaurants, gas stations, shops, ATMs, hospitals, etc.

**Data Sources** (Free/Open):
- **OpenStreetMap** - Already in Protomaps, just need to style POI layer
- **Overture Maps** - Microsoft/Meta/Amazon backed, high quality POIs
  - Download: https://overturemaps.org/download/
  - ~50GB for full planet, can filter to Texas only
- **Foursquare Open Source Places** - 100M+ POIs
  - https://opensource.foursquare.com/os-places/

**Implementation**:
```bash
# Download Overture POIs for Texas
overturemaps download --theme=places --bbox=-106.6,25.8,-93.5,36.5 -f geoparquet -o texas_pois.parquet
# Convert to GeoJSON then PMTiles
ogr2ogr -f GeoJSON texas_pois.geojson texas_pois.parquet
tippecanoe -z14 -o pois_texas.pmtiles texas_pois.geojson -l pois
```

### 2. Satellite/Aerial Imagery 🛰️
**What it is**: Bird's eye view photography

**Data Sources** (Free):
- **USGS/NAIP** - US aerial imagery, 1m resolution, updated every 2-3 years
  - https://earthexplorer.usgs.gov/
  - Texas coverage available
- **Sentinel-2** - ESA satellite, 10m resolution, updated frequently
  - https://scihub.copernicus.eu/
- **Mapbox Satellite** - Free tier available (limited)

**Implementation**: Convert to MBTiles/PMTiles raster format
```bash
# Using GDAL to create tiles from GeoTIFF
gdal2tiles.py --zoom=10-18 naip_texas.tif ./satellite_tiles/
# Or use rio-mbtiles for cloud-optimized approach
```

### 3. Street View / 360° Imagery 📷
**What it is**: Ground-level panoramic photos

**Data Sources**:
- **Mapillary** (Meta) - Crowdsourced street-level imagery, FREE API
  - https://www.mapillary.com/
  - Cover most major roads
- **OpenStreetCam** - Community street imagery
- **DIY**: Collect with GoPro Max/Insta360 + upload to Mapillary

### 4. Traffic Data 🚗
**What it is**: Real-time congestion, incidents

**Data Sources**:
- **HERE Traffic** - Commercial but has free tier
- **TomTom Traffic** - Commercial
- **Waze** (Google-owned) - No public API
- **State DOT feeds** - Texas has free traffic camera/incident feeds
  - https://www.drivetexas.org/

### 5. Transit/Public Transportation 🚌
**What it is**: Bus routes, train lines, schedules

**Data Sources** (FREE):
- **GTFS feeds** - Standard transit data format
  - Houston METRO: https://www.ridemetro.org/developers
  - Most US transit agencies publish GTFS
- **Transitland** - Aggregated GTFS for thousands of agencies
  - https://www.transit.land/

### 6. Terrain/Elevation 🏔️
**What it is**: Hillshading, elevation contours, 3D terrain

**Data Sources** (FREE):
- **USGS 3DEP** - High resolution elevation for US
- **SRTM** - 30m global elevation
- **Mapzen Terrain Tiles** - Pre-rendered terrain tiles
  - Now hosted by AWS/Stamen

**Implementation**:
```bash
# Generate hillshade from DEM
gdaldem hillshade dem.tif hillshade.tif
# Create terrain RGB tiles for MapLibre 3D terrain
rio rgbify -b -10000 -i 0.1 dem.tif terrain-rgb.tif
```

### 7. Address Search / Geocoding 🔍
**What it is**: Search "123 Main St" → get coordinates

**Data Sources** (FREE):
- **Nominatim** - OpenStreetMap geocoder, can self-host
- **Pelias** - Open source geocoder, used by Mapzen
- **Photon** - Fast OSM geocoder
- **Our parcel data!** - We have all Harris County addresses

### 8. Routing / Directions 🗺️
**What it is**: Turn-by-turn navigation

**Data Sources** (FREE to self-host):
- **OSRM** - OpenStreetMap Routing Machine
  - http://project-osrm.org/
  - Can self-host, very fast
- **Valhalla** - Mapzen's router, now open source
- **GraphHopper** - Java-based, feature-rich

### 9. 3D Buildings 🏢
**What it is**: Extruded building footprints

**Already have this!** Protomaps includes building footprints. Just need to add:
```javascript
{
    id: "buildings-3d",
    type: "fill-extrusion",
    source: "protomaps",
    "source-layer": "buildings",
    paint: {
        "fill-extrusion-color": "#ddd",
        "fill-extrusion-height": ["get", "height"],
        "fill-extrusion-base": 0
    }
}
```

## Priority Implementation Order

### Phase 1 - Quick Wins (Already have data)
1. ✅ Basemap with roads, water, parks
2. ✅ Property parcels (Harris County - coordinate transform fixed)
3. ✅ POIs from Protomaps (styled: hospitals, schools, restaurants, shops, fuel)
4. ✅ 3D buildings (fill-extrusion layer with toggle)
5. ✅ Terrain/hillshade (Stadia Maps tiles with toggle)
6. 🔲 Address search using parcel data

### Phase 2 - Additional Free Data
1. 🔲 Download Overture Maps POIs for Texas (~2GB)
2. 🔲 Add USGS aerial imagery for hunting areas
3. 🔲 Integrate Mapillary street view

### Phase 3 - Advanced Features
1. 🔲 Self-host OSRM for routing
2. ✅ Add Houston METRO transit data
   - URL: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/transit/houston_metro.pmtiles
   - Features: 8,859 stops + 347 route shapes
3. 🔲 Real-time traffic from TxDOT

## Storage Estimates

| Data Layer | Size | Update Frequency |
|------------|------|------------------|
| Protomaps basemap | 110GB | Monthly |
| Texas parcels (all counties) | ~50GB | Quarterly |
| Texas POIs (Overture) | ~2GB | Monthly |
| Texas aerial imagery | ~500GB | Yearly |
| Texas terrain/elevation | 2.3GB | Never |
| Houston GTFS transit | 1MB | Weekly |

**Total for Texas-focused app**: ~700GB
**Monthly R2 cost at $0.015/GB**: ~$10.50/month storage

## R2 Data URLs

All data is hosted on Cloudflare R2 at: `https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/`

| Data Layer | URL | Size |
|------------|-----|------|
| Basemap | `basemap/planet.pmtiles` | 109GB |
| Parcels (all 50 states) | `parcels/` | 127GB |
| POIs | `pois/` | 4GB |
| Roads | `roads/` | 18GB |
| Addresses | `addresses/` | 7GB |
| **Terrain RGB (Texas)** | `terrain/terrain-rgb-texas.pmtiles` | 2.3GB |
| **Houston Transit** | `transit/houston_metro.pmtiles` | 1MB |

## Quick Start - Add POIs Now

The Protomaps basemap already has POI data! Let me add POI styling:

```javascript
// Add to map style layers array:
{
    id: "pois-icons",
    type: "symbol",
    source: "protomaps",
    "source-layer": "pois",
    minzoom: 14,
    layout: {
        "icon-image": ["get", "pmap:kind"],
        "text-field": ["get", "name"],
        "text-size": 10,
        "text-offset": [0, 1.5],
        "text-anchor": "top"
    },
    paint: {
        "text-color": "#666",
        "text-halo-color": "#fff",
        "text-halo-width": 1
    }
}
```
