#!/bin/bash
set -e

# ============================================================================
# PostGIS to GeoJSON Export Script
# ============================================================================
# Exports parcel data from PostGIS to GeoJSON format for tile generation.
# Produces one file per state to keep file sizes manageable.
# ============================================================================

PG_CONN="${1:-postgresql://postgres:postgres@localhost:5432/gspot}"
OUTPUT_DIR="${2:-./data-pipeline/output/geojson}"
STATE="${3:-}"  # Optional: export single state

echo "=============================================="
echo " PostGIS to GeoJSON Export"
echo "=============================================="
echo ""
echo "Database:   $PG_CONN"
echo "Output:     $OUTPUT_DIR"
if [ -n "$STATE" ]; then
  echo "State:      $STATE"
fi
echo ""

# ============================================================================
# Prerequisites Check
# ============================================================================

echo "Checking prerequisites..."

# Check ogr2ogr (GDAL)
if ! command -v ogr2ogr >/dev/null 2>&1; then
  echo ""
  echo "ERROR: ogr2ogr not found!"
  echo ""
  echo "Install GDAL:"
  echo "  macOS:  brew install gdal"
  echo "  Ubuntu: apt-get install gdal-bin"
  echo ""
  exit 1
fi

# Check psql
if ! command -v psql >/dev/null 2>&1; then
  echo ""
  echo "ERROR: psql not found!"
  echo ""
  echo "Install PostgreSQL client or ensure it's in PATH"
  echo ""
  exit 1
fi

echo "  ogr2ogr: OK"
echo "  psql:    OK"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# ============================================================================
# Export Function
# ============================================================================

export_state() {
  local state=$1
  local state_lower=$(echo "$state" | tr '[:upper:]' '[:lower:]')
  local output_file="$OUTPUT_DIR/parcels_${state_lower}.geojson"

  echo "Exporting $state parcels..."

  # Export with selected fields for tile display
  # Keep tiles lightweight - not all fields needed for display
  ogr2ogr -f GeoJSON \
    "$output_file" \
    PG:"$PG_CONN" \
    -sql "SELECT
            gid,
            apn,
            owner_name,
            county,
            acres,
            geom
          FROM parcels
          WHERE state = '${state}'" \
    -lco RFC7946=YES \
    -progress

  # Show file size
  if [ -f "$output_file" ]; then
    local size=$(ls -lh "$output_file" | awk '{print $5}')
    local count=$(grep -c '"type":"Feature"' "$output_file" 2>/dev/null || echo "0")
    echo "  Output: $output_file"
    echo "  Size: $size"
    echo "  Features: ~$count"
  else
    echo "  WARNING: Output file not created"
  fi

  echo ""
}

# ============================================================================
# Main Export
# ============================================================================

if [ -n "$STATE" ]; then
  # Export single state
  echo "Exporting single state: $STATE"
  echo ""
  export_state "$STATE"
else
  # Export all states with data
  echo "Finding states with parcel data..."

  STATES=$(psql "$PG_CONN" -t -c "SELECT DISTINCT state FROM parcels ORDER BY state" 2>/dev/null)

  if [ -z "$STATES" ]; then
    echo ""
    echo "No parcel data found in database."
    echo ""
    echo "Load parcel data first using:"
    echo "  ./scripts/load_texas.sh <gdb_path>"
    echo ""
    exit 1
  fi

  echo "Found states: $(echo $STATES | tr '\n' ' ')"
  echo ""

  for state in $STATES; do
    state=$(echo "$state" | tr -d ' ')  # Remove whitespace
    if [ -n "$state" ]; then
      export_state "$state"
    fi
  done
fi

# ============================================================================
# Summary
# ============================================================================

echo "=============================================="
echo " Export Complete - Summary"
echo "=============================================="
echo ""
echo "Output directory: $OUTPUT_DIR"
echo ""

if [ -d "$OUTPUT_DIR" ]; then
  echo "Files created:"
  ls -lh "$OUTPUT_DIR"/*.geojson 2>/dev/null || echo "  (no files)"
fi

echo ""
echo "Next step: Generate vector tiles with:"
echo "  ./scripts/generate_tiles.sh"
echo ""
echo "Done!"
