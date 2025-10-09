import httpx
import base64
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ImageUploadService:
    def __init__(self):
        self.upload_url = "https://flashgenai.com/api/public/upload-base64"
        self.headers = {
            "Content-Type": "application/json"
        }
    
    async def upload_base64_image(self, base64_data: str, folder: str = "public-images") -> Dict[str, Any]:
        """
        Upload a base64 encoded image to FlashGenAI
        
        Args:
            base64_data: Base64 encoded image data (with data:image/... prefix)
            folder: Folder to store the image in
            
        Returns:
            Dict containing success status and image URL
        """
        try:
            payload = {
                "base64Data": base64_data,
                "folder": folder,
                "resource_type": "auto"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.upload_url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully uploaded image: {data.get('url')}")
                    return {
                        "success": True,
                        "url": data.get("url"),
                        "public_id": data.get("public_id"),
                        "secure_url": data.get("secure_url")
                    }
                else:
                    logger.error(f"Image upload API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Image upload API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to upload image: {str(e)}"
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
image_service = ImageUploadService()
