#!/usr/bin/env python3
"""
Upload font glyph PBF files to Cloudflare R2
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

def upload_file(s3_client, local_path, remote_key):
    """Upload a single file to R2"""
    file_size = os.path.getsize(local_path) / 1024  # KB
    
    try:
        s3_client.upload_file(
            local_path,
            R2_BUCKET,
            remote_key,
            ExtraArgs={'ContentType': 'application/x-protobuf'}
        )
        print(f"  Uploaded: {remote_key} ({file_size:.1f}KB)")
        return True
    except Exception as e:
        print(f"  Error uploading {remote_key}: {e}")
        return False

def main():
    font_dir = Path("/home/exx/Documents/C/hitd_maps/data-pipeline/assets/fonts/Noto Sans Regular")
    
    if not font_dir.exists():
        print(f"Error: Font directory not found: {font_dir}")
        return
    
    s3_client = get_s3_client()
    
    # Find all PBF files
    pbf_files = sorted(font_dir.glob("*.pbf"))
    
    if not pbf_files:
        print("No PBF files found")
        return
    
    print(f"Found {len(pbf_files)} PBF font files to upload")
    print(f"Uploading to: fonts/Noto Sans Regular/")
    print()
    
    uploaded = 0
    failed = 0
    
    for file_path in pbf_files:
        # Upload to fonts/Noto Sans Regular/{filename}
        remote_key = f"fonts/Noto Sans Regular/{file_path.name}"
        if upload_file(s3_client, str(file_path), remote_key):
            uploaded += 1
        else:
            failed += 1
    
    print()
    print(f"{'='*60}")
    print(f"Upload complete: {uploaded} succeeded, {failed} failed")
    print(f"Public URL: {R2_PUBLIC_URL}/fonts/Noto%20Sans%20Regular/")
    print(f"Example: {R2_PUBLIC_URL}/fonts/Noto%20Sans%20Regular/0-255.pbf")

if __name__ == "__main__":
    main()
