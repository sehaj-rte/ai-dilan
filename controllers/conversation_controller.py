from typing import Dict, Any
from services.elevenlabs_service import elevenlabs_service
from services.expert_service import ExpertService
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

async def get_conversation_signed_url(db: Session, expert_id: str, user_id: str = None) -> Dict[str, Any]:
    """
    Get a signed URL for WebSocket conversation with an expert's ElevenLabs agent
    
    Args:
        expert_id: The expert ID from our database
        user_id: The user ID (for future authentication/logging)
        
    Returns:
        Dict containing signed URL or error
    """
    try:
        # Get expert details from database
        expert_service = ExpertService(db)
        expert_result = expert_service.get_expert(expert_id)
        
        if not expert_result["success"]:
            logger.error(f"Expert not found: {expert_id}")
            return {
                "success": False,
                "error": "Expert not found"
            }
        
        expert = expert_result["expert"]
        
        # Check if expert has an ElevenLabs agent ID
        if not expert.get("elevenlabs_agent_id"):
            logger.error(f"Expert {expert_id} does not have an ElevenLabs agent ID")
            return {
                "success": False,
                "error": "Expert does not have voice capabilities configured"
            }
        
        # Check if expert is active
        if not expert.get("is_active"):
            logger.warning(f"Expert {expert_id} is not active")
            return {
                "success": False,
                "error": "Expert is currently not available"
            }
        
        # Get signed URL from ElevenLabs
        signed_url_result = await elevenlabs_service.get_signed_url(expert["elevenlabs_agent_id"])
        
        if not signed_url_result["success"]:
            logger.error(f"Failed to get signed URL for expert {expert_id}: {signed_url_result.get('error')}")
            return {
                "success": False,
                "error": "Failed to establish voice connection",
                "details": signed_url_result.get("error")
            }
        
        logger.info(f"Successfully generated signed URL for expert {expert_id} (agent: {expert['elevenlabs_agent_id']})")
        
        return {
            "success": True,
            "signed_url": signed_url_result["signed_url"],
            "expert_name": expert["name"],
            "agent_id": expert["elevenlabs_agent_id"]
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation signed URL for expert {expert_id}: {str(e)}")
        return {
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }
