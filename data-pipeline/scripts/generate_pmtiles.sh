#!/bin/bash
# Generate PMTiles from all GeoJSON files
# Runs multiple conversions in parallel for speed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

GEOJSON_DIR="output/geojson"
PMTILES_DIR="output/pmtiles"
LOG_FILE="logs/pmtiles_generation.log"
PARALLEL_JOBS=${PARALLEL_JOBS:-4}  # Number of parallel conversions

mkdir -p "$PMTILES_DIR"
mkdir -p "logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

convert_file() {
    local geojson_file="$1"
    local filename=$(basename "$geojson_file" .geojson)
    local pmtiles_file="$PMTILES_DIR/${filename}.pmtiles"

    if [ -f "$pmtiles_file" ]; then
        echo "  SKIP: $filename.pmtiles already exists"
        return 0
    fi

    local size=$(ls -lh "$geojson_file" | awk '{print $5}')
    echo "  CONVERTING: $filename ($size)..."

    # tippecanoe options:
    # -zg: auto-select max zoom based on feature density
    # --drop-densest-as-needed: drop features in dense areas at low zooms
    # --extend-zooms-if-still-dropping: extend zoom if still dropping features
    # -o: output file
    # --force: overwrite if exists
    if tippecanoe \
        -zg \
        --drop-densest-as-needed \
        --extend-zooms-if-still-dropping \
        --no-tile-compression \
        -o "$pmtiles_file" \
        "$geojson_file" 2>/dev/null; then
        local pmtiles_size=$(ls -lh "$pmtiles_file" | awk '{print $5}')
        echo "  ✓ Created: $filename.pmtiles ($pmtiles_size)"
        return 0
    else
        echo "  ✗ Failed: $filename"
        return 1
    fi
}

export -f convert_file
export PMTILES_DIR

log "=========================================="
log "PMTiles Generation Started"
log "Parallel jobs: $PARALLEL_JOBS"
log "=========================================="

# Count files
TOTAL_FILES=$(ls "$GEOJSON_DIR"/*.geojson 2>/dev/null | wc -l | tr -d ' ')
log "Found $TOTAL_FILES GeoJSON files to process"

# Check for tippecanoe
if ! command -v tippecanoe &> /dev/null; then
    log "ERROR: tippecanoe is not installed"
    exit 1
fi

# Process files (sorted by size, smallest first)
CONVERTED=0
FAILED=0
SKIPPED=0

for geojson_file in $(ls -S -r "$GEOJSON_DIR"/*.geojson 2>/dev/null); do
    filename=$(basename "$geojson_file" .geojson)
    pmtiles_file="$PMTILES_DIR/${filename}.pmtiles"

    if [ -f "$pmtiles_file" ]; then
        ((SKIPPED++))
        continue
    fi

    size=$(ls -lh "$geojson_file" | awk '{print $5}')
    log "Converting: $filename ($size)..."

    if tippecanoe \
        -zg \
        --drop-densest-as-needed \
        --extend-zooms-if-still-dropping \
        --no-tile-compression \
        -o "$pmtiles_file" \
        "$geojson_file" 2>&1 | tee -a "$LOG_FILE"; then
        pmtiles_size=$(ls -lh "$pmtiles_file" | awk '{print $5}')
        log "  ✓ Created: $filename.pmtiles ($pmtiles_size)"
        ((CONVERTED++))
    else
        log "  ✗ Failed: $filename"
        ((FAILED++))
    fi
done

log "=========================================="
log "PMTiles Generation Complete"
log "Converted: $CONVERTED"
log "Skipped (already exist): $SKIPPED"
log "Failed: $FAILED"
log "Output directory: $PMTILES_DIR"
log "=========================================="
