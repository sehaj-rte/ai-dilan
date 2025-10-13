#!/usr/bin/env python3
"""
Test script for expert creation with selected files
"""

import requests
import json

def test_expert_creation_with_files():
    """Test expert creation with selected files"""
    
    url = "http://localhost:8000/experts/"
    
    # Test payload with selected files
    payload = {
        "name": "Knowledge Expert",
        "description": "An expert with access to uploaded documents",
        "system_prompt": "You are a knowledgeable AI assistant with access to uploaded documents. Use the search tool to find relevant information from the user's documents when answering questions.",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Default ElevenLabs voice
        "selected_files": ["test-file-1", "test-file-2"]  # Mock file IDs
    }
    
    try:
        print("🧪 Testing expert creation with selected files...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Expert creation successful!")
            print(json.dumps(result, indent=2))
            
            if result.get("success"):
                expert = result.get("expert", {})
                expert_id = expert.get("id")
                agent_id = result.get("elevenlabs_agent_id")
                tool_id = expert.get("knowledge_base_tool_id")
                
                print(f"\n🎉 Expert created successfully!")
                print(f"Expert ID: {expert_id}")
                print(f"ElevenLabs Agent ID: {agent_id}")
                print(f"Knowledge Base Tool ID: {tool_id}")
                print(f"Selected Files: {expert.get('selected_files', [])}")
                
                if tool_id:
                    print("✅ Knowledge base tool was created and attached!")
                else:
                    print("⚠️ No knowledge base tool was created")
                    
            else:
                print(f"❌ Expert creation failed: {result.get('error')}")
        else:
            print("❌ Expert creation failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during expert creation: {e}")

def test_tools_list():
    """Check the tools list to see our created tools"""
    import asyncio
    from services.elevenlabs_service import elevenlabs_service
    
    async def list_tools():
        print("\n🔧 Checking ElevenLabs tools...")
        tools_result = await elevenlabs_service.list_tools()
        
        if tools_result["success"]:
            tools = tools_result["tools"]
            print(f"📋 Found {len(tools)} tools:")
            
            for i, tool in enumerate(tools, 1):
                tool_config = tool.get("tool_config", {})
                print(f"{i}. {tool['id']} - {tool_config.get('name', 'N/A')}")
                
                # Check dependencies
                deps_result = await elevenlabs_service.get_tool_dependent_agents(tool['id'])
                if deps_result["success"]:
                    agents = deps_result["agents"]
                    if agents:
                        print(f"   📎 Attached to {len(agents)} agents")
                        for agent in agents:
                            if agent.get("type") == "available":
                                print(f"      - {agent['name']} (ID: {agent['id']})")
                    else:
                        print(f"   📎 Not attached to any agents")
        else:
            print(f"❌ Failed to list tools: {tools_result.get('error')}")
    
    asyncio.run(list_tools())

if __name__ == "__main__":
    test_expert_creation_with_files()
    test_tools_list()
