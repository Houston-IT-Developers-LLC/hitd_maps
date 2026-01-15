#!/bin/bash
# Retry failed PMTiles with fixed zoom level
# Run this after parallel_pmtiles.sh to catch any that failed with -zg

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/.."
cd "$DATA_DIR"

GEOJSON_DIR="$DATA_DIR/output/geojson"
PMTILES_DIR="$DATA_DIR/output/pmtiles"
LOG_DIR="$DATA_DIR/logs"
PARALLEL_JOBS=${PARALLEL_JOBS:-8}

mkdir -p "$PMTILES_DIR" "$LOG_DIR"

echo "=============================================="
echo "Retry Failed PMTiles (Fixed Zoom)"
echo "=============================================="

# Find GeoJSON files without corresponding PMTiles
missing=()
for geojson in "$GEOJSON_DIR"/*.geojson; do
    filename=$(basename "$geojson" .geojson)
    pmtiles="$PMTILES_DIR/${filename}.pmtiles"
    if [ ! -f "$pmtiles" ]; then
        missing+=("$geojson")
    fi
done

if [ ${#missing[@]} -eq 0 ]; then
    echo "All PMTiles exist! Nothing to retry."
    exit 0
fi

echo "Found ${#missing[@]} missing PMTiles"
echo "=============================================="

# Function to convert with fixed zoom
convert_fixed() {
    local geojson_file="$1"
    local pmtiles_dir="$2"
    local log_dir="$3"
    local filename=$(basename "$geojson_file" .geojson)
    local pmtiles_file="$pmtiles_dir/${filename}.pmtiles"
    local log_file="$log_dir/${filename}_retry.log"

    if [ -f "$pmtiles_file" ]; then
        echo "SKIP: $filename (exists)"
        return 0
    fi

    local size=$(du -h "$geojson_file" | cut -f1)
    echo "RETRY: $filename ($size) with fixed zoom 0-14"

    if tippecanoe \
        -z14 \
        --drop-densest-as-needed \
        --extend-zooms-if-still-dropping \
        --no-tile-compression \
        -o "$pmtiles_file" \
        "$geojson_file" 2>"$log_file"; then
        local out_size=$(du -h "$pmtiles_file" | cut -f1)
        echo "DONE: $filename ($size -> $out_size)"
        return 0
    else
        echo "FAIL: $filename"
        tail -3 "$log_file"
        return 1
    fi
}

export -f convert_fixed

# Process missing files in parallel
printf "%s\n" "${missing[@]}" | xargs -P "$PARALLEL_JOBS" -I {} bash -c 'convert_fixed "$@"' _ {} "$PMTILES_DIR" "$LOG_DIR"

echo ""
echo "=============================================="
echo "Retry complete!"
pmtiles_count=$(ls "$PMTILES_DIR"/*.pmtiles 2>/dev/null | wc -l | tr -d ' ')
geojson_count=$(ls "$GEOJSON_DIR"/*.geojson 2>/dev/null | wc -l | tr -d ' ')
echo "PMTiles: $pmtiles_count / $geojson_count"
echo "=============================================="
