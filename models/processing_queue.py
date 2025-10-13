from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Enum as SQLEnum
from sqlalchemy.sql import func
from config.database import Base
import uuid
import enum

class TaskStatus(enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessingQueue(Base):
    __tablename__ = "processing_queue"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    expert_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=False)
    
    # Task details
    task_type = Column(String(50), nullable=False, default="file_processing")  # file_processing, reindex, etc.
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.QUEUED, index=True)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    
    # Queue position
    queue_position = Column(Integer, nullable=True)  # Position in queue (1 = next)
    
    # Task data
    task_data = Column(JSON, nullable=True)  # Store file IDs, config, etc.
    
    # Processing info
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "expert_id": self.expert_id,
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "priority": self.priority,
            "queue_position": self.queue_position,
            "task_data": self.task_data,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
