#!/bin/bash
# R2 Duplicate Cleanup Script
# Generated: 2026-01-27
# Removes 29 old/duplicate PMTiles versions from R2
# Saves ~3.1 GB of storage

set -e

export AWS_ACCESS_KEY_ID=ecd653afe3300fdc045b9980df0dbb14
export AWS_SECRET_ACCESS_KEY=c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35
ENDPOINT="https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

echo "========================================"
echo "R2 Duplicate Cleanup"
echo "========================================"
echo "This will remove 29 old/duplicate files"
echo "and save ~3.1 GB of storage"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Removing old versions from R2..."

aws s3 rm s3://gspot-tiles/parcels/parcels_ca_orange.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_ca_sacramento.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_ct_statewide.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_ga_gwinnett.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_il_dupage.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_la_orleans.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_mi_kent.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_mi_oakland_v2.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_mo_clay_v2.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_mo_st_charles_v2.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_mo_st_charles.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_mt_statewide.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_nc_durham.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_nc_forsyth_wgs84.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_nc_guilford_wgs84.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_nc_mecklenburg_wgs84.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_ny_statewide.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_sd_beadle_wgs84.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_sd_codington.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_tx_harris_v2.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_tx_harris.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_tx_statewide.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_tx_tarrant.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_tx_travis.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_tx_williamson.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_va_statewide.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_wa_king_wgs84.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_wa_spokane_wgs84.pmtiles --endpoint-url $ENDPOINT
aws s3 rm s3://gspot-tiles/parcels/parcels_wi_milwaukee_v2.pmtiles --endpoint-url $ENDPOINT

echo ""
echo "✓ Cleanup complete!"
echo "Removed 29 files, saved ~3.1 GB"
echo ""
echo "Note: valid_parcels.json has already been updated"
echo "Run verify_all_parcels.py to confirm cleanup"
