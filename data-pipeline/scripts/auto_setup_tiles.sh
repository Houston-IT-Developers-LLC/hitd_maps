#!/bin/bash
# Automated self-hosted tiles setup
# This script handles everything: download, upload, cleanup, and config update
# Run with: nohup ./auto_setup_tiles.sh > setup.log 2>&1 &

set -e

# Configuration
TEMP_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/data/temp_tiles"
INDEX_HTML="/home/exx/Documents/C/hitd_maps/demo/index.html"
R2_ENDPOINT="https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_BUCKET="gspot-tiles"
AWS_CMD="/home/exx/.local/bin/aws"

# URLs
PROTOMAPS_URL="https://build.protomaps.com/20260117.pmtiles"
MAPTERHORN_URL="https://download.mapterhorn.com/planet.pmtiles"
USA_BBOX="-125,24,-66,50"

cd "$TEMP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

upload_to_r2() {
    local file=$1
    local dest=$2
    log "Uploading $file to R2: $dest"
    $AWS_CMD s3 cp "$file" "s3://${R2_BUCKET}/${dest}" \
        --endpoint-url "$R2_ENDPOINT" \
        --profile r2 \
        --no-progress
    log "Upload complete: $dest"
}

# ============================================
# STEP 1: Download Protomaps (if not exists)
# ============================================
log "=== STEP 1: Protomaps Basemap ==="
if [ -f "protomaps_planet.pmtiles" ]; then
    SIZE=$(stat -c%s "protomaps_planet.pmtiles" 2>/dev/null || echo "0")
    if [ "$SIZE" -gt 100000000000 ]; then
        log "protomaps_planet.pmtiles already exists ($(numfmt --to=iec $SIZE))"
    else
        log "Incomplete file found, resuming download..."
        wget -c --progress=dot:giga "$PROTOMAPS_URL" -O protomaps_planet.pmtiles
    fi
else
    log "Downloading Protomaps basemap (~133GB)..."
    wget -c --progress=dot:giga "$PROTOMAPS_URL" -O protomaps_planet.pmtiles
fi

# ============================================
# STEP 2: Upload Protomaps to R2
# ============================================
log "=== STEP 2: Upload Protomaps to R2 ==="
upload_to_r2 "protomaps_planet.pmtiles" "basemap/protomaps_planet.pmtiles"

log "Deleting local Protomaps file..."
rm -f protomaps_planet.pmtiles
log "Freed $(numfmt --to=iec 133000000000) disk space"

# ============================================
# STEP 3: Extract USA terrain from Mapterhorn
# ============================================
log "=== STEP 3: Extract USA Terrain ==="
if [ -f "mapterhorn_usa.pmtiles" ]; then
    log "mapterhorn_usa.pmtiles already exists"
else
    log "Extracting USA terrain from Mapterhorn (this downloads ~45GB)..."
    pmtiles extract \
        --bbox="$USA_BBOX" \
        --maxzoom=14 \
        --download-threads=8 \
        "$MAPTERHORN_URL" \
        mapterhorn_usa.pmtiles
fi

# ============================================
# STEP 4: Upload Terrain to R2
# ============================================
log "=== STEP 4: Upload Terrain to R2 ==="
upload_to_r2 "mapterhorn_usa.pmtiles" "terrain/mapterhorn_usa.pmtiles"

log "Deleting local terrain file..."
rm -f mapterhorn_usa.pmtiles
log "Freed disk space"

# ============================================
# STEP 5: Update index.html config
# ============================================
log "=== STEP 5: Update Config ==="
sed -i 's/USE_SELF_HOSTED_BASEMAP = false/USE_SELF_HOSTED_BASEMAP = true/' "$INDEX_HTML"
sed -i 's/USE_SELF_HOSTED_TERRAIN = false/USE_SELF_HOSTED_TERRAIN = true/' "$INDEX_HTML"
log "Updated index.html to use self-hosted tiles"

# ============================================
# STEP 6: Verify
# ============================================
log "=== STEP 6: Verify Uploads ==="
log "Checking R2 basemap folder:"
$AWS_CMD s3 ls "s3://${R2_BUCKET}/basemap/" --endpoint-url "$R2_ENDPOINT" --profile r2

log "Checking R2 terrain folder:"
$AWS_CMD s3 ls "s3://${R2_BUCKET}/terrain/" --endpoint-url "$R2_ENDPOINT" --profile r2

log ""
log "============================================"
log "SETUP COMPLETE!"
log "============================================"
log ""
log "Self-hosted tiles are now live at:"
log "  - Basemap: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/basemap/protomaps_planet.pmtiles"
log "  - Terrain: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/terrain/mapterhorn_usa.pmtiles"
log ""
log "Deploy index.html to see the changes on https://hitd-maps.vercel.app/"
