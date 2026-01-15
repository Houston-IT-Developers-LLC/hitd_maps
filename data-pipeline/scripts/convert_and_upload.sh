#!/bin/bash
# Convert GeoJSON to PMTiles and upload to R2
# Handles coordinate reprojection to WGS84

set -e

GEOJSON_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/output/geojson/counties"
PMTILES_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/output/pmtiles"
REPROJECTED_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/output/geojson/reprojected"
LOGS_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/logs"

mkdir -p "$PMTILES_DIR"
mkdir -p "$REPROJECTED_DIR"
mkdir -p "$LOGS_DIR"

# R2 Configuration
R2_ACCESS_KEY="ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY="c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET="gspot-tiles"
R2_ENDPOINT="https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

process_file() {
    local geojson="$1"
    local basename=$(basename "$geojson" .geojson)
    local reprojected="$REPROJECTED_DIR/${basename}_wgs84.geojson"
    local pmtiles="$PMTILES_DIR/${basename}.pmtiles"
    local log="$LOGS_DIR/convert_${basename}.log"

    # Skip if already uploaded
    if [ -f "$PMTILES_DIR/${basename}.uploaded" ]; then
        echo "SKIP (uploaded): $basename"
        return 0
    fi

    echo "========================================" | tee -a "$log"
    echo "Processing: $basename" | tee -a "$log"
    echo "Time: $(date)" | tee -a "$log"
    echo "========================================" | tee -a "$log"

    # Check if file needs reprojection by looking at coordinate range
    local first_coord=$(head -c 10000 "$geojson" | grep -o '"coordinates":\s*\[\[\[\[[0-9.-]*' | head -1 | grep -o '[0-9.-]*$' || true)

    local needs_reproject=0
    if [ -n "$first_coord" ]; then
        # If first X coordinate is > 180, it's likely in projected CRS
        if (( $(echo "$first_coord > 180" | bc -l 2>/dev/null || echo 0) )); then
            needs_reproject=1
        fi
    fi

    # Reproject if needed
    if [ "$needs_reproject" -eq 1 ]; then
        echo "  Reprojecting to WGS84..." | tee -a "$log"
        ogr2ogr -f GeoJSON -t_srs EPSG:4326 "$reprojected" "$geojson" 2>> "$log"
        if [ $? -ne 0 ]; then
            echo "  ERROR: Reprojection failed" | tee -a "$log"
            return 1
        fi
        local input="$reprojected"
    else
        echo "  Already in WGS84" | tee -a "$log"
        local input="$geojson"
    fi

    # Convert to PMTiles
    echo "  Converting to PMTiles..." | tee -a "$log"
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
        --attribution "GSpot Outdoors" \
        "$input" \
        2>> "$log"

    if [ $? -ne 0 ]; then
        echo "  ERROR: tippecanoe failed" | tee -a "$log"
        return 1
    fi

    local pmsize=$(du -h "$pmtiles" | cut -f1)
    echo "  PMTiles created: $pmsize" | tee -a "$log"

    # Upload to R2
    echo "  Uploading to R2..." | tee -a "$log"
    AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY" \
    AWS_SECRET_ACCESS_KEY="$R2_SECRET_KEY" \
    aws s3 cp "$pmtiles" "s3://$R2_BUCKET/parcels/${basename}.pmtiles" \
        --endpoint-url "$R2_ENDPOINT" \
        2>> "$log"

    if [ $? -eq 0 ]; then
        echo "  Uploaded successfully!" | tee -a "$log"
        touch "$PMTILES_DIR/${basename}.uploaded"

        # Clean up local files
        echo "  Cleaning up local files..." | tee -a "$log"
        rm -f "$geojson"
        rm -f "$reprojected"
        rm -f "$pmtiles"
        echo "  DONE: $basename" | tee -a "$log"
    else
        echo "  ERROR: Upload failed" | tee -a "$log"
        return 1
    fi

    return 0
}

export -f process_file
export PMTILES_DIR REPROJECTED_DIR LOGS_DIR R2_ACCESS_KEY R2_SECRET_KEY R2_BUCKET R2_ENDPOINT

echo "========================================"
echo "GeoJSON to PMTiles Conversion & Upload"
echo "========================================"
echo "Source: $GEOJSON_DIR"
echo "Output: $PMTILES_DIR"
echo "R2 Bucket: $R2_BUCKET"
echo ""

# Process files (one at a time due to memory constraints with large files)
for geojson in "$GEOJSON_DIR"/*.geojson; do
    if [ -f "$geojson" ]; then
        process_file "$geojson" || echo "Failed: $(basename $geojson)"
    fi
done

echo ""
echo "========================================"
echo "Processing complete!"
echo "========================================"
