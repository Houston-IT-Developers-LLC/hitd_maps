#!/usr/bin/env python3
"""
Master Health Orchestrator for HITD Maps
=========================================
Comprehensive system health checker and fix deployer.

Checks:
1. R2 bucket data integrity (basemap, parcels, terrain, transit)
2. API endpoints availability
3. Local files status
4. Demo accessibility
5. Pipeline health

Deploys auto-fixers for any issues found.

Run: python3 master_orchestrator.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import socket

import aiohttp
import boto3
from botocore.exceptions import ClientError

# Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

AGENT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = AGENT_DIR.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"
DEMO_DIR = DATA_PIPELINE_DIR.parent / "demo"

# Expected R2 data
REQUIRED_R2_FILES = {
    "basemap": ["basemap/planet.pmtiles"],
    "terrain": ["terrain/terrain-rgb-texas.pmtiles"],
    "transit": ["transit/houston_metro.pmtiles"],
    "parcels": [],  # Dynamic - many files
}


class HealthReport:
    """Stores health check results."""

    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.checks = {}
        self.issues = []
        self.warnings = []
        self.passed = 0
        self.failed = 0

    def add_check(self, name: str, status: str, details: str = "", data: dict = None):
        """Add a health check result."""
        self.checks[name] = {
            "status": status,
            "details": details,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        if status == "pass":
            self.passed += 1
        elif status == "fail":
            self.failed += 1
            self.issues.append(f"{name}: {details}")
        elif status == "warn":
            self.warnings.append(f"{name}: {details}")

    def summary(self) -> str:
        """Generate summary report."""
        total = self.passed + self.failed
        lines = [
            "=" * 60,
            "  HITD MAPS SYSTEM HEALTH REPORT",
            "=" * 60,
            f"  Timestamp: {self.timestamp}",
            f"  Checks: {self.passed}/{total} passed",
            "",
        ]

        if self.issues:
            lines.append("  ISSUES FOUND:")
            for issue in self.issues:
                lines.append(f"    - {issue}")
            lines.append("")

        if self.warnings:
            lines.append("  WARNINGS:")
            for warn in self.warnings:
                lines.append(f"    - {warn}")
            lines.append("")

        lines.append("  DETAILED RESULTS:")
        for name, result in self.checks.items():
            icon = "✓" if result["status"] == "pass" else ("⚠" if result["status"] == "warn" else "✗")
            lines.append(f"    {icon} {name}: {result['status'].upper()}")
            if result["details"]:
                lines.append(f"        {result['details']}")

        lines.append("=" * 60)
        return "\n".join(lines)


class MasterOrchestrator:
    """Master health checker and fix deployer."""

    def __init__(self):
        self.report = HealthReport()
        self.s3_client = None

    def get_s3_client(self):
        """Get or create S3 client for R2."""
        if not self.s3_client:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=R2_ENDPOINT,
                aws_access_key_id=R2_ACCESS_KEY,
                aws_secret_access_key=R2_SECRET_KEY,
            )
        return self.s3_client

    async def check_r2_connectivity(self) -> bool:
        """Check if R2 bucket is accessible."""
        print("Checking R2 connectivity...")
        try:
            client = self.get_s3_client()
            response = client.head_bucket(Bucket=R2_BUCKET)
            self.report.add_check(
                "r2_connectivity",
                "pass",
                f"Connected to bucket: {R2_BUCKET}"
            )
            return True
        except Exception as e:
            self.report.add_check(
                "r2_connectivity",
                "fail",
                f"Cannot connect to R2: {e}"
            )
            return False

    async def check_r2_data_integrity(self) -> Dict:
        """Check all expected data exists in R2."""
        print("Checking R2 data integrity...")
        client = self.get_s3_client()

        inventory = {
            "basemap": [],
            "parcels": [],
            "terrain": [],
            "transit": [],
            "pois": [],
            "roads": [],
            "addresses": [],
            "other": []
        }
        total_size = 0

        try:
            paginator = client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=R2_BUCKET):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    size = obj['Size']
                    total_size += size

                    if key.startswith('basemap/'):
                        inventory["basemap"].append({"key": key, "size": size})
                    elif key.startswith('parcels/'):
                        inventory["parcels"].append({"key": key, "size": size})
                    elif key.startswith('terrain/'):
                        inventory["terrain"].append({"key": key, "size": size})
                    elif key.startswith('transit/'):
                        inventory["transit"].append({"key": key, "size": size})
                    elif key.startswith('pois/') or key.startswith('poi/'):
                        inventory["pois"].append({"key": key, "size": size})
                    elif key.startswith('roads/'):
                        inventory["roads"].append({"key": key, "size": size})
                    elif key.startswith('addresses/'):
                        inventory["addresses"].append({"key": key, "size": size})
                    else:
                        inventory["other"].append({"key": key, "size": size})

        except Exception as e:
            self.report.add_check(
                "r2_inventory",
                "fail",
                f"Failed to list R2 objects: {e}"
            )
            return inventory

        # Calculate sizes
        sizes = {k: sum(f["size"] for f in v) / (1024**3) for k, v in inventory.items()}
        total_gb = total_size / (1024**3)

        # Check required files
        missing = []

        # Check basemap
        if not inventory["basemap"]:
            missing.append("basemap/planet.pmtiles")
        else:
            basemap_size = sizes["basemap"]
            if basemap_size < 100:  # Should be ~109GB
                self.report.add_check(
                    "basemap_size",
                    "warn",
                    f"Basemap is {basemap_size:.1f}GB (expected ~109GB)"
                )
            else:
                self.report.add_check(
                    "basemap_size",
                    "pass",
                    f"Basemap: {basemap_size:.1f}GB"
                )

        # Check terrain
        if not inventory["terrain"]:
            missing.append("terrain/terrain-rgb-texas.pmtiles")
        else:
            self.report.add_check(
                "terrain_data",
                "pass",
                f"Terrain tiles: {len(inventory['terrain'])} files, {sizes['terrain']:.2f}GB"
            )

        # Check transit
        if not inventory["transit"]:
            missing.append("transit/houston_metro.pmtiles")
        else:
            self.report.add_check(
                "transit_data",
                "pass",
                f"Transit data: {len(inventory['transit'])} files"
            )

        # Check parcels
        if len(inventory["parcels"]) < 50:  # Should have 50 states
            self.report.add_check(
                "parcels_count",
                "warn",
                f"Only {len(inventory['parcels'])} parcel files (expected 50+ states)"
            )
        else:
            self.report.add_check(
                "parcels_count",
                "pass",
                f"Parcels: {len(inventory['parcels'])} files, {sizes['parcels']:.1f}GB"
            )

        if missing:
            self.report.add_check(
                "r2_required_files",
                "fail",
                f"Missing required files: {', '.join(missing)}"
            )
        else:
            self.report.add_check(
                "r2_required_files",
                "pass",
                "All required files present"
            )

        self.report.add_check(
            "r2_total_storage",
            "pass",
            f"Total R2 storage: {total_gb:.1f}GB",
            data={"total_gb": total_gb, "by_category": sizes}
        )

        return inventory

    async def check_r2_public_access(self) -> bool:
        """Check if R2 files are publicly accessible."""
        print("Checking R2 public access...")
        test_urls = [
            f"{R2_PUBLIC_URL}/basemap/planet.pmtiles",
            f"{R2_PUBLIC_URL}/terrain/terrain-rgb-texas.pmtiles",
            f"{R2_PUBLIC_URL}/transit/houston_metro.pmtiles",
        ]

        async with aiohttp.ClientSession() as session:
            for url in test_urls:
                try:
                    async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            self.report.add_check(
                                f"public_access_{url.split('/')[-1]}",
                                "pass",
                                f"Accessible: {url.split('/')[-1]}"
                            )
                        else:
                            self.report.add_check(
                                f"public_access_{url.split('/')[-1]}",
                                "fail",
                                f"HTTP {resp.status}: {url}"
                            )
                except Exception as e:
                    # File might not exist - that's different from access issue
                    if "terrain" in url or "transit" in url:
                        self.report.add_check(
                            f"public_access_{url.split('/')[-1]}",
                            "warn",
                            f"Cannot verify: {e}"
                        )
                    else:
                        self.report.add_check(
                            f"public_access_{url.split('/')[-1]}",
                            "fail",
                            f"Access error: {e}"
                        )
        return True

    async def check_demo_server(self) -> bool:
        """Check if demo server is running and accessible."""
        print("Checking demo server...")

        # Check if port 8080 is in use
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8080))
        sock.close()

        if result == 0:
            # Port is open, check if it's serving the demo
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "http://localhost:8080",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        if resp.status == 200:
                            content = await resp.text()
                            if "HITD Maps" in content or "maplibregl" in content:
                                self.report.add_check(
                                    "demo_server",
                                    "pass",
                                    "Demo running at http://localhost:8080"
                                )
                                return True
            except:
                pass

            self.report.add_check(
                "demo_server",
                "warn",
                "Port 8080 in use but may not be demo"
            )
            return True
        else:
            self.report.add_check(
                "demo_server",
                "fail",
                "Demo server not running on port 8080"
            )
            return False

    async def check_local_disk_space(self) -> bool:
        """Check available disk space."""
        print("Checking disk space...")
        import shutil

        stat = shutil.disk_usage(OUTPUT_DIR.parent)
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_pct = (stat.used / stat.total) * 100

        if free_gb < 10:
            self.report.add_check(
                "disk_space",
                "fail",
                f"Low disk space: {free_gb:.1f}GB free ({used_pct:.1f}% used)"
            )
            return False
        elif free_gb < 50:
            self.report.add_check(
                "disk_space",
                "warn",
                f"Disk space low: {free_gb:.1f}GB free ({used_pct:.1f}% used)"
            )
            return True
        else:
            self.report.add_check(
                "disk_space",
                "pass",
                f"Disk space OK: {free_gb:.1f}GB free of {total_gb:.1f}GB"
            )
            return True

    async def check_pipeline_dependencies(self) -> bool:
        """Check if required tools are installed."""
        print("Checking pipeline dependencies...")

        tools = {
            "python3": "python3 --version",
            "tippecanoe": "tippecanoe --version",
            "pmtiles": "pmtiles --version",
            "ogr2ogr": "ogr2ogr --version",
        }

        all_ok = True
        for tool, cmd in tools.items():
            try:
                result = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip() or result.stderr.strip()
                    version = version.split('\n')[0][:50]
                    self.report.add_check(
                        f"tool_{tool}",
                        "pass",
                        f"{tool}: {version}"
                    )
                else:
                    self.report.add_check(
                        f"tool_{tool}",
                        "warn",
                        f"{tool}: installed but returned error"
                    )
            except FileNotFoundError:
                self.report.add_check(
                    f"tool_{tool}",
                    "fail",
                    f"{tool}: NOT INSTALLED"
                )
                all_ok = False
            except Exception as e:
                self.report.add_check(
                    f"tool_{tool}",
                    "warn",
                    f"{tool}: check failed - {e}"
                )

        return all_ok

    async def check_sample_apis(self) -> bool:
        """Check a few sample ArcGIS APIs are responding."""
        print("Checking sample APIs...")

        sample_apis = [
            ("TX Harris Parcels", "https://gis.hctx.net/arcgis/rest/services/Parcels/MapServer/0"),
            ("TX Statewide Parcels", "https://services.arcgis.com/KTcxiTD9dsQw4r7Z/arcgis/rest/services/Texas_Parcels/FeatureServer/0"),
        ]

        async with aiohttp.ClientSession() as session:
            for name, url in sample_apis:
                try:
                    async with session.get(
                        f"{url}?f=json",
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if "error" not in data:
                                self.report.add_check(
                                    f"api_{name.replace(' ', '_').lower()}",
                                    "pass",
                                    f"{name}: responding"
                                )
                            else:
                                self.report.add_check(
                                    f"api_{name.replace(' ', '_').lower()}",
                                    "fail",
                                    f"{name}: API error - {data.get('error', {}).get('message', 'unknown')}"
                                )
                        else:
                            self.report.add_check(
                                f"api_{name.replace(' ', '_').lower()}",
                                "fail",
                                f"{name}: HTTP {resp.status}"
                            )
                except asyncio.TimeoutError:
                    self.report.add_check(
                        f"api_{name.replace(' ', '_').lower()}",
                        "warn",
                        f"{name}: timeout"
                    )
                except Exception as e:
                    self.report.add_check(
                        f"api_{name.replace(' ', '_').lower()}",
                        "fail",
                        f"{name}: {e}"
                    )

        return True

    async def run_all_checks(self) -> HealthReport:
        """Run all health checks."""
        print("\n" + "=" * 60)
        print("  HITD MAPS SYSTEM HEALTH CHECK")
        print("=" * 60 + "\n")

        # Run checks in order
        await self.check_r2_connectivity()
        await self.check_r2_data_integrity()
        await self.check_r2_public_access()
        await self.check_demo_server()
        await self.check_local_disk_space()
        await self.check_pipeline_dependencies()
        await self.check_sample_apis()

        return self.report

    async def deploy_fixes(self) -> Dict:
        """Deploy auto-fixers for any issues found."""
        print("\n" + "=" * 60)
        print("  DEPLOYING AUTO-FIXERS")
        print("=" * 60 + "\n")

        results = {
            "fixes_attempted": 0,
            "fixes_successful": 0,
            "actions_taken": []
        }

        # Check for specific issues and deploy appropriate fixes

        # 1. Demo server not running
        demo_check = self.report.checks.get("demo_server", {})
        if demo_check.get("status") == "fail":
            print("Attempting to start demo server...")
            try:
                # Start the server in background
                subprocess.Popen(
                    ["python3", "-m", "http.server", "8080"],
                    cwd=str(DEMO_DIR),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                results["fixes_attempted"] += 1
                results["actions_taken"].append("Started demo server on port 8080")
                results["fixes_successful"] += 1
                print("  Started demo server")
            except Exception as e:
                results["actions_taken"].append(f"Failed to start demo: {e}")
                print(f"  Failed: {e}")

        # 2. Disk space issues
        disk_check = self.report.checks.get("disk_space", {})
        if disk_check.get("status") in ["fail", "warn"]:
            print("Attempting to free disk space...")
            try:
                # Run cleanup
                from data_agent import DataAgent
                agent = DataAgent()
                cleanup_result = await agent.scraper.cleanup_processed_files()
                results["fixes_attempted"] += 1
                if cleanup_result.get("status") == "success":
                    results["fixes_successful"] += 1
                    results["actions_taken"].append(
                        f"Cleaned up {cleanup_result.get('cleaned', 0)} files"
                    )
                    print(f"  Cleaned {cleanup_result.get('cleaned', 0)} files")
            except Exception as e:
                results["actions_taken"].append(f"Cleanup failed: {e}")
                print(f"  Cleanup failed: {e}")

        # 3. Run general auto-fixer for any tracked issues
        print("\nRunning general auto-fixer...")
        try:
            from auto_fixer import AutoFixer
            from issue_tracker import IssueTracker

            tracker = IssueTracker()
            fixer = AutoFixer(tracker)

            fix_results = await fixer.fix_all_auto_fixable(aggressive=True)
            results["fixes_attempted"] += fix_results.get("attempted", 0)
            results["fixes_successful"] += fix_results.get("fixed", 0)

            if fix_results.get("fixed", 0) > 0:
                results["actions_taken"].append(
                    f"Auto-fixer resolved {fix_results['fixed']} issues"
                )
                print(f"  Auto-fixer resolved {fix_results['fixed']} issues")
            else:
                print("  No issues to auto-fix")

        except ImportError:
            print("  Auto-fixer modules not available")
        except Exception as e:
            results["actions_taken"].append(f"Auto-fixer error: {e}")
            print(f"  Auto-fixer error: {e}")

        return results


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="HITD Maps Master Health Orchestrator"
    )
    parser.add_argument(
        "--check-only", "-c",
        action="store_true",
        help="Run health checks only, don't deploy fixes"
    )
    parser.add_argument(
        "--fix-only", "-f",
        action="store_true",
        help="Run auto-fixers only (skip health checks)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously (check every 30 minutes)"
    )
    args = parser.parse_args()

    orchestrator = MasterOrchestrator()

    if args.continuous:
        print("Running in continuous mode (Ctrl+C to stop)")
        while True:
            try:
                report = await orchestrator.run_all_checks()
                print(report.summary())

                if report.failed > 0:
                    print("\nIssues found - deploying fixes...")
                    fixes = await orchestrator.deploy_fixes()
                    print(f"\nFix results: {fixes['fixes_successful']}/{fixes['fixes_attempted']} successful")

                print(f"\nNext check in 30 minutes...")
                await asyncio.sleep(1800)

                # Reset for next cycle
                orchestrator = MasterOrchestrator()

            except KeyboardInterrupt:
                print("\nStopping continuous mode...")
                break
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(60)
    else:
        # Single run
        if not args.fix_only:
            report = await orchestrator.run_all_checks()

            if args.json:
                print(json.dumps({
                    "timestamp": report.timestamp,
                    "passed": report.passed,
                    "failed": report.failed,
                    "checks": report.checks,
                    "issues": report.issues,
                    "warnings": report.warnings
                }, indent=2))
            else:
                print(report.summary())

        if not args.check_only:
            if orchestrator.report.failed > 0 or args.fix_only:
                print("\nDeploying fixes...")
                fixes = await orchestrator.deploy_fixes()

                if args.json:
                    print(json.dumps(fixes, indent=2))
                else:
                    print("\n" + "=" * 60)
                    print("  FIX DEPLOYMENT RESULTS")
                    print("=" * 60)
                    print(f"  Attempted: {fixes['fixes_attempted']}")
                    print(f"  Successful: {fixes['fixes_successful']}")
                    if fixes['actions_taken']:
                        print("\n  Actions taken:")
                        for action in fixes['actions_taken']:
                            print(f"    - {action}")
                    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
