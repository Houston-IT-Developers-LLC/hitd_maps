#!/usr/bin/env python3
"""
Upload all parcel PMTiles files to Cloudflare R2 with multipart upload.
Skips files that already exist in R2.
"""

import os
import sys
import boto3
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path

# R2 Credentials
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

# Source directory
SOURCE_DIR = "/home/exx/Documents/C/hitd_maps/data-pipeline/output/pmtiles"

# R2 prefix for parcels
R2_PREFIX = "parcels/"

# Multipart upload config
MULTIPART_THRESHOLD = 100 * 1024 * 1024  # 100MB
MULTIPART_CHUNKSIZE = 100 * 1024 * 1024  # 100MB chunks
MAX_CONCURRENCY = 10  # Concurrent parts per file
MAX_PARALLEL_UPLOADS = 4  # Concurrent files

# Thread-safe counters
upload_lock = threading.Lock()
total_uploaded = 0
total_uploaded_size = 0
total_skipped = 0
total_skipped_size = 0
total_failed = 0

def get_s3_client():
    """Create S3 client configured for R2."""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
    )

def get_existing_files(client):
    """Get set of files already in R2 under the parcels/ prefix."""
    existing = {}
    paginator = client.get_paginator('list_objects_v2')

    print(f"Checking existing files in R2 bucket '{R2_BUCKET}' under prefix '{R2_PREFIX}'...")

    try:
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=R2_PREFIX):
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    size = obj['Size']
                    existing[key] = size
    except Exception as e:
        print(f"Warning: Could not list existing files: {e}")
        return {}

    print(f"Found {len(existing)} existing files in R2")
    return existing

def format_size(size_bytes):
    """Format bytes as human readable."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

def upload_file(client, local_path, r2_key, file_size, existing_files):
    """Upload a single file to R2 with multipart if needed."""
    global total_uploaded, total_uploaded_size, total_skipped, total_skipped_size, total_failed

    filename = os.path.basename(local_path)

    # Check if already exists with same size
    if r2_key in existing_files:
        existing_size = existing_files[r2_key]
        if existing_size == file_size:
            with upload_lock:
                total_skipped += 1
                total_skipped_size += file_size
            print(f"  SKIP: {filename} (already exists, {format_size(file_size)})")
            return True
        else:
            print(f"  REUPLOAD: {filename} (size mismatch: local={format_size(file_size)}, remote={format_size(existing_size)})")

    try:
        # Use multipart upload for large files
        transfer_config = boto3.s3.transfer.TransferConfig(
            multipart_threshold=MULTIPART_THRESHOLD,
            multipart_chunksize=MULTIPART_CHUNKSIZE,
            max_concurrency=MAX_CONCURRENCY,
            use_threads=True
        )

        print(f"  UPLOAD: {filename} ({format_size(file_size)})...")

        client.upload_file(
            local_path,
            R2_BUCKET,
            r2_key,
            Config=transfer_config,
            ExtraArgs={
                'ContentType': 'application/x-protobuf'
            }
        )

        with upload_lock:
            total_uploaded += 1
            total_uploaded_size += file_size

        print(f"  DONE: {filename}")
        return True

    except Exception as e:
        with upload_lock:
            total_failed += 1
        print(f"  FAIL: {filename} - {e}")
        return False

def main():
    global total_uploaded, total_uploaded_size, total_skipped, total_skipped_size, total_failed

    print("=" * 60)
    print("Parcel PMTiles Upload to Cloudflare R2")
    print("=" * 60)

    # Get list of local pmtiles files
    pmtiles_files = []
    for filename in sorted(os.listdir(SOURCE_DIR)):
        if filename.endswith('.pmtiles'):
            local_path = os.path.join(SOURCE_DIR, filename)
            file_size = os.path.getsize(local_path)
            r2_key = f"{R2_PREFIX}{filename}"
            pmtiles_files.append((local_path, r2_key, file_size))

    if not pmtiles_files:
        print("No .pmtiles files found!")
        return

    total_local_size = sum(f[2] for f in pmtiles_files)
    print(f"\nFound {len(pmtiles_files)} PMTiles files")
    print(f"Total local size: {format_size(total_local_size)}")
    print()

    # Create S3 client
    client = get_s3_client()

    # Get existing files
    existing_files = get_existing_files(client)
    print()

    # Upload files in parallel
    print(f"Starting parallel upload (max {MAX_PARALLEL_UPLOADS} concurrent)...")
    print("-" * 60)

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_UPLOADS) as executor:
        futures = {}
        for local_path, r2_key, file_size in pmtiles_files:
            future = executor.submit(upload_file, client, local_path, r2_key, file_size, existing_files)
            futures[future] = (local_path, file_size)

        for future in as_completed(futures):
            local_path, file_size = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"  ERROR: {os.path.basename(local_path)} - {e}")

    # Summary
    print()
    print("=" * 60)
    print("UPLOAD SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {len(pmtiles_files)}")
    print(f"Files uploaded:        {total_uploaded} ({format_size(total_uploaded_size)})")
    print(f"Files skipped:         {total_skipped} ({format_size(total_skipped_size)})")
    print(f"Files failed:          {total_failed}")
    print("=" * 60)

if __name__ == "__main__":
    main()
