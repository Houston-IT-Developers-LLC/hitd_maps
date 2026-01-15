#!/bin/bash
# ============================================================================
# Export All States Parcel Data - Overnight Batch Runner
# ============================================================================
# Runs exports for all configured states sequentially.
# Each state's progress is logged to its own file.
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${1:-$SCRIPT_DIR/../output/geojson}"
LOG_DIR="$SCRIPT_DIR/../logs"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$LOG_DIR"

# States to export (in order of priority for hunting app)
# Texas is handled separately by export_texas_parcels.sh
STATES=("MT" "FL" "NC" "OR" "IN" "WI")

echo "=============================================="
echo " Multi-State Parcel Export"
echo "=============================================="
echo ""
echo "Output directory: $OUTPUT_DIR"
echo "Log directory: $LOG_DIR"
echo "States to export: ${STATES[*]}"
echo ""
echo "Starting at: $(date)"
echo ""

TOTAL_STATES=${#STATES[@]}
COMPLETED=0
FAILED=0

for STATE in "${STATES[@]}"; do
    COMPLETED=$((COMPLETED + 1))
    STATE_LOWER=$(echo "$STATE" | tr '[:upper:]' '[:lower:]')
    STATE_LOG="$LOG_DIR/export_${STATE_LOWER}.log"
    STATE_OUTPUT="$OUTPUT_DIR/${STATE_LOWER}"

    echo "[$COMPLETED/$TOTAL_STATES] Starting $STATE export..."
    echo "  Output: $STATE_OUTPUT"
    echo "  Log: $STATE_LOG"

    mkdir -p "$STATE_OUTPUT"

    # Run export and capture exit code
    if python3 "$SCRIPT_DIR/export_state_parcels.py" "$STATE" -o "$STATE_OUTPUT" 2>&1 | tee "$STATE_LOG"; then
        echo "  ✓ $STATE completed successfully"
    else
        echo "  ✗ $STATE failed - check log"
        FAILED=$((FAILED + 1))
    fi

    echo ""
done

echo "=============================================="
echo " Multi-State Export Complete"
echo "=============================================="
echo ""
echo "Completed: $((TOTAL_STATES - FAILED))/$TOTAL_STATES states"
echo "Failed: $FAILED states"
echo "Finished at: $(date)"
echo ""

# Summary of output sizes
echo "Output summary:"
for STATE in "${STATES[@]}"; do
    STATE_LOWER=$(echo "$STATE" | tr '[:upper:]' '[:lower:]')
    STATE_DIR="$OUTPUT_DIR/${STATE_LOWER}"
    if [ -d "$STATE_DIR" ]; then
        SIZE=$(du -sh "$STATE_DIR" 2>/dev/null | cut -f1)
        FILES=$(find "$STATE_DIR" -name "*.geojson" 2>/dev/null | wc -l | tr -d ' ')
        echo "  $STATE: $FILES files, $SIZE"
    fi
done
echo ""
