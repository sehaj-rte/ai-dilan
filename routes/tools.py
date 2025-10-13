from fastapi import APIRouter, HTTPException, status, Query, Request, Depends
from pydantic import BaseModel
from typing import Optional
import logging
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from config.database import get_db
from services.expert_service import ExpertService

# Load environment variables
load_dotenv()

# OpenAI API key is loaded from .env file via load_dotenv()

from services.pinecone_service import PineconeService

router = APIRouter()
logger = logging.getLogger(__name__)

# Create Pinecone service instance
pinecone_service = PineconeService()

class PineconeSearchRequest(BaseModel):
    query: str
    namespace: Optional[str] = None
    top_k: Optional[int] = 5

@router.post("/pinecone-search")
async def pinecone_search_webhook(
    request: PineconeSearchRequest, 
    index_type: str = Query(default="education", description="Index type: education or travel")
):
    """
    Webhook endpoint for ElevenLabs agents to search Pinecone knowledge base
    This endpoint is called by ElevenLabs agents during conversations
    
    Args:
        request: Search request from ElevenLabs agent
        index_type: Type of index to search ("education" or "travel")
        
    Returns:
        Formatted search results for the agent
    """
    try:
        logger.info(f"🔍 Pinecone search request: '{request.query}' (index: {index_type})")
        
        # Search Pinecone directly
        result = await pinecone_service.search(
            query=request.query,
            index_type=index_type,
            namespace=request.namespace,
            top_k=request.top_k or 5
        )
        
        if result["success"]:
            # Format results for ElevenLabs agent
            formatted_results = []
            for item in result["results"]:
                if item["content"]:  # Only include results with content
                    formatted_results.append(f"**{item['title']}**\n{item['content']}\n(Relevance: {item['score']:.3f})")
            
            if not formatted_results:
                response_text = f"No relevant information found in the {index_type} knowledge base for this query."
            else:
                response_text = "\n\n".join(formatted_results)
            
            # Return response in the format ElevenLabs expects
            return {
                "response": response_text,
                "metadata": {
                    "results_count": len(formatted_results),
                    "query": request.query,
                    "index_searched": index_type
                }
            }
        else:
            # Return error in ElevenLabs format
            return {
                "response": f"I couldn't find relevant information for that query. {result.get('error', '')}",
                "metadata": {"error": True}
            }
            
    except Exception as e:
        logger.error(f"❌ Error in Pinecone search webhook: {str(e)}")
        return {
            "response": "I'm having trouble accessing the knowledge base right now. Please try again later.",
            "metadata": {"error": True}
        }

@router.post("/search-user-knowledge")
async def search_user_knowledge_webhook(
    request_obj: Request,
    search_request: PineconeSearchRequest,
    db: Session = Depends(get_db),
    user_id: str = Query(default=None, description="User ID for knowledge base isolation"),
    agent_id: str = Query(default=None, description="ElevenLabs agent ID")
):
    """
    Webhook endpoint for ElevenLabs agents to search user's custom knowledge base
    This endpoint is called by ElevenLabs agents during conversations
    
    Args:
        request_obj: FastAPI request object to get headers
        search_request: Search request from ElevenLabs agent
        db: Database session
        user_id: Optional user ID (fallback)
        
    Returns:
        Formatted search results from user's uploaded documents
    """
    try:
        logger.info("🚀 === WEBHOOK REQUEST STARTED ===")

        # Log all request headers for debugging
        logger.info(f"📋 Request Headers: {dict(request_obj.headers)}")
        logger.info(f"📝 Search Query: '{search_request.query}'")
        logger.info(f"🔢 Top K: {search_request.top_k}")
        logger.info(f"📍 Namespace: {search_request.namespace}")
        logger.info(f"🆔 URL User ID: {user_id}")

        # Get agent_id from query parameters (since ElevenLabs doesn't send it in headers)
        agent_id = request_obj.query_params.get("agent_id")
        logger.info(f"🤖 Agent ID from query params: {agent_id}")

        # Also check headers just in case
        header_agent_id = request_obj.headers.get("x-elevenlabs-agent-id")
        if header_agent_id:
            logger.info(f"🤖 Agent ID from headers: {header_agent_id}")
            agent_id = header_agent_id  # Prefer header if available

        actual_user_id = user_id

        # If we have agent_id, get the actual user from database
        if agent_id:
            logger.info(f"🔍 Looking up expert for agent_id: {agent_id}")
            expert_service = ExpertService(db)
            expert_result = expert_service.get_expert_by_agent_id(agent_id)

            if expert_result["success"]:
                expert = expert_result["expert"]
                # Use expert_id as user identifier for now (until we add proper user association)
                actual_user_id = f"user_{expert['id']}"
                logger.info(f"✅ Found expert: {expert['name']} (ID: {expert['id']})")
                logger.info(f"📊 Expert details: pinecone_index={expert.get('pinecone_index_name')}, tool_id={expert.get('knowledge_base_tool_id')}")
                logger.info(f"📁 Selected files: {expert.get('selected_files')}")
            else:
                logger.warning(f"❌ Expert not found for agent_id: {agent_id} - Error: {expert_result.get('error')}")
        else:
            logger.warning("⚠️ No agent_id found in query params or headers")
            logger.info("📋 All available headers:")
            for header_name, header_value in request_obj.headers.items():
                logger.info(f"   {header_name}: {header_value}")
            logger.info("❓ All query parameters:")
            for param_name, param_value in request_obj.query_params.items():
                logger.info(f"   {param_name}: {param_value}")
        
        # Fallback to provided user_id or default
        if not actual_user_id:
            actual_user_id = user_id or "default_user"
            logger.info(f"🔄 Using fallback user_id: {actual_user_id}")
        
        logger.info(f"🎯 Final user_id for search: {actual_user_id}")
        logger.info(f"🔍 Starting Pinecone search with query: '{search_request.query}'")

        # Search agent's custom knowledge base using the correct namespace
        logger.info(f"📡 Calling Pinecone service with agent_id: {agent_id}")
        print(f"\U0001f916 ElevenLabs Webhook: Searching agent knowledge base for agent {agent_id}")
        print(f"🔍 Query: '{search_request.query}' (top_k: {search_request.top_k or 5})")
        
        # Use the expert's pinecone_index_name as the namespace (ElevenLabs agent_id used during storage)
        search_namespace = agent_id  # This should be the ElevenLabs agent_id
        if expert_result["success"]:
            search_namespace = expert.get('pinecone_index_name') or agent_id
        
        print(f"🎯 Searching in namespace: {search_namespace}")
        result = await pinecone_service.search_user_knowledge(
            query=search_request.query,
            agent_id=search_namespace,  # Use the correct namespace for search
            top_k=search_request.top_k or 5
        )
        logger.info(f"\U0001f4c8 Pinecone search result: success={result.get('success')}, results_count={len(result.get('results', []))}")
        print(f"\U0001f4c8 ElevenLabs Webhook: Pinecone search completed with {len(result.get('results', []))} results")
        
        if result["success"]:
            logger.info("✅ Pinecone search successful, processing results...")
            # Format results for ElevenLabs agent
            formatted_results = []
            for i, item in enumerate(result["results"]):
                logger.info(f"📄 Result {i+1}: score={item.get('score', 0):.3f}, filename={item.get('filename', 'Unknown')}, text_length={len(item.get('text', ''))}")
                print(f"📄 Processing result {i+1}: {item.get('filename', 'Unknown')} (score: {item.get('score', 0):.3f})")
                if item["text"] and item["score"] > 0.4:  # Include moderately relevant results
                    source_info = f"**{item['filename']}**" if item['filename'] else "**Document**"
                    formatted_results.append(f"{source_info}\n{item['text']}\n(Relevance: {item['score']:.3f})")
                    logger.info(f"✅ Including result {i+1} (score > 0.4)")
                    print(f"✅ Including result {i+1} (moderate relevance)")
                else:
                    logger.info(f"❌ Excluding result {i+1} (score <= 0.4 or no text)")
                    print(f"❌ Excluding result {i+1} (low relevance)")
            
            logger.info(f"📊 Final formatted results count: {len(formatted_results)}")
            print(f"📊 Final results: {len(formatted_results)} relevant documents found")
            
            if not formatted_results:
                response_text = "I don't have any relevant information in your uploaded documents for this query. You may want to upload more documents to expand my knowledge base."
                logger.info("📭 No relevant results found, returning empty message")
            else:
                response_text = "\n\n".join(formatted_results)
                logger.info(f"📝 Returning {len(formatted_results)} formatted results")
            
            response_data = {
                "response": response_text,
                "metadata": {
                    "results_count": len(formatted_results),
                    "query": search_request.query,
                    "agent_id": agent_id,
                    "namespace": search_namespace,  # The actual namespace used for search
                    "source": "agent_knowledge_base"
                }
            }
            logger.info(f"🎉 === WEBHOOK SUCCESS === Returning response with {len(formatted_results)} results")
            print(f"🎉 Webhook completed successfully for agent {agent_id}")
            print(f"📋 Query: '{search_request.query}' → {len(formatted_results)} relevant results")
            return response_data
        else:
            # Return error in ElevenLabs format
            logger.error(f"❌ Pinecone search failed: {result.get('error', 'Unknown error')}")
            error_response = {
                "response": f"I couldn't search your knowledge base right now. {result.get('error', '')}",
                "metadata": {"error": True, "agent_id": agent_id, "namespace": search_namespace}
            }
            logger.info(f"💥 === WEBHOOK ERROR === Returning error response")
            print(f"💥 Webhook failed for agent {agent_id}: {result.get('error', 'Unknown error')}")
            return error_response
            
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR in user knowledge search webhook: {str(e)}")
        logger.error(f"🔍 Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"📚 Full traceback: {traceback.format_exc()}")
        return {
            "response": "I'm having trouble accessing your knowledge base right now. Please try again later.",
            "metadata": {"error": True, "exception": str(e)}
        }

@router.get("/search-user-knowledge/health")
async def search_user_knowledge_health():
    """Health check for user knowledge base search webhook"""
    return {
        "status": "healthy",
        "endpoint": "search-user-knowledge",
        "message": "Agent knowledge base search webhook is operational",
        "indexing_method": "agent_id_namespace",
        "supported_features": ["agent_isolation", "custom_documents", "elevenlabs_integration"],
        "current_agent_namespaces": ["agent_id_based_namespaces"],
        "pinecone_index": os.getenv("PINECONE_USER_KB_INDEX", "user-knowledge-base")
    }
