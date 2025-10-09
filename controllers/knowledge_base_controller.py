from typing import Dict, Any
from fastapi import UploadFile, HTTPException
from services.file_service import FileService
from sqlalchemy.orm import Session

def upload_file(file: UploadFile, db: Session, user_id: str = None) -> Dict[str, Any]:
    """Upload file to knowledge base"""
    try:
        # Validate file
        if not file.filename:
            return {"success": False, "error": "No file provided"}
        
        # Check file size (limit to 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        file_content = file.file.read()
        
        if len(file_content) > max_size:
            return {"success": False, "error": "File size exceeds 50MB limit"}
        
        if len(file_content) == 0:
            return {"success": False, "error": "File is empty"}
        
        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/csv',
            'image/jpeg',
            'image/png',
            'image/gif',
            'audio/mpeg',
            'audio/wav',
            'video/mp4',
            'video/avi'
        ]
        
        if file.content_type not in allowed_types:
            return {"success": False, "error": f"File type '{file.content_type}' not supported"}
        
        # Upload file
        file_service = FileService(db)
        result = file_service.upload_file(
            file_content=file_content,
            file_name=file.filename,
            content_type=file.content_type,
            file_size=len(file_content),
            user_id=user_id
        )
        
        return result
        
    except Exception as e:
        return {"success": False, "error": f"Upload failed: {str(e)}"}

def get_files(db: Session, user_id: str = None) -> Dict[str, Any]:
    """Get all uploaded files"""
    try:
        file_service = FileService(db)
        return file_service.get_files(user_id=user_id)
        
    except Exception as e:
        return {"success": False, "error": f"Failed to retrieve files: {str(e)}"}

def get_file_by_id(file_id: str, db: Session) -> Dict[str, Any]:
    """Get file by ID"""
    try:
        file_service = FileService(db)
        return file_service.get_file_by_id(file_id)
        
    except Exception as e:
        return {"success": False, "error": f"Failed to retrieve file: {str(e)}"}

def delete_file(file_id: str, db: Session) -> Dict[str, Any]:
    """Delete file from knowledge base"""
    try:
        file_service = FileService(db)
        return file_service.delete_file(file_id)
        
    except Exception as e:
        return {"success": False, "error": f"Failed to delete file: {str(e)}"}

def get_file_stats(db: Session, user_id: str = None) -> Dict[str, Any]:
    """Get file statistics"""
    try:
        file_service = FileService(db)
        return file_service.get_file_stats(user_id=user_id)
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get statistics: {str(e)}"}
