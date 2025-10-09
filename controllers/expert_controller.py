from typing import List, Dict, Any
from services.pinecone_service import store_expert_knowledge, search_expert_knowledge, get_all_experts
from services.openai_service import create_embedding, generate_response, process_expert_content
from services.elevenlabs_service import elevenlabs_service
from services.expert_service import ExpertService
from services.aws_s3_service import s3_service
from models.expert import Expert, ExpertCreate, ExpertContent, ExpertResponse
from sqlalchemy.orm import Session
import uuid
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def create_expert_with_elevenlabs(db: Session, expert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new expert with ElevenLabs integration"""
    try:
        # Validate required fields
        if not expert_data.get("name"):
            return {"success": False, "error": "Expert name is required"}
        
        if not expert_data.get("system_prompt"):
            return {"success": False, "error": "System prompt is required"}
        
        if not expert_data.get("voice_id"):
            return {"success": False, "error": "Voice ID is required"}
        
        # Create ElevenLabs agent
        elevenlabs_result = await elevenlabs_service.create_agent(
            name=expert_data["name"],
            system_prompt=expert_data["system_prompt"],
            voice_id=expert_data["voice_id"]
        )
        
        if not elevenlabs_result["success"]:
            logger.error(f"Failed to create ElevenLabs agent: {elevenlabs_result.get('error')}")
            return {
                "success": False,
                "error": f"Failed to create voice agent: {elevenlabs_result.get('error')}"
            }
        
        # Handle avatar upload if provided
        avatar_url = None
        if expert_data.get("avatar_base64"):
            # Validate the base64 image
            validation_result = s3_service.validate_base64_image(expert_data["avatar_base64"])
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid avatar image: {validation_result['error']}"
                }
            
            # Upload the image to AWS S3
            upload_result = await s3_service.upload_base64_image(
                expert_data["avatar_base64"],
                folder="expert-avatars"
            )
            
            if upload_result["success"]:
                avatar_url = upload_result.get("secure_url") or upload_result.get("url")
                logger.info(f"Avatar uploaded successfully to S3: {avatar_url}")
            else:
                logger.warning(f"S3 avatar upload failed: {upload_result.get('error')}")
                # Don't fail the entire expert creation if avatar upload fails
        
        # Prepare expert data for database (excluding system_prompt and voice_id as requested)
        db_expert_data = {
            "name": expert_data["name"],
            "description": expert_data.get("description"),
            "elevenlabs_agent_id": elevenlabs_result["agent_id"],
            "avatar_url": avatar_url,
            "selected_files": expert_data.get("selected_files", [])
        }
        
        # Create expert in database
        expert_service = ExpertService(db)
        db_result = expert_service.create_expert(db_expert_data)
        
        if not db_result["success"]:
            # If database creation fails, we should ideally clean up the ElevenLabs agent
            # For now, we'll log the agent_id for manual cleanup
            logger.error(f"Database creation failed, ElevenLabs agent created: {elevenlabs_result['agent_id']}")
            return db_result
        
        # Return success with both database and ElevenLabs data
        return {
            "success": True,
            "expert": db_result["expert"],
            "elevenlabs_agent_id": elevenlabs_result["agent_id"],
            "main_branch_id": elevenlabs_result.get("main_branch_id"),
            "initial_version_id": elevenlabs_result.get("initial_version_id")
        }
        
    except Exception as e:
        logger.error(f"Error creating expert: {str(e)}")
        return {"success": False, "error": f"Failed to create expert: {str(e)}"}

def create_expert(expert_data: ExpertCreate) -> Dict[str, Any]:
    """Legacy create expert function - kept for backward compatibility"""
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
        
        return {"success": True, "expert": expert}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_expert_from_db(db: Session, expert_id: str) -> Dict[str, Any]:
    """Get expert by ID from database"""
    try:
        expert_service = ExpertService(db)
        return expert_service.get_expert(expert_id)
    except Exception as e:
        logger.error(f"Error getting expert: {str(e)}")
        return {"success": False, "error": str(e)}

def get_expert(expert_id: str) -> Dict[str, Any]:
    """Legacy get expert function - kept for backward compatibility"""
    try:
        # This would need to be updated to use database in production
        return {"success": False, "error": "Expert not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def list_experts_from_db(db: Session) -> Dict[str, Any]:
    """List all experts from database"""
    try:
        expert_service = ExpertService(db)
        return expert_service.list_experts()
    except Exception as e:
        logger.error(f"Error listing experts: {str(e)}")
        return {"success": False, "error": str(e)}

def list_experts() -> Dict[str, Any]:
    """Legacy list experts function - kept for backward compatibility"""
    try:
        return {"success": True, "experts": []}
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
