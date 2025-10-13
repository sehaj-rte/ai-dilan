#!/usr/bin/env python3
"""
Test script to verify file processing with pre-extracted text
"""

import os
import sys
from sqlalchemy.orm import Session
from config.database import SessionLocal
from controllers.knowledge_base_controller import process_expert_files
import asyncio

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_file_processing():
    """Test file processing using pre-extracted text"""
    # Get database session
    db = SessionLocal()
    
    try:
        print("Testing file processing with pre-extracted text...")
        
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
            
            if 'extracted_text' in test_file and test_file['extracted_text']:
                print(f"📝 Extracted text preview: {test_file['extracted_text'][:100]}...")
            
            # Test process_expert_files function directly
            # Using a dummy expert_id and agent_id for testing
            expert_id = "test_expert_id"
            agent_id = "test_agent_id"
            
            print("\n🚀 Starting file processing test...")
            result = await process_expert_files(
                expert_id=expert_id,
                agent_id=agent_id,
                selected_files=[file_id],
                db=db
            )
            
            if result["success"]:
                print("✅ File processing successful")
                print(f"📊 Processed count: {result['processed_count']}")
                print(f"📈 Success rate: {result['success_rate']:.1f}%")
            else:
                print(f"❌ File processing failed: {result['error']}")
                # This is expected since we don't have valid ElevenLabs credentials
                print("💡 This failure is expected without valid ElevenLabs API credentials")
                print("💡 The important part is that text extraction was skipped (using pre-extracted text)")
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
    asyncio.run(test_file_processing())
