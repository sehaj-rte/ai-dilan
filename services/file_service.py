from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.file_db import FileDB
from models.folder_db import FolderDB
# from services.s3_service import s3_service
import uuid
import logging

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, db: Session):
        self.db = db
    
    def upload_file(self, file_content: bytes, file_name: str, content_type: str, file_size: int, user_id: Optional[str] = None, extraction_result: Optional[Dict[str, Any]] = None, folder_id: Optional[str] = None, folder: str = "Uncategorized") -> Dict[str, Any]:
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
            
            # Resolve folder_id
            folder_uuid = None
            if folder_id:
                try:
                    folder_uuid = uuid.UUID(folder_id)
                    # Verify folder exists
                    folder_exists = self.db.query(FolderDB).filter(FolderDB.id == folder_uuid).first()
                    if not folder_exists:
                        logger.error(f"FileService: Folder with ID {folder_id} not found")
                        return {"success": False, "error": f"Folder with ID {folder_id} not found"}
                    folder = folder_exists.name  # Update folder name for backward compatibility
                    logger.info(f"FileService: Using folder_id: {folder_uuid}, name: {folder}")
                except ValueError as e:
                    logger.error(f"FileService: Invalid folder_id format: {folder_id}, error: {e}")
                    return {"success": False, "error": f"Invalid folder_id format: {folder_id}"}
            else:
                # If no folder_id provided, try to find or create "Uncategorized" folder
                uncategorized_folder = self.db.query(FolderDB).filter(FolderDB.name == "Uncategorized").first()
                if uncategorized_folder:
                    folder_uuid = uncategorized_folder.id
                    logger.info(f"FileService: Using existing Uncategorized folder: {folder_uuid}")
                else:
                    # Create Uncategorized folder if it doesn't exist
                    uncategorized_folder = FolderDB(name="Uncategorized", user_id=user_uuid)
                    self.db.add(uncategorized_folder)
                    self.db.flush()  # Get the ID without committing
                    folder_uuid = uncategorized_folder.id
                    logger.info(f"FileService: Created new Uncategorized folder: {folder_uuid}")
            
            # Determine processing status based on extraction result
            # If extraction was successful, mark as completed
            # Otherwise, mark as pending (for files that need processing)
            processing_status = 'completed' if (extraction_result and extraction_result.get("success")) else 'pending'
            
            # Save to database (with content if S3 failed)
            print(f"\U0001f4be File Service: Creating database record for {file_name} in folder: {folder}")
            logger.info(f"FileService: Creating database record with status: {processing_status}, folder: {folder}")
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
                folder_id=folder_uuid,  # Set folder ID (primary)
                folder=folder,  # Set folder/category (backward compatibility)
                document_type=metadata.get("document_type"),
                language=metadata.get("language"),
                word_count=extraction_result.get("word_count") if extraction_result else None,
                page_count=metadata.get("page_count"),
                has_images=metadata.get("has_images", False),
                has_tables=metadata.get("has_tables", False),
                extracted_text=extraction_result.get("text") if extraction_result and extraction_result.get("success") else None,
                extracted_text_preview=metadata.get("extracted_text_preview"),
                processing_status=processing_status  # Set based on extraction success
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
            
            # Convert to dict but exclude full extracted_text for performance
            files_list = []
            for file in files:
                file_dict = file.to_dict()
                # Remove full extracted_text to improve performance (keep only preview)
                file_dict.pop('extracted_text', None)
                files_list.append(file_dict)
            
            return {
                "success": True,
                "files": files_list,
                "total": len(files)
            }
            
        except Exception as e:
            print(f"❌ Error in get_files: {str(e)}")
            import traceback
            traceback.print_exc()
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
    
    def get_folders(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all folders with file counts"""
        try:
            # Get all folders from folders table
            folders_query = self.db.query(FolderDB)
            if user_id:
                folders_query = folders_query.filter(FolderDB.user_id == uuid.UUID(user_id))
            
            all_folders = folders_query.all()
            
            # Get file counts for each folder using folder_id
            files_query = self.db.query(FileDB.folder_id, func.count(FileDB.id).label('count'))
            if user_id:
                files_query = files_query.filter(FileDB.user_id == uuid.UUID(user_id))
            
            file_counts = dict(files_query.group_by(FileDB.folder_id).all())
            
            # Combine folders with their counts
            folder_list = []
            for folder in all_folders:
                folder_list.append({
                    "id": str(folder.id),
                    "name": folder.name,
                    "count": file_counts.get(folder.id, 0)
                })
            
            # Sort: Uncategorized last, others alphabetically
            folder_list.sort(key=lambda x: (x["name"] == "Uncategorized", x["name"]))
            
            return {
                "success": True,
                "folders": folder_list,
                "total": len(folder_list)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def create_folder(self, folder_name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new folder"""
        try:
            if not folder_name or folder_name.strip() == "":
                return {"success": False, "error": "Folder name cannot be empty"}
            
            trimmed_name = folder_name.strip()
            
            # Check if folder already exists
            query = self.db.query(FolderDB).filter(FolderDB.name == trimmed_name)
            if user_id:
                query = query.filter(FolderDB.user_id == uuid.UUID(user_id))
            else:
                query = query.filter(FolderDB.user_id.is_(None))
            
            existing_folder = query.first()
            if existing_folder:
                return {"success": False, "error": f"Folder '{trimmed_name}' already exists"}
            
            # Create new folder
            user_uuid = None
            if user_id:
                try:
                    user_uuid = uuid.UUID(user_id)
                except ValueError:
                    return {"success": False, "error": "Invalid user_id format"}
            
            new_folder = FolderDB(
                name=trimmed_name,
                user_id=user_uuid
            )
            
            self.db.add(new_folder)
            self.db.commit()
            self.db.refresh(new_folder)
            
            return {
                "success": True,
                "message": f"Folder '{trimmed_name}' created successfully",
                "folder": new_folder.to_dict()
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def rename_folder(self, old_name: str, new_name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Rename a folder (updates all files in that folder)"""
        try:
            if old_name == "Uncategorized":
                return {"success": False, "error": "Cannot rename Uncategorized folder"}
            
            if not new_name or new_name.strip() == "":
                return {"success": False, "error": "New folder name cannot be empty"}
            
            query = self.db.query(FileDB).filter(FileDB.folder == old_name)
            
            if user_id:
                query = query.filter(FileDB.user_id == uuid.UUID(user_id))
            
            files = query.all()
            
            if not files:
                return {"success": False, "error": "Folder not found"}
            
            for file in files:
                file.folder = new_name.strip()
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Renamed folder '{old_name}' to '{new_name}'",
                "files_updated": len(files)
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def delete_folder(self, folder_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Delete a folder (moves all files to Uncategorized)"""
        try:
            # Validate folder_id
            try:
                folder_uuid = uuid.UUID(folder_id)
            except ValueError:
                return {"success": False, "error": f"Invalid folder_id format: {folder_id}"}
            
            # Get folder to check if it's Uncategorized
            folder_record = self.db.query(FolderDB).filter(FolderDB.id == folder_uuid).first()
            if not folder_record:
                return {"success": False, "error": "Folder not found"}
            
            if folder_record.name == "Uncategorized":
                return {"success": False, "error": "Cannot delete Uncategorized folder"}
            
            # Get Uncategorized folder for moving files
            uncategorized_folder = self.db.query(FolderDB).filter(FolderDB.name == "Uncategorized").first()
            if not uncategorized_folder:
                return {"success": False, "error": "Uncategorized folder not found"}
            
            # Find all files in this folder
            query = self.db.query(FileDB).filter(FileDB.folder_id == folder_uuid)
            if user_id:
                query = query.filter(FileDB.user_id == uuid.UUID(user_id))
            
            files = query.all()
            
            # Move files to Uncategorized
            for file in files:
                file.folder_id = uncategorized_folder.id
                file.folder = "Uncategorized"  # Update for backward compatibility
            
            # Delete the folder record
            self.db.delete(folder_record)
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Deleted folder '{folder_record.name}', moved {len(files)} files to Uncategorized",
                "files_moved": len(files)
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def move_file_to_folder(self, file_id: str, folder_id: str) -> Dict[str, Any]:
        """Move a file to a different folder using folder_id"""
        try:
            file_record = self.db.query(FileDB).filter(FileDB.id == uuid.UUID(file_id)).first()
            
            if not file_record:
                return {"success": False, "error": "File not found"}
            
            # Validate folder_id and get folder
            if not folder_id:
                # Default to Uncategorized
                uncategorized_folder = self.db.query(FolderDB).filter(FolderDB.name == "Uncategorized").first()
                if not uncategorized_folder:
                    return {"success": False, "error": "Uncategorized folder not found"}
                folder_uuid = uncategorized_folder.id
                folder_name = "Uncategorized"
            else:
                try:
                    folder_uuid = uuid.UUID(folder_id)
                    folder_record = self.db.query(FolderDB).filter(FolderDB.id == folder_uuid).first()
                    if not folder_record:
                        return {"success": False, "error": f"Folder with ID {folder_id} not found"}
                    folder_name = folder_record.name
                except ValueError:
                    return {"success": False, "error": f"Invalid folder_id format: {folder_id}"}
            
            old_folder = file_record.folder
            file_record.folder_id = folder_uuid
            file_record.folder = folder_name  # Update for backward compatibility
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Moved file from '{old_folder}' to '{folder_name}'",
                "file": file_record.to_dict()
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"Database error: {str(e)}"}
