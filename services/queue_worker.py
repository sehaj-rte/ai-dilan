import asyncio
import logging
import threading
from sqlalchemy.orm import Session
from config.database import SessionLocal
from services.queue_service import QueueService
from controllers.knowledge_base_controller import process_expert_files, process_document_for_knowledge_base
from models.processing_queue import TaskStatus
from models.file_db import FileDB
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
            elif task.task_type == "knowledge_base_processing":
                await self._process_knowledge_base_task(task, db)
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
            
            # Check if error is due to missing OpenAI API key
            error_msg = result.get("error", "")
            is_api_key_error = "401" in str(error_msg) or "invalid_api_key" in str(error_msg).lower() or "incorrect api key" in str(error_msg).lower()
            
            if result.get("success") or is_api_key_error:
                processed_count = result.get("processed_count", 0)
                total_files = result.get("total_files", 0)
                
                if is_api_key_error:
                    logger.warning(f"⚠️ OpenAI API key not configured - Skipping file processing")
                    print(f"\n{'='*60}")
                    print(f"⚠️ Task Completed (File Processing Skipped)")
                    print(f"📊 Reason: OpenAI API key not configured")
                    print(f"💡 Expert created successfully without knowledge base")
                    print(f"👤 Expert: {expert_id}")
                    print(f"{'='*60}\n")
                else:
                    logger.info(f"✅ Task completed: {processed_count}/{total_files} files processed")
                    print(f"\n{'='*60}")
                    print(f"✅ Task Completed Successfully")
                    print(f"📊 Files Processed: {processed_count}/{total_files}")
                    print(f"👤 Expert: {expert_id}")
                    print(f"{'='*60}\n")
                
                queue_service.mark_task_completed(task.id)
            else:
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

    async def _process_knowledge_base_task(self, task, db: Session):
        """Process knowledge base processing task"""
        try:
            queue_service = QueueService(db)
            task_data = task.task_data
            
            file_id = task_data.get("file_id")
            filename = task_data.get("filename")
            content_type = task_data.get("content_type")
            user_id = task_data.get("user_id")
            agent_id = task_data.get("agent_id")
            extracted_text = task_data.get("extracted_text")
            
            logger.info(f"Processing knowledge base task for file {file_id} (agent: {agent_id})")
            
            # Update file status to processing
            file_record = db.query(FileDB).filter(FileDB.id == file_id).first()
            if file_record:
                file_record.processing_status = "processing"
                db.commit()
            
            # Process document for knowledge base with agent isolation
            if extracted_text:
                # Use pre-extracted text for faster processing
                processing_result = await process_document_for_knowledge_base(
                    file_content=extracted_text.encode('utf-8'),
                    content_type="text/plain",
                    filename=filename,
                    file_id=file_id,
                    user_id=user_id,
                    agent_id=agent_id
                )
            else:
                # Need to re-extract text (fallback)
                logger.warning(f"No pre-extracted text for {file_id}, will need file content")
                processing_result = {"success": False, "error": "No extracted text available"}
            
            # Update file status based on result
            if file_record:
                if processing_result.get("success"):
                    file_record.processing_status = "completed"
                    file_record.word_count = processing_result.get("word_count", 0)
                else:
                    file_record.processing_status = "failed"
                    file_record.processing_error = processing_result.get("error", "Unknown error")
                db.commit()
            
            if processing_result.get("success"):
                logger.info(f"Successfully processed knowledge base for file {file_id}")
                queue_service.mark_task_completed(task.id)
            else:
                error_msg = processing_result.get("error", "Unknown processing error")
                logger.error(f"Knowledge base processing failed for file {file_id}: {error_msg}")
                queue_service.mark_task_failed(task.id, error_msg)
                
        except Exception as e:
            logger.error(f"Error processing knowledge base task: {str(e)}")
            queue_service = QueueService(db)
            queue_service.mark_task_failed(task.id, str(e))
            
            # Update file status to failed
            try:
                file_id = task.task_data.get("file_id")
                if file_id:
                    file_record = db.query(FileDB).filter(FileDB.id == file_id).first()
                    if file_record:
                        file_record.processing_status = "failed"
                        file_record.processing_error = str(e)
                        db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update file status: {str(update_error)}")
    
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
