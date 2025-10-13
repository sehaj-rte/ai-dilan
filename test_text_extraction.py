#!/usr/bin/env python3
"""
Test script to verify text extraction and storage functionality
"""

import os
import sys
from sqlalchemy.orm import Session
from config.database import SessionLocal
from controllers.knowledge_base_controller import upload_file
from services.file_service import FileService
import asyncio

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_text_extraction():
    """Test text extraction during file upload"""
    # Create a test text file
    test_content = "This is a test document with some content to verify text extraction functionality."
    
    # Create a mock file object
    class MockFile:
        def __init__(self, content, filename, content_type):
            self.file = MockFileContent(content)
            self.filename = filename
            self.content_type = content_type
            
    class MockFileContent:
        def __init__(self, content):
            self.content = content
            
        def read(self):
            return self.content.encode('utf-8')
    
    # Create mock file
    mock_file = MockFile(test_content, "test_document.txt", "text/plain")
    
    # Get database session
    db = SessionLocal()
    
    try:
        print("Testing text extraction during file upload...")
        
        # Upload file
        result = await upload_file(mock_file, db, user_id=None)
        
        if result["success"]:
            print("✅ File upload successful")
            file_id = result["id"]
            print(f"📁 File ID: {file_id}")
            
            # Check if extracted text was stored
            file_service = FileService(db)
            file_result = file_service.get_file_by_id(file_id)
            
            if file_result["success"]:
                file_data = file_result["file"]
                extracted_text = file_data.get("extracted_text")
                word_count = file_data.get("word_count")
                
                if extracted_text:
                    print("✅ Extracted text stored in database")
                    print(f"📝 Extracted text: {extracted_text}")
                    print(f"📊 Word count: {word_count}")
                else:
                    print("❌ Extracted text not stored in database")
            else:
                print(f"❌ Failed to retrieve file: {file_result['error']}")
        else:
            print(f"❌ File upload failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_text_extraction())
