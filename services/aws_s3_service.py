import boto3
import base64
import os
import uuid
from typing import Dict, Any, Optional
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime

logger = logging.getLogger(__name__)

class AWSS3Service:
    def __init__(self):
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "ai-dilan")
        self.access_key_id = os.getenv("S3_ACCESS_KEY_ID")
        self.secret_key = os.getenv("S3_SECRET_KEY")
        self.region = os.getenv("S3_REGION", "us-east-1")
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            logger.info("AWS S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS S3 client: {str(e)}")
            self.s3_client = None
    
    def _get_content_type(self, image_type: str) -> str:
        """Get content type from image type"""
        content_types = {
            'jpeg': 'image/jpeg',
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        return content_types.get(image_type.lower(), 'image/jpeg')
    
    def _generate_filename(self, image_type: str, folder: str = "expert-avatars") -> str:
        """Generate unique filename for the image"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        extension = image_type.lower()
        if extension == 'jpeg':
            extension = 'jpg'
        
        return f"{folder}/{timestamp}_{unique_id}.{extension}"
    
    async def upload_base64_image(self, base64_data: str, folder: str = "expert-avatars") -> Dict[str, Any]:
        """
        Upload a base64 encoded image to AWS S3
        
        Args:
            base64_data: Base64 encoded image data (with data:image/... prefix)
            folder: Folder to store the image in
            
        Returns:
            Dict containing success status and image URL
        """
        try:
            if not self.s3_client:
                return {
                    "success": False,
                    "error": "AWS S3 client not initialized"
                }
            
            # Validate base64 data
            if not base64_data.startswith("data:image/"):
                return {
                    "success": False,
                    "error": "Invalid image format. Must be base64 encoded image."
                }
            
            # Extract image type and base64 content
            header, encoded = base64_data.split(',', 1)
            image_type = header.split('/')[1].split(';')[0]
            
            # Decode base64 to binary
            image_binary = base64.b64decode(encoded)
            
            # Generate filename
            filename = self._generate_filename(image_type, folder)
            
            # Get content type
            content_type = self._get_content_type(image_type)
            
            # Upload to S3 with public-read ACL
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=filename,
                    Body=image_binary,
                    ContentType=content_type,
                    ACL='public-read'  # Make the object publicly readable
                )
            except ClientError as acl_error:
                # If ACL fails, try without ACL (fallback)
                logger.warning(f"Failed to set public-read ACL, uploading without ACL: {acl_error}")
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=filename,
                    Body=image_binary,
                    ContentType=content_type
                )
            
            # Generate public URL
            image_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
            
            logger.info(f"Successfully uploaded image to S3: {image_url}")
            
            return {
                "success": True,
                "url": image_url,
                "secure_url": image_url,
                "filename": filename,
                "bucket": self.bucket_name
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS S3 ClientError: {error_code} - {str(e)}")
            return {
                "success": False,
                "error": f"AWS S3 error: {error_code}",
                "details": str(e)
            }
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return {
                "success": False,
                "error": "AWS credentials not configured"
            }
        except Exception as e:
            logger.error(f"Error uploading image to S3: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to upload image: {str(e)}"
            }
    
    def delete_image(self, filename: str) -> Dict[str, Any]:
        """
        Delete an image from S3
        
        Args:
            filename: The S3 key/filename to delete
            
        Returns:
            Dict containing success status
        """
        try:
            if not self.s3_client:
                return {
                    "success": False,
                    "error": "AWS S3 client not initialized"
                }
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            
            logger.info(f"Successfully deleted image from S3: {filename}")
            return {"success": True}
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS S3 delete error: {error_code} - {str(e)}")
            return {
                "success": False,
                "error": f"Failed to delete image: {error_code}"
            }
        except Exception as e:
            logger.error(f"Error deleting image from S3: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to delete image: {str(e)}"
            }
    
    def validate_base64_image(self, base64_data: str) -> Dict[str, Any]:
        """
        Validate base64 image data
        
        Args:
            base64_data: Base64 encoded image data
            
        Returns:
            Dict containing validation result
        """
        try:
            # Check if it starts with data:image/
            if not base64_data.startswith("data:image/"):
                return {
                    "valid": False,
                    "error": "Invalid image format. Must be base64 encoded image."
                }
            
            # Extract the actual base64 part
            header, encoded = base64_data.split(',', 1)
            
            # Try to decode to verify it's valid base64
            decoded = base64.b64decode(encoded)
            
            # Check file size (limit to 10MB)
            if len(decoded) > 10 * 1024 * 1024:
                return {
                    "valid": False,
                    "error": "Image too large. Maximum size is 10MB."
                }
            
            # Extract image type from header
            image_type = header.split('/')[1].split(';')[0]
            allowed_types = ['jpeg', 'jpg', 'png', 'gif', 'webp']
            
            if image_type.lower() not in allowed_types:
                return {
                    "valid": False,
                    "error": f"Unsupported image type: {image_type}. Allowed types: {', '.join(allowed_types)}"
                }
            
            return {
                "valid": True,
                "image_type": image_type,
                "size_bytes": len(decoded)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Invalid base64 image data: {str(e)}"
            }

# Create a singleton instance
s3_service = AWSS3Service()
