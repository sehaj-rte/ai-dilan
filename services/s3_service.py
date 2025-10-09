import boto3
import uuid
import os
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError
from config.settings import S3_BUCKET_NAME, S3_ACCESS_KEY_ID, S3_SECRET_KEY, S3_REGION

class S3Service:
    def __init__(self):
        self.bucket_name = S3_BUCKET_NAME
        self.region = S3_REGION
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=S3_ACCESS_KEY_ID,
                aws_secret_access_key=S3_SECRET_KEY,
                region_name=S3_REGION
            )
        except Exception as e:
            print(f"Error initializing S3 client: {e}")
            self.s3_client = None
    
    def upload_file(self, file_content: bytes, file_name: str, content_type: str) -> Dict[str, Any]:
        """Upload file to S3 and return the URL"""
        try:
            if not self.s3_client:
                return {"success": False, "error": "S3 client not initialized"}
            
            if not self.bucket_name:
                return {"success": False, "error": "S3 bucket name not configured"}
            
            # Generate unique file key
            file_extension = os.path.splitext(file_name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            s3_key = f"knowledge-base/{unique_filename}"
            
            # Upload file to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                ServerSideEncryption='AES256'
            )
            
            # Generate public URL
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return {
                "success": True,
                "url": s3_url,
                "s3_key": s3_key,
                "bucket": self.bucket_name
            }
            
        except NoCredentialsError:
            return {"success": False, "error": "AWS credentials not found"}
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                return {"success": False, "error": f"Bucket '{self.bucket_name}' does not exist"}
            else:
                return {"success": False, "error": f"AWS S3 error: {e.response['Error']['Message']}"}
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {str(e)}"}
    
    def delete_file(self, s3_key: str) -> Dict[str, Any]:
        """Delete file from S3"""
        try:
            if not self.s3_client:
                return {"success": False, "error": "S3 client not initialized"}
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {"success": True}
            
        except ClientError as e:
            return {"success": False, "error": f"AWS S3 error: {e.response['Error']['Message']}"}
        except Exception as e:
            return {"success": False, "error": f"Delete failed: {str(e)}"}
    
    def get_file_url(self, s3_key: str, expiration: int = 3600) -> Dict[str, Any]:
        """Generate presigned URL for file access"""
        try:
            if not self.s3_client:
                return {"success": False, "error": "S3 client not initialized"}
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            return {"success": True, "url": url}
            
        except ClientError as e:
            return {"success": False, "error": f"AWS S3 error: {e.response['Error']['Message']}"}
        except Exception as e:
            return {"success": False, "error": f"URL generation failed: {str(e)}"}
    
    def check_bucket_exists(self) -> bool:
        """Check if the S3 bucket exists and is accessible"""
        try:
            if not self.s3_client:
                return False
            
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
            
        except ClientError:
            return False
        except Exception:
            return False

# Global S3 service instance
s3_service = S3Service()
