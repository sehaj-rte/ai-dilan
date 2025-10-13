#!/usr/bin/env python3
"""
Test script for ElevenLabs Tools API exploration
"""

import asyncio
from services.elevenlabs_service import elevenlabs_service

async def test_list_tools():
    """Test listing all tools in workspace"""
    print("🔧 Testing ElevenLabs Tools API...")
    print("=" * 50)
    
    # List all tools
    print("📋 Listing all tools in workspace...")
    tools_result = await elevenlabs_service.list_tools()
    
    if tools_result["success"]:
        tools = tools_result["tools"]
        print(f"✅ Found {len(tools)} tools in workspace:")
        
        for i, tool in enumerate(tools, 1):
            tool_config = tool.get("tool_config", {})
            print(f"\n{i}. Tool ID: {tool['id']}")
            print(f"   Name: {tool_config.get('name', 'N/A')}")
            print(f"   Type: {tool_config.get('type', 'N/A')}")
            print(f"   Description: {tool_config.get('description', 'N/A')}")
            
            # Check dependent agents for each tool
            print(f"   🔍 Checking dependent agents...")
            deps_result = await elevenlabs_service.get_tool_dependent_agents(tool['id'])
            
            if deps_result["success"]:
                agents = deps_result["agents"]
                if agents:
                    print(f"   📎 Attached to {len(agents)} agents:")
                    for agent in agents:
                        if agent.get("type") == "available":
                            print(f"      - {agent['name']} (ID: {agent['id']})")
                        else:
                            print(f"      - Unknown agent")
                else:
                    print(f"   📎 Not attached to any agents")
            else:
                print(f"   ❌ Failed to check dependencies: {deps_result.get('error')}")
        
        return tools
    else:
        print(f"❌ Failed to list tools: {tools_result.get('error')}")
        return []

async def test_create_simple_tool():
    """Test creating a simple webhook tool"""
    print("\n" + "=" * 50)
    print("🛠️ Testing tool creation...")
    
    tool_config = {
        "name": "test_knowledge_search",
        "description": "Test tool for searching knowledge base",
        "webhook_url": "http://localhost:8000/tools/search-user-knowledge?user_id=test_user",
        "authentication": {
            "type": "bearer",
            "token": "test-token-123"
        }
    }
    
    result = await elevenlabs_service.create_webhook_tool(tool_config)
    
    if result["success"]:
        tool_id = result["tool_id"]
        print(f"✅ Created test tool: {tool_id}")
        
        # Check if any agents are using this tool
        deps_result = await elevenlabs_service.get_tool_dependent_agents(tool_id)
        if deps_result["success"]:
            print(f"📎 Tool dependencies: {len(deps_result['agents'])} agents")
        
        return tool_id
    else:
        print(f"❌ Failed to create tool: {result.get('error')}")
        return None

async def main():
    """Main test function"""
    print("🚀 ElevenLabs Tools API Exploration")
    print("=" * 50)
    
    # List existing tools
    existing_tools = await test_list_tools()
    
    # Create a test tool
    new_tool_id = await test_create_simple_tool()
    
    # List tools again to see the new one
    if new_tool_id:
        print("\n" + "=" * 50)
        print("📋 Updated tools list:")
        await test_list_tools()
    
    print("\n" + "=" * 50)
    print("🎯 Key Findings:")
    print("1. Tools can be created successfully")
    print("2. Tools exist in workspace but may not be attached to agents")
    print("3. Tool attachment might require manual configuration or different API")
    print("4. The 'dependent-agents' endpoint shows which agents use each tool")

if __name__ == "__main__":
    asyncio.run(main())
