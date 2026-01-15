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
