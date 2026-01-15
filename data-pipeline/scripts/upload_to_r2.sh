#!/bin/bash
set -e

# ============================================================================
# Upload Tiles to Cloudflare R2
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env.r2"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
else
  echo "ERROR: .env.r2 file not found at $ENV_FILE"
  echo "Please create it with your R2 credentials"
  exit 1
fi

FILE_PATH="$1"
REMOTE_NAME="${2:-$(basename "$FILE_PATH")}"

if [ -z "$FILE_PATH" ]; then
  echo "Usage: $0 <file_path> [remote_name]"
  echo ""
  echo "Examples:"
  echo "  $0 ./output/tiles/parcels_tx.pmtiles"
  echo "  $0 ./output/tiles/parcels_tx.pmtiles parcels/texas.pmtiles"
  exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
  echo "ERROR: File not found: $FILE_PATH"
  exit 1
fi

echo "=============================================="
echo " Uploading to Cloudflare R2"
echo "=============================================="
echo ""
echo "File: $FILE_PATH"
echo "Size: $(ls -lh "$FILE_PATH" | awk '{print $5}')"
echo "Destination: $R2_BUCKET_NAME/$REMOTE_NAME"
echo "Public URL: $R2_PUBLIC_URL/$REMOTE_NAME"
echo ""

# Check for AWS CLI (try multiple locations)
AWS_CMD="aws"
if ! command -v aws >/dev/null 2>&1; then
  if [ -x "/opt/homebrew/bin/aws" ]; then
    AWS_CMD="/opt/homebrew/bin/aws"
  elif command -v brew >/dev/null 2>&1; then
    echo "Installing AWS CLI..."
    brew install awscli
  else
    echo "ERROR: AWS CLI not found. Install it with: brew install awscli"
    exit 1
  fi
fi

# Configure AWS CLI for R2
export AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="auto"

echo "Uploading..."
$AWS_CMD s3 cp "$FILE_PATH" "s3://$R2_BUCKET_NAME/$REMOTE_NAME" \
  --endpoint-url "$R2_ENDPOINT" \
  --no-progress

echo ""
echo "=============================================="
echo " Upload Complete!"
echo "=============================================="
echo ""
echo "Public URL: $R2_PUBLIC_URL/$REMOTE_NAME"
echo ""
