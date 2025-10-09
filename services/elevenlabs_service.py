import httpx
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = "your_elevenlabs_api_key_here"
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def create_agent(self, name: str, system_prompt: str, voice_id: str) -> Dict[str, Any]:
        """
        Create a new ElevenLabs conversational agent
        
        Args:
            name: Name of the agent
            system_prompt: The system prompt for the agent
            voice_id: ElevenLabs voice ID to use
            
        Returns:
            Dict containing agent_id and other response data
        """
        try:
            url = f"{self.base_url}/convai/agents/create"
            
            payload = {
                "conversation_config": {
                    "agent": {
                        "prompt": {
                            "prompt": system_prompt
                        }
                    },
                    "tts": {
                        "voice_id": voice_id
                    }
                },
                "name": name
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully created ElevenLabs agent: {data.get('agent_id')}")
                    return {
                        "success": True,
                        "agent_id": data.get("agent_id"),
                        "main_branch_id": data.get("main_branch_id"),
                        "initial_version_id": data.get("initial_version_id")
                    }
                else:
                    logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"ElevenLabs API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Error creating ElevenLabs agent: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to create agent: {str(e)}"
            }
    
    async def get_voices(self) -> Dict[str, Any]:
        """
        Get available voices from ElevenLabs
        
        Returns:
            Dict containing list of available voices
        """
        try:
            url = f"{self.base_url}/voices"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "voices": data.get("voices", [])
                    }
                else:
                    logger.error(f"ElevenLabs voices API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"ElevenLabs API error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching ElevenLabs voices: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to fetch voices: {str(e)}"
            }
    
    async def update_agent(self, agent_id: str, name: Optional[str] = None, 
                          system_prompt: Optional[str] = None, 
                          voice_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing ElevenLabs agent
        
        Args:
            agent_id: The ElevenLabs agent ID
            name: New name for the agent (optional)
            system_prompt: New system prompt (optional)
            voice_id: New voice ID (optional)
            
        Returns:
            Dict containing success status and response data
        """
        try:
            url = f"{self.base_url}/convai/agents/{agent_id}"
            
            payload = {}
            if name is not None:
                payload["name"] = name
                
            if system_prompt is not None or voice_id is not None:
                payload["conversation_config"] = {}
                if system_prompt is not None:
                    payload["conversation_config"]["agent"] = {
                        "prompt": {"prompt": system_prompt}
                    }
                if voice_id is not None:
                    payload["conversation_config"]["tts"] = {
                        "voice_id": voice_id
                    }
            
            if not payload:
                return {"success": False, "error": "No update data provided"}
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    logger.info(f"Successfully updated ElevenLabs agent: {agent_id}")
                    return {"success": True, "data": response.json()}
                else:
                    logger.error(f"ElevenLabs update API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"ElevenLabs API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Error updating ElevenLabs agent: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to update agent: {str(e)}"
            }
    
    async def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Delete an ElevenLabs agent
        
        Args:
            agent_id: The ElevenLabs agent ID to delete
            
        Returns:
            Dict containing success status
        """
        try:
            url = f"{self.base_url}/convai/agents/{agent_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=self.headers)
                
                if response.status_code == 200:
                    logger.info(f"Successfully deleted ElevenLabs agent: {agent_id}")
                    return {"success": True}
                else:
                    logger.error(f"ElevenLabs delete API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"ElevenLabs API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Error deleting ElevenLabs agent: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to delete agent: {str(e)}"
            }
    
    async def get_signed_url(self, agent_id: str) -> Dict[str, Any]:
        """
        Get a signed URL for WebSocket conversation with an ElevenLabs agent
        
        Args:
            agent_id: The ElevenLabs agent ID
            
        Returns:
            Dict containing signed URL for WebSocket connection
        """
        try:
            url = f"{self.base_url}/convai/conversation/get-signed-url"
            params = {"agent_id": agent_id}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully got signed URL for agent: {agent_id}")
                    return {
                        "success": True,
                        "signed_url": data.get("signed_url")
                    }
                else:
                    logger.error(f"ElevenLabs signed URL API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"ElevenLabs API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Error getting signed URL for agent {agent_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get signed URL: {str(e)}"
            }

# Create a singleton instance
elevenlabs_service = ElevenLabsService()
