#!/bin/bash
# Reproject GeoJSON files from projected CRS to WGS84 (EPSG:4326)
# Requires GDAL: sudo apt-get install -y gdal-bin

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/.."
cd "$DATA_DIR"

GEOJSON_DIR="output/geojson"
BACKUP_DIR="output/geojson_projected"
LOG_DIR="logs"
PARALLEL_JOBS=${PARALLEL_JOBS:-8}

mkdir -p "$BACKUP_DIR" "$LOG_DIR"

echo "=============================================="
echo "Reproject GeoJSON to WGS84"
echo "=============================================="

# Check for ogr2ogr
if ! command -v ogr2ogr &> /dev/null; then
    echo "ERROR: ogr2ogr not found. Install GDAL:"
    echo "  sudo apt-get install -y gdal-bin"
    exit 1
fi

echo "Using: $(ogr2ogr --version)"
echo ""

# Function to check if file needs reprojection
needs_reprojection() {
    local file="$1"
    python3 -c "
import json
import sys
try:
    with open('$file') as f:
        data = json.load(f)
        if not data.get('features'):
            sys.exit(1)
        geom = data['features'][0].get('geometry')
        if not geom or not geom.get('coordinates'):
            sys.exit(1)
        coords = geom['coordinates']
        # Get first coordinate based on geometry type
        if geom['type'] == 'Point':
            c = coords
        elif geom['type'] in ['LineString', 'MultiPoint']:
            c = coords[0]
        elif geom['type'] in ['Polygon', 'MultiLineString']:
            c = coords[0][0]
        elif geom['type'] == 'MultiPolygon':
            c = coords[0][0][0]
        else:
            sys.exit(1)
        # Check if outside WGS84 range
        if abs(c[0]) > 180 or abs(c[1]) > 90:
            sys.exit(0)  # Needs reprojection
        sys.exit(1)  # Already WGS84
except:
    sys.exit(1)
" 2>/dev/null
    return $?
}

# Function to detect CRS and reproject
reproject_file() {
    local input_file="$1"
    local filename=$(basename "$input_file")
    local backup_file="$BACKUP_DIR/$filename"
    local temp_file="${input_file}.tmp"
    local log_file="$LOG_DIR/reproject_${filename%.geojson}.log"

    echo "Processing: $filename"

    # Backup original
    cp "$input_file" "$backup_file"

    # Most parcel data is in Web Mercator (EPSG:3857) or State Plane
    # Try Web Mercator first, then let GDAL auto-detect
    if ogr2ogr -f GeoJSON -s_srs EPSG:3857 -t_srs EPSG:4326 "$temp_file" "$input_file" 2>"$log_file"; then
        # Verify the output has valid coordinates
        if python3 -c "
import json
with open('$temp_file') as f:
    data = json.load(f)
    c = data['features'][0]['geometry']['coordinates'][0][0]
    if abs(c[0]) <= 180 and abs(c[1]) <= 90:
        exit(0)
    exit(1)
" 2>/dev/null; then
            mv "$temp_file" "$input_file"
            echo "  ✓ Reprojected from Web Mercator (EPSG:3857)"
            return 0
        fi
        rm -f "$temp_file"
    fi

    # Try with auto-detection (if file has embedded CRS info)
    if ogr2ogr -f GeoJSON -t_srs EPSG:4326 "$temp_file" "$input_file" 2>>"$log_file"; then
        if python3 -c "
import json
with open('$temp_file') as f:
    data = json.load(f)
    c = data['features'][0]['geometry']['coordinates'][0][0]
    if abs(c[0]) <= 180 and abs(c[1]) <= 90:
        exit(0)
    exit(1)
" 2>/dev/null; then
            mv "$temp_file" "$input_file"
            echo "  ✓ Reprojected with auto-detected CRS"
            return 0
        fi
        rm -f "$temp_file"
    fi

    # Restore from backup if all attempts failed
    cp "$backup_file" "$input_file"
    echo "  ✗ Failed to reproject (see $log_file)"
    return 1
}

export -f needs_reprojection reproject_file
export BACKUP_DIR LOG_DIR

# Find files needing reprojection
files_to_process=()
for f in "$GEOJSON_DIR"/*.geojson; do
    if needs_reprojection "$f"; then
        files_to_process+=("$f")
    fi
done

total=${#files_to_process[@]}

if [ $total -eq 0 ]; then
    echo "All files are already in WGS84. Nothing to do."
    exit 0
fi

echo "Found $total files needing reprojection"
echo "Backup directory: $BACKUP_DIR"
echo "=============================================="

# Process files
success=0
failed=0

for f in "${files_to_process[@]}"; do
    if reproject_file "$f"; then
        ((success++))
    else
        ((failed++))
    fi
done

echo ""
echo "=============================================="
echo "Reprojection complete!"
echo "Success: $success"
echo "Failed: $failed"
echo "Originals backed up to: $BACKUP_DIR"
echo "=============================================="
