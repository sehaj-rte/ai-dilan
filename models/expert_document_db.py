from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from config.database import Base
from datetime import datetime
import uuid

class ExpertDocumentDB(Base):
    """Junction table for expert-document relationships"""
    __tablename__ = "expert_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expert_id = Column(UUID(as_uuid=True), ForeignKey('experts.id'), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id'), nullable=False)
    
    # Processing status for this specific expert-document relationship
    processing_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    processing_error = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "expert_id": str(self.expert_id),
            "file_id": str(self.file_id),
            "processing_status": self.processing_status,
            "processing_error": self.processing_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
