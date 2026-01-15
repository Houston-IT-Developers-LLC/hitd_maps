#!/usr/bin/env python3
"""Upload usa_roads.pmtiles to Cloudflare R2 with manual multipart upload."""

import boto3
import os
import sys
import hashlib
import base64

# R2 Configuration
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_BUCKET = "gspot-tiles"
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"

# File paths
LOCAL_FILE = "/home/exx/Documents/C/hitd_maps/data-pipeline/downloads/pois/usa_roads.pmtiles"
R2_KEY = "roads/usa_roads.pmtiles"

# Chunk size: 100MB
CHUNK_SIZE = 100 * 1024 * 1024

def get_file_size(filepath):
    return os.path.getsize(filepath)

def format_size(bytes_size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"

def main():
    print(f"Starting upload of {LOCAL_FILE}")
    print(f"Destination: s3://{R2_BUCKET}/{R2_KEY}")
    
    file_size = get_file_size(LOCAL_FILE)
    print(f"File size: {format_size(file_size)}")
    
    # Create S3 client for R2
    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'
    )
    
    # Calculate number of parts
    num_parts = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
    print(f"Will upload in {num_parts} parts of {format_size(CHUNK_SIZE)} each")
    
    try:
        # Start multipart upload
        print("Initiating multipart upload...")
        response = s3_client.create_multipart_upload(
            Bucket=R2_BUCKET,
            Key=R2_KEY,
            ContentType='application/vnd.pmtiles'
        )
        upload_id = response['UploadId']
        print(f"Upload ID: {upload_id}")
        
        parts = []
        uploaded_bytes = 0
        
        with open(LOCAL_FILE, 'rb') as f:
            for part_num in range(1, num_parts + 1):
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                
                # Upload part
                part_response = s3_client.upload_part(
                    Bucket=R2_BUCKET,
                    Key=R2_KEY,
                    PartNumber=part_num,
                    UploadId=upload_id,
                    Body=chunk
                )
                
                parts.append({
                    'PartNumber': part_num,
                    'ETag': part_response['ETag']
                })
                
                uploaded_bytes += len(chunk)
                percent = int((uploaded_bytes / file_size) * 100)
                print(f"Part {part_num}/{num_parts} uploaded - {percent}% ({format_size(uploaded_bytes)} / {format_size(file_size)})")
                sys.stdout.flush()
        
        # Complete multipart upload
        print("Completing multipart upload...")
        s3_client.complete_multipart_upload(
            Bucket=R2_BUCKET,
            Key=R2_KEY,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        
        print(f"\nUpload complete: {R2_KEY}")
        
        # Verify the upload
        response = s3_client.head_object(Bucket=R2_BUCKET, Key=R2_KEY)
        remote_size = response['ContentLength']
        print(f"Verified remote file size: {format_size(remote_size)}")
        
        if remote_size == file_size:
            print("Size verification passed!")
            return True
        else:
            print(f"WARNING: Size mismatch! Local: {file_size}, Remote: {remote_size}")
            return False
            
    except Exception as e:
        print(f"Upload failed: {e}")
        # Try to abort the multipart upload if it was started
        try:
            if 'upload_id' in dir():
                print("Aborting multipart upload...")
                s3_client.abort_multipart_upload(
                    Bucket=R2_BUCKET,
                    Key=R2_KEY,
                    UploadId=upload_id
                )
        except:
            pass
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
