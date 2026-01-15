#!/usr/bin/env python3
"""
Upload GeoJSON files to Cloudflare R2 using boto3
"""

import os
import sys
import boto3
from pathlib import Path

# R2 Configuration
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

def get_s3_client():
    """Create an S3 client configured for R2"""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
    )

def upload_file(s3_client, local_path, remote_key, delete_after=False):
    """Upload a single file to R2"""
    file_size = os.path.getsize(local_path) / (1024 * 1024)  # MB
    print(f"Uploading: {os.path.basename(local_path)} ({file_size:.1f}MB)...")

    try:
        s3_client.upload_file(
            local_path,
            R2_BUCKET,
            remote_key,
            ExtraArgs={'ContentType': 'application/geo+json'}
        )
        print(f"  ✓ Uploaded to: {R2_PUBLIC_URL}/{remote_key}")

        if delete_after:
            os.remove(local_path)
            print(f"  ✓ Deleted local file")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def list_r2_files(s3_client, prefix="parcels/"):
    """List files in R2"""
    response = s3_client.list_objects_v2(Bucket=R2_BUCKET, Prefix=prefix)
    files = []
    if 'Contents' in response:
        for obj in response['Contents']:
            files.append((obj['Key'], obj['Size']))
    return files

def main():
    s3_client = get_s3_client()

    # Get arguments
    delete_after = "--delete" in sys.argv
    geojson_dir = Path("output/geojson")

    if "--list" in sys.argv:
        print("Files in R2:")
        files = list_r2_files(s3_client)
        for key, size in sorted(files):
            print(f"  {key} ({size/1024/1024:.1f}MB)")
        print(f"\nTotal: {len(files)} files")
        return

    # Find all GeoJSON files
    geojson_files = sorted(geojson_dir.glob("*.geojson"), key=lambda f: f.stat().st_size)

    if not geojson_files:
        print("No GeoJSON files found in output/geojson/")
        return

    print(f"Found {len(geojson_files)} files to upload")
    print(f"Delete after upload: {delete_after}")
    print()

    uploaded = 0
    failed = 0

    for file_path in geojson_files:
        remote_key = f"parcels/{file_path.name}"
        if upload_file(s3_client, str(file_path), remote_key, delete_after):
            uploaded += 1
        else:
            failed += 1

    print(f"\n{'='*50}")
    print(f"Upload complete: {uploaded} succeeded, {failed} failed")
    print(f"Public URL: {R2_PUBLIC_URL}/parcels/")

if __name__ == "__main__":
    main()
