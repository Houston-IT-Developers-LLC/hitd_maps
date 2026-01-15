#!/usr/bin/env python3
"""
Upload both GeoJSON and PMTiles files to Cloudflare R2

Usage:
    python3 upload_all_to_r2.py                    # Upload all files
    python3 upload_all_to_r2.py --list             # List files in R2
    python3 upload_all_to_r2.py --geojson-only     # Upload only GeoJSON
    python3 upload_all_to_r2.py --pmtiles-only     # Upload only PMTiles
    python3 upload_all_to_r2.py --delete           # Delete local files after upload
    python3 upload_all_to_r2.py --dry-run          # Show what would be uploaded
"""

import os
import sys
import boto3
from pathlib import Path
from datetime import datetime

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

# Content types
CONTENT_TYPES = {
    '.geojson': 'application/geo+json',
    '.pmtiles': 'application/x-protobuf',
}

# R2 folder structure
R2_FOLDERS = {
    '.geojson': 'geojson/',   # GeoJSON files go to geojson/
    '.pmtiles': 'pmtiles/',   # PMTiles files go to pmtiles/
}


def get_s3_client():
    """Create an S3 client configured for R2"""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
    )


def format_size(size_bytes):
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def upload_file(s3_client, local_path, remote_key, content_type, delete_after=False, dry_run=False):
    """Upload a single file to R2"""
    file_size = os.path.getsize(local_path)
    size_str = format_size(file_size)

    if dry_run:
        print(f"  [DRY RUN] Would upload: {os.path.basename(local_path)} ({size_str}) -> {remote_key}")
        return True

    print(f"  Uploading: {os.path.basename(local_path)} ({size_str})...")

    try:
        s3_client.upload_file(
            local_path,
            R2_BUCKET,
            remote_key,
            ExtraArgs={'ContentType': content_type}
        )
        print(f"    ✓ {R2_PUBLIC_URL}/{remote_key}")

        if delete_after:
            os.remove(local_path)
            print(f"    ✓ Deleted local file")

        return True
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False


def list_r2_files(s3_client):
    """List all files in R2 bucket"""
    all_files = []

    for prefix in ['geojson/', 'pmtiles/', 'parcels/']:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    all_files.append((obj['Key'], obj['Size']))

    return sorted(all_files)


def check_exists_in_r2(s3_client, remote_key):
    """Check if a file already exists in R2"""
    try:
        s3_client.head_object(Bucket=R2_BUCKET, Key=remote_key)
        return True
    except:
        return False


def main():
    s3_client = get_s3_client()

    # Parse arguments
    args = sys.argv[1:]
    delete_after = "--delete" in args
    dry_run = "--dry-run" in args
    geojson_only = "--geojson-only" in args
    pmtiles_only = "--pmtiles-only" in args
    skip_existing = "--skip-existing" in args

    # Change to data-pipeline directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)

    if "--list" in args:
        print("Files in R2 bucket:")
        print("=" * 60)
        files = list_r2_files(s3_client)

        geojson_count = 0
        pmtiles_count = 0
        total_size = 0

        for key, size in files:
            print(f"  {key} ({format_size(size)})")
            total_size += size
            if key.endswith('.geojson'):
                geojson_count += 1
            elif key.endswith('.pmtiles'):
                pmtiles_count += 1

        print("=" * 60)
        print(f"Total: {len(files)} files ({format_size(total_size)})")
        print(f"  GeoJSON: {geojson_count}")
        print(f"  PMTiles: {pmtiles_count}")
        return

    # Collect files to upload
    files_to_upload = []

    if not pmtiles_only:
        geojson_dir = Path("output/geojson")
        if geojson_dir.exists():
            for f in geojson_dir.glob("*.geojson"):
                files_to_upload.append((f, '.geojson'))

    if not geojson_only:
        pmtiles_dir = Path("output/pmtiles")
        if pmtiles_dir.exists():
            for f in pmtiles_dir.glob("*.pmtiles"):
                files_to_upload.append((f, '.pmtiles'))

    if not files_to_upload:
        print("No files found to upload.")
        print("  GeoJSON: output/geojson/*.geojson")
        print("  PMTiles: output/pmtiles/*.pmtiles")
        return

    # Sort by size (smallest first)
    files_to_upload.sort(key=lambda x: x[0].stat().st_size)

    # Calculate totals
    total_size = sum(f[0].stat().st_size for f in files_to_upload)
    geojson_files = [f for f in files_to_upload if f[1] == '.geojson']
    pmtiles_files = [f for f in files_to_upload if f[1] == '.pmtiles']

    print("=" * 60)
    print(f"R2 Upload - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Files to upload: {len(files_to_upload)} ({format_size(total_size)})")
    print(f"  GeoJSON: {len(geojson_files)}")
    print(f"  PMTiles: {len(pmtiles_files)}")
    print(f"Options: delete_after={delete_after}, dry_run={dry_run}")
    print("=" * 60)

    uploaded = 0
    failed = 0
    skipped = 0

    for file_path, ext in files_to_upload:
        remote_folder = R2_FOLDERS[ext]
        remote_key = f"{remote_folder}{file_path.name}"
        content_type = CONTENT_TYPES[ext]

        # Check if already exists in R2
        if skip_existing and check_exists_in_r2(s3_client, remote_key):
            print(f"  SKIP (exists): {file_path.name}")
            skipped += 1
            continue

        if upload_file(s3_client, str(file_path), remote_key, content_type, delete_after, dry_run):
            uploaded += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Upload complete!")
    print(f"  Uploaded: {uploaded}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")
    print(f"\nPublic URLs:")
    print(f"  GeoJSON: {R2_PUBLIC_URL}/geojson/")
    print(f"  PMTiles: {R2_PUBLIC_URL}/pmtiles/")
    print("=" * 60)


if __name__ == "__main__":
    main()
