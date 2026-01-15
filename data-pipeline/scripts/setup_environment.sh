#!/bin/bash
#
# Setup Environment for HITD Maps Data Pipeline
# ==============================================
# This script installs all dependencies needed for the data pipeline
# to run autonomously. Supports both local development and server deployments.
#
# Usage: ./scripts/setup_environment.sh [--dev|--server|--ci]
#
# Options:
#   --dev     Development setup (lighter dependencies)
#   --server  Full server setup with all tools
#   --ci      CI/CD setup (minimal, no interactive prompts)
#

set -e

SETUP_MODE="${1:-server}"

echo "=============================================="
echo "HITD Maps - Data Pipeline Setup"
echo "Mode: $SETUP_MODE"
echo "=============================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DATA_PIPELINE_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ==== 1. System Dependencies ====
echo ""
echo "1. Installing System Dependencies..."
echo "------------------------------------"

# Check for apt (Debian/Ubuntu)
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y \
        gdal-bin \
        python3 \
        python3-pip \
        python3-venv \
        jq \
        curl \
        git \
        build-essential \
        libsqlite3-dev \
        zlib1g-dev
    print_status "System packages installed"
else
    print_warning "apt-get not found. Please install manually:"
    echo "  - gdal-bin (for ogr2ogr)"
    echo "  - python3, python3-pip, python3-venv"
    echo "  - jq, curl, git"
fi

# ==== 2. Tippecanoe ====
echo ""
echo "2. Installing Tippecanoe..."
echo "---------------------------"

if command -v tippecanoe &> /dev/null; then
    print_status "Tippecanoe already installed: $(tippecanoe --version 2>&1 | head -1)"
else
    echo "Building Tippecanoe from source..."
    TMP_DIR=$(mktemp -d)
    cd "$TMP_DIR"
    git clone https://github.com/felt/tippecanoe.git
    cd tippecanoe
    make -j$(nproc)
    sudo make install
    cd "$DATA_PIPELINE_DIR"
    rm -rf "$TMP_DIR"
    print_status "Tippecanoe installed: $(tippecanoe --version 2>&1 | head -1)"
fi

# ==== 3. PMTiles CLI (optional but useful) ====
echo ""
echo "3. Installing PMTiles CLI..."
echo "----------------------------"

if command -v pmtiles &> /dev/null; then
    print_status "PMTiles CLI already installed"
else
    # Download latest release
    PMTILES_VERSION="1.10.5"
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        PMTILES_ARCH="x86_64"
    elif [ "$ARCH" = "aarch64" ]; then
        PMTILES_ARCH="arm64"
    else
        PMTILES_ARCH="x86_64"
    fi

    echo "Downloading PMTiles CLI v${PMTILES_VERSION}..."
    curl -sSL "https://github.com/protomaps/go-pmtiles/releases/download/v${PMTILES_VERSION}/pmtiles_${PMTILES_VERSION}_Linux_${PMTILES_ARCH}.tar.gz" | sudo tar xz -C /usr/local/bin pmtiles
    print_status "PMTiles CLI installed"
fi

# ==== 4. Python Virtual Environment ====
echo ""
echo "4. Setting up Python Environment..."
echo "------------------------------------"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Created virtual environment"
else
    print_status "Virtual environment already exists"
fi

# Activate and install packages
source venv/bin/activate

pip install --upgrade pip
pip install \
    boto3 \
    aiohttp \
    requests \
    botocore

print_status "Python packages installed"

# ==== 5. Create Environment File ====
echo ""
echo "5. Creating Environment File..."
echo "--------------------------------"

ENV_FILE="$DATA_PIPELINE_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'EOF'
# Cloudflare R2 Credentials
R2_ACCESS_KEY=ecd653afe3300fdc045b9980df0dbb14
R2_SECRET_KEY=c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35
R2_BUCKET=gspot-tiles
R2_ENDPOINT=https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev

# Ollama (for AI agent)
OLLAMA_BASE=http://10.8.0.1:11434
OLLAMA_MODEL=qwen2.5:72b

# Processing settings
PARALLEL_JOBS=8
MAX_WORKERS=4
EOF
    print_status "Created .env file"
else
    print_status ".env file already exists"
fi

# ==== 6. Create Directory Structure ====
echo ""
echo "6. Creating Directory Structure..."
echo "-----------------------------------"

mkdir -p output/geojson/counties
mkdir -p output/geojson/reprojected
mkdir -p output/pmtiles
mkdir -p logs
mkdir -p agent

print_status "Directory structure created"

# ==== 7. Verify Installation ====
echo ""
echo "7. Verifying Installation..."
echo "----------------------------"

echo ""
echo "GDAL Version:"
ogr2ogr --version || print_error "ogr2ogr not found"

echo ""
echo "Tippecanoe Version:"
tippecanoe --version 2>&1 | head -1 || print_error "tippecanoe not found"

echo ""
echo "Python Version:"
python3 --version || print_error "python3 not found"

echo ""
echo "Boto3 Version:"
python3 -c "import boto3; print(f'boto3 {boto3.__version__}')" || print_error "boto3 not installed"

# ==== 8. Test R2 Connection ====
echo ""
echo "8. Testing R2 Connection..."
echo "---------------------------"

python3 << 'PYEOF'
import boto3
try:
    client = boto3.client(
        's3',
        endpoint_url='https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com',
        aws_access_key_id='ecd653afe3300fdc045b9980df0dbb14',
        aws_secret_access_key='c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35',
    )
    response = client.list_objects_v2(Bucket='gspot-tiles', MaxKeys=1)
    print("R2 Connection: SUCCESS")
except Exception as e:
    print(f"R2 Connection: FAILED - {e}")
PYEOF

# ==== 9. Test Ollama Connection ====
echo ""
echo "9. Testing Ollama Connection..."
echo "-------------------------------"

if curl -s --connect-timeout 5 http://10.8.0.1:11434/api/tags > /dev/null 2>&1; then
    MODELS=$(curl -s http://10.8.0.1:11434/api/tags | jq -r '.models[].name' 2>/dev/null | head -5)
    print_status "Ollama Connection: SUCCESS"
    echo "Available models: $MODELS"
else
    print_warning "Ollama not reachable at http://10.8.0.1:11434"
fi

# ==== 10. Create Convenience Scripts ====
echo ""
echo "10. Creating Convenience Scripts..."
echo "------------------------------------"

# Create update_all.sh wrapper
cat > "$DATA_PIPELINE_DIR/update_all.sh" << 'UPDATEEOF'
#!/bin/bash
# HITD Maps - Update All
# Runs the complete pipeline to fetch, process, and upload all data

set -e
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true

echo "HITD Maps - Running Full Update Pipeline"
echo "========================================="

# Check if we should do a full scrape or just process existing
if [ "$1" == "--full" ]; then
    echo "Running full scrape + pipeline..."
    python3 agent/data_agent.py --once
    python3 agent/data_agent.py --pipeline --workers ${WORKERS:-4}
else
    echo "Running pipeline only (use --full for scraping)..."
    python3 agent/data_agent.py --pipeline --workers ${WORKERS:-4}
fi

echo ""
echo "Update complete!"
UPDATEEOF
chmod +x "$DATA_PIPELINE_DIR/update_all.sh"
print_status "Created update_all.sh"

# Create quick-status.sh
cat > "$DATA_PIPELINE_DIR/quick-status.sh" << 'STATUSEOF'
#!/bin/bash
# Quick status check for HITD Maps data pipeline

cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true

echo "HITD Maps - Pipeline Status"
echo "============================"
echo ""

# Check local files
echo "Local Files:"
echo "  GeoJSON: $(find output/geojson -name "*.geojson" 2>/dev/null | wc -l) files"
echo "  PMTiles: $(find output/pmtiles -name "*.pmtiles" 2>/dev/null | wc -l) files"

# Check R2 if credentials available
if [ -f .env ]; then
    source .env
    echo ""
    echo "R2 Status: Checking..."
    python3 -c "
import boto3
client = boto3.client('s3',
    endpoint_url='$R2_ENDPOINT',
    aws_access_key_id='$R2_ACCESS_KEY',
    aws_secret_access_key='$R2_SECRET_KEY')
response = client.list_objects_v2(Bucket='$R2_BUCKET', Prefix='parcels/', MaxKeys=1000)
count = response.get('KeyCount', 0)
print(f'  R2 Parcels: {count} files')
" 2>/dev/null || echo "  R2: Could not connect"
fi

# Check agent state
if [ -f agent/agent_state.db ]; then
    echo ""
    echo "Last Agent Activity:"
    sqlite3 agent/agent_state.db "SELECT source_id, status, last_check FROM api_checks ORDER BY last_check DESC LIMIT 5;" 2>/dev/null || true
fi
STATUSEOF
chmod +x "$DATA_PIPELINE_DIR/quick-status.sh"
print_status "Created quick-status.sh"

# ==== Done ====
echo ""
echo "=============================================="
echo "HITD Maps Setup Complete!"
echo "=============================================="
echo ""
echo "Quick Start:"
echo "  cd $DATA_PIPELINE_DIR"
echo "  source venv/bin/activate"
echo ""
echo "Check Status:"
echo "  ./quick-status.sh"
echo ""
echo "Run Full Update:"
echo "  ./update_all.sh --full"
echo ""
echo "Start Autonomous Agent (checks every 6 hours):"
echo "  python3 agent/data_agent.py --interval 360"
echo ""
echo "Or use Makefile:"
echo "  make status      # Check pipeline status"
echo "  make update      # Run pipeline"
echo "  make agent       # Start autonomous agent"
echo ""
echo "=============================================="
