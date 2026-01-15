#!/bin/bash
set -e

# ============================================================================
# Export Texas Parcels from TNRIS ArcGIS Feature Service
# ============================================================================
# Queries the TNRIS StratMap Land Parcels service county-by-county and
# exports to GeoJSON files. Each county is queried in chunks of 2000 records.
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${1:-$SCRIPT_DIR/../output/geojson}"
COMBINED_OUTPUT="$OUTPUT_DIR/parcels_tx.geojson"

# TNRIS ArcGIS Feature Service
TNRIS_SERVICE="https://feature.tnris.org/arcgis/rest/services/Parcels/stratmap25_land_parcels_48/MapServer/0/query"

# Fields to export (reduce file size by selecting only needed fields)
OUT_FIELDS="objectid,prop_id,geo_id,owner_name,county,situs_addr,situs_city,mkt_value,land_value,imp_value,legal_area,gis_area,lgl_area_unit,tax_year"

echo "=============================================="
echo " Texas Parcel Export from TNRIS"
echo "=============================================="
echo ""
echo "Output directory: $OUTPUT_DIR"
echo ""

mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/counties"

# Get list of all Texas counties
COUNTIES_FILE="$SCRIPT_DIR/../texas_counties.txt"

if [ -f "$COUNTIES_FILE" ]; then
  echo "Loading counties from $COUNTIES_FILE..."
  COUNTIES=$(cat "$COUNTIES_FILE")
else
  echo "Fetching county list from TNRIS..."
  COUNTIES=$(curl -s "$TNRIS_SERVICE?where=1%3D1&outFields=county&returnGeometry=false&returnDistinctValues=true&f=json" | \
    python3 -c "import sys,json; data=json.load(sys.stdin); print('\n'.join(sorted(set(f['attributes']['county'] for f in data.get('features',[]) if f['attributes'].get('county')))))" 2>/dev/null || echo "")
fi

if [ -z "$COUNTIES" ]; then
  echo "ERROR: Could not load county list"
  echo "Please create $COUNTIES_FILE with one county per line"
  exit 1
fi

TOTAL_COUNTIES=$(echo "$COUNTIES" | wc -l | tr -d ' ')
echo "Found $TOTAL_COUNTIES counties"
echo ""

# Counter
PROCESSED=0
TOTAL_FEATURES=0

# Process each county
while IFS= read -r COUNTY; do
  [ -z "$COUNTY" ] && continue

  PROCESSED=$((PROCESSED + 1))
  COUNTY_FILE="$OUTPUT_DIR/counties/${COUNTY// /_}.geojson"

  echo "[$PROCESSED/$TOTAL_COUNTIES] Processing $COUNTY County..."

  # Skip if already exists and has data
  if [ -f "$COUNTY_FILE" ] && [ -s "$COUNTY_FILE" ]; then
    EXISTING_COUNT=$(python3 -c "import json; f=open('$COUNTY_FILE'); d=json.load(f); print(len(d.get('features',[])))" 2>/dev/null || echo "0")
    if [ "$EXISTING_COUNT" -gt "0" ]; then
      echo "  Skipping - already exported ($EXISTING_COUNT features)"
      TOTAL_FEATURES=$((TOTAL_FEATURES + EXISTING_COUNT))
      continue
    fi
  fi

  # Query this county with pagination
  OFFSET=0
  COUNTY_FEATURES=0
  TEMP_FILES=""

  while true; do
    # URL encode county name
    COUNTY_ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$COUNTY'))")

    # Query with offset
    QUERY_URL="$TNRIS_SERVICE?where=county%3D%27$COUNTY_ENCODED%27&outFields=$OUT_FIELDS&returnGeometry=true&outSR=4326&f=geojson&resultOffset=$OFFSET&resultRecordCount=2000"

    TEMP_FILE="/tmp/tnris_${COUNTY// /_}_$OFFSET.geojson"

    # Fetch chunk
    HTTP_CODE=$(curl -s -w "%{http_code}" -o "$TEMP_FILE" "$QUERY_URL")

    if [ "$HTTP_CODE" != "200" ]; then
      echo "  Warning: HTTP $HTTP_CODE at offset $OFFSET"
      break
    fi

    # Check if we got features
    CHUNK_COUNT=$(python3 -c "import json; f=open('$TEMP_FILE'); d=json.load(f); print(len(d.get('features',[])))" 2>/dev/null || echo "0")

    if [ "$CHUNK_COUNT" -eq "0" ]; then
      rm -f "$TEMP_FILE"
      break
    fi

    TEMP_FILES="$TEMP_FILES $TEMP_FILE"
    COUNTY_FEATURES=$((COUNTY_FEATURES + CHUNK_COUNT))
    OFFSET=$((OFFSET + 2000))

    echo "    Fetched $CHUNK_COUNT features (total: $COUNTY_FEATURES)"

    # Rate limiting - be nice to the API
    sleep 0.5
  done

  # Combine chunks for this county
  if [ -n "$TEMP_FILES" ]; then
    if [ $(echo "$TEMP_FILES" | wc -w) -eq 1 ]; then
      mv $TEMP_FILES "$COUNTY_FILE"
    else
      # Merge multiple GeoJSON files
      python3 << PYEOF
import json
import glob

features = []
for f in "$TEMP_FILES".split():
    with open(f) as fp:
        data = json.load(fp)
        features.extend(data.get('features', []))

output = {
    "type": "FeatureCollection",
    "features": features
}

with open("$COUNTY_FILE", "w") as fp:
    json.dump(output, fp)

print(f"  Combined {len(features)} features")
PYEOF
      rm -f $TEMP_FILES
    fi

    TOTAL_FEATURES=$((TOTAL_FEATURES + COUNTY_FEATURES))
    echo "  Saved: $COUNTY_FILE ($COUNTY_FEATURES features)"
  else
    echo "  No features found for $COUNTY County"
  fi

done <<< "$COUNTIES"

echo ""
echo "=============================================="
echo " Combining all counties..."
echo "=============================================="

# Combine all county files into one
python3 << 'PYEOF'
import json
import glob
import os

output_dir = os.environ.get('OUTPUT_DIR', './output/geojson')
county_files = glob.glob(f"{output_dir}/counties/*.geojson")

all_features = []
for f in sorted(county_files):
    try:
        with open(f) as fp:
            data = json.load(fp)
            features = data.get('features', [])
            all_features.extend(features)
            print(f"  Added {len(features):,} from {os.path.basename(f)}")
    except Exception as e:
        print(f"  Error reading {f}: {e}")

print(f"\nTotal features: {len(all_features):,}")

output = {
    "type": "FeatureCollection",
    "features": all_features
}

output_file = f"{output_dir}/parcels_tx.geojson"
with open(output_file, "w") as fp:
    json.dump(output, fp)

print(f"Saved to: {output_file}")
print(f"File size: {os.path.getsize(output_file) / (1024*1024*1024):.2f} GB")
PYEOF

echo ""
echo "=============================================="
echo " Export Complete!"
echo "=============================================="
echo ""
echo "Total features exported: $TOTAL_FEATURES"
echo "Combined file: $COMBINED_OUTPUT"
echo ""
echo "Next step: Generate tiles with:"
echo "  ./scripts/generate_tiles.sh $OUTPUT_DIR ./output/tiles TX"
echo ""
