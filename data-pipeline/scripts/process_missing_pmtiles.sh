#!/bin/bash
# Process all GeoJSON files that are missing PMTiles
# Downloads from R2, converts to PMTiles, uploads back

set -e

export AWS_ACCESS_KEY_ID="ecd653afe3300fdc045b9980df0dbb14"
export AWS_SECRET_ACCESS_KEY="c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_ENDPOINT="https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_BUCKET="gspot-tiles"

PARALLEL_JOBS=${PARALLEL_JOBS:-8}

mkdir -p output/geojson output/pmtiles logs

# List of files that need processing
MISSING_FILES=(
    "parcels_tx_harris"
    "parcels_ar_statewide"
    "parcels_ca_san_diego"
    "parcels_fl_statewide"
    "parcels_ia_statewide"
    "parcels_la_jefferson_v2"
    "parcels_la_orleans"
    "parcels_la_orleans_v2"
    "parcels_ma_statewide"
    "parcels_md_statewide"
    "parcels_me"
    "parcels_mt_statewide_v2"
    "parcels_nv_statewide"
    "parcels_or_multnomah"
    "parcels_pa_pasda_statewide"
    "parcels_tn_statewide"
    "parcels_tx_statewide"
    "parcels_tx_statewide_recent"
    "parcels_wi_waukesha"
)

process_file() {
    local name=$1
    local geojson="output/geojson/${name}.geojson"
    local pmtiles="output/pmtiles/${name}.pmtiles"
    local log="logs/${name}.log"

    echo "[$(date +%H:%M:%S)] Processing: $name"

    # Download if not exists locally
    if [ ! -f "$geojson" ]; then
        echo "[$(date +%H:%M:%S)] Downloading $name.geojson from R2..."
        aws s3 cp "s3://${R2_BUCKET}/parcels/${name}.geojson" "$geojson" \
            --endpoint-url "$R2_ENDPOINT" 2>&1 | tee -a "$log"
    fi

    # Skip if PMTiles already exists
    if [ -f "$pmtiles" ]; then
        echo "[$(date +%H:%M:%S)] $name.pmtiles already exists locally, skipping conversion"
    else
        # Convert to PMTiles
        echo "[$(date +%H:%M:%S)] Converting $name to PMTiles..."
        tippecanoe -z14 -o "$pmtiles" "$geojson" \
            --drop-densest-as-needed \
            --extend-zooms-if-still-dropping \
            -l parcels \
            --force 2>&1 | tee -a "$log"
    fi

    # Upload PMTiles to R2
    echo "[$(date +%H:%M:%S)] Uploading $name.pmtiles to R2..."
    aws s3 cp "$pmtiles" "s3://${R2_BUCKET}/parcels/${name}.pmtiles" \
        --endpoint-url "$R2_ENDPOINT" 2>&1 | tee -a "$log"

    echo "[$(date +%H:%M:%S)] Completed: $name"
}

export -f process_file
export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY R2_ENDPOINT R2_BUCKET

echo "=============================================="
echo "Processing ${#MISSING_FILES[@]} files with $PARALLEL_JOBS parallel jobs"
echo "=============================================="

# Run in parallel
printf '%s\n' "${MISSING_FILES[@]}" | xargs -P "$PARALLEL_JOBS" -I {} bash -c 'process_file "$@"' _ {}

echo ""
echo "=============================================="
echo "All processing complete!"
echo "=============================================="
