#!/usr/bin/env python3
"""
Test script for expert creation
"""

import requests
import json

def test_expert_creation():
    """Test expert creation endpoint"""
    
    url = "http://localhost:8000/experts/"
    
    # Test payload
    payload = {
        "name": "Test Expert",
        "description": "A test expert for validation",
        "system_prompt": "You are a helpful AI assistant specializing in testing and validation.",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Default ElevenLabs voice
        "selected_files": []  # No files for this test
    }
    
    try:
        print("🧪 Testing expert creation...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Expert creation successful!")
            print(json.dumps(result, indent=2))
            
            if result.get("success"):
                expert_id = result.get("expert", {}).get("id")
                agent_id = result.get("elevenlabs_agent_id")
                print(f"\n🎉 Expert created successfully!")
                print(f"Expert ID: {expert_id}")
                print(f"ElevenLabs Agent ID: {agent_id}")
            else:
                print(f"❌ Expert creation failed: {result.get('error')}")
        else:
            print("❌ Expert creation failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during expert creation: {e}")

def test_expert_listing():
    """Test expert listing endpoint"""
    
    url = "http://localhost:8000/experts/"
    
    try:
        print("\n🧪 Testing expert listing...")
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Expert listing successful!")
            experts = result.get("experts", [])
            print(f"Total experts: {len(experts)}")
            
            for i, expert in enumerate(experts, 1):
                print(f"{i}. {expert['name']} (ID: {expert['id']})")
                print(f"   Agent ID: {expert.get('elevenlabs_agent_id', 'N/A')}")
                print(f"   Active: {expert.get('is_active', False)}")
                print()
        else:
            print("❌ Expert listing failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during expert listing: {e}")

if __name__ == "__main__":
    test_expert_creation()
    test_expert_listing()
