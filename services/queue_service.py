from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.processing_queue import ProcessingQueue, TaskStatus
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class QueueService:
    """Service to manage processing queue without Redis"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def enqueue_task(
        self, 
        expert_id: str, 
        agent_id: str, 
        task_data: Dict[str, Any],
        task_type: str = "file_processing",
        priority: int = 0
    ) -> ProcessingQueue:
        """Add a task to the queue"""
        try:
            # Create queue entry
            task = ProcessingQueue(
                expert_id=expert_id,
                agent_id=agent_id,
                task_type=task_type,
                status=TaskStatus.QUEUED,
                priority=priority,
                task_data=task_data
            )
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            # Update queue positions
            self._update_queue_positions()
            
            logger.info(f"✅ Task queued for expert {expert_id}: {task.id}")
            print(f"📋 Task {task.id} added to queue for expert {expert_id}")
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to enqueue task: {str(e)}")
            self.db.rollback()
            raise
    
    def get_next_task(self) -> Optional[ProcessingQueue]:
        """Get the next task to process (highest priority, oldest first)"""
        try:
            task = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.status == TaskStatus.QUEUED
            ).order_by(
                ProcessingQueue.priority.desc(),
                ProcessingQueue.created_at.asc()
            ).first()
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to get next task: {str(e)}")
            return None
    
    def mark_task_processing(self, task_id: str) -> bool:
        """Mark a task as currently processing"""
        try:
            task = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.id == task_id
            ).first()
            
            if not task:
                return False
            
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.utcnow()
            
            self.db.commit()
            self._update_queue_positions()
            
            logger.info(f"🔄 Task {task_id} marked as processing")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark task as processing: {str(e)}")
            self.db.rollback()
            return False
    
    def mark_task_completed(self, task_id: str) -> bool:
        """Mark a task as completed"""
        try:
            task = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.id == task_id
            ).first()
            
            if not task:
                return False
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            self.db.commit()
            self._update_queue_positions()
            
            logger.info(f"✅ Task {task_id} marked as completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark task as completed: {str(e)}")
            self.db.rollback()
            return False
    
    def mark_task_failed(self, task_id: str, error_message: str) -> bool:
        """Mark a task as failed"""
        try:
            task = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.id == task_id
            ).first()
            
            if not task:
                return False
            
            task.retry_count += 1
            
            if task.retry_count >= task.max_retries:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                logger.error(f"❌ Task {task_id} failed after {task.retry_count} retries")
            else:
                # Re-queue for retry
                task.status = TaskStatus.QUEUED
                logger.warning(f"⚠️ Task {task_id} failed, retry {task.retry_count}/{task.max_retries}")
            
            task.error_message = error_message
            
            self.db.commit()
            self._update_queue_positions()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark task as failed: {str(e)}")
            self.db.rollback()
            return False
    
    def get_task_by_expert_id(self, expert_id: str) -> Optional[ProcessingQueue]:
        """Get the current task for an expert"""
        try:
            task = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.expert_id == expert_id,
                ProcessingQueue.status.in_([TaskStatus.QUEUED, TaskStatus.PROCESSING])
            ).first()
            
            return task
            
        except Exception as e:
            logger.error(f"Failed to get task for expert {expert_id}: {str(e)}")
            return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        try:
            queued_count = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.status == TaskStatus.QUEUED
            ).count()
            
            processing_count = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.status == TaskStatus.PROCESSING
            ).count()
            
            completed_count = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.status == TaskStatus.COMPLETED
            ).count()
            
            failed_count = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.status == TaskStatus.FAILED
            ).count()
            
            return {
                "queued": queued_count,
                "processing": processing_count,
                "completed": completed_count,
                "failed": failed_count,
                "total": queued_count + processing_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {str(e)}")
            return {
                "queued": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "total": 0
            }
    
    def _update_queue_positions(self):
        """Update queue positions for all queued tasks"""
        try:
            queued_tasks = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.status == TaskStatus.QUEUED
            ).order_by(
                ProcessingQueue.priority.desc(),
                ProcessingQueue.created_at.asc()
            ).all()
            
            for position, task in enumerate(queued_tasks, start=1):
                task.queue_position = position
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update queue positions: {str(e)}")
            self.db.rollback()
    
    def get_all_queued_tasks(self) -> List[ProcessingQueue]:
        """Get all queued tasks"""
        try:
            return self.db.query(ProcessingQueue).filter(
                ProcessingQueue.status == TaskStatus.QUEUED
            ).order_by(
                ProcessingQueue.priority.desc(),
                ProcessingQueue.created_at.asc()
            ).all()
            
        except Exception as e:
            logger.error(f"Failed to get queued tasks: {str(e)}")
            return []
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a queued task"""
        try:
            task = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.id == task_id,
                ProcessingQueue.status == TaskStatus.QUEUED
            ).first()
            
            if not task:
                return False
            
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            
            self.db.commit()
            self._update_queue_positions()
            
            logger.info(f"🚫 Task {task_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task: {str(e)}")
            self.db.rollback()
            return False
