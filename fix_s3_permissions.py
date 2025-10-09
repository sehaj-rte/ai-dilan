#!/usr/bin/env python3
"""
Script to fix S3 bucket permissions for public read access
"""

import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_s3_bucket_permissions():
    """Fix S3 bucket permissions to allow public read access"""
    
    # Get S3 configuration from environment
    bucket_name = os.getenv("S3_BUCKET_NAME", "ai-dilan")
    access_key_id = os.getenv("S3_ACCESS_KEY_ID")
    secret_key = os.getenv("S3_SECRET_KEY")
    region = os.getenv("S3_REGION", "us-east-1")
    
    print(f"🔧 Fixing S3 bucket permissions for: {bucket_name}")
    
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # 1. Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket {bucket_name} exists")
        except Exception as e:
            print(f"❌ Bucket {bucket_name} not found: {e}")
            return False
        
        # 2. Set bucket policy for public read access
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        
        try:
            s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            print("✅ Bucket policy updated for public read access")
        except Exception as e:
            print(f"⚠️  Could not set bucket policy: {e}")
            print("   This might be due to bucket ownership controls.")
        
        # 3. Disable block public access (if needed)
        try:
            s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': False,
                    'IgnorePublicAcls': False,
                    'BlockPublicPolicy': False,
                    'RestrictPublicBuckets': False
                }
            )
            print("✅ Public access block settings updated")
        except Exception as e:
            print(f"⚠️  Could not update public access block: {e}")
        
        # 4. List existing objects and make them public
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="expert-avatars/")
            if 'Contents' in response:
                print(f"📁 Found {len(response['Contents'])} existing avatar files")
                for obj in response['Contents']:
                    try:
                        # Try to set ACL to public-read
                        s3_client.put_object_acl(
                            Bucket=bucket_name,
                            Key=obj['Key'],
                            ACL='public-read'
                        )
                        print(f"   ✅ Made public: {obj['Key']}")
                    except Exception as e:
                        print(f"   ⚠️  Could not set ACL for {obj['Key']}: {e}")
            else:
                print("📁 No existing avatar files found")
        except Exception as e:
            print(f"⚠️  Could not list objects: {e}")
        
        # 5. Test access to a sample URL
        sample_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/expert-avatars/test.jpg"
        print(f"\n🔗 Sample URL format: {sample_url}")
        print("   Test this URL format with your actual image files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing S3 permissions: {e}")
        return False

if __name__ == "__main__":
    print("🚀 S3 Bucket Permission Fixer")
    print("=" * 40)
    
    success = fix_s3_bucket_permissions()
    
    if success:
        print("\n✅ S3 bucket permissions have been updated!")
        print("   Your avatar images should now be publicly accessible.")
    else:
        print("\n❌ Failed to update S3 bucket permissions.")
        print("   Please check your AWS credentials and bucket configuration.")
