from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import boto3
import os
from botocore.exceptions import ClientError
import io

router = APIRouter()

def get_s3_client():
    """Get S3 client"""
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name=os.getenv("S3_REGION", "us-east-1")
    )

@router.get("/avatar/{filename}")
async def get_avatar_image(filename: str):
    """
    Proxy endpoint to serve avatar images from S3
    """
    try:
        s3_client = get_s3_client()
        bucket_name = os.getenv("S3_BUCKET_NAME", "ai-dilan")
        
        # Construct the S3 key
        s3_key = f"expert-avatars/{filename}"
        
        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        
        # Get content type
        content_type = response.get('ContentType', 'image/jpeg')
        
        # Create a streaming response
        def generate():
            for chunk in response['Body'].iter_chunks(chunk_size=8192):
                yield chunk
        
        return StreamingResponse(
            generate(),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Access-Control-Allow-Origin": "*",  # Allow CORS
            }
        )
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            raise HTTPException(status_code=404, detail="Image not found")
        else:
            raise HTTPException(status_code=500, detail=f"Error retrieving image: {error_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/avatar/full/{path:path}")
async def get_avatar_image_full_path(path: str):
    """
    Proxy endpoint to serve avatar images from S3 with full path
    """
    try:
        # Check if AWS credentials are configured
        aws_configured = (
            os.getenv("S3_ACCESS_KEY_ID") and 
            os.getenv("S3_ACCESS_KEY_ID") != "your_s3_access_key_id" and
            os.getenv("S3_SECRET_KEY") and 
            os.getenv("S3_SECRET_KEY") != "your_s3_secret_key" and
            os.getenv("S3_BUCKET_NAME") and 
            os.getenv("S3_BUCKET_NAME") != "your_s3_bucket_name"
        )
        
        if not aws_configured:
            # Return a default avatar or 404
            raise HTTPException(status_code=404, detail="AWS S3 not configured - avatar not available")
        
        s3_client = get_s3_client()
        bucket_name = os.getenv("S3_BUCKET_NAME", "ai-dilan")
        
        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=path)
        
        # Get content type
        content_type = response.get('ContentType', 'image/jpeg')
        
        # Create a streaming response
        def generate():
            for chunk in response['Body'].iter_chunks(chunk_size=8192):
                yield chunk
        
        return StreamingResponse(
            generate(),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Access-Control-Allow-Origin": "*",  # Allow CORS
            }
        )
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            raise HTTPException(status_code=404, detail="Image not found")
        elif error_code == 'InvalidAccessKeyId':
            raise HTTPException(status_code=404, detail="AWS credentials not configured")
        else:
            raise HTTPException(status_code=500, detail=f"Error retrieving image: {error_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
