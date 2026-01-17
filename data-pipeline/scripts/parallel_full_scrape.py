#!/usr/bin/env python3
"""
Parallel Full Scrape - Deploy multiple agents to scrape all states simultaneously.

This script maximizes throughput by running multiple scraping jobs in parallel,
using all available CPU cores on the Exxact server (48 cores, 512GB RAM).
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))

DATA_PIPELINE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = DATA_PIPELINE_DIR / "scripts"
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"

# All statewide configs to scrape (prioritized by size/importance)
PRIORITY_STATES = [
    # Large states first (run these early as they take longest)
    "TX_STATEWIDE",
    "CA_STATEWIDE",
    "NY_STATEWIDE_V2",
    "FL_STATEWIDE",
    "PA_STATEWIDE",
    "OH_STATEWIDE",
    "IL_STATEWIDE",  # Will use county APIs
    "MI_STATEWIDE",  # Will use county APIs
    "GA_STATEWIDE",  # Will use county APIs

    # Medium states
    "NC_STATEWIDE",
    "NJ_STATEWIDE_V2",
    "VA_STATEWIDE_V2",
    "WA_STATEWIDE_V2",
    "MA_STATEWIDE",
    "MD_STATEWIDE",
    "WI_STATEWIDE_V2",
    "CO_STATEWIDE",
    "MN_STATEWIDE",
    "MO_STATEWIDE",  # Will use county APIs
    "IN_STATEWIDE",
    "TN_STATEWIDE",
    "OR_STATEWIDE",
    "SC_STATEWIDE",  # Will use county APIs
    "LA_STATEWIDE",  # Will use county APIs
    "KY_STATEWIDE",  # Will use county APIs
    "OK_STATEWIDE",  # Will use county APIs
    "KS_STATEWIDE",  # Will use county APIs

    # Smaller states
    "CT_STATEWIDE_V2",
    "IA_STATEWIDE",
    "UT_STATEWIDE",
    "NV_STATEWIDE",
    "NE_STATEWIDE",
    "NM_STATEWIDE_V2",
    "WV_STATEWIDE_V2",
    "ID_STATEWIDE",
    "HI_STATEWIDE",
    "ME_STATEWIDE",
    "NH_STATEWIDE",
    "RI_STATEWIDE",
    "MT_STATEWIDE_V2",
    "DE_STATEWIDE",
    "ND_STATEWIDE",
    "VT_STATEWIDE_V2",
    "WY_STATEWIDE_V2",
    "AR_STATEWIDE",
    "MS_STATEWIDE_2024",
]

# County-level APIs for states without statewide data
COUNTY_SCRAPES = {
    "IL": ["cook", "dupage", "lake", "will", "kane", "mchenry"],
    "MI": ["wayne", "oakland", "macomb", "kent", "genesee", "washtenaw", "ottawa", "ingham", "kalamazoo"],
    "GA": ["fulton", "gwinnett", "cobb", "dekalb", "chatham", "muscogee", "richmond", "bibb", "clarke"],
    "MO": ["st_louis", "jackson", "st_charles", "clay", "greene", "boone", "kansas_city"],
    "SC": ["greenville", "richland", "charleston", "horry", "spartanburg", "lexington"],
    "LA": ["orleans", "jefferson", "eastbatonrouge", "caddo", "calcasieu", "ouachita", "rapides"],
    "KY": ["jefferson", "fayette", "kenton", "boone", "warren", "hardin", "daviess"],
    "OK": ["oklahoma", "tulsa", "cleveland", "comanche", "canadian", "rogers"],
    "KS": ["johnson", "sedgwick", "shawnee", "wyandotte", "douglas", "leavenworth"],
}


def run_scrape_subprocess(config_id: str) -> dict:
    """Run a scrape as a subprocess."""
    start = datetime.now()
    print(f"[{start.strftime('%H:%M:%S')}] Starting scrape: {config_id}")

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "export_county_parcels.py"),
                config_id,
                "-o", str(OUTPUT_DIR / "geojson")
            ],
            capture_output=True,
            text=True,
            timeout=7200,  # 2 hour timeout per state
            cwd=DATA_PIPELINE_DIR
        )

        duration = (datetime.now() - start).total_seconds()
        success = result.returncode == 0

        status = "SUCCESS" if success else "FAILED"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {status}: {config_id} ({duration:.0f}s)")

        if not success:
            print(f"  Error: {result.stderr[:200] if result.stderr else 'No error output'}")

        return {
            "config_id": config_id,
            "success": success,
            "duration": duration,
            "error": result.stderr[:500] if not success else None
        }

    except subprocess.TimeoutExpired:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] TIMEOUT: {config_id}")
        return {
            "config_id": config_id,
            "success": False,
            "duration": 7200,
            "error": "Timeout after 2 hours"
        }
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {config_id} - {e}")
        return {
            "config_id": config_id,
            "success": False,
            "duration": 0,
            "error": str(e)
        }


async def run_pipeline_after_scrapes():
    """Run the full pipeline after scraping completes."""
    print("\n" + "=" * 60)
    print("Running full pipeline (reproject → tile → upload)...")
    print("=" * 60)

    result = subprocess.run(
        [
            sys.executable,
            str(DATA_PIPELINE_DIR / "agent" / "data_agent.py"),
            "--pipeline",
            "--workers", "8"
        ],
        capture_output=True,
        text=True,
        timeout=14400,  # 4 hour timeout for pipeline
        cwd=DATA_PIPELINE_DIR
    )

    print(result.stdout)
    if result.returncode != 0:
        print(f"Pipeline error: {result.stderr}")

    return result.returncode == 0


def main():
    """Main entry point for parallel scraping."""
    print("=" * 60)
    print("  HITD Maps Parallel Full Scrape")
    print("=" * 60)
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  CPU Cores: {multiprocessing.cpu_count()}")
    print(f"  Max parallel jobs: 12")
    print("=" * 60)

    # Combine all scrape targets
    all_scrapes = list(PRIORITY_STATES)

    # Add county-level scrapes
    for state, counties in COUNTY_SCRAPES.items():
        for county in counties:
            config_id = f"{state}_{county}".upper()
            if config_id not in all_scrapes:
                all_scrapes.append(config_id)

    print(f"\nTotal scrape jobs: {len(all_scrapes)}")
    print(f"Statewide: {len(PRIORITY_STATES)}")
    print(f"County-level: {len(all_scrapes) - len(PRIORITY_STATES)}")

    # Run scrapes in parallel using ProcessPoolExecutor
    # Use 12 workers to balance between parallelism and not overwhelming APIs
    max_workers = 12

    print(f"\nStarting {max_workers} parallel workers...")
    print("-" * 60)

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_scrape_subprocess, config_id): config_id
                   for config_id in all_scrapes}

        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                config_id = futures[future]
                print(f"Exception for {config_id}: {e}")
                results.append({
                    "config_id": config_id,
                    "success": False,
                    "error": str(e)
                })

    # Summary
    print("\n" + "=" * 60)
    print("  SCRAPE SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    print(f"  Total jobs:    {len(results)}")
    print(f"  Successful:    {len(successful)}")
    print(f"  Failed:        {len(failed)}")

    if failed:
        print("\n  Failed jobs:")
        for r in failed[:20]:  # Show first 20 failures
            print(f"    - {r['config_id']}: {r.get('error', 'Unknown')[:60]}")
        if len(failed) > 20:
            print(f"    ... and {len(failed) - 20} more")

    total_duration = sum(r.get("duration", 0) for r in results)
    print(f"\n  Total scrape time: {total_duration/3600:.1f} hours (parallel)")

    # Run pipeline if we had any successful scrapes
    if successful:
        print("\n" + "=" * 60)
        print("  Running full pipeline...")
        print("=" * 60)

        asyncio.run(run_pipeline_after_scrapes())

    print("\n" + "=" * 60)
    print(f"  Completed: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
