#!/bin/bash
# =============================================================================
# Setup Self-Hosted Basemap PMTiles
# =============================================================================
# Downloads Protomaps planet tiles and uploads to Cloudflare R2
#
# Requirements:
#   - wget or curl
#   - AWS CLI configured for R2 (see upload_all_to_r2.py for credentials)
#   - ~80GB free disk space temporarily
#
# Usage:
#   ./scripts/setup_basemap.sh
#
# =============================================================================

set -e

# Configuration
PROTOMAPS_URL="https://build.protomaps.com/20240101.pmtiles"  # ~70GB
OUTPUT_DIR="output/basemap"
OUTPUT_FILE="$OUTPUT_DIR/planet.pmtiles"

# R2 Configuration
R2_BUCKET="gspot-tiles"
R2_ENDPOINT="https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PATH="basemap/planet.pmtiles"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  GSpot Basemap Setup - Self-Hosted Protomaps Tiles${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if already downloaded
if [ -f "$OUTPUT_FILE" ]; then
    echo -e "${YELLOW}Basemap already downloaded: $OUTPUT_FILE${NC}"
    echo "Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
    read -p "Re-download? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping download..."
    else
        rm "$OUTPUT_FILE"
    fi
fi

# Download if needed
if [ ! -f "$OUTPUT_FILE" ]; then
    echo -e "${GREEN}Downloading Protomaps planet tiles...${NC}"
    echo "Source: $PROTOMAPS_URL"
    echo "Destination: $OUTPUT_FILE"
    echo ""
    echo -e "${YELLOW}This is ~70GB and will take a while depending on your connection.${NC}"
    echo ""

    # Get latest build URL from Protomaps
    echo "Fetching latest build info..."
    LATEST_URL=$(curl -s "https://build.protomaps.com/" | grep -oP 'href="\K[0-9]+\.pmtiles' | head -1)

    if [ -n "$LATEST_URL" ]; then
        PROTOMAPS_URL="https://build.protomaps.com/$LATEST_URL"
        echo -e "${GREEN}Latest build: $PROTOMAPS_URL${NC}"
    fi

    # Download with resume support
    wget -c -O "$OUTPUT_FILE" "$PROTOMAPS_URL" || {
        echo -e "${RED}wget failed, trying curl...${NC}"
        curl -C - -L -o "$OUTPUT_FILE" "$PROTOMAPS_URL"
    }

    echo -e "${GREEN}Download complete!${NC}"
    echo "Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
fi

# Verify download
echo ""
echo "Verifying PMTiles file..."
if command -v pmtiles &> /dev/null; then
    pmtiles show "$OUTPUT_FILE" | head -20
else
    echo -e "${YELLOW}pmtiles CLI not installed, skipping verification${NC}"
    echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
fi

# Upload to R2
echo ""
echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  Uploading to Cloudflare R2${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI not found. Install it first:${NC}"
    echo "  pip install awscli"
    exit 1
fi

# Set R2 credentials (from PMTILES_WORKFLOW.md)
export AWS_ACCESS_KEY_ID="ecd653afe3300fdc045b9980df0dbb14"
export AWS_SECRET_ACCESS_KEY="c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

echo "Uploading to: s3://$R2_BUCKET/$R2_PATH"
echo "Endpoint: $R2_ENDPOINT"
echo ""
echo -e "${YELLOW}This will take a while for a 70GB file...${NC}"
echo ""

aws s3 cp "$OUTPUT_FILE" "s3://$R2_BUCKET/$R2_PATH" \
    --endpoint-url "$R2_ENDPOINT" \
    --no-progress

echo ""
echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  Upload Complete!${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""
echo "Your basemap is now available at:"
echo -e "${GREEN}https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/basemap/planet.pmtiles${NC}"
echo ""
echo "The Flutter app will automatically use this via the style in:"
echo "  assets/map/basemap_style.json"
echo ""

# Optional: Clean up local file
echo ""
read -p "Delete local file to save disk space? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm "$OUTPUT_FILE"
    echo "Local file deleted."
else
    echo "Local file kept at: $OUTPUT_FILE"
fi

echo ""
echo -e "${GREEN}Done!${NC}"
