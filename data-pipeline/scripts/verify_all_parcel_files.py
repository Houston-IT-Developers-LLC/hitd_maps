#!/usr/bin/env python3
"""
Verify ALL parcel files in valid_parcels.json are accessible on R2.
This ensures every single file we claim to have actually exists and loads.
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

CDN_BASE = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev/parcels"


def check_file(filename: str) -> dict:
    """Check if a PMTiles file exists and is accessible."""
    url = f"{CDN_BASE}/{filename}.pmtiles"
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            size_bytes = int(response.headers.get('Content-Length', 0))
            size_mb = size_bytes / 1024 / 1024
            return {
                "filename": filename,
                "exists": True,
                "size_mb": size_mb,
                "size_bytes": size_bytes,
                "url": url
            }
        else:
            return {
                "filename": filename,
                "exists": False,
                "status_code": response.status_code,
                "url": url
            }
    except requests.exceptions.Timeout:
        return {
            "filename": filename,
            "exists": False,
            "error": "timeout",
            "url": url
        }
    except Exception as e:
        return {
            "filename": filename,
            "exists": False,
            "error": str(e),
            "url": url
        }


def main():
    print("=" * 100)
    print("VERIFYING ALL PARCEL FILES IN valid_parcels.json")
    print("=" * 100)
    print()

    # Load valid_parcels.json
    with open("data/valid_parcels.json", "r") as f:
        valid_parcels = json.load(f)

    total_files = len(valid_parcels)
    print(f"Total files to verify: {total_files}")
    print()

    # Check all files in parallel (faster)
    print("Checking files (parallel)...")
    print("-" * 100)

    results = {
        "passed": [],
        "failed": [],
        "total_size_gb": 0
    }

    # Use thread pool for parallel checking
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(check_file, filename): filename
            for filename in valid_parcels
        }

        # Process results as they complete
        completed = 0
        for future in as_completed(future_to_file):
            result = future.result()
            completed += 1

            # Print progress
            if result["exists"]:
                size_mb = result["size_mb"]
                results["passed"].append(result)
                results["total_size_gb"] += size_mb / 1024
                status = f"✅ {size_mb:8.1f} MB"
            else:
                results["failed"].append(result)
                error = result.get("error", result.get("status_code", "unknown"))
                status = f"❌ {error}"

            # Print with progress counter
            filename = result["filename"]
            print(f"[{completed:3d}/{total_files:3d}] {filename:50s} {status}")

    # Sort results by state
    results["passed"].sort(key=lambda x: x["filename"])
    results["failed"].sort(key=lambda x: x["filename"])

    # Summary
    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total files verified: {total_files}")
    print(f"✅ Accessible: {len(results['passed'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"Success rate: {(len(results['passed'])/total_files*100):.1f}%")
    print(f"Total size: {results['total_size_gb']:.1f} GB")
    print()

    if results["failed"]:
        print("=" * 100)
        print("FAILED FILES")
        print("=" * 100)
        for result in results["failed"]:
            error = result.get("error", result.get("status_code", "unknown"))
            print(f"  ❌ {result['filename']:50s} - {error}")
            print(f"      URL: {result['url']}")
        print()

    # Analyze by state
    print("=" * 100)
    print("FILES BY STATE")
    print("=" * 100)

    by_state = {}
    for result in results["passed"]:
        # Extract state code from filename
        parts = result["filename"].split("_")
        if len(parts) >= 2:
            state = parts[1].upper()
            if state not in by_state:
                by_state[state] = {
                    "count": 0,
                    "total_mb": 0,
                    "files": []
                }
            by_state[state]["count"] += 1
            by_state[state]["total_mb"] += result["size_mb"]
            by_state[state]["files"].append(result["filename"])

    # Print state summary
    for state in sorted(by_state.keys()):
        info = by_state[state]
        total_gb = info["total_mb"] / 1024
        print(f"{state:3s}: {info['count']:3d} files, {total_gb:7.2f} GB")

    # Save detailed results
    output = {
        "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_files": total_files,
            "passed": len(results["passed"]),
            "failed": len(results["failed"]),
            "success_rate": round(len(results["passed"])/total_files*100, 1),
            "total_size_gb": round(results["total_size_gb"], 2)
        },
        "passed_files": [r["filename"] for r in results["passed"]],
        "failed_files": results["failed"],
        "by_state": {
            state: {
                "count": info["count"],
                "total_gb": round(info["total_mb"]/1024, 2)
            }
            for state, info in by_state.items()
        }
    }

    with open("/tmp/all_parcel_files_verification.json", "w") as f:
        json.dump(output, f, indent=2)

    print()
    print("✅ Detailed results saved to: /tmp/all_parcel_files_verification.json")

    if len(results["failed"]) == 0:
        print()
        print("🎉 ✅ ALL FILES VERIFIED AND ACCESSIBLE!")
    else:
        print()
        print(f"⚠️  {len(results['failed'])} files need attention")

    print()


if __name__ == "__main__":
    main()
