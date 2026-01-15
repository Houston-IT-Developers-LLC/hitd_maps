#!/bin/bash
set -e

# ============================================================================
# Texas Parcel Data Download Script
# Source: TxGIO DataHub (https://tnris.org/stratmap/land-parcels)
# ============================================================================
# Downloads the StratMap Land Parcels statewide dataset from TNRIS.
# The download URL changes with each release, so user must provide it.
# ============================================================================

OUTPUT_DIR="${1:-./data-pipeline/downloads}"
DOWNLOAD_URL="$2"

echo "=============================================="
echo " Texas Parcel Data Download"
echo "=============================================="
echo ""
echo "Output directory: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# If no URL provided, show instructions
if [ -z "$DOWNLOAD_URL" ]; then
  cat << 'INSTRUCTIONS'
MANUAL STEP REQUIRED - Finding the Download URL
================================================

The TxGIO download URL changes with each quarterly release.
Follow these steps to find the current URL:

1. Visit: https://tnris.org/stratmap/land-parcels

2. Look for "Data Access" or "Download" section

3. Find the statewide Geodatabase (GDB) download option
   - Usually labeled "Statewide Download" or "Bulk Download"
   - File format should be .gdb.zip or similar

4. Right-click the download link and copy the URL

5. Run this script with the URL:

   ./download_texas.sh ./downloads "https://data.tnris.org/..."

ALTERNATIVE: Direct from TNRIS Data Hub
---------------------------------------
1. Visit: https://data.tnris.org/
2. Search for "StratMap Land Parcels"
3. Select the latest version
4. Download the Geodatabase format

NOTE: The dataset is approximately 2-5 GB compressed.
      Ensure you have sufficient disk space.

INSTRUCTIONS

  echo ""
  echo "ERROR: No download URL provided"
  echo ""
  echo "Usage: $0 <output_dir> <download_url>"
  echo ""
  echo "Example:"
  echo "  $0 ./downloads \"https://data.tnris.org/xyz/StratMap_Land_Parcels.gdb.zip\""
  echo ""
  exit 1
fi

# Determine filename from URL or use default
FILENAME=$(basename "$DOWNLOAD_URL" 2>/dev/null || echo "texas_parcels.gdb.zip")
# Ensure it has an extension
if [[ ! "$FILENAME" =~ \. ]]; then
  FILENAME="texas_parcels.gdb.zip"
fi

echo "Download URL: $DOWNLOAD_URL"
echo "Output file:  $OUTPUT_DIR/$FILENAME"
echo ""

# Check for curl
command -v curl >/dev/null 2>&1 || {
  echo "ERROR: curl is required but not installed."
  exit 1
}

# Download the file
echo "Downloading... (this may take 10-30 minutes)"
echo ""

curl -L \
  -o "$OUTPUT_DIR/$FILENAME" \
  --progress-bar \
  --fail \
  --retry 3 \
  --retry-delay 5 \
  "$DOWNLOAD_URL"

echo ""
echo "Download complete: $OUTPUT_DIR/$FILENAME"
echo ""

# Extract if it's a zip file
if [[ "$FILENAME" == *.zip ]]; then
  echo "Extracting archive..."

  # Check for unzip
  command -v unzip >/dev/null 2>&1 || {
    echo "WARNING: unzip not installed. Please extract manually."
    exit 0
  }

  cd "$OUTPUT_DIR"
  unzip -o "$FILENAME"

  echo ""
  echo "Extraction complete!"
fi

echo ""
echo "=============================================="
echo " Download Summary"
echo "=============================================="
echo ""
echo "Files in $OUTPUT_DIR:"
ls -lh "$OUTPUT_DIR"
echo ""

# Look for .gdb directory
GDB_DIR=$(find "$OUTPUT_DIR" -name "*.gdb" -type d 2>/dev/null | head -1)
if [ -n "$GDB_DIR" ]; then
  echo "Geodatabase found: $GDB_DIR"
  echo ""
  echo "Next step: Load to PostGIS with:"
  echo "  ./scripts/load_texas.sh \"$GDB_DIR\""
else
  echo "NOTE: Geodatabase directory not found."
  echo "      Check the extracted contents and locate the .gdb folder."
fi

echo ""
echo "Done!"
