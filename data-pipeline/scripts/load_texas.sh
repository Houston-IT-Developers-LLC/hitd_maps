#!/bin/bash
set -e

# ============================================================================
# Texas Parcel Data - Convert and Load to PostGIS
# ============================================================================
# Converts TxGIO Geodatabase to PostgreSQL/PostGIS with normalized schema.
# Uses ogr2ogr for format conversion and coordinate transformation.
# ============================================================================

GDB_PATH="${1:-./data-pipeline/downloads/StratMap_Land_Parcels.gdb}"
PG_CONN="${2:-postgresql://postgres:postgres@localhost:5432/gspot}"
LAYER_NAME="${3:-}"  # Auto-detect if not provided

echo "=============================================="
echo " Texas Parcel Data Loader"
echo "=============================================="
echo ""
echo "Input GDB:  $GDB_PATH"
echo "Database:   $PG_CONN"
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

# Check GDB exists
if [ ! -d "$GDB_PATH" ]; then
  echo ""
  echo "ERROR: Geodatabase not found: $GDB_PATH"
  echo ""
  echo "Usage: $0 <gdb_path> [pg_connection] [layer_name]"
  echo ""
  echo "Example:"
  echo "  $0 ./downloads/StratMap_Land_Parcels.gdb"
  echo "  $0 ./downloads/texas.gdb postgresql://user:pass@localhost:5432/gspot"
  echo ""
  exit 1
fi

echo "  ogr2ogr: OK"
echo "  psql:    OK"
echo "  GDB:     OK"
echo ""

# ============================================================================
# Layer Discovery
# ============================================================================

echo "Scanning geodatabase for layers..."
echo ""

# List all layers
ogrinfo -so "$GDB_PATH" 2>/dev/null | head -30

echo ""

# Auto-detect parcel layer if not specified
if [ -z "$LAYER_NAME" ]; then
  echo "Auto-detecting parcel layer..."

  # Common layer names in TxGIO data
  CANDIDATES=(
    "StratMap_Land_Parcels"
    "Land_Parcels"
    "Parcels"
    "parcels"
    "PARCELS"
  )

  for candidate in "${CANDIDATES[@]}"; do
    if ogrinfo -so "$GDB_PATH" "$candidate" >/dev/null 2>&1; then
      LAYER_NAME="$candidate"
      echo "Found layer: $LAYER_NAME"
      break
    fi
  done

  if [ -z "$LAYER_NAME" ]; then
    echo ""
    echo "ERROR: Could not auto-detect parcel layer."
    echo ""
    echo "Please specify the layer name:"
    echo "  $0 <gdb_path> <pg_connection> <layer_name>"
    echo ""
    echo "List layers with:"
    echo "  ogrinfo -so \"$GDB_PATH\""
    echo ""
    exit 1
  fi
fi

echo ""
echo "Using layer: $LAYER_NAME"
echo ""

# Show layer info
echo "Layer details:"
ogrinfo -so "$GDB_PATH" "$LAYER_NAME" | head -20
echo ""

# ============================================================================
# Load Raw Data
# ============================================================================

RAW_TABLE="parcels_texas_raw"

echo "=============================================="
echo " Step 1: Loading raw data to $RAW_TABLE"
echo "=============================================="
echo ""
echo "This may take 10-30 minutes for statewide data (~28M parcels)..."
echo ""

# ogr2ogr options:
# -f PostgreSQL    : Output format
# -nln             : New layer name (table name)
# -nlt             : Force geometry type
# -t_srs           : Target coordinate system (MUST be EPSG:4326)
# -lco             : Layer creation options
# -overwrite       : Replace existing table
# -progress        : Show progress

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

# Show sample of what we loaded
echo "Sample fields from raw data:"
psql "$PG_CONN" -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '$RAW_TABLE' LIMIT 15;"
echo ""

# ============================================================================
# Normalize to Main Schema
# ============================================================================

echo "=============================================="
echo " Step 2: Normalizing to parcels table"
echo "=============================================="
echo ""

# The field names vary across TxGIO releases
# Use COALESCE to try multiple possible field names

psql "$PG_CONN" << 'SQL'
-- Delete existing Texas data (clean re-import)
DELETE FROM parcels WHERE state = 'TX';

-- Insert with field mapping (COALESCE handles varying field names)
-- Field names are lowercase in PostgreSQL
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
    NULLIF(pid::text, ''),
    NULLIF(apn::text, ''),
    gid::text
  ) AS apn,

  -- Owner name
  COALESCE(
    NULLIF(owner_name::text, ''),
    NULLIF(owner::text, ''),
    NULLIF(owner1::text, ''),
    NULLIF(ownername::text, '')
  ) AS owner_name,

  -- Property address (situs = physical location)
  COALESCE(
    NULLIF(situs_addr::text, ''),
    NULLIF(situs_address::text, ''),
    NULLIF(address::text, ''),
    NULLIF(prop_addr::text, ''),
    NULLIF(physical_addr::text, '')
  ) AS situs_address,

  -- City
  COALESCE(
    NULLIF(situs_city::text, ''),
    NULLIF(city::text, ''),
    NULLIF(prop_city::text, '')
  ) AS city,

  -- State (always TX)
  'TX' AS state,

  -- County
  COALESCE(
    NULLIF(county::text, ''),
    NULLIF(cnty_name::text, ''),
    NULLIF(county_name::text, ''),
    NULLIF(co_name::text, '')
  ) AS county,

  -- Acres (calculate from area if not available)
  COALESCE(
    acres::numeric(10,2),
    (ST_Area(geom::geography) / 4046.86)::numeric(10,2)
  ) AS acres,

  -- Source tracking
  'txgio' AS source,
  CURRENT_DATE AS source_date,

  -- Geometry (already in EPSG:4326)
  geom

FROM parcels_texas_raw
WHERE geom IS NOT NULL
  AND ST_IsValid(geom);

-- Log the import
INSERT INTO import_log (source, state, record_count, source_url)
SELECT
  'txgio',
  'TX',
  COUNT(*),
  'https://tnris.org/stratmap/land-parcels'
FROM parcels
WHERE state = 'TX' AND source = 'txgio';

-- Report results
SELECT 'Loaded ' || COUNT(*) || ' Texas parcels' AS result
FROM parcels
WHERE state = 'TX';

SQL

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "=============================================="
echo " Load Complete - Summary"
echo "=============================================="
echo ""

psql "$PG_CONN" << 'SQL'
-- Total counts
SELECT
  state,
  COUNT(*) AS total_parcels,
  COUNT(DISTINCT county) AS counties,
  ROUND(SUM(acres)::numeric, 0) AS total_acres
FROM parcels
WHERE state = 'TX'
GROUP BY state;

-- Top 10 counties by parcel count
SELECT county, COUNT(*) AS parcels
FROM parcels
WHERE state = 'TX'
GROUP BY county
ORDER BY COUNT(*) DESC
LIMIT 10;
SQL

echo ""
echo "=============================================="
echo " Next Steps"
echo "=============================================="
echo ""
echo "1. Generate vector tiles:"
echo "   ./scripts/export_geojson.sh"
echo "   ./scripts/generate_tiles.sh"
echo ""
echo "2. Optional: Clean up raw table:"
echo "   psql \$PG_CONN -c 'DROP TABLE IF EXISTS parcels_texas_raw;'"
echo ""
echo "Done!"
