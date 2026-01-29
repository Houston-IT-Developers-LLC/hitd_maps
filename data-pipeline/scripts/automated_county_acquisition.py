#!/usr/bin/env python3
"""
Automated parallel county acquisition for 14 partial states.
Uses AI agents to find sources and download ~150 high-priority counties.
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_priority_counties():
    """Load the priority counties list."""
    with open("data/priority_counties_to_acquire.json", "r") as f:
        return json.load(f)


def generate_acquisition_tasks():
    """Generate list of all county acquisition tasks."""
    data = load_priority_counties()
    tasks = []

    for state_code, state_data in data["states"].items():
        state_name = state_data["name"]
        for county in state_data["counties_to_add"]:
            tasks.append({
                "state": state_code,
                "state_name": state_name,
                "county": county["name"],
                "city": county.get("city", ""),
                "population": county.get("population", 0),
                "source_id": f"{state_code.lower()}_{county['name'].lower().replace(' ', '_')}"
            })

    return tasks


def main():
    print("=" * 100)
    print("AUTOMATED COUNTY ACQUISITION - PARALLEL AI AGENTS")
    print("=" * 100)
    print()

    # Load tasks
    tasks = generate_acquisition_tasks()
    total = len(tasks)

    print(f"Total counties to acquire: {total}")
    print()

    # Group by state for better organization
    by_state = {}
    for task in tasks:
        state = task["state"]
        if state not in by_state:
            by_state[state] = []
        by_state[state].append(task)

    # Print summary
    print("COUNTIES BY STATE:")
    print("-" * 100)
    for state in sorted(by_state.keys()):
        counties = by_state[state]
        print(f"{state:3s}: {len(counties):2d} counties - {', '.join(c['county'] for c in counties[:3])}...")

    print()
    print("=" * 100)
    print("RECOMMENDED EXECUTION PLAN")
    print("=" * 100)
    print()

    print("PHASE 1: Find Sources (Use AI Agents)")
    print("-" * 100)
    print("Run in parallel batches of 10-20 counties at a time:")
    print()
    print("  cd data-pipeline")
    print("  python3 agent/source_finder.py --state IL --county 'Madison County'")
    print("  python3 agent/source_finder.py --state MI --county 'Genesee County'")
    print("  ... (repeat for all counties)")
    print()
    print("OR use the batch approach:")
    print()
    print("  python3 scripts/batch_find_sources.py --file data/priority_counties_to_acquire.json")
    print()

    print("PHASE 2: Download Data (Parallel)")
    print("-" * 100)
    print("After sources are found, download in parallel:")
    print()
    print("  python3 scripts/download_missing_states.py --source il_madison --workers 10")
    print("  python3 scripts/download_missing_states.py --source mi_genesee --workers 10")
    print()

    print("PHASE 3: Process & Upload (Automated Pipeline)")
    print("-" * 100)
    print("Process all downloaded files:")
    print()
    print("  make pipeline  # Processes all files in downloads/")
    print()

    print("=" * 100)
    print("QUICK START - TOP 10 HIGH-VALUE COUNTIES")
    print("=" * 100)
    print()

    # Sort by population, get top 10
    top_10 = sorted(tasks, key=lambda x: x["population"], reverse=True)[:10]

    print("Start with these 10 counties for quick wins:")
    print()
    for i, task in enumerate(top_10, 1):
        pop_k = task["population"] // 1000
        print(f"{i:2d}. {task['county']:20s} County, {task['state']:2s} - {pop_k:4d}K - {task['city']}")

    print()
    print("Commands to find sources for top 10:")
    print()
    for task in top_10:
        print(f"  python3 agent/source_finder.py --state {task['state']} --county '{task['county']} County'")

    print()
    print("=" * 100)
    print("ALTERNATIVE: USE GSD AGENTS")
    print("=" * 100)
    print()
    print("The GSD (Get Stuff Done) agent system can handle this entire workflow:")
    print()
    print("  1. Create a roadmap for county acquisition")
    print("  2. For each county: find source → download → process → upload")
    print("  3. Track progress and handle errors automatically")
    print()
    print("To use GSD:")
    print("  /gsd:create-roadmap  # Create phases for all 150 counties")
    print("  /gsd:execute-plan    # Execute automated acquisition")
    print()

    # Save task list for batch processing
    output_file = "/tmp/county_acquisition_tasks.json"
    with open(output_file, "w") as f:
        json.dump(tasks, f, indent=2)

    print()
    print(f"✅ Full task list saved to: {output_file}")
    print()

    print("=" * 100)
    print("NEXT STEP")
    print("=" * 100)
    print()
    print("Choose your approach:")
    print()
    print("  A) Manual (Full Control): Find sources one by one using source_finder.py")
    print("  B) Semi-Automated: Use batch_find_sources.py for parallel source finding")
    print("  C) Fully Automated: Use GSD agents to handle everything")
    print()
    print("Recommendation: Start with Option A for top 10, then move to B for the rest")
    print()


if __name__ == "__main__":
    main()
