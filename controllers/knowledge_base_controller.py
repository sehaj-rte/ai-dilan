from typing import Dict, Any
from fastapi import UploadFile, HTTPException
from services.file_service import FileService
from services.document_processor import document_processor
from services.embedding_service import embedding_service
from services.pinecone_service import pinecone_service
from services.aws_s3_service import s3_service
from services.expert_processing_progress_service import ExpertProcessingProgressService
from models.file_db import FileDB
from sqlalchemy.orm import Session
import logging
import uuid

logger = logging.getLogger(__name__)

async def upload_file(file: UploadFile, db: Session, user_id: str = None) -> Dict[str, Any]:
    """Upload file to knowledge base"""
    try:
        logger.info(f"Starting file upload: {file.filename}, content_type: {file.content_type}")
        
        # Validate file
        if not file.filename:
            logger.error("No filename provided")
            return {"success": False, "error": "No file provided"}
        
        # Check file size (limit to 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        file_content = file.file.read()
        
        logger.info(f"File size: {len(file_content)} bytes")
        
        if len(file_content) > max_size:
            logger.error(f"File size {len(file_content)} exceeds limit {max_size}")
            return {"success": False, "error": "File size exceeds 50MB limit"}
        
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
        
        # Extract text and metadata first (temporarily disabled)
        extraction_result = None
        # extraction_result = document_processor.extract_text(
        #     file_content=file_content,
        #     content_type=file.content_type,
        #     filename=file.filename
        # )
        
        # Upload file to S3 and save metadata
        logger.info("Starting file service upload")
        file_service = FileService(db)
        upload_result = file_service.upload_file(
            file_content=file_content,
            file_name=file.filename,
            content_type=file.content_type,
            file_size=len(file_content),
            user_id=user_id,
            extraction_result=extraction_result if extraction_result and extraction_result.get("success") else None
        )
        
        logger.info(f"File service upload result: {upload_result.get('success', False)}")
        
        if not upload_result["success"]:
            logger.error(f"File service upload failed: {upload_result.get('error', 'Unknown error')}")
            return upload_result
        
        file_id = upload_result["id"]
        logger.info(f"File uploaded successfully with ID: {file_id}")
        
        # Process document for knowledge base (temporarily disabled)
        processing_result = {"success": True, "message": "Processing temporarily disabled"}
        # processing_result = await process_document_for_knowledge_base(
        #     file_content=file_content,
        #     content_type=file.content_type,
        #     filename=file.filename,
        #     file_id=file_id,
        #     user_id=user_id
        # )
        
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

def get_files(db: Session, user_id: str = None) -> Dict[str, Any]:
    """Get all uploaded files"""
    try:
        file_service = FileService(db)
        return file_service.get_files(user_id=user_id)
        
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

async def process_document_for_knowledge_base(
    file_content: bytes, 
    content_type: str, 
    filename: str, 
    file_id: str, 
    user_id: str = None
) -> Dict[str, Any]:
    """
    Process uploaded document for knowledge base integration
    
    Args:
        file_content: Raw file content
        content_type: MIME type of the file
        filename: Original filename
        file_id: Unique file identifier
        user_id: User who uploaded the file
        
    Returns:
        Dict containing processing status and results
    """
    try:
        logger.info(f"Starting document processing for {filename} (file_id: {file_id})")
        
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
        
        # Step 2: Process document (chunk and embed)
        processing_result = embedding_service.process_document(
            text=extracted_text,
            file_id=file_id,
            filename=filename,
            user_id=user_id
        )
        
        if not processing_result["success"]:
            logger.error(f"Document processing failed for {filename}: {processing_result['error']}")
            return {
                "success": False,
                "error": f"Document processing failed: {processing_result['error']}",
                "stage": "document_processing"
            }
        
        chunks = processing_result["chunks"]
        total_chunks = processing_result["total_chunks"]
        
        logger.info(f"Created {total_chunks} chunks for {filename}")
        
        # Step 3: Store in Pinecone
        storage_result = await pinecone_service.store_document_chunks(
            chunks=chunks,
            user_id=user_id
        )
        
        if not storage_result["success"]:
            logger.error(f"Pinecone storage failed for {filename}: {storage_result['error']}")
            return {
                "success": False,
                "error": f"Knowledge base storage failed: {storage_result['error']}",
                "stage": "pinecone_storage"
            }
        
        logger.info(f"Successfully processed and stored {filename} in knowledge base")
        
        return {
            "success": True,
            "text_extraction": {
                "word_count": word_count,
                "content_type": content_type
            },
            "document_processing": {
                "total_chunks": total_chunks,
                "processed_word_count": processing_result["processed_word_count"]
            },
            "knowledge_base_storage": {
                "chunks_stored": storage_result["chunks_stored"],
                "namespace": storage_result["namespace"]
            }
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
                
                # Fallback to database if S3 failed or content not in S3
                if not file_content:
                    logger.info(f"📂 Trying to get file content from database for {file_id}")
                    print(f"📂 Trying to get file content from database for {file_id}")
                    file_record = file_service.db.query(FileDB).filter(FileDB.id == uuid.UUID(file_id)).first()
                    
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
                
                logger.info(f"📝 Extracting text from {filename}")
                
                # Step 2: Extract text from file
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
                pinecone_result = await pinecone_service.store_document_chunks(
                    chunks=embeddings_data,
                    agent_id=agent_id  # Use ElevenLabs agent_id as namespace
                )
                
                if not pinecone_result["success"]:
                    logger.error(f"\U0001f6ab Pinecone storage failed for {filename}: {pinecone_result.get('error')}")
                    print(f"\U0001f6ab Pinecone storage failed for {filename}: {pinecone_result.get('error')}")
                    failed_files.append({"file_id": file_id, "error": f"Pinecone storage failed: {pinecone_result.get('error')}"})
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
