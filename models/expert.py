from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

def create_expert_model():
    """Expert profile model"""
    class Expert(BaseModel):
        id: Optional[str] = None
        name: str
        role: str
        bio: Optional[str] = None
        image_url: Optional[str] = None
        voice_id: Optional[str] = None
        knowledge_base_id: Optional[str] = None
        is_active: bool = True
        created_at: Optional[datetime] = None
        
    return Expert

def create_expert_create_model():
    """Expert creation model"""
    class ExpertCreate(BaseModel):
        name: str
        role: str
        bio: Optional[str] = None
        image_url: Optional[str] = None
        
    return ExpertCreate

def create_expert_content_model():
    """Expert content upload model"""
    class ExpertContent(BaseModel):
        expert_id: str
        content_type: str  # "text", "audio", "video", "document"
        content: str
        metadata: Optional[dict] = None
        
    return ExpertContent

def create_expert_response_model():
    """Expert response model"""
    class ExpertResponse(BaseModel):
        expert_id: str
        question: str
        answer: str
        confidence: float
        sources: Optional[List[str]] = None
        
    return ExpertResponse

# Create model instances
Expert = create_expert_model()
ExpertCreate = create_expert_create_model()
ExpertContent = create_expert_content_model()
ExpertResponse = create_expert_response_model()
