#!/usr/bin/env python3
"""
Test script to check if agent exists and try different API endpoints
"""
import asyncio
import httpx

async def test_agent():
    agent_id = "agent_2301k74d7arffbb8thy7pwmww4jf"
    api_key = "4b757c743f73858a0b19a8947b7742c3c2acbacc947374329ae264bb61d02c2d"
    base_url = "https://api.elevenlabs.io/v1"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"🔍 Testing agent: {agent_id}")
    print("=" * 50)
    
    # Try to get agent details
    print("1. Testing agent details...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/convai/agents/{agent_id}", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Agent exists!")
            data = response.json()
            print(f"   Name: {data.get('name', 'N/A')}")
        else:
            print(f"   ❌ Agent not found: {response.text}")
    
    # Try different tools endpoints
    endpoints_to_try = [
        f"/convai/agents/{agent_id}/tools",
        f"/conversational-ai/agents/{agent_id}/tools", 
        f"/agents/{agent_id}/tools",
        f"/convai/agents/{agent_id}/webhooks"
    ]
    
    print("\n2. Testing different tools endpoints...")
    for endpoint in endpoints_to_try:
        print(f"   Testing: {endpoint}")
        async with httpx.AsyncClient() as client:
            # Try GET first to see if endpoint exists
            response = await client.get(f"{base_url}{endpoint}", headers=headers)
            print(f"   GET Status: {response.status_code}")
            if response.status_code != 404:
                print(f"   Response: {response.text[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_agent())
