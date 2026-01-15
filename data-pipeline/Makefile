# HITD Maps Data Pipeline - Makefile
# ==================================
# Common operations for the data pipeline.
#
# Usage: make <target>
#

.PHONY: help setup status update agent scrape pipeline cleanup docs test

# Default target
help:
	@echo "HITD Maps Data Pipeline"
	@echo "======================="
	@echo ""
	@echo "Setup:"
	@echo "  make setup        Install all dependencies"
	@echo "  make setup-dev    Development setup (lighter)"
	@echo ""
	@echo "Operations:"
	@echo "  make status       Show pipeline status"
	@echo "  make update       Run full update (scrape + pipeline)"
	@echo "  make pipeline     Process and upload existing files"
	@echo "  make cleanup      Remove uploaded local files"
	@echo "  make docs         Update documentation"
	@echo ""
	@echo "Agent:"
	@echo "  make agent        Start autonomous agent (6hr interval)"
	@echo "  make agent-once   Run one monitoring cycle"
	@echo ""
	@echo "Scraping:"
	@echo "  make scrape STATE=TX          Scrape Texas"
	@echo "  make scrape STATE=CA COUNTY=LA  Scrape LA County, CA"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make check-api    Check all monitored APIs"
	@echo ""

# Setup
setup:
	@./scripts/setup_environment.sh --server

setup-dev:
	@./scripts/setup_environment.sh --dev

# Status
status:
	@./quick-status.sh 2>/dev/null || (source venv/bin/activate && python3 agent/data_agent.py --check-api tx_statewide)

# Full update (scrape + process + upload)
update:
	@source venv/bin/activate && python3 agent/data_agent.py --once && python3 agent/data_agent.py --pipeline --workers 4

# Pipeline only (process existing files)
pipeline:
	@source venv/bin/activate && python3 agent/data_agent.py --pipeline --workers $${WORKERS:-4}

# Cleanup uploaded files
cleanup:
	@source venv/bin/activate && python3 agent/data_agent.py --cleanup

# Update documentation
docs:
	@source venv/bin/activate && python3 agent/data_agent.py --update-docs

# Start autonomous agent
agent:
	@source venv/bin/activate && python3 agent/data_agent.py --interval $${INTERVAL:-360}

agent-once:
	@source venv/bin/activate && python3 agent/data_agent.py --once

# Scraping (requires STATE variable)
scrape:
ifndef STATE
	$(error STATE is required. Usage: make scrape STATE=TX)
endif
ifdef COUNTY
	@source venv/bin/activate && python3 agent/data_agent.py --scrape $(STATE) --county $(COUNTY)
else
	@source venv/bin/activate && python3 agent/data_agent.py --scrape $(STATE)
endif

# Check all APIs
check-api:
	@source venv/bin/activate && python3 -c "\
import asyncio; \
from agent.data_agent import DataAgent; \
async def run(): \
    agent = DataAgent(); \
    results = await agent.api_monitor.check_all_apis(); \
    for r in results: print(f\"{r['source_id']}: {r.get('status', 'error')} ({r.get('record_count', 0):,} records)\"); \
asyncio.run(run())"

# Run tests
test:
	@source venv/bin/activate && python3 -m pytest tests/ -v 2>/dev/null || echo "No tests found"

# Enrichment pipeline
enrichment:
ifndef STATE
	$(error STATE is required. Usage: make enrichment STATE=TX)
endif
	@source venv/bin/activate && python3 scripts/enrichment/run_enrichment_pipeline.py --state $(STATE)

# Install as systemd service
install-service:
	@sudo cp config/hitd-data-agent.service /etc/systemd/system/
	@sudo systemctl daemon-reload
	@sudo systemctl enable hitd-data-agent
	@echo "Service installed. Start with: sudo systemctl start hitd-data-agent"

# View agent logs
logs:
	@tail -f agent/agent.log 2>/dev/null || echo "No log file found"

# R2 inventory
r2-inventory:
	@source venv/bin/activate && python3 -c "\
import boto3; \
import os; \
client = boto3.client('s3', \
    endpoint_url=os.environ.get('R2_ENDPOINT', 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com'), \
    aws_access_key_id=os.environ.get('R2_ACCESS_KEY', 'ecd653afe3300fdc045b9980df0dbb14'), \
    aws_secret_access_key=os.environ.get('R2_SECRET_KEY', 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35')); \
resp = client.list_objects_v2(Bucket='gspot-tiles', MaxKeys=100); \
print(f\"R2 Bucket: {resp.get('KeyCount', 0)} objects (first 100)\"); \
for obj in resp.get('Contents', [])[:20]: print(f\"  {obj['Key']}: {obj['Size']/1024/1024:.1f} MB\")"
