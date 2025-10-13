import asyncio
import logging
import threading
from sqlalchemy.orm import Session
from config.database import SessionLocal
from services.queue_service import QueueService
from controllers.knowledge_base_controller import process_expert_files
from models.processing_queue import TaskStatus
import time

logger = logging.getLogger(__name__)

class QueueWorker:
    """Background worker to process queued tasks"""
    
    def __init__(self):
        self.is_running = False
        self.current_task_id = None
        self.poll_interval = 2  # Check for new tasks every 2 seconds
        self.worker_thread = None
    
    def start(self):
        """Start the queue worker in a separate thread"""
        if self.is_running:
            logger.warning("Queue worker already running")
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self.worker_thread.start()
        logger.info("🚀 Queue worker started in background thread")
        print("🚀 Queue worker started - Processing tasks in background")
    
    def _run_worker(self):
        """Worker thread main loop"""
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._worker_loop())
        except Exception as e:
            logger.error(f"Worker thread error: {str(e)}")
        finally:
            loop.close()
    
    async def _worker_loop(self):
        """Main worker loop"""
        while self.is_running:
            try:
                await self._process_next_task()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in queue worker: {str(e)}")
                await asyncio.sleep(self.poll_interval)
    
    def stop(self):
        """Stop the queue worker"""
        self.is_running = False
        logger.info("🛑 Queue worker stopped")
        print("🛑 Queue worker stopped")
    
    async def _process_next_task(self):
        """Process the next task in the queue"""
        db = SessionLocal()
        
        try:
            queue_service = QueueService(db)
            
            # Get next task
            task = queue_service.get_next_task()
            
            if not task:
                # No tasks in queue
                return
            
            self.current_task_id = task.id
            
            logger.info(f"📋 Processing task {task.id} for expert {task.expert_id}")
            print(f"\n{'='*60}")
            print(f"📋 Processing Task: {task.id}")
            print(f"👤 Expert: {task.expert_id}")
            print(f"🤖 Agent: {task.agent_id}")
            print(f"📊 Task Type: {task.task_type}")
            print(f"{'='*60}\n")
            
            # Mark as processing
            queue_service.mark_task_processing(task.id)
            
            # Process based on task type
            if task.task_type == "file_processing":
                await self._process_file_task(task, db)
            else:
                logger.warning(f"Unknown task type: {task.task_type}")
                queue_service.mark_task_failed(task.id, f"Unknown task type: {task.task_type}")
            
            self.current_task_id = None
            
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            if self.current_task_id:
                queue_service = QueueService(db)
                queue_service.mark_task_failed(self.current_task_id, str(e))
        finally:
            db.close()
    
    async def _process_file_task(self, task, db: Session):
        """Process file processing task"""
        try:
            queue_service = QueueService(db)
            
            # Extract task data
            expert_id = task.expert_id
            agent_id = task.agent_id
            selected_files = task.task_data.get("selected_files", [])
            
            if not selected_files:
                logger.warning(f"No files to process for expert {expert_id}")
                queue_service.mark_task_completed(task.id)
                return
            
            logger.info(f"🔄 Processing {len(selected_files)} files for expert {expert_id}")
            print(f"🔄 Processing {len(selected_files)} files for expert {expert_id}")
            
            # Process the files
            result = await process_expert_files(
                expert_id=expert_id,
                agent_id=agent_id,
                selected_files=selected_files,
                db=db
            )
            
            if result.get("success"):
                processed_count = result.get("processed_count", 0)
                total_files = result.get("total_files", 0)
                
                logger.info(f"✅ Task completed: {processed_count}/{total_files} files processed")
                print(f"\n{'='*60}")
                print(f"✅ Task Completed Successfully")
                print(f"📊 Files Processed: {processed_count}/{total_files}")
                print(f"👤 Expert: {expert_id}")
                print(f"{'='*60}\n")
                
                queue_service.mark_task_completed(task.id)
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"❌ Task failed: {error_msg}")
                print(f"\n{'='*60}")
                print(f"❌ Task Failed")
                print(f"📊 Error: {error_msg}")
                print(f"👤 Expert: {expert_id}")
                print(f"{'='*60}\n")
                
                queue_service.mark_task_failed(task.id, error_msg)
                
        except Exception as e:
            logger.error(f"Error in file processing task: {str(e)}")
            queue_service = QueueService(db)
            queue_service.mark_task_failed(task.id, str(e))
    
    def get_status(self) -> dict:
        """Get worker status"""
        return {
            "is_running": self.is_running,
            "current_task_id": self.current_task_id,
            "poll_interval": self.poll_interval
        }

# Global worker instance
_worker_instance = None

def get_worker() -> QueueWorker:
    """Get the global worker instance"""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = QueueWorker()
    return _worker_instance

def start_worker():
    """Start the background worker"""
    worker = get_worker()
    worker.start()

def stop_worker():
    """Stop the background worker"""
    worker = get_worker()
    worker.stop()
