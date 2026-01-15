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
import os
client = boto3.client('s3',
    endpoint_url=os.environ.get('R2_ENDPOINT', 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com'),
    aws_access_key_id=os.environ.get('R2_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('R2_SECRET_KEY'))
response = client.list_objects_v2(Bucket=os.environ.get('R2_BUCKET', 'gspot-tiles'), Prefix='parcels/', MaxKeys=1000)
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

# Check systemd service status
echo ""
echo "Service Status:"
systemctl is-active hitd-data-agent 2>/dev/null || echo "  hitd-data-agent: not installed"
