from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.folder_db import FolderDB
from models.file_db import FileDB
import uuid
import logging

logger = logging.getLogger(__name__)

class FolderService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_folder(self, name: str, user_id: Optional[str] = None, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new folder with agent isolation"""
        try:
            # Convert user_id to UUID if provided
            user_uuid = None
            if user_id:
                try:
                    user_uuid = uuid.UUID(user_id)
                except ValueError as e:
                    logger.error(f"Invalid user_id format: {user_id}, error: {e}")
                    return {"success": False, "error": f"Invalid user_id format: {user_id}"}
            
            # Check if folder already exists for this agent
            existing_folder = self.db.query(FolderDB).filter(
                FolderDB.name == name,
                FolderDB.agent_id == agent_id
            ).first()
            
            if existing_folder:
                return {"success": False, "error": f"Folder '{name}' already exists for this agent"}
            
            # Create new folder
            folder = FolderDB(
                name=name,
                user_id=user_uuid,
                agent_id=agent_id
            )
            
            self.db.add(folder)
            self.db.commit()
            self.db.refresh(folder)
            
            logger.info(f"Created folder '{name}' with ID: {folder.id} for agent: {agent_id}")
            
            return {
                "success": True,
                "folder": folder.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to create folder: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": f"Failed to create folder: {str(e)}"}
    
    def get_folders(self, user_id: Optional[str] = None, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get folders with agent isolation"""
        try:
            query = self.db.query(FolderDB)
            
            # Filter by user
            if user_id:
                query = query.filter(FolderDB.user_id == uuid.UUID(user_id))
            
            # Filter by agent (for agent isolation)
            if agent_id:
                query = query.filter(FolderDB.agent_id == agent_id)
            else:
                # If no agent_id specified, only show global folders
                query = query.filter(FolderDB.agent_id.is_(None))
            
            folders = query.order_by(FolderDB.name).all()
            
            # Get file counts for each folder
            folder_data = []
            for folder in folders:
                file_count = self.db.query(func.count(FileDB.id)).filter(
                    FileDB.folder_id == folder.id
                ).scalar()
                
                folder_dict = folder.to_dict()
                folder_dict["file_count"] = file_count
                folder_data.append(folder_dict)
            
            logger.info(f"Retrieved {len(folder_data)} folders for agent: {agent_id}")
            
            return {
                "success": True,
                "folders": folder_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get folders: {str(e)}")
            return {"success": False, "error": f"Failed to get folders: {str(e)}"}
    
    def update_folder(self, folder_id: str, name: str, user_id: Optional[str] = None, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Update folder name with agent isolation"""
        try:
            folder_uuid = uuid.UUID(folder_id)
            
            # Find folder with agent isolation
            query = self.db.query(FolderDB).filter(FolderDB.id == folder_uuid)
            
            if agent_id:
                query = query.filter(FolderDB.agent_id == agent_id)
            
            folder = query.first()
            
            if not folder:
                return {"success": False, "error": "Folder not found or access denied"}
            
            # Check if new name conflicts with existing folder for this agent
            existing_folder = self.db.query(FolderDB).filter(
                FolderDB.name == name,
                FolderDB.agent_id == agent_id,
                FolderDB.id != folder_uuid
            ).first()
            
            if existing_folder:
                return {"success": False, "error": f"Folder '{name}' already exists for this agent"}
            
            folder.name = name
            self.db.commit()
            self.db.refresh(folder)
            
            logger.info(f"Updated folder {folder_id} to name '{name}' for agent: {agent_id}")
            
            return {
                "success": True,
                "folder": folder.to_dict()
            }
            
        except ValueError:
            return {"success": False, "error": "Invalid folder ID format"}
        except Exception as e:
            logger.error(f"Failed to update folder: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": f"Failed to update folder: {str(e)}"}
    
    def delete_folder(self, folder_id: str, user_id: Optional[str] = None, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Delete folder with agent isolation"""
        try:
            folder_uuid = uuid.UUID(folder_id)
            
            # Find folder with agent isolation
            query = self.db.query(FolderDB).filter(FolderDB.id == folder_uuid)
            
            if agent_id:
                query = query.filter(FolderDB.agent_id == agent_id)
            
            folder = query.first()
            
            if not folder:
                return {"success": False, "error": "Folder not found or access denied"}
            
            # Check if folder has files
            file_count = self.db.query(func.count(FileDB.id)).filter(
                FileDB.folder_id == folder_uuid
            ).scalar()
            
            if file_count > 0:
                return {"success": False, "error": f"Cannot delete folder '{folder.name}' - it contains {file_count} files"}
            
            self.db.delete(folder)
            self.db.commit()
            
            logger.info(f"Deleted folder '{folder.name}' (ID: {folder_id}) for agent: {agent_id}")
            
            return {"success": True, "message": f"Folder '{folder.name}' deleted successfully"}
            
        except ValueError:
            return {"success": False, "error": "Invalid folder ID format"}
        except Exception as e:
            logger.error(f"Failed to delete folder: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": f"Failed to delete folder: {str(e)}"}
    
    def get_folder_by_id(self, folder_id: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get folder by ID with agent isolation"""
        try:
            folder_uuid = uuid.UUID(folder_id)
            
            query = self.db.query(FolderDB).filter(FolderDB.id == folder_uuid)
            
            if agent_id:
                query = query.filter(FolderDB.agent_id == agent_id)
            
            folder = query.first()
            
            if not folder:
                return {"success": False, "error": "Folder not found or access denied"}
            
            # Get file count
            file_count = self.db.query(func.count(FileDB.id)).filter(
                FileDB.folder_id == folder_uuid
            ).scalar()
            
            folder_dict = folder.to_dict()
            folder_dict["file_count"] = file_count
            
            return {
                "success": True,
                "folder": folder_dict
            }
            
        except ValueError:
            return {"success": False, "error": "Invalid folder ID format"}
        except Exception as e:
            logger.error(f"Failed to get folder: {str(e)}")
            return {"success": False, "error": f"Failed to get folder: {str(e)}"}
