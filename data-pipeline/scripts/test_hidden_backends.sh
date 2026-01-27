#!/bin/bash
# Test Hidden ArcGIS Online Backends for Louisiana Parishes
# Method: Try common utility.arcgis.com and services.arcgis.com patterns

set -e

echo "=== Testing Hidden ArcGIS Backends for Blocked Louisiana Parishes ==="
echo ""

# Parish list with their GeoportalMaps/Atlas URLs
declare -A PARISHES=(
    ["rapides"]="https://rapc.org"
    ["st_john"]="https://www.sjbparish.com"
    ["st_martin"]="https://www.stmartinparish.org"
    ["avoyelles"]="https://www.avoyellesparish.org"
    ["lafourche"]="https://www.lafourchegov.org"
    ["west_baton_rouge"]="https://www.wbrcouncil.org"
)

# Function to test if URL returns valid ArcGIS service
test_endpoint() {
    local url=$1
    local parish=$2

    echo -n "Testing $parish: $url ... "

    response=$(curl -s -m 10 "$url?f=json" 2>/dev/null || echo "timeout")

    if echo "$response" | grep -q "\"layers\""; then
        echo "✅ FOUND!"
        echo "$parish: $url" >> /tmp/found_backends.txt

        # Get layer count
        layer_count=$(echo "$response" | grep -o "\"id\"" | wc -l)
        echo "  → $layer_count layers available"

        # Try to find parcel layer
        if echo "$response" | grep -qi "parcel"; then
            echo "  → 🎯 PARCEL LAYER FOUND!"
        fi
    elif echo "$response" | grep -q "timeout"; then
        echo "⏱️  Timeout"
    elif echo "$response" | grep -q "\"error\""; then
        echo "🔒 Access denied"
    else
        echo "❌ Not found"
    fi
}

# Common ArcGIS Online server patterns to test
# These are known hosting patterns for Louisiana parishes
COMMON_SERVERS=(
    "https://utility.arcgis.com/usrsvcs/servers"
    "https://services1.arcgis.com"
    "https://services2.arcgis.com"
    "https://services3.arcgis.com"
    "https://services6.arcgis.com"
    "https://services8.arcgis.com"
    "https://services9.arcgis.com"
)

# Sample server IDs seen in Louisiana deployments
SERVER_IDS=(
    "0e5f5ffb59b745f7bb82abb3d428da88"  # Livingston pattern
    "1234567890abcdef1234567890abcdef"   # Generic test
)

echo "Testing known patterns..."
echo ""

# Test Rapides RAPC
echo "=== RAPIDES PARISH (131K) ==="
test_endpoint "https://rapc.org/arcgis/rest/services" "rapides"
test_endpoint "https://gis.rapc.org/arcgis/rest/services" "rapides"

# Try to find their ArcGIS Server
echo ""
echo "Searching for RAPC ArcGIS Server..."
for subdomain in gis maps data www arcgis; do
    test_endpoint "https://${subdomain}.rapc.org/arcgis/rest/services" "rapides_${subdomain}"
done

echo ""
echo "=== ST. JOHN THE BAPTIST (43K) ==="
# St. John uses GeoportalMaps - try to find backend
for server in "${COMMON_SERVERS[@]}"; do
    # Try common service paths
    test_endpoint "${server}/Hosted/arcgis/rest/services/StJohn_Parcels/FeatureServer" "st_john_hosted"
done

echo ""
echo "=== LAFOURCHE PARISH (97K) ==="
# Lafourche uses qPublic/Schneider but may have ArcGIS backend
test_endpoint "https://gis.lafourchegov.org/arcgis/rest/services" "lafourche"
test_endpoint "https://lafourche-la.geoportalmaps.com/arcgis/rest/services" "lafourche_geoportal"

echo ""
echo "=== Summary ==="
if [ -f /tmp/found_backends.txt ]; then
    echo ""
    echo "✅ Found working backends:"
    cat /tmp/found_backends.txt
    echo ""
    echo "Next steps:"
    echo "1. Manually verify these endpoints have parcel data"
    echo "2. Create deployment scripts for successful parishes"
    echo "3. Run: python3 download_parish.py --endpoint <URL>"
else
    echo "❌ No hidden backends found via automated testing"
    echo ""
    echo "Manual investigation required:"
    echo "1. Visit parish GIS portals in browser"
    echo "2. Open DevTools (F12) → Network tab"
    echo "3. Click parcels layer and watch for FeatureServer requests"
    echo "4. Extract utility.arcgis.com or services.arcgis.com URLs"
fi

echo ""
echo "=== Alternative Methods ==="
echo "• Wait for St. Tammany migration (Feb 15)"
echo "• Contact Regional Planning Commissions"
echo "• Submit LDWF public records request"
echo "• Purchase Regrid data ($5,000-8,000 for all 50 parishes)"
echo ""
echo "Full strategy: /home/exx/Documents/C/hitd_maps/LOUISIANA_CREATIVE_ACQUISITION_METHODS.md"
