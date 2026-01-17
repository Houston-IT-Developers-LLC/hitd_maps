#!/usr/bin/env python3
"""
Verify R2 uploads and clean up duplicates.
Keeps only the most recent/complete version of each county.
"""

import boto3
from botocore.config import Config
from datetime import datetime
import sys

sys.stdout.reconfigure(line_buffering=True)

R2_ENDPOINT = 'https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com'
R2_ACCESS_KEY = 'ecd653afe3300fdc045b9980df0dbb14'
R2_SECRET_KEY = 'c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35'
R2_BUCKET = 'gspot-tiles'


def get_r2_client():
    return boto3.client('s3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version='s3v4'))


def list_all_parcels():
    """List all parcel files in R2."""
    client = get_r2_client()
    paginator = client.get_paginator('list_objects_v2')

    files = []
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix='parcels/'):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if 'parcels_' in key:
                files.append({
                    'key': key,
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'filename': key.split('/')[-1]
                })
    return files


def find_duplicates(files):
    """Find duplicate versions of same county."""
    # Group by base county name (remove _v2, _v3, etc.)
    by_county = {}

    for f in files:
        filename = f['filename']
        base = filename.replace('.pmtiles', '').replace('.geojson', '')

        # Normalize: remove _v2, _v3 suffixes to find base county
        normalized = base
        for suffix in ['_v2', '_v3', '_v4']:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
                break

        if normalized not in by_county:
            by_county[normalized] = []
        by_county[normalized].append(f)

    # Find counties with multiple versions
    duplicates = {k: v for k, v in by_county.items() if len(v) > 1}
    return duplicates, by_county


def main():
    print("=" * 70)
    print("  VERIFY AND CLEANUP R2")
    print("=" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print()

    # List all files
    print("Listing all parcel files in R2...")
    files = list_all_parcels()

    pmtiles = [f for f in files if f['filename'].endswith('.pmtiles')]
    geojson = [f for f in files if f['filename'].endswith('.geojson')]

    print(f"  PMTiles: {len(pmtiles)}")
    print(f"  GeoJSON: {len(geojson)}")
    print(f"  Total: {len(files)}")

    # Find duplicates
    print("\nAnalyzing for duplicates...")
    duplicates, by_county = find_duplicates(pmtiles)

    if duplicates:
        print(f"\n  Found {len(duplicates)} counties with multiple versions:")
        to_delete = []
        to_keep = []

        for county, versions in sorted(duplicates.items()):
            # Sort by size (largest = most complete) and date (most recent)
            versions.sort(key=lambda x: (x['size'], x['last_modified']), reverse=True)
            best = versions[0]
            others = versions[1:]

            to_keep.append(best)
            to_delete.extend(others)

            print(f"\n  {county}:")
            print(f"    KEEP: {best['filename']} ({best['size']/1024/1024:.1f}MB, {best['last_modified']})")
            for other in others:
                print(f"    DELETE: {other['filename']} ({other['size']/1024/1024:.1f}MB, {other['last_modified']})")

        if to_delete:
            print(f"\n\nDeleting {len(to_delete)} duplicate files...")
            client = get_r2_client()
            deleted = 0
            for f in to_delete:
                try:
                    client.delete_object(Bucket=R2_BUCKET, Key=f['key'])
                    print(f"  Deleted: {f['key']}")
                    deleted += 1
                except Exception as e:
                    print(f"  FAILED to delete {f['key']}: {e}")
            print(f"\n  Deleted {deleted} duplicate files")
    else:
        print("  No duplicates found!")

    # Also delete any leftover GeoJSON files (we only need PMTiles)
    if geojson:
        print(f"\nDeleting {len(geojson)} GeoJSON files (keeping only PMTiles)...")
        client = get_r2_client()
        deleted = 0
        for f in geojson:
            try:
                client.delete_object(Bucket=R2_BUCKET, Key=f['key'])
                print(f"  Deleted: {f['key']}")
                deleted += 1
            except Exception as e:
                print(f"  FAILED to delete {f['key']}: {e}")
        print(f"  Deleted {deleted} GeoJSON files")

    # Final count
    print("\n" + "=" * 70)
    print("  FINAL VERIFICATION")
    print("=" * 70)

    files = list_all_parcels()
    pmtiles = [f for f in files if f['filename'].endswith('.pmtiles')]

    print(f"  Total PMTiles in R2: {len(pmtiles)}")
    total_size = sum(f['size'] for f in pmtiles) / 1024**3
    print(f"  Total size: {total_size:.1f} GB")

    # List by state
    by_state = {}
    for f in pmtiles:
        parts = f['filename'].replace('parcels_', '').split('_')
        state = parts[0].upper()
        if state not in by_state:
            by_state[state] = []
        by_state[state].append(f)

    print(f"\n  Files by state:")
    for state in sorted(by_state.keys()):
        state_files = by_state[state]
        state_size = sum(f['size'] for f in state_files) / 1024**3
        print(f"    {state}: {len(state_files)} files ({state_size:.1f}GB)")

    print("\n" + "=" * 70)
    print("  VERIFICATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
