import pinecone
from typing import List, Dict, Any
from config.settings import PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME
import uuid
import json

# Initialize Pinecone
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

def get_or_create_index():
    """Get or create Pinecone index"""
    try:
        if PINECONE_INDEX_NAME not in pinecone.list_indexes():
            pinecone.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=1536,  # OpenAI embedding dimension
                metric="cosine"
            )
        return pinecone.Index(PINECONE_INDEX_NAME)
    except Exception as e:
        print(f"Error with Pinecone index: {e}")
        return None

def store_expert_knowledge(expert_id: str, content: str, embedding: List[float], metadata: Dict[str, Any] = None):
    """Store expert knowledge in Pinecone"""
    try:
        index = get_or_create_index()
        if not index:
            return False
            
        vector_id = f"{expert_id}_{uuid.uuid4()}"
        
        vector_metadata = {
            "expert_id": expert_id,
            "content": content,
            "content_type": metadata.get("content_type", "text") if metadata else "text",
            **(metadata or {})
        }
        
        index.upsert(vectors=[(vector_id, embedding, vector_metadata)])
        return vector_id
    except Exception as e:
        print(f"Error storing knowledge: {e}")
        return None

def search_expert_knowledge(expert_id: str, query_embedding: List[float], top_k: int = 5):
    """Search expert knowledge in Pinecone"""
    try:
        index = get_or_create_index()
        if not index:
            return []
            
        results = index.query(
            vector=query_embedding,
            filter={"expert_id": expert_id},
            top_k=top_k,
            include_metadata=True
        )
        
        return [
            {
                "id": match.id,
                "score": match.score,
                "content": match.metadata.get("content", ""),
                "metadata": match.metadata
            }
            for match in results.matches
        ]
    except Exception as e:
        print(f"Error searching knowledge: {e}")
        return []

def get_all_experts():
    """Get all expert IDs from Pinecone"""
    try:
        index = get_or_create_index()
        if not index:
            return []
            
        # This is a simplified approach - in production, you'd want a proper expert registry
        stats = index.describe_index_stats()
        return list(stats.namespaces.keys()) if stats.namespaces else []
    except Exception as e:
        print(f"Error getting experts: {e}")
        return []

def delete_expert_knowledge(expert_id: str):
    """Delete all knowledge for an expert"""
    try:
        index = get_or_create_index()
        if not index:
            return False
            
        index.delete(filter={"expert_id": expert_id})
        return True
    except Exception as e:
        print(f"Error deleting expert knowledge: {e}")
        return False
