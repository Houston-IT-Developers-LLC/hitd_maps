#!/bin/bash
# Batch convert and upload parcel data to R2
# Runs multiple tippecanoe processes in parallel

set -e

GEOJSON_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/output/geojson/counties"
PMTILES_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/output/pmtiles"
LOGS_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/logs"

mkdir -p "$PMTILES_DIR"
mkdir -p "$LOGS_DIR"

# Process files in parallel (8 at a time to not overwhelm CPU)
MAX_JOBS=8

convert_file() {
    local geojson="$1"
    local basename=$(basename "$geojson" .geojson)
    local pmtiles="$PMTILES_DIR/${basename}.pmtiles"
    local log="$LOGS_DIR/tippecanoe_${basename}.log"

    if [ -f "$pmtiles" ]; then
        echo "SKIP: $basename (already exists)"
        return 0
    fi

    echo "CONVERTING: $basename"
    tippecanoe \
        -o "$pmtiles" \
        --force \
        --no-feature-limit \
        --no-tile-size-limit \
        -zg \
        --drop-densest-as-needed \
        --extend-zooms-if-still-dropping \
        --layer parcels \
        --name "parcels_${basename}" \
        "$geojson" \
        > "$log" 2>&1

    if [ $? -eq 0 ]; then
        echo "DONE: $basename ($(du -h "$pmtiles" | cut -f1))"
    else
        echo "FAILED: $basename"
        cat "$log"
    fi
}

export -f convert_file
export PMTILES_DIR LOGS_DIR

echo "========================================"
echo "Starting batch PMTiles conversion"
echo "========================================"
echo "Source: $GEOJSON_DIR"
echo "Output: $PMTILES_DIR"
echo "Max parallel jobs: $MAX_JOBS"
echo ""

# Find all geojson files and process in parallel
find "$GEOJSON_DIR" -name "*.geojson" -type f | \
    xargs -P $MAX_JOBS -I {} bash -c 'convert_file "$@"' _ {}

echo ""
echo "========================================"
echo "Conversion complete!"
echo "========================================"
ls -lh "$PMTILES_DIR"/*.pmtiles 2>/dev/null | wc -l
echo "PMTiles files created"
du -sh "$PMTILES_DIR"
