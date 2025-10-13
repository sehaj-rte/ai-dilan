#!/usr/bin/env python3
"""
Manual script to insert the failed expert into the database
This uses the fixed ExpertService code to handle the JSON properly
"""

import os
import sys
from sqlalchemy.orm import Session
from config.database import SessionLocal, create_tables
from services.expert_service import ExpertService
import json

def main():
    """Insert the failed expert manually"""
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Ensure tables exist
        create_tables()
        
        # Expert data from the failed request (removed first_message as it doesn't exist in DB)
        expert_data = {
            "id": "5f2cf2f4-185d-4e66-acc0-742127ea968f",
            "name": "chris",
            "description": "yo are a chris an expert of therapist",
            "system_prompt": None,
            "voice_id": None,
            "elevenlabs_agent_id": "agent_2001k7ek3n5qea29sfpf8jyvkz2r",
            "avatar_url": "https://ai-dilan.s3.us-east-1.amazonaws.com/expert-avatars/20251013_162057_1b4877ac.png",
            "pinecone_index_name": "agent_2001k7ek3n5qea29sfpf8jyvkz2r",
            "selected_files": ["1e604360-9ca1-4f1d-89b4-f1dc28853043", "e3d74085-5dca-4f1f-a4c4-2611172c76b7"],  # As Python list
            "knowledge_base_tool_id": "tool_1401k7ek3pbxem7aa9dvqck3ndp0",
            "is_active": True
        }
        
        print("🔧 Manually inserting expert with fixed JSON handling...")
        print(f"Expert ID: {expert_data['id']}")
        print(f"Expert Name: {expert_data['name']}")
        print(f"Selected Files: {expert_data['selected_files']}")
        
        # Create expert using the fixed service
        expert_service = ExpertService(db)
        result = expert_service.create_expert(expert_data)
        
        if result["success"]:
            print("✅ Expert created successfully!")
            print(f"Expert: {result['expert']}")
        else:
            print(f"❌ Failed to create expert: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
