#!/usr/bin/env python3
"""
Upload enrichment PMTiles to Cloudflare R2 with multipart upload.
Skips files that already exist in R2.
"""

import os
import sys
import boto3
from botocore.config import Config
from pathlib import Path
import hashlib

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"

# Source directory
SOURCE_DIR = "/home/exx/Documents/C/hitd_maps/data-pipeline/output/enrichment/pmtiles"

# R2 prefix for enrichment files
R2_PREFIX = "enrichment/"

# Multipart upload threshold and chunk size (5MB minimum for S3/R2)
MULTIPART_THRESHOLD = 5 * 1024 * 1024  # 5MB
MULTIPART_CHUNKSIZE = 10 * 1024 * 1024  # 10MB chunks


def get_s3_client():
    """Create and return an S3 client configured for R2."""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
    )


def list_existing_keys(s3_client, prefix):
    """List all existing keys in R2 under the given prefix."""
    existing_keys = set()
    paginator = s3_client.get_paginator('list_objects_v2')

    try:
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    existing_keys.add(obj['Key'])
    except Exception as e:
        print(f"Warning: Could not list existing keys: {e}")

    return existing_keys


def format_size(size_bytes):
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def multipart_upload(s3_client, file_path, key):
    """Upload a file using multipart upload."""
    file_size = os.path.getsize(file_path)

    # Initialize multipart upload
    response = s3_client.create_multipart_upload(
        Bucket=R2_BUCKET,
        Key=key,
        ContentType='application/octet-stream'
    )
    upload_id = response['UploadId']

    parts = []
    part_number = 1
    uploaded_bytes = 0

    try:
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(MULTIPART_CHUNKSIZE)
                if not data:
                    break

                # Upload part
                part_response = s3_client.upload_part(
                    Bucket=R2_BUCKET,
                    Key=key,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=data
                )

                parts.append({
                    'ETag': part_response['ETag'],
                    'PartNumber': part_number
                })

                uploaded_bytes += len(data)
                progress = (uploaded_bytes / file_size) * 100
                print(f"    Progress: {progress:.1f}% ({format_size(uploaded_bytes)}/{format_size(file_size)})", end='\r')

                part_number += 1

        # Complete multipart upload
        s3_client.complete_multipart_upload(
            Bucket=R2_BUCKET,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        print()  # New line after progress

    except Exception as e:
        # Abort on failure
        s3_client.abort_multipart_upload(
            Bucket=R2_BUCKET,
            Key=key,
            UploadId=upload_id
        )
        raise e


def simple_upload(s3_client, file_path, key):
    """Upload a small file without multipart."""
    with open(file_path, 'rb') as f:
        s3_client.put_object(
            Bucket=R2_BUCKET,
            Key=key,
            Body=f,
            ContentType='application/octet-stream'
        )


def upload_file(s3_client, file_path, key):
    """Upload a file to R2, using multipart for large files."""
    file_size = os.path.getsize(file_path)

    if file_size > MULTIPART_THRESHOLD:
        multipart_upload(s3_client, file_path, key)
    else:
        simple_upload(s3_client, file_path, key)


def main():
    print("=" * 60)
    print("Enrichment PMTiles Upload to R2")
    print("=" * 60)
    print(f"\nSource: {SOURCE_DIR}")
    print(f"Destination: s3://{R2_BUCKET}/{R2_PREFIX}")
    print()

    # Get S3 client
    s3_client = get_s3_client()

    # Find all .pmtiles files
    source_path = Path(SOURCE_DIR)
    pmtiles_files = list(source_path.glob("**/*.pmtiles"))

    # Filter out .tmp files
    pmtiles_files = [f for f in pmtiles_files if not str(f).endswith('.tmp')]

    print(f"Found {len(pmtiles_files)} PMTiles files to process")

    # Calculate total size
    total_size = sum(f.stat().st_size for f in pmtiles_files)
    print(f"Total size: {format_size(total_size)}")
    print()

    # List existing keys in R2
    print("Checking existing files in R2...")
    existing_keys = list_existing_keys(s3_client, R2_PREFIX)
    print(f"Found {len(existing_keys)} existing files in R2 under '{R2_PREFIX}'")
    print()

    # Upload files
    uploaded_count = 0
    uploaded_size = 0
    skipped_count = 0
    skipped_size = 0
    failed_files = []

    for i, file_path in enumerate(sorted(pmtiles_files), 1):
        # Compute R2 key preserving subdirectory structure
        relative_path = file_path.relative_to(source_path)
        r2_key = R2_PREFIX + str(relative_path)
        file_size = file_path.stat().st_size

        print(f"[{i}/{len(pmtiles_files)}] {file_path.name} ({format_size(file_size)})")

        # Check if file exists
        if r2_key in existing_keys:
            print(f"  -> SKIPPED (already exists in R2)")
            skipped_count += 1
            skipped_size += file_size
            continue

        # Upload file
        try:
            print(f"  -> Uploading to {r2_key}...")
            upload_file(s3_client, str(file_path), r2_key)
            print(f"  -> SUCCESS")
            uploaded_count += 1
            uploaded_size += file_size
        except Exception as e:
            print(f"  -> FAILED: {e}")
            failed_files.append((file_path.name, str(e)))

    # Summary
    print()
    print("=" * 60)
    print("UPLOAD SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {len(pmtiles_files)}")
    print(f"Files uploaded:        {uploaded_count} ({format_size(uploaded_size)})")
    print(f"Files skipped:         {skipped_count} ({format_size(skipped_size)})")
    print(f"Files failed:          {len(failed_files)}")

    if failed_files:
        print("\nFailed files:")
        for name, error in failed_files:
            print(f"  - {name}: {error}")

    print()
    print("Done!")

    return 0 if not failed_files else 1


if __name__ == "__main__":
    sys.exit(main())
