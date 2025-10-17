import httpx
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        # Hardcoded API key for now
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not found in environment variables")
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def create_agent(self, name: str, system_prompt: str, voice_id: str, first_message: str = None, tool_ids: list = None) -> Dict[str, Any]:
        """
        Create a new ElevenLabs conversational agent with optional tools
        
        Args:
            name: Name of the agent
            system_prompt: The system prompt for the agent
            voice_id: ElevenLabs voice ID to use
            first_message: The initial greeting message the agent will send
            tool_ids: List of tool IDs to attach to the agent
            
        Returns:
            Dict containing agent_id and other response data
        """
        try:
            url = f"{self.base_url}/convai/agents/create"
            
            # Build the prompt configuration
            prompt_config = {
                "prompt": system_prompt
            }
            
            # Add tool_ids if provided (new format)
            if tool_ids:
                prompt_config["tool_ids"] = tool_ids
                logger.info(f"Creating agent with {len(tool_ids)} tools: {tool_ids}")
            
            payload = {
                "conversation_config": {
                    "agent": {
                        "prompt": prompt_config
                    },
                    "tts": {
                        "voice_id": voice_id
                    }
                },
                "name": name
            }
            
            # Add first_message if provided
            if first_message:
                payload["conversation_config"]["agent"]["first_message"] = first_message
                logger.info(f"Adding first message to agent: {first_message[:50]}...")
            
            # Debug: Log the complete payload structure
            logger.info(f"ElevenLabs create_agent payload: {payload}")
            
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
    
    async def get_voices(self, 
                        search: Optional[str] = None,
                        voice_type: Optional[str] = None,
                        category: Optional[str] = None,
                        page_size: int = 50,
                        next_page_token: Optional[str] = None,
                        sort: Optional[str] = None,
                        sort_direction: Optional[str] = None) -> Dict[str, Any]:
        """
        Get available voices from ElevenLabs using v2 API with advanced filtering
        
        Args:
            search: Search term to filter voices by name, description, labels, category
            voice_type: Type filter ('personal', 'community', 'default', 'workspace', 'non-default')
            category: Category filter ('premade', 'cloned', 'generated', 'professional')
            page_size: Number of voices to return (max 100, default 50)
            next_page_token: Token for pagination
            sort: Sort field ('created_at_unix' or 'name')
            sort_direction: Sort direction ('asc' or 'desc')
        
        Returns:
            Dict containing list of available voices with pagination info
        """
        try:
            # Use v2 API endpoint for advanced features
            url = "https://api.elevenlabs.io/v2/voices"
            
            # Build query parameters
            params = {
                "page_size": min(page_size, 100),  # Ensure we don't exceed API limit
                "include_total_count": True
            }
            
            if search:
                params["search"] = search
            if voice_type:
                params["voice_type"] = voice_type
            if category:
                params["category"] = category
            if next_page_token:
                params["next_page_token"] = next_page_token
            if sort:
                params["sort"] = sort
            if sort_direction:
                params["sort_direction"] = sort_direction
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "voices": data.get("voices", []),
                        "has_more": data.get("has_more", False),
                        "total_count": data.get("total_count", 0),
                        "next_page_token": data.get("next_page_token")
                    }
                else:
                    logger.error(f"ElevenLabs voices API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"ElevenLabs API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching ElevenLabs voices: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to fetch voices: {str(e)}"
            }
    
    async def get_voice_details(self, voice_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific voice
        
        Args:
            voice_id: ElevenLabs voice ID
            
        Returns:
            Dict containing detailed voice information
        """
        try:
            url = f"{self.base_url}/voices/{voice_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "voice": data
                    }
                else:
                    logger.error(f"ElevenLabs voice details API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"ElevenLabs API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching voice details: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to fetch voice details: {str(e)}"
            }
    
    async def update_agent(self, agent_id: str, name: Optional[str] = None, 
                          system_prompt: Optional[str] = None, 
                          voice_id: Optional[str] = None,
                          first_message: Optional[str] = None,
                          tool_ids: Optional[list] = None) -> Dict[str, Any]:
        """
        Update an existing ElevenLabs agent
        
        Args:
            agent_id: The ElevenLabs agent ID
            name: New name for the agent (optional)
            system_prompt: New system prompt (optional)
            voice_id: New voice ID (optional)
            first_message: New first message (optional)
            tool_ids: List of tool IDs to attach (optional)
            
        Returns:
            Dict containing success status and response data
        """
        try:
            url = f"{self.base_url}/convai/agents/{agent_id}"
            
            payload = {}
            if name is not None:
                payload["name"] = name
                
            if system_prompt is not None or voice_id is not None or first_message is not None or tool_ids is not None:
                payload["conversation_config"] = {}
                
                if system_prompt is not None or first_message is not None or tool_ids is not None:
                    agent_config = {}
                    
                    if system_prompt is not None or tool_ids is not None:
                        prompt_config = {}
                        if system_prompt is not None:
                            prompt_config["prompt"] = system_prompt
                        if tool_ids is not None:
                            prompt_config["tool_ids"] = tool_ids
                            logger.info(f"Adding {len(tool_ids)} tools to agent: {tool_ids}")
                        agent_config["prompt"] = prompt_config
                    
                    if first_message is not None:
                        agent_config["first_message"] = first_message
                        logger.info(f"Updating first message: {first_message[:50]}...")
                    
                    payload["conversation_config"]["agent"] = agent_config
                    
                if voice_id is not None:
                    payload["conversation_config"]["tts"] = {
                        "voice_id": voice_id
                    }
            
            if not payload:
                return {"success": False, "error": "No update data provided"}
            
            logger.info(f"Updating agent {agent_id} with payload: {payload}")
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    logger.info(f"Successfully updated ElevenLabs agent: {agent_id}")
                    return {"success": True, "data": response.json()}
                else:
                    error_text = response.text
                    logger.error(f"ElevenLabs update API error: {response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": f"ElevenLabs API returned {response.status_code}: {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Exception updating ElevenLabs agent: {str(e)}", exc_info=True)
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
                
                if response.status_code in [200, 204]:  # 200 OK or 204 No Content are both success
                    logger.info(f"Successfully deleted ElevenLabs agent: {agent_id} (status: {response.status_code})")
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
    
    async def create_webhook_tool(self, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a webhook tool using ElevenLabs API
        
        Args:
            tool_config: Tool configuration dictionary
            
        Returns:
            Dict containing success status and tool details
        """
        try:
            # Create the tool payload according to ElevenLabs API spec
            tool_payload = {
                "tool_config": {
                    "type": "webhook",
                    "name": tool_config["name"],
                    "description": tool_config["description"],
                    "api_schema": {
                        "url": tool_config["webhook_url"],
                        "method": "POST",
                        "request_body_schema": {
                            "type": "object",
                            "description": "search for user query in tool",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query to find relevant information in the user's knowledge base"
                                }
                            },
                            "required": ["query"]
                        },
                        "request_headers": {
                            "Authorization": f"Bearer {tool_config['authentication']['token']}"
                        }
                    }
                }
            }
            
            # Debug: Log the payload being sent
            logger.info(f"Creating tool with payload: {tool_payload}")
            logger.info(f"Headers: {self.headers}")
            
            # Create tool using the correct ElevenLabs API endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/convai/tools",
                    headers=self.headers,
                    json=tool_payload
                )
            
            logger.info(f"Tool creation response: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                tool_id = result.get("id")
                logger.info(f"Successfully created webhook tool: {tool_id}")
                return {
                    "success": True,
                    "tool_id": tool_id,
                    "message": "Webhook tool created successfully"
                }
            else:
                logger.error(f"Failed to create tool: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"ElevenLabs API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error creating webhook tool: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def list_tools(self) -> Dict[str, Any]:
        """
        List all tools in the workspace
        
        Returns:
            Dict containing list of tools
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.elevenlabs.io/v1/convai/tools",
                    headers=self.headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully retrieved {len(result.get('tools', []))} tools")
                return {
                    "success": True,
                    "tools": result.get("tools", [])
                }
            else:
                logger.error(f"Failed to list tools: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"ElevenLabs API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_tool_dependent_agents(self, tool_id: str) -> Dict[str, Any]:
        """
        Get agents that depend on a specific tool
        
        Args:
            tool_id: Tool ID to check dependencies for
            
        Returns:
            Dict containing dependent agents
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.elevenlabs.io/v1/convai/tools/{tool_id}/dependent-agents",
                    headers=self.headers
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Tool {tool_id} has {len(result.get('agents', []))} dependent agents")
                return {
                    "success": True,
                    "agents": result.get("agents", []),
                    "has_more": result.get("has_more", False)
                }
            else:
                logger.error(f"Failed to get dependent agents: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"ElevenLabs API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error getting dependent agents: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def add_tool_to_agent(self, agent_id: str, tool_id: str) -> Dict[str, Any]:
        """
        Add an existing tool to an ElevenLabs agent
        
        Args:
            agent_id: ElevenLabs agent ID
            tool_id: Tool ID to attach
            
        Returns:
            Dict containing success status
        """
        try:
            logger.info(f"🔧 Attempting to attach tool {tool_id} to agent {agent_id}")
            
            # First verify the agent exists
            async with httpx.AsyncClient() as client:
                agent_check = await client.get(
                    f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}",
                    headers=self.headers
                )
                logger.info(f"Agent verification: {agent_check.status_code} - {agent_check.text[:200]}")
                
                if agent_check.status_code == 404:
                    return {
                        "success": False,
                        "error": f"Agent {agent_id} not found in ElevenLabs workspace"
                    }
            
            # Try different possible endpoints and methods for adding tools to agents
            endpoints_to_try = [
                {
                    "method": "POST",
                    "url": f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}/tools",
                    "payload": {"tool_id": tool_id}
                },
                {
                    "method": "PUT",
                    "url": f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}/tools",
                    "payload": {"tool_id": tool_id}
                },
                {
                    "method": "PATCH",
                    "url": f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}",
                    "payload": {"tool_ids": [tool_id]}
                },
                {
                    "method": "PATCH",
                    "url": f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}",
                    "payload": {"tools": [{"id": tool_id}]}
                },
                {
                    "method": "PATCH",
                    "url": f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}",
                    "payload": {"conversation_config": {"tool_ids": [tool_id]}}
                },
                {
                    "method": "PUT",
                    "url": f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}/tools/{tool_id}",
                    "payload": {}
                }
            ]
            
            for i, endpoint_config in enumerate(endpoints_to_try):
                logger.info(f"🔄 Trying {endpoint_config['method']} {i+1}/{len(endpoints_to_try)}: {endpoint_config['url']}")
                logger.info(f"📦 Payload: {endpoint_config['payload']}")
                
                async with httpx.AsyncClient() as client:
                    if endpoint_config["method"] == "POST":
                        response = await client.post(
                            endpoint_config["url"],
                            headers=self.headers,
                            json=endpoint_config["payload"]
                        )
                    elif endpoint_config["method"] == "PUT":
                        response = await client.put(
                            endpoint_config["url"],
                            headers=self.headers,
                            json=endpoint_config["payload"]
                        )
                    elif endpoint_config["method"] == "PATCH":
                        response = await client.patch(
                            endpoint_config["url"],
                            headers=self.headers,
                            json=endpoint_config["payload"]
                        )
                
                logger.info(f"📊 Response {i+1}: {response.status_code} - {response.text[:300]}")
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Successfully added tool {tool_id} to agent {agent_id}")
                    return {
                        "success": True,
                        "message": "Tool added to agent successfully",
                        "endpoint_used": endpoint_config["url"]
                    }
            
            # If all endpoints fail, return the last error
            logger.error(f"❌ All endpoints failed to add tool {tool_id} to agent {agent_id}")
            return {
                "success": False,
                "error": f"All API endpoints failed. Last response: {response.status_code} - {response.text}"
            }
                
        except Exception as e:
            logger.error(f"Error adding tool to agent: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def update_webhook_tool(self, tool_id: str, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing webhook tool configuration
        
        Args:
            tool_id: ElevenLabs tool ID to update
            tool_config: Updated tool configuration
            
        Returns:
            Dict containing success status
        """
        try:
            url = f"{self.base_url}/convai/tools/{tool_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.put(url, headers=self.headers, json=tool_config)
                
                if response.status_code in [200, 204]:
                    logger.info(f"Successfully updated webhook tool: {tool_id}")
                    return {
                        "success": True,
                        "tool_id": tool_id,
                        "message": "Tool updated successfully"
                    }
                else:
                    logger.error(f"Failed to update webhook tool: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"ElevenLabs API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Error updating webhook tool: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def synthesize_speech(self, text: str, voice_id: str, settings: dict = None) -> Dict[str, Any]:
        """
        Synthesize speech using ElevenLabs TTS API
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            settings: Voice settings (stability, similarity_boost, style, use_speaker_boost)
            
        Returns:
            Dict containing audio data or error
        """
        try:
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            # Default settings
            voice_settings = {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
            
            # Update with provided settings
            if settings:
                voice_settings.update(settings)
            
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": voice_settings
            }
            
            # Use different headers for TTS endpoint
            tts_headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=tts_headers)
                
                if response.status_code == 200:
                    # Return audio data as bytes
                    audio_data = response.content
                    logger.info(f"Successfully synthesized speech for voice: {voice_id}")
                    return {
                        "success": True,
                        "audio_data": audio_data,
                        "content_type": "audio/mpeg"
                    }
                else:
                    logger.error(f"ElevenLabs TTS API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"ElevenLabs API error: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to synthesize speech: {str(e)}"
            }

# Create a singleton instance
elevenlabs_service = ElevenLabsService()
