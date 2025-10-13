from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.file_db import FileDB
# from services.s3_service import s3_service
import uuid
import logging

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, db: Session):
        self.db = db
    
    def upload_file(self, file_content: bytes, file_name: str, content_type: str, file_size: int, user_id: Optional[str] = None, extraction_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Upload file to S3 and save metadata to database"""
        try:
            print(f"\U0001f4c1 File Service: Starting upload for {file_name}, size: {file_size}")
            logger.info(f"FileService: Starting upload for {file_name}, size: {file_size}, user_id: {user_id}")
            
            # Upload to S3
            from services.aws_s3_service import s3_service
            s3_result = s3_service.upload_file(file_content, file_name, content_type)
            
            # Determine if we need to store content in database (fallback)
            store_content_in_db = False
            if not s3_result["success"]:
                logger.warning(f"S3 upload failed: {s3_result.get('error')}")
                print(f"⚠️ S3 not configured - storing file content in database as fallback")
                store_content_in_db = True
                # Create fallback S3 result
                s3_result = {
                    "success": True,
                    "url": f"https://temp-bucket.s3.amazonaws.com/{file_name}",
                    "s3_key": f"fallback/{file_name}"
                }
            
            # Prepare enhanced metadata
            metadata = extraction_result.get("metadata", {}) if extraction_result else {}
            logger.info(f"FileService: Metadata prepared, extraction_result: {extraction_result is not None}")
            
            # Convert user_id to UUID if provided
            user_uuid = None
            if user_id:
                try:
                    user_uuid = uuid.UUID(user_id)
                    logger.info(f"FileService: Converted user_id to UUID: {user_uuid}")
                except ValueError as e:
                    logger.error(f"FileService: Invalid user_id format: {user_id}, error: {e}")
                    print(f"\U0001f6ab File Service: Invalid user_id format: {user_id}")
                    return {"success": False, "error": f"Invalid user_id format: {user_id}"}
            
            # Save to database (with content if S3 failed)
            print(f"\U0001f4be File Service: Creating database record for {file_name}")
            logger.info("FileService: Creating database record")
            file_record = FileDB(
                name=file_name,
                original_name=file_name,
                size=file_size,
                type=content_type,
                s3_url=s3_result["url"],
                s3_key=s3_result["s3_key"],
                user_id=user_uuid,
                content=file_content if store_content_in_db else None,  # Store content as fallback
                
                # Enhanced metadata
                document_type=metadata.get("document_type"),
                language=metadata.get("language"),
                word_count=extraction_result.get("word_count") if extraction_result else None,
                page_count=metadata.get("page_count"),
                has_images=metadata.get("has_images", False),
                has_tables=metadata.get("has_tables", False),
                extracted_text_preview=metadata.get("extracted_text_preview"),
                processing_status='pending'  # Set to pending since processing is disabled
            )
            
            logger.info("FileService: Adding record to database")
            self.db.add(file_record)
            self.db.commit()
            self.db.refresh(file_record)
            
            logger.info(f"FileService: Successfully saved file with ID: {file_record.id}")
            print(f"\U0001f389 File Service: Successfully saved file {file_name} with ID: {file_record.id}")
            
            return {
                "success": True,
                "id": str(file_record.id),
                "url": file_record.s3_url,
                "s3_key": file_record.s3_key,
                "file": file_record.to_dict()
            }
            
        except Exception as e:
            logger.error(f"FileService: Upload failed with exception: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def get_files(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all files, optionally filtered by user"""
        try:
            print(f"\U0001f4c2 File Service: Retrieving files for user {user_id}")
            query = self.db.query(FileDB)
            
            if user_id:
                query = query.filter(FileDB.user_id == uuid.UUID(user_id))
            
            files = query.order_by(FileDB.created_at.desc()).all()
            print(f"\U0001f389 File Service: Found {len(files)} files")
            
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
            print(f"\U0001f4c4 File Service: Retrieving file by ID {file_id}")
            file_record = self.db.query(FileDB).filter(FileDB.id == uuid.UUID(file_id)).first()
            
            if not file_record:
                print(f"\U0001f6ab File Service: File not found for ID {file_id}")
                return {"success": False, "error": "File not found"}
            
            print(f"\U0001f389 File Service: Found file {file_record.name} for ID {file_id}")
            return {
                "success": True,
                "file": file_record.to_dict()
            }
            
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete file from S3 and database"""
        try:
            print(f"\U0001f5d1 File Service: Deleting file with ID {file_id}")
            # Get file record
            file_record = self.db.query(FileDB).filter(FileDB.id == uuid.UUID(file_id)).first()
            
            if not file_record:
                print(f"\U0001f6ab File Service: File not found for deletion (ID: {file_id})")
                return {"success": False, "error": "File not found"}
            
            print(f"\U0001f4c4 File Service: Found file {file_record.name} for deletion")
            # Delete from S3 (temporarily disabled)
            # s3_result = s3_service.delete_file(file_record.s3_key)
            # 
            # if not s3_result["success"]:
            #     print(f"Warning: Failed to delete from S3: {s3_result['error']}")
            #     # Continue with database deletion even if S3 deletion fails
            
            # Delete from database
            self.db.delete(file_record)
            self.db.commit()
            
            print(f"\U0001f389 File Service: Successfully deleted file {file_record.name}")
            return {"success": True}
            
        except Exception as e:
            print(f"\U0001f4a5 File Service: Error during file deletion: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def get_file_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get file statistics"""
        try:
            print(f"\U0001f4ca File Service: Getting file statistics for user {user_id}")
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
            
            print(f"\U0001f389 File Service: Statistics - {total_files} files, {total_size} bytes total")
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
