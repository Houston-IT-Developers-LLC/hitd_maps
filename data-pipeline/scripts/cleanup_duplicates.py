#!/usr/bin/env python3
"""
DUPLICATE VERSION CLEANUP SCRIPT
Identifies duplicate PMTiles versions and provides cleanup recommendations.
Based on the consistency check results, helps clean up 29 duplicate base files.
"""

import subprocess
import json
import os
import re
from collections import defaultdict
from datetime import datetime

# R2 Configuration
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
AWS_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
AWS_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

VALID_PARCELS_JSON = "data/valid_parcels.json"

def get_r2_parcels():
    """Get list of all parcel files from R2 with metadata"""
    result = subprocess.run([
        'aws', 's3', 'ls', 's3://gspot-tiles/parcels/',
        '--endpoint-url', R2_ENDPOINT
    ], capture_output=True, text=True, env={
        **os.environ,
        'AWS_ACCESS_KEY_ID': AWS_ACCESS_KEY,
        'AWS_SECRET_ACCESS_KEY': AWS_SECRET_KEY
    })

    parcels = {}
    for line in result.stdout.strip().split('\n'):
        if '.pmtiles' in line:
            parts = line.split()
            if len(parts) >= 4:
                filename = parts[3].replace('.pmtiles', '')
                size_bytes = int(parts[2])
                size_mb = size_bytes / (1024*1024)
                date_str = f"{parts[0]} {parts[1]}"
                parcels[filename] = {
                    'size_mb': round(size_mb, 2),
                    'size_bytes': size_bytes,
                    'date': date_str
                }
    return parcels

def normalize_filename(filename):
    """Remove version suffixes like _v2, _v3, _wgs84"""
    filename = re.sub(r'_v\d+$', '', filename)
    filename = re.sub(r'_wgs84$', '', filename)
    filename = re.sub(r'_recent$', '', filename)
    filename = re.sub(r'_new$', '', filename)
    return filename

def find_duplicates(parcels):
    """Find files with multiple versions"""
    groups = defaultdict(list)
    for name in parcels:
        normalized = normalize_filename(name)
        groups[normalized].append(name)

    # Return groups with >1 file
    return {k: v for k, v in groups.items() if len(v) > 1}

def recommend_version(versions, parcels_metadata):
    """Recommend which version to keep based on size and naming"""
    # Rules:
    # 1. If one has "_new" suffix, prefer it
    # 2. If one has "_recent" suffix, prefer it
    # 3. Ignore _wgs84 versions if they're much smaller (likely corrupted)
    # 4. Otherwise, prefer larger file (more complete data)
    # 5. If sizes similar, prefer higher version number

    version_data = []
    for v in versions:
        meta = parcels_metadata[v]
        version_data.append({
            'name': v,
            'size_mb': meta['size_mb'],
            'size_bytes': meta['size_bytes'],
            'date': meta['date'],
            'is_new': '_new' in v,
            'is_recent': '_recent' in v,
            'is_wgs84': '_wgs84' in v,
            'version_num': int(re.search(r'_v(\d+)$', v).group(1)) if re.search(r'_v(\d+)$', v) else 0
        })

    # Sort by preference
    def score_version(v):
        score = 0
        if v['is_new']: score += 1000
        if v['is_recent']: score += 900
        if v['is_wgs84'] and v['size_mb'] < 5:
            score -= 1000  # Likely corrupted, deprioritize
        score += v['size_bytes'] / (1024*1024)  # Add size in MB
        score += v['version_num'] * 10
        return score

    version_data.sort(key=score_version, reverse=True)

    recommended = version_data[0]['name']
    to_remove = [v['name'] for v in version_data[1:]]

    return recommended, to_remove

def load_valid_parcels():
    """Load valid_parcels.json"""
    if not os.path.exists(VALID_PARCELS_JSON):
        return []
    with open(VALID_PARCELS_JSON, 'r') as f:
        return json.load(f)

def save_valid_parcels(parcels):
    """Save valid_parcels.json"""
    parcels.sort()
    with open(VALID_PARCELS_JSON, 'w') as f:
        json.dump(parcels, f, indent=2)

def main():
    print("="*70)
    print("DUPLICATE VERSION CLEANUP")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Get R2 parcels
    print("Fetching parcel list from R2...")
    r2_parcels = get_r2_parcels()
    print(f"Found {len(r2_parcels)} files in R2\n")

    # Find duplicates
    duplicates = find_duplicates(r2_parcels.keys())
    print(f"Found {len(duplicates)} base files with multiple versions:\n")

    # Analyze each duplicate group
    cleanup_plan = []
    total_to_remove = 0
    total_space_saved = 0

    for base, versions in sorted(duplicates.items()):
        print(f"\n{base}:")
        for v in sorted(versions):
            size = r2_parcels[v]['size_mb']
            date = r2_parcels[v]['date']
            print(f"  - {v} ({size} MB, {date})")

        # Get recommendation
        keep, remove = recommend_version(versions, r2_parcels)

        print(f"  ✓ KEEP: {keep} ({r2_parcels[keep]['size_mb']} MB)")
        for r in remove:
            size_mb = r2_parcels[r]['size_mb']
            print(f"  ✗ REMOVE: {r} ({size_mb} MB)")
            total_space_saved += size_mb

        total_to_remove += len(remove)
        cleanup_plan.append({
            'base': base,
            'keep': keep,
            'remove': remove
        })

    # Summary
    print("\n" + "="*70)
    print("CLEANUP SUMMARY")
    print("="*70)
    print(f"Duplicate groups: {len(duplicates)}")
    print(f"Files to remove: {total_to_remove}")
    print(f"Space to save: ~{total_space_saved:.1f} MB ({total_space_saved/1024:.2f} GB)")

    # Generate cleanup commands
    print("\n" + "="*70)
    print("CLEANUP COMMANDS")
    print("="*70)
    print("\n# Remove old versions from R2:")
    print("export AWS_ACCESS_KEY_ID=ecd653afe3300fdc045b9980df0dbb14")
    print("export AWS_SECRET_ACCESS_KEY=c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35")
    print()

    for plan in cleanup_plan:
        for file in plan['remove']:
            print(f"aws s3 rm s3://gspot-tiles/parcels/{file}.pmtiles --endpoint-url {R2_ENDPOINT}")

    # Update valid_parcels.json
    print("\n# Updating valid_parcels.json...")
    valid_parcels = load_valid_parcels()

    removed_count = 0
    added_count = 0

    for plan in cleanup_plan:
        keep = plan['keep']
        remove_list = plan['remove']

        # Remove old versions
        for r in remove_list:
            if r in valid_parcels:
                valid_parcels.remove(r)
                removed_count += 1

        # Ensure keep version is in list
        if keep not in valid_parcels:
            valid_parcels.append(keep)
            added_count += 1

    save_valid_parcels(valid_parcels)

    print(f"\n✓ Updated valid_parcels.json:")
    print(f"  - Removed {removed_count} old versions")
    print(f"  - Added {added_count} recommended versions")
    print(f"  - Total: {len(valid_parcels)} files")

    # Save detailed cleanup plan
    output_path = '/tmp/duplicate_cleanup_plan.json'
    with open(output_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'duplicate_groups': len(duplicates),
                'files_to_remove': total_to_remove,
                'space_to_save_mb': round(total_space_saved, 2),
                'space_to_save_gb': round(total_space_saved/1024, 3)
            },
            'cleanup_plan': cleanup_plan
        }, f, indent=2)

    print(f"\nDetailed plan saved to: {output_path}")

    # Ask for confirmation
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("\n1. Review the cleanup commands above")
    print("2. Execute the aws s3 rm commands to remove old versions")
    print("3. valid_parcels.json has been updated")
    print("\nNote: You can run the commands in the output above to clean up R2.")

if __name__ == '__main__':
    main()
