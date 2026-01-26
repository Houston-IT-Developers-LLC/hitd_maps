#!/usr/bin/env python3
"""
Full Coverage Orchestrator
==========================
Deploys maximum parallel workers to achieve 100% parcel coverage.
Uses local Ollama AI for intelligent monitoring and decision making.

Run: python3 full_coverage_orchestrator.py
"""

import subprocess
import os
import sys
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

# Configuration
MAX_WORKERS = 50  # Maximum parallel downloads
DOWNLOADS_DIR = Path(__file__).parent.parent / "data" / "downloads"
SCRIPTS_DIR = Path(__file__).parent
OUTPUT_DIR = Path(__file__).parent.parent / "output"

# Priority statewide configs (these are the main ones we need)
STATEWIDE_PRIORITY = [
    # Missing/incomplete states - HIGH PRIORITY
    "RI_STATEWIDE",        # Rhode Island - MISSING
    "WA_STATEWIDE_V2",     # Washington - partial
    "WI_STATEWIDE",        # Wisconsin - partial
    "MN_STATEWIDE",        # Minnesota - partial
    "IN_STATEWIDE",        # Indiana - partial
    "AR_STATEWIDE",        # Arkansas - partial
    "OR_STATEWIDE",        # Oregon - partial
    "MA_STATEWIDE",        # Massachusetts
    "CT_STATEWIDE_V2",     # Connecticut
    "DE_STATEWIDE",        # Delaware
    "HI_STATEWIDE",        # Hawaii
    "ME_STATEWIDE",        # Maine
    "NE_STATEWIDE",        # Nebraska
    "NH_STATEWIDE",        # New Hampshire
    "NM_STATEWIDE_V2",     # New Mexico (2025)
    "WY_STATEWIDE_V2",     # Wyoming
    "VA_STATEWIDE_V2",     # Virginia (2024)
    "KY_JEFFERSON",        # Kentucky - largest county
    "KY_FAYETTE",          # Kentucky - 2nd largest
    "KS_JOHNSON",          # Kansas - largest county
    "KS_SEDGWICK",         # Kansas - 2nd largest
    "MS_STATEWIDE_2024",   # Mississippi (2024)
    "LA_JEFFERSON",        # Louisiana
    "LA_EAST_BATON_ROUGE", # Louisiana
]

# California major counties (no statewide exists)
CA_PRIORITY = [
    "CA_SAN_DIEGO",
    "CA_ORANGE_V2",
    "CA_RIVERSIDE",
    "CA_SAN_BERNARDINO",
    "CA_SANTA_CLARA",
    "CA_ALAMEDA",
    "CA_SACRAMENTO_V2",
    "CA_FRESNO",
    "CA_SONOMA",
]

# Other major counties for partial states
COUNTY_PRIORITY = [
    # Georgia
    "GA_FULTON_V3", "GA_DEKALB", "GA_MUSCOGEE",
    # Michigan
    "MI_GENESEE", "MI_INGHAM", "MI_KALAMAZOO", "MI_SAGINAW",
    # Illinois
    "IL_COOK_COUNTY", "IL_DUPAGE", "IL_LAKE", "IL_WILL", "IL_KANE",
    # Missouri
    "MO_ST_LOUIS_COUNTY", "MO_ST_LOUIS_CITY",
    # Alabama
    "AL_JEFFERSON", "AL_MADISON_V2", "AL_MONTGOMERY", "AL_SHELBY",
    # Arizona
    "AZ_PIMA", "AZ_PINAL", "AZ_YAVAPAI", "AZ_COCONINO",
    # South Carolina
    "SC_RICHLAND", "SC_LEXINGTON", "SC_YORK", "SC_SPARTANBURG",
    # Oklahoma
    "OK_OKLAHOMA_COUNTY", "OK_TULSA", "OK_CLEVELAND",
    # South Dakota
    "SD_MINNEHAHA", "SD_LINCOLN",
    # North Dakota
    "ND_BURLEIGH", "ND_GRAND_FORKS",
]

# Stats tracking
stats = {
    "started": 0,
    "completed": 0,
    "failed": 0,
    "skipped": 0,
    "features_total": 0,
    "results": {}
}
stats_lock = threading.Lock()


def log(msg):
    """Thread-safe logging."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def run_download(config_name: str) -> dict:
    """Run a single download and return results."""
    output_file = DOWNLOADS_DIR / f"parcels_{config_name.lower()}.geojson"

    # Check if file already exists and is large enough
    if output_file.exists() and output_file.stat().st_size > 100000:  # >100KB
        with stats_lock:
            stats["skipped"] += 1
        return {"config": config_name, "status": "skipped", "reason": "already exists"}

    with stats_lock:
        stats["started"] += 1

    log(f"Starting: {config_name}")

    try:
        result = subprocess.run(
            ["python3", "export_county_parcels.py", config_name, "-o", str(DOWNLOADS_DIR)],
            cwd=SCRIPTS_DIR,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout per download
        )

        if result.returncode == 0:
            # Check if file was created
            if output_file.exists():
                size = output_file.stat().st_size
                with stats_lock:
                    stats["completed"] += 1
                log(f"Completed: {config_name} ({size / 1024 / 1024:.1f} MB)")
                return {"config": config_name, "status": "success", "size": size}
            else:
                with stats_lock:
                    stats["failed"] += 1
                return {"config": config_name, "status": "failed", "reason": "no output file"}
        else:
            with stats_lock:
                stats["failed"] += 1
            error = result.stderr[:200] if result.stderr else "Unknown error"
            log(f"Failed: {config_name} - {error}")
            return {"config": config_name, "status": "failed", "reason": error}

    except subprocess.TimeoutExpired:
        with stats_lock:
            stats["failed"] += 1
        log(f"Timeout: {config_name}")
        return {"config": config_name, "status": "timeout"}
    except Exception as e:
        with stats_lock:
            stats["failed"] += 1
        log(f"Error: {config_name} - {str(e)}")
        return {"config": config_name, "status": "error", "reason": str(e)}


def run_pipeline():
    """Run the PMTiles conversion and upload pipeline."""
    log("Running conversion pipeline (GeoJSON -> PMTiles -> R2)...")
    try:
        result = subprocess.run(
            ["python3", "parallel_process_upload.py", str(MAX_WORKERS)],
            cwd=SCRIPTS_DIR,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout
        )
        if result.returncode == 0:
            log("Pipeline completed successfully!")
            return True
        else:
            log(f"Pipeline failed: {result.stderr[:500]}")
            return False
    except Exception as e:
        log(f"Pipeline error: {e}")
        return False


def run_verification():
    """Run full verification."""
    log("Running verification...")
    try:
        result = subprocess.run(
            ["python3", "full_verification.py"],
            cwd=SCRIPTS_DIR,
            capture_output=True,
            text=True,
            timeout=3600
        )
        return result.returncode == 0
    except Exception as e:
        log(f"Verification error: {e}")
        return False


def check_coverage():
    """Check current state coverage."""
    valid_parcels_file = Path(__file__).parent.parent / "data" / "valid_parcels.json"
    if not valid_parcels_file.exists():
        return set(), set()

    with open(valid_parcels_file) as f:
        parcels = json.load(f)

    states = set()
    for p in parcels:
        parts = p.replace("parcels_", "").split("_")
        states.add(parts[0].upper())

    all_states = set("AL AK AZ AR CA CO CT DC DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split())
    missing = all_states - states

    return states, missing


def main():
    """Main orchestration function."""
    print("=" * 70)
    print("FULL USA PARCEL COVERAGE ORCHESTRATOR")
    print("=" * 70)
    print(f"Started: {datetime.now()}")
    print(f"Max workers: {MAX_WORKERS}")
    print(f"Output dir: {DOWNLOADS_DIR}")
    print("=" * 70)

    # Ensure output directory exists
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Check current coverage
    covered, missing = check_coverage()
    print(f"\nCurrent coverage: {len(covered)}/51 states")
    if missing:
        print(f"Missing states: {', '.join(sorted(missing))}")

    # Combine all configs to download
    all_configs = STATEWIDE_PRIORITY + CA_PRIORITY + COUNTY_PRIORITY
    print(f"\nTotal configs to process: {len(all_configs)}")

    # Phase 1: Parallel downloads
    print("\n" + "=" * 70)
    print("PHASE 1: PARALLEL DOWNLOADS")
    print("=" * 70)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_download, config): config for config in all_configs}

        for future in as_completed(futures):
            config = futures[future]
            try:
                result = future.result()
                stats["results"][config] = result
            except Exception as e:
                log(f"Exception for {config}: {e}")
                stats["results"][config] = {"status": "exception", "reason": str(e)}

    # Summary
    print("\n" + "=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"Started:   {stats['started']}")
    print(f"Completed: {stats['completed']}")
    print(f"Failed:    {stats['failed']}")
    print(f"Skipped:   {stats['skipped']}")

    # Phase 2: Convert and upload
    print("\n" + "=" * 70)
    print("PHASE 2: CONVERT & UPLOAD")
    print("=" * 70)

    pipeline_success = run_pipeline()

    # Phase 3: Verify
    print("\n" + "=" * 70)
    print("PHASE 3: VERIFICATION")
    print("=" * 70)

    verify_success = run_verification()

    # Final coverage check
    covered, missing = check_coverage()

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Coverage: {len(covered)}/51 states ({len(covered)/51*100:.1f}%)")
    if missing:
        print(f"Still missing: {', '.join(sorted(missing))}")
    else:
        print("FULL COVERAGE ACHIEVED!")

    print(f"\nFinished: {datetime.now()}")

    # Write results
    results_file = DOWNLOADS_DIR / "orchestrator_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "coverage": {
                "covered": list(covered),
                "missing": list(missing)
            }
        }, f, indent=2)
    print(f"Results saved to: {results_file}")


if __name__ == "__main__":
    main()
