#!/bin/bash
# Check coordinate systems of GeoJSON files
# Files with coordinates outside WGS84 range need reprojection

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/.."
cd "$DATA_DIR"

GEOJSON_DIR="output/geojson"

echo "=============================================="
echo "Coordinate System Check"
echo "=============================================="
echo "WGS84 range: longitude -180 to 180, latitude -90 to 90"
echo ""

needs_reproject=0
wgs84_count=0
error_count=0

for f in "$GEOJSON_DIR"/*.geojson; do
    filename=$(basename "$f")

    # Get first coordinate
    result=$(python3 -c "
import json
import sys
try:
    with open('$f') as file:
        data = json.load(file)
        if not data.get('features'):
            print('EMPTY')
            sys.exit(0)
        geom = data['features'][0].get('geometry')
        if not geom:
            print('NO_GEOM')
            sys.exit(0)
        coords = geom.get('coordinates')
        if not coords:
            print('NO_COORDS')
            sys.exit(0)
        # Handle different geometry types
        if geom['type'] == 'Point':
            c = coords
        elif geom['type'] in ['LineString', 'MultiPoint']:
            c = coords[0]
        elif geom['type'] in ['Polygon', 'MultiLineString']:
            c = coords[0][0]
        elif geom['type'] == 'MultiPolygon':
            c = coords[0][0][0]
        else:
            print('UNKNOWN_TYPE')
            sys.exit(0)

        # Check if WGS84
        if abs(c[0]) <= 180 and abs(c[1]) <= 90:
            print(f'WGS84:{c[0]:.4f},{c[1]:.4f}')
        else:
            print(f'PROJECTED:{c[0]:.1f},{c[1]:.1f}')
except Exception as e:
    print(f'ERROR:{e}')
" 2>&1)

    if [[ "$result" == WGS84:* ]]; then
        ((wgs84_count++))
    elif [[ "$result" == PROJECTED:* ]]; then
        echo "⚠️  $filename - $result"
        ((needs_reproject++))
    elif [[ "$result" == ERROR:* ]] || [[ "$result" == EMPTY* ]] || [[ "$result" == NO_* ]]; then
        echo "❌ $filename - $result"
        ((error_count++))
    fi
done

echo ""
echo "=============================================="
echo "Summary"
echo "=============================================="
echo "✓ WGS84 (ready): $wgs84_count"
echo "⚠️  Needs reprojection: $needs_reproject"
echo "❌ Errors/empty: $error_count"
echo ""

if [ $needs_reproject -gt 0 ]; then
    echo "Run ./scripts/reproject_to_wgs84.sh to fix projected files"
fi
