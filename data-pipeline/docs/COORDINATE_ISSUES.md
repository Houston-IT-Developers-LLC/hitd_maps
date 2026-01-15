# Coordinate System Issues and Fixes

## Overview

When processing county parcel data for PMTiles, we encountered coordinate system issues that caused parcels to appear in the wrong location (ocean instead of Texas).

## Problem Description

### Symptoms
- Parcels appearing in the ocean or completely wrong location
- PMTiles metadata showing incorrect bounds (e.g., `26.31, 76.78` instead of `-95.4, 29.7`)
- Very small PMTiles files (24KB instead of expected 200MB+)
- "Rendered parcel features: 0" in MapLibre debug output

### Root Cause
County GIS data is often stored in **State Plane Coordinate System** (feet), not WGS84 (degrees). For Texas counties, common projections include:

| EPSG Code | Name | Coverage |
|-----------|------|----------|
| EPSG:2278 | NAD83 / Texas South Central (ftUS) | Houston, Austin area |
| EPSG:2277 | NAD83 / Texas Central (ftUS) | Dallas area |
| EPSG:2279 | NAD83 / Texas South (ftUS) | Rio Grande Valley |
| EPSG:32139 | NAD83 / Texas South Central (meters) | Same as 2278 but meters |

### How to Identify the Issue

1. **Check raw coordinate values in GeoJSON:**
   ```bash
   head -c 5000 parcels.geojson | grep -o '\[[-0-9.]*,[-0-9.]*\]' | head -5
   ```

2. **State Plane feet coordinates look like:**
   ```
   [3154733.9, 13922510.6]  # Large numbers in feet
   ```

3. **WGS84 coordinates look like:**
   ```
   [-95.3698, 29.7604]  # Longitude/Latitude in degrees
   ```

4. **Check PMTiles bounds after generation:**
   ```bash
   pmtiles show parcels.pmtiles
   # Look at "bounds" - should be reasonable lat/lng values
   ```

## Solution

### Step 1: Identify Source Projection

For Texas counties, start with EPSG:2278 (Texas South Central feet). If coordinates still appear wrong, try:
- EPSG:2277 (Texas Central)
- EPSG:2279 (Texas South)

### Step 2: Transform with ogr2ogr

```bash
# Transform from State Plane feet to WGS84
ogr2ogr -f GeoJSON \
    -s_srs EPSG:2278 \
    -t_srs EPSG:4326 \
    output_wgs84.geojson \
    input_stateplane.geojson
```

### Step 3: Verify Transformation

```bash
# Check first few coordinates
head -c 5000 output_wgs84.geojson | grep -o '\[-[0-9.]*,[0-9.]*\]' | head -5
# Should show: [-95.xxx, 29.xxx] for Houston area
```

### Step 4: Generate PMTiles

```bash
tippecanoe -z14 -Z10 --drop-densest-as-needed \
    -o parcels.pmtiles \
    -l parcels_layer_name \
    output_wgs84.geojson
```

### Step 5: Verify PMTiles Bounds

```bash
pmtiles show parcels.pmtiles
# Bounds should show Houston area: approximately
# (-95.96, 29.50) to (-94.91, 30.17) for Harris County
```

## Common Mistakes to Avoid

### 1. Don't manually adjust coordinates
We initially tried subtracting 172.5 from longitude values. This was wrong - the data needed proper projection transformation, not arithmetic adjustment.

### 2. Don't assume GeoJSON is always WGS84
Many GIS sources export GeoJSON in their native projection (State Plane, UTM, etc.) even though GeoJSON spec recommends WGS84.

### 3. Don't skip verification
Always check PMTiles bounds after generation. A 24KB file when expecting 200MB+ indicates coordinate issues.

## Quick Reference: Texas County Projections

| Region | EPSG | Counties |
|--------|------|----------|
| South Central | 2278 | Harris, Fort Bend, Galveston, Brazoria, Montgomery, etc. |
| Central | 2277 | Dallas, Tarrant, Collin, Denton, Travis, Williamson |
| South | 2279 | Cameron, Hidalgo, Webb, Starr |
| North Central | 2276 | Lubbock, Amarillo area |

## Automation Script

For bulk processing, use this pattern:

```bash
#!/bin/bash
# reproject_and_convert.sh

INPUT=$1
OUTPUT_NAME=$2
EPSG=${3:-2278}  # Default to Texas South Central

# Step 1: Reproject
ogr2ogr -f GeoJSON \
    -s_srs EPSG:$EPSG \
    -t_srs EPSG:4326 \
    temp_wgs84.geojson \
    "$INPUT"

# Step 2: Verify bounds (should be reasonable lat/lng)
echo "Checking coordinates..."
head -c 5000 temp_wgs84.geojson | grep -o '\[-[0-9.]*,[0-9.]*\]' | head -3

# Step 3: Generate PMTiles
tippecanoe -z14 -Z10 --drop-densest-as-needed \
    -o "${OUTPUT_NAME}.pmtiles" \
    -l "$OUTPUT_NAME" \
    temp_wgs84.geojson

# Step 4: Verify
pmtiles show "${OUTPUT_NAME}.pmtiles"

rm temp_wgs84.geojson
echo "Done: ${OUTPUT_NAME}.pmtiles"
```

## Troubleshooting Checklist

- [ ] Source GeoJSON coordinates checked (State Plane vs WGS84?)
- [ ] Correct EPSG code identified for the county
- [ ] ogr2ogr transformation applied with `-s_srs` and `-t_srs`
- [ ] Output coordinates verified (should be negative longitude, positive latitude for Texas)
- [ ] PMTiles bounds checked with `pmtiles show`
- [ ] PMTiles file size reasonable (not just a few KB)
- [ ] Map source-layer name matches tippecanoe layer name
