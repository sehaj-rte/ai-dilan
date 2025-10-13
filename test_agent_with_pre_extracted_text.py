#!/usr/bin/env python3
"""
Test script to verify agent creation with pre-extracted text
"""

import os
import sys
from sqlalchemy.orm import Session
from config.database import SessionLocal
from controllers.expert_controller import create_expert_with_elevenlabs
from controllers.knowledge_base_controller import process_expert_files
import asyncio

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_agent_with_pre_extracted_text():
    """Test agent creation using pre-extracted text"""
    # Get database session
    db = SessionLocal()
    
    try:
        print("Testing agent creation with pre-extracted text...")
        
        # First, let's get a list of existing files to use for testing
        from services.file_service import FileService
        file_service = FileService(db)
        files_result = file_service.get_files()
        
        if files_result["success"] and files_result["files"]:
            # Use the first file for testing
            test_file = files_result["files"][0]
            file_id = test_file["id"]
            filename = test_file["name"]
            
            print(f"📁 Using existing file: {filename} (ID: {file_id})")
            print(f"📄 File has extracted_text: {'extracted_text' in test_file and bool(test_file['extracted_text'])}")
            
            # Create test expert data
            expert_data = {
                "name": "Test Expert",
                "description": "Test expert for verifying pre-extracted text processing",
                "system_prompt": "You are a helpful assistant that answers questions based on uploaded documents.",
                "voice_id": "test_voice_id",
                "selected_files": [file_id]  # Use the existing file
            }
            
            # Create expert with ElevenLabs integration
            result = await create_expert_with_elevenlabs(db, expert_data)
            
            if result["success"]:
                print("✅ Expert creation successful")
                expert_id = result["expert"]["id"]
                agent_id = result["elevenlabs_agent_id"]
                print(f"👤 Expert ID: {expert_id}")
                print(f"🤖 Agent ID: {agent_id}")
                
                # Check if file processing was queued
                file_processing = result.get("file_processing", {})
                if file_processing.get("queued"):
                    print("📋 File processing queued successfully")
                    print(f"   Queue position: {file_processing.get('queue_position')}")
                    print(f"   Task ID: {file_processing.get('task_id')}")
                else:
                    print("📭 No files selected for processing")
            else:
                print(f"❌ Expert creation failed: {result['error']}")
        else:
            print("📭 No existing files found for testing")
            print("💡 Please upload some files first using the /knowledge-base/upload endpoint")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_agent_with_pre_extracted_text())
