#!/usr/bin/env python3
"""
Test script to debug ElevenLabs integration for agent agent_9201k7rsgd12fxj8xb0nr1b689s9
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from services.elevenlabs_service import ElevenLabsService
from services.pinecone_service import PineconeService

async def test_elevenlabs_integration():
    """Test ElevenLabs integration with the specific agent"""
    
    agent_id = "agent_9201k7rsgd12fxj8xb0nr1b689s9"
    
    print(f"🧪 Testing ElevenLabs integration for agent: {agent_id}")
    print("=" * 60)
    
    # Check environment variables
    print("🔧 Environment Variables:")
    print(f"   ELEVENLABS_API_KEY: {'✅ Set' if os.getenv('ELEVENLABS_API_KEY') else '❌ Missing'}")
    print(f"   BASE_URL: {os.getenv('BASE_URL', 'Not set - using default')}")
    print(f"   WEBHOOK_AUTH_TOKEN: {'✅ Set' if os.getenv('WEBHOOK_AUTH_TOKEN') else '❌ Missing'}")
    print()
    
    # Initialize services
    elevenlabs_service = ElevenLabsService()
    pinecone_service = PineconeService()
    
    # Test 1: Check if agent exists
    print("🔍 Step 1: Verifying agent exists...")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}",
                headers=elevenlabs_service.headers
            )
            print(f"   Agent check: {response.status_code}")
            if response.status_code == 200:
                agent_data = response.json()
                print(f"   ✅ Agent exists: {agent_data.get('name', 'Unknown')}")
                print(f"   Current tools: {len(agent_data.get('tools', []))}")
            elif response.status_code == 404:
                print(f"   ❌ Agent not found in workspace")
                return
            else:
                print(f"   ⚠️ Unexpected response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error checking agent: {e}")
        return
    
    # Test 2: Create webhook tool
    print("\n🔧 Step 2: Creating webhook tool...")
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
    
    tool_result = await elevenlabs_service.create_webhook_tool(tool_config)
    print(f"   Tool creation result: {tool_result}")
    
    if not tool_result.get("success"):
        print(f"   ❌ Tool creation failed: {tool_result.get('error')}")
        return
    
    tool_id = tool_result.get("tool_id")
    print(f"   ✅ Tool created with ID: {tool_id}")
    
    # Test 3: Attach tool to agent
    print(f"\n🔗 Step 3: Attaching tool {tool_id} to agent {agent_id}...")
    attachment_result = await elevenlabs_service.add_tool_to_agent(agent_id, tool_id)
    print(f"   Attachment result: {attachment_result}")
    
    if attachment_result.get("success"):
        print(f"   ✅ Successfully attached tool to agent!")
    else:
        print(f"   ❌ Tool attachment failed: {attachment_result.get('error')}")
    
    # Test 4: List agent's tools to verify (with delay for API sync)
    print(f"\n📋 Step 4: Verifying agent's tools...")
    import time
    print("   Waiting 2 seconds for API sync...")
    time.sleep(2)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}",
                headers=elevenlabs_service.headers
            )
            if response.status_code == 200:
                agent_data = response.json()
                print(f"   Full agent data keys: {list(agent_data.keys())}")
                
                # Check different possible tool fields
                tools = agent_data.get('tools', [])
                tool_ids = agent_data.get('tool_ids', [])
                
                # Check conversation_config for tools
                conv_config = agent_data.get('conversation_config', {})
                conv_tools = conv_config.get('tools', [])
                conv_tool_ids = conv_config.get('tool_ids', [])
                
                # Check workflow for tools
                workflow = agent_data.get('workflow', {})
                workflow_tools = workflow.get('tools', [])
                
                print(f"   Agent tools field: {tools}")
                print(f"   Agent tool_ids field: {tool_ids}")
                print(f"   Conversation config tools: {conv_tools}")
                print(f"   Conversation config tool_ids: {conv_tool_ids}")
                print(f"   Workflow tools: {workflow_tools}")
                
                # Count all tools found
                all_tools = tools + conv_tools + workflow_tools
                print(f"   Agent now has {len(all_tools)} tools total:")
                for tool in all_tools:
                    if isinstance(tool, dict):
                        print(f"     - {tool.get('name', 'Unknown')} (ID: {tool.get('id', 'Unknown')})")
                    else:
                        print(f"     - Tool ID: {tool}")
                    
                if tool_ids or conv_tool_ids:
                    print(f"   All Tool IDs: {tool_ids + conv_tool_ids}")
            else:
                print(f"   ❌ Could not fetch agent tools: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error fetching agent tools: {e}")
    
    # Test 5: Try to list all tools in workspace to verify tool exists
    print(f"\n🔧 Step 5: Listing all tools in workspace...")
    try:
        tools_result = await elevenlabs_service.list_tools()
        if tools_result.get("success"):
            workspace_tools = tools_result.get("tools", [])
            print(f"   Workspace has {len(workspace_tools)} tools total")
            for tool in workspace_tools:
                if tool.get('id') == tool_id:
                    print(f"   ✅ Found our tool: {tool.get('name')} (ID: {tool.get('id')})")
                    break
            else:
                print(f"   ❌ Our tool {tool_id} not found in workspace")
        else:
            print(f"   ❌ Could not list workspace tools: {tools_result.get('error')}")
    except Exception as e:
        print(f"   ❌ Error listing workspace tools: {e}")

if __name__ == "__main__":
    asyncio.run(test_elevenlabs_integration())
