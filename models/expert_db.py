from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from config.database import Base
import uuid

class ExpertDB(Base):
    __tablename__ = "experts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    voice_id = Column(String(255), nullable=True)
    elevenlabs_agent_id = Column(String(255), nullable=True, unique=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Knowledge base configuration
    pinecone_index_name = Column(String(255), nullable=True)  # Expert's dedicated Pinecone index
    selected_files = Column(JSON, nullable=True)  # Store file IDs as JSON array
    knowledge_base_tool_id = Column(String(255), nullable=True)  # ElevenLabs tool ID
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "voice_id": self.voice_id,
            "elevenlabs_agent_id": self.elevenlabs_agent_id,
            "avatar_url": self.avatar_url,
            
            # Knowledge base info
            "pinecone_index_name": self.pinecone_index_name,
            "selected_files": self.selected_files,
            "knowledge_base_tool_id": self.knowledge_base_tool_id,
            
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
