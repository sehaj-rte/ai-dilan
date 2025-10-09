from fastapi import APIRouter, HTTPException, status, Depends
from controllers.conversation_controller import get_conversation_signed_url
from config.database import get_db
from sqlalchemy.orm import Session
from typing import Optional

router = APIRouter()

@router.get("/signed-url/{expert_id}", response_model=dict)
async def get_signed_url_for_expert(
    expert_id: str,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a signed URL for WebSocket conversation with an expert
    
    Args:
        expert_id: The expert ID to get conversation access for
        user_id: Optional user ID for authentication/logging
        
    Returns:
        Dict containing signed URL for WebSocket connection
    """
    result = await get_conversation_signed_url(db, expert_id, user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/health", response_model=dict)
async def conversation_health_check():
    """Health check endpoint for conversation service"""
    return {
        "success": True,
        "message": "Conversation service is healthy",
        "service": "ElevenLabs WebSocket Conversations"
    }
