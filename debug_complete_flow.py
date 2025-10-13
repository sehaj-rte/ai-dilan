#!/usr/bin/env python3
"""
Debug script to test the complete document processing flow
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from config.database import get_db
from models.file_db import FileDB
from services.file_service import FileService
from services.document_processor import document_processor
from services.embedding_service import embedding_service
import uuid

def test_complete_flow():
    """Test the complete document processing flow"""
    
    print("🔍 Debug: Testing Complete Document Processing Flow")
    print("="*60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if there are any files in the database
        files = db.query(FileDB).all()
        print(f"📊 Found {len(files)} files in database")
        
        if not files:
            print("❌ No files found in database to test with")
            return
        
        # Test with the first file
        test_file = files[0]
        print(f"\n📄 Testing with file: {test_file.name}")
        print(f"   - ID: {test_file.id}")
        print(f"   - Type: {test_file.type}")
        print(f"   - Size: {test_file.size} bytes")
        print(f"   - Has content: {test_file.content is not None}")
        print(f"   - Has extracted text: {test_file.extracted_text is not None}")
        print(f"   - S3 Key: {test_file.s3_key}")
        
        # Test file service
        file_service = FileService(db)
        file_result = file_service.get_file_by_id(str(test_file.id))
        
        print(f"\n🔍 File service result: {file_result.get('success', False)}")
        
        if not file_result.get("success"):
            print(f"❌ File service failed: {file_result.get('error')}")
            return
        
        # Test document extraction if we have content
        if test_file.content:
            print(f"\n📝 Testing document extraction...")
            
            extraction_result = document_processor.extract_text(
                file_content=test_file.content,
                content_type=test_file.type,
                filename=test_file.name
            )
            
            print(f"📊 Extraction result: {extraction_result.get('success', False)}")
            
            if extraction_result.get("success"):
                text = extraction_result.get("text", "")
                print(f"✅ Extracted {len(text)} characters")
                print(f"📝 Text preview: {text[:200]}...")
                
                # Test embedding generation
                print(f"\n🧠 Testing embedding generation...")
                
                embedding_result = embedding_service.process_document(
                    text=text,
                    file_id=str(test_file.id),
                    filename=test_file.name,
                    user_id="test_user"
                )
                
                print(f"📊 Embedding result: {embedding_result.get('success', False)}")
                
                if embedding_result.get("success"):
                    chunks = embedding_result.get("chunks", [])
                    print(f"✅ Generated {len(chunks)} embedding chunks")
                    
                    if chunks:
                        first_chunk = chunks[0]
                        print(f"🔍 First chunk:")
                        print(f"   - ID: {first_chunk.get('id')}")
                        print(f"   - Text length: {len(first_chunk.get('text', ''))}")
                        print(f"   - Embedding dimensions: {len(first_chunk.get('embedding', []))}")
                else:
                    print(f"❌ Embedding failed: {embedding_result.get('error')}")
            else:
                print(f"❌ Extraction failed: {extraction_result.get('error')}")
        else:
            print("⚠️ No file content to test with")
            
        # Test with pre-extracted text if available
        if test_file.extracted_text:
            print(f"\n📝 Testing with pre-extracted text...")
            print(f"   - Extracted text length: {len(test_file.extracted_text)}")
            print(f"   - Word count: {test_file.word_count}")
            
            # Test embedding generation with pre-extracted text
            embedding_result = embedding_service.process_document(
                text=test_file.extracted_text,
                file_id=str(test_file.id),
                filename=test_file.name,
                user_id="test_user"
            )
            
            print(f"📊 Pre-extracted embedding result: {embedding_result.get('success', False)}")
            
            if embedding_result.get("success"):
                chunks = embedding_result.get("chunks", [])
                print(f"✅ Generated {len(chunks)} embedding chunks from pre-extracted text")
            else:
                print(f"❌ Pre-extracted embedding failed: {embedding_result.get('error')}")
        
    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_complete_flow()
