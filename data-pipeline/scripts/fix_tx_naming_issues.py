#!/usr/bin/env python3
"""
Fix Texas parcel naming issues:
1. Rename parcels_montgomery.pmtiles -> parcels_tx_montgomery.pmtiles
2. Copy parcels_tx_williamson_v2.pmtiles -> parcels_tx_williamson.pmtiles (or create symlink)
"""

import boto3
import json

# R2 Configuration
R2_ENDPOINT = "https://551bf8d24bb6069fbaa10e863a672fd5.r2.cloudflarestorage.com"
R2_ACCESS_KEY = "ecd653afe3300fdc045b9980df0dbb14"
R2_SECRET_KEY = "c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35"
BUCKET = "gspot-tiles"

# Initialize S3 client for R2
s3 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name='auto'
)


def copy_r2_file(source_key: str, dest_key: str) -> bool:
    """Copy a file within R2 bucket."""
    try:
        print(f"Copying: {source_key} -> {dest_key}")

        # Copy the object
        copy_source = {'Bucket': BUCKET, 'Key': source_key}
        s3.copy_object(
            CopySource=copy_source,
            Bucket=BUCKET,
            Key=dest_key
        )

        print(f"✅ Copied successfully")
        return True

    except Exception as e:
        print(f"❌ Error copying: {e}")
        return False


def delete_r2_file(key: str) -> bool:
    """Delete a file from R2 bucket."""
    try:
        print(f"Deleting: {key}")
        s3.delete_object(Bucket=BUCKET, Key=key)
        print(f"✅ Deleted successfully")
        return True

    except Exception as e:
        print(f"❌ Error deleting: {e}")
        return False


def check_file_exists(key: str) -> bool:
    """Check if a file exists in R2."""
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        return True
    except:
        return False


def main():
    print("=" * 80)
    print("FIXING TEXAS PARCEL NAMING ISSUES")
    print("=" * 80)
    print()

    fixes = []

    # Issue 1: Rename parcels_montgomery -> parcels_tx_montgomery
    print("Issue 1: Montgomery County naming")
    print("-" * 80)

    old_key = "parcels/parcels_montgomery.pmtiles"
    new_key = "parcels/parcels_tx_montgomery.pmtiles"

    print(f"Checking if {old_key} exists...")
    if check_file_exists(old_key):
        print(f"✅ Found: {old_key}")

        print(f"Checking if {new_key} already exists...")
        if check_file_exists(new_key):
            print(f"⚠️  WARNING: {new_key} already exists!")
            print("   Skipping to avoid overwriting...")
        else:
            print(f"Copying {old_key} -> {new_key}...")
            if copy_r2_file(old_key, new_key):
                fixes.append({
                    "issue": "montgomery_naming",
                    "action": "copied",
                    "from": old_key,
                    "to": new_key,
                    "status": "success"
                })

                # Optionally delete the old file
                print("\nDelete the old file? (will do this manually)")
                # delete_r2_file(old_key)
    else:
        print(f"❌ File not found: {old_key}")
        fixes.append({
            "issue": "montgomery_naming",
            "status": "source_not_found"
        })

    print()

    # Issue 2: Copy parcels_tx_williamson_v2 -> parcels_tx_williamson
    print("Issue 2: Williamson County missing base file")
    print("-" * 80)

    source_key = "parcels/parcels_tx_williamson_v2.pmtiles"
    dest_key = "parcels/parcels_tx_williamson.pmtiles"

    print(f"Checking if {source_key} exists...")
    if check_file_exists(source_key):
        print(f"✅ Found: {source_key}")

        print(f"Checking if {dest_key} already exists...")
        if check_file_exists(dest_key):
            print(f"✅ {dest_key} already exists (no action needed)")
            fixes.append({
                "issue": "williamson_base_file",
                "status": "already_exists"
            })
        else:
            print(f"Copying {source_key} -> {dest_key}...")
            if copy_r2_file(source_key, dest_key):
                fixes.append({
                    "issue": "williamson_base_file",
                    "action": "copied",
                    "from": source_key,
                    "to": dest_key,
                    "status": "success"
                })
    else:
        print(f"❌ File not found: {source_key}")
        fixes.append({
            "issue": "williamson_base_file",
            "status": "source_not_found"
        })

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(json.dumps(fixes, indent=2))

    print("\n✅ Fix script completed")
    print("\nNEXT STEPS:")
    print("1. Update data/valid_parcels.json:")
    print("   - Add: 'parcels_tx_montgomery'")
    print("   - Ensure: 'parcels_tx_williamson' exists (not just _v2)")
    print("2. Optionally delete old 'parcels_montgomery.pmtiles'")
    print("3. Re-run test: python3 scripts/test_tx_coverage.py")
    print()


if __name__ == "__main__":
    main()
