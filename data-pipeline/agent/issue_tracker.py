#!/usr/bin/env python3
"""
Issue Tracker for HITD Maps Data Pipeline

Logs issues encountered during scraping/processing so they can be reviewed
and fixed later (either manually or by Claude).

Issues are stored in SQLite with full context for debugging.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import traceback

AGENT_DIR = Path(__file__).parent
ISSUES_DB = AGENT_DIR / "issues.db"


class IssueTracker:
    """Track and manage pipeline issues."""

    SEVERITY_LEVELS = ["critical", "error", "warning", "info"]
    ISSUE_TYPES = [
        "api_error",           # API returned error or timeout
        "scrape_failed",       # Scraping failed
        "reproject_failed",    # Coordinate reprojection failed
        "tile_failed",         # PMTiles generation failed
        "upload_failed",       # R2 upload failed
        "invalid_data",        # Data validation failed
        "missing_data",        # Expected data not found
        "config_error",        # Configuration problem
        "dependency_error",    # Missing tool or library
        "unknown"              # Catch-all
    ]

    def __init__(self, db_path: Path = ISSUES_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the issues database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    severity TEXT NOT NULL,
                    issue_type TEXT NOT NULL,
                    source_id TEXT,
                    state TEXT,
                    county TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    error_message TEXT,
                    stack_trace TEXT,
                    context JSON,
                    suggested_fix TEXT,
                    resolution TEXT,
                    auto_fixable BOOLEAN DEFAULT FALSE,
                    fix_attempts INTEGER DEFAULT 0
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_issues_state ON issues(state)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues(severity)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_issues_resolved ON issues(resolved_at)
            """)

    def log_issue(
        self,
        title: str,
        issue_type: str,
        severity: str = "error",
        source_id: str = None,
        state: str = None,
        county: str = None,
        description: str = None,
        error_message: str = None,
        exception: Exception = None,
        context: Dict[str, Any] = None,
        suggested_fix: str = None,
        auto_fixable: bool = False
    ) -> int:
        """Log a new issue.

        Returns the issue ID.
        """
        stack_trace = None
        if exception:
            stack_trace = traceback.format_exc()
            if not error_message:
                error_message = str(exception)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO issues (
                    severity, issue_type, source_id, state, county,
                    title, description, error_message, stack_trace,
                    context, suggested_fix, auto_fixable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                severity, issue_type, source_id, state, county,
                title, description, error_message, stack_trace,
                json.dumps(context) if context else None,
                suggested_fix, auto_fixable
            ))
            return cursor.lastrowid

    def resolve_issue(self, issue_id: int, resolution: str):
        """Mark an issue as resolved."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE issues
                SET resolved_at = CURRENT_TIMESTAMP, resolution = ?
                WHERE id = ?
            """, (resolution, issue_id))

    def increment_fix_attempts(self, issue_id: int):
        """Increment the fix attempt counter."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE issues
                SET fix_attempts = fix_attempts + 1
                WHERE id = ?
            """, (issue_id,))

    def get_open_issues(
        self,
        severity: str = None,
        issue_type: str = None,
        state: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get unresolved issues, optionally filtered."""
        query = "SELECT * FROM issues WHERE resolved_at IS NULL"
        params = []

        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if issue_type:
            query += " AND issue_type = ?"
            params.append(issue_type)
        if state:
            query += " AND state = ?"
            params.append(state)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_auto_fixable_issues(self, max_attempts: int = 5) -> List[Dict]:
        """Get issues that can be automatically fixed."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM issues
                WHERE resolved_at IS NULL
                AND auto_fixable = TRUE
                AND fix_attempts < ?
                ORDER BY severity DESC, created_at ASC
            """, (max_attempts,)).fetchall()
            return [dict(row) for row in rows]

    def get_exhausted_issues(self, max_attempts: int = 5) -> List[Dict]:
        """Get issues that have exhausted all fix attempts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM issues
                WHERE resolved_at IS NULL
                AND auto_fixable = TRUE
                AND fix_attempts >= ?
                ORDER BY created_at DESC
            """, (max_attempts,)).fetchall()
            return [dict(row) for row in rows]

    def get_issues_summary(self) -> Dict:
        """Get summary statistics of issues."""
        with sqlite3.connect(self.db_path) as conn:
            # Total counts
            total = conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
            open_count = conn.execute(
                "SELECT COUNT(*) FROM issues WHERE resolved_at IS NULL"
            ).fetchone()[0]
            resolved = total - open_count

            # By severity
            by_severity = {}
            for row in conn.execute("""
                SELECT severity, COUNT(*) as count
                FROM issues WHERE resolved_at IS NULL
                GROUP BY severity
            """):
                by_severity[row[0]] = row[1]

            # By type
            by_type = {}
            for row in conn.execute("""
                SELECT issue_type, COUNT(*) as count
                FROM issues WHERE resolved_at IS NULL
                GROUP BY issue_type
            """):
                by_type[row[0]] = row[1]

            # By state
            by_state = {}
            for row in conn.execute("""
                SELECT state, COUNT(*) as count
                FROM issues WHERE resolved_at IS NULL AND state IS NOT NULL
                GROUP BY state
            """):
                by_state[row[0]] = row[1]

            return {
                "total": total,
                "open": open_count,
                "resolved": resolved,
                "by_severity": by_severity,
                "by_type": by_type,
                "by_state": by_state
            }

    def export_for_claude(self, limit: int = 50) -> str:
        """Export open issues in a format suitable for Claude to analyze.

        Returns a markdown-formatted report.
        """
        issues = self.get_open_issues(limit=limit)
        summary = self.get_issues_summary()

        report = f"""# HITD Maps Pipeline Issues Report
Generated: {datetime.now().isoformat()}

## Summary
- **Total Issues**: {summary['total']}
- **Open**: {summary['open']}
- **Resolved**: {summary['resolved']}

### By Severity
"""
        for sev, count in sorted(summary['by_severity'].items()):
            report += f"- {sev}: {count}\n"

        report += "\n### By Type\n"
        for typ, count in sorted(summary['by_type'].items()):
            report += f"- {typ}: {count}\n"

        if summary['by_state']:
            report += "\n### By State\n"
            for state, count in sorted(summary['by_state'].items()):
                report += f"- {state}: {count}\n"

        report += "\n## Open Issues\n\n"

        for issue in issues:
            report += f"""### Issue #{issue['id']}: {issue['title']}
- **Type**: {issue['issue_type']}
- **Severity**: {issue['severity']}
- **State**: {issue.get('state', 'N/A')}
- **Source**: {issue.get('source_id', 'N/A')}
- **Created**: {issue['created_at']}
- **Fix Attempts**: {issue['fix_attempts']}
- **Auto-fixable**: {issue['auto_fixable']}

**Error**: {issue.get('error_message', 'No error message')}

**Description**: {issue.get('description', 'No description')}

**Suggested Fix**: {issue.get('suggested_fix', 'No suggestion')}

"""
            if issue.get('context'):
                try:
                    ctx = json.loads(issue['context'])
                    report += f"**Context**: ```json\n{json.dumps(ctx, indent=2)}\n```\n\n"
                except:
                    pass

            report += "---\n\n"

        return report


# Common issue patterns and suggested fixes
KNOWN_ISSUES = {
    "timeout": {
        "pattern": ["timeout", "timed out", "connect timeout"],
        "suggested_fix": "Increase timeout or retry with exponential backoff",
        "auto_fixable": True
    },
    "rate_limit": {
        "pattern": ["429", "rate limit", "too many requests"],
        "suggested_fix": "Add delay between requests or reduce batch size",
        "auto_fixable": True
    },
    "auth_error": {
        "pattern": ["401", "403", "unauthorized", "forbidden"],
        "suggested_fix": "Check API credentials or access permissions",
        "auto_fixable": False
    },
    "invalid_json": {
        "pattern": ["json decode", "invalid json", "expecting value"],
        "suggested_fix": "API returned non-JSON response, check endpoint URL",
        "auto_fixable": False
    },
    "coordinate_error": {
        "pattern": ["coordinate", "crs", "projection", "epsg"],
        "suggested_fix": "Run reproject_to_wgs84.sh to fix coordinate system",
        "auto_fixable": True
    },
    "disk_space": {
        "pattern": ["no space", "disk full", "cannot write"],
        "suggested_fix": "Run cleanup to remove uploaded files, or expand storage",
        "auto_fixable": True
    },
    "memory_error": {
        "pattern": ["memory", "killed", "oom"],
        "suggested_fix": "Reduce batch size or process smaller regions",
        "auto_fixable": True
    }
}


def analyze_error(error_message: str) -> Dict:
    """Analyze an error message and return suggested fix info."""
    error_lower = error_message.lower()

    for issue_name, issue_info in KNOWN_ISSUES.items():
        for pattern in issue_info["pattern"]:
            if pattern in error_lower:
                return {
                    "issue_name": issue_name,
                    "suggested_fix": issue_info["suggested_fix"],
                    "auto_fixable": issue_info["auto_fixable"]
                }

    return {
        "issue_name": "unknown",
        "suggested_fix": "Review error details and fix manually",
        "auto_fixable": False
    }


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="HITD Maps Issue Tracker")
    parser.add_argument("--summary", action="store_true", help="Show issues summary")
    parser.add_argument("--list", action="store_true", help="List open issues")
    parser.add_argument("--export", action="store_true", help="Export for Claude")
    parser.add_argument("--severity", type=str, help="Filter by severity")
    parser.add_argument("--state", type=str, help="Filter by state")
    parser.add_argument("--resolve", type=int, help="Resolve issue by ID")
    parser.add_argument("--resolution", type=str, help="Resolution message")

    args = parser.parse_args()
    tracker = IssueTracker()

    if args.summary:
        summary = tracker.get_issues_summary()
        print(json.dumps(summary, indent=2))

    elif args.list:
        issues = tracker.get_open_issues(severity=args.severity, state=args.state)
        for issue in issues:
            print(f"[{issue['severity'].upper()}] #{issue['id']}: {issue['title']}")
            print(f"  State: {issue.get('state', 'N/A')} | Type: {issue['issue_type']}")
            print(f"  Error: {issue.get('error_message', 'N/A')[:100]}")
            print()

    elif args.export:
        report = tracker.export_for_claude()
        print(report)

    elif args.resolve and args.resolution:
        tracker.resolve_issue(args.resolve, args.resolution)
        print(f"Issue #{args.resolve} resolved")

    else:
        parser.print_help()
