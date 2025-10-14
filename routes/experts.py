from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from config.database import get_db
from dependencies.auth import get_current_user_required
from models.expert import Expert, ExpertCreate, ExpertContent, ExpertResponse
from controllers.expert_controller import (
    create_expert, get_expert, list_experts, upload_expert_content, 
    ask_expert, update_expert, delete_expert, create_expert_with_elevenlabs,
    get_expert_from_db, list_experts_from_db, delete_expert_from_db
)
from controllers.knowledge_base_controller import process_expert_files
from services.expert_service import ExpertService
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ExpertCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    first_message: Optional[str] = None
    voice_id: str
    avatar_base64: Optional[str] = None  # Base64 encoded image data
    selected_files: List[str] = []

@router.post("/", response_model=dict)
async def create_new_expert(
    expert_data: ExpertCreateRequest, 
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Create a new expert with ElevenLabs integration"""
    expert_dict = expert_data.dict()
    expert_dict['user_id'] = current_user_id  # Set user_id from authenticated user
    result = await create_expert_with_elevenlabs(db, expert_dict)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result

@router.post("/legacy", response_model=dict)
def create_new_expert_legacy(expert_data: ExpertCreate):
    """Create a new expert (legacy method)"""
    result = create_expert(expert_data)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result

@router.get("/", response_model=dict)
def get_all_experts(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Get all experts for the current user"""
    result = list_experts_from_db(db, current_user_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    # Return the experts list directly, not the whole result dict
    return {
        "success": True,
        "experts": result.get("experts", [])
    }

@router.get("/legacy", response_model=dict)
def get_all_experts_legacy():
    """Get all experts (legacy method)"""
    result = list_experts()
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    return result

@router.get("/{expert_id}", response_model=dict)
def get_expert_by_id(
    expert_id: str, 
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Get expert by ID from database"""
    result = get_expert_from_db(db, expert_id, current_user_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    return result

@router.get("/legacy/{expert_id}", response_model=dict)
def get_expert_by_id_legacy(expert_id: str):
    """Get expert by ID (legacy method)"""
    result = get_expert(expert_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    return result

@router.post("/{expert_id}/content", response_model=dict)
def upload_content(expert_id: str, content_data: ExpertContent):
    """Upload content for an expert"""
    # Set the expert_id from the URL
    content_data.expert_id = expert_id
    
    result = upload_expert_content(content_data)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result

@router.post("/{expert_id}/ask", response_model=dict)
def ask_expert_question(expert_id: str, question_data: dict):
    """Ask a question to an expert"""
    question = question_data.get("question", "")
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is required"
        )
    
    result = ask_expert(expert_id, question)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result

@router.put("/{expert_id}", response_model=dict)
def update_expert_info(expert_id: str, update_data: dict):
    """Update expert information"""
    result = update_expert(expert_id, update_data)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    return result

@router.delete("/{expert_id}", response_model=dict)
async def delete_expert_by_id(
    expert_id: str, 
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Delete expert from database"""
    result = await delete_expert_from_db(db, expert_id, current_user_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    return result

@router.delete("/legacy/{expert_id}", response_model=dict)
def delete_expert_by_id_legacy(expert_id: str):
    """Delete an expert (legacy method)"""
    result = delete_expert(expert_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    return result

@router.post("/{expert_id}/process-files", response_model=dict)
async def process_expert_files_route(expert_id: str, file_ids: List[str], db: Session = Depends(get_db)):
    """Manually trigger file processing for an expert"""
    try:
        # Get expert to retrieve agent_id
        expert_service = ExpertService(db)
        expert_result = expert_service.get_expert(expert_id)
        
        if not expert_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expert not found"
            )
        
        expert = expert_result["expert"]
        agent_id = expert.get("elevenlabs_agent_id")
        
        if not agent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expert does not have an associated ElevenLabs agent"
            )
        
        # Process the files
        result = await process_expert_files(
            expert_id=expert_id,
            agent_id=agent_id,
            selected_files=file_ids,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing expert files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
