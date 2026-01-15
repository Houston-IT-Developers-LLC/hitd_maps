#!/usr/bin/env python3
"""
Parallel upload to R2 - uploads multiple files concurrently
Usage: python3 parallel_upload.py [--workers N] [--pmtiles-only] [--geojson-only]
"""

import os
import sys
import boto3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

CONTENT_TYPES = {
    '.geojson': 'application/geo+json',
    '.pmtiles': 'application/x-protobuf',
}

R2_FOLDERS = {
    '.geojson': 'geojson/',
    '.pmtiles': 'pmtiles/',
}

print_lock = Lock()
stats = {'uploaded': 0, 'failed': 0, 'skipped': 0}
stats_lock = Lock()

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
    )

def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"

def upload_file(file_info):
    """Upload a single file - designed to run in thread pool"""
    file_path, ext = file_info
    s3_client = get_s3_client()  # Each thread gets its own client

    remote_folder = R2_FOLDERS[ext]
    remote_key = f"{remote_folder}{file_path.name}"
    content_type = CONTENT_TYPES[ext]

    file_size = file_path.stat().st_size
    size_str = format_size(file_size)

    try:
        s3_client.upload_file(
            str(file_path),
            R2_BUCKET,
            remote_key,
            ExtraArgs={'ContentType': content_type}
        )
        with print_lock:
            print(f"✓ {file_path.name} ({size_str})")
        with stats_lock:
            stats['uploaded'] += 1
        return True
    except Exception as e:
        with print_lock:
            print(f"✗ {file_path.name}: {e}")
        with stats_lock:
            stats['failed'] += 1
        return False

def main():
    args = sys.argv[1:]
    workers = 8  # Default parallel workers
    pmtiles_only = "--pmtiles-only" in args
    geojson_only = "--geojson-only" in args

    # Parse --workers N
    for i, arg in enumerate(args):
        if arg == "--workers" and i + 1 < len(args):
            workers = int(args[i + 1])

    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)

    # Collect files
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
        print("No files to upload")
        return

    # Sort by size (smallest first for quick progress)
    files_to_upload.sort(key=lambda x: x[0].stat().st_size)

    total_size = sum(f[0].stat().st_size for f in files_to_upload)

    print("=" * 60)
    print(f"Parallel R2 Upload")
    print(f"Workers: {workers}")
    print(f"Files: {len(files_to_upload)} ({format_size(total_size)})")
    print("=" * 60)

    # Upload in parallel
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(upload_file, f): f for f in files_to_upload}
        for future in as_completed(futures):
            pass  # Results handled in upload_file

    print("=" * 60)
    print(f"Complete! Uploaded: {stats['uploaded']}, Failed: {stats['failed']}")
    print(f"URLs: {R2_PUBLIC_URL}/geojson/ and {R2_PUBLIC_URL}/pmtiles/")
    print("=" * 60)

if __name__ == "__main__":
    main()
