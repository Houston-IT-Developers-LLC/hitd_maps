#!/bin/bash
set -e

# ============================================================================
# Batch Process States
# ============================================================================
# Orchestrates multi-state parcel data processing:
# - Load downloaded datasets
# - Export to GeoJSON
# - Generate vector tiles
# ============================================================================

COMMAND="${1:-}"
STATES="${2:-}"
PG_CONN="${3:-postgresql://postgres:postgres@localhost:5432/gspot}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOWNLOADS_DIR="$BASE_DIR/data-pipeline/downloads"
OUTPUT_DIR="$BASE_DIR/data-pipeline/output"
CONFIG_FILE="$BASE_DIR/data-pipeline/config/sources.json"

# ============================================================================
# Usage
# ============================================================================

show_usage() {
  echo "=============================================="
  echo " Batch Process States"
  echo "=============================================="
  echo ""
  echo "Usage: $0 <command> [states] [pg_conn]"
  echo ""
  echo "Commands:"
  echo "  status    Show import status for all states"
  echo "  load      Load downloaded data for specified states"
  echo "  export    Export loaded states to GeoJSON"
  echo "  tiles     Generate vector tiles for specified states"
  echo "  full      Load, export, and generate tiles"
  echo "  list      List states in sources.json by tier"
  echo ""
  echo "States argument:"
  echo "  TX,WI,FL  Comma-separated state codes"
  echo "  tier1     All tier 1 (free statewide) states"
  echo "  all       All states with downloaded data"
  echo ""
  echo "Examples:"
  echo "  $0 status"
  echo "  $0 list"
  echo "  $0 load TX,WI,FL"
  echo "  $0 tiles tier1"
  echo "  $0 full TX"
  echo ""
}

# ============================================================================
# Helper Functions
# ============================================================================

# Get tier1 states from sources.json
get_tier1_states() {
  if [ -f "$CONFIG_FILE" ]; then
    jq -r '.acquisition_tiers.tier1_free_statewide | join(",")' "$CONFIG_FILE"
  else
    echo ""
  fi
}

# Get all states from sources.json
get_all_states() {
  if [ -f "$CONFIG_FILE" ]; then
    jq -r '.states | keys | join(",")' "$CONFIG_FILE"
  else
    echo ""
  fi
}

# Parse states argument into comma-separated list
parse_states() {
  local input="$1"
  case "$input" in
    all)
      # All states with downloaded data
      local found=""
      for gdb in "$DOWNLOADS_DIR"/*.gdb "$DOWNLOADS_DIR"/*_parcels 2>/dev/null; do
        if [ -e "$gdb" ]; then
          local state=$(basename "$gdb" | grep -oE '^[a-zA-Z]{2}' | tr '[:lower:]' '[:upper:]')
          if [ -n "$state" ]; then
            if [ -z "$found" ]; then
              found="$state"
            else
              found="$found,$state"
            fi
          fi
        fi
      done
      echo "$found"
      ;;
    tier1)
      get_tier1_states
      ;;
    *)
      echo "$input"
      ;;
  esac
}

# Find GDB file for a state
find_gdb() {
  local state="$1"
  local state_lower=$(echo "$state" | tr '[:upper:]' '[:lower:]')

  # Try various naming patterns
  local patterns=(
    "$DOWNLOADS_DIR/${state_lower}_parcels.gdb"
    "$DOWNLOADS_DIR/${state_lower}.gdb"
    "$DOWNLOADS_DIR/parcels_${state_lower}.gdb"
    "$DOWNLOADS_DIR/*${state_lower}*.gdb"
    "$DOWNLOADS_DIR/*${state}*.gdb"
  )

  for pattern in "${patterns[@]}"; do
    local match=$(ls -d $pattern 2>/dev/null | head -1)
    if [ -n "$match" ] && [ -e "$match" ]; then
      echo "$match"
      return 0
    fi
  done

  return 1
}

# ============================================================================
# Commands
# ============================================================================

# Show current status
cmd_status() {
  echo "=============================================="
  echo " Parcel Data Status"
  echo "=============================================="
  echo ""

  echo "Downloads directory: $DOWNLOADS_DIR"
  echo ""

  echo "Downloaded datasets:"
  if [ -d "$DOWNLOADS_DIR" ]; then
    ls -lh "$DOWNLOADS_DIR"/*.gdb 2>/dev/null || echo "  (no .gdb files)"
    ls -lh "$DOWNLOADS_DIR"/*.shp 2>/dev/null || true
  else
    echo "  (directory not found)"
  fi
  echo ""

  echo "Database records by state:"
  psql "$PG_CONN" -c "
    SELECT
      state,
      to_char(COUNT(*), 'FM999,999,999') AS parcels,
      COUNT(DISTINCT county) AS counties,
      to_char(MAX(imported_at), 'YYYY-MM-DD') AS last_import
    FROM parcels
    GROUP BY state
    ORDER BY state;
  " 2>/dev/null || echo "  (database not connected)"
  echo ""

  echo "GeoJSON exports:"
  if [ -d "$OUTPUT_DIR/geojson" ]; then
    ls -lh "$OUTPUT_DIR/geojson"/*.geojson 2>/dev/null || echo "  (none)"
  else
    echo "  (directory not found)"
  fi
  echo ""

  echo "Generated tiles:"
  if [ -d "$OUTPUT_DIR/tiles" ]; then
    ls -lh "$OUTPUT_DIR/tiles"/*.mbtiles 2>/dev/null || echo "  (none)"
  else
    echo "  (directory not found)"
  fi
}

# List states by tier
cmd_list() {
  echo "=============================================="
  echo " States by Acquisition Tier"
  echo "=============================================="
  echo ""

  if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: sources.json not found at $CONFIG_FILE"
    exit 1
  fi

  echo "Tier 1 (Free Statewide) - $(jq '.acquisition_tiers.tier1_free_statewide | length' "$CONFIG_FILE") states:"
  jq -r '.acquisition_tiers.tier1_free_statewide | .[]' "$CONFIG_FILE" | tr '\n' ' '
  echo ""
  echo ""

  echo "Tier 2 (County Portals) - $(jq '.acquisition_tiers.tier2_county_portals | length' "$CONFIG_FILE") states:"
  jq -r '.acquisition_tiers.tier2_county_portals | .[]' "$CONFIG_FILE" | tr '\n' ' '
  echo ""
  echo ""

  echo "Tier 3 (FOIA Required) - $(jq '.acquisition_tiers.tier3_foia_required | length' "$CONFIG_FILE") states:"
  jq -r '.acquisition_tiers.tier3_foia_required | .[]' "$CONFIG_FILE" | tr '\n' ' '
  echo ""
}

# Load states
cmd_load() {
  local states="$1"

  if [ -z "$states" ]; then
    echo "ERROR: No states specified"
    show_usage
    exit 1
  fi

  IFS=',' read -ra STATE_ARRAY <<< "$states"

  local loaded=0
  local skipped=0

  for state in "${STATE_ARRAY[@]}"; do
    state=$(echo "$state" | tr -d ' ' | tr '[:lower:]' '[:upper:]')

    if [ -z "$state" ]; then
      continue
    fi

    # Find GDB file
    local gdb_file=$(find_gdb "$state")

    if [ -z "$gdb_file" ]; then
      echo "SKIP: No GDB found for $state"
      ((skipped++))
      continue
    fi

    echo ""
    echo "=============================================="
    echo " Loading $state"
    echo "=============================================="
    echo ""

    "$SCRIPT_DIR/load_state.sh" "$state" "$gdb_file" "$PG_CONN" "$CONFIG_FILE"
    ((loaded++))
  done

  echo ""
  echo "=============================================="
  echo " Load Complete"
  echo "=============================================="
  echo "  Loaded: $loaded states"
  echo "  Skipped: $skipped states"
}

# Export to GeoJSON
cmd_export() {
  local states="$1"

  if [ -z "$states" ]; then
    echo "ERROR: No states specified"
    show_usage
    exit 1
  fi

  mkdir -p "$OUTPUT_DIR/geojson"

  IFS=',' read -ra STATE_ARRAY <<< "$states"

  for state in "${STATE_ARRAY[@]}"; do
    state=$(echo "$state" | tr -d ' ' | tr '[:upper:]' '[:lower:]')

    if [ -z "$state" ]; then
      continue
    fi

    echo "Exporting ${state^^} to GeoJSON..."
    "$SCRIPT_DIR/export_geojson.sh" "$PG_CONN" "$OUTPUT_DIR/geojson" "${state^^}"
  done
}

# Generate tiles
cmd_tiles() {
  local states="$1"

  if [ -z "$states" ]; then
    echo "ERROR: No states specified"
    show_usage
    exit 1
  fi

  mkdir -p "$OUTPUT_DIR/tiles"

  IFS=',' read -ra STATE_ARRAY <<< "$states"

  for state in "${STATE_ARRAY[@]}"; do
    state=$(echo "$state" | tr -d ' ' | tr '[:upper:]' '[:lower:]')

    if [ -z "$state" ]; then
      continue
    fi

    # Check if GeoJSON exists
    if [ ! -f "$OUTPUT_DIR/geojson/parcels_${state}.geojson" ]; then
      echo "SKIP: No GeoJSON for ${state^^} - run 'export' first"
      continue
    fi

    echo "Generating tiles for ${state^^}..."
    "$SCRIPT_DIR/generate_tiles.sh" "$OUTPUT_DIR/geojson" "$OUTPUT_DIR/tiles" "$state"
  done
}

# Full pipeline
cmd_full() {
  local states="$1"

  if [ -z "$states" ]; then
    echo "ERROR: No states specified"
    show_usage
    exit 1
  fi

  echo "=============================================="
  echo " Full Pipeline"
  echo "=============================================="
  echo ""
  echo "States: $states"
  echo ""

  # Parse states once
  local parsed_states=$(parse_states "$states")

  if [ -z "$parsed_states" ]; then
    echo "ERROR: No states resolved from '$states'"
    exit 1
  fi

  echo "Resolved to: $parsed_states"
  echo ""

  # Step 1: Load
  echo ""
  echo ">>> Step 1/3: Loading data..."
  cmd_load "$parsed_states"

  # Step 2: Export
  echo ""
  echo ">>> Step 2/3: Exporting to GeoJSON..."
  cmd_export "$parsed_states"

  # Step 3: Generate tiles
  echo ""
  echo ">>> Step 3/3: Generating tiles..."
  cmd_tiles "$parsed_states"

  echo ""
  echo "=============================================="
  echo " Full Pipeline Complete"
  echo "=============================================="
  cmd_status
}

# ============================================================================
# Main
# ============================================================================

case "$COMMAND" in
  status)
    cmd_status
    ;;
  list)
    cmd_list
    ;;
  load)
    cmd_load "$(parse_states "$STATES")"
    ;;
  export)
    cmd_export "$(parse_states "$STATES")"
    ;;
  tiles)
    cmd_tiles "$(parse_states "$STATES")"
    ;;
  full)
    cmd_full "$STATES"
    ;;
  -h|--help|help)
    show_usage
    ;;
  *)
    if [ -z "$COMMAND" ]; then
      show_usage
    else
      echo "ERROR: Unknown command '$COMMAND'"
      echo ""
      show_usage
    fi
    exit 1
    ;;
esac
