#!/bin/bash
# Reproject GeoJSON from source CRS to WGS84 (EPSG:4326) and rebuild PMTiles
# The Harris County data appears to be in a projected coordinate system

set -e

export AWS_ACCESS_KEY_ID="ecd653afe3300fdc045b9980df0dbb14"
export AWS_SECRET_ACCESS_KEY="c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_ENDPOINT="https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_BUCKET="gspot-tiles"

WORK_DIR="output"
mkdir -p "$WORK_DIR/geojson" "$WORK_DIR/pmtiles" "$WORK_DIR/wgs84" logs

# File to process
FILE_NAME="${1:-parcels_tx_harris}"
GEOJSON_FILE="$WORK_DIR/geojson/${FILE_NAME}.geojson"
WGS84_FILE="$WORK_DIR/wgs84/${FILE_NAME}_wgs84.geojson"
PMTILES_FILE="$WORK_DIR/pmtiles/${FILE_NAME}.pmtiles"

echo "=============================================="
echo "Reprojecting and rebuilding: $FILE_NAME"
echo "=============================================="

# Step 1: Download GeoJSON if not present
if [ ! -f "$GEOJSON_FILE" ]; then
    echo "[$(date +%H:%M:%S)] Downloading $FILE_NAME.geojson from R2..."
    aws s3 cp "s3://${R2_BUCKET}/parcels/${FILE_NAME}.geojson" "$GEOJSON_FILE" \
        --endpoint-url "$R2_ENDPOINT"
fi

echo "[$(date +%H:%M:%S)] GeoJSON file size: $(du -h "$GEOJSON_FILE" | cut -f1)"

# Step 2: Check current CRS and inspect data
echo "[$(date +%H:%M:%S)] Inspecting current coordinate system..."
ogrinfo -so "$GEOJSON_FILE" 2>/dev/null | head -30 || echo "ogrinfo not available, proceeding anyway"

# Get a sample of coordinates to understand the CRS
echo "[$(date +%H:%M:%S)] Sample coordinates from source:"
head -c 5000 "$GEOJSON_FILE" | grep -o '"coordinates":\s*\[\[\[[^]]*' | head -3 || true

# Step 3: Reproject to WGS84 (EPSG:4326)
# The coordinates 26-29, 76-77 suggest Texas State Plane coordinates in feet
# Texas South Central zone is EPSG:2278 (feet) or EPSG:32139 (meters)
echo "[$(date +%H:%M:%S)] Reprojecting to WGS84 (trying EPSG:2278 -> EPSG:4326)..."

if [ -f "$WGS84_FILE" ]; then
    echo "[$(date +%H:%M:%S)] WGS84 file already exists, skipping reprojection"
else
    # Try Texas State Plane South Central (feet) - EPSG:2278
    ogr2ogr -f GeoJSON \
        -s_srs EPSG:2278 \
        -t_srs EPSG:4326 \
        "$WGS84_FILE" \
        "$GEOJSON_FILE" \
        -progress 2>&1 | tee "logs/${FILE_NAME}_reproject.log"
fi

# Verify the reprojection worked
echo "[$(date +%H:%M:%S)] Verifying reprojected coordinates..."
head -c 5000 "$WGS84_FILE" | grep -o '"coordinates":\s*\[\[\[[^]]*' | head -3 || true

# Step 4: Rebuild PMTiles from reprojected GeoJSON
echo "[$(date +%H:%M:%S)] Building PMTiles from reprojected GeoJSON..."
rm -f "$PMTILES_FILE"  # Remove old file

tippecanoe -z14 -o "$PMTILES_FILE" "$WGS84_FILE" \
    --drop-densest-as-needed \
    --extend-zooms-if-still-dropping \
    -l "${FILE_NAME}" \
    --force 2>&1 | tee "logs/${FILE_NAME}_tippecanoe.log"

echo "[$(date +%H:%M:%S)] PMTiles file size: $(du -h "$PMTILES_FILE" | cut -f1)"

# Step 5: Verify PMTiles bounds
echo "[$(date +%H:%M:%S)] Verifying PMTiles bounds..."
tippecanoe-decode --stats "$PMTILES_FILE" 2>/dev/null | head -20 || pmtiles show "$PMTILES_FILE" 2>/dev/null | head -20 || echo "Could not verify bounds"

# Step 6: Upload to R2
echo "[$(date +%H:%M:%S)] Uploading corrected PMTiles to R2..."
aws s3 cp "$PMTILES_FILE" "s3://${R2_BUCKET}/parcels/${FILE_NAME}.pmtiles" \
    --endpoint-url "$R2_ENDPOINT"

echo ""
echo "=============================================="
echo "Complete! $FILE_NAME has been reprojected and uploaded"
echo "=============================================="
echo ""
echo "Test URL: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/${FILE_NAME}.pmtiles"
