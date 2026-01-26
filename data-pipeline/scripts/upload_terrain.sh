#!/bin/bash
# Upload terrain to R2 after extraction completes
# Run with: ./upload_terrain.sh

TEMP_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/data/temp_tiles"
R2_ENDPOINT="https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_BUCKET="gspot-tiles"
AWS_CMD="/home/exx/.local/bin/aws"

cd "$TEMP_DIR"

echo "[$(date)] Checking for terrain file..."

if [ ! -f "mapterhorn_usa.pmtiles" ]; then
    echo "ERROR: mapterhorn_usa.pmtiles not found"
    exit 1
fi

SIZE=$(stat -c%s "mapterhorn_usa.pmtiles")
echo "Found terrain file: $(numfmt --to=iec $SIZE)"

echo "[$(date)] Uploading to R2..."
$AWS_CMD s3 cp "mapterhorn_usa.pmtiles" "s3://${R2_BUCKET}/terrain/mapterhorn_usa.pmtiles" \
    --endpoint-url "$R2_ENDPOINT" \
    --profile r2

echo "[$(date)] Upload complete!"

echo "[$(date)] Deleting local file..."
rm -f mapterhorn_usa.pmtiles

echo "[$(date)] Done! Terrain available at:"
echo "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/terrain/mapterhorn_usa.pmtiles"
