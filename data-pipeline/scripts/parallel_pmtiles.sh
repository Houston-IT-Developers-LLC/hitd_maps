#!/bin/bash
# Parallel PMTiles generation - uses all available cores
# Handles new/updated files automatically
# Uses fallback zoom if auto-zoom fails

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/.."
cd "$DATA_DIR"

GEOJSON_DIR="$DATA_DIR/output/geojson"
PMTILES_DIR="$DATA_DIR/output/pmtiles"
LOG_DIR="$DATA_DIR/logs"
PARALLEL_JOBS=${PARALLEL_JOBS:-12}

mkdir -p "$PMTILES_DIR" "$LOG_DIR"

echo "=============================================="
echo "Parallel PMTiles Generation"
echo "Jobs: $PARALLEL_JOBS"
echo "GeoJSON: $GEOJSON_DIR"
echo "PMTiles: $PMTILES_DIR"
echo "Logs: $LOG_DIR"
echo "=============================================="

# Function to convert a single file
convert_one() {
    local geojson_file="$1"
    local pmtiles_dir="$2"
    local log_dir="$3"
    local filename=$(basename "$geojson_file" .geojson)
    local pmtiles_file="$pmtiles_dir/${filename}.pmtiles"
    local log_file="$log_dir/${filename}.log"

    # Skip if PMTiles exists and is newer than GeoJSON
    if [ -f "$pmtiles_file" ]; then
        if [ "$pmtiles_file" -nt "$geojson_file" ]; then
            echo "SKIP: $filename (up to date)"
            return 0
        else
            echo "REGEN: $filename (source updated)"
            rm -f "$pmtiles_file"
        fi
    fi

    local size=$(du -h "$geojson_file" | cut -f1)
    echo "START: $filename ($size)"

    # Try with auto-zoom first
    if tippecanoe \
        -zg \
        --drop-densest-as-needed \
        --extend-zooms-if-still-dropping \
        --no-tile-compression \
        -o "$pmtiles_file" \
        "$geojson_file" 2>"$log_file"; then
        local out_size=$(du -h "$pmtiles_file" | cut -f1)
        echo "DONE: $filename ($size -> $out_size)"
        return 0
    fi

    # If auto-zoom failed, try with fixed zoom 0-14
    echo "RETRY: $filename (using fixed zoom 0-14)"
    rm -f "$pmtiles_file"

    if tippecanoe \
        -z14 \
        --drop-densest-as-needed \
        --extend-zooms-if-still-dropping \
        --no-tile-compression \
        -o "$pmtiles_file" \
        "$geojson_file" 2>>"$log_file"; then
        local out_size=$(du -h "$pmtiles_file" | cut -f1)
        echo "DONE: $filename ($size -> $out_size) [fixed zoom]"
        return 0
    fi

    echo "FAIL: $filename (see $log_file)"
    tail -3 "$log_file"
    return 1
}

export -f convert_one

# Get list of files sorted by size (smallest first for quick progress)
if [ ! -d "$GEOJSON_DIR" ] || [ -z "$(ls -A "$GEOJSON_DIR"/*.geojson 2>/dev/null)" ]; then
    echo "No GeoJSON files found in $GEOJSON_DIR"
    exit 1
fi

files=$(ls -Sr "$GEOJSON_DIR"/*.geojson 2>/dev/null)
total=$(echo "$files" | wc -l | tr -d ' ')

echo "Total files: $total"
echo "=============================================="

# Run in parallel using xargs
echo "$files" | xargs -P "$PARALLEL_JOBS" -I {} bash -c 'convert_one "$@"' _ {} "$PMTILES_DIR" "$LOG_DIR"

echo ""
echo "=============================================="
echo "Generation complete!"
pmtiles_count=$(ls "$PMTILES_DIR"/*.pmtiles 2>/dev/null | wc -l | tr -d ' ')
pmtiles_size=$(du -sh "$PMTILES_DIR" 2>/dev/null | cut -f1)
echo "PMTiles: $pmtiles_count files ($pmtiles_size)"
echo "=============================================="
