from typing import List, Dict, Any
from services.pinecone_service import pinecone_service
from services.aws_s3_service import s3_service
from services.elevenlabs_service import elevenlabs_service
from services.expert_service import ExpertService
from services.queue_service import QueueService
from services.expert_processing_progress_service import ExpertProcessingProgressService
from models.expert import Expert, ExpertCreate, ExpertContent, ExpertResponse
from sqlalchemy.orm import Session
import uuid
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

async def create_expert_with_elevenlabs(db: Session, expert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new expert with ElevenLabs integration"""
    try:
        # Validate required fields
        if not expert_data.get("name"):
            return {"success": False, "error": "Expert name is required"}
        
        if not expert_data.get("voice_id"):
            return {"success": False, "error": "Voice ID is required"}
        
        # Use default system prompt if not provided
        system_prompt = expert_data.get("system_prompt") or "You are a helpful AI assistant."
        
        # Step 1: Create ElevenLabs agent first
        # Use default first message if not provided
        first_message = expert_data.get("first_message") or "Hi I'm your knowledgebase assistant how I can assist you with"
        
        elevenlabs_result = await elevenlabs_service.create_agent(
            name=expert_data["name"],
            system_prompt=system_prompt,
            voice_id=expert_data["voice_id"],
            first_message=first_message,
            tool_ids=None  # No tools initially
        )
        
        if not elevenlabs_result["success"]:
            logger.error(f"Failed to create ElevenLabs agent: {elevenlabs_result.get('error')}")
            return {
                "success": False,
                "error": f"Failed to create voice agent: {elevenlabs_result.get('error')}"
            }
        
        agent_id = elevenlabs_result["agent_id"]
        logger.info(f"Created ElevenLabs agent: {agent_id}")
        
        # Step 2: Always create knowledge base tool for user documents (regardless of initial file selection)
        tool_id = None
        try:
            logger.info(f"Creating user-knowledge-base tool for agent: {agent_id}")
            tool_result = await create_knowledge_base_tool(agent_id=agent_id)
            if tool_result["success"]:
                tool_id = tool_result["tool_id"]
                logger.info(f"Created user-knowledge-base tool: {tool_id}")
                
                # Step 3: Update agent to include the tool
                logger.info(f"Updating agent {agent_id} to include user-knowledge-base tool {tool_id}")
                update_result = await elevenlabs_service.update_agent(
                    agent_id=agent_id,
                    tool_ids=[tool_id]
                )
                if update_result["success"]:
                    logger.info(f"Successfully attached user-knowledge-base tool {tool_id} to agent {agent_id}")
                else:
                    logger.warning(f"Failed to attach user-knowledge-base tool to agent: {update_result.get('error')}")
            else:
                logger.warning(f"Failed to create user-knowledge-base tool: {tool_result.get('error')}")
        except Exception as e:
            logger.warning(f"User-knowledge-base tool creation/attachment failed: {str(e)}")
        
        # Agent and tool creation completed above
        
        # Handle avatar upload if provided (non-blocking)
        avatar_url = None
        if expert_data.get("avatar_base64"):
            try:
                # Check if AWS credentials are configured
                import os
                aws_configured = (
                    os.getenv("S3_ACCESS_KEY_ID") and 
                    os.getenv("S3_ACCESS_KEY_ID") != "your_s3_access_key_id" and
                    os.getenv("S3_SECRET_KEY") and 
                    os.getenv("S3_SECRET_KEY") != "your_s3_secret_key" and
                    os.getenv("S3_BUCKET_NAME") and 
                    os.getenv("S3_BUCKET_NAME") != "your_s3_bucket_name"
                )
                
                if aws_configured:
                    # Validate the base64 image
                    validation_result = s3_service.validate_base64_image(expert_data["avatar_base64"])
                    if validation_result["valid"]:
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
                    else:
                        logger.warning(f"Invalid avatar image: {validation_result['error']}")
                else:
                    logger.info("AWS S3 not configured, skipping avatar upload")
                    # You could save the base64 image locally or use a default avatar
                    avatar_url = None
            except Exception as e:
                logger.warning(f"Avatar upload failed: {str(e)}")
                # Don't fail the entire expert creation if avatar upload fails
        
        # Prepare expert data for database (excluding system_prompt and voice_id as requested)
        db_expert_data = {
            "user_id": expert_data.get("user_id"),  # Pass user_id from authenticated user
            "name": expert_data["name"],
            "description": expert_data.get("description"),
            "elevenlabs_agent_id": elevenlabs_result["agent_id"],
            "avatar_url": avatar_url,
            "pinecone_index_name": elevenlabs_result["agent_id"],  # Set pinecone index to match agent_id
            "selected_files": expert_data.get("selected_files", []),
            "knowledge_base_tool_id": tool_id  # Store the tool ID
        }
        
        # Create expert in database
        expert_service = ExpertService(db)
        db_result = expert_service.create_expert(db_expert_data)
        
        if not db_result["success"]:
            # If database creation fails, we should ideally clean up the ElevenLabs agent
            # For now, we'll log the agent_id for manual cleanup
            logger.error(f"Database creation failed, ElevenLabs agent created: {elevenlabs_result['agent_id']}")
            return db_result
        
        # Step 4: Skip file processing for now (OpenAI API key not configured)
        expert_id = db_result["expert"]["id"]
        selected_files = expert_data.get("selected_files", [])
        
        queue_task = None
        if selected_files:
            logger.info(f"📭 File processing skipped for expert {expert_id} ({len(selected_files)} files)")
            print(f"📭 File processing skipped - OpenAI API key not configured")
            # TODO: Enable file processing when OpenAI API key is configured
        else:
            logger.info(f"📭 No files selected for expert {expert_id}")
            print(f"📭 No files selected for expert {expert_id}")
        
        # Return success with both database and ElevenLabs data
        return {
            "success": True,
            "expert": db_result["expert"],
            "elevenlabs_agent_id": elevenlabs_result["agent_id"],
            "main_branch_id": elevenlabs_result.get("main_branch_id"),
            "initial_version_id": elevenlabs_result.get("initial_version_id"),
            "file_processing": {
                "files_selected": len(selected_files),
                "queued": queue_task is not None,
                "queue_position": queue_task.queue_position if queue_task else None,
                "task_id": queue_task.id if queue_task else None
            }
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

def get_expert_from_db(db: Session, expert_id: str, user_id: str = None) -> Dict[str, Any]:
    """Get expert by ID from database"""
    try:
        expert_service = ExpertService(db)
        result = expert_service.get_expert(expert_id)
        
        if not result["success"]:
            return result
        
        expert_data = result["expert"]
        
        # Check if expert belongs to user
        if user_id and expert_data.get("user_id") != user_id:
            return {"success": False, "error": "Expert not found or access denied"}
        
        return {"success": True, "expert": expert_data}
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

def list_experts_from_db(db: Session, user_id: str = None) -> Dict[str, Any]:
    """List all experts from database for a specific user"""
    try:
        expert_service = ExpertService(db)
        result = expert_service.list_experts(user_id=user_id)
        
        # Service already returns {"success": True, "experts": [...]}
        return result
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

async def update_expert_in_db(db: Session, expert_id: str, update_data: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    """Update expert information in database and ElevenLabs"""
    try:
        expert_service = ExpertService(db)
        
        # Get expert details
        expert_result = expert_service.get_expert(expert_id)
        if not expert_result["success"]:
            return {"success": False, "error": "Expert not found"}
        
        expert_data = expert_result["expert"]
        
        # Check if expert belongs to user
        if user_id and expert_data.get("user_id") != user_id:
            return {"success": False, "error": "Expert not found or access denied"}
        
        # If voice_id is being updated, update ElevenLabs agent
        if "voice_id" in update_data and expert_data.get("elevenlabs_agent_id"):
            try:
                logger.info(f"Updating ElevenLabs agent voice for expert {expert_id}, agent_id: {expert_data['elevenlabs_agent_id']}, voice_id: {update_data['voice_id']}")
                elevenlabs_result = await elevenlabs_service.update_agent(
                    agent_id=expert_data["elevenlabs_agent_id"],
                    voice_id=update_data["voice_id"]
                )
                
                logger.info(f"ElevenLabs update result: {elevenlabs_result}")
                
                if not elevenlabs_result["success"]:
                    error_msg = elevenlabs_result.get('error', 'Unknown error')
                    logger.error(f"Failed to update ElevenLabs agent voice: {error_msg}")
                    return {
                        "success": False,
                        "error": f"Failed to update voice in ElevenLabs: {error_msg}"
                    }
                
                logger.info(f"Successfully updated ElevenLabs agent voice to {update_data['voice_id']}")
            except Exception as e:
                logger.error(f"Exception updating ElevenLabs agent: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": f"Failed to update voice: {str(e)}"
                }
        
        # Update expert in database
        result = expert_service.update_expert(expert_id, update_data)
        
        if not result["success"]:
            return result
        
        logger.info(f"Successfully updated expert {expert_id}")
        return {
            "success": True,
            "expert": result["expert"],
            "message": "Expert updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating expert: {str(e)}")
        return {"success": False, "error": f"Failed to update expert: {str(e)}"}

def update_expert(expert_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy update expert function - kept for backward compatibility"""
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

async def delete_expert_from_db(db: Session, expert_id: str, user_id: str = None) -> Dict[str, Any]:
    """Delete an expert from database and cleanup associated resources"""
    try:
        expert_service = ExpertService(db)
        
        # Get expert details before deletion
        expert_result = expert_service.get_expert(expert_id)
        if not expert_result["success"]:
            return {"success": False, "error": "Expert not found"}
        
        # Check if expert belongs to user
        expert_data = expert_result["expert"]
        if user_id and expert_data.get("user_id") != user_id:
            return {"success": False, "error": "Expert not found or access denied"}
        
        expert = expert_result["expert"]
        elevenlabs_agent_id = expert.get("elevenlabs_agent_id")
        knowledge_base_tool_id = expert.get("knowledge_base_tool_id")
        
        logger.info(f"Deleting expert {expert['name']} (ID: {expert_id})")
        
        # Step 1: Delete ElevenLabs agent if exists
        if elevenlabs_agent_id:
            try:
                logger.info(f"Deleting ElevenLabs agent: {elevenlabs_agent_id}")
                delete_agent_result = await elevenlabs_service.delete_agent(elevenlabs_agent_id)
                if delete_agent_result["success"]:
                    logger.info(f"Successfully deleted ElevenLabs agent: {elevenlabs_agent_id}")
                else:
                    logger.warning(f"Failed to delete ElevenLabs agent: {delete_agent_result.get('error')}")
            except Exception as e:
                logger.warning(f"Error deleting ElevenLabs agent: {str(e)}")
        
        # Step 2: Delete knowledge base tool if exists
        if knowledge_base_tool_id:
            try:
                logger.info(f"Deleting knowledge base tool: {knowledge_base_tool_id}")
                # Note: ElevenLabs API might not have a direct delete tool endpoint
                # The tool will be automatically removed when the agent is deleted
                logger.info(f"Tool {knowledge_base_tool_id} removed with agent deletion")
            except Exception as e:
                logger.warning(f"Error handling tool deletion: {str(e)}")
        
        # Step 3: Clean up user knowledge base from Pinecone (optional)
        user_id = f"user_{expert_id}"
        try:
            logger.info(f"Cleaning up Pinecone knowledge base for user: {user_id}")
            # You can uncomment this if you want to delete the knowledge base
            # await pinecone_service.delete_user_knowledge_base(user_id)
            logger.info(f"Pinecone cleanup completed for user: {user_id}")
        except Exception as e:
            logger.warning(f"Error cleaning up Pinecone: {str(e)}")
        
        # Step 4: Delete expert from database
        delete_result = expert_service.delete_expert(expert_id)
        if not delete_result["success"]:
            return delete_result
        
        logger.info(f"Successfully deleted expert {expert['name']} and cleaned up resources")
        return {
            "success": True,
            "message": f"Expert '{expert['name']}' deleted successfully",
            "deleted_resources": {
                "expert_id": expert_id,
                "elevenlabs_agent_id": elevenlabs_agent_id,
                "knowledge_base_tool_id": knowledge_base_tool_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error deleting expert: {str(e)}")
        return {"success": False, "error": f"Failed to delete expert: {str(e)}"}

def delete_expert(expert_id: str) -> Dict[str, Any]:
    """Legacy delete expert function - kept for backward compatibility"""
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

async def create_knowledge_base_tool(agent_id: str) -> Dict[str, Any]:
    """
    Create a user-knowledge-base search tool for an agent
    This tool allows the agent to search through user's uploaded documents
    
    Args:
        agent_id: ElevenLabs agent ID to identify the expert
        
    Returns:
        Dict containing tool creation status and tool_id
    """
    try:
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        webhook_token = os.getenv("WEBHOOK_AUTH_TOKEN", "your-secret-token")
        
        # Create tool configuration with agent_id in the URL
        tool_config = {
            "name": f"user_knowledge_base",
            "description": "Search the user's uploaded documents and knowledge base for relevant information to answer questions. Use this when you need specific information that might be in the user's documents or files they have shared with you.",
            "webhook_url": f"{base_url}/tools/search-user-knowledge?agent_id={agent_id}",  # Include agent_id in URL
            "authentication": {
                "type": "bearer",
                "token": webhook_token
            }
        }
        
        # Create the webhook tool
        tool_result = await elevenlabs_service.create_webhook_tool(tool_config)
        
        if tool_result["success"]:
            tool_id = tool_result["tool_id"]
            logger.info(f"Successfully created knowledge base tool {tool_id} for agent {agent_id}")
            return {
                "success": True,
                "tool_id": tool_id,
                "message": "Knowledge base tool created successfully"
            }
        else:
            logger.error(f"Failed to create webhook tool: {tool_result.get('error')}")
            return tool_result
        
    except Exception as e:
        logger.error(f"Error creating knowledge base tool: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def update_knowledge_base_tool_url(tool_id: str, agent_id: str) -> Dict[str, Any]:
    """
    Update the webhook URL of a knowledge base tool with the actual agent_id
    
    Args:
        tool_id: ElevenLabs tool ID
        agent_id: Actual ElevenLabs agent ID
        
    Returns:
        Dict containing update status
    """
    try:
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        webhook_token = os.getenv("WEBHOOK_AUTH_TOKEN", "your-secret-token")
        
        # Create updated tool configuration with real agent_id
        updated_config = {
            "name": f"search_user_knowledge_{agent_id}",
            "description": "Search the user's uploaded documents and knowledge base for relevant information to answer questions. Use this when you need specific information that might be in the user's documents.",
            "webhook_url": f"{base_url}/tools/search-user-knowledge?agent_id={agent_id}",
            "authentication": {
                "type": "bearer",
                "token": webhook_token
            }
        }
        
        # Update the tool using ElevenLabs API
        update_result = await elevenlabs_service.update_webhook_tool(tool_id, updated_config)
        
        if update_result["success"]:
            logger.info(f"Successfully updated tool {tool_id} with agent_id {agent_id}")
            return {
                "success": True,
                "message": "Tool webhook URL updated successfully"
            }
        else:
            logger.error(f"Failed to update tool webhook URL: {update_result.get('error')}")
            return update_result
            
    except Exception as e:
        logger.error(f"Error updating tool webhook URL: {str(e)}")
        return {"success": False, "error": str(e)}

async def add_user_knowledge_tool_to_existing_agent(db: Session, expert_id: str, user_id: str = None) -> Dict[str, Any]:
    """
    Add user-knowledge-base tool to an existing agent that doesn't have it
    
    Args:
        db: Database session
        expert_id: Expert ID in our database
        user_id: User ID for access control
        
    Returns:
        Dict containing success status and tool details
    """
    try:
        expert_service = ExpertService(db)
        
        # Get expert details
        expert_result = expert_service.get_expert(expert_id)
        if not expert_result["success"]:
            return {"success": False, "error": "Expert not found"}
        
        expert_data = expert_result["expert"]
        
        # Check if expert belongs to user
        if user_id and expert_data.get("user_id") != user_id:
            return {"success": False, "error": "Expert not found or access denied"}
        
        elevenlabs_agent_id = expert_data.get("elevenlabs_agent_id")
        if not elevenlabs_agent_id:
            return {"success": False, "error": "Expert does not have an ElevenLabs agent ID"}
        
        # Check if expert already has a knowledge base tool
        existing_tool_id = expert_data.get("knowledge_base_tool_id")
        if existing_tool_id:
            logger.info(f"Expert {expert_id} already has user-knowledge-base tool: {existing_tool_id}")
            return {
                "success": True,
                "message": "Expert already has user-knowledge-base tool",
                "tool_id": existing_tool_id,
                "already_exists": True
            }
        
        # Create the user-knowledge-base tool
        logger.info(f"Adding user-knowledge-base tool to existing expert {expert_id} (agent: {elevenlabs_agent_id})")
        tool_result = await create_knowledge_base_tool(agent_id=elevenlabs_agent_id)
        
        if not tool_result["success"]:
            return {
                "success": False,
                "error": f"Failed to create user-knowledge-base tool: {tool_result.get('error')}"
            }
        
        tool_id = tool_result["tool_id"]
        logger.info(f"Created user-knowledge-base tool: {tool_id}")
        
        # Update agent to include the tool
        logger.info(f"Updating agent {elevenlabs_agent_id} to include user-knowledge-base tool {tool_id}")
        update_result = await elevenlabs_service.update_agent(
            agent_id=elevenlabs_agent_id,
            tool_ids=[tool_id]
        )
        
        if not update_result["success"]:
            logger.warning(f"Failed to attach user-knowledge-base tool to agent: {update_result.get('error')}")
            return {
                "success": False,
                "error": f"Failed to attach tool to agent: {update_result.get('error')}"
            }
        
        # Update expert in database with the new tool ID
        update_data = {"knowledge_base_tool_id": tool_id}
        db_update_result = expert_service.update_expert(expert_id, update_data)
        
        if not db_update_result["success"]:
            logger.warning(f"Failed to update expert with tool ID: {db_update_result.get('error')}")
            # Tool is created and attached, but database update failed
            return {
                "success": True,
                "warning": "Tool created and attached but database update failed",
                "tool_id": tool_id,
                "db_error": db_update_result.get('error')
            }
        
        logger.info(f"Successfully added user-knowledge-base tool {tool_id} to expert {expert_id}")
        return {
            "success": True,
            "message": "User-knowledge-base tool added successfully",
            "tool_id": tool_id,
            "expert_id": expert_id,
            "agent_id": elevenlabs_agent_id
        }
        
    except Exception as e:
        logger.error(f"Error adding user-knowledge-base tool to existing agent: {str(e)}")
        return {"success": False, "error": f"Failed to add tool: {str(e)}"}
