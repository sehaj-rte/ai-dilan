from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Integer, Float
from sqlalchemy.sql import func
from config.database import Base
import uuid

class ExpertProcessingProgress(Base):
    __tablename__ = "expert_processing_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    expert_id = Column(String, nullable=False, index=True)  # Links to experts table
    agent_id = Column(String, nullable=False)  # ElevenLabs agent ID (Pinecone namespace)

    # Processing stages
    stage = Column(String(50), nullable=False)  # e.g., "queued", "file_processing", "text_extraction", "chunking", "embedding", "pinecone_storage", "complete", "failed"
    status = Column(String(20), nullable=False, default="pending")  # pending, in_progress, completed, failed
    
    # Queue information
    queue_position = Column(Integer, nullable=True)  # Position in queue (1 = next, null = not queued/processing)
    task_id = Column(String, nullable=True)  # Reference to processing_queue table

    # Progress tracking
    current_file = Column(String(255), nullable=True)  # Current file being processed
    current_file_index = Column(Integer, default=0)  # Index of current file (0-based)
    total_files = Column(Integer, default=0)  # Total number of files to process

    # Batch progress (for embedding batches)
    current_batch = Column(Integer, default=0)  # Current batch number
    total_batches = Column(Integer, default=0)  # Total batches for current file
    current_chunk = Column(Integer, default=0)  # Current chunk in batch
    total_chunks = Column(Integer, default=0)  # Total chunks for current file

    # Overall progress
    processed_files = Column(Integer, default=0)  # Files completed
    failed_files = Column(Integer, default=0)  # Files that failed
    progress_percentage = Column(Float, default=0.0)  # Overall progress (0-100)

    # Detailed progress info
    details = Column(JSON, nullable=True)  # Additional progress details
    error_message = Column(Text, nullable=True)  # Error message if failed

    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Processing metadata
    processing_metadata = Column(JSON, nullable=True)  # Store processing stats, timing, etc.

    def to_dict(self):
        return {
            "id": self.id,
            "expert_id": self.expert_id,
            "agent_id": self.agent_id,
            "stage": self.stage,
            "status": self.status,
            "queue_position": self.queue_position,
            "task_id": self.task_id,
            "current_file": self.current_file,
            "current_file_index": self.current_file_index,
            "total_files": self.total_files,
            "current_batch": self.current_batch,
            "total_batches": self.total_batches,
            "current_chunk": self.current_chunk,
            "total_chunks": self.total_chunks,
            "processed_files": self.processed_files,
            "failed_files": self.failed_files,
            "progress_percentage": self.progress_percentage,
            "details": self.details,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_metadata": self.processing_metadata
        }

    def update_progress(self, **kwargs):
        """Update progress fields and timestamp"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = func.now()

    def mark_completed(self):
        """Mark processing as completed"""
        self.status = "completed"
        self.stage = "complete"
        self.completed_at = func.now()
        self.progress_percentage = 100.0

    def mark_failed(self, error_message: str):
        """Mark processing as failed"""
        self.status = "failed"
        self.stage = "failed"
        self.error_message = error_message
        self.completed_at = func.now()
