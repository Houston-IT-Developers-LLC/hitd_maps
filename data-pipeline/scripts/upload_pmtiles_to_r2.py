#!/usr/bin/env python3
"""Upload PMTiles to Cloudflare R2"""
import os
import sys
import boto3
from pathlib import Path

R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
R2_BUCKET = "gspot-tiles"
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-2ecaf6bcd4974935938a5ec02cd32cc9.r2.dev"

def get_s3_client():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                       aws_access_key_id=R2_ACCESS_KEY,
                       aws_secret_access_key=R2_SECRET_KEY)

def upload_file(s3_client, local_path, remote_key):
    file_size = os.path.getsize(local_path) / (1024 * 1024)
    print(f"Uploading: {os.path.basename(local_path)} ({file_size:.1f}MB)...")
    try:
        s3_client.upload_file(local_path, R2_BUCKET, remote_key,
                             ExtraArgs={'ContentType': 'application/x-protobuf'})
        print(f"  ✓ Uploaded to: {R2_PUBLIC_URL}/{remote_key}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    s3_client = get_s3_client()
    pmtiles_dir = Path("output/pmtiles")
    pmtiles_files = sorted(pmtiles_dir.glob("*.pmtiles"), key=lambda f: f.stat().st_size)
    
    if not pmtiles_files:
        print("No PMTiles files found")
        return
    
    print(f"Found {len(pmtiles_files)} PMTiles files to upload")
    uploaded = failed = 0
    
    for f in pmtiles_files:
        remote_key = f"parcels/{f.name}"
        if upload_file(s3_client, str(f), remote_key):
            uploaded += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Upload complete: {uploaded} succeeded, {failed} failed")
    print(f"Public URL: {R2_PUBLIC_URL}/parcels/")

if __name__ == "__main__":
    main()
