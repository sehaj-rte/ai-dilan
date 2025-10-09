from fastapi import APIRouter, HTTPException, status
from models.chat import ChatRequest, ChatResponse, ChatHistory
from controllers.chat_controller import send_message, get_chat_history

router = APIRouter()

@router.post("/{expert_id}", response_model=dict)
def chat_with_expert(expert_id: str, chat_data: ChatRequest):
    """Send a message to an expert"""
    # Set expert_id from URL
    chat_data.expert_id = expert_id
    
    result = send_message(chat_data)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result

@router.get("/{expert_id}/history", response_model=dict)
def get_expert_chat_history(expert_id: str, user_id: str = None):
    """Get chat history with an expert"""
    result = get_chat_history(expert_id, user_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    return result

@router.delete("/{expert_id}/history", response_model=dict)
def clear_chat_history(expert_id: str, user_id: str = None):
    """Clear chat history with an expert"""
    return {
        "success": True,
        "message": "Chat history cleared (not implemented yet)"
    }
