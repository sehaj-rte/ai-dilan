from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from config.database import Base
from datetime import datetime
import uuid

class FileDB(Base):
    __tablename__ = "files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    type = Column(String(100), nullable=False)
    s3_url = Column(Text, nullable=False)
    s3_key = Column(String(500), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Optional user association
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "original_name": self.original_name,
            "size": self.size,
            "type": self.type,
            "url": self.s3_url,
            "s3_key": self.s3_key,
            "user_id": str(self.user_id) if self.user_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
