#!/usr/bin/env python3
"""
Debug script to simulate frontend request and identify the issue
"""

import asyncio
import httpx
import json

async def test_frontend_request():
    """Test what the frontend is sending"""
    
    # This is exactly what the frontend sends based on the code
    frontend_payload = {
        "name": "Test Expert Frontend",
        "description": "A test expert from frontend simulation", 
        "system_prompt": "You are a helpful AI assistant.",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "avatar_base64": None,
        "selected_files": []
        # Note: frontend doesn't send user_id
    }
    
    print("🔍 Testing frontend payload:")
    print(json.dumps(frontend_payload, indent=2))
    
    try:
        async with httpx.AsyncClient() as client:
            # Test debug endpoint first
            print("\n🔍 Testing debug endpoint...")
            debug_response = await client.post(
                "http://localhost:8000/experts/debug",
                json=frontend_payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"Debug Status: {debug_response.status_code}")
            print(f"Debug Response: {debug_response.text}")
            
            # Test actual endpoint
            print("\n🔍 Testing actual endpoint...")
            response = await client.post(
                "http://localhost:8000/experts/",
                json=frontend_payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 422:
                try:
                    error_detail = response.json()
                    print(f"422 Error Details: {json.dumps(error_detail, indent=2)}")
                except:
                    print("Could not parse 422 error response")
                    
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_frontend_request())
