from sqlalchemy.orm import Session
from models.expert_db import ExpertDB
from typing import Dict, Any, Optional, List
import uuid
import logging
import os
import re

logger = logging.getLogger(__name__)

class ExpertService:
    def __init__(self, db: Session):
        self.db = db
    
    def _convert_s3_url_to_proxy(self, s3_url: str) -> str:
        """
        Convert S3 URL to proxy URL for public access
        
        Args:
            s3_url: Original S3 URL
            
        Returns:
            Proxy URL that goes through our backend
        """
        if not s3_url:
            return s3_url
        
        # Extract the S3 key from the URL
        # Format: https://bucket.s3.region.amazonaws.com/key
        bucket_name = os.getenv("S3_BUCKET_NAME", "ai-dilan")
        pattern = rf"https://{bucket_name}\.s3\.[^/]+\.amazonaws\.com/(.+)"
        match = re.match(pattern, s3_url)
        
        if match:
            s3_key = match.group(1)
            # Return proxy URL
            return f"http://localhost:8000/images/avatar/full/{s3_key}"
        
        return s3_url
    
    def _process_expert_dict(self, expert_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process expert dictionary to convert S3 URLs to proxy URLs
        
        Args:
            expert_dict: Expert dictionary from database
            
        Returns:
            Processed expert dictionary with proxy URLs
        """
        if expert_dict.get("avatar_url"):
            expert_dict["avatar_url"] = self._convert_s3_url_to_proxy(expert_dict["avatar_url"])
        
        return expert_dict
    
    def create_expert(self, expert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new expert in the database
        
        Args:
            expert_data: Dictionary containing expert information
            
        Returns:
            Dict containing success status and expert data
        """
        try:
            expert = ExpertDB(
                name=expert_data.get("name"),
                description=expert_data.get("description"),
                system_prompt=expert_data.get("system_prompt"),
                voice_id=expert_data.get("voice_id"),
                elevenlabs_agent_id=expert_data.get("elevenlabs_agent_id"),
                avatar_url=expert_data.get("avatar_url"),
                pinecone_index_name=expert_data.get("pinecone_index_name"),
                selected_files=expert_data.get("selected_files", []),
                knowledge_base_tool_id=expert_data.get("knowledge_base_tool_id")
            )
            
            self.db.add(expert)
            self.db.commit()
            self.db.refresh(expert)
            
            logger.info(f"Successfully created expert: {expert.id}")
            return {
                "success": True,
                "expert": self._process_expert_dict(expert.to_dict())
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating expert: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to create expert: {str(e)}"
            }
    
    def get_expert(self, expert_id: str) -> Dict[str, Any]:
        """
        Get expert by ID
        
        Args:
            expert_id: The expert ID
            
        Returns:
            Dict containing success status and expert data
        """
        try:
            expert = self.db.query(ExpertDB).filter(ExpertDB.id == expert_id).first()
            
            if not expert:
                return {
                    "success": False,
                    "error": "Expert not found"
                }
            
            return {
                "success": True,
                "expert": expert.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error getting expert: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get expert: {str(e)}"
            }
    
    def get_expert_by_agent_id(self, agent_id: str) -> Dict[str, Any]:
        """
        Get expert by ElevenLabs agent ID
        
        Args:
            agent_id: The ElevenLabs agent ID
            
        Returns:
            Dict containing success status and expert data
        """
        try:
            expert = self.db.query(ExpertDB).filter(ExpertDB.elevenlabs_agent_id == agent_id).first()
            
            if not expert:
                return {
                    "success": False,
                    "error": "Expert not found"
                }
            
            return {
                "success": True,
                "expert": expert.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error getting expert by agent ID: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get expert: {str(e)}"
            }
    
    def list_experts(self, user_id: Optional[str] = None, active_only: bool = True) -> Dict[str, Any]:
        """
        List all experts
        
        Args:
            user_id: Optional user ID to filter experts (for future use)
            active_only: Whether to return only active experts
            
        Returns:
            Dict containing success status and list of experts
        """
        try:
            query = self.db.query(ExpertDB)
            
            if active_only:
                query = query.filter(ExpertDB.is_active == True)
            
            experts = query.all()
            
            return {
                "success": True,
                "experts": [expert.to_dict() for expert in experts]
            }
            
        except Exception as e:
            logger.error(f"Error listing experts: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to list experts: {str(e)}"
            }
    
    def update_expert(self, expert_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update expert information
        
        Args:
            expert_id: The expert ID
            update_data: Dictionary containing fields to update
            
        Returns:
            Dict containing success status and updated expert data
        """
        try:
            expert = self.db.query(ExpertDB).filter(ExpertDB.id == expert_id).first()
            
            if not expert:
                return {
                    "success": False,
                    "error": "Expert not found"
                }
            
            # Update allowed fields
            allowed_fields = [
                "name", "description", "system_prompt", "voice_id", 
                "elevenlabs_agent_id", "avatar_url", "pinecone_index_name",
                "selected_files", "knowledge_base_tool_id", "is_active"
            ]
            
            for field in allowed_fields:
                if field in update_data:
                    setattr(expert, field, update_data[field])
            
            self.db.commit()
            self.db.refresh(expert)
            
            logger.info(f"Successfully updated expert: {expert_id}")
            return {
                "success": True,
                "expert": expert.to_dict()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating expert: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to update expert: {str(e)}"
            }
    
    def delete_expert(self, expert_id: str) -> Dict[str, Any]:
        """
        Delete expert (soft delete by setting is_active to False)
        
        Args:
            expert_id: The expert ID
            
        Returns:
            Dict containing success status
        """
        try:
            expert = self.db.query(ExpertDB).filter(ExpertDB.id == expert_id).first()
            
            if not expert:
                return {
                    "success": False,
                    "error": "Expert not found"
                }
            
            expert.is_active = False
            self.db.commit()
            
            logger.info(f"Successfully deleted expert: {expert_id}")
            return {
                "success": True,
                "message": "Expert deleted successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting expert: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to delete expert: {str(e)}"
            }
