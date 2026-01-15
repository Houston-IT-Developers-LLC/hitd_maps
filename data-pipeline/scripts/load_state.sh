#!/bin/bash
set -e

# ============================================================================
# Generic State Parcel Loader
# ============================================================================
# Uses configuration from sources.json to load any state's parcel data.
# Handles varying field names across different state data sources.
# ============================================================================

STATE="${1:-}"
GDB_PATH="${2:-}"
PG_CONN="${3:-postgresql://postgres:postgres@localhost:5432/gspot}"
CONFIG_FILE="${4:-./data-pipeline/config/sources.json}"

# ============================================================================
# Usage
# ============================================================================

if [ -z "$STATE" ] || [ -z "$GDB_PATH" ]; then
  echo "=============================================="
  echo " Generic State Parcel Loader"
  echo "=============================================="
  echo ""
  echo "Usage: $0 <STATE_ABBR> <GDB_PATH> [PG_CONN] [CONFIG_FILE]"
  echo ""
  echo "Arguments:"
  echo "  STATE_ABBR   Two-letter state code (TX, WI, FL, etc.)"
  echo "  GDB_PATH     Path to geodatabase or shapefile"
  echo "  PG_CONN      PostgreSQL connection string (optional)"
  echo "  CONFIG_FILE  Path to sources.json (optional)"
  echo ""
  echo "Examples:"
  echo "  $0 WI ./downloads/wisconsin_parcels.gdb"
  echo "  $0 FL ./downloads/florida_parcels.gdb"
  echo "  $0 TX ./downloads/texas.gdb postgresql://user:pass@host:5432/db"
  echo ""
  exit 1
fi

STATE_UPPER=$(echo "$STATE" | tr '[:lower:]' '[:upper:]')
STATE_LOWER=$(echo "$STATE" | tr '[:upper:]' '[:lower:]')

echo "=============================================="
echo " Generic State Parcel Loader"
echo "=============================================="
echo ""
echo "State:      $STATE_UPPER"
echo "Input:      $GDB_PATH"
echo "Database:   $PG_CONN"
echo "Config:     $CONFIG_FILE"
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

# Check jq
if ! command -v jq >/dev/null 2>&1; then
  echo ""
  echo "ERROR: jq not found!"
  echo ""
  echo "Install jq:"
  echo "  macOS:  brew install jq"
  echo "  Ubuntu: apt-get install jq"
  echo ""
  exit 1
fi

# Check psql
if ! command -v psql >/dev/null 2>&1; then
  echo ""
  echo "ERROR: psql not found!"
  echo ""
  exit 1
fi

# Check input file/directory exists
if [ ! -e "$GDB_PATH" ]; then
  echo ""
  echo "ERROR: Input path not found: $GDB_PATH"
  echo ""
  exit 1
fi

echo "  ogr2ogr: OK"
echo "  jq:      OK"
echo "  psql:    OK"
echo "  Input:   OK"
echo ""

# ============================================================================
# Configuration Reading
# ============================================================================

echo "Reading configuration from sources.json..."

# Read state config
if [ -f "$CONFIG_FILE" ]; then
  STATE_CONFIG=$(jq -r ".states.${STATE_UPPER} // empty" "$CONFIG_FILE")
  LAYER_NAMES=$(jq -r ".states.${STATE_UPPER}.layer_names // [] | .[]" "$CONFIG_FILE" 2>/dev/null)
  SOURCE_NAME=$(jq -r ".states.${STATE_UPPER}.primary_source.name // \"state_${STATE_LOWER}\"" "$CONFIG_FILE" 2>/dev/null)
else
  echo "  WARNING: sources.json not found, using defaults"
  STATE_CONFIG=""
  LAYER_NAMES=""
  SOURCE_NAME="state_${STATE_LOWER}"
fi

echo "  Source: $SOURCE_NAME"
echo ""

# ============================================================================
# Layer Discovery
# ============================================================================

echo "Scanning input for layers..."
echo ""

# List available layers
ogrinfo -so "$GDB_PATH" 2>/dev/null | head -20

echo ""

# Try configured layer names first
LAYER_NAME=""
if [ -n "$LAYER_NAMES" ]; then
  for candidate in $LAYER_NAMES; do
    if ogrinfo -so "$GDB_PATH" "$candidate" >/dev/null 2>&1; then
      LAYER_NAME="$candidate"
      echo "Found configured layer: $LAYER_NAME"
      break
    fi
  done
fi

# If not found, try common patterns
if [ -z "$LAYER_NAME" ]; then
  echo "Trying common parcel layer patterns..."
  COMMON_NAMES=(
    "Parcels"
    "parcels"
    "PARCELS"
    "Land_Parcels"
    "land_parcels"
    "Parcel"
    "parcel"
    "Cadastral"
    "cadastral"
    "Tax_Parcels"
    "tax_parcels"
    "PropertyParcels"
  )

  for candidate in "${COMMON_NAMES[@]}"; do
    if ogrinfo -so "$GDB_PATH" "$candidate" >/dev/null 2>&1; then
      LAYER_NAME="$candidate"
      echo "Found layer: $LAYER_NAME"
      break
    fi
  done
fi

# Last resort - try to find any polygon layer
if [ -z "$LAYER_NAME" ]; then
  echo "Looking for polygon layers..."
  LAYER_NAME=$(ogrinfo -so "$GDB_PATH" | grep -i "polygon\|multi polygon" | head -1 | sed 's/^[0-9]*: //' | sed 's/ .*//')
fi

if [ -z "$LAYER_NAME" ]; then
  echo ""
  echo "ERROR: Could not auto-detect parcel layer"
  echo ""
  echo "Available layers:"
  ogrinfo -so "$GDB_PATH"
  echo ""
  echo "Please add layer_names to sources.json for state ${STATE_UPPER}"
  echo ""
  exit 1
fi

echo ""
echo "Using layer: $LAYER_NAME"
echo ""

# Show layer info
echo "Layer details:"
ogrinfo -so "$GDB_PATH" "$LAYER_NAME" 2>/dev/null | head -25
echo ""

# ============================================================================
# Load Raw Data
# ============================================================================

RAW_TABLE="parcels_${STATE_LOWER}_raw"

echo "=============================================="
echo " Step 1: Loading raw data to $RAW_TABLE"
echo "=============================================="
echo ""
echo "This may take several minutes for large datasets..."
echo ""

ogr2ogr -f PostgreSQL "$PG_CONN" "$GDB_PATH" "$LAYER_NAME" \
  -nln "$RAW_TABLE" \
  -nlt MULTIPOLYGON \
  -t_srs EPSG:4326 \
  -lco GEOMETRY_NAME=geom \
  -lco FID=gid \
  -lco PRECISION=NO \
  -overwrite \
  -progress

echo ""
echo "Raw data loaded to $RAW_TABLE"
echo ""

# Show sample columns
echo "Sample columns from raw data:"
psql "$PG_CONN" -c "SELECT column_name FROM information_schema.columns WHERE table_name = '$RAW_TABLE' LIMIT 20;"

# ============================================================================
# Normalize to Main Schema
# ============================================================================

echo ""
echo "=============================================="
echo " Step 2: Normalizing to parcels table"
echo "=============================================="
echo ""

# Build dynamic COALESCE expressions based on available columns
# This handles field name variations across states
psql "$PG_CONN" << SQL
-- Delete existing data for this state (clean re-import)
DELETE FROM parcels WHERE state = '${STATE_UPPER}';

-- Normalize and insert
-- Uses COALESCE to try multiple possible field names
INSERT INTO parcels (
  apn,
  owner_name,
  situs_address,
  city,
  state,
  county,
  acres,
  source,
  source_date,
  geom
)
SELECT
  -- APN: Try multiple field name variations
  COALESCE(
    NULLIF(prop_id::text, ''),
    NULLIF(parcel_id::text, ''),
    NULLIF(pin::text, ''),
    NULLIF(apn::text, ''),
    NULLIF(pid::text, ''),
    NULLIF(parcelid::text, ''),
    NULLIF(parcelnumb::text, ''),
    gid::text
  ) AS apn,

  -- Owner name
  COALESCE(
    NULLIF(owner_name::text, ''),
    NULLIF(owner::text, ''),
    NULLIF(owner1::text, ''),
    NULLIF(ownername::text, ''),
    NULLIF(ownernme1::text, ''),
    NULLIF(own_name::text, '')
  ) AS owner_name,

  -- Property address (situs)
  COALESCE(
    NULLIF(situs_addr::text, ''),
    NULLIF(situs_address::text, ''),
    NULLIF(address::text, ''),
    NULLIF(prop_addr::text, ''),
    NULLIF(physical_addr::text, ''),
    NULLIF(siteaddr::text, ''),
    NULLIF(siteaddress::text, '')
  ) AS situs_address,

  -- City
  COALESCE(
    NULLIF(situs_city::text, ''),
    NULLIF(city::text, ''),
    NULLIF(prop_city::text, ''),
    NULLIF(sitecity::text, '')
  ) AS city,

  -- State (always the current state)
  '${STATE_UPPER}' AS state,

  -- County
  COALESCE(
    NULLIF(county::text, ''),
    NULLIF(cnty_name::text, ''),
    NULLIF(county_name::text, ''),
    NULLIF(co_name::text, ''),
    NULLIF(cntyname::text, '')
  ) AS county,

  -- Acres (calculate from geometry if not available)
  COALESCE(
    acres::numeric(10,2),
    acreage::numeric(10,2),
    gisacres::numeric(10,2),
    (ST_Area(geom::geography) / 4046.86)::numeric(10,2)
  ) AS acres,

  -- Source tracking
  '${SOURCE_NAME}' AS source,
  CURRENT_DATE AS source_date,

  -- Geometry (already transformed to EPSG:4326)
  geom

FROM ${RAW_TABLE}
WHERE geom IS NOT NULL
  AND ST_IsValid(geom);

-- Log the import
INSERT INTO import_log (source, state, record_count, source_url)
SELECT
  '${SOURCE_NAME}',
  '${STATE_UPPER}',
  COUNT(*),
  NULL
FROM parcels
WHERE state = '${STATE_UPPER}' AND source = '${SOURCE_NAME}';

-- Report results
SELECT 'Loaded ' || COUNT(*) || ' ${STATE_UPPER} parcels' AS result
FROM parcels
WHERE state = '${STATE_UPPER}';
SQL

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "=============================================="
echo " Load Complete - Summary"
echo "=============================================="
echo ""

psql "$PG_CONN" << SQL
-- Total counts
SELECT
  state,
  COUNT(*) AS total_parcels,
  COUNT(DISTINCT county) AS counties,
  ROUND(SUM(acres)::numeric, 0) AS total_acres
FROM parcels
WHERE state = '${STATE_UPPER}'
GROUP BY state;

-- Top counties by parcel count
SELECT county, COUNT(*) AS parcels
FROM parcels
WHERE state = '${STATE_UPPER}' AND county IS NOT NULL
GROUP BY county
ORDER BY COUNT(*) DESC
LIMIT 10;

-- Data quality check
SELECT
  'Owner name populated' AS metric,
  ROUND(100.0 * COUNT(CASE WHEN owner_name IS NOT NULL AND owner_name != '' THEN 1 END) / COUNT(*), 1) || '%' AS value
FROM parcels WHERE state = '${STATE_UPPER}'
UNION ALL
SELECT
  'Address populated',
  ROUND(100.0 * COUNT(CASE WHEN situs_address IS NOT NULL AND situs_address != '' THEN 1 END) / COUNT(*), 1) || '%'
FROM parcels WHERE state = '${STATE_UPPER}'
UNION ALL
SELECT
  'County populated',
  ROUND(100.0 * COUNT(CASE WHEN county IS NOT NULL AND county != '' THEN 1 END) / COUNT(*), 1) || '%'
FROM parcels WHERE state = '${STATE_UPPER}';
SQL

echo ""
echo "=============================================="
echo " Next Steps"
echo "=============================================="
echo ""
echo "1. Export to GeoJSON:"
echo "   ./scripts/export_geojson.sh \"$PG_CONN\" ./output/geojson ${STATE_UPPER}"
echo ""
echo "2. Generate vector tiles:"
echo "   ./scripts/generate_tiles.sh ./output/geojson ./output/tiles ${STATE_LOWER}"
echo ""
echo "3. Optional: Clean up raw table:"
echo "   psql \"$PG_CONN\" -c 'DROP TABLE IF EXISTS ${RAW_TABLE};'"
echo ""
echo "Done!"
