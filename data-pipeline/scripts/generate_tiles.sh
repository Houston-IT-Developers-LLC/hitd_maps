#!/bin/bash
set -e

# ============================================================================
# Vector Tile Generation Script
# ============================================================================
# Generates MBTiles from GeoJSON using Tippecanoe.
# Produces optimized vector tiles for efficient map display.
# ============================================================================

INPUT_DIR="${1:-./data-pipeline/output/geojson}"
OUTPUT_DIR="${2:-./data-pipeline/output/tiles}"
STATE="${3:-}"  # Optional: generate for single state

echo "=============================================="
echo " Vector Tile Generation (Tippecanoe)"
echo "=============================================="
echo ""
echo "Input:      $INPUT_DIR"
echo "Output:     $OUTPUT_DIR"
if [ -n "$STATE" ]; then
  echo "State:      $STATE"
fi
echo ""

# ============================================================================
# Prerequisites Check
# ============================================================================

echo "Checking prerequisites..."

# Check Tippecanoe
if ! command -v tippecanoe >/dev/null 2>&1; then
  echo ""
  echo "ERROR: tippecanoe not found!"
  echo ""
  echo "Install Tippecanoe:"
  echo "  macOS:  brew install tippecanoe"
  echo "  Ubuntu: See https://github.com/felt/tippecanoe#installation"
  echo ""
  echo "Or build from source:"
  echo "  git clone https://github.com/felt/tippecanoe.git"
  echo "  cd tippecanoe && make -j && make install"
  echo ""
  exit 1
fi

echo "  tippecanoe: OK ($(tippecanoe --version 2>&1 | head -1))"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# ============================================================================
# Tile Generation Function
# ============================================================================

generate_state_tiles() {
  local state=$1
  local state_lower=$(echo "$state" | tr '[:upper:]' '[:lower:]')
  local input="$INPUT_DIR/parcels_${state_lower}.geojson"
  local output="$OUTPUT_DIR/parcels_${state_lower}.mbtiles"

  if [ ! -f "$input" ]; then
    echo "Skipping $state - no GeoJSON file found at $input"
    return
  fi

  echo "Generating tiles for ${state^^}..."
  echo "  Input: $input"
  echo "  Output: $output"

  # Tippecanoe with optimized settings for parcels
  tippecanoe \
    -o "$output" \
    -Z8 -z14 \
    --drop-densest-as-needed \
    --extend-zooms-if-still-dropping \
    --coalesce-densest-as-needed \
    --detect-shared-borders \
    --simplification=10 \
    -l "parcels_${state_lower}" \
    --force \
    "$input"

  # Show result
  if [ -f "$output" ]; then
    local size=$(ls -lh "$output" | awk '{print $5}')
    echo "  Generated: $output ($size)"
  else
    echo "  ERROR: Output file not created"
  fi

  echo ""
}

# Function to generate combined nationwide tiles
generate_nationwide() {
  echo "Generating nationwide combined tileset..."

  # Find all state GeoJSON files
  local inputs=$(find "$INPUT_DIR" -name "parcels_*.geojson" 2>/dev/null | sort)

  if [ -z "$inputs" ]; then
    echo "No GeoJSON files found in $INPUT_DIR"
    exit 1
  fi

  echo "Found input files:"
  for f in $inputs; do
    echo "  - $(basename $f)"
  done
  echo ""

  local output="$OUTPUT_DIR/parcels_usa.mbtiles"

  # Generate combined tiles
  # Use lower min zoom for nationwide view
  tippecanoe \
    -o "$output" \
    -Z5 -z14 \
    --drop-densest-as-needed \
    --extend-zooms-if-still-dropping \
    --coalesce-densest-as-needed \
    --detect-shared-borders \
    --simplification=10 \
    -l parcels \
    --force \
    $inputs

  if [ -f "$output" ]; then
    local size=$(ls -lh "$output" | awk '{print $5}')
    echo "Generated: $output ($size)"
  fi
}

# ============================================================================
# Main Execution
# ============================================================================

# Handle special flags
case "$1" in
  --nationwide|--usa)
    generate_nationwide
    ;;
  --help|-h)
    echo "Usage: $0 [input_dir] [output_dir] [state]"
    echo ""
    echo "Options:"
    echo "  --nationwide    Generate combined USA tileset"
    echo "  --help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Generate tiles for all states"
    echo "  $0 ./geojson ./tiles TX               # Generate tiles for Texas only"
    echo "  $0 --nationwide                       # Generate combined USA tileset"
    echo ""
    exit 0
    ;;
  *)
    if [ -n "$STATE" ]; then
      # Generate for single state
      generate_state_tiles "${STATE,,}"
    else
      # Generate for all available states
      echo "Processing all GeoJSON files in $INPUT_DIR..."
      echo ""

      found_files=0
      for geojson in "$INPUT_DIR"/parcels_*.geojson; do
        if [ -f "$geojson" ]; then
          found_files=1
          state=$(basename "$geojson" | sed 's/parcels_//' | sed 's/.geojson//')
          generate_state_tiles "$state"
        fi
      done

      if [ $found_files -eq 0 ]; then
        echo "No GeoJSON files found in $INPUT_DIR"
        echo ""
        echo "Generate GeoJSON first using:"
        echo "  ./scripts/export_geojson.sh"
        echo ""
        exit 1
      fi
    fi
    ;;
esac

# ============================================================================
# Summary
# ============================================================================

echo "=============================================="
echo " Tile Generation Complete - Summary"
echo "=============================================="
echo ""
echo "Output directory: $OUTPUT_DIR"
echo ""

if [ -d "$OUTPUT_DIR" ]; then
  echo "MBTiles files:"
  for mbtiles in "$OUTPUT_DIR"/*.mbtiles; do
    if [ -f "$mbtiles" ]; then
      echo "  $(basename $mbtiles): $(ls -lh "$mbtiles" | awk '{print $5}')"
    fi
  done 2>/dev/null || echo "  (no files)"
fi

echo ""
echo "=============================================="
echo " Next Steps"
echo "=============================================="
echo ""
echo "1. For development testing:"
echo "   npm install -g @maptiler/mbtiles-server"
echo "   mbtiles-server --port 8080 $OUTPUT_DIR"
echo ""
echo "2. For production (PMTiles on CDN):"
echo "   npm install -g pmtiles"
echo "   pmtiles convert parcels_tx.mbtiles parcels_tx.pmtiles"
echo "   # Upload to S3/CloudFront"
echo ""
echo "See docs/tile_serving.md for full serving options."
echo ""
echo "Done!"
