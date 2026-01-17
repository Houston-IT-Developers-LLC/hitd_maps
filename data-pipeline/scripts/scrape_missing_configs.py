#!/usr/bin/env python3
"""
Scrape Missing Configs - Direct parallel scraping of all missing county configs
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

DATA_PIPELINE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = DATA_PIPELINE_DIR / "output"
GEOJSON_DIR = OUTPUT_DIR / "geojson"

# All configs confirmed missing from R2
MISSING_CONFIGS = [
    'MI_MARQUETTE', 'MI_WASHTENAW', 'GA_FULTON', 'GA_CHEROKEE', 'GA_GLYNN',
    'KY_FAYETTE', 'KY_HARDIN', 'SC_RICHLAND', 'AL_JEFFERSON', 'AL_MOBILE',
    'LA_EASTBATONROUGE', 'LA_JEFFERSON', 'MS_HINDS', 'MS_HARRISON', 'OK_OKLAHOMA',
    'MS_HINDS_V2', 'OR_STATEWIDE', 'MI_GRAND_TRAVERSE', 'GA_FORSYTH', 'AZ_MOHAVE',
    'WY_STATEWIDE', 'MS_STATEWIDE', 'MS_EAST_STATEWIDE', 'MS_WEST_STATEWIDE',
    'OK_OKLAHOMA_COUNTY', 'OR_CLACKAMAS', 'AZ_COCONINO', 'RI_CRANSTON', 'RI_PROVIDENCE',
    'GA_FULTON_V3', 'GA_DEKALB_V2', 'GA_CHEROKEE_V2', 'GA_GLYNN_V2', 'MS_STATEWIDE_2024',
    'MS_HARRISON_V2', 'OK_OKLAHOMA_V2', 'OK_TULSA_V2', 'AK_MATSU', 'AK_KENAI',
    'WY_STATEWIDE_V2', 'WY_LINCOLN', 'KS_SHAWNEE', 'MO_GREENE', 'MI_MACOMB_V2',
    'LA_ST_TAMMANY', 'OR_WASHINGTON', 'OR_MARION', 'SD_PENNINGTON', 'AL_BALDWIN',
    'MS_MADISON', 'LA_JEFFERSON_V3', 'LA_CALCASIEU', 'KY_WARREN', 'GA_MUSCOGEE',
    'GA_BIBB', 'GA_HENRY', 'GA_HOUSTON', 'GA_HALL', 'GA_DOUGLAS', 'GA_PAULDING',
    'GA_BARTOW', 'KY_DAVIESS', 'KY_MADISON', 'KY_CHRISTIAN', 'KY_PIKE', 'KY_PULASKI',
    'MO_ST_LOUIS_CITY', 'MO_ST_LOUIS_COUNTY', 'MO_BOONE', 'MO_JEFFERSON', 'KS_JOHNSON',
    'IL_KANE', 'IL_MCHENRY', 'IL_WINNEBAGO', 'IL_PEORIA', 'IL_CHAMPAIGN', 'IL_SANGAMON',
    'MI_GENESEE', 'MI_INGHAM', 'MI_KALAMAZOO', 'MI_SAGINAW', 'MI_MUSKEGON', 'MN_STATEWIDE',
    'LA_CADDO', 'LA_OUACHITA', 'OK_CANADIAN', 'OK_COMANCHE', 'SC_DORCHESTER', 'SC_LEXINGTON',
    'SC_YORK', 'RI_STATEWIDE', 'SD_LINCOLN', 'AL_SHELBY', 'AL_TUSCALOOSA', 'AK_ANCHORAGE',
    'AZ_COCHISE', 'AK_SKAGWAY', 'AK_FNSB_DIRECT', 'AK_DNR_DISPOSALS', 'AK_BLM_NATIVE',
    'AK_BLM_ANCSA', 'AK_BLM_STATE', 'AK_BLM_PRIVATE', 'NE_HALL', 'AZ_PINAL_V2', 'AZ_YUMA',
    'LA_EBR', 'MS_RANKIN', 'MO_STL_CITY', 'MO_STL_COUNTY', 'MO_MONTGOMERY',
    'OR_MULTNOMAH_V2', 'OR_LANE_V2', 'OR_MARION_V2', 'OK_CREEK', 'OK_OSAGE', 'OK_ROGERS',
    'OK_WAGONER', 'OK_NORMAN', 'OK_EDMOND', 'OK_BROKEN_ARROW', 'WY_CAMPBELL', 'WY_TETON',
    'WY_PARK', 'WY_SHERIDAN', 'WY_FREMONT', 'KY_FAYETTE_V2', 'KY_BOONE_V2', 'KY_CAMPBELL',
    'SD_GRANT', 'SD_HAMLIN', 'SD_CLARK', 'SD_DEUEL', 'SD_MOODY', 'SD_MINER'
]


def run_scrape(config_id: str) -> dict:
    """Run a single scrape."""
    start = datetime.now()
    result = {
        "config_id": config_id,
        "success": False,
        "message": ""
    }

    try:
        cmd = [
            sys.executable,
            str(DATA_PIPELINE_DIR / "scripts" / "export_county_parcels.py"),
            config_id,
            "-o", str(GEOJSON_DIR)
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            cwd=str(DATA_PIPELINE_DIR)
        )

        if proc.returncode == 0:
            result["success"] = True
            result["message"] = "OK"
        else:
            # Check for common errors
            err = proc.stderr[:300] if proc.stderr else ""
            if "not found" in err.lower() or "invalid" in err.lower():
                result["message"] = "Config invalid"
            elif "timeout" in err.lower():
                result["message"] = "Timeout"
            elif "403" in err or "401" in err:
                result["message"] = "Access denied"
            elif "404" in err:
                result["message"] = "API not found"
            else:
                result["message"] = err[:100] if err else "Unknown error"

    except subprocess.TimeoutExpired:
        result["message"] = "Timeout (1hr)"
    except Exception as e:
        result["message"] = str(e)[:100]

    result["duration"] = (datetime.now() - start).total_seconds()
    return result


def main():
    """Main entry point."""
    print("=" * 70)
    print("  SCRAPE MISSING CONFIGS - 96 Counties")
    print("=" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  Total configs: {len(MISSING_CONFIGS)}")
    print("=" * 70)

    # Ensure directory exists
    GEOJSON_DIR.mkdir(parents=True, exist_ok=True)

    # Skip configs that already have local files
    to_scrape = []
    for cfg in MISSING_CONFIGS:
        local_file = GEOJSON_DIR / f"parcels_{cfg.lower()}.geojson"
        if local_file.exists() and local_file.stat().st_size > 1000:
            print(f"  [skip] {cfg} - local file exists")
        else:
            to_scrape.append(cfg)

    print(f"\nConfigs to scrape: {len(to_scrape)}")
    print("=" * 70)

    if not to_scrape:
        print("Nothing to scrape!")
        return []

    # Scrape in parallel - use 20 workers for aggressive parallel scraping
    max_workers = 20
    results = []

    print(f"\nStarting {max_workers} parallel workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_scrape, cfg): cfg for cfg in to_scrape}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            try:
                result = future.result(timeout=3700)
                results.append(result)

                status = "OK" if result["success"] else "FAIL"
                duration = result.get("duration", 0)
                msg = result.get("message", "")[:40]
                print(f"[{completed:3}/{len(to_scrape)}] {status:4} {result['config_id']:25} ({duration:5.0f}s) {msg}")

            except Exception as e:
                print(f"[{completed:3}/{len(to_scrape)}] ERR  Unknown ({str(e)[:30]})")

    # Summary
    successful = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 70)
    print("  SCRAPE SUMMARY")
    print("=" * 70)
    print(f"  Total attempted: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(results) - successful}")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("=" * 70)

    # List new GeoJSON files
    new_files = list(GEOJSON_DIR.glob("parcels_*.geojson"))
    total_size = sum(f.stat().st_size for f in new_files) / 1024**3
    print(f"\n  GeoJSON files ready: {len(new_files)} ({total_size:.1f} GB)")

    return results


if __name__ == "__main__":
    main()
