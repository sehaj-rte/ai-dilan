from sqlalchemy import Column, String, DateTime, UUID, ForeignKey
from sqlalchemy.sql import func
from config.database import Base
import uuid

class FolderDB(Base):
    __tablename__ = "folders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # User who owns the folder
    agent_id = Column(String, ForeignKey('experts.id'), nullable=True)  # Agent isolation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "user_id": str(self.user_id) if self.user_id else None,
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
