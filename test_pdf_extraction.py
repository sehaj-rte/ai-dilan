#!/usr/bin/env python3
"""
Test script to verify PDF text extraction and storage functionality
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

async def test_pdf_extraction():
    """Test PDF text extraction during file upload"""
    # Read the test PDF file
    with open("test_pdf_document.pdf", "rb") as f:
        pdf_content = f.read()
    
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
            return self.content
    
    # Create mock file
    mock_file = MockFile(pdf_content, "test_pdf_document.pdf", "application/pdf")
    
    # Get database session
    db = SessionLocal()
    
    try:
        print("Testing PDF text extraction during file upload...")
        
        # Upload file
        result = await upload_file(mock_file, db, user_id=None)
        
        if result["success"]:
            print("✅ PDF file upload successful")
            file_id = result["id"]
            print(f"📁 File ID: {file_id}")
            
            # Check if extracted text was stored
            file_service = FileService(db)
            file_result = file_service.get_file_by_id(file_id)
            
            if file_result["success"]:
                file_data = file_result["file"]
                extracted_text = file_data.get("extracted_text")
                word_count = file_data.get("word_count")
                document_type = file_data.get("document_type")
                
                print(f"📄 Document type: {document_type}")
                
                if extracted_text:
                    print("✅ Extracted text stored in database")
                    print(f"📝 Extracted text: {extracted_text}")
                    print(f"📊 Word count: {word_count}")
                else:
                    print("❌ Extracted text not stored in database")
            else:
                print(f"❌ Failed to retrieve file: {file_result['error']}")
        else:
            print(f"❌ PDF file upload failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_pdf_extraction())
