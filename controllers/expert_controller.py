from typing import List, Dict, Any
from services.pinecone_service import store_expert_knowledge, search_expert_knowledge, get_all_experts
from services.openai_service import create_embedding, generate_response, process_expert_content
from models.expert import Expert, ExpertCreate, ExpertContent, ExpertResponse
import uuid
import json
from datetime import datetime

# Simple in-memory storage for experts (replace with database in production)
experts_db = {}

def create_expert(expert_data: ExpertCreate) -> Dict[str, Any]:
    """Create a new expert"""
    try:
        expert_id = str(uuid.uuid4())
        expert = {
            "id": expert_id,
            "name": expert_data.name,
            "role": expert_data.role,
            "bio": expert_data.bio,
            "image_url": expert_data.image_url,
            "voice_id": None,
            "knowledge_base_id": expert_id,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        experts_db[expert_id] = expert
        return {"success": True, "expert": expert}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_expert(expert_id: str) -> Dict[str, Any]:
    """Get expert by ID"""
    try:
        expert = experts_db.get(expert_id)
        if not expert:
            return {"success": False, "error": "Expert not found"}
        return {"success": True, "expert": expert}
    except Exception as e:
        return {"success": False, "error": str(e)}

def list_experts() -> Dict[str, Any]:
    """List all experts"""
    try:
        experts_list = list(experts_db.values())
        return {"success": True, "experts": experts_list}
    except Exception as e:
        return {"success": False, "error": str(e)}

def upload_expert_content(content_data: ExpertContent) -> Dict[str, Any]:
    """Upload content for an expert"""
    try:
        expert = experts_db.get(content_data.expert_id)
        if not expert:
            return {"success": False, "error": "Expert not found"}
        
        # Process content into chunks
        chunks = process_expert_content(content_data.content, content_data.content_type)
        
        stored_chunks = []
        for chunk in chunks:
            # Create embedding for the chunk
            embedding = create_embedding(chunk)
            if not embedding:
                continue
            
            # Store in Pinecone
            vector_id = store_expert_knowledge(
                expert_id=content_data.expert_id,
                content=chunk,
                embedding=embedding,
                metadata={
                    "content_type": content_data.content_type,
                    "expert_name": expert["name"],
                    **(content_data.metadata or {})
                }
            )
            
            if vector_id:
                stored_chunks.append(vector_id)
        
        return {
            "success": True,
            "message": f"Stored {len(stored_chunks)} content chunks",
            "chunks_stored": len(stored_chunks)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def ask_expert(expert_id: str, question: str) -> Dict[str, Any]:
    """Ask a question to an expert"""
    try:
        expert = experts_db.get(expert_id)
        if not expert:
            return {"success": False, "error": "Expert not found"}
        
        # Create embedding for the question
        question_embedding = create_embedding(question)
        if not question_embedding:
            return {"success": False, "error": "Failed to process question"}
        
        # Search for relevant knowledge
        relevant_knowledge = search_expert_knowledge(expert_id, question_embedding, top_k=3)
        
        # Combine relevant content
        context = "\n".join([item["content"] for item in relevant_knowledge])
        
        # Generate response
        response = generate_response(context, question, expert["name"])
        
        # Calculate confidence based on search scores
        confidence = sum([item["score"] for item in relevant_knowledge]) / len(relevant_knowledge) if relevant_knowledge else 0.0
        
        return {
            "success": True,
            "response": {
                "expert_id": expert_id,
                "expert_name": expert["name"],
                "question": question,
                "answer": response,
                "confidence": confidence,
                "sources": [item["id"] for item in relevant_knowledge]
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_expert(expert_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update expert information"""
    try:
        expert = experts_db.get(expert_id)
        if not expert:
            return {"success": False, "error": "Expert not found"}
        
        # Update allowed fields
        allowed_fields = ["name", "role", "bio", "image_url", "is_active"]
        for field in allowed_fields:
            if field in update_data:
                expert[field] = update_data[field]
        
        experts_db[expert_id] = expert
        return {"success": True, "expert": expert}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_expert(expert_id: str) -> Dict[str, Any]:
    """Delete an expert"""
    try:
        expert = experts_db.get(expert_id)
        if not expert:
            return {"success": False, "error": "Expert not found"}
        
        # Delete from experts database
        del experts_db[expert_id]
        
        # Delete knowledge from Pinecone (optional - you might want to keep the data)
        # delete_expert_knowledge(expert_id)
        
        return {"success": True, "message": "Expert deleted successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}
