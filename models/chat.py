from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

def create_chat_message_model():
    """Chat message model"""
    class ChatMessage(BaseModel):
        id: Optional[str] = None
        user_id: str
        expert_id: str
        message: str
        response: Optional[str] = None
        message_type: str = "text"  # "text", "voice"
        timestamp: Optional[datetime] = None
        
    return ChatMessage

def create_chat_request_model():
    """Chat request model"""
    class ChatRequest(BaseModel):
        expert_id: str
        message: str
        message_type: str = "text"
        user_id: Optional[str] = None
        
    return ChatRequest

def create_chat_response_model():
    """Chat response model"""
    class ChatResponse(BaseModel):
        message_id: str
        expert_id: str
        expert_name: str
        response: str
        response_type: str = "text"
        confidence: float
        timestamp: datetime
        
    return ChatResponse

def create_chat_history_model():
    """Chat history model"""
    class ChatHistory(BaseModel):
        expert_id: str
        messages: List[dict]
        total_messages: int
        
    return ChatHistory

# Create model instances
ChatMessage = create_chat_message_model()
ChatRequest = create_chat_request_model()
ChatResponse = create_chat_response_model()
ChatHistory = create_chat_history_model()
