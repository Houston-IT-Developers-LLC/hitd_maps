#!/usr/bin/env python3
"""Upload usa_addresses.pmtiles to Cloudflare R2 with multipart upload."""

import boto3
from boto3.s3.transfer import TransferConfig
import os
import sys

# R2 Configuration
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_BUCKET = "gspot-tiles"
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# File paths
LOCAL_FILE = "/home/exx/Documents/C/hitd_maps/data-pipeline/downloads/pois/usa_addresses.pmtiles"
R2_KEY = "addresses/usa_addresses.pmtiles"

def get_file_size_gb(filepath):
    """Get file size in GB."""
    size_bytes = os.path.getsize(filepath)
    return size_bytes / (1024 ** 3)

def upload_to_r2():
    """Upload file to R2 with multipart upload and progress tracking."""
    
    if not os.path.exists(LOCAL_FILE):
        print(f"ERROR: File not found: {LOCAL_FILE}")
        return False
    
    file_size = os.path.getsize(LOCAL_FILE)
    file_size_gb = get_file_size_gb(LOCAL_FILE)
    print(f"File: {LOCAL_FILE}")
    print(f"Size: {file_size_gb:.2f} GB ({file_size:,} bytes)")
    print(f"Destination: s3://{R2_BUCKET}/{R2_KEY}")
    print()
    
    # Create S3 client for R2
    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'
    )
    
    # Configure multipart upload
    # Use 100MB chunks for 7GB file (results in ~71 parts)
    config = TransferConfig(
        multipart_threshold=100 * 1024 * 1024,  # 100MB
        max_concurrency=10,
        multipart_chunksize=100 * 1024 * 1024,  # 100MB chunks
        use_threads=True
    )
    
    # Progress tracking
    uploaded_bytes = 0
    last_percent = -1
    
    def progress_callback(bytes_transferred):
        nonlocal uploaded_bytes, last_percent
        uploaded_bytes += bytes_transferred
        percent = int((uploaded_bytes / file_size) * 100)
        if percent != last_percent:
            uploaded_gb = uploaded_bytes / (1024 ** 3)
            print(f"\rProgress: {percent}% ({uploaded_gb:.2f} GB / {file_size_gb:.2f} GB)", end='', flush=True)
            last_percent = percent
    
    print("Starting multipart upload...")
    try:
        s3_client.upload_file(
            LOCAL_FILE,
            R2_BUCKET,
            R2_KEY,
            Config=config,
            Callback=progress_callback
        )
        print()  # New line after progress
        print("Upload completed successfully!")
        return True
    except Exception as e:
        print()
        print(f"ERROR: Upload failed: {e}")
        return False

def verify_upload():
    """Verify the uploaded file exists and has correct size."""
    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'
    )
    
    try:
        response = s3_client.head_object(Bucket=R2_BUCKET, Key=R2_KEY)
        remote_size = response['ContentLength']
        local_size = os.path.getsize(LOCAL_FILE)
        
        print(f"\nVerification:")
        print(f"  Local size:  {local_size:,} bytes")
        print(f"  Remote size: {remote_size:,} bytes")
        
        if remote_size == local_size:
            print("  Status: VERIFIED - sizes match")
            return True
        else:
            print("  Status: MISMATCH - sizes differ!")
            return False
    except Exception as e:
        print(f"\nVerification failed: {e}")
        return False

def delete_local_file():
    """Delete the local file after successful upload."""
    try:
        os.remove(LOCAL_FILE)
        print(f"\nDeleted local file: {LOCAL_FILE}")
        print("Freed ~7.1 GB of disk space")
        return True
    except Exception as e:
        print(f"\nFailed to delete local file: {e}")
        return False

def main():
    print("=" * 60)
    print("Uploading usa_addresses.pmtiles to Cloudflare R2")
    print("=" * 60)
    print()
    
    # Upload
    if not upload_to_r2():
        sys.exit(1)
    
    # Verify
    if not verify_upload():
        print("WARNING: Verification failed, not deleting local file")
        sys.exit(1)
    
    # Delete local file
    if not delete_local_file():
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("SUCCESS: Upload complete, local file deleted")
    print(f"R2 URL: {R2_ENDPOINT}/{R2_BUCKET}/{R2_KEY}")
    print("=" * 60)

if __name__ == "__main__":
    main()
