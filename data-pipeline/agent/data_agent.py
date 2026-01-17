#!/usr/bin/env python3
"""
Autonomous Data Agent for HITD Maps
====================================
Continuously monitors data sources, runs scrapers, and updates documentation.
Uses local Ollama models for intelligent decision-making.

Part of the HITD Maps package by Houston IT Developers LLC.

Run as: python3 data_agent.py
Or install as systemd service: sudo systemctl start hitd-data-agent

Commands:
  python3 data_agent.py --once           # Single monitoring cycle
  python3 data_agent.py --pipeline       # Run full pipeline only
  python3 data_agent.py --cleanup        # Cleanup uploaded files
  python3 data_agent.py --scrape TX      # Scrape specific state
  python3 data_agent.py --interval 360   # Run continuously (6hr interval)
  python3 data_agent.py --update-docs    # Update documentation only
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import hashlib
import sqlite3

import aiohttp
import requests

# Import issue tracker
try:
    from issue_tracker import IssueTracker, analyze_error
    from auto_fixer import AutoFixer
    ISSUE_TRACKING_ENABLED = True
except ImportError:
    ISSUE_TRACKING_ENABLED = False
    IssueTracker = None
    AutoFixer = None

# Configuration
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://10.8.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.3:70b")
DATA_PIPELINE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"
DOCS_DIR = DATA_PIPELINE_DIR / "docs"
SCRIPTS_DIR = DATA_PIPELINE_DIR / "scripts"
AGENT_DIR = DATA_PIPELINE_DIR / "agent"
DB_PATH = AGENT_DIR / "agent_state.db"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(AGENT_DIR / "agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataAgent")


class AgentState:
    """Persistent state storage for the agent using SQLite."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_checks (
                    source_id TEXT PRIMARY KEY,
                    last_check TIMESTAMP,
                    last_record_count INTEGER,
                    last_edit_date TEXT,
                    status TEXT,
                    error_message TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scrape_jobs (
                    job_id TEXT PRIMARY KEY,
                    state TEXT,
                    county TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    records_scraped INTEGER,
                    status TEXT,
                    error_message TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS doc_updates (
                    doc_path TEXT PRIMARY KEY,
                    last_updated TIMESTAMP,
                    content_hash TEXT
                )
            """)
            conn.commit()

    def get_last_check(self, source_id: str) -> Optional[datetime]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT last_check FROM api_checks WHERE source_id = ?",
                (source_id,)
            ).fetchone()
            return datetime.fromisoformat(row[0]) if row else None

    def update_api_check(self, source_id: str, record_count: int,
                         edit_date: str, status: str, error: str = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO api_checks
                (source_id, last_check, last_record_count, last_edit_date, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (source_id, datetime.now().isoformat(), record_count, edit_date, status, error))
            conn.commit()

    def record_scrape_job(self, job_id: str, state: str, county: str,
                          status: str, records: int = 0, error: str = None):
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            if status == "started":
                conn.execute("""
                    INSERT OR REPLACE INTO scrape_jobs
                    (job_id, state, county, started_at, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (job_id, state, county, now, status))
            else:
                conn.execute("""
                    UPDATE scrape_jobs
                    SET completed_at = ?, records_scraped = ?, status = ?, error_message = ?
                    WHERE job_id = ?
                """, (now, records, status, error, job_id))
            conn.commit()


class OllamaClient:
    """Client for interacting with local Ollama instance."""

    def __init__(self, base_url: str = OLLAMA_BASE, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model

    async def generate(self, prompt: str, system: str = None) -> str:
        """Generate a response from Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("response", "")
                    else:
                        logger.error(f"Ollama error: {resp.status}")
                        return ""
        except Exception as e:
            logger.error(f"Ollama connection error: {e}")
            return ""

    async def analyze_api_changes(self, old_count: int, new_count: int,
                                   source_name: str) -> dict:
        """Use LLM to analyze API changes and recommend action."""
        prompt = f"""Analyze this data source change:
Source: {source_name}
Previous record count: {old_count}
Current record count: {new_count}
Change: {new_count - old_count} records ({((new_count - old_count) / max(old_count, 1)) * 100:.1f}%)

Should we trigger a re-scrape? Consider:
- If records increased significantly (>1%), likely new data
- If records decreased, possible data cleanup or API issue
- Small changes (<0.1%) might be noise

Respond in JSON format:
{{"should_scrape": true/false, "priority": "high/medium/low", "reason": "brief explanation"}}"""

        response = await self.generate(prompt, system="You are a data engineering assistant. Respond only with valid JSON.")
        try:
            return json.loads(response)
        except:
            return {"should_scrape": False, "priority": "low", "reason": "Could not parse LLM response"}


class APIMonitor:
    """Monitor ArcGIS APIs for data updates.

    Loads ALL APIs dynamically from:
    - COUNTY_CONFIGS in export_county_parcels.py (516+ parcel APIs)
    - enrichment_sources.json (11 enrichment layers)
    """

    def __init__(self, state: AgentState, ollama: OllamaClient):
        self.state = state
        self.ollama = ollama
        self.MONITORED_APIS = self._load_all_apis()
        logger.info(f"Loaded {len(self.MONITORED_APIS)} APIs to monitor")

    def _load_all_apis(self) -> dict:
        """Load all APIs from COUNTY_CONFIGS and enrichment sources."""
        apis = {}

        # 1. Load parcel APIs from export_county_parcels.py
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "export_county_parcels",
                SCRIPTS_DIR / "export_county_parcels.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for config_id, config in module.COUNTY_CONFIGS.items():
                # Convert service_url to base URL (remove /query suffix if present)
                service_url = config.get("service_url", "")
                if service_url.endswith("/query"):
                    base_url = service_url[:-6]  # Remove /query
                else:
                    base_url = service_url

                # Parse state and county from config_id (e.g., "TX_HARRIS" -> TX, Harris)
                parts = config_id.split("_", 1)
                state_code = parts[0]
                county_or_type = parts[1].lower() if len(parts) > 1 else None

                apis[config_id.lower()] = {
                    "url": base_url,
                    "state": state_code,
                    "county": county_or_type if county_or_type and county_or_type not in ["statewide", "statewide_v2", "statewide_recent"] else None,
                    "name": config.get("name", config_id),
                    "type": "parcel",
                    "expected_records": config.get("expected_records", 0)
                }
            logger.info(f"Loaded {len(apis)} parcel APIs from COUNTY_CONFIGS")
        except Exception as e:
            logger.error(f"Failed to load COUNTY_CONFIGS: {e}")

        # 2. Load enrichment layer APIs
        try:
            enrichment_path = DATA_PIPELINE_DIR / "config" / "enrichment_sources.json"
            if enrichment_path.exists():
                with open(enrichment_path) as f:
                    enrichment_data = json.load(f)

                for source_id, source in enrichment_data.get("sources", {}).items():
                    api_url = source.get("api_url")
                    if api_url:
                        apis[f"enrichment_{source_id}"] = {
                            "url": api_url,
                            "name": source.get("name", source_id),
                            "type": "enrichment",
                            "priority": source.get("priority", 10),
                            "update_frequency": source.get("update_frequency", "annual"),
                            "expected_records": 0  # Enrichment layers don't have simple counts
                        }
                logger.info(f"Loaded enrichment APIs: {[k for k in apis if k.startswith('enrichment_')]}")
        except Exception as e:
            logger.error(f"Failed to load enrichment sources: {e}")

        return apis

    async def check_api(self, source_id: str, config: dict) -> dict:
        """Check an API for record count and last edit date."""
        url = config["url"]
        query_url = f"{url}/query?where=1=1&returnCountOnly=true&f=json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(query_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        count = data.get("count", 0)

                        # Get metadata for last edit date
                        meta_url = f"{url}?f=json"
                        async with session.get(meta_url) as meta_resp:
                            if meta_resp.status == 200:
                                meta = await meta_resp.json()
                                edit_date = meta.get("editingInfo", {}).get("lastEditDate", "unknown")
                            else:
                                edit_date = "unknown"

                        return {
                            "source_id": source_id,
                            "status": "healthy",
                            "record_count": count,
                            "last_edit_date": str(edit_date),
                            "expected": config.get("expected_records", 0)
                        }
                    else:
                        return {
                            "source_id": source_id,
                            "status": "error",
                            "error": f"HTTP {resp.status}"
                        }
        except Exception as e:
            return {
                "source_id": source_id,
                "status": "error",
                "error": str(e)
            }

    async def check_all_apis(self, batch_size: int = 50, delay_between_batches: float = 2.0) -> list:
        """Check all monitored APIs with batching to avoid overwhelming servers.

        Args:
            batch_size: Number of APIs to check concurrently per batch
            delay_between_batches: Seconds to wait between batches
        """
        all_results = []
        api_items = list(self.MONITORED_APIS.items())
        total_batches = (len(api_items) + batch_size - 1) // batch_size

        logger.info(f"Checking {len(api_items)} APIs in {total_batches} batches of {batch_size}")

        for i in range(0, len(api_items), batch_size):
            batch = api_items[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            logger.info(f"Checking batch {batch_num}/{total_batches} ({len(batch)} APIs)")

            tasks = [
                self.check_api(source_id, config)
                for source_id, config in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results, handling any exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    all_results.append({
                        "source_id": "unknown",
                        "status": "error",
                        "error": str(result)
                    })
                else:
                    all_results.append(result)

            # Rate limit between batches (except for last batch)
            if i + batch_size < len(api_items):
                await asyncio.sleep(delay_between_batches)

        # Log summary
        healthy = sum(1 for r in all_results if r.get("status") == "healthy")
        errors = sum(1 for r in all_results if r.get("status") == "error")
        logger.info(f"API check complete: {healthy} healthy, {errors} errors")

        return all_results

    async def check_priority_apis(self, max_apis: int = 100) -> list:
        """Check only priority APIs (statewide + high-value counties).

        Use this for quick status checks instead of checking all 500+ APIs.
        """
        priority_apis = {}

        for source_id, config in self.MONITORED_APIS.items():
            # Include all statewide APIs
            if "statewide" in source_id:
                priority_apis[source_id] = config
            # Include all enrichment APIs
            elif config.get("type") == "enrichment":
                priority_apis[source_id] = config
            # Stop when we have enough
            if len(priority_apis) >= max_apis:
                break

        logger.info(f"Checking {len(priority_apis)} priority APIs")

        tasks = [
            self.check_api(source_id, config)
            for source_id, config in priority_apis.items()
        ]
        return await asyncio.gather(*tasks)


class ScraperManager:
    """Manage scraping jobs with full pipeline: scrape → reproject → tile → upload → cleanup."""

    def __init__(self, state: AgentState):
        self.state = state
        self.active_jobs = {}

    async def run_scraper(self, state: str, county: str = None) -> dict:
        """Run the export_county_parcels.py scraper."""
        job_id = f"{state}_{county or 'statewide'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.state.record_scrape_job(job_id, state, county or "statewide", "started")
        logger.info(f"Starting scrape job: {job_id}")

        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "export_county_parcels.py"),
            "--state", state
        ]
        if county:
            cmd.extend(["--county", county])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(DATA_PIPELINE_DIR)
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Count output records
                output_pattern = OUTPUT_DIR / "geojson" / state.lower()
                records = 0  # Would parse from output
                self.state.record_scrape_job(job_id, state, county or "statewide",
                                             "completed", records)
                logger.info(f"Scrape job completed: {job_id}")
                return {"status": "success", "job_id": job_id}
            else:
                error = stderr.decode()[:500]
                self.state.record_scrape_job(job_id, state, county or "statewide",
                                             "failed", error=error)
                logger.error(f"Scrape job failed: {job_id} - {error}")
                return {"status": "failed", "job_id": job_id, "error": error}
        except Exception as e:
            self.state.record_scrape_job(job_id, state, county or "statewide",
                                         "failed", error=str(e))
            return {"status": "failed", "job_id": job_id, "error": str(e)}

    async def run_full_pipeline(self, workers: int = 4) -> dict:
        """Run the full pipeline: reproject → tile → upload → cleanup.

        This processes all pending GeoJSON files through:
        1. Coordinate reprojection (EPSG:3857 → EPSG:4326)
        2. PMTiles generation (tippecanoe)
        3. R2 upload
        4. Local file cleanup after successful upload
        """
        logger.info(f"Starting full pipeline with {workers} workers")

        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "parallel_process_upload.py"),
            str(workers)
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(DATA_PIPELINE_DIR)
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info("Full pipeline completed successfully")
                return {"status": "success", "output": stdout.decode()[-1000:]}
            else:
                error = stderr.decode()[:500]
                logger.error(f"Full pipeline failed: {error}")
                return {"status": "failed", "error": error}
        except Exception as e:
            logger.error(f"Full pipeline error: {e}")
            return {"status": "failed", "error": str(e)}

    async def cleanup_processed_files(self) -> dict:
        """Clean up local files that have been successfully uploaded to R2."""
        import boto3
        from botocore.config import Config

        R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
        R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
        R2_BUCKET = "gspot-tiles"
        R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

        logger.info("Cleaning up local files already in R2...")

        try:
            client = boto3.client(
                's3',
                endpoint_url=R2_ENDPOINT,
                aws_access_key_id=R2_ACCESS_KEY,
                aws_secret_access_key=R2_SECRET_KEY,
            )

            # Get list of files in R2
            r2_files = set()
            paginator = client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=R2_BUCKET, Prefix='parcels/'):
                for obj in page.get('Contents', []):
                    # Extract filename from key (parcels/filename.pmtiles)
                    filename = obj['Key'].split('/')[-1].replace('.pmtiles', '')
                    r2_files.add(filename)

            # Find local files that are already in R2
            cleaned = 0
            geojson_dir = OUTPUT_DIR / "geojson" / "counties"
            pmtiles_dir = OUTPUT_DIR / "pmtiles"

            for local_dir in [geojson_dir, pmtiles_dir]:
                if not local_dir.exists():
                    continue
                for f in local_dir.iterdir():
                    if f.stem in r2_files or f.stem.replace('_wgs84', '') in r2_files:
                        f.unlink()
                        logger.info(f"Deleted: {f}")
                        cleaned += 1

            return {"status": "success", "cleaned": cleaned}

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return {"status": "failed", "error": str(e)}


class DocumentationUpdater:
    """Automatically update documentation based on scraping activity."""

    def __init__(self, state: AgentState, ollama: OllamaClient):
        self.state = state
        self.ollama = ollama

    async def update_progress_doc(self, api_results: list):
        """Update the DATA_FRESHNESS.md with latest API check results."""
        doc_path = DOCS_DIR / "DATA_FRESHNESS.md"

        # Build status table
        rows = []
        for result in api_results:
            if result.get("status") == "healthy":
                status_emoji = "✅"
                count = f"{result['record_count']:,}"
            else:
                status_emoji = "❌"
                count = "Error"
            rows.append(f"| {result['source_id']} | {status_emoji} | {count} | {datetime.now().strftime('%Y-%m-%d %H:%M')} |")

        table = "\n".join(rows)

        # Read existing doc and update the automated section
        if doc_path.exists():
            content = doc_path.read_text()

            # Find or create automated section
            marker_start = "<!-- AGENT_STATUS_START -->"
            marker_end = "<!-- AGENT_STATUS_END -->"

            new_section = f"""{marker_start}
## Automated API Health Check

Last updated by Data Agent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

| Source | Status | Records | Last Check |
|--------|--------|---------|------------|
{table}

{marker_end}"""

            if marker_start in content:
                # Replace existing section
                import re
                content = re.sub(
                    f"{marker_start}.*?{marker_end}",
                    new_section,
                    content,
                    flags=re.DOTALL
                )
            else:
                # Append new section
                content += f"\n\n{new_section}"

            doc_path.write_text(content)
            logger.info(f"Updated {doc_path}")

    async def generate_scraping_summary(self, completed_jobs: list) -> str:
        """Use LLM to generate a summary of scraping activity."""
        if not completed_jobs:
            return ""

        jobs_text = "\n".join([
            f"- {j['state']}/{j.get('county', 'statewide')}: {j['status']}"
            for j in completed_jobs
        ])

        prompt = f"""Summarize today's data scraping activity:

{jobs_text}

Write a brief 2-3 sentence summary for the changelog."""

        return await self.ollama.generate(prompt)


class DataAgent:
    """Main agent orchestrator."""

    def __init__(self):
        self.state = AgentState()
        self.ollama = OllamaClient()
        self.api_monitor = APIMonitor(self.state, self.ollama)
        self.scraper = ScraperManager(self.state)
        self.docs = DocumentationUpdater(self.state, self.ollama)

        # Issue tracking
        if ISSUE_TRACKING_ENABLED:
            self.issue_tracker = IssueTracker()
            self.auto_fixer = AutoFixer(self.issue_tracker)
            logger.info("Issue tracking enabled")
        else:
            self.issue_tracker = None
            self.auto_fixer = None
            logger.warning("Issue tracking not available")

        # Check intervals
        self.api_check_interval = timedelta(hours=6)
        self.scrape_check_interval = timedelta(hours=12)

    async def run_monitoring_cycle(self, check_all: bool = False):
        """Run one monitoring cycle.

        Args:
            check_all: If True, check all 500+ APIs. If False, check only priority APIs.
        """
        logger.info("Starting monitoring cycle")

        # 1. Check APIs (all or just priority)
        if check_all:
            logger.info("Checking ALL APIs (this may take several minutes)...")
            api_results = await self.api_monitor.check_all_apis()
        else:
            logger.info("Checking priority APIs (statewide + enrichment)...")
            api_results = await self.api_monitor.check_priority_apis()
        logger.info(f"Checked {len(api_results)} APIs")

        # 2. Log any API errors as issues
        error_count = 0
        for result in api_results:
            if result.get("status") == "error" and self.issue_tracker:
                error_count += 1
                config = self.api_monitor.MONITORED_APIS.get(result.get("source_id", ""), {})
                analysis = analyze_error(result.get("error", "")) if ISSUE_TRACKING_ENABLED else {}

                self.issue_tracker.log_issue(
                    title=f"API check failed: {result.get('source_id', 'unknown')}",
                    issue_type="api_error",
                    severity="warning",
                    source_id=result.get("source_id"),
                    state=config.get("state"),
                    county=config.get("county"),
                    error_message=result.get("error"),
                    context={"url": config.get("url"), "result": result},
                    suggested_fix=analysis.get("suggested_fix"),
                    auto_fixable=analysis.get("auto_fixable", False)
                )

        if error_count > 0:
            logger.warning(f"Logged {error_count} API errors to issue tracker")

        # 3. Analyze changes and decide on scraping
        scrape_queue = []
        for result in api_results:
            if result.get("status") != "healthy":
                continue

            source_id = result["source_id"]
            config = self.api_monitor.MONITORED_APIS.get(source_id, {})

            # Get previous count from state
            with sqlite3.connect(DB_PATH) as conn:
                row = conn.execute(
                    "SELECT last_record_count FROM api_checks WHERE source_id = ?",
                    (source_id,)
                ).fetchone()
                old_count = row[0] if row else 0

            new_count = result["record_count"]

            # Update state
            self.state.update_api_check(
                source_id, new_count,
                result.get("last_edit_date", "unknown"),
                "healthy"
            )

            # Use LLM to analyze if we should scrape
            if old_count > 0 and abs(new_count - old_count) > old_count * 0.001:
                analysis = await self.ollama.analyze_api_changes(
                    old_count, new_count, source_id
                )
                if analysis.get("should_scrape"):
                    scrape_queue.append({
                        "source_id": source_id,
                        "state": config.get("state"),
                        "county": config.get("county"),
                        "priority": analysis.get("priority", "medium"),
                        "reason": analysis.get("reason", "Data changed")
                    })
                    logger.info(f"Queuing scrape for {source_id}: {analysis.get('reason')}")

        # 3. Update documentation
        await self.docs.update_progress_doc(api_results)

        # 4. Return scrape queue for processing
        return {
            "api_results": api_results,
            "scrape_queue": scrape_queue
        }

    async def process_scrape_queue(self, queue: list, max_concurrent: int = 5):
        """Process queued scrape jobs."""
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        queue.sort(key=lambda x: priority_order.get(x.get("priority"), 2))

        results = []
        for job in queue[:max_concurrent]:  # Limit concurrent
            result = await self.scraper.run_scraper(
                job["state"],
                job.get("county")
            )
            results.append({**job, **result})

        return results

    async def run_forever(self, check_interval_minutes: int = 360, full_check_every: int = 4):
        """Run the agent continuously with full pipeline.

        Each cycle:
        1. Check APIs for data changes (priority by default, full every N cycles)
        2. Queue and run scrapes for changed data
        3. Run full pipeline (reproject → tile → upload → cleanup)
        4. Clean up any orphaned local files
        5. Update documentation

        Args:
            check_interval_minutes: Minutes between cycles (default 360 = 6 hours)
            full_check_every: Run full API check every N cycles (default 4 = once daily)
        """
        logger.info("Data Agent starting continuous operation")
        logger.info(f"Interval: {check_interval_minutes} minutes")
        logger.info(f"Full API check: every {full_check_every} cycles ({full_check_every * check_interval_minutes / 60:.0f} hours)")
        logger.info(f"Total APIs monitored: {len(self.api_monitor.MONITORED_APIS)}")

        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                check_all = (cycle_count % full_check_every == 0)

                if check_all:
                    logger.info(f"Cycle {cycle_count}: FULL API CHECK (all {len(self.api_monitor.MONITORED_APIS)} APIs)")
                else:
                    logger.info(f"Cycle {cycle_count}: Priority API check")

                # Run monitoring cycle
                cycle_result = await self.run_monitoring_cycle(check_all=check_all)

                # Process any queued scrapes
                if cycle_result["scrape_queue"]:
                    scrape_results = await self.process_scrape_queue(
                        cycle_result["scrape_queue"]
                    )
                    logger.info(f"Processed {len(scrape_results)} scrape jobs")

                    # Run full pipeline after scraping
                    logger.info("Running full pipeline (reproject → tile → upload → cleanup)")
                    pipeline_result = await self.scraper.run_full_pipeline(workers=4)
                    logger.info(f"Pipeline result: {pipeline_result.get('status')}")

                # Always cleanup orphaned local files
                cleanup_result = await self.scraper.cleanup_processed_files()
                if cleanup_result.get("cleaned", 0) > 0:
                    logger.info(f"Cleaned {cleanup_result['cleaned']} orphaned files")

                # Run auto-fixes for any logged issues
                if self.auto_fixer:
                    logger.info("Running auto-fixes for logged issues...")
                    fix_results = await self.auto_fixer.fix_all_auto_fixable()
                    if fix_results["attempted"] > 0:
                        logger.info(f"Auto-fix: {fix_results['fixed']}/{fix_results['attempted']} issues fixed")

                logger.info(f"Cycle complete. Sleeping {check_interval_minutes} minutes")
                await asyncio.sleep(check_interval_minutes * 60)

            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                # Log the error as an issue
                if self.issue_tracker:
                    self.issue_tracker.log_issue(
                        title=f"Monitoring cycle error",
                        issue_type="unknown",
                        severity="error",
                        error_message=str(e),
                        exception=e,
                        auto_fixable=False
                    )
                await asyncio.sleep(60)  # Short sleep on error


async def update_all_docs(agent: "DataAgent"):
    """Update all documentation with current state."""
    print("Updating documentation...")

    # Run API checks first
    api_results = await agent.api_monitor.check_all_apis()

    # Update DATA_FRESHNESS.md
    await agent.docs.update_progress_doc(api_results)

    # Update R2 inventory
    await update_r2_inventory()

    print("Documentation updated.")
    return {"status": "success", "apis_checked": len(api_results)}


async def update_r2_inventory():
    """Update the R2 inventory documentation."""
    try:
        import boto3
        from datetime import datetime

        R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY", "ecd653afe3300fdc045b9980df0dbb14")
        R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY", "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35")
        R2_BUCKET = os.environ.get("R2_BUCKET", "gspot-tiles")
        R2_ENDPOINT = os.environ.get("R2_ENDPOINT", "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com")

        client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )

        # Get all objects
        inventory = {"parcels": [], "enrichment": [], "basemap": [], "other": []}
        total_size = 0

        paginator = client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=R2_BUCKET):
            for obj in page.get('Contents', []):
                key = obj['Key']
                size = obj['Size']
                total_size += size

                entry = {
                    "key": key,
                    "size_mb": round(size / 1024 / 1024, 2),
                    "modified": obj['LastModified'].isoformat()
                }

                if key.startswith('parcels/'):
                    inventory["parcels"].append(entry)
                elif key.startswith('enrichment/'):
                    inventory["enrichment"].append(entry)
                elif key.startswith('basemap'):
                    inventory["basemap"].append(entry)
                else:
                    inventory["other"].append(entry)

        # Write inventory doc
        doc_path = DOCS_DIR / "R2_INVENTORY.md"
        content = f"""# R2 Bucket Inventory

Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Category | Files | Size |
|----------|-------|------|
| Parcels | {len(inventory['parcels'])} | {sum(p['size_mb'] for p in inventory['parcels']):.1f} MB |
| Enrichment | {len(inventory['enrichment'])} | {sum(p['size_mb'] for p in inventory['enrichment']):.1f} MB |
| Basemap | {len(inventory['basemap'])} | {sum(p['size_mb'] for p in inventory['basemap']):.1f} MB |
| Other | {len(inventory['other'])} | {sum(p['size_mb'] for p in inventory['other']):.1f} MB |
| **Total** | **{sum(len(v) for v in inventory.values())}** | **{total_size / 1024 / 1024:.1f} MB** |

## Parcel Files

| File | Size (MB) | Last Modified |
|------|-----------|---------------|
"""
        for p in sorted(inventory['parcels'], key=lambda x: x['key']):
            content += f"| {p['key']} | {p['size_mb']} | {p['modified'][:10]} |\n"

        content += """
## Enrichment Layers

| File | Size (MB) | Last Modified |
|------|-----------|---------------|
"""
        for p in sorted(inventory['enrichment'], key=lambda x: x['key']):
            content += f"| {p['key']} | {p['size_mb']} | {p['modified'][:10]} |\n"

        doc_path.write_text(content)
        logger.info(f"Updated R2 inventory: {sum(len(v) for v in inventory.values())} files")

    except Exception as e:
        logger.error(f"Failed to update R2 inventory: {e}")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="HITD Maps Data Agent - Autonomous Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --once                    # Run one monitoring cycle
  %(prog)s --pipeline                # Process and upload files
  %(prog)s --scrape TX               # Scrape Texas data
  %(prog)s --scrape CA --county LA   # Scrape LA County, CA
  %(prog)s --update-docs             # Update documentation only
  %(prog)s --interval 360            # Run continuously (6hr)
        """
    )
    parser.add_argument("--once", action="store_true",
                        help="Run one monitoring cycle and exit")
    parser.add_argument("--check-all", action="store_true",
                        help="Check ALL APIs (500+) instead of just priority APIs")
    parser.add_argument("--list-apis", action="store_true",
                        help="List all monitored APIs and exit")
    parser.add_argument("--interval", type=int, default=360,
                        help="Check interval in minutes (default: 360)")
    parser.add_argument("--full-check-every", type=int, default=4,
                        help="Run full API check every N cycles (default: 4)")
    parser.add_argument("--check-api", type=str,
                        help="Check a specific API")
    parser.add_argument("--pipeline", action="store_true",
                        help="Run full pipeline only (reproject → tile → upload → cleanup)")
    parser.add_argument("--cleanup", action="store_true",
                        help="Cleanup local files already in R2")
    parser.add_argument("--workers", type=int, default=4,
                        help="Number of parallel workers (default: 4)")
    parser.add_argument("--scrape", type=str, metavar="STATE",
                        help="Scrape a specific state (e.g., TX)")
    parser.add_argument("--county", type=str,
                        help="Scrape a specific county (use with --scrape)")
    parser.add_argument("--update-docs", action="store_true",
                        help="Update documentation files only")
    parser.add_argument("--issues", action="store_true",
                        help="Show open issues summary")
    parser.add_argument("--issues-export", action="store_true",
                        help="Export issues for Claude to analyze")
    parser.add_argument("--auto-fix", action="store_true",
                        help="Run auto-fixes for logged issues")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose logging output")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    agent = DataAgent()

    if args.list_apis:
        # List all monitored APIs
        print(f"\nTotal APIs monitored: {len(agent.api_monitor.MONITORED_APIS)}")
        print("\n=== PARCEL APIs ===")
        parcel_apis = [(k, v) for k, v in agent.api_monitor.MONITORED_APIS.items() if v.get("type") == "parcel"]
        statewide = [k for k, v in parcel_apis if "statewide" in k]
        county = [k for k, v in parcel_apis if "statewide" not in k]

        print(f"\nStatewide APIs ({len(statewide)}):")
        for api_id in sorted(statewide):
            config = agent.api_monitor.MONITORED_APIS[api_id]
            print(f"  {api_id}: {config.get('name', api_id)}")

        print(f"\nCounty APIs ({len(county)}):")
        # Group by state
        by_state = {}
        for api_id in county:
            config = agent.api_monitor.MONITORED_APIS[api_id]
            state = config.get("state", "??")
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(api_id)

        for state in sorted(by_state.keys()):
            print(f"  {state}: {len(by_state[state])} counties")

        print("\n=== ENRICHMENT APIs ===")
        enrichment_apis = [(k, v) for k, v in agent.api_monitor.MONITORED_APIS.items() if v.get("type") == "enrichment"]
        for api_id, config in sorted(enrichment_apis):
            print(f"  {api_id}: {config.get('name', api_id)}")

        return

    if args.issues:
        # Show issues summary
        if agent.issue_tracker:
            summary = agent.issue_tracker.get_issues_summary()
            print("\n=== HITD Maps Pipeline Issues ===")
            print(f"Total: {summary['total']} | Open: {summary['open']} | Resolved: {summary['resolved']}")
            if summary['by_severity']:
                print("\nBy Severity:")
                for sev, count in sorted(summary['by_severity'].items()):
                    print(f"  {sev}: {count}")
            if summary['by_type']:
                print("\nBy Type:")
                for typ, count in sorted(summary['by_type'].items()):
                    print(f"  {typ}: {count}")
            if summary['by_state']:
                print("\nBy State:")
                for state, count in sorted(summary['by_state'].items()):
                    print(f"  {state}: {count}")
        else:
            print("Issue tracking not available")
        return

    elif args.issues_export:
        # Export issues for Claude
        if agent.issue_tracker:
            report = agent.issue_tracker.export_for_claude()
            print(report)
        else:
            print("Issue tracking not available")
        return

    elif args.auto_fix:
        # Run auto-fixes
        if agent.auto_fixer:
            results = await agent.auto_fixer.fix_all_auto_fixable()
            print(f"\n=== Auto-Fix Results ===")
            print(f"Attempted: {results['attempted']}")
            print(f"Fixed: {results['fixed']}")
            print(f"Failed: {results['failed']}")
            for detail in results['details']:
                print(f"  Issue #{detail['id']}: {detail['status']}")
        else:
            print("Auto-fixer not available")
        return

    elif args.update_docs:
        # Update documentation only
        result = await update_all_docs(agent)
        print(json.dumps(result, indent=2, default=str))

    elif args.check_api:
        # Check single API
        if args.check_api in agent.api_monitor.MONITORED_APIS:
            result = await agent.api_monitor.check_api(
                args.check_api,
                agent.api_monitor.MONITORED_APIS[args.check_api]
            )
            print(json.dumps(result, indent=2))
        else:
            print(f"Unknown API: {args.check_api}")
            print(f"Available: {list(agent.api_monitor.MONITORED_APIS.keys())}")

    elif args.pipeline:
        # Run full pipeline only
        print("Running full pipeline (reproject → tile → upload → cleanup)...")
        result = await agent.scraper.run_full_pipeline(workers=args.workers)
        print(json.dumps(result, indent=2, default=str))

    elif args.cleanup:
        # Cleanup orphaned files
        print("Cleaning up local files already uploaded to R2...")
        result = await agent.scraper.cleanup_processed_files()
        print(json.dumps(result, indent=2, default=str))

    elif args.scrape:
        # Scrape specific state/county
        print(f"Scraping {args.scrape}" + (f"/{args.county}" if args.county else ""))
        result = await agent.scraper.run_scraper(args.scrape, args.county)
        print(json.dumps(result, indent=2, default=str))

        # Run pipeline after successful scrape
        if result.get("status") == "success":
            print("\nScrape complete. Running full pipeline...")
            pipeline_result = await agent.scraper.run_full_pipeline(workers=args.workers)
            print(json.dumps(pipeline_result, indent=2, default=str))

    elif args.once:
        result = await agent.run_monitoring_cycle(check_all=args.check_all)
        print(json.dumps(result, indent=2, default=str))

    else:
        # Run forever
        await agent.run_forever(
            check_interval_minutes=args.interval,
            full_check_every=args.full_check_every
        )


if __name__ == "__main__":
    asyncio.run(main())
