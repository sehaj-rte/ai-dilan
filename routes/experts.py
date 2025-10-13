from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from config.database import get_db
from models.expert import Expert, ExpertCreate, ExpertContent, ExpertResponse
from controllers.expert_controller import (
    create_expert, get_expert, list_experts, upload_expert_content, 
    ask_expert, update_expert, delete_expert, create_expert_with_elevenlabs,
    get_expert_from_db, list_experts_from_db, delete_expert_from_db
)
from pydantic import BaseModel

router = APIRouter()

class ExpertCreateRequest(BaseModel):
    name: str
    description: str = None
    system_prompt: str
    voice_id: str
    avatar_base64: str = None  # Base64 encoded image data
    selected_files: List[str] = []
    user_id: str = "default_user"  # TODO: Get from authentication token

@router.post("/", response_model=dict)
async def create_new_expert(expert_data: ExpertCreateRequest, db: Session = Depends(get_db)):
    """Create a new expert with ElevenLabs integration"""
    expert_dict = expert_data.dict()
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
def get_all_experts(db: Session = Depends(get_db)):
    """Get all experts from database"""
    result = list_experts_from_db(db)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    return result

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
def get_expert_by_id(expert_id: str, db: Session = Depends(get_db)):
    """Get expert by ID from database"""
    result = get_expert_from_db(db, expert_id)
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
async def delete_expert_by_id(expert_id: str, db: Session = Depends(get_db)):
    """Delete an expert and cleanup all associated resources"""
    result = await delete_expert_from_db(db, expert_id)
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
