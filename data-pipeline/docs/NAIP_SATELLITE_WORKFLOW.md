# NAIP Satellite Imagery Workflow

## Overview

This document describes the workflow for downloading, processing, and uploading NASA NAIP (National Agriculture Imagery Program) satellite imagery for use in the GSpot Outdoors app.

## Data Source

**NAIP** provides high-resolution (0.6m-1m) aerial imagery covering the continental United States during agricultural growing seasons ("leaf-on" imagery).

### Access Methods

1. **Microsoft Planetary Computer STAC API** (Recommended)
   - URL: `https://planetarycomputer.microsoft.com/api/stac/v1`
   - Collection: `naip`
   - Free access, no authentication required
   - Data stored on Azure Blob Storage

2. **AWS Registry of Open Data**
   - S3 buckets: `naip-source`, `naip-visualization`, `naip-analytic`
   - May require requester-pays access

3. **USGS EarthExplorer**
   - https://earthexplorer.usgs.gov/
   - Requires free account

## Pipeline Steps

### 1. Search for Imagery
```python
from pystac_client import Client

catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
search = catalog.search(
    collections=["naip"],
    bbox=[-95.8, 29.5, -95.0, 30.1],  # Houston area
    datetime="2022-01-01/2023-12-31",
    max_items=50
)
```

### 2. Download Images
Images are Cloud Optimized GeoTIFFs (COGs) accessible via HTTPS:
```python
import requests
for item in search.items():
    url = item.assets['image'].href
    response = requests.get(url, stream=True)
    # Save to local file
```

### 3. Create Mosaic
```bash
gdalbuildvrt output/mosaic.vrt raw/*.tif
```

### 4. Reproject to Web Mercator
```bash
gdalwarp -t_srs EPSG:3857 \
    -r bilinear \
    -co COMPRESS=JPEG \
    -co JPEG_QUALITY=85 \
    -co TILED=YES \
    output/mosaic.vrt \
    output/mosaic_3857.tif
```

### 5. Add Overviews
```bash
gdaladdo -r average output/mosaic_3857.tif 2 4 8 16 32
```

### 6. Create Tiles
```bash
gdal2tiles.py --zoom=10-16 --xyz output/mosaic_3857.tif output/tiles
```

### 7. Package as MBTiles
```bash
mb-util --scheme=xyz output/tiles output/satellite.mbtiles
```

### 8. Convert to PMTiles
```bash
pmtiles convert output/satellite.mbtiles output/satellite.pmtiles
```

### 9. Upload to R2
```python
import boto3
s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT, ...)
s3.upload_file('satellite.pmtiles', 'gspot-tiles', 'satellite/texas_naip.pmtiles')
```

## Current Data

### Houston Test Area
- **Bounding Box**: -95.8, 29.5, -95.0, 30.1
- **Images**: 5 NAIP tiles from 2022
- **Zoom Levels**: 10-15
- **R2 Location**: `satellite/texas_naip_houston.pmtiles`
- **Public URL**: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/satellite/texas_naip_houston.pmtiles
- **File Size**: 40MB

## Scaling Considerations

### Full Texas Coverage
- Texas has ~23,500 NAIP tiles
- Estimated raw size: 10-15 TB
- Estimated PMTiles: 50-100 GB after compression
- Recommend: Download in batches by region/county

### Recommended Strategy
1. Start with hunting-relevant areas (rural counties with public lands)
2. Skip urban areas initially
3. Use zoom 10-16 (0.6m imagery works well through z16)
4. Process in parallel (4-8 threads)

## Storage Costs

### Cloudflare R2
- Storage: $0.015/GB/month
- Egress: Free (no bandwidth charges)
- Estimated Texas full: 100GB = $1.50/month

## Scripts

### Search Script
`data-pipeline/downloads/satellite/search_naip.py`

### Download Script
`data-pipeline/downloads/satellite/download_naip.py`

### Processing Script
`data-pipeline/downloads/satellite/process_naip.sh`

### Upload Script
`data-pipeline/downloads/satellite/upload_to_r2.py`

## Usage in Flutter App

```dart
// Add satellite layer to MapLibre
MapLibreMap(
  styleString: 'mapbox://styles/mapbox/satellite-v9',  // Or custom style
  // Add PMTiles source
  sources: [
    RasterSource(
      id: 'naip-satellite',
      tiles: ['https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/satellite/texas_naip_houston.pmtiles/{z}/{x}/{y}'],
      tileSize: 256,
    ),
  ],
)
```

## Next Steps

1. [ ] Expand coverage to all Texas hunting areas
2. [ ] Create county-by-county download script
3. [ ] Add progress tracking and resume capability
4. [ ] Implement automatic tile index generation
5. [ ] Add metadata (capture date, resolution) to tiles
