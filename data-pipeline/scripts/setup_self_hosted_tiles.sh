#!/bin/bash
# Setup script for self-hosted Protomaps basemap and Mapterhorn terrain
# Downloads to local, uploads to Cloudflare R2, then deletes local files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# R2 Configuration (from CLAUDE.md)
R2_BUCKET="gspot-tiles"
R2_ENDPOINT="https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
AWS_ACCESS_KEY_ID="ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_ACCESS_KEY="c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# Download URLs
# Find latest build date at: https://maps.protomaps.com/builds/
PROTOMAPS_DATE="20260117"  # Update this to latest available
PROTOMAPS_URL="https://build.protomaps.com/${PROTOMAPS_DATE}.pmtiles"
MAPTERHORN_URL="https://download.mapterhorn.com/planet.pmtiles"

# USA bounding box for terrain extract (continental USA)
USA_BBOX="-125,24,-66,50"

# Local temp directory
TEMP_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/data/temp_tiles"

echo -e "${GREEN}=== HITD Maps Self-Hosted Tiles Setup ===${NC}"
echo ""
echo "This script will:"
echo "  1. Download Protomaps basemap (~133GB full planet)"
echo "  2. Extract USA terrain from Mapterhorn (~43GB)"
echo "  3. Upload both to Cloudflare R2"
echo "  4. Delete local files to free space"
echo ""
echo -e "${YELLOW}Estimated time: 6-12 hours depending on connection${NC}"
echo -e "${YELLOW}Estimated R2 storage cost: ~$2.60/month additional${NC}"
echo ""

# Check for required tools
echo "Checking required tools..."
command -v rclone >/dev/null 2>&1 || { echo -e "${RED}rclone is required. Install with: sudo apt install rclone${NC}"; exit 1; }
command -v pmtiles >/dev/null 2>&1 || { echo -e "${RED}pmtiles CLI is required. Install with: pip install pmtiles${NC}"; exit 1; }
command -v wget >/dev/null 2>&1 || { echo -e "${RED}wget is required${NC}"; exit 1; }

echo -e "${GREEN}All tools available!${NC}"
echo ""

# Setup rclone config for R2
echo "Setting up rclone configuration for R2..."
mkdir -p ~/.config/rclone

cat > ~/.config/rclone/rclone.conf << EOF
[r2]
type = s3
provider = Cloudflare
access_key_id = ${AWS_ACCESS_KEY_ID}
secret_access_key = ${AWS_SECRET_ACCESS_KEY}
endpoint = ${R2_ENDPOINT}
acl = private
EOF

echo -e "${GREEN}rclone configured!${NC}"
echo ""

# Create temp directory
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# ============================================
# STEP 1: Download Protomaps basemap
# ============================================
echo -e "${GREEN}=== Step 1: Downloading Protomaps basemap ===${NC}"
echo "URL: $PROTOMAPS_URL"
echo "Size: ~133GB"
echo ""

if [ -f "protomaps_planet.pmtiles" ]; then
    echo -e "${YELLOW}protomaps_planet.pmtiles already exists, skipping download${NC}"
else
    wget -c --progress=bar:force "$PROTOMAPS_URL" -O protomaps_planet.pmtiles
fi

echo -e "${GREEN}Protomaps download complete!${NC}"
ls -lh protomaps_planet.pmtiles
echo ""

# ============================================
# STEP 2: Upload Protomaps to R2
# ============================================
echo -e "${GREEN}=== Step 2: Uploading Protomaps to R2 ===${NC}"
echo "Destination: r2:${R2_BUCKET}/basemap/protomaps_planet.pmtiles"
echo "This will take several hours for 133GB..."
echo ""

rclone copy protomaps_planet.pmtiles r2:${R2_BUCKET}/basemap/ \
    --s3-upload-cutoff=200M \
    --s3-chunk-size=200M \
    --progress \
    --transfers=1

echo -e "${GREEN}Protomaps uploaded to R2!${NC}"
echo ""

# Delete local Protomaps file
echo "Deleting local Protomaps file to free space..."
rm -f protomaps_planet.pmtiles
echo -e "${GREEN}Local file deleted (freed ~133GB)${NC}"
echo ""

# ============================================
# STEP 3: Extract USA terrain from Mapterhorn
# ============================================
echo -e "${GREEN}=== Step 3: Extracting USA terrain from Mapterhorn ===${NC}"
echo "Source: $MAPTERHORN_URL (663GB planet)"
echo "Extracting USA bbox: $USA_BBOX"
echo "Max zoom: 14 (sufficient for 3D terrain)"
echo "Expected size: ~43GB"
echo ""

if [ -f "mapterhorn_usa.pmtiles" ]; then
    echo -e "${YELLOW}mapterhorn_usa.pmtiles already exists, skipping extract${NC}"
else
    pmtiles extract \
        --bbox="$USA_BBOX" \
        --maxzoom=14 \
        --download-threads=8 \
        "$MAPTERHORN_URL" \
        mapterhorn_usa.pmtiles
fi

echo -e "${GREEN}Mapterhorn USA extract complete!${NC}"
ls -lh mapterhorn_usa.pmtiles
echo ""

# ============================================
# STEP 4: Upload Mapterhorn to R2
# ============================================
echo -e "${GREEN}=== Step 4: Uploading Mapterhorn terrain to R2 ===${NC}"
echo "Destination: r2:${R2_BUCKET}/terrain/mapterhorn_usa.pmtiles"
echo ""

rclone copy mapterhorn_usa.pmtiles r2:${R2_BUCKET}/terrain/ \
    --s3-upload-cutoff=200M \
    --s3-chunk-size=200M \
    --progress \
    --transfers=1

echo -e "${GREEN}Mapterhorn uploaded to R2!${NC}"
echo ""

# Delete local Mapterhorn file
echo "Deleting local Mapterhorn file to free space..."
rm -f mapterhorn_usa.pmtiles
echo -e "${GREEN}Local file deleted (freed ~43GB)${NC}"
echo ""

# ============================================
# STEP 5: Verify uploads
# ============================================
echo -e "${GREEN}=== Step 5: Verifying uploads ===${NC}"
echo ""

echo "Checking R2 bucket contents..."
echo ""
echo "Basemap files:"
rclone ls r2:${R2_BUCKET}/basemap/ 2>/dev/null || echo "  (none yet)"
echo ""
echo "Terrain files:"
rclone ls r2:${R2_BUCKET}/terrain/ 2>/dev/null || echo "  (none yet)"

echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo "Files uploaded to R2:"
echo "  - basemap/protomaps_planet.pmtiles (~133GB)"
echo "  - terrain/mapterhorn_usa.pmtiles (~43GB)"
echo ""
echo "CDN URLs:"
echo "  - https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/basemap/protomaps_planet.pmtiles"
echo "  - https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/terrain/mapterhorn_usa.pmtiles"
echo ""
echo "Estimated monthly R2 cost for these files: ~\$2.60"
echo ""
echo -e "${YELLOW}Next step: Run the index.html update to use self-hosted tiles${NC}"
