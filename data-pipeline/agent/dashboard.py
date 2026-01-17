#!/usr/bin/env python3
"""
HITD Maps Pipeline Dashboard

A comprehensive status dashboard showing:
- R2 bucket status
- API health
- Issue summary
- Recent activity

Usage:
  python3 dashboard.py           # Show full dashboard
  python3 dashboard.py --watch   # Watch mode (refresh every 30s)
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from issue_tracker import IssueTracker


def get_r2_stats():
    """Get R2 bucket statistics."""
    try:
        import boto3

        client = boto3.client('s3',
            endpoint_url=os.environ.get('R2_ENDPOINT', 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com'),
            aws_access_key_id=os.environ.get('R2_ACCESS_KEY', 'ecd653afe3300fdc045b9980df0dbb14'),
            aws_secret_access_key=os.environ.get('R2_SECRET_KEY', 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'))

        paginator = client.get_paginator('list_objects_v2')

        stats = {
            'total_files': 0,
            'total_size': 0,
            'by_prefix': {},
            'states_covered': set()
        }

        for page in paginator.paginate(Bucket=os.environ.get('R2_BUCKET', 'gspot-tiles')):
            for obj in page.get('Contents', []):
                stats['total_files'] += 1
                stats['total_size'] += obj.get('Size', 0)

                # Get prefix
                key = obj['Key']
                prefix = key.split('/')[0] if '/' in key else 'root'
                if prefix not in stats['by_prefix']:
                    stats['by_prefix'][prefix] = {'count': 0, 'size': 0}
                stats['by_prefix'][prefix]['count'] += 1
                stats['by_prefix'][prefix]['size'] += obj.get('Size', 0)

                # Track states
                if key.startswith('parcels/parcels_'):
                    parts = key.replace('parcels/parcels_', '').split('_')
                    if parts and len(parts[0]) == 2:
                        stats['states_covered'].add(parts[0].upper())

        stats['states_covered'] = sorted(stats['states_covered'])
        return stats

    except Exception as e:
        return {'error': str(e)}


def get_local_stats():
    """Get local file statistics."""
    data_pipeline_dir = Path(__file__).parent.parent
    output_dir = data_pipeline_dir / "output"

    stats = {
        'geojson_files': 0,
        'pmtiles_files': 0,
        'total_local_size': 0
    }

    for geojson in output_dir.rglob("*.geojson"):
        stats['geojson_files'] += 1
        stats['total_local_size'] += geojson.stat().st_size

    for pmtiles in output_dir.rglob("*.pmtiles"):
        stats['pmtiles_files'] += 1
        stats['total_local_size'] += pmtiles.stat().st_size

    return stats


def get_service_status():
    """Check systemd service status."""
    import subprocess
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'hitd-data-agent'],
            capture_output=True, text=True
        )
        return result.stdout.strip()
    except:
        return 'unknown'


def format_size(bytes_size):
    """Format bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} PB"


def print_dashboard():
    """Print the full dashboard."""
    print("\n" + "=" * 60)
    print("          HITD MAPS DATA PIPELINE DASHBOARD")
    print("=" * 60)
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Service Status
    service_status = get_service_status()
    status_icon = "🟢" if service_status == "active" else "🔴"
    print(f"\n{status_icon} SERVICE STATUS: {service_status}")

    # R2 Stats
    print("\n" + "-" * 60)
    print("  CLOUDFLARE R2 BUCKET")
    print("-" * 60)

    r2_stats = get_r2_stats()
    if 'error' in r2_stats:
        print(f"  ❌ Error: {r2_stats['error']}")
    else:
        print(f"  Total Files: {r2_stats['total_files']}")
        print(f"  Total Size:  {format_size(r2_stats['total_size'])}")
        print(f"\n  States with Data: {len(r2_stats['states_covered'])}/50")
        print(f"  {', '.join(r2_stats['states_covered'][:25])}")
        if len(r2_stats['states_covered']) > 25:
            print(f"  {', '.join(r2_stats['states_covered'][25:])}")

        print(f"\n  By Category:")
        for prefix, data in sorted(r2_stats['by_prefix'].items()):
            print(f"    {prefix}: {data['count']} files ({format_size(data['size'])})")

    # Local Stats
    print("\n" + "-" * 60)
    print("  LOCAL FILES")
    print("-" * 60)

    local_stats = get_local_stats()
    print(f"  GeoJSON Files:  {local_stats['geojson_files']}")
    print(f"  PMTiles Files:  {local_stats['pmtiles_files']}")
    print(f"  Total Size:     {format_size(local_stats['total_local_size'])}")

    # Issue Tracking
    print("\n" + "-" * 60)
    print("  ISSUE TRACKER")
    print("-" * 60)

    try:
        tracker = IssueTracker()
        summary = tracker.get_issues_summary()
        print(f"  Total Issues:  {summary['total']}")
        print(f"  Open:          {summary['open']}")
        print(f"  Resolved:      {summary['resolved']}")

        if summary['by_severity']:
            print(f"\n  By Severity:")
            for sev, count in sorted(summary['by_severity'].items()):
                icon = "🔴" if sev == "critical" else "🟠" if sev == "error" else "🟡" if sev == "warning" else "🔵"
                print(f"    {icon} {sev}: {count}")

        if summary['open'] > 0:
            print(f"\n  Recent Open Issues:")
            issues = tracker.get_open_issues(limit=5)
            for issue in issues:
                print(f"    #{issue['id']}: {issue['title'][:50]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Quick Commands
    print("\n" + "-" * 60)
    print("  QUICK COMMANDS")
    print("-" * 60)
    print("  Check status:     python3 agent/data_agent.py --once")
    print("  View issues:      python3 agent/data_agent.py --issues")
    print("  Export for Claude: python3 agent/data_agent.py --issues-export")
    print("  Run auto-fix:     python3 agent/data_agent.py --auto-fix")
    print("  View logs:        tail -f agent/agent.log")

    print("\n" + "=" * 60 + "\n")


async def watch_mode():
    """Watch mode - refresh dashboard every 30 seconds."""
    while True:
        os.system('clear' if os.name != 'nt' else 'cls')
        print_dashboard()
        print("Refreshing in 30 seconds... (Ctrl+C to exit)")
        await asyncio.sleep(30)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HITD Maps Pipeline Dashboard")
    parser.add_argument("--watch", action="store_true", help="Watch mode")
    args = parser.parse_args()

    if args.watch:
        try:
            asyncio.run(watch_mode())
        except KeyboardInterrupt:
            print("\nExiting...")
    else:
        print_dashboard()


if __name__ == "__main__":
    main()
