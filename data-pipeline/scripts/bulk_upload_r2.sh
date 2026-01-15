#!/bin/bash
# Continuous R2 uploader - runs all night, uploading files as they complete

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

R2_ACCESS_KEY_ID="ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_ACCESS_KEY="c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET="gspot-tiles"
R2_ENDPOINT="https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

export AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY"

GEOJSON_DIR="output/geojson"
LOG_FILE="logs/r2_upload.log"
TOTAL_UPLOADED=0

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Continuous R2 Uploader Started"
log "=========================================="

# Run continuously
while true; do
    UPLOADED=0
    FAILED=0

    # Get list of files (sorted by size, smallest first for quick wins)
    for file in $(ls -S -r "$GEOJSON_DIR"/*.geojson 2>/dev/null); do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            size=$(ls -lh "$file" | awk '{print $5}')
            log "Uploading: $filename ($size)..."

            if aws s3 cp "$file" "s3://$R2_BUCKET/parcels/$filename" \
                --endpoint-url "$R2_ENDPOINT" \
                --no-progress 2>/dev/null; then
                log "  ✓ Uploaded, deleting local file..."
                rm "$file"
                ((UPLOADED++))
                ((TOTAL_UPLOADED++))
            else
                log "  ✗ Failed to upload"
                ((FAILED++))
            fi
        fi
    done

    if [ $UPLOADED -gt 0 ]; then
        log "Batch complete: $UPLOADED uploaded, $FAILED failed. Total: $TOTAL_UPLOADED"
    fi

    # Check disk space
    disk_free=$(df -h /Users/richyorozco 2>/dev/null | tail -1 | awk '{print $4}')
    file_count=$(ls "$GEOJSON_DIR"/*.geojson 2>/dev/null | wc -l | tr -d ' ')
    log "Status: $file_count files pending, $disk_free disk free"

    # Wait before next check
    sleep 60
done
