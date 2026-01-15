#!/bin/bash
# NLCD Download Script
# Note: The MRLC/ScienceBase downloads require CAPTCHA verification
# This script provides manual download instructions and verification

OUTPUT_DIR="/home/exx/Documents/C/hitd_maps/data-pipeline/output/landcover"
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "NLCD 2021 Data Download Guide"
echo "=========================================="
echo ""
echo "The NLCD data requires manual download due to CAPTCHA verification."
echo ""
echo "STEP 1: Download NLCD 2021 Land Cover (CONUS)"
echo "   URL: https://www.sciencebase.gov/catalog/item/649595d8d34ef77fcb01dca1"
echo "   File: nlcd_2021_land_cover_l48_20230630.zip (~1.9 GB)"
echo ""
echo "STEP 2: Download NLCD 2021 Tree Canopy Cover"  
echo "   URL: https://www.sciencebase.gov/catalog/item/649595e9d34ef77fcb01dca3"
echo "   File: nlcd_tcc_conus_2021_v2021-4.zip (~1-2 GB)"
echo ""
echo "STEP 3: Save downloaded files to:"
echo "   $OUTPUT_DIR"
echo ""
echo "STEP 4: Run this script again to verify and extract"
echo ""

# Check if files exist
if [ -f "$OUTPUT_DIR/nlcd_2021_land_cover_l48_20230630.zip" ]; then
    echo "[OK] Land Cover file found"
    unzip -l "$OUTPUT_DIR/nlcd_2021_land_cover_l48_20230630.zip" | head -5
    
    echo ""
    echo "Extracting..."
    cd "$OUTPUT_DIR" && unzip -o nlcd_2021_land_cover_l48_20230630.zip
    echo "Done extracting Land Cover"
else
    echo "[MISSING] nlcd_2021_land_cover_l48_20230630.zip"
fi

echo ""

if [ -f "$OUTPUT_DIR/nlcd_tcc_conus_2021_v2021-4.zip" ]; then
    echo "[OK] Tree Canopy file found"
    unzip -l "$OUTPUT_DIR/nlcd_tcc_conus_2021_v2021-4.zip" | head -5
    
    echo ""
    echo "Extracting..."
    cd "$OUTPUT_DIR" && unzip -o nlcd_tcc_conus_2021_v2021-4.zip
    echo "Done extracting Tree Canopy"
else
    echo "[MISSING] nlcd_tcc_conus_2021_v2021-4.zip"
fi

echo ""
echo "=========================================="
echo "After download, you can convert to tiles with:"
echo "gdal2tiles.py -z 5-14 -w none nlcd_2021_land_cover_l48_20230630.img tiles/"
echo "=========================================="
