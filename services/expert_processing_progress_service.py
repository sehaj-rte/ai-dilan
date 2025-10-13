from sqlalchemy.orm import Session
from models.expert_processing_progress import ExpertProcessingProgress
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ExpertProcessingProgressService:

    def __init__(self, db: Session):
        self.db = db

    def create_progress_record(self, expert_id: str, agent_id: str, total_files: int) -> ExpertProcessingProgress:
        """Create a new progress record for expert processing"""
        progress_record = ExpertProcessingProgress(
            expert_id=expert_id,
            agent_id=agent_id,
            stage="file_processing",
            status="pending",
            total_files=total_files,
            progress_percentage=0.0
        )

        self.db.add(progress_record)
        self.db.commit()
        self.db.refresh(progress_record)

        logger.info(f"Created progress record for expert {expert_id} with {total_files} files")
        return progress_record

    def get_progress_by_expert_id(self, expert_id: str) -> Optional[ExpertProcessingProgress]:
        """Get progress record by expert ID"""
        progress = self.db.query(ExpertProcessingProgress).filter(
            ExpertProcessingProgress.expert_id == expert_id
        ).first()
        
        # If progress exists and has a task_id, sync with queue
        if progress and progress.task_id and progress.stage == "queued":
            from models.processing_queue import ProcessingQueue
            task = self.db.query(ProcessingQueue).filter(
                ProcessingQueue.id == progress.task_id
            ).first()
            
            if task:
                progress.queue_position = task.queue_position
        
        return progress

    def update_progress(self, expert_id: str, **kwargs) -> bool:
        """Update progress for an expert"""
        progress_record = self.get_progress_by_expert_id(expert_id)
        if not progress_record:
            logger.warning(f"No progress record found for expert {expert_id}")
            return False

        try:
            progress_record.update_progress(**kwargs)
            self.db.commit()
            logger.debug(f"Updated progress for expert {expert_id}: {kwargs}")
            return True
        except Exception as e:
            logger.error(f"Failed to update progress for expert {expert_id}: {str(e)}")
            self.db.rollback()
            return False

    def mark_completed(self, expert_id: str, metadata: Dict[str, Any] = None) -> bool:
        """Mark processing as completed"""
        progress_record = self.get_progress_by_expert_id(expert_id)
        if not progress_record:
            logger.warning(f"No progress record found for expert {expert_id}")
            return False

        try:
            progress_record.mark_completed()
            if metadata:
                if progress_record.processing_metadata:
                    progress_record.processing_metadata.update(metadata)
                else:
                    progress_record.processing_metadata = metadata

            self.db.commit()
            logger.info(f"Marked processing as completed for expert {expert_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark completed for expert {expert_id}: {str(e)}")
            self.db.rollback()
            return False

    def mark_failed(self, expert_id: str, error_message: str, metadata: Dict[str, Any] = None) -> bool:
        """Mark processing as failed"""
        progress_record = self.get_progress_by_expert_id(expert_id)
        if not progress_record:
            logger.warning(f"No progress record found for expert {expert_id}")
            return False

        try:
            progress_record.mark_failed(error_message)
            if metadata:
                if progress_record.processing_metadata:
                    progress_record.processing_metadata.update(metadata)
                else:
                    progress_record.processing_metadata = metadata

            self.db.commit()
            logger.error(f"Marked processing as failed for expert {expert_id}: {error_message}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark failed for expert {expert_id}: {str(e)}")
            self.db.rollback()
            return False

    def delete_progress_record(self, expert_id: str) -> bool:
        """Delete progress record for an expert"""
        progress_record = self.get_progress_by_expert_id(expert_id)
        if not progress_record:
            logger.warning(f"No progress record found for expert {expert_id}")
            return False

        try:
            self.db.delete(progress_record)
            self.db.commit()
            logger.info(f"Deleted progress record for expert {expert_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete progress record for expert {expert_id}: {str(e)}")
            self.db.rollback()
            return False

    def get_all_active_progress(self) -> list:
        """Get all active (not completed/failed) progress records"""
        return self.db.query(ExpertProcessingProgress).filter(
            ExpertProcessingProgress.status.in_(["pending", "in_progress"])
        ).all()
