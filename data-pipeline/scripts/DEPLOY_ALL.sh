#!/bin/bash
###############################################################################
# HITD Maps - MAXIMUM POWER DEPLOYMENT
###############################################################################
# Deploy ALL AI agents to scrape all partial states and upload to Cloudflare R2
#
# System: 48 cores, 471 GB RAM
# Target: ~1000+ missing counties across 14 states
#
# Usage: ./DEPLOY_ALL.sh
###############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data"
LOG_DIR="$SCRIPT_DIR/../logs"

mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/deployment_$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Banner
echo ""
echo "================================================================================"
echo "  HITD MAPS - MEGA DEPLOYMENT"
echo "================================================================================"
echo "  System Resources:"
echo "  - CPU Cores: 48"
echo "  - Available RAM: 471 GB"
echo "  - Target: ~1000+ counties across 14 states"
echo ""
echo "  Phases:"
echo "  1. AI County Source Discovery (Ollama @ 10.8.0.1:11434)"
echo "  2. Parallel Download (24 workers)"
echo "  3. Parallel Processing (16 workers: ogr2ogr + tippecanoe)"
echo "  4. Parallel Upload to R2 (8 workers)"
echo "  5. Verification & Tracking Updates"
echo "================================================================================"
echo ""

# Check Ollama
info "Checking Ollama AI server..."
if curl -s "http://10.8.0.1:11434/api/tags" > /dev/null 2>&1; then
    log "✓ Ollama AI server is running"
else
    error "✗ Ollama AI server not reachable at 10.8.0.1:11434"
    exit 1
fi

# Check required tools
info "Checking required tools..."
for tool in python3 tippecanoe pmtiles ogr2ogr aws; do
    if command -v $tool &> /dev/null; then
        log "✓ $tool found"
    else
        error "✗ $tool not found!"
        exit 1
    fi
done

# Check Python packages
info "Checking Python packages..."
python3 -c "import aiohttp, requests, boto3" 2>/dev/null
if [ $? -eq 0 ]; then
    log "✓ Python packages OK"
else
    error "✗ Missing Python packages. Run: pip install aiohttp requests boto3"
    exit 1
fi

echo ""
read -p "Ready to deploy? This will use maximum system resources. Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    warn "Deployment cancelled"
    exit 0
fi

echo ""
log "🚀 DEPLOYMENT STARTED"
echo ""

###############################################################################
# PHASE 1: AI County Source Discovery
###############################################################################

log "PHASE 1: AI County Source Discovery"
log "Using Ollama llama3.3:70b to find county parcel APIs..."

cd "$SCRIPT_DIR/.."

# Priority states first (top 30 counties each)
PRIORITY_STATES="GA IL MI"

for state in $PRIORITY_STATES; do
    log "🤖 Finding sources for $state (top 30 counties)..."
    python3 scripts/ai_county_finder_deployer.py \
        --state "$state" \
        --find-all-counties \
        --limit 30 2>&1 | tee -a "$LOG_FILE"
done

# Remaining states (top 15 counties each)
REMAINING_STATES="MO AL LA OK OR SC AZ KS KY MS SD"

for state in $REMAINING_STATES; do
    log "🤖 Finding sources for $state (top 15 counties)..."
    python3 scripts/ai_county_finder_deployer.py \
        --state "$state" \
        --find-all-counties \
        --limit 15 2>&1 | tee -a "$LOG_FILE"
done

if [ ! -f "$DATA_DIR/ai_found_county_sources.json" ]; then
    error "Failed to find county sources!"
    exit 1
fi

FOUND_COUNT=$(python3 -c "import json; data=json.load(open('$DATA_DIR/ai_found_county_sources.json')); print(data.get('total_counties', 0))")
log "✓ Found $FOUND_COUNT county sources"

###############################################################################
# PHASE 2-4: Download, Process, Upload (All Parallel)
###############################################################################

log "PHASE 2-4: Parallel Download/Process/Upload"
log "Deploying max workers: Download(24) + Process(16) + Upload(8)..."

python3 scripts/ai_county_finder_deployer.py \
    --deploy-all 2>&1 | tee -a "$LOG_FILE"

if [ $? -ne 0 ]; then
    error "Deployment failed!"
    exit 1
fi

###############################################################################
# PHASE 5: Update Tracking & Generate Report
###############################################################################

log "PHASE 5: Updating tracking files..."

# Regenerate coverage status
log "Generating fresh coverage report..."
python3 scripts/generate_coverage_report.py 2>&1 | tee -a "$LOG_FILE"

# Update valid parcels list
log "Updating valid_parcels.json..."
aws s3 ls s3://gspot-tiles/parcels/ --endpoint-url "$R2_ENDPOINT" \
    | grep ".pmtiles" \
    | awk '{print $4}' \
    | sed 's/.pmtiles$//' \
    > /tmp/r2_parcels_list.txt

python3 -c "
import json
from pathlib import Path

# Read current valid parcels
valid_file = Path('$DATA_DIR/valid_parcels.json')
if valid_file.exists():
    with open(valid_file) as f:
        current = set(json.load(f))
else:
    current = set()

# Read R2 list
with open('/tmp/r2_parcels_list.txt') as f:
    r2_files = set(line.strip() for line in f if line.strip())

# Combine and save
all_files = sorted(current | r2_files)

with open(valid_file, 'w') as f:
    json.dump(all_files, f, indent=2)

print(f'Updated valid_parcels.json: {len(all_files)} files')
"

###############################################################################
# FINAL REPORT
###############################################################################

echo ""
echo "================================================================================"
log "🎉 DEPLOYMENT COMPLETE!"
echo "================================================================================"

# Generate stats
TOTAL_FILES=$(aws s3 ls s3://gspot-tiles/parcels/ --endpoint-url "$R2_ENDPOINT" | grep ".pmtiles" | wc -l)
TOTAL_SIZE=$(aws s3 ls s3://gspot-tiles/parcels/ --recursive --endpoint-url "$R2_ENDPOINT" --summarize | grep "Total Size" | awk '{print $3}')
TOTAL_SIZE_GB=$(echo "scale=2; $TOTAL_SIZE / 1024 / 1024 / 1024" | bc)

echo ""
info "Final Statistics:"
info "  Total Parcel Files: $TOTAL_FILES"
info "  Total Size: ${TOTAL_SIZE_GB} GB"
info "  Log File: $LOG_FILE"
echo ""

# Check coverage
log "Generating final coverage report..."
python3 scripts/generate_coverage_report.py --summary 2>&1 | tee -a "$LOG_FILE"

echo ""
log "🌎 All data deployed to Cloudflare R2 CDN:"
log "   https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels/"
echo ""

echo "================================================================================"
log "✓ Deployment log saved to: $LOG_FILE"
echo "================================================================================"
