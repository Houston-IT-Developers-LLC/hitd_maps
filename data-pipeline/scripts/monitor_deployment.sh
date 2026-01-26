#!/bin/bash
###############################################################################
# HITD Maps - Deployment Monitor
###############################################################################
# Real-time monitoring of the mega deployment
# Usage: ./monitor_deployment.sh
###############################################################################

LOG_FILE="/tmp/deployment_live.log"
DATA_DIR="$(dirname "$0")/../data"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

clear

while true; do
    clear
    echo "================================================================================"
    echo "  HITD MAPS - DEPLOYMENT MONITOR"
    echo "================================================================================"
    echo ""

    # Current phase
    CURRENT_PHASE=$(tail -100 "$LOG_FILE" 2>/dev/null | grep "PHASE" | tail -1)
    echo -e "${BLUE}Current Phase:${NC}"
    echo "  $CURRENT_PHASE"
    echo ""

    # AI Search Progress
    echo -e "${BLUE}AI Search Progress:${NC}"
    if [ -f "$DATA_DIR/ai_found_county_sources.json" ]; then
        FOUND=$(python3 -c "import json; data=json.load(open('$DATA_DIR/ai_found_county_sources.json')); print(data.get('total_counties', 0))" 2>/dev/null)
        echo -e "  ${GREEN}✓${NC} Found: $FOUND county sources"
    else
        echo "  🤖 AI searching for county sources..."
    fi

    # Recent activity
    echo ""
    echo -e "${BLUE}Recent Activity (last 15 lines):${NC}"
    tail -15 "$LOG_FILE" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g'

    # Downloads
    echo ""
    echo -e "${BLUE}Downloaded Files:${NC}"
    GEOJSON_COUNT=$(find "$(dirname "$0")/../output/geojson" -name "*.geojson" 2>/dev/null | wc -l)
    echo "  GeoJSON: $GEOJSON_COUNT files"

    # Processed
    echo -e "${BLUE}Processed Files:${NC}"
    PMTILES_COUNT=$(find "$(dirname "$0")/../output/pmtiles" -name "*.pmtiles" 2>/dev/null | wc -l)
    echo "  PMTiles: $PMTILES_COUNT files"

    # R2 Status
    echo ""
    echo -e "${BLUE}R2 Upload Status:${NC}"
    echo "  (Checking R2 requires AWS CLI - use 'aws s3 ls' manually)"

    # System resources
    echo ""
    echo -e "${BLUE}System Resources:${NC}"
    FREE_MEM=$(free -h | grep "Mem:" | awk '{print $7}')
    LOAD=$(uptime | awk -F'load average:' '{print $2}')
    echo "  Free RAM: $FREE_MEM"
    echo "  Load Average:$LOAD"

    echo ""
    echo "================================================================================"
    echo "Press Ctrl+C to exit monitor (deployment continues in background)"
    echo "Refreshing in 10 seconds..."
    echo "================================================================================"

    sleep 10
done
