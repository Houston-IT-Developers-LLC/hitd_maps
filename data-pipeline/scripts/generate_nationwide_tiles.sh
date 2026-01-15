#!/bin/bash
# Generate nationwide PMTiles from all available GeoJSON parcel data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../output/geojson"
TILES_DIR="$SCRIPT_DIR/../output/tiles"
TEMP_DIR="$SCRIPT_DIR/../temp"

TIPPECANOE="/opt/homebrew/bin/tippecanoe"

mkdir -p "$TILES_DIR" "$TEMP_DIR"

echo "=== Generating Nationwide Parcel Tiles ==="
echo "Data directory: $DATA_DIR"
echo ""

# Find all GeoJSON files
echo "Finding all GeoJSON files..."
GEOJSON_FILES=$(find "$DATA_DIR" -name "*.geojson" -type f | sort)
FILE_COUNT=$(echo "$GEOJSON_FILES" | wc -l | xargs)
echo "Found $FILE_COUNT GeoJSON files"
echo ""

# Calculate total size
TOTAL_SIZE=$(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)
echo "Total data size: $TOTAL_SIZE"
echo ""

# Generate tiles using tippecanoe
# Using line-delimited input for large datasets
echo "Generating vector tiles with tippecanoe..."
echo "This may take a while for large datasets..."
echo ""

# Create a file list for tippecanoe
FILE_LIST="$TEMP_DIR/geojson_files.txt"
echo "$GEOJSON_FILES" > "$FILE_LIST"

# Run tippecanoe with optimized settings for parcel data
# - Zoom 8-16 (parcels visible from regional to street level)
# - Drop densest parcels at lower zooms to reduce tile size
# - Coalesce for better rendering
# - Detect shared borders for cleaner polygon edges

$TIPPECANOE \
  -o "$TILES_DIR/parcels_nationwide.mbtiles" \
  -Z8 -z16 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --coalesce-densest-as-needed \
  --detect-shared-borders \
  --simplification=10 \
  -l parcels \
  --force \
  --read-parallel \
  $(cat "$FILE_LIST" | tr '\n' ' ')

echo ""
echo "MBTiles generated: $TILES_DIR/parcels_nationwide.mbtiles"

# Convert to PMTiles
echo ""
echo "Converting to PMTiles format..."

# Check if pmtiles CLI is available
if command -v pmtiles &> /dev/null; then
  pmtiles convert "$TILES_DIR/parcels_nationwide.mbtiles" "$TILES_DIR/parcels_nationwide.pmtiles"
  echo "PMTiles generated: $TILES_DIR/parcels_nationwide.pmtiles"
else
  echo "pmtiles CLI not found. MBTiles file is ready for conversion."
  echo "Install with: go install github.com/protomaps/go-pmtiles/cmd/pmtiles@latest"
fi

# Cleanup
rm -f "$FILE_LIST"

echo ""
echo "=== Done ==="
echo ""
echo "To serve tiles locally:"
echo "  python3 -m http.server 8080 --directory $TILES_DIR"
echo ""
echo "To upload to Cloudflare R2:"
echo "  aws s3 cp $TILES_DIR/parcels_nationwide.pmtiles s3://gspot-tiles/parcels/ --endpoint-url https://YOUR_ACCOUNT.r2.cloudflarestorage.com"
