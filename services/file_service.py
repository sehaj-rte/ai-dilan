from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.file_db import FileDB
from services.s3_service import s3_service
import uuid

class FileService:
    def __init__(self, db: Session):
        self.db = db
    
    def upload_file(self, file_content: bytes, file_name: str, content_type: str, file_size: int, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Upload file to S3 and save metadata to database"""
        try:
            # Upload to S3
            s3_result = s3_service.upload_file(file_content, file_name, content_type)
            
            if not s3_result["success"]:
                return s3_result
            
            # Save to database
            file_record = FileDB(
                name=file_name,
                original_name=file_name,
                size=file_size,
                type=content_type,
                s3_url=s3_result["url"],
                s3_key=s3_result["s3_key"],
                user_id=uuid.UUID(user_id) if user_id else None
            )
            
            self.db.add(file_record)
            self.db.commit()
            self.db.refresh(file_record)
            
            return {
                "success": True,
                "id": str(file_record.id),
                "url": file_record.s3_url,
                "s3_key": file_record.s3_key,
                "file": file_record.to_dict()
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def get_files(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all files, optionally filtered by user"""
        try:
            query = self.db.query(FileDB)
            
            if user_id:
                query = query.filter(FileDB.user_id == uuid.UUID(user_id))
            
            files = query.order_by(FileDB.created_at.desc()).all()
            
            return {
                "success": True,
                "files": [file.to_dict() for file in files],
                "total": len(files)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def get_file_by_id(self, file_id: str) -> Dict[str, Any]:
        """Get file by ID"""
        try:
            file_record = self.db.query(FileDB).filter(FileDB.id == uuid.UUID(file_id)).first()
            
            if not file_record:
                return {"success": False, "error": "File not found"}
            
            return {
                "success": True,
                "file": file_record.to_dict()
            }
            
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete file from S3 and database"""
        try:
            # Get file record
            file_record = self.db.query(FileDB).filter(FileDB.id == uuid.UUID(file_id)).first()
            
            if not file_record:
                return {"success": False, "error": "File not found"}
            
            # Delete from S3
            s3_result = s3_service.delete_file(file_record.s3_key)
            
            if not s3_result["success"]:
                print(f"Warning: Failed to delete from S3: {s3_result['error']}")
                # Continue with database deletion even if S3 deletion fails
            
            # Delete from database
            self.db.delete(file_record)
            self.db.commit()
            
            return {"success": True}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def get_file_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get file statistics"""
        try:
            query = self.db.query(FileDB)
            
            if user_id:
                query = query.filter(FileDB.user_id == uuid.UUID(user_id))
            
            files = query.all()
            
            total_files = len(files)
            total_size = sum(file.size for file in files)
            
            # Group by file type
            type_stats = {}
            for file in files:
                file_type = file.type.split('/')[0] if '/' in file.type else file.type
                if file_type not in type_stats:
                    type_stats[file_type] = {"count": 0, "size": 0}
                type_stats[file_type]["count"] += 1
                type_stats[file_type]["size"] += file.size
            
            return {
                "success": True,
                "stats": {
                    "total_files": total_files,
                    "total_size": total_size,
                    "type_breakdown": type_stats
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}
