#!/bin/bash
# Watch for downloads to complete and upload automatically
# Runs in background, checks every 30 seconds

TEMP_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/data/temp_tiles"
SCRIPTS_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/scripts"
INDEX_HTML="/home/exx/Documents/C/hitd_maps/demo/index.html"
R2_ENDPOINT="https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_BUCKET="gspot-tiles"
AWS_CMD="/home/exx/.local/bin/aws"

TERRAIN_UPLOADED=false
PROTOMAPS_UPLOADED=false

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

cd "$TEMP_DIR"

log "Starting watch_and_upload - monitoring for completed downloads..."

while true; do
    # Check if terrain extraction is complete (file exists and no pmtiles process running for it)
    if [ "$TERRAIN_UPLOADED" = false ] && [ -f "mapterhorn_usa.pmtiles" ]; then
        # Check if pmtiles extract is still running
        if ! pgrep -f "pmtiles.*mapterhorn" > /dev/null; then
            SIZE=$(stat -c%s "mapterhorn_usa.pmtiles" 2>/dev/null || echo "0")
            if [ "$SIZE" -gt 1000000000 ]; then  # > 1GB means it's complete
                log "=== TERRAIN EXTRACTION COMPLETE ==="
                log "File size: $(numfmt --to=iec $SIZE)"
                log "Uploading to R2..."

                $AWS_CMD s3 cp "mapterhorn_usa.pmtiles" "s3://${R2_BUCKET}/terrain/mapterhorn_usa.pmtiles" \
                    --endpoint-url "$R2_ENDPOINT" \
                    --profile r2

                if [ $? -eq 0 ]; then
                    log "Terrain upload complete!"
                    log "Deleting local file..."
                    rm -f mapterhorn_usa.pmtiles

                    # Update index.html
                    sed -i 's/USE_SELF_HOSTED_TERRAIN = false/USE_SELF_HOSTED_TERRAIN = true/' "$INDEX_HTML"
                    log "Updated index.html: USE_SELF_HOSTED_TERRAIN = true"

                    TERRAIN_UPLOADED=true
                else
                    log "ERROR: Terrain upload failed!"
                fi
            fi
        fi
    fi

    # Check if protomaps download is complete
    if [ "$PROTOMAPS_UPLOADED" = false ] && [ -f "protomaps_planet.pmtiles" ]; then
        # Check if wget is still running for protomaps
        if ! pgrep -f "wget.*protomaps" > /dev/null; then
            SIZE=$(stat -c%s "protomaps_planet.pmtiles" 2>/dev/null || echo "0")
            if [ "$SIZE" -gt 100000000000 ]; then  # > 100GB means it's complete
                log "=== PROTOMAPS DOWNLOAD COMPLETE ==="
                log "File size: $(numfmt --to=iec $SIZE)"
                log "Uploading to R2 (this will take 2-4 hours)..."

                $AWS_CMD s3 cp "protomaps_planet.pmtiles" "s3://${R2_BUCKET}/basemap/protomaps_planet.pmtiles" \
                    --endpoint-url "$R2_ENDPOINT" \
                    --profile r2

                if [ $? -eq 0 ]; then
                    log "Protomaps upload complete!"
                    log "Deleting local file..."
                    rm -f protomaps_planet.pmtiles

                    # Update index.html
                    sed -i 's/USE_SELF_HOSTED_BASEMAP = false/USE_SELF_HOSTED_BASEMAP = true/' "$INDEX_HTML"
                    log "Updated index.html: USE_SELF_HOSTED_BASEMAP = true"

                    PROTOMAPS_UPLOADED=true
                else
                    log "ERROR: Protomaps upload failed!"
                fi
            fi
        fi
    fi

    # Exit if both are done
    if [ "$TERRAIN_UPLOADED" = true ] && [ "$PROTOMAPS_UPLOADED" = true ]; then
        log "=== ALL UPLOADS COMPLETE ==="
        log "Self-hosted tiles are now live!"
        log ""
        log "URLs:"
        log "  Basemap: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/basemap/protomaps_planet.pmtiles"
        log "  Terrain: https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/terrain/mapterhorn_usa.pmtiles"
        log ""
        log "Deploy index.html to Vercel to see changes."
        exit 0
    fi

    sleep 30
done
