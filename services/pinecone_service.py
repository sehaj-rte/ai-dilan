from typing import Dict, Any, List
import os
import logging
from pinecone import Pinecone
import openai
from services.elevenlabs_service import elevenlabs_service

logger = logging.getLogger(__name__)

class PineconeService:
    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.user_kb_index_name = os.getenv("PINECONE_USER_KB_INDEX", "user-knowledge-base")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.pinecone_api_key:
            logger.warning("PINECONE_API_KEY not set - Pinecone features disabled")
            self.user_kb_index = None
            return
        
        try:
            # Initialize Pinecone (v6.0.0 style)
            self.pc = Pinecone(api_key=self.pinecone_api_key)
            
            # Initialize user knowledge base index
            self.user_kb_index = None
            
            try:
                self.user_kb_index = self.pc.Index(self.user_kb_index_name)
                logger.info(f"User KB index '{self.user_kb_index_name}' initialized")
            except Exception as e:
                logger.warning(f"User KB index '{self.user_kb_index_name}' not available: {str(e)}")
                logger.info("You'll need to create the user knowledge base index in Pinecone dashboard")
            
            # Initialize OpenAI for embeddings
            if self.openai_api_key:
                openai.api_key = self.openai_api_key
            
            logger.info("Pinecone service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone service: {str(e)}")
            self.pc = None
            self.user_kb_index = None
    
    def get_index(self, index_type: str = "user_kb"):
        """Get the user knowledge base Pinecone index"""
        return self.user_kb_index
    
    async def add_search_tool_to_agent(self, agent_id: str, user_id: str = None) -> Dict[str, Any]:
        """
        Add a user knowledge base search tool to an ElevenLabs agent
        
        Args:
            agent_id: ElevenLabs agent ID
            user_id: User ID for namespace isolation
            
        Returns:
            Dict containing tool creation status
        """
        try:
            index = self.get_index()
            if not index:
                return {
                    "success": False,
                    "error": "User knowledge base not initialized"
                }
            
            # Create tool configuration for ElevenLabs
            tool_config = {
                "name": "search_user_knowledge",
                "description": "Search the user's uploaded documents and knowledge base for relevant information to answer questions. Use this when you need specific information from the user's files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant information in the user's knowledge base"
                        }
                    },
                    "required": ["query"]
                },
                "webhook_url": f"{os.getenv('BASE_URL', 'http://localhost:8000')}/tools/search-user-knowledge",
                "authentication": {
                    "type": "bearer",
                    "token": os.getenv("WEBHOOK_AUTH_TOKEN", "your-secret-token")
                }
            }
            
            # Add tool to ElevenLabs agent
            result = await elevenlabs_service.add_search_tool_to_agent(agent_id, tool_config)
            
            if result["success"]:
                logger.info(f"Successfully added user knowledge search tool to agent {agent_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error adding search tool to agent: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search(self, query: str, user_id: str = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Search user knowledge base with a text query (alias for search_user_knowledge)
        
        Args:
            query: Search query text
            user_id: User ID for namespace isolation
            top_k: Number of results to return
            
        Returns:
            Dict containing search results
        """
        print(f"\U0001f50d Pinecone Service: Searching user knowledge for query '{query}'")
        # Delegate to search_user_knowledge method
        return await self.search_user_knowledge(query, user_id, top_k)

    async def store_document_chunks(self, chunks: List[Dict[str, Any]], agent_id: str = None) -> Dict[str, Any]:
        """
        Store document chunks in agent's knowledge base index
        
        Args:
            chunks: List of processed chunks with embeddings and metadata
            agent_id: Agent ID for namespace isolation
            
        Returns:
            Dict containing storage status
        """
        try:
            print(f"\U0001f525 Pinecone Service: Storing document chunks for agent {agent_id}")
            if not self.user_kb_index:
                print(f"\U0001f6ab Pinecone Service: User knowledge base index not initialized")
                return {
                    "success": False,
                    "error": "User knowledge base index not initialized"
                }
            
            # Prepare vectors for upsert
            vectors = []
            for chunk in chunks:
                vector_data = {
                    "id": chunk["id"],
                    "values": chunk["embedding"],
                    "metadata": chunk["metadata"]
                }
                vectors.append(vector_data)
            
            # Use agent_id as namespace for isolation (changed from user_id format)
            namespace = agent_id if agent_id else "default"
            
            total_vectors = len(vectors)
            print(f"\U0001f4e5 Pinecone Service: Storing {total_vectors} vectors to namespace '{namespace}'")
            
            # Pinecone has a 2MB payload limit, so chunk into smaller batches
            # Each vector is roughly 15KB (3072*4 bytes + metadata), so limit to ~130 vectors per batch for 2MB
            max_vectors_per_batch = 100  # Reduced from 200 to stay under 2MB limit
            total_upserted = 0
            
            # Process vectors in smaller batches to avoid payload size limits
            for i in range(0, total_vectors, max_vectors_per_batch):
                batch_end = min(i + max_vectors_per_batch, total_vectors)
                batch_vectors = vectors[i:batch_end]
                batch_number = (i // max_vectors_per_batch) + 1
                total_batches = (total_vectors + max_vectors_per_batch - 1) // max_vectors_per_batch
                
                print(f"📦 Processing batch {batch_number}/{total_batches} ({len(batch_vectors)} vectors)")
                
                try:
                    # Upsert this batch to Pinecone
                    upsert_response = self.user_kb_index.upsert(
                        vectors=batch_vectors,
                        namespace=namespace
                    )
                    
                    batch_upserted = upsert_response.upserted_count
                    total_upserted += batch_upserted
                    
                    print(f"✅ Batch {batch_number}/{total_batches} completed: {batch_upserted} vectors stored")
                    
                    # Small delay between batches to avoid rate limiting
                    if batch_end < total_vectors:
                        import time
                        time.sleep(0.1)
                        
                except Exception as batch_error:
                    print(f"❌ Batch {batch_number}/{total_batches} failed: {str(batch_error)}")
                    logger.error(f"Error storing batch {batch_number}: {str(batch_error)}")
                    return {
                        "success": False,
                        "error": f"Batch storage failed: {str(batch_error)}",
                        "stored_so_far": total_upserted
                    }
            
            logger.info(f"Successfully stored {total_upserted} chunks for agent {agent_id} in namespace {namespace}")
            print(f"\U0001f389 Pinecone Service: Successfully stored {total_upserted}/{total_vectors} chunks for agent {agent_id}")
            
            return {
                "success": True,
                "upserted_count": total_upserted,
                "namespace": namespace,
                "chunks_stored": total_upserted,
                "total_requested": total_vectors,
                "batches_processed": total_batches
            }
            
        except Exception as e:
            logger.error(f"Error storing document chunks: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_user_knowledge(self, query: str, agent_id: str = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Search agent's knowledge base with a text query
        
        Args:
            query: Search query text
            agent_id: Agent ID for namespace isolation
            top_k: Number of results to return
            
        Returns:
            Dict containing search results
        """
        try:
            print(f"\U0001f50d Pinecone Service: Searching agent knowledge for agent {agent_id} with query '{query}'")
            if not self.user_kb_index:
                print(f"\U0001f6ab Pinecone Service: User knowledge base index not initialized")
                return {
                    "success": False,
                    "error": "User knowledge base index not initialized"
                }
            
            # Generate embedding for the query
            if self.openai_api_key:
                print(f"\U0001f9e0 Pinecone Service: Generating embedding for query")
                response = openai.embeddings.create(
                    model="text-embedding-3-large",
                    input=query
                )
                query_embedding = response.data[0].embedding
            else:
                print(f"\U0001f6ab Pinecone Service: OpenAI API key required for generating embeddings")
                return {
                    "success": False,
                    "error": "OpenAI API key required for generating embeddings"
                }
            
            # Use agent_id as namespace
            namespace = agent_id if agent_id else "default"
            
            print(f"\U0001f50e Pinecone Service: Querying Pinecone index with top_k={top_k} in namespace '{namespace}'")
            # Search Pinecone
            search_response = self.user_kb_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace
            )
            
            results = []
            for match in search_response.matches:
                metadata = match.metadata or {}
                results.append({
                    "id": match.id,
                    "score": match.score,
                    "text": metadata.get("text", ""),
                    "filename": metadata.get("filename", ""),
                    "file_id": metadata.get("file_id", ""),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "metadata": metadata
                })
            print("results",results)
            print(f"\U0001f389 Pinecone Service: Found {len(results)} results for query '{query}'")
            return {
                "success": True,
                "results": results,
                "query": query,
                "namespace": namespace,
                "agent_id": agent_id
            }
            
        except Exception as e:
            logger.error(f"Error searching user knowledge base: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_user_document(self, file_id: str, agent_id: str = None) -> Dict[str, Any]:
        """
        Delete all chunks for a specific document from agent's knowledge base
        
        Args:
            file_id: File ID to delete
            agent_id: Agent ID for namespace isolation
            
        Returns:
            Dict containing deletion status
        """
        try:
            print(f"\U0001f5d1 Pinecone Service: Deleting agent document {file_id} for agent {agent_id}")
            if not self.user_kb_index:
                print(f"\U0001f6ab Pinecone Service: User knowledge base index not initialized")
                return {
                    "success": False,
                    "error": "User knowledge base index not initialized"
                }
            
            namespace = agent_id if agent_id else "default"
            
            print(f"\U0001f50d Pinecone Service: Querying for chunks to delete in namespace '{namespace}'")
            # Query to find all chunks for this file
            search_response = self.user_kb_index.query(
                vector=[0] * 3072,  # Dummy vector for metadata-only search
                top_k=1000,  # Large number to get all chunks
                include_metadata=True,
                namespace=namespace,
                filter={"file_id": file_id}
            )
            
            # Extract chunk IDs
            chunk_ids = [match.id for match in search_response.matches]
            
            print(f"\U0001f4cb Pinecone Service: Found {len(chunk_ids)} chunks to delete")
            if chunk_ids:
                # Delete chunks
                delete_response = self.user_kb_index.delete(
                    ids=chunk_ids,
                    namespace=namespace
                )
                
                logger.info(f"Deleted {len(chunk_ids)} chunks for file {file_id} from agent {agent_id}")
                print(f"\U0001f5d1 Pinecone Service: Successfully deleted {len(chunk_ids)} chunks for file {file_id}")
                
                return {
                    "success": True,
                    "deleted_chunks": len(chunk_ids),
                    "namespace": namespace
                }
            else:
                print(f"\U0001f4ed Pinecone Service: No chunks found for file {file_id}")
                return {
                    "success": True,
                    "deleted_chunks": 0,
                    "message": "No chunks found for this file"
                }
            
        except Exception as e:
            logger.error(f"Error deleting user document: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Create singleton instance
pinecone_service = PineconeService()
