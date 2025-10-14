from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, LargeBinary
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
    user_id = Column(UUID(as_uuid=True), nullable=True)
    content = Column(LargeBinary, nullable=True)  # Fallback storage when S3 not configured
    
    # Enhanced metadata fields
    description = Column(Text, nullable=True)  # User-provided description
    tags = Column(JSON, nullable=True)  # Array of tags for categorization
    folder = Column(String(255), default="Uncategorized", nullable=False)  # Folder/category name
    document_type = Column(String(50), nullable=True)  # auto-detected: pdf, docx, image, etc.
    language = Column(String(10), nullable=True)  # detected language
    word_count = Column(Integer, nullable=True)  # extracted word count
    page_count = Column(Integer, nullable=True)  # for PDFs
    
    # Processing status
    processing_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)  # error message if processing failed
    
    # Content metadata
    extracted_text = Column(Text, nullable=True)  # Full extracted text content
    extracted_text_preview = Column(Text, nullable=True)  # First 500 chars for preview
    has_images = Column(Boolean, default=False)  # contains images
    has_tables = Column(Boolean, default=False)  # contains tables
    
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
            
            # Enhanced metadata
            "description": self.description,
            "tags": self.tags or [],
            "folder": self.folder,
            "document_type": self.document_type,
            "language": self.language,
            "word_count": self.word_count,
            "page_count": self.page_count,
            
            # Processing info
            "processing_status": self.processing_status,
            "processing_error": self.processing_error,
            
            # Content metadata
            "extracted_text": self.extracted_text,
            "extracted_text_preview": self.extracted_text_preview,
            "has_images": self.has_images,
            "has_tables": self.has_tables,
            
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_summary_dict(self):
        """Lightweight version for document selection (excludes full extracted_text for performance)"""
        return {
            "id": str(self.id),
            "name": self.name,
            "original_name": self.original_name,
            "type": self.type,
            "document_type": self.document_type,
            "size": self.size,
            "word_count": self.word_count,
            "page_count": self.page_count,
            "description": self.description,
            "tags": self.tags or [],
            "folder": self.folder,
            "processing_status": self.processing_status,
            "processing_error": self.processing_error,
            "url": self.url,
            "s3_key": self.s3_key,
            "has_images": self.has_images,
            "has_tables": self.has_tables,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # Only include preview, not full text for performance
            "extracted_text_preview": self.extracted_text_preview
        }
