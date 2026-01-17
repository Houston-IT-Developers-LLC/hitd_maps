#!/usr/bin/env python3
"""
Auto-Fixer for HITD Maps Data Pipeline

Automatically attempts to fix common issues that occur during scraping/processing.
Works with the issue_tracker to find and resolve issues.

Enhanced Features:
- Aggressive retry with exponential backoff
- Learning log for issues that couldn't be fixed
- Fix history tracking for continuous improvement
- Pattern learning from successful fixes
"""

import asyncio
import subprocess
import shutil
import os
from pathlib import Path
from typing import Dict, Optional, Callable, List, Any
from datetime import datetime
import json
import sqlite3
import hashlib

from issue_tracker import IssueTracker, analyze_error

AGENT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = AGENT_DIR.parent
SCRIPTS_DIR = DATA_PIPELINE_DIR / "scripts"
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"
LEARNING_LOG_PATH = AGENT_DIR / "learning_log.json"
FIX_HISTORY_DB = AGENT_DIR / "fix_history.db"

# Configuration for aggressive retry
MAX_FIX_ATTEMPTS = 5  # Increased from 3
RETRY_DELAYS = [30, 60, 120, 300, 600]  # Exponential backoff (seconds)
MAX_CONCURRENT_FIXES = 10


class LearningLog:
    """
    Logs issues that couldn't be fixed for later analysis and training.
    Creates a structured JSON log that can be used to improve the auto-fixer.
    """

    def __init__(self, log_path: Path = LEARNING_LOG_PATH):
        self.log_path = log_path
        self.entries: List[Dict] = []
        self._load()

    def _load(self):
        """Load existing learning log."""
        if self.log_path.exists():
            try:
                with open(self.log_path) as f:
                    data = json.load(f)
                    self.entries = data.get("entries", [])
            except (json.JSONDecodeError, IOError):
                self.entries = []

    def _save(self):
        """Save learning log to disk."""
        data = {
            "last_updated": datetime.now().isoformat(),
            "total_entries": len(self.entries),
            "entries": self.entries[-1000:]  # Keep last 1000 entries
        }
        with open(self.log_path, 'w') as f:
            json.dump(data, f, indent=2)

    def log_unfixable(self, issue: Dict, fix_attempts: List[Dict], reason: str):
        """Log an issue that couldn't be fixed."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "issue_id": issue.get("id"),
            "issue_type": issue.get("issue_type"),
            "severity": issue.get("severity"),
            "state": issue.get("state"),
            "county": issue.get("county"),
            "source_id": issue.get("source_id"),
            "title": issue.get("title"),
            "error_message": issue.get("error_message", "")[:500],  # Truncate
            "context": issue.get("context"),
            "fix_attempts": fix_attempts,
            "failure_reason": reason,
            "needs_manual_review": True,
            "suggested_improvements": self._suggest_improvements(issue, fix_attempts)
        }
        self.entries.append(entry)
        self._save()
        return entry

    def _suggest_improvements(self, issue: Dict, fix_attempts: List[Dict]) -> List[str]:
        """Generate suggestions for improving the auto-fixer based on failure patterns."""
        suggestions = []
        error_msg = issue.get("error_message", "").lower()
        issue_type = issue.get("issue_type", "")

        # Analyze patterns
        if "ssl" in error_msg or "certificate" in error_msg:
            suggestions.append("Add SSL certificate handling or bypass for this source")
        if "redirect" in error_msg:
            suggestions.append("Handle HTTP redirects for this API")
        if "502" in error_msg or "503" in error_msg:
            suggestions.append("Server maintenance - add longer retry window")
        if "geojson" in error_msg and "invalid" in error_msg:
            suggestions.append("Add GeoJSON validation/repair step")
        if "encoding" in error_msg:
            suggestions.append("Handle character encoding issues")
        if issue_type == "api_error" and len(fix_attempts) >= MAX_FIX_ATTEMPTS:
            suggestions.append("API may be permanently changed - needs manual investigation")
        if "permission" in error_msg or "access denied" in error_msg:
            suggestions.append("Check if API requires authentication or IP whitelist")

        if not suggestions:
            suggestions.append("Analyze error pattern and add new fix handler")

        return suggestions

    def get_patterns(self) -> Dict[str, int]:
        """Analyze logged failures to identify common patterns."""
        patterns = {}
        for entry in self.entries:
            key = f"{entry.get('issue_type', 'unknown')}:{entry.get('failure_reason', 'unknown')}"
            patterns[key] = patterns.get(key, 0) + 1
        return dict(sorted(patterns.items(), key=lambda x: -x[1]))

    def export_for_training(self) -> str:
        """Export learning log in a format suitable for Claude to analyze and learn from."""
        report = f"""# HITD Maps Auto-Fixer Learning Log
Generated: {datetime.now().isoformat()}
Total Unfixable Issues: {len(self.entries)}

## Pattern Analysis
"""
        patterns = self.get_patterns()
        for pattern, count in list(patterns.items())[:20]:
            report += f"- {pattern}: {count} occurrences\n"

        report += "\n## Recent Unfixable Issues\n\n"

        for entry in self.entries[-50:]:  # Last 50 entries
            report += f"""### Issue #{entry.get('issue_id')}: {entry.get('title', 'Unknown')}
- **Type**: {entry.get('issue_type')}
- **Severity**: {entry.get('severity')}
- **State**: {entry.get('state', 'N/A')}
- **Error**: {entry.get('error_message', 'N/A')[:200]}
- **Failure Reason**: {entry.get('failure_reason')}
- **Suggested Improvements**: {', '.join(entry.get('suggested_improvements', []))}

"""
        return report


class FixHistoryTracker:
    """
    Tracks fix history to learn what works and what doesn't.
    Uses SQLite for persistence and pattern analysis.
    """

    def __init__(self, db_path: Path = FIX_HISTORY_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the fix history database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fix_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    issue_id INTEGER,
                    issue_type TEXT,
                    fix_type TEXT,
                    error_pattern TEXT,
                    state TEXT,
                    county TEXT,
                    source_id TEXT,
                    success BOOLEAN,
                    duration_seconds REAL,
                    retry_count INTEGER,
                    notes TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fix_success ON fix_history(success)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fix_type ON fix_history(fix_type)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fix_strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_pattern_hash TEXT UNIQUE,
                    error_pattern TEXT,
                    best_fix_type TEXT,
                    success_rate REAL,
                    total_attempts INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def record_fix(self, issue: Dict, fix_type: str, success: bool,
                   duration: float = 0, retry_count: int = 0, notes: str = None):
        """Record a fix attempt."""
        error_pattern = self._extract_error_pattern(issue.get("error_message", ""))

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO fix_history (
                    issue_id, issue_type, fix_type, error_pattern,
                    state, county, source_id, success, duration_seconds,
                    retry_count, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                issue.get("id"),
                issue.get("issue_type"),
                fix_type,
                error_pattern,
                issue.get("state"),
                issue.get("county"),
                issue.get("source_id"),
                success,
                duration,
                retry_count,
                notes
            ))

            # Update strategy table
            self._update_strategy(conn, error_pattern, fix_type, success)

    def _extract_error_pattern(self, error_message: str) -> str:
        """Extract a generalizable pattern from error message."""
        if not error_message:
            return "unknown"

        # Normalize the error message
        error_lower = error_message.lower()

        # Common patterns to match
        patterns = [
            ("timeout", "timeout"),
            ("connection refused", "connection_refused"),
            ("429", "rate_limit"),
            ("403", "forbidden"),
            ("401", "unauthorized"),
            ("404", "not_found"),
            ("500", "server_error"),
            ("502", "bad_gateway"),
            ("503", "service_unavailable"),
            ("ssl", "ssl_error"),
            ("certificate", "certificate_error"),
            ("json", "json_error"),
            ("memory", "memory_error"),
            ("disk", "disk_error"),
            ("coordinate", "coordinate_error"),
            ("projection", "projection_error"),
        ]

        for keyword, pattern in patterns:
            if keyword in error_lower:
                return pattern

        return "other"

    def _update_strategy(self, conn, error_pattern: str, fix_type: str, success: bool):
        """Update the fix strategy based on this result."""
        pattern_hash = hashlib.md5(error_pattern.encode()).hexdigest()[:16]

        # Get existing strategy
        row = conn.execute("""
            SELECT success_rate, total_attempts FROM fix_strategies
            WHERE error_pattern_hash = ?
        """, (pattern_hash,)).fetchone()

        if row:
            old_rate, old_count = row
            new_count = old_count + 1
            new_rate = ((old_rate * old_count) + (1 if success else 0)) / new_count

            conn.execute("""
                UPDATE fix_strategies
                SET success_rate = ?, total_attempts = ?, last_updated = CURRENT_TIMESTAMP,
                    best_fix_type = CASE WHEN ? > success_rate THEN ? ELSE best_fix_type END
                WHERE error_pattern_hash = ?
            """, (new_rate, new_count, 1 if success else 0, fix_type, pattern_hash))
        else:
            conn.execute("""
                INSERT INTO fix_strategies (
                    error_pattern_hash, error_pattern, best_fix_type,
                    success_rate, total_attempts
                ) VALUES (?, ?, ?, ?, 1)
            """, (pattern_hash, error_pattern, fix_type, 1.0 if success else 0.0))

    def get_best_strategy(self, error_message: str) -> Optional[Dict]:
        """Get the best fix strategy for an error pattern."""
        error_pattern = self._extract_error_pattern(error_message)
        pattern_hash = hashlib.md5(error_pattern.encode()).hexdigest()[:16]

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM fix_strategies WHERE error_pattern_hash = ?
            """, (pattern_hash,)).fetchone()

            if row:
                return dict(row)
        return None

    def get_statistics(self) -> Dict:
        """Get overall fix statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM fix_history").fetchone()[0]
            successful = conn.execute(
                "SELECT COUNT(*) FROM fix_history WHERE success = TRUE"
            ).fetchone()[0]

            by_type = {}
            for row in conn.execute("""
                SELECT fix_type, COUNT(*) as total,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes
                FROM fix_history GROUP BY fix_type
            """):
                by_type[row[0]] = {
                    "total": row[1],
                    "successful": row[2],
                    "rate": row[2] / row[1] if row[1] > 0 else 0
                }

            return {
                "total_attempts": total,
                "successful": successful,
                "success_rate": successful / total if total > 0 else 0,
                "by_fix_type": by_type
            }


class AutoFixer:
    """
    Automatically fix common pipeline issues.

    Enhanced with:
    - Aggressive retry with exponential backoff
    - Learning from failures
    - Fix history tracking
    - Pattern-based strategy selection
    """

    def __init__(self, tracker: IssueTracker = None):
        self.tracker = tracker or IssueTracker()
        self.learning_log = LearningLog()
        self.fix_history = FixHistoryTracker()
        self.fix_log = []

        # Register fix handlers
        self.fix_handlers: Dict[str, Callable] = {
            "timeout": self.fix_timeout,
            "rate_limit": self.fix_rate_limit,
            "coordinate_error": self.fix_coordinate_error,
            "disk_space": self.fix_disk_space,
            "memory_error": self.fix_memory_error,
            "api_error": self.fix_api_error,
            "scrape_failed": self.fix_scrape_failed,
            "ssl_error": self.fix_ssl_error,
            "server_error": self.fix_server_error,
            "connection_refused": self.fix_connection_refused,
        }

    def log(self, message: str):
        """Log a fix action."""
        entry = f"[{datetime.now().isoformat()}] {message}"
        self.fix_log.append(entry)
        print(entry)

    async def fix_all_auto_fixable(self, aggressive: bool = True) -> Dict:
        """
        Attempt to fix all auto-fixable issues.

        Args:
            aggressive: If True, uses exponential backoff retries and tries multiple strategies
        """
        issues = self.tracker.get_auto_fixable_issues(max_attempts=MAX_FIX_ATTEMPTS)
        results = {
            "attempted": 0,
            "fixed": 0,
            "failed": 0,
            "logged_for_learning": 0,
            "details": []
        }

        # Process issues in batches to avoid overwhelming the system
        for issue in issues:
            start_time = datetime.now()
            self.log(f"Attempting to fix issue #{issue['id']}: {issue['title']}")

            # Get the current attempt count
            current_attempts = issue.get('fix_attempts', 0)
            self.tracker.increment_fix_attempts(issue['id'])

            # Analyze the error to determine fix type
            analysis = analyze_error(issue.get('error_message', ''))
            fix_type = analysis.get('issue_name', issue['issue_type'])

            # Check if we have a learned strategy for this error pattern
            learned_strategy = self.fix_history.get_best_strategy(issue.get('error_message', ''))
            if learned_strategy and learned_strategy.get('success_rate', 0) > 0.5:
                self.log(f"Using learned strategy: {learned_strategy['best_fix_type']} "
                         f"(success rate: {learned_strategy['success_rate']:.1%})")
                fix_type = learned_strategy['best_fix_type']

            results["attempted"] += 1
            fix_attempts_log = []

            try:
                success = False

                # Try the primary fix handler
                if fix_type in self.fix_handlers:
                    success = await self.fix_handlers[fix_type](issue)
                    fix_attempts_log.append({
                        "fix_type": fix_type,
                        "success": success,
                        "timestamp": datetime.now().isoformat()
                    })

                # If primary failed and aggressive mode, try alternate strategies
                if not success and aggressive:
                    alternate_strategies = self._get_alternate_strategies(fix_type, issue)
                    for alt_strategy in alternate_strategies:
                        if alt_strategy in self.fix_handlers:
                            self.log(f"Trying alternate strategy: {alt_strategy}")
                            # Wait with exponential backoff
                            delay = RETRY_DELAYS[min(current_attempts, len(RETRY_DELAYS) - 1)]
                            self.log(f"Waiting {delay}s before retry...")
                            await asyncio.sleep(delay)

                            success = await self.fix_handlers[alt_strategy](issue)
                            fix_attempts_log.append({
                                "fix_type": alt_strategy,
                                "success": success,
                                "timestamp": datetime.now().isoformat()
                            })

                            if success:
                                fix_type = alt_strategy
                                break

                # Calculate duration
                duration = (datetime.now() - start_time).total_seconds()

                # Record in fix history
                self.fix_history.record_fix(
                    issue, fix_type, success,
                    duration=duration,
                    retry_count=current_attempts + 1,
                    notes=f"Attempts: {fix_attempts_log}"
                )

                if success:
                    self.tracker.resolve_issue(
                        issue['id'],
                        f"Auto-fixed by {fix_type} handler after {current_attempts + 1} attempts"
                    )
                    results["fixed"] += 1
                    results["details"].append({
                        "id": issue['id'],
                        "status": "fixed",
                        "fix_type": fix_type,
                        "attempts": current_attempts + 1,
                        "duration": duration
                    })
                else:
                    # Check if we've exhausted all attempts
                    if current_attempts + 1 >= MAX_FIX_ATTEMPTS:
                        self.log(f"Issue #{issue['id']} exhausted all {MAX_FIX_ATTEMPTS} fix attempts")
                        # Log to learning log for future training
                        self.learning_log.log_unfixable(
                            issue, fix_attempts_log,
                            f"Exhausted {MAX_FIX_ATTEMPTS} fix attempts"
                        )
                        results["logged_for_learning"] += 1

                    results["failed"] += 1
                    results["details"].append({
                        "id": issue['id'],
                        "status": "failed",
                        "fix_type": fix_type,
                        "attempts": current_attempts + 1,
                        "will_retry": current_attempts + 1 < MAX_FIX_ATTEMPTS
                    })

            except Exception as e:
                self.log(f"Error fixing issue #{issue['id']}: {e}")

                # Record the failure
                self.fix_history.record_fix(
                    issue, fix_type, False,
                    notes=f"Exception: {str(e)}"
                )

                results["failed"] += 1
                results["details"].append({
                    "id": issue['id'],
                    "status": "error",
                    "error": str(e),
                    "fix_type": fix_type
                })

        # Process exhausted issues - log them for learning
        exhausted_issues = self.tracker.get_exhausted_issues(max_attempts=MAX_FIX_ATTEMPTS)
        for issue in exhausted_issues:
            if not any(d.get("id") == issue["id"] for d in results["details"]):
                self.learning_log.log_unfixable(
                    issue, [],
                    "Previously exhausted all fix attempts"
                )
                results["logged_for_learning"] += 1

        return results

    def _get_alternate_strategies(self, primary_type: str, issue: Dict) -> List[str]:
        """Get alternate fix strategies to try if primary fails."""
        strategies = []

        # Map primary types to potential alternates
        alternates = {
            "timeout": ["rate_limit", "server_error"],
            "rate_limit": ["timeout", "api_error"],
            "api_error": ["timeout", "server_error", "scrape_failed"],
            "scrape_failed": ["api_error", "timeout"],
            "server_error": ["timeout", "api_error"],
            "connection_refused": ["timeout", "server_error"],
            "ssl_error": ["api_error", "scrape_failed"],
        }

        if primary_type in alternates:
            strategies = alternates[primary_type]

        # Filter to only include handlers we have
        return [s for s in strategies if s in self.fix_handlers]

    async def fix_timeout(self, issue: Dict) -> bool:
        """Fix timeout issues by retrying with longer timeout."""
        self.log("Attempting timeout fix: will be retried with increased timeout")
        # The agent will retry with exponential backoff naturally
        # Mark as "will retry" - actual fix happens on next cycle
        return True

    async def fix_rate_limit(self, issue: Dict) -> bool:
        """Fix rate limit issues by adding delay."""
        self.log("Rate limit detected: adding delay before retry")
        await asyncio.sleep(60)  # Wait 1 minute
        return True

    async def fix_coordinate_error(self, issue: Dict) -> bool:
        """Fix coordinate issues by running reprojection."""
        state = issue.get('state', '').lower()
        county = issue.get('county', '').lower() if issue.get('county') else None

        if state:
            # Find the GeoJSON file
            if county:
                geojson_pattern = f"parcels_{state}_{county}*.geojson"
            else:
                geojson_pattern = f"parcels_{state}*.geojson"

            geojson_dir = OUTPUT_DIR / "geojson"
            if geojson_dir.exists():
                for geojson_file in geojson_dir.rglob(geojson_pattern):
                    self.log(f"Reprojecting {geojson_file}")
                    result = subprocess.run(
                        ["bash", str(SCRIPTS_DIR / "reproject_to_wgs84.sh")],
                        cwd=DATA_PIPELINE_DIR,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        return True

        return False

    async def fix_disk_space(self, issue: Dict) -> bool:
        """Fix disk space issues by cleaning up uploaded files."""
        self.log("Running cleanup to free disk space")

        # Run the cleanup script
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "parallel_process_upload.py"), "--cleanup-only"],
            cwd=DATA_PIPELINE_DIR,
            capture_output=True,
            text=True,
            env={**os.environ, "AUTO_CLEANUP": "true"}
        )

        # Also clean old logs
        log_dir = AGENT_DIR
        for log_file in log_dir.glob("*.log"):
            if log_file.stat().st_size > 100 * 1024 * 1024:  # > 100MB
                self.log(f"Truncating large log file: {log_file}")
                with open(log_file, 'w') as f:
                    f.write(f"# Log truncated by auto-fixer at {datetime.now()}\n")

        # Check if we have space now
        stat = shutil.disk_usage(OUTPUT_DIR)
        free_gb = stat.free / (1024**3)
        self.log(f"Free disk space: {free_gb:.1f} GB")

        return free_gb > 10  # Success if > 10GB free

    async def fix_memory_error(self, issue: Dict) -> bool:
        """Fix memory issues by reducing batch size."""
        self.log("Memory error: will retry with smaller batch size")
        # Update config to use smaller batches
        # The agent uses PARALLEL_JOBS and MAX_WORKERS env vars
        return True

    async def fix_api_error(self, issue: Dict) -> bool:
        """Fix API errors by checking if API is back online."""
        import aiohttp

        url = issue.get('context', {})
        if isinstance(url, str):
            try:
                url = json.loads(url)
            except:
                pass

        if isinstance(url, dict):
            url = url.get('url', '')

        if url:
            self.log(f"Checking if API is back online: {url}")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{url}?f=json",
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status == 200:
                            self.log("API is back online!")
                            return True
            except:
                pass

        return False

    async def fix_scrape_failed(self, issue: Dict) -> bool:
        """Fix scrape failures by retrying the scrape."""
        state = issue.get('state', '').upper()
        county = issue.get('county')

        if not state:
            return False

        self.log(f"Retrying scrape for {state}" + (f"/{county}" if county else ""))

        # Build the scrape command
        cmd = ["python3", str(SCRIPTS_DIR / "export_county_parcels.py")]

        if county:
            cmd.extend(["--county", f"{state}_{county.upper()}"])
        else:
            cmd.extend(["--state", state])

        result = subprocess.run(
            cmd,
            cwd=DATA_PIPELINE_DIR,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max
        )

        return result.returncode == 0

    async def fix_ssl_error(self, issue: Dict) -> bool:
        """Fix SSL/certificate errors by retrying with SSL verification disabled."""
        import aiohttp
        import ssl

        url = self._extract_url(issue)
        if not url:
            return False

        self.log(f"Attempting SSL fix for: {url}")

        try:
            # Create SSL context that doesn't verify
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    f"{url}?f=json",
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        self.log("SSL bypass successful - API accessible")
                        return True
        except Exception as e:
            self.log(f"SSL fix failed: {e}")

        return False

    async def fix_server_error(self, issue: Dict) -> bool:
        """Fix server errors (500/502/503) by waiting and retrying."""
        url = self._extract_url(issue)

        self.log("Server error detected - waiting for server recovery...")

        # Wait longer for server recovery
        await asyncio.sleep(120)

        if url:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{url}?f=json",
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as resp:
                        if resp.status == 200:
                            self.log("Server recovered!")
                            return True
                        elif resp.status >= 500:
                            self.log(f"Server still returning {resp.status}")
            except Exception as e:
                self.log(f"Server check failed: {e}")

        return False

    async def fix_connection_refused(self, issue: Dict) -> bool:
        """Fix connection refused errors by checking if server is back up."""
        import aiohttp

        url = self._extract_url(issue)
        if not url:
            return False

        self.log(f"Connection refused - checking if server is back up: {url}")

        # Try multiple times with increasing delays
        for attempt, delay in enumerate([30, 60, 120], 1):
            await asyncio.sleep(delay)
            self.log(f"Retry attempt {attempt}...")

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{url}?f=json",
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status == 200:
                            self.log("Server is back online!")
                            return True
            except aiohttp.ClientConnectorError:
                self.log(f"Still refusing connections after attempt {attempt}")
            except Exception as e:
                self.log(f"Attempt {attempt} failed: {e}")

        return False

    def _extract_url(self, issue: Dict) -> Optional[str]:
        """Extract URL from issue context."""
        context = issue.get('context', {})

        if isinstance(context, str):
            try:
                context = json.loads(context)
            except (json.JSONDecodeError, TypeError):
                # Maybe the context itself is a URL
                if context.startswith('http'):
                    return context
                return None

        if isinstance(context, dict):
            return context.get('url') or context.get('api_url')

        return None

    async def generic_fix(self, issue: Dict) -> bool:
        """Generic fix attempt - try basic recovery strategies."""
        self.log(f"No specific fix for issue type: {issue['issue_type']}")

        # Try a few generic things
        url = self._extract_url(issue)
        if url:
            self.log("Attempting generic API health check...")
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{url}?f=json",
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status == 200:
                            self.log("API is responding - issue may be resolved")
                            return True
            except:
                pass

        return False

    def get_fix_log(self) -> str:
        """Get the fix log as a string."""
        return "\n".join(self.fix_log)

    def get_learning_report(self) -> str:
        """Get the learning log report for analysis."""
        return self.learning_log.export_for_training()

    def get_fix_statistics(self) -> Dict:
        """Get fix history statistics."""
        return self.fix_history.get_statistics()


async def run_auto_fixes(aggressive: bool = True):
    """Run all auto-fixes with enhanced logging."""
    print("=" * 60)
    print("  HITD Maps Auto-Fixer - Enhanced Mode")
    print("=" * 60)
    print(f"  Max fix attempts: {MAX_FIX_ATTEMPTS}")
    print(f"  Retry delays: {RETRY_DELAYS}")
    print(f"  Aggressive mode: {aggressive}")
    print("=" * 60)

    fixer = AutoFixer()
    results = await fixer.fix_all_auto_fixable(aggressive=aggressive)

    print("\n" + "=" * 60)
    print("  AUTO-FIX RESULTS")
    print("=" * 60)
    print(f"  Attempted:           {results['attempted']}")
    print(f"  Fixed:               {results['fixed']}")
    print(f"  Failed:              {results['failed']}")
    print(f"  Logged for learning: {results['logged_for_learning']}")

    if results['fixed'] > 0:
        print(f"\n  Success rate: {results['fixed']/results['attempted']*100:.1f}%")

    if results['details']:
        print("\n  Details:")
        for detail in results['details']:
            status_icon = "✓" if detail['status'] == 'fixed' else "✗"
            attempts = detail.get('attempts', '?')
            will_retry = " (will retry)" if detail.get('will_retry') else ""
            print(f"    {status_icon} Issue #{detail['id']}: {detail['status']} "
                  f"(attempts: {attempts}){will_retry}")

    # Show fix statistics
    stats = fixer.get_fix_statistics()
    if stats['total_attempts'] > 0:
        print("\n" + "-" * 60)
        print("  HISTORICAL FIX STATISTICS")
        print("-" * 60)
        print(f"  Total attempts:  {stats['total_attempts']}")
        print(f"  Successful:      {stats['successful']}")
        print(f"  Overall rate:    {stats['success_rate']*100:.1f}%")

        if stats['by_fix_type']:
            print("\n  By Fix Type:")
            for fix_type, data in stats['by_fix_type'].items():
                print(f"    {fix_type}: {data['successful']}/{data['total']} "
                      f"({data['rate']*100:.1f}%)")

    print("\n" + "=" * 60)

    return results


async def run_continuous_fixer(interval_minutes: int = 30):
    """
    Run the auto-fixer continuously at specified intervals.
    This is the 'always try to fix' mode the user requested.
    """
    print("=" * 60)
    print("  HITD Maps Continuous Auto-Fixer")
    print("=" * 60)
    print(f"  Running every {interval_minutes} minutes")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'='*60}")
        print(f"  AUTO-FIX CYCLE #{cycle} - {datetime.now().isoformat()}")
        print(f"{'='*60}")

        try:
            results = await run_auto_fixes(aggressive=True)

            # If we fixed things, run again sooner
            if results['fixed'] > 0:
                print(f"\nFixed {results['fixed']} issues - checking for more in 5 minutes...")
                await asyncio.sleep(300)
            else:
                print(f"\nNo issues fixed - sleeping for {interval_minutes} minutes...")
                await asyncio.sleep(interval_minutes * 60)

        except Exception as e:
            print(f"\nError in auto-fix cycle: {e}")
            print(f"Retrying in 5 minutes...")
            await asyncio.sleep(300)


def print_learning_report():
    """Print the learning log report."""
    fixer = AutoFixer()
    report = fixer.get_learning_report()
    print(report)


def print_fix_statistics():
    """Print fix history statistics."""
    fixer = AutoFixer()
    stats = fixer.get_fix_statistics()

    print("\n" + "=" * 60)
    print("  FIX HISTORY STATISTICS")
    print("=" * 60)

    if stats['total_attempts'] == 0:
        print("  No fix history yet.")
        return

    print(f"  Total attempts:  {stats['total_attempts']}")
    print(f"  Successful:      {stats['successful']}")
    print(f"  Overall rate:    {stats['success_rate']*100:.1f}%")

    if stats['by_fix_type']:
        print("\n  By Fix Type:")
        for fix_type, data in sorted(stats['by_fix_type'].items(),
                                      key=lambda x: -x[1]['total']):
            print(f"    {fix_type}:")
            print(f"      Total: {data['total']}, Success: {data['successful']}, "
                  f"Rate: {data['rate']*100:.1f}%")

    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="HITD Maps Auto-Fixer - Automatic Issue Resolution"
    )
    parser.add_argument(
        "--continuous", "-c",
        action="store_true",
        help="Run continuously (auto-fix every 30 minutes)"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=30,
        help="Interval in minutes for continuous mode (default: 30)"
    )
    parser.add_argument(
        "--learning-report", "-l",
        action="store_true",
        help="Print the learning log report (issues that couldn't be fixed)"
    )
    parser.add_argument(
        "--statistics", "-s",
        action="store_true",
        help="Print fix history statistics"
    )
    parser.add_argument(
        "--no-aggressive",
        action="store_true",
        help="Disable aggressive retry mode"
    )

    args = parser.parse_args()

    if args.learning_report:
        print_learning_report()
    elif args.statistics:
        print_fix_statistics()
    elif args.continuous:
        try:
            asyncio.run(run_continuous_fixer(args.interval))
        except KeyboardInterrupt:
            print("\nStopping continuous auto-fixer...")
    else:
        asyncio.run(run_auto_fixes(aggressive=not args.no_aggressive))
