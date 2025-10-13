import os
import logging
from typing import Dict, Any, List
import openai
import re
from datetime import datetime
import time
import asyncio

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service to chunk text and generate embeddings for knowledge base"""
    
    def __init__(self):
        # Use hardcoded key directly (temporary for development)
        self.openai_api_key = "REMOVED_API_KEY"

        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        else:
            logger.warning("OPENAI_API_KEY not found - embedding generation will fail")
        
        # Embedding model configuration
        self.embedding_model = "text-embedding-3-large"  # 3072 dimensions
        self.chunk_size = 400  # Reduced from 800 for faster processing
        self.chunk_overlap = 50   # Reduced from 100
        self.max_chunk_size = 500  # Reduced from 1000
        
        # Performance optimizations
        self.batch_size = 10  # Process multiple chunks in one API call
        self.max_concurrent_batches = 3  # Process batches concurrently
        self.rate_limit_delay = 0.1  # Small delay between API calls
        self.max_chunks_per_document = 1000  # Limit to prevent extremely long processing
    
    def process_document(self, text: str, file_id: str, filename: str, user_id: str = None, progress_callback=None) -> Dict[str, Any]:
        """
        Process a document: chunk text and generate embeddings
        
        Args:
            text: Extracted text content
            file_id: Unique file identifier
            filename: Original filename
            user_id: User who uploaded the file
            progress_callback: Optional callback function(batch_num, total_batches, chunks_completed, total_chunks)
            
        Returns:
            Dict containing chunks with embeddings and metadata
        """
        try:
            start_time = time.time()
            print(f"🧠 Embedding Service: Processing document {filename} (file_id: {file_id})")
            print(f"📊 Text length: {len(text)} characters")
            logger.info(f"Starting document processing for {filename}")
            
            # Step 1: Clean and prepare text
            print(f"🧹 Embedding Service: Cleaning text for {filename}")
            cleaned_text = self._clean_text(text)
            clean_time = time.time() - start_time
            print(f"✅ Text cleaning completed in {clean_time:.2f}s")
            
            if len(cleaned_text.strip()) == 0:
                print(f"❌ Embedding Service: No valid text content in {filename}")
                return {
                    "success": False,
                    "error": "No valid text content to process"
                }
            
            # Step 2: Split text into chunks
            print(f"✂️ Embedding Service: Chunking text for {filename}")
            chunk_start = time.time()
            chunks = self._chunk_text(cleaned_text)
            chunk_time = time.time() - chunk_start
            print(f"📦 Embedding Service: Created {len(chunks)} chunks from {filename} in {chunk_time:.2f}s")
            logger.info(f"Created {len(chunks)} chunks in {chunk_time:.2f}s")
            
            if not chunks:
                print(f"❌ Embedding Service: Failed to create text chunks for {filename}")
                return {
                    "success": False,
                    "error": "Failed to create text chunks"
                }
            
            # Check if document is too large
            if len(chunks) > self.max_chunks_per_document:
                print(f"⚠️ Document too large: {len(chunks)} chunks exceeds limit of {self.max_chunks_per_document}")
                print(f"📝 Processing only first {self.max_chunks_per_document} chunks")
                chunks = chunks[:self.max_chunks_per_document]
                logger.warning(f"Document {filename} truncated to {self.max_chunks_per_document} chunks")
            
            # Step 3: Generate embeddings for chunks in batches
            print(f"🚀 Embedding Service: Starting batch embedding generation for {len(chunks)} chunks (batch size: {self.batch_size})")
            processed_chunks = []
            embedding_start = time.time()
            
            # Process chunks in batches
            total_batches = (len(chunks) - 1) // self.batch_size + 1
            
            for batch_start in range(0, len(chunks), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(chunks))
                batch_chunks = chunks[batch_start:batch_end]
                batch_indices = list(range(batch_start, batch_end))
                batch_num = batch_start // self.batch_size + 1
                
                print(f"🔄 Processing batch {batch_num}/{total_batches} (chunks {batch_start+1}-{batch_end})")
                
                # Generate embeddings for this batch
                batch_result = self._generate_embeddings_batch(batch_chunks)
                
                if batch_result["success"]:
                    batch_embeddings = batch_result["embeddings"]
                    
                    # Create chunk data for successfully embedded chunks
                    for i, (chunk_text, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                        chunk_index = batch_indices[i]
                        chunk_data = {
                            "id": f"{file_id}_chunk_{chunk_index}",
                            "text": chunk_text,
                            "embedding": embedding,
                            "metadata": {
                                "file_id": file_id,
                                "filename": filename,
                                "chunk_index": chunk_index,
                                "total_chunks": len(chunks),
                                "user_id": user_id,
                                "word_count": len(chunk_text.split()),
                                "text": chunk_text,  # Include text in metadata for retrieval
                                "created_at": datetime.utcnow().isoformat()
                            }
                        }
                        processed_chunks.append(chunk_data)
                    
                    print(f"✅ Batch {batch_num} completed: {len(batch_embeddings)}/{len(batch_chunks)} chunks embedded")
                    
                    # Call progress callback if provided
                    if progress_callback:
                        try:
                            progress_callback(batch_num, total_batches, len(processed_chunks), len(chunks))
                        except Exception as e:
                            logger.warning(f"Progress callback failed: {str(e)}")
                else:
                    print(f"❌ Batch {batch_num} failed: {batch_result['error']}")
                
                # Small delay to avoid rate limiting
                if batch_end < len(chunks):
                    time.sleep(self.rate_limit_delay)
                
                # Progress update every batch
                completed = len(processed_chunks)
                total = len(chunks)
                elapsed = time.time() - embedding_start
                avg_time_per_chunk = elapsed / completed if completed > 0 else 0
                remaining = (total - completed) * avg_time_per_chunk
                print(f"📊 Progress: {completed}/{total} chunks ({(completed/total*100):.1f}%) - Est. {remaining:.1f}s remaining")
                
                # Final progress callback after batch
                if progress_callback and completed > 0:
                    try:
                        progress_callback(batch_num, total_batches, completed, total)
                    except Exception as e:
                        logger.warning(f"Progress callback failed: {str(e)}")
            
            total_embedding_time = time.time() - embedding_start
            
            if not processed_chunks:
                print(f"❌ Embedding Service: Failed to generate embeddings for any chunks in {filename}")
                return {
                    "success": False,
                    "error": "Failed to generate embeddings for any chunks"
                }
            
            # Final progress callback - 100% complete
            if progress_callback:
                try:
                    progress_callback(total_batches, total_batches, len(processed_chunks), len(chunks))
                except Exception as e:
                    logger.warning(f"Final progress callback failed: {str(e)}")
            
            total_time = time.time() - start_time
            # Calculate original chunks before truncation
            was_truncated = len(chunks) == self.max_chunks_per_document
            original_chunks = len(chunks) if not was_truncated else len(chunks) + 1  # Approximate
            print(f"🎉 Embedding Service: Successfully processed {len(processed_chunks)}/{original_chunks} chunks for {filename}")
            print(f"⏱️ Total processing time: {total_time:.2f}s (Cleaning: {clean_time:.2f}s, Chunking: {chunk_time:.2f}s, Embedding: {total_embedding_time:.2f}s)")
            logger.info(f"Document processing completed in {total_time:.2f}s")
            
            return {
                "success": True,
                "chunks": processed_chunks,
                "total_chunks": len(processed_chunks),
                "original_chunks": original_chunks,
                "chunks_truncated": original_chunks > len(processed_chunks),
                "original_word_count": len(text.split()),
                "processed_word_count": sum(len(chunk["text"].split()) for chunk in processed_chunks),
                "processing_time": total_time
            }
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            print(f"💥 Embedding Service: Critical error - {str(e)}")
            return {
                "success": False,
                "error": f"Document processing failed: {str(e)}"
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        try:
            logger.info(f"Cleaning text of length {len(text)}")
            
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove special characters but keep punctuation
            text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\\]', ' ', text)
            
            # Remove multiple consecutive punctuation
            text = re.sub(r'[\.]{3,}', '...', text)
            text = re.sub(r'[\!\?]{2,}', '!', text)
            
            # Normalize line breaks
            text = re.sub(r'\n+', '\n', text)
            
            cleaned = text.strip()
            logger.info(f"Text cleaned: {len(text)} -> {len(cleaned)} characters")
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            print(f"⚠️ Text cleaning error: {str(e)}")
            return text
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        try:
            words = text.split()
            logger.info(f"Chunking text with {len(words)} words")
            
            if len(words) <= self.chunk_size:
                logger.info("Text fits in single chunk")
                return [text]
            
            chunks = []
            start = 0
            iteration = 0
            max_iterations = len(words) * 2  # Safety limit to prevent infinite loops
            
            while start < len(words) and iteration < max_iterations:
                iteration += 1
                if iteration % 20 == 0:
                    logger.info(f"Chunking iteration {iteration}, start position: {start}/{len(words)}")
                
                # Calculate end position
                end = min(start + self.chunk_size, len(words))
                
                # Extract chunk
                chunk_words = words[start:end]
                chunk_text = ' '.join(chunk_words)
                
                # Try to end at sentence boundary if possible
                if end < len(words):
                    # Look for sentence endings in the last 50 words
                    last_part = ' '.join(chunk_words[-50:])
                    sentence_endings = ['.', '!', '?', '\n']
                    
                    for ending in sentence_endings:
                        if ending in last_part:
                            # Find the last occurrence of sentence ending
                            last_sentence_end = last_part.rfind(ending)
                            if last_sentence_end > 0:
                                # Adjust chunk to end at sentence boundary
                                adjusted_chunk = ' '.join(chunk_words[:-50]) + ' ' + last_part[:last_sentence_end + 1]
                                chunk_text = adjusted_chunk.strip()
                                break
                
                chunks.append(chunk_text)
                
                # Move start position with overlap
                start = end - self.chunk_overlap
                
                # Prevent infinite loop - ensure progress
                if start <= end - self.chunk_overlap:
                    start = end - self.chunk_overlap
                else:
                    # If overlap would cause no progress, advance at least one word
                    start = end - 1
                    
                # Final safety check
                if start >= end or start >= len(words):
                    break
            
            logger.info(f"Chunking completed: {len(chunks)} chunks created in {iteration} iterations")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            print(f"❌ Text chunking error: {str(e)}")
            return [text]  # Return original text as single chunk if chunking fails
    
    def _generate_embeddings_batch(self, chunk_texts: List[str]) -> Dict[str, Any]:
        """Generate embeddings for multiple text chunks in a single API call"""
        try:
            if not self.openai_api_key:
                return {
                    "success": False,
                    "error": "OpenAI API key not configured"
                }
            
            total_chars = sum(len(text) for text in chunk_texts)
            print(f"🔗 Embedding Service: Batch API call for {len(chunk_texts)} chunks ({total_chars} total characters)")
            api_start = time.time()
            
            # OpenAI supports batch embedding requests
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=chunk_texts,
                timeout=60  # Increased timeout for batches
            )
            
            api_time = time.time() - api_start
            print(f"✅ Batch API call completed in {api_time:.2f}s ({api_time/len(chunk_texts):.2f}s per chunk)")
            
            # Extract embeddings from response
            embeddings = [data.embedding for data in response.data]
            
            return {
                "success": True,
                "embeddings": embeddings,
                "model": self.embedding_model,
                "batch_size": len(chunk_texts),
                "api_time": api_time
            }
            
        except Exception as e:
            api_time = time.time() - api_start if 'api_start' in locals() else 0
            logger.error(f"Error in batch embedding generation: {str(e)}")
            print(f"❌ Batch embedding error after {api_time:.2f}s: {str(e)}")
            return {
                "success": False,
                "error": f"Batch embedding generation failed: {str(e)}"
            }
    
    def generate_query_embedding(self, query: str) -> Dict[str, Any]:
        """Generate embedding for a search query"""
        # For single queries, we can still use the batch method with one item
        batch_result = self._generate_embeddings_batch([query])
        if batch_result["success"] and len(batch_result["embeddings"]) > 0:
            return {
                "success": True,
                "embedding": batch_result["embeddings"][0],
                "model": batch_result["model"],
                "dimensions": len(batch_result["embeddings"][0]),
                "api_time": batch_result["api_time"]
            }
        else:
            return {
                "success": False,
                "error": batch_result.get("error", "Failed to generate query embedding")
            }

# Create singleton instance
embedding_service = EmbeddingService()
