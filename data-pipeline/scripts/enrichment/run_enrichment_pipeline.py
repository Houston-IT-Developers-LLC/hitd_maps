#!/usr/bin/env python3
"""
Master Enrichment Pipeline

Orchestrates downloading, processing, and uploading of all enrichment
data sources for the GSpot Outdoors property data.

Usage:
    # Download all enrichment data for a state
    python3 run_enrichment_pipeline.py --state TX

    # Download specific sources only
    python3 run_enrichment_pipeline.py --state TX --sources pad_us,nwi,nhd

    # Download all states for a specific source
    python3 run_enrichment_pipeline.py --all-states --sources pad_us

    # Full pipeline with PMTiles and R2 upload
    python3 run_enrichment_pipeline.py --state TX --pmtiles --upload --cleanup

Date Added: 2026-01-13
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_PIPELINE_DIR = SCRIPT_DIR.parent.parent
CONFIG_FILE = DATA_PIPELINE_DIR / "config" / "enrichment_sources.json"
LOG_DIR = DATA_PIPELINE_DIR / "logs" / "enrichment"

# All US states
ALL_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

# Source scripts mapping
SOURCE_SCRIPTS = {
    "pad_us": {
        "script": "download_pad_us.py",
        "priority": 1,
        "description": "Protected Areas Database (public lands)",
        "supports_state": True
    },
    "nwi": {
        "script": "download_nwi.py",
        "priority": 2,
        "description": "National Wetlands Inventory",
        "supports_state": True
    },
    "nhd": {
        "script": "download_nhd.py",
        "priority": 3,
        "description": "National Hydrography Dataset",
        "supports_state": True
    },
    "state_wma": {
        "script": "download_state_wma.py",
        "priority": 4,
        "description": "State Wildlife Management Areas",
        "supports_state": True
    },
    "nlcd": {
        "script": "download_nlcd.py",
        "priority": 5,
        "description": "National Land Cover Database",
        "supports_state": False,
        "supports_bbox": True
    },
    "ssurgo": {
        "script": "download_ssurgo.py",
        "priority": 6,
        "description": "SSURGO Soil Survey",
        "supports_state": False,
        "supports_bbox": True
    },
    "federal_lands": {
        "script": "download_federal_lands.py",
        "priority": 7,
        "description": "BLM/USFS Federal Lands",
        "supports_state": True
    },
    "fema_flood": {
        "script": "download_fema_flood.py",
        "priority": 8,
        "description": "FEMA Flood Zones",
        "supports_state": True,
        "supports_bbox": True
    }
}


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def ensure_directories():
    """Create necessary directories"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    """Load enrichment sources configuration"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return None


def run_download_script(source_key, state=None, bbox=None, pmtiles=False, upload=False, cleanup=False):
    """
    Run a download script for a specific source

    Args:
        source_key: Key from SOURCE_SCRIPTS
        state: State abbreviation
        bbox: Bounding box for bbox-based sources
        pmtiles: Generate PMTiles
        upload: Upload to R2
        cleanup: Remove local files after upload

    Returns:
        (success, output, error)
    """
    source_info = SOURCE_SCRIPTS.get(source_key)
    if not source_info:
        return False, "", f"Unknown source: {source_key}"

    script_path = SCRIPT_DIR / source_info["script"]
    if not script_path.exists():
        return False, "", f"Script not found: {script_path}"

    # Build command
    cmd = ["python3", str(script_path)]

    if state and source_info.get("supports_state"):
        cmd.extend(["--state", state])
    elif bbox and source_info.get("supports_bbox"):
        cmd.extend(["--bbox", bbox])

    if pmtiles:
        cmd.append("--pmtiles")
    if upload:
        cmd.append("--upload")
    if cleanup:
        cmd.append("--cleanup")

    log(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200,  # 2 hour timeout
            cwd=SCRIPT_DIR
        )

        if result.returncode == 0:
            return True, result.stdout, ""
        else:
            return False, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return False, "", "Script timed out"
    except Exception as e:
        return False, "", str(e)


def run_pipeline(states, sources, pmtiles=False, upload=False, cleanup=False, parallel=1):
    """
    Run the enrichment pipeline

    Args:
        states: List of state abbreviations
        sources: List of source keys to process
        pmtiles: Generate PMTiles
        upload: Upload to R2
        cleanup: Remove local files after upload
        parallel: Number of parallel jobs
    """
    log("=" * 70)
    log("ENRICHMENT PIPELINE")
    log("=" * 70)
    log(f"States: {', '.join(states)}")
    log(f"Sources: {', '.join(sources)}")
    log(f"PMTiles: {pmtiles}")
    log(f"Upload: {upload}")
    log(f"Cleanup: {cleanup}")
    log(f"Parallel jobs: {parallel}")
    log("=" * 70)

    # Sort sources by priority
    sorted_sources = sorted(
        sources,
        key=lambda s: SOURCE_SCRIPTS.get(s, {}).get("priority", 99)
    )

    results = {
        "success": [],
        "failed": [],
        "skipped": []
    }

    # Process each source
    for source_key in sorted_sources:
        source_info = SOURCE_SCRIPTS.get(source_key, {})

        log("")
        log(f"{'='*70}")
        log(f"Processing: {source_key} (Priority {source_info.get('priority', '?')})")
        log(f"  {source_info.get('description', '')}")
        log(f"{'='*70}")

        if source_info.get("supports_state"):
            # Process each state
            for state in states:
                log(f"\n  State: {state}")
                success, output, error = run_download_script(
                    source_key,
                    state=state,
                    pmtiles=pmtiles,
                    upload=upload,
                    cleanup=cleanup
                )

                if success:
                    results["success"].append(f"{source_key}_{state}")
                    log(f"    Success")
                else:
                    results["failed"].append(f"{source_key}_{state}")
                    log(f"    Failed: {error}", "ERROR")

        elif source_info.get("supports_bbox"):
            # These sources need bbox - skip for now
            log(f"  Skipping {source_key} - requires --bbox parameter")
            results["skipped"].append(source_key)
        else:
            log(f"  Skipping {source_key} - not state-based")
            results["skipped"].append(source_key)

    # Summary
    log("")
    log("=" * 70)
    log("PIPELINE COMPLETE")
    log("=" * 70)
    log(f"Success: {len(results['success'])}")
    log(f"Failed: {len(results['failed'])}")
    log(f"Skipped: {len(results['skipped'])}")

    if results['failed']:
        log("\nFailed items:")
        for item in results['failed']:
            log(f"  - {item}")

    return results


def update_check_dates():
    """Update the next check dates in config file"""
    if not CONFIG_FILE.exists():
        log("Config file not found", "WARNING")
        return

    with open(CONFIG_FILE) as f:
        config = json.load(f)

    # Update last_updated
    config["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    # Save
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

    log(f"Updated config file: {CONFIG_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description="Master Enrichment Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all enrichment data for Texas
  python3 run_enrichment_pipeline.py --state TX

  # Download specific sources
  python3 run_enrichment_pipeline.py --state TX,CO --sources pad_us,nwi

  # Download PAD-US for all states
  python3 run_enrichment_pipeline.py --all-states --sources pad_us

  # Full pipeline with upload
  python3 run_enrichment_pipeline.py --state TX --all-sources --pmtiles --upload --cleanup

Available Sources (by priority):
  1. pad_us      - Protected Areas Database (public lands)
  2. nwi         - National Wetlands Inventory
  3. nhd         - National Hydrography Dataset
  4. state_wma   - State Wildlife Management Areas
  5. nlcd        - National Land Cover Database (bbox only)
  6. ssurgo      - SSURGO Soil Survey (bbox only)
  7. federal_lands - BLM/USFS Federal Lands
  8. fema_flood  - FEMA Flood Zones
        """
    )

    parser.add_argument("--state", "-s", help="State abbreviation(s), comma-separated")
    parser.add_argument("--all-states", action="store_true", help="Process all US states")
    parser.add_argument("--sources", help="Source(s) to process, comma-separated")
    parser.add_argument("--all-sources", action="store_true", help="Process all sources")
    parser.add_argument("--pmtiles", action="store_true", help="Generate PMTiles")
    parser.add_argument("--upload", action="store_true", help="Upload to Cloudflare R2")
    parser.add_argument("--cleanup", action="store_true", help="Remove local files after upload")
    parser.add_argument("--parallel", type=int, default=1, help="Number of parallel jobs")
    parser.add_argument("--list-sources", action="store_true", help="List available sources")
    parser.add_argument("--update-config", action="store_true", help="Update config check dates")

    args = parser.parse_args()

    ensure_directories()

    if args.list_sources:
        log("Available Enrichment Sources:")
        for key, info in sorted(SOURCE_SCRIPTS.items(), key=lambda x: x[1].get("priority", 99)):
            state_support = "state" if info.get("supports_state") else "bbox"
            log(f"  {info.get('priority', '?')}. {key}: {info.get('description')} [{state_support}]")
        return

    if args.update_config:
        update_check_dates()
        return

    # Determine states
    states = []
    if args.state:
        states = [s.strip().upper() for s in args.state.split(",")]
    elif args.all_states:
        states = ALL_STATES
    else:
        log("Please specify --state or --all-states", "ERROR")
        parser.print_help()
        return

    # Determine sources
    sources = []
    if args.sources:
        sources = [s.strip().lower() for s in args.sources.split(",")]
        # Validate sources
        invalid = [s for s in sources if s not in SOURCE_SCRIPTS]
        if invalid:
            log(f"Invalid sources: {invalid}", "ERROR")
            log(f"Available: {list(SOURCE_SCRIPTS.keys())}")
            return
    elif args.all_sources:
        sources = list(SOURCE_SCRIPTS.keys())
    else:
        # Default to top 3 priority sources
        sources = ["pad_us", "nwi", "nhd"]
        log(f"Using default sources: {sources}")

    # Run pipeline
    results = run_pipeline(
        states=states,
        sources=sources,
        pmtiles=args.pmtiles,
        upload=args.upload,
        cleanup=args.cleanup,
        parallel=args.parallel
    )

    # Exit with error code if any failures
    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
