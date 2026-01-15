# Data Agent - Autonomous Monitoring System

An AI-powered agent that continuously monitors data sources, runs scrapers when updates are detected, and keeps documentation current.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA AGENT                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ API Monitor  │───▶│ Ollama LLM   │───▶│ Scraper Mgr  │       │
│  │ (6hr cycle)  │    │ (analysis)   │    │ (execution)  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ SQLite State │    │ Doc Updater  │    │ R2 Upload    │       │
│  │ (persistent) │    │ (auto-docs)  │    │ (background) │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │         Ollama Server          │
              │     (http://10.8.0.1:11434)    │
              │     - llama3.3:70b (chat)      │
              │     - deepseek-r1:671b (deep)  │
              └───────────────────────────────┘
```

## Quick Start

### Test Run (Single Cycle)
```bash
cd /home/exx/Documents/C/hitd_maps/data-pipeline
python3 agent/data_agent.py --once
```

### Check Specific API
```bash
python3 agent/data_agent.py --check-api tx_statewide
python3 agent/data_agent.py --check-api fl_statewide
```

### Install as Service
```bash
sudo bash agent/install.sh
sudo systemctl start data-agent
```

### View Logs
```bash
tail -f agent/agent.log
```

## What It Does

### 1. API Monitoring (Every 6 Hours)
- Checks record counts on 5 key APIs (TX, FL, NY, CA-LA, OH)
- Compares to previous counts in SQLite database
- Uses Llama 3.3 70B to analyze if changes warrant re-scraping

### 2. Intelligent Scraping Decisions
The LLM analyzes changes and returns:
```json
{
  "should_scrape": true,
  "priority": "high",
  "reason": "TX statewide API gained 50,000 records (0.18% increase)"
}
```

### 3. Automatic Documentation Updates
Updates `docs/DATA_FRESHNESS.md` with:
- API health status (✅/❌)
- Current record counts
- Last check timestamps

### 4. Persistent State
SQLite database (`agent_state.db`) tracks:
- Last API check times
- Record count history
- Scrape job history

## Configuration

### Environment Variables
```bash
OLLAMA_BASE=http://10.8.0.1:11434  # Your Ollama server
OLLAMA_MODEL=llama3.3:70b          # Model for analysis
```

### Adding New APIs to Monitor
Edit `data_agent.py` and add to `MONITORED_APIS`:
```python
"new_api_id": {
    "url": "https://arcgis-server/rest/services/...",
    "state": "XX",
    "county": "optional",
    "expected_records": 1000000
}
```

## Files

```
agent/
├── data_agent.py          # Main agent script
├── data-agent.service     # Systemd service file
├── install.sh             # Installation script
├── agent_state.db         # SQLite state (created on first run)
├── agent.log              # Main log file
├── agent_error.log        # Error log
└── README.md              # This file
```

## Integration with Continue VSCode

The updated `~/.continue/config.yaml` includes:
- `/scrape` - Run a single monitoring cycle
- `/api-health` - Check API status

Use in Continue chat: "Run /scrape to check for updates"

## Extending the Agent

### Add Custom Scraper Logic
Override the `ScraperManager.run_scraper()` method to add:
- Rate limiting
- Retry logic
- Notification webhooks

### Add More LLM Analysis
The `OllamaClient` can be used for:
- Summarizing scrape results
- Generating changelog entries
- Analyzing data quality issues

### Webhook Notifications
Add to the monitoring cycle:
```python
async def send_webhook(self, event: str, data: dict):
    async with aiohttp.ClientSession() as session:
        await session.post("https://your-webhook-url", json={
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
```
