#!/bin/bash
# Reproject ALL GeoJSON files to WGS84 using parallel processing
# Assumes all files need reprojection (from projected CRS to WGS84)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/.."
cd "$DATA_DIR"

GEOJSON_DIR="output/geojson"
BACKUP_DIR="output/geojson_projected_backup"
WGS84_DIR="output/geojson_wgs84"
LOG_DIR="logs"
PARALLEL_JOBS=${PARALLEL_JOBS:-8}

mkdir -p "$BACKUP_DIR" "$WGS84_DIR" "$LOG_DIR"

echo "=============================================="
echo "Parallel GeoJSON Reprojection to WGS84"
echo "Jobs: $PARALLEL_JOBS"
echo "Source: $GEOJSON_DIR"
echo "Output: $WGS84_DIR"
echo "Backup: $BACKUP_DIR"
echo "=============================================="

# Check for ogr2ogr
if ! command -v ogr2ogr &> /dev/null; then
    echo "ERROR: ogr2ogr not found"
    exit 1
fi

echo "GDAL: $(ogr2ogr --version)"
echo ""

# Count files
total=$(ls "$GEOJSON_DIR"/*.geojson 2>/dev/null | wc -l)
echo "Total files to process: $total"
echo "=============================================="

# Function to reproject a single file
reproject_one() {
    local input_file="$1"
    local wgs84_dir="$2"
    local log_dir="$3"

    local filename=$(basename "$input_file")
    local output_file="$wgs84_dir/$filename"
    local log_file="$log_dir/reproject_${filename%.geojson}.log"

    # Skip if already processed
    if [ -f "$output_file" ]; then
        local out_size=$(stat -c%s "$output_file" 2>/dev/null || echo 0)
        if [ "$out_size" -gt 1000 ]; then
            echo "SKIP: $filename (already exists)"
            return 0
        fi
    fi

    local size=$(du -h "$input_file" | cut -f1)
    echo "START: $filename ($size)"

    # Try reprojection from Web Mercator (EPSG:3857) - most common for web data
    if ogr2ogr -f GeoJSON \
        -s_srs EPSG:3857 \
        -t_srs EPSG:4326 \
        -lco RFC7946=YES \
        "$output_file" \
        "$input_file" 2>"$log_file"; then

        # Quick verify the output
        local out_size=$(stat -c%s "$output_file" 2>/dev/null || echo 0)
        if [ "$out_size" -gt 1000 ]; then
            echo "DONE: $filename (Web Mercator -> WGS84)"
            return 0
        fi
    fi

    rm -f "$output_file"

    # Try auto-detection (let GDAL figure it out)
    if ogr2ogr -f GeoJSON \
        -t_srs EPSG:4326 \
        -lco RFC7946=YES \
        "$output_file" \
        "$input_file" 2>>"$log_file"; then

        local out_size=$(stat -c%s "$output_file" 2>/dev/null || echo 0)
        if [ "$out_size" -gt 1000 ]; then
            echo "DONE: $filename (auto-detect -> WGS84)"
            return 0
        fi
    fi

    echo "FAIL: $filename (see $log_file)"
    rm -f "$output_file"
    return 1
}

export -f reproject_one

# Process files in parallel (smallest first for quick wins)
ls -Sr "$GEOJSON_DIR"/*.geojson 2>/dev/null | \
    xargs -P "$PARALLEL_JOBS" -I {} bash -c 'reproject_one "$@"' _ {} "$WGS84_DIR" "$LOG_DIR"

echo ""
echo "=============================================="
echo "Reprojection complete!"
wgs84_count=$(ls "$WGS84_DIR"/*.geojson 2>/dev/null | wc -l)
wgs84_size=$(du -sh "$WGS84_DIR" 2>/dev/null | cut -f1)
echo "WGS84 files: $wgs84_count ($wgs84_size)"
echo "Output: $WGS84_DIR"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Move WGS84 files to geojson dir: mv $WGS84_DIR/*.geojson $GEOJSON_DIR/"
echo "2. Generate PMTiles: PARALLEL_JOBS=12 ./scripts/parallel_pmtiles.sh"
echo "3. Upload to R2: python3 scripts/upload_all_to_r2.py"
