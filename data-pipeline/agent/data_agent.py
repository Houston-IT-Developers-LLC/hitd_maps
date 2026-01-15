#!/usr/bin/env python3
"""
Autonomous Data Agent for MyGSpot Outdoors
==========================================
Continuously monitors data sources, runs scrapers, and updates documentation.
Uses local Ollama models for intelligent decision-making.

Run as: python3 data_agent.py
Or install as systemd service: sudo systemctl start data-agent
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
    """Monitor ArcGIS APIs for data updates."""

    # Key APIs to monitor (subset from your COUNTY_CONFIGS)
    MONITORED_APIS = {
        "tx_statewide": {
            "url": "https://feature.stratmap.tnris.org/arcgis/rest/services/Land_Parcels/Statewide_Land_Parcels/MapServer/0",
            "state": "TX",
            "expected_records": 28000000
        },
        "fl_statewide": {
            "url": "https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/PARCELS/MapServer/0",
            "state": "FL",
            "expected_records": 10000000
        },
        "ny_statewide": {
            "url": "https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/arcgis/rest/services/NYS_Tax_Parcels_Public/FeatureServer/0",
            "state": "NY",
            "expected_records": 9000000
        },
        "ca_la_county": {
            "url": "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0",
            "state": "CA",
            "county": "los_angeles",
            "expected_records": 2500000
        },
        "oh_statewide": {
            "url": "https://gis.ohiosos.gov/arcgis/rest/services/OpenData/OpenData/MapServer/0",
            "state": "OH",
            "expected_records": 5500000
        }
    }

    def __init__(self, state: AgentState, ollama: OllamaClient):
        self.state = state
        self.ollama = ollama

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

    async def check_all_apis(self) -> list:
        """Check all monitored APIs concurrently."""
        tasks = [
            self.check_api(source_id, config)
            for source_id, config in self.MONITORED_APIS.items()
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

        # Check intervals
        self.api_check_interval = timedelta(hours=6)
        self.scrape_check_interval = timedelta(hours=12)

    async def run_monitoring_cycle(self):
        """Run one monitoring cycle."""
        logger.info("Starting monitoring cycle")

        # 1. Check all APIs
        api_results = await self.api_monitor.check_all_apis()
        logger.info(f"Checked {len(api_results)} APIs")

        # 2. Analyze changes and decide on scraping
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

    async def run_forever(self, check_interval_minutes: int = 360):
        """Run the agent continuously with full pipeline.

        Each cycle:
        1. Check all APIs for data changes
        2. Queue and run scrapes for changed data
        3. Run full pipeline (reproject → tile → upload → cleanup)
        4. Clean up any orphaned local files
        5. Update documentation
        """
        logger.info("Data Agent starting continuous operation")
        logger.info(f"Interval: {check_interval_minutes} minutes")

        while True:
            try:
                # Run monitoring cycle
                cycle_result = await self.run_monitoring_cycle()

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

                logger.info(f"Cycle complete. Sleeping {check_interval_minutes} minutes")
                await asyncio.sleep(check_interval_minutes * 60)

            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(60)  # Short sleep on error


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="MyGSpot Data Agent - Autonomous Data Pipeline")
    parser.add_argument("--once", action="store_true", help="Run one monitoring cycle and exit")
    parser.add_argument("--interval", type=int, default=360,
                        help="Check interval in minutes (default: 360)")
    parser.add_argument("--check-api", type=str, help="Check a specific API")
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
    args = parser.parse_args()

    agent = DataAgent()

    if args.check_api:
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

        # Ask if user wants to run pipeline
        if result.get("status") == "success":
            print("\nScrape complete. Running full pipeline...")
            pipeline_result = await agent.scraper.run_full_pipeline(workers=args.workers)
            print(json.dumps(pipeline_result, indent=2, default=str))

    elif args.once:
        result = await agent.run_monitoring_cycle()
        print(json.dumps(result, indent=2, default=str))

    else:
        # Run forever
        await agent.run_forever(args.interval)


if __name__ == "__main__":
    asyncio.run(main())
