from typing import Dict, Any
from fastapi import UploadFile, HTTPException
from services.file_service import FileService
from services.document_processor import document_processor
from services.embedding_service import embedding_service
from services.pinecone_service import pinecone_service
from services.aws_s3_service import s3_service
from services.expert_processing_progress_service import ExpertProcessingProgressService
from services.youtube_service import youtube_service
from services.web_scraper_service import web_scraper_service
from services.queue_service import QueueService
from models.file_db import FileDB
from sqlalchemy.orm import Session
import logging
import uuid
import os
import httpx
import re

logger = logging.getLogger(__name__)

async def upload_file(file: UploadFile, db: Session, user_id: str = None, agent_id: str = None, folder_id: str = None, folder: str = "Uncategorized", custom_name: str = None) -> Dict[str, Any]:
    """Upload file to knowledge base"""
    try:
        # Use custom name if provided, otherwise use original filename
        display_name = custom_name if custom_name else file.filename
        logger.info(f"Starting file upload: {file.filename}, custom_name: {custom_name}, content_type: {file.content_type}, folder: {folder}")
        
        # Validate file
        if not file.filename:
            logger.error("No filename provided")
            return {"success": False, "error": "No file provided"}
        
        # Check file size (limit to 15MB)
        max_size = 15 * 1024 * 1024  # 15MB
        file_content = file.file.read()
        
        logger.info(f"File size: {len(file_content)} bytes")
        
        if len(file_content) > max_size:
            logger.error(f"File size {len(file_content)} exceeds limit {max_size}")
            return {"success": False, "error": "File size exceeds 15MB limit"}
        
        if len(file_content) == 0:
            logger.error("File is empty")
            return {"success": False, "error": "File is empty"}
        
        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/csv',
            'image/jpeg',
            'image/png',
            'image/gif',
            'audio/mpeg',
            'audio/wav',
            'video/mp4',
            'video/avi'
        ]
        
        if file.content_type not in allowed_types:
            logger.error(f"Unsupported file type: {file.content_type}")
            return {"success": False, "error": f"File type '{file.content_type}' not supported"}
        
        logger.info("File validation passed")
        
        # Extract text and metadata first
        extraction_result = document_processor.extract_text(
            file_content=file_content,
            content_type=file.content_type,
            filename=file.filename
        )
        
        # Upload file to S3 and save metadata
        logger.info("Starting file service upload")
        file_service = FileService(db)
        upload_result = file_service.upload_file(
            file_content=file_content,
            file_name=display_name,
            content_type=file.content_type,
            file_size=len(file_content),
            user_id=user_id,
            agent_id=agent_id,
            extraction_result=extraction_result if extraction_result and extraction_result.get("success") else None,
            folder_id=folder_id,
            folder=folder
        )
        
        logger.info(f"File service upload result: {upload_result.get('success', False)}")
        
        if not upload_result["success"]:
            logger.error(f"File service upload failed: {upload_result.get('error', 'Unknown error')}")
            return upload_result
        
        file_id = upload_result["id"]
        logger.info(f"File uploaded successfully with ID: {file_id}")
        
        # Queue document processing for knowledge base with agent isolation
        processing_result = await queue_document_processing(
            file_id=file_id,
            file_content=file_content,
            content_type=file.content_type,
            filename=file.filename,
            user_id=user_id,
            agent_id=agent_id,
            db=db
        )
        
        # Return combined result
        return {
            "success": True,
            "id": file_id,
            "url": upload_result["url"],
            "s3_key": upload_result["s3_key"],
            "file": upload_result["file"],
            "processing": processing_result
        }
        
    except Exception as e:
        logger.error(f"Upload failed with exception: {str(e)}")
        return {"success": False, "error": f"Upload failed: {str(e)}"}

def get_files(db: Session, user_id: str = None, agent_id: str = None) -> Dict[str, Any]:
    """Get all uploaded files"""
    try:
        file_service = FileService(db)
        return file_service.get_files(user_id=user_id, agent_id=agent_id)
        
    except Exception as e:
        return {"success": False, "error": f"Failed to retrieve files: {str(e)}"}

def get_file_by_id(file_id: str, db: Session) -> Dict[str, Any]:
    """Get file by ID"""
    try:
        file_service = FileService(db)
        return file_service.get_file_by_id(file_id)
        
    except Exception as e:
        return {"success": False, "error": f"Failed to retrieve file: {str(e)}"}

async def delete_file(file_id: str, db: Session, user_id: str = None) -> Dict[str, Any]:
    """Delete file from knowledge base"""
    try:
        # Delete from Pinecone first
        if user_id:
            pinecone_result = await pinecone_service.delete_user_document(file_id, user_id)
            logger.info(f"Pinecone deletion result for file {file_id}: {pinecone_result}")
        
        # Delete from S3 and database
        file_service = FileService(db)
        return file_service.delete_file(file_id)
        
    except Exception as e:
        return {"success": False, "error": f"Failed to delete file: {str(e)}"}

def get_file_stats(db: Session, user_id: str = None) -> Dict[str, Any]:
    """Get file statistics"""
    try:
        file_service = FileService(db)
        return file_service.get_file_stats(user_id=user_id)
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get statistics: {str(e)}"}

async def queue_document_processing(
    file_id: str,
    file_content: bytes,
    content_type: str,
    filename: str,
    user_id: str = None,
    agent_id: str = None,
    db: Session = None
) -> Dict[str, Any]:
    """
    Queue document processing for knowledge base with agent isolation
    
    Args:
        file_id: Unique file identifier
        file_content: Raw file content (for immediate text extraction)
        content_type: MIME type of the file
        filename: Original filename
        user_id: User who uploaded the file
        agent_id: Agent ID for isolation
        db: Database session
        
    Returns:
        Dict containing queue status and immediate processing results
    """
    try:
        logger.info(f"Queueing document processing for {filename} (file_id: {file_id}, agent_id: {agent_id})")
        
        # Step 1: Immediate text extraction for quick preview
        extraction_result = document_processor.extract_text(
            file_content=file_content,
            content_type=content_type,
            filename=filename
        )
        
        # Update file record with extracted text (for immediate search/preview)
        if extraction_result.get("success") and db:
            try:
                file_record = db.query(FileDB).filter(FileDB.id == file_id).first()
                if file_record:
                    file_record.extracted_text = extraction_result.get("text", "")[:10000]  # Store first 10k chars
                    file_record.word_count = extraction_result.get("word_count", 0)
                    file_record.processing_status = "queued"
                    db.commit()
                    logger.info(f"Updated file record with extracted text preview for {file_id}")
            except Exception as e:
                logger.error(f"Failed to update file record: {str(e)}")
                db.rollback()
        
        # Step 2: Queue background processing for embedding and indexing
        if agent_id and db:
            queue_service = QueueService(db)
            
            task_data = {
                "file_id": file_id,
                "filename": filename,
                "content_type": content_type,
                "user_id": user_id,
                "agent_id": agent_id,
                "task_type": "knowledge_base_processing",
                "extracted_text": extraction_result.get("text", "") if extraction_result.get("success") else None
            }
            
            # Queue the processing task
            queue_task = queue_service.enqueue_task(
                expert_id=agent_id,  # Using agent_id as expert_id for compatibility
                agent_id=agent_id,
                task_data=task_data,
                task_type="knowledge_base_processing",
                priority=1  # High priority for knowledge base processing
            )
            
            logger.info(f"Queued knowledge base processing task {queue_task.id} for file {file_id}")
            
            return {
                "success": True,
                "message": "File queued for processing",
                "task_id": queue_task.id,
                "status": "queued",
                "text_extracted": extraction_result.get("success", False),
                "word_count": extraction_result.get("word_count", 0) if extraction_result.get("success") else 0
            }
        else:
            # Fallback: immediate processing if no agent_id or db
            logger.warning(f"No agent_id or db provided, falling back to immediate processing for {file_id}")
            return await process_document_for_knowledge_base(
                file_content=file_content,
                content_type=content_type,
                filename=filename,
                file_id=file_id,
                user_id=user_id,
                agent_id=agent_id
            )
            
    except Exception as e:
        logger.error(f"Failed to queue document processing for {filename}: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to queue processing: {str(e)}",
            "status": "failed"
        }

async def process_document_for_knowledge_base(
    file_content: bytes, 
    content_type: str, 
    filename: str, 
    file_id: str, 
    user_id: str = None,
    agent_id: str = None
) -> Dict[str, Any]:
    """
    Process uploaded document for knowledge base integration with agent isolation
    
    Args:
        file_content: Raw file content
        content_type: MIME type of the file
        filename: Original filename
        file_id: Unique file identifier
        user_id: User who uploaded the file
        agent_id: Agent ID for isolation
        
    Returns:
        Dict containing processing status and results
    """
    try:
        logger.info(f"Starting document processing for {filename} (file_id: {file_id}, agent_id: {agent_id})")
        
        # Step 1: Extract text from file
        extraction_result = document_processor.extract_text(
            file_content=file_content,
            content_type=content_type,
            filename=filename
        )
        
        if not extraction_result["success"]:
            logger.error(f"Text extraction failed for {filename}: {extraction_result['error']}")
            return {
                "success": False,
                "error": f"Text extraction failed: {extraction_result['error']}",
                "stage": "text_extraction"
            }
        
        extracted_text = extraction_result["text"]
        word_count = extraction_result.get("word_count", 0)
        
        logger.info(f"Extracted {word_count} words from {filename}")
        
        # Step 2: Process document (chunk and embed) with agent isolation
        processing_result = embedding_service.process_document(
            text=extracted_text,
            file_id=file_id,
            filename=filename,
            user_id=user_id,
            agent_id=agent_id  # Pass agent_id for isolation
        )
        
        if not processing_result["success"]:
            logger.error(f"Document processing failed for {filename}: {processing_result['error']}")
            return {
                "success": False,
                "error": f"Document processing failed: {processing_result['error']}",
                "stage": "document_processing"
            }
        
        chunks_created = processing_result.get("chunks_created", 0)
        logger.info(f"Created {chunks_created} chunks for {filename}")
        
        # Step 3: Store embeddings in Pinecone with agent isolation
        if chunks_created > 0:
            pinecone_result = await pinecone_service.store_document_embeddings(
                chunks_with_embeddings=processing_result["chunks"],
                file_id=file_id,
                filename=filename,
                user_id=user_id,
                agent_id=agent_id  # Pass agent_id for namespace isolation
            )
            
            if not pinecone_result["success"]:
                logger.error(f"Pinecone storage failed for {filename}: {pinecone_result['error']}")
                return {
                    "success": False,
                    "error": f"Vector storage failed: {pinecone_result['error']}",
                    "stage": "vector_storage"
                }
            
            vectors_stored = pinecone_result.get("vectors_stored", 0)
            logger.info(f"Stored {vectors_stored} vectors in Pinecone for {filename}")
        
        # Step 4: Automatically attach knowledge base to agent for chat
        if agent_id:
            attachment_result = await attach_knowledge_base_to_agent(
                agent_id=agent_id,
                user_id=user_id
            )
            logger.info(f"Knowledge base attachment result for agent {agent_id}: {attachment_result}")
        
        return {
            "success": True,
            "message": f"Document processed successfully",
            "word_count": word_count,
            "chunks_created": chunks_created,
            "vectors_stored": vectors_stored if chunks_created > 0 else 0,
            "agent_attached": bool(agent_id),
            "stage": "completed"
        }
        
    except Exception as e:
        logger.error(f"Unexpected error processing {filename}: {str(e)}")
        return {
            "success": False,
            "error": f"Processing failed: {str(e)}",
            "stage": "unknown"
        }

async def process_expert_files(expert_id: str, agent_id: str, selected_files: list, db: Session) -> Dict[str, Any]:
    """
    Process selected files for an expert and store them in Pinecone
    
    Args:
        expert_id: The expert's database ID
        agent_id: The ElevenLabs agent ID (used as Pinecone namespace)
        selected_files: List of file IDs to process
        db: Database session
        
    Returns:
        Dict containing processing results
    """
    try:
        if not selected_files:
            logger.info(f"No files selected for expert {expert_id}")
            print(f"\U0001f4ed No files selected for expert {expert_id}")
            return {"success": True, "message": "No files to process", "processed_count": 0}
        
        logger.info(f"\U0001f680 Starting file processing for expert {expert_id} with {len(selected_files)} files")
        print(f"\U0001f680 Starting Pinecone processing for expert {expert_id} with {len(selected_files)} files")
        
        # Create progress tracking record
        progress_service = ExpertProcessingProgressService(db)
        progress_record = progress_service.create_progress_record(
            expert_id=expert_id,
            agent_id=agent_id,
            total_files=len(selected_files)
        )
        
        processed_count = 0
        failed_files = []
        
        file_service = FileService(db)
        
        for file_index, file_id in enumerate(selected_files):
            try:
                logger.info(f"\U0001f4c4 Processing file {file_id} for expert {expert_id}")
                print(f"\U0001f4d1 Processing file {file_id} for expert {expert_id}")
                
                # Update progress: starting new file
                progress_service.update_progress(
                    expert_id=expert_id,
                    status="in_progress",
                    stage="file_processing",
                    current_file_index=file_index,
                    current_file=file_id
                )
                
                # Step 1: Get file from database
                file_result = file_service.get_file_by_id(file_id)
                if not file_result["success"]:
                    logger.error(f"\U0001f6ab Failed to get file {file_id}: {file_result.get('error')}")
                    print(f"\U0001f6ab Failed to get file {file_id}: {file_result.get('error')}")
                    failed_files.append({"file_id": file_id, "error": "File not found"})
                    continue
                
                file_data = file_result["file"]
                filename = file_data.get("name", f"file_{file_id}")
                file_type = file_data.get("type", "text/plain")
                s3_key = file_data.get("s3_key")
                
                # Try to get file content - first from S3, then from database
                file_content = None
                
                # Try S3 first if key exists and not a fallback key
                if s3_key and not s3_key.startswith("fallback/"):
                    logger.info(f"📥 Downloading file from S3: {s3_key}")
                    print(f"📥 Downloading file from S3: {s3_key}")
                    file_content = s3_service.download_file(s3_key)
                    
                    if file_content:
                        logger.info(f"✅ Successfully downloaded from S3: {s3_key}")
                        print(f"✅ Successfully downloaded from S3: {s3_key}")
                
                # Get file record from database for pre-extracted text
                logger.info(f"📂 Getting file record from database for {file_id}")
                print(f"📂 Getting file record from database for {file_id}")
                file_record = file_service.db.query(FileDB).filter(FileDB.id == uuid.UUID(file_id)).first()
                
                # Fallback to database if S3 failed or content not in S3
                if not file_content:
                    logger.info(f"📂 Trying to get file content from database for {file_id}")
                    print(f"📂 Trying to get file content from database for {file_id}")
                    
                    if file_record and file_record.content:
                        file_content = file_record.content
                        logger.info(f"✅ Retrieved file content from database: {filename}")
                        print(f"✅ Retrieved file content from database: {filename}")
                    else:
                        logger.error(f"\U0001f6ab No content found in S3 or database for file {file_id}")
                        print(f"\U0001f6ab No content found in S3 or database for file {file_id}")
                        print(f"💡 This file may have been uploaded before the hybrid storage system was implemented.")
                        print(f"💡 Please re-upload the file: {filename}")
                        failed_files.append({"file_id": file_id, "error": f"No content available. Please re-upload '{filename}'"})
                        continue
                
                logger.info(f"📝 Using pre-extracted text from database for {filename}")
                
                # Step 2: Use pre-extracted text from database
                # If file was uploaded before the text extraction feature was enabled, we'll need to extract it now
                if file_record and file_record.extracted_text:
                    # Use pre-extracted text
                    extracted_text = file_record.extracted_text
                    extraction_result = {
                        "success": True,
                        "text": extracted_text,
                        "content_type": file_data.get('type', 'text/plain'),
                        "filename": filename,
                        "word_count": file_record.word_count or len(extracted_text.split()),
                        "metadata": {
                            "document_type": file_record.document_type,
                            "language": file_record.language,
                            "page_count": file_record.page_count,
                            "has_images": file_record.has_images,
                            "has_tables": file_record.has_tables,
                            "extracted_text_preview": file_record.extracted_text_preview or extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
                        }
                    }
                else:
                    # Extract text from file (fallback for older uploads)
                    extraction_result = document_processor.extract_text(
                        file_content=file_content,
                        content_type=file_data.get('type', 'text/plain'),
                        filename=filename
                    )
                
                if not extraction_result["success"]:
                    logger.error(f"\U0001f6ab Text extraction failed for {filename}: {extraction_result.get('error')}")
                    print(f"\U0001f6ab Text extraction failed for {filename}: {extraction_result.get('error')}")
                    failed_files.append({"file_id": file_id, "error": f"Text extraction failed: {extraction_result.get('error')}"})
                    continue
                
                extracted_text = extraction_result["text"]
                logger.info(f"✅ Extracted {len(extracted_text)} characters from {filename}")
                
                # Update progress: text extraction complete
                progress_service.update_progress(
                    expert_id=expert_id,
                    stage="text_extraction",
                    details={"filename": filename, "characters_extracted": len(extracted_text)}
                )
                
                # Step 3: Process document (chunk and embed) with progress callback
                logger.info(f"\U0001f9e0 Processing document {filename} for embeddings")
                
                def progress_callback(batch_num: int, total_batches: int, chunks_completed: int, total_chunks: int):
                    """Callback to update progress during embedding generation"""
                    progress_percentage = ((file_index + (chunks_completed / total_chunks)) / len(selected_files)) * 100
                    progress_service.update_progress(
                        expert_id=expert_id,
                        stage="embedding",
                        current_batch=batch_num,
                        total_batches=total_batches,
                        current_chunk=chunks_completed,
                        total_chunks=total_chunks,
                        progress_percentage=progress_percentage,
                        details={
                            "filename": filename,
                            "batch": f"{batch_num}/{total_batches}",
                            "chunks": f"{chunks_completed}/{total_chunks}"
                        }
                    )
                
                embedding_result = embedding_service.process_document(
                    text=extracted_text,
                    file_id=file_id,
                    filename=filename,
                    user_id=expert_id,  # Pass expert_id as agent_id for metadata
                    progress_callback=progress_callback
                )
                
                if not embedding_result["success"]:
                    logger.error(f"\U0001f6ab Embedding generation failed for {filename}: {embedding_result.get('error')}")
                    print(f"\U0001f6ab Embedding generation failed for {filename}: {embedding_result.get('error')}")
                    failed_files.append({"file_id": file_id, "error": f"Embedding generation failed: {embedding_result.get('error')}"})
                    continue
                
                embeddings_data = embedding_result["chunks"]
                logger.info(f"\U0001f389 Generated {len(embeddings_data)} embedding chunks for {filename}")
                
                # Update progress: embedding complete, starting Pinecone storage
                progress_service.update_progress(
                    expert_id=expert_id,
                    stage="pinecone_storage",
                    details={"filename": filename, "chunks_to_store": len(embeddings_data)}
                )
                
                # Step 4: Store in Pinecone
                logger.info(f"\U0001f4ca Storing embeddings in Pinecone for agent_id: {agent_id}")
                print(f"\U0001f4ca Storing {len(embeddings_data)} chunks in Pinecone for {filename}...")
                
                try:
                    pinecone_result = await pinecone_service.store_document_chunks(
                        chunks=embeddings_data,
                        agent_id=agent_id  # Use ElevenLabs agent_id as namespace
                    )
                    
                    if not pinecone_result["success"]:
                        logger.error(f"\U0001f6ab Pinecone storage failed for {filename}: {pinecone_result.get('error')}")
                        print(f"\U0001f6ab Pinecone storage failed for {filename}: {pinecone_result.get('error')}")
                        failed_files.append({"file_id": file_id, "error": f"Pinecone storage failed: {pinecone_result.get('error')}"})
                        continue
                    
                    print(f"✅ Pinecone storage completed for {filename}: {pinecone_result.get('upserted_count', 0)} vectors stored")
                    
                except Exception as pinecone_error:
                    logger.error(f"\U0001f6ab Pinecone storage exception for {filename}: {str(pinecone_error)}")
                    print(f"\U0001f6ab Pinecone storage exception for {filename}: {str(pinecone_error)}")
                    failed_files.append({"file_id": file_id, "error": f"Pinecone storage exception: {str(pinecone_error)}"})
                    continue
                
                processed_count += 1
                logger.info(f"\U0001f389 Successfully processed {filename} for expert {expert_id}")
                print(f"\U0001f389 Successfully processed {filename} for expert {expert_id}")
                
                # Update progress: file completed
                file_progress = ((file_index + 1) / len(selected_files)) * 100
                progress_service.update_progress(
                    expert_id=expert_id,
                    processed_files=processed_count,
                    progress_percentage=file_progress,
                    details={"last_completed_file": filename}
                )
                
            except Exception as e:
                logger.error(f"\U0001f6ab Error processing file {file_id}: {str(e)}")
                print(f"\U0001f6ab Error processing file {file_id}: {str(e)}")
                failed_files.append({"file_id": file_id, "error": str(e)})
        
        # Summary
        total_files = len(selected_files)
        success_rate = (processed_count / total_files) * 100 if total_files > 0 else 0
        
        logger.info(f"\U0001f389 File processing complete for expert {expert_id}")
        logger.info(f"\U0001f4ca Results: {processed_count}/{total_files} files processed successfully ({success_rate:.1f}%)")
        print(f"\U0001f389 Pinecone processing complete for expert {expert_id}")
        print(f"\U0001f4ca Results: {processed_count}/{total_files} files processed successfully ({success_rate:.1f}%)")
        
        if failed_files:
            logger.warning(f"\U0001f525 {len(failed_files)} files failed to process: {failed_files}")
            print(f"\U0001f525 {len(failed_files)} files failed to process")
        
        # Mark progress as completed or failed
        if processed_count == total_files:
            progress_service.mark_completed(
                expert_id=expert_id,
                metadata={
                    "processed_count": processed_count,
                    "total_files": total_files,
                    "success_rate": success_rate
                }
            )
        elif processed_count == 0:
            progress_service.mark_failed(
                expert_id=expert_id,
                error_message="All files failed to process",
                metadata={"failed_files": failed_files}
            )
        else:
            # Partial success
            progress_service.update_progress(
                expert_id=expert_id,
                status="completed",
                stage="complete",
                progress_percentage=100.0,
                failed_files=len(failed_files),
                details={"partial_success": True, "failed_files": failed_files}
            )
        
        return {
            "success": True,
            "message": f"Processed {processed_count}/{total_files} files successfully",
            "processed_count": processed_count,
            "total_files": total_files,
            "failed_files": failed_files,
            "success_rate": success_rate,
            "agent_id": agent_id  # Return the ElevenLabs agent_id for consistency
        }
        
    except Exception as e:
        logger.error(f"💥 Critical error in expert file processing: {str(e)}")
        
        # Mark progress as failed
        try:
            progress_service = ExpertProcessingProgressService(db)
            progress_service.mark_failed(
                expert_id=expert_id,
                error_message=str(e)
            )
        except:
            pass  # Don't fail if progress update fails
        
        return {
            "success": False,
            "error": f"File processing failed: {str(e)}",
            "processed_count": 0
        }

async def transcribe_and_save_audio(file: UploadFile, db: Session, user_id: str = None, folder_id: str = None, folder: str = "Uncategorized", custom_name: str = None) -> Dict[str, Any]:
    """
    Transcribe audio using ElevenLabs Speech-to-Text API and save to knowledge base
    
    Args:
        file: Audio file upload
        db: Database session
        user_id: User who uploaded the audio
        folder: Folder to save the transcription in
        
    Returns:
        Dict containing transcription results and saved file info
    """
    try:
        logger.info(f"Starting audio transcription: {file.filename}, content_type: {file.content_type}")
        print(f"🎤 Starting audio transcription: {file.filename}, content_type: {file.content_type}")
        
        # Validate file
        if not file.filename:
            logger.error("No filename provided")
            return {"success": False, "error": "No file provided"}
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            logger.error("File is empty")
            return {"success": False, "error": "File is empty"}
        
        logger.info(f"File size: {len(file_content)} bytes")
        print(f"📊 File size: {len(file_content)} bytes")
        
        # No file size limit for audio files
        
        # Validate audio file type - be more lenient with content types
        allowed_audio_types = [
            'audio/mpeg',
            'audio/mp3',
            'audio/wav',
            'audio/webm',
            'audio/webm;codecs=opus',
            'audio/ogg',
            'audio/m4a',
            'audio/x-m4a',
            'audio/mp4'
        ]
        
        # Check if content type starts with audio/ or is in allowed list
        is_audio = file.content_type and (
            file.content_type.startswith('audio/') or 
            file.content_type in allowed_audio_types
        )
        
        if not is_audio:
            logger.error(f"Unsupported audio type: {file.content_type}")
            return {"success": False, "error": f"Audio type '{file.content_type}' not supported. Supported: MP3, WAV, WebM, OGG, M4A"}
        
        logger.info(f"Audio validation passed: {file.filename} ({len(file_content)} bytes)")
        print(f"✅ Audio validation passed")
        
        # Get ElevenLabs API key from environment
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            return {"success": False, "error": "ElevenLabs API key not configured"}
        
        # Call ElevenLabs Speech-to-Text API
        logger.info("Calling ElevenLabs Speech-to-Text API...")
        print(f"🌐 Calling ElevenLabs Speech-to-Text API...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Prepare multipart form data
            files_data = {
                "file": (file.filename, file_content, file.content_type)
            }
            
            # Optional parameters - use scribe_v1 for speech-to-text
            form_data = {
                "model_id": "scribe_v1"  # ElevenLabs speech-to-text model
            }
            
            try:
                response = await client.post(
                    "https://api.elevenlabs.io/v1/speech-to-text",
                    headers={
                        "xi-api-key": elevenlabs_api_key
                    },
                    files=files_data,
                    data=form_data
                )
                
                logger.info(f"ElevenLabs API response status: {response.status_code}")
                print(f"📡 ElevenLabs API response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"ElevenLabs API error: {response.status_code} - {error_detail}")
                    print(f"❌ ElevenLabs API error: {response.status_code} - {error_detail}")
                    return {
                        "success": False,
                        "error": f"Transcription failed: {error_detail}"
                    }
                
                transcription_result = response.json()
                logger.info(f"Transcription result keys: {transcription_result.keys()}")
                print(f"✅ Transcription successful")
                
            except httpx.HTTPError as http_err:
                logger.error(f"HTTP error during transcription: {str(http_err)}")
                print(f"❌ HTTP error during transcription: {str(http_err)}")
                return {
                    "success": False,
                    "error": f"Network error during transcription: {str(http_err)}"
                }
        
        # Extract transcribed text
        transcribed_text = transcription_result.get("text", "")
        
        if not transcribed_text or len(transcribed_text.strip()) == 0:
            return {"success": False, "error": "No text could be transcribed from the audio"}
        
        logger.info(f"Transcription successful: {len(transcribed_text)} characters")
        print(f"🎤 Transcribed {len(transcribed_text)} characters from {file.filename}")
        
        # Create metadata for the transcription
        word_count = len(transcribed_text.split())
        language_code = transcription_result.get("language_code", "unknown")
        
        extraction_result = {
            "success": True,
            "text": transcribed_text,
            "content_type": "audio/transcription",
            "filename": file.filename,
            "word_count": word_count,
            "metadata": {
                "document_type": "audio_transcription",
                "language": language_code,
                "page_count": 1,
                "has_images": False,
                "has_tables": False,
                "extracted_text_preview": transcribed_text[:500] + "..." if len(transcribed_text) > 500 else transcribed_text,
                "transcription_source": "elevenlabs",
                "original_audio_type": file.content_type
            }
        }
        
        # Save transcription as a text file in the knowledge base
        file_service = FileService(db)
        
        # Convert transcribed text to bytes for storage
        text_content = transcribed_text.encode('utf-8')
        
        # Generate filename for transcription
        if custom_name:
            transcription_filename = custom_name if custom_name.endswith('.txt') else f"{custom_name}.txt"
        else:
            base_filename = os.path.splitext(file.filename)[0]
            transcription_filename = f"{base_filename}_transcription.txt"
        
        upload_result = file_service.upload_file(
            file_content=text_content,
            file_name=transcription_filename,
            content_type="text/plain",
            file_size=len(text_content),
            user_id=user_id,
            extraction_result=extraction_result,
            folder_id=folder_id,
            folder=folder
        )
        
        if not upload_result["success"]:
            logger.error(f"Failed to save transcription: {upload_result.get('error')}")
            return upload_result
        
        logger.info(f"Transcription saved successfully with ID: {upload_result['id']}")
        print(f"✅ Transcription saved to knowledge base: {transcription_filename}")
        
        return {
            "success": True,
            "message": "Audio transcribed and saved successfully",
            "transcription": {
                "text": transcribed_text,
                "word_count": word_count,
                "language": language_code,
                "preview": transcribed_text[:200] + "..." if len(transcribed_text) > 200 else transcribed_text
            },
            "file": {
                "id": upload_result["id"],
                "name": transcription_filename,
                "url": upload_result["url"],
                "s3_key": upload_result["s3_key"]
            }
        }
        
    except httpx.TimeoutException:
        logger.error("ElevenLabs API timeout")
        return {"success": False, "error": "Transcription request timed out. Please try with a shorter audio file."}
    except Exception as e:
        logger.error(f"Audio transcription failed: {str(e)}")
        return {"success": False, "error": f"Transcription failed: {str(e)}"}

async def transcribe_youtube_video(youtube_url: str, db: Session, user_id: str = None, folder_id: str = None, custom_name: str = None) -> Dict[str, Any]:
    """
    Download audio from YouTube video and transcribe using ElevenLabs
    Automatically splits long videos into chunks
    
    Args:
        youtube_url: YouTube video URL
        db: Database session
        user_id: User who requested the transcription
        folder: Folder to save the transcription in
        
    Returns:
        Dict containing transcription results and saved file info
    """
    temp_files = []
    
    try:
        logger.info(f"Starting YouTube video transcription: {youtube_url}")
        print(f"🎬 Starting YouTube video transcription")
        
        # Step 1: Get video info
        video_info = youtube_service.get_video_info(youtube_url)
        if not video_info.get("success"):
            return video_info
        
        video_title = video_info["title"]
        video_duration = video_info["duration"]
        
        logger.info(f"Video: {video_title}, Duration: {video_duration}s")
        
        # Step 2: Download audio
        download_result = youtube_service.download_audio(youtube_url)
        if not download_result["success"]:
            return download_result
        
        audio_path = download_result["audio_path"]
        temp_files.append(audio_path)
        
        file_size_mb = download_result["file_size"] / (1024 * 1024)
        logger.info(f"Audio file size: {file_size_mb:.2f} MB")
        
        # Step 3: Check if we need to split into chunks
        chunk_paths = []
        if file_size_mb > 20 or video_duration > 600:  # > 20MB or > 10 minutes
            logger.info("Audio is large, splitting into chunks")
            print(f"📦 Video is long, splitting into manageable chunks...")
            chunk_paths = youtube_service.split_audio_into_chunks(audio_path, chunk_duration_minutes=10)
            temp_files.extend(chunk_paths)
        else:
            chunk_paths = [audio_path]
        
        logger.info(f"Processing {len(chunk_paths)} audio chunk(s)")
        print(f"🎤 Transcribing {len(chunk_paths)} audio chunk(s) with ElevenLabs...")
        
        # Step 4: Transcribe each chunk
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            return {"success": False, "error": "ElevenLabs API key not configured"}
        
        all_transcriptions = []
        total_chunks = len(chunk_paths)
        
        for idx, chunk_path in enumerate(chunk_paths, 1):
            try:
                logger.info(f"Transcribing chunk {idx}/{total_chunks}")
                print(f"🎙️ Transcribing chunk {idx}/{total_chunks}...")
                
                # Read chunk file
                with open(chunk_path, 'rb') as f:
                    chunk_content = f.read()
                
                # Call ElevenLabs API
                async with httpx.AsyncClient(timeout=120.0) as client:
                    files_data = {
                        "file": (f"chunk_{idx}.mp3", chunk_content, "audio/mpeg")
                    }
                    
                    form_data = {
                        "model_id": "scribe_v1"
                    }
                    
                    response = await client.post(
                        "https://api.elevenlabs.io/v1/speech-to-text",
                        headers={"xi-api-key": elevenlabs_api_key},
                        files=files_data,
                        data=form_data
                    )
                    
                    if response.status_code != 200:
                        error_detail = response.text
                        logger.error(f"ElevenLabs API error for chunk {idx}: {response.status_code} - {error_detail}")
                        print(f"❌ Transcription failed for chunk {idx}: {error_detail}")
                        continue
                    
                    result = response.json()
                    transcribed_text = result.get("text", "")
                    
                    if transcribed_text:
                        all_transcriptions.append({
                            "chunk": idx,
                            "text": transcribed_text,
                            "language": result.get("language_code", "unknown")
                        })
                        logger.info(f"✅ Chunk {idx} transcribed: {len(transcribed_text)} characters")
                        print(f"✅ Chunk {idx}/{total_chunks} complete: {len(transcribed_text)} characters")
                
            except Exception as chunk_error:
                logger.error(f"Error transcribing chunk {idx}: {str(chunk_error)}")
                print(f"❌ Error transcribing chunk {idx}: {str(chunk_error)}")
                continue
        
        # Step 5: Combine all transcriptions
        if not all_transcriptions:
            return {"success": False, "error": "No transcription could be generated from the video"}
        
        # Combine transcriptions with chunk markers
        combined_text = ""
        for trans in all_transcriptions:
            if len(chunk_paths) > 1:
                combined_text += f"\n\n=== Part {trans['chunk']}/{total_chunks} ===\n\n"
            combined_text += trans['text']
        
        combined_text = combined_text.strip()
        word_count = len(combined_text.split())
        language = all_transcriptions[0].get("language", "unknown")
        
        logger.info(f"Combined transcription: {len(combined_text)} characters, {word_count} words")
        print(f"📝 Total transcription: {word_count} words")
        
        # Step 6: Save to knowledge base
        extraction_result = {
            "success": True,
            "text": combined_text,
            "content_type": "video/transcription",
            "filename": f"{video_title}.txt",
            "word_count": word_count,
            "metadata": {
                "document_type": "youtube_transcription",
                "language": language,
                "page_count": 1,
                "has_images": False,
                "has_tables": False,
                "extracted_text_preview": combined_text[:500] + "..." if len(combined_text) > 500 else combined_text,
                "transcription_source": "elevenlabs",
                "youtube_url": youtube_url,
                "video_title": video_title,
                "video_duration": video_duration,
                "video_channel": video_info.get("channel", "Unknown"),
                "chunks_processed": len(all_transcriptions)
            }
        }
        
        file_service = FileService(db)
        text_content = combined_text.encode('utf-8')
        
        # Convert folder_id to folder_name if provided
        folder_name = "Uncategorized"  # Default
        if folder_id:
            try:
                from models.folder_db import FolderDB
                folder_record = db.query(FolderDB).filter(FolderDB.id == folder_id).first()
                if folder_record:
                    folder_name = folder_record.name
                else:
                    logger.warning(f"Folder ID {folder_id} not found, using Uncategorized")
            except Exception as e:
                logger.error(f"Error getting folder name: {str(e)}")
        
        # Create filename for transcription
        if custom_name:
            transcription_filename = custom_name if custom_name.endswith('.txt') else f"{custom_name}.txt"
        else:
            # Create safe filename from video title
            safe_title = re.sub(r'[^\w\s-]', '', video_info["title"])
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            safe_title = safe_title[:100]  # Limit length
            transcription_filename = f"{safe_title}_youtube_transcription.txt"
        
        upload_result = file_service.upload_file(
            file_content=text_content,
            file_name=transcription_filename,
            content_type="text/plain",
            file_size=len(text_content),
            user_id=user_id,
            extraction_result=extraction_result,
            folder_id=folder_id,
            folder=folder_name
        )
        
        if not upload_result["success"]:
            logger.error(f"Failed to save transcription: {upload_result.get('error')}")
            return upload_result
        
        logger.info(f"YouTube transcription saved successfully with ID: {upload_result['id']}")
        print(f"✅ YouTube transcription saved to knowledge base!")
        
        return {
            "success": True,
            "message": "YouTube video transcribed and saved successfully",
            "video": {
                "title": video_title,
                "duration": video_info["duration_formatted"],
                "channel": video_info.get("channel", "Unknown"),
                "url": youtube_url
            },
            "transcription": {
                "text": combined_text,
                "word_count": word_count,
                "language": language,
                "chunks_processed": len(all_transcriptions),
                "preview": combined_text[:200] + "..." if len(combined_text) > 200 else combined_text
            },
            "file": {
                "id": upload_result["id"],
                "name": transcription_filename,
                "url": upload_result["url"],
                "s3_key": upload_result["s3_key"]
            }
        }
        
    except Exception as e:
        logger.error(f"YouTube transcription failed: {str(e)}")
        print(f"❌ YouTube transcription failed: {str(e)}")
        return {"success": False, "error": f"YouTube transcription failed: {str(e)}"}
    
    finally:
        # Clean up temporary files
        if temp_files:
            logger.info(f"Cleaning up {len(temp_files)} temporary files")
            youtube_service.cleanup_files(temp_files)


async def scrape_and_save_website(url: str, db: Session, user_id: str = None, folder_id: str = None, folder: str = "Uncategorized", custom_name: str = None) -> Dict[str, Any]:
    """Scrape website content and save to knowledge base"""
    try:
        logger.info(f"🌐 Starting website scraping for URL: {url}")
        print(f"🌐 Scraping website: {url}")
        
        # Scrape the website
        scrape_result = web_scraper_service.scrape_url(url)
        
        if not scrape_result["success"]:
            logger.error(f"Failed to scrape website: {scrape_result.get('error')}")
            return scrape_result
        
        content = scrape_result["content"]
        metadata = scrape_result["metadata"]
        
        logger.info(f"🌐 Web Scraper: Retrieved content length: {len(content)} characters")
        logger.info(f"🌐 Web Scraper: Metadata keys: {list(metadata.keys())}")
        logger.info(f"🌐 Web Scraper: Page title: {metadata.get('title', 'No title')}")
        
        # Generate filename
        if custom_name:
            filename = f"{custom_name}.txt"
        else:
            # Use page title or domain as filename
            title = metadata.get('title', metadata.get('domain', 'webpage'))
            # Clean title for filename - handle empty title case
            if not title or title.strip() == '':
                title = metadata.get('domain', 'webpage')
            safe_title = re.sub(r'[^\w\s-]', '', str(title)).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            # Ensure we have a valid filename
            if not safe_title:
                safe_title = 'scraped-webpage'
            filename = f"{safe_title[:50]}_scraped.txt"
        
        logger.info(f"🌐 Web Scraper: Generated filename: {filename}")
        
        logger.info(f"📝 Scraped {metadata.get('word_count', 0)} words from {metadata.get('title', url)}")
        
        # Create extraction result matching document_processor format
        extraction_result = {
            "success": True,
            "text": content,  # Use "text" key to match document_processor
            "content_type": "text/plain",
            "filename": filename,
            "word_count": metadata.get("word_count", len(content.split())),
            "metadata": {
                **metadata,
                "source_type": "website_scraping",
                "original_url": url,
                "scraped_at": metadata.get("scraped_at"),
                "extraction_method": "web_scraper",
                "document_type": "webpage",
                "language": "en"
            }
        }
        
        # Get folder name for metadata
        folder_name = folder
        if folder_id and folder_id != "uncategorized":
            try:
                # You might want to get the actual folder name from the database
                # For now, we'll use the provided folder parameter
                pass
            except:
                folder_name = "Uncategorized"
        
        # Save to knowledge base using existing file service
        file_service = FileService(db)
        upload_result = file_service.upload_file(
            file_content=content.encode('utf-8'),
            file_name=filename,
            content_type="text/plain",
            file_size=len(content.encode('utf-8')),
            user_id=user_id,
            extraction_result=extraction_result,
            folder_id=folder_id,
            folder=folder_name
        )
        
        if not upload_result["success"]:
            logger.error(f"Failed to save scraped content: {upload_result.get('error')}")
            return upload_result
        
        logger.info(f"Website content saved successfully with ID: {upload_result['id']}")
        print(f"✅ Website content saved to knowledge base!")
        
        return {
            "success": True,
            "message": "Website scraped and saved successfully",
            "website": {
                "title": metadata.get('title', 'Untitled'),
                "url": url,
                "domain": metadata.get('domain', ''),
                "description": metadata.get('description', metadata.get('og_description', ''))
            },
            "content": {
                "text": content,
                "word_count": metadata.get('word_count', 0),
                "content_length": metadata.get('content_length', 0),
                "preview": content[:200] + "..." if len(content) > 200 else content
            },
            "file": {
                "id": upload_result["id"],
                "name": filename,
                "url": upload_result["url"],
                "s3_key": upload_result["s3_key"]
            }
        }
        
    except Exception as e:
        logger.error(f"Website scraping failed: {str(e)}")
        print(f"❌ Website scraping failed: {str(e)}")
        return {"success": False, "error": f"Website scraping failed: {str(e)}"}


async def get_website_preview(url: str) -> Dict[str, Any]:
    """Get website preview information without full scraping"""
    try:
        logger.info(f"🔍 Getting website preview for: {url}")
        
        # Get page info
        preview_result = web_scraper_service.get_page_info(url)
        
        if not preview_result["success"]:
            logger.error(f"Failed to get website preview: {preview_result.get('error')}")
            return preview_result
        
        logger.info(f"✅ Retrieved preview for {preview_result['metadata'].get('title', url)}")
        
        return {
            "success": True,
            "preview": {
                "title": preview_result["metadata"].get('title', 'Untitled'),
                "description": preview_result["metadata"].get('description', preview_result["metadata"].get('og_description', '')),
                "domain": preview_result["metadata"].get('domain', ''),
                "content_preview": preview_result.get('content_preview', ''),
                "url": url
            }
        }
        
    except Exception as e:
        logger.error(f"Website preview failed: {str(e)}")
        return {"success": False, "error": f"Website preview failed: {str(e)}"}

async def attach_knowledge_base_to_agent(agent_id: str, user_id: str = None) -> Dict[str, Any]:
    """
    Automatically attach knowledge base search capability to an agent
    
    Args:
        agent_id: Expert ID (our database ID) to attach knowledge base to
        user_id: User ID for context
        
    Returns:
        Dict containing attachment status
    """
    try:
        logger.info(f"Attaching knowledge base to expert {agent_id}")
        
        # First, get the expert from database to get the ElevenLabs agent ID
        from services.expert_service import ExpertService
        from config.database import SessionLocal
        
        db = SessionLocal()
        try:
            expert_service = ExpertService(db)
            expert_result = expert_service.get_expert(agent_id)
            
            if not expert_result.get("success"):
                logger.error(f"Expert {agent_id} not found: {expert_result.get('error')}")
                return {
                    "success": False,
                    "error": f"Expert not found: {expert_result.get('error')}",
                    "agent_id": agent_id,
                    "search_enabled": False
                }
            
            expert_data = expert_result["expert"]
            elevenlabs_agent_id = expert_data.get("elevenlabs_agent_id")
            
            if not elevenlabs_agent_id:
                logger.warning(f"Expert {agent_id} has no ElevenLabs agent ID")
                return {
                    "success": False,
                    "error": "Expert has no ElevenLabs agent configured",
                    "agent_id": agent_id,
                    "search_enabled": False
                }
            
            logger.info(f"Found ElevenLabs agent ID: {elevenlabs_agent_id} for expert {agent_id}")
            
            # Use the existing pinecone service method to add search tool
            attachment_result = await pinecone_service.add_search_tool_to_agent(
                agent_id=elevenlabs_agent_id,  # Use ElevenLabs agent ID
                user_id=user_id
            )
            
            if attachment_result.get("success"):
                logger.info(f"Successfully attached knowledge base to expert {agent_id} (ElevenLabs agent: {elevenlabs_agent_id})")
                return {
                    "success": True,
                    "message": "Knowledge base attached to agent for chat",
                    "agent_id": agent_id,
                    "elevenlabs_agent_id": elevenlabs_agent_id,
                    "search_enabled": True
                }
            else:
                logger.warning(f"Failed to attach knowledge base to expert {agent_id}: {attachment_result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "error": attachment_result.get("error", "Failed to attach knowledge base"),
                    "agent_id": agent_id,
                    "elevenlabs_agent_id": elevenlabs_agent_id,
                    "search_enabled": False
                }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error attaching knowledge base to expert {agent_id}: {str(e)}")
        return {
            "success": False,
            "error": f"Attachment failed: {str(e)}",
            "agent_id": agent_id,
            "search_enabled": False
        }
